# -*- coding: utf-8 -*-
"""
视频分析器 - 重构版本
功能：视频内容分析、场景检测、语音识别、对象检测等
"""

import subprocess
import json
import os
import cv2
import speech_recognition as sr
import librosa
import numpy as np
import whisper
from ultralytics import YOLO
from typing import Dict, Any, List, Optional

from core.utils.config_manager import config, ErrorHandler, PathHelper

try:
    # 新版本 PySceneDetect API (推荐)
    from scenedetect import open_video, SceneManager, ContentDetector

    NEW_API_AVAILABLE = True
except ImportError:
    try:
        # 旧版本 API (向后兼容)
        from scenedetect import VideoManager, SceneManager
        from scenedetect.detectors import ContentDetector

        NEW_API_AVAILABLE = False
    except ImportError:
        print("❌ PySceneDetect 未安装或版本不兼容")
        NEW_API_AVAILABLE = None


class VideoAnalyzer:
    def __init__(self):
        # 抑制PySceneDetect的弃用警告
        import warnings
        warnings.filterwarnings("ignore", message=".*VideoManager.*deprecated.*", category=DeprecationWarning)

        self.yolo_model = None
        self._whisper_model = None
        self.speech_timestamps = {}  # 新增：存储时间戳数据

    @property
    def whisper_model(self):
        """懒加载Whisper模型"""
        if self._whisper_model is None:
            try:
                print("[+] 加载Whisper模型...")
                self._whisper_model = whisper.load_model("base")
                print("[+] Whisper模型加载成功")
            except Exception as e:
                print(f"❌ Whisper模型加载失败: {e}")
                self._whisper_model = False
        return self._whisper_model if self._whisper_model is not False else None

    def detect_videos(self, input_path):
        """检测视频数量和路径"""
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

        if os.path.isfile(input_path):
            if input_path.lower().endswith(video_extensions):
                return [input_path]
            else:
                raise ValueError(f"不是有效的视频文件: {input_path}")
        elif os.path.isdir(input_path):
            video_files = [
                os.path.join(input_path, f)
                for f in os.listdir(input_path)
                if f.lower().endswith(video_extensions)
            ]
            if not video_files:
                raise ValueError(f"目录中没有找到视频文件: {input_path}")
            return video_files
        else:
            raise ValueError(f"路径不存在: {input_path}")

    def get_video_metadata(self, video_path):
        """提取视频基础信息"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-show_format',
                video_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe failed: {result.stderr}")

            metadata = json.loads(result.stdout)

            video_info = {
                "filename": os.path.basename(video_path),
                "filepath": video_path,
                "duration": float(metadata['format']['duration']),
                "bit_rate": metadata['format'].get('bit_rate'),
                "streams": []
            }

            # 添加便于访问的属性
            video_info["width"] = 0
            video_info["height"] = 0
            video_info["has_audio"] = False

            for stream in metadata['streams']:
                if stream['codec_type'] == 'video':
                    fps_str = stream.get("r_frame_rate", "30/1")
                    fps = eval(fps_str) if fps_str else 30
                    video_info["width"] = stream.get("width", 0)
                    video_info["height"] = stream.get("height", 0)
                    video_info["streams"].append({
                        "type": "video",
                        "width": stream.get("width"),
                        "height": stream.get("height"),
                        "fps": fps,
                        "codec": stream.get("codec_name")
                    })
                elif stream['codec_type'] == 'audio':
                    video_info["has_audio"] = True
                    video_info["streams"].append({
                        "type": "audio",
                        "sample_rate": stream.get("sample_rate"),
                        "channels": stream.get("channels"),
                        "codec": stream.get("codec_name")
                    })

            return video_info
        except Exception as e:
            print(f"❌ 获取视频元数据失败: {str(e)}")
            return None

    def detect_scenes(self, video_path, threshold=30.0):
        """场景检测 - 支持新旧API"""
        try:
            if NEW_API_AVAILABLE is None:
                print("❌ PySceneDetect 不可用，跳过场景检测")
                return []

            if NEW_API_AVAILABLE:
                # 使用新版本 API
                print("[+] 使用新版 PySceneDetect API 进行场景检测...")

                # 打开视频
                video = open_video(video_path)

                # 创建场景管理器
                scene_manager = SceneManager()
                scene_manager.add_detector(ContentDetector(threshold=threshold))

                # 检测场景
                scene_manager.detect_scenes(video)
                scene_list = scene_manager.get_scene_list()

                # 转换为秒数格式
                scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]

                print(f"[+] 检测到 {len(scenes)} 个场景")
                return scenes

            else:
                # 使用旧版本 API (向后兼容)
                print("[+] 使用旧版 PySceneDetect API 进行场景检测...")

                video_manager = VideoManager([video_path])
                scene_manager = SceneManager()
                scene_manager.add_detector(ContentDetector(threshold=threshold))

                base_timecode = video_manager.get_base_timecode()
                video_manager.set_downscale_factor()
                video_manager.start()
                scene_manager.detect_scenes(frame_source=video_manager)

                scene_list = scene_manager.get_scene_list(base_timecode)
                scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]

                video_manager.release()
                print(f"[+] 检测到 {len(scenes)} 个场景")
                return scenes

        except Exception as e:
            print(f"❌ 场景检测失败: {str(e)}")
            return []

    def extract_audio(self, video_path, output_audio="temp_audio.wav"):
        """提取音频 - 优化为Whisper格式"""
        try:
            # 为Whisper优化的音频提取参数
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-vn',  # 不要视频流
                '-acodec', 'pcm_s16le',  # 音频编码
                '-ar', '16000',  # 采样率16kHz（Whisper推荐）
                '-ac', '1',  # 单声道
                output_audio
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return output_audio
            else:
                print(f"❌ 音频提取失败: {result.stderr.decode()}")
                return None
        except Exception as e:
            print(f"❌ 音频提取异常: {str(e)}")
            return None

    def _format_time(self, seconds: float) -> str:
        """将秒数转换为 mm:ss.ff 格式"""
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:05.2f}"

    def _analyze_speech_segments(self, speech_timestamps: dict, target_duration: int = 30):
        """基于语音时间戳分析最佳剪辑片段"""

        segments = speech_timestamps.get("segments", [])
        if not segments:
            return []

        print(f"\n📊 语音片段分析 (目标时长: {target_duration}秒):")
        print("-" * 50)

        # 计算每个时间段的语音密度
        best_segments = []

        for i in range(0, len(segments)):
            # 尝试从当前段开始，找到累计时长接近目标的片段组合
            current_duration = 0
            current_segments = []

            for j in range(i, len(segments)):
                segment = segments[j]
                segment_duration = segment["end"] - segment["start"]

                if current_duration + segment_duration <= target_duration:
                    current_segments.append(segment)
                    current_duration += segment_duration
                else:
                    break

            if current_segments and current_duration >= target_duration * 0.8:  # 至少80%的目标时长
                # 计算这个组合的质量分数
                total_words = sum(len(seg["text"].split()) for seg in current_segments)
                density = total_words / max(current_duration, 1)  # 词密度

                segment_info = {
                    "start": current_segments[0]["start"],
                    "end": current_segments[-1]["end"],
                    "duration": current_duration,
                    "segments_count": len(current_segments),
                    "word_density": density,
                    "text_preview": current_segments[0]["text"][:50] + "..."
                }

                best_segments.append(segment_info)

        # 按词密度排序，选择最佳片段
        best_segments.sort(key=lambda x: x["word_density"], reverse=True)

        print("🎯 最佳语音片段推荐:")
        for i, seg in enumerate(best_segments[:3]):  # 显示前3个
            start_time = self._format_time(seg["start"])
            end_time = self._format_time(seg["end"])
            print(f"  {i + 1}. {start_time} - {end_time} "
                  f"(时长: {seg['duration']:.1f}s, 密度: {seg['word_density']:.1f} 词/秒)")
            print(f"     内容预览: {seg['text_preview']}")

        # 将最佳片段保存到时间戳数据中
        speech_timestamps["best_segments"] = best_segments

        return best_segments

    def transcribe_audio(self, audio_path):
        """语音识别 - 简化版，只保留句子级时间戳"""
        if not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在: {audio_path}")
            return ""

        try:
            # 优先使用Whisper（离线，更准确）
            if self.whisper_model:
                print("[+] 使用Whisper进行语音识别...")

                # 关键：启用word_timestamps参数获取时间戳
                result = self.whisper_model.transcribe(
                    audio_path,
                    word_timestamps=True,  # 启用词级时间戳
                    language='zh'  # 指定中文
                )

                # 提取完整文本
                full_text = result["text"].strip()
                print(f"[+] Whisper识别成功: {full_text[:100]}...")

                # **简化版：只显示句子级时间戳**
                print("\n🎙️ 语音识别句子级时间戳:")
                print("=" * 50)

                # **只处理segments（句子级别的时间戳），不处理words**
                simplified_segments = []
                for i, segment in enumerate(result["segments"]):
                    start_time = round(segment["start"], 2)
                    end_time = round(segment["end"], 2)
                    text = segment["text"].strip()

                    # 格式化时间显示
                    start_formatted = self._format_time(start_time)
                    end_formatted = self._format_time(end_time)

                    print(f"[{i + 1:2d}] {start_formatted} - {end_formatted} | {text}")

                    # **只保存句子级信息，不保存词级信息**
                    simplified_segments.append({
                        "start": start_time,
                        "end": end_time,
                        "text": text,
                        "duration": round(end_time - start_time, 2)
                    })

                print("=" * 50)

                # **简化的时间戳字典，只包含必要信息**
                timestamp_data = {
                    "full_text": full_text,
                    "segments": simplified_segments,  # 只保留句子级别
                    "total_duration": simplified_segments[-1]["end"] if simplified_segments else 0,
                    "segments_count": len(simplified_segments)
                }

                # 将简化的时间戳数据保存到实例中
                self.speech_timestamps = timestamp_data

                # 分析最佳语音片段
                self._analyze_speech_segments(timestamp_data)

                # **打印最终保存的时间戳数据大小（用于调试）**
                print(f"\n📊 时间戳数据摘要:")
                print(f"  - 句子数量: {len(simplified_segments)}")
                print(f"  - 总时长: {timestamp_data['total_duration']:.1f}秒")
                print(
                    f"  - 平均句长: {len(full_text) / len(simplified_segments) if simplified_segments else 0:.1f}字/句")

                if full_text:
                    return full_text
                else:
                    print("[!] Whisper识别结果为空")
            else:
                print("[!] Whisper模型不可用")

        except Exception as e:
            print(f"❌ Whisper识别失败: {e}")

        # Fallback到Google（保持原有兼容性）
        return self._fallback_google_recognition(audio_path)

    def _fallback_google_recognition(self, audio_path):
        """备用的Google识别"""
        try:
            print("[+] 尝试Google语音识别...")
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='zh-CN')
            print(f"[+] Google识别成功: {text[:50]}...")
            return text
        except Exception as e:
            print(f"❌ Google识别失败: {e}")
            return ""

    def analyze_background_music(self, audio_path):
        """背景音乐分析"""
        if not os.path.exists(audio_path):
            return {"tempo": 0, "energy": 0, "chroma_mean": 0}

        try:
            y, sr_rate = librosa.load(audio_path, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr_rate)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr_rate).mean()
            energy = np.mean(librosa.feature.rms(y=y))
            return {
                "tempo": round(float(tempo)),
                "energy": round(float(energy), 2),
                "chroma_mean": round(float(chroma), 2)
            }
        except Exception as e:
            print(f"❌ 音乐分析失败: {str(e)}")
            return {"tempo": 0, "energy": 0, "chroma_mean": 0}

    def detect_objects(self, video_path, conf=0.5):
        """对象检测"""
        try:
            if self.yolo_model is None:
                print("[+] 加载YOLO模型...")
                self.yolo_model = YOLO('yolov8n.pt')  # 使用轻量级模型

            results = self.yolo_model(video_path, stream=True, conf=conf)
            detected_objects = {}

            frame_count = 0
            max_frames = 30  # 只检测前30帧，提高速度

            for r in results:
                if frame_count >= max_frames:
                    break
                frame_count += 1

                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        cls = int(box.cls[0])
                        name = self.yolo_model.names[cls]
                        confidence = float(box.conf[0])

                        if name not in detected_objects:
                            detected_objects[name] = []
                        detected_objects[name].append(confidence)

            # 计算每个对象的平均置信度
            object_summary = {}
            for obj_name, confidences in detected_objects.items():
                object_summary[obj_name] = {
                    "count": len(confidences),
                    "avg_confidence": round(sum(confidences) / len(confidences), 2),
                    "max_confidence": round(max(confidences), 2)
                }

            return object_summary
        except Exception as e:
            print(f"❌ 对象检测失败: {str(e)}")
            return {}

    def detect_faces(self, video_path):
        """人脸检测"""
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            cap = cv2.VideoCapture(video_path)
            face_present = False

            frame_count = 0
            max_frames = 30  # 只检测前30帧

            while cap.isOpened() and frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    face_present = True
                    break
                frame_count += 1

            cap.release()
            return face_present
        except Exception as e:
            print(f"❌ 人脸检测失败: {str(e)}")
            return False

    def classify_video_content(self, analysis_report):
        """视频内容分类"""
        content_type = "unknown"
        mood = "neutral"
        structure = "linear"
        style = "standard"
        purpose = "general"

        speech_text = analysis_report.get("speech_text", "")
        has_face = analysis_report.get("face_detected", False)
        detected_objects = analysis_report.get("objects_detected", {})
        scene_changes = analysis_report.get("scene_changes", [])
        music_analysis = analysis_report.get("music_analysis", {})
        tempo = music_analysis.get("tempo", 0)
        duration = analysis_report.get("metadata", {}).get("duration", 0)

        # 1. 判断content_type
        if len(speech_text.strip()) > 0 or has_face:
            content_type = "人声剧情类"
            if 'person' in detected_objects:
                if duration > 1800:  # 30分钟以上
                    content_type = "直播录播类"
                elif any(keyword in speech_text for keyword in ["产品", "购买", "优惠", "课程", "教学", "培训"]):
                    content_type = "广告宣传片类"
                elif any(keyword in speech_text for keyword in ["教", "学", "步骤", "方法"]):
                    content_type = "教育教学类"
        else:
            content_type = "场景风景类"
            if any(obj in detected_objects for obj in ['car', 'bicycle', 'skateboard', 'sports ball']):
                content_type = "动作运动类"
            elif tempo > 100 and 'person' not in detected_objects:
                content_type = "音乐视频类"

        # 2. 判断mood
        if tempo > 120:
            mood = "激昂"
        elif tempo < 80 and len(scene_changes) < 5:
            mood = "宁静"
        elif any(keyword in speech_text for keyword in ["感动", "难过", "泪"]):
            mood = "感动"
        elif any(keyword in speech_text for keyword in ["危险", "紧急", "快", "限时", "马上", "立即"]):
            mood = "紧张"
        elif any(keyword in speech_text for keyword in ["开心", "快乐", "哈哈"]):
            mood = "欢快"

        # 3. 判断structure
        if len(scene_changes) > 20:
            structure = "板块拼接"
        elif len(scene_changes) > 10:
            structure = "多线并行"
        elif any(keyword in speech_text for keyword in ["回忆", "过去", "以前"]):
            structure = "回忆插叙"

        # 4. 判断style
        metadata = analysis_report.get("metadata", {})
        width = metadata.get("width", 1920)
        height = metadata.get("height", 1080)

        if height > width:  # 竖屏
            style = "抖音风"
        elif duration > 1800:  # 长视频
            style = "纪录片风"
        elif tempo > 120 and len(scene_changes) > 15:
            style = "抖音风"
        elif has_face and duration < 600:  # 有人脸且10分钟内
            style = "Vlog风"
        elif 'cinematic' in speech_text.lower():
            style = "电影感"

        # 5. 判断purpose
        if duration < 60:
            purpose = "社交媒体"
        elif any(keyword in speech_text for keyword in ["教程", "教你", "学习", "步骤"]):
            purpose = "教学培训"
        elif any(keyword in speech_text for keyword in ["产品", "公司", "品牌", "服务"]):
            purpose = "企业宣传"
        elif any(keyword in speech_text for keyword in ["旅行", "生活", "日常", "分享"]):
            purpose = "个人记录"

        return {
            "content_type": content_type,
            "mood": mood,
            "structure": structure,
            "style": style,
            "purpose": purpose
        }

    def generate_highlights(self, analysis_report):
        """生成精彩片段推荐"""
        highlights = []
        scene_changes = analysis_report.get("scene_changes", [])
        duration = analysis_report.get("metadata", {}).get("duration", 0)

        # 基于场景变化推荐精彩片段
        if scene_changes:
            # 选择前几个场景作为精彩片段
            for i, (start, end) in enumerate(scene_changes[:5]):
                highlights.append({
                    "start_time": start,
                    "end_time": end,
                    "duration": end - start,
                    "reason": f"场景 {i + 1}",
                    "confidence": 0.7
                })

        # 如果没有场景变化，按时间段推荐
        if not highlights and duration > 0:
            segment_duration = min(30, duration / 3)  # 每段最多30秒
            for i in range(3):
                start = i * (duration / 3)
                end = min(start + segment_duration, duration)
                if end > start:
                    highlights.append({
                        "start_time": start,
                        "end_time": end,
                        "duration": end - start,
                        "reason": f"时间段 {i + 1}",
                        "confidence": 0.5
                    })

        return highlights

    def _save_timestamps_to_file(self, video_path: str, analysis_result: dict):
        """保存简化的时间戳信息到文件"""
        timestamp_file = video_path.replace('.mkv', '_timestamps.json').replace('.mp4', '_timestamps.json')
        try:
            # **只保存必要的信息，避免文件过大**
            timestamp_data = {
                'video_path': video_path,
                'analysis_time': __import__('datetime').datetime.now().isoformat(),
                'speech_summary': {
                    'total_duration': analysis_result.get('speech_timestamps', {}).get('total_duration', 0),
                    'segments_count': analysis_result.get('speech_timestamps', {}).get('segments_count', 0),
                    'text_length': len(analysis_result.get('speech_text', ''))
                },
                'highlights': analysis_result.get('highlights', []),
                'classification': analysis_result.get('classification', {}),
                'best_segments': analysis_result.get('speech_timestamps', {}).get('best_segments', [])[:3]  # 只保存前3个最佳片段
            }

            with open(timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(timestamp_data, f, ensure_ascii=False, indent=2)
            print(f"[+] 简化时间戳信息已保存到: {timestamp_file}")
        except Exception as e:
            print(f"[!] 保存时间戳文件失败: {e}")

    def get_best_speech_segments(self, target_duration: int = 30):
        """获取最佳语音片段（供外部调用）"""
        if hasattr(self, 'speech_timestamps') and self.speech_timestamps:
            return self.speech_timestamps.get('best_segments', [])
        return []

    def analyze_video(self, video_path):
        """综合视频分析 - 简化输出版"""
        print(f"[+] 正在分析视频: {video_path}")

        print("[+] 正在提取基础信息...")
        metadata = self.get_video_metadata(video_path)
        if not metadata:
            raise ValueError("无法获取视频元数据")

        print("[+] 正在进行场景检测...")
        scenes = self.detect_scenes(video_path)

        print("[+] 提取音频并进行语音识别...")
        audio_path = self.extract_audio(video_path)
        speech_text = ""
        music_analysis = {"tempo": 120, "energy": 0.01, "chroma_mean": 0.3}

        if audio_path:
            speech_text = self.transcribe_audio(audio_path)  # 这里会生成简化的时间戳
            music_analysis = self.analyze_background_music(audio_path)
            # 清理临时音频文件
            try:
                os.remove(audio_path)
            except:
                pass
        else:
            print("[!] 无法提取音频，跳过语音相关分析")

        print("[+] 进行对象检测...")
        objects = self.detect_objects(video_path)

        print("[+] 检测是否有人脸...")
        has_face = self.detect_faces(video_path)

        # 构建简化的分析报告
        analysis_report = {
            "metadata": metadata,
            "scene_changes": scenes,
            "speech_text": speech_text,
            "speech_timestamps": getattr(self, 'speech_timestamps', {}),  # 简化的时间戳数据
            "music_analysis": music_analysis,
            "objects_detected": objects,
            "face_detected": has_face
        }

        # 进行内容分类
        print("[+] 进行内容分类...")
        classification = self.classify_video_content(analysis_report)
        analysis_report["classification"] = classification

        # 生成精彩片段
        highlights = self.generate_highlights(analysis_report)
        analysis_report["highlights"] = highlights

        # 保存简化的时间戳到文件
        self._save_timestamps_to_file(video_path, analysis_report)

        print("✅ 视频分析完成")

        # **简化输出：不显示完整的时间戳数据**
        print(f"\n📊 分析结果摘要:")
        print(f"  - 视频时长: {metadata.get('duration', 0):.1f}秒")
        print(f"  - 内容类型: {classification.get('content_type', '未知')}")
        print(f"  - 语音句子数: {len(analysis_report.get('speech_timestamps', {}).get('segments', []))}")
        print(f"  - 精彩片段数: {len(highlights)}")

        return analysis_report


# 便捷函数
def analyze_video(video_path):
    """快速分析单个视频的便捷函数"""
    analyzer = VideoAnalyzer()
    return analyzer.analyze_video(video_path)


def detect_videos(input_path):
    """快速检测视频文件"""
    analyzer = VideoAnalyzer()
    return analyzer.detect_videos(input_path)
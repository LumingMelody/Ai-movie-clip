"""
视频剪辑执行器
根据生成的时间轴JSON执行实际的视频剪辑操作
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, ImageClip, ColorClip
# MoviePy 2.x imports
try:
    from moviepy.video.fx.Resize import Resize
    from moviepy.video.fx.FadeIn import FadeIn
    from moviepy.video.fx.FadeOut import FadeOut
    from moviepy.video.fx.Rotate import Rotate
    from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
    from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
except ImportError:
    # Fallback for older versions
    from moviepy.video.fx import resize as Resize, fadein as FadeIn, fadeout as FadeOut, rotate as Rotate
    from moviepy.audio.fx import audio_fadein as AudioFadeIn, audio_fadeout as AudioFadeOut, volumex as MultiplyVolume
import numpy as np


class VideoEditor:
    """视频剪辑执行器"""
    
    def __init__(self, resource_dir: str = "./resources"):
        """
        初始化视频编辑器
        
        Args:
            resource_dir: 资源文件目录（视频、音频、图片等）
        """
        self.resource_dir = Path(resource_dir)
        self.logger = self._setup_logger()
        
        # 特效映射
        self.effect_mapping = {
            "blur": self._apply_blur,
            "glow": self._apply_glow,
            "particle": self._apply_particle,
            "fade": self._apply_fade,
            "zoom": self._apply_zoom,
            "rotate": self._apply_rotate,
            "shake": self._apply_shake,
            "color_correct": self._apply_color_correct
        }
        
        # 转场映射
        self.transition_mapping = {
            "fade_in": lambda clip, duration: clip.with_effects([FadeIn(duration)]),
            "fade_out": lambda clip, duration: clip.with_effects([FadeOut(duration)]),
            "cross_fade": self._cross_fade,
            "cut": lambda clip, duration: clip,  # 硬切
            "slide": self._slide_transition,
            "zoom": self._zoom_transition
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("VideoEditor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def execute_timeline(self, timeline_json: Dict, output_path: str) -> bool:
        """
        执行时间轴剪辑
        
        Args:
            timeline_json: 时间轴JSON数据
            output_path: 输出视频路径
            
        Returns:
            是否成功
        """
        try:
            self.logger.info("开始处理时间轴...")
            
            # 解析时间轴
            timeline = timeline_json.get("timeline", {})
            duration = timeline.get("duration", 60)
            fps = timeline.get("fps", 30)
            resolution = timeline.get("resolution", {"width": 1920, "height": 1080})
            
            # 处理各个轨道
            video_clips = []
            audio_clips = []
            text_clips = []
            
            for track in timeline.get("tracks", []):
                track_type = track.get("type")
                
                if track_type == "video":
                    video_clips.extend(self._process_video_track(track, resolution))
                elif track_type == "audio":
                    audio_clips.extend(self._process_audio_track(track))
                elif track_type == "text":
                    text_clips.extend(self._process_text_track(track, resolution))
            
            # 合成最终视频
            final_video = self._composite_video(video_clips, text_clips, audio_clips, duration, resolution, fps)
            
            # 输出视频
            self.logger.info(f"正在输出视频到: {output_path}")
            
            # 保存实际使用的时间轴到output目录
            import os
            output_dir = os.path.dirname(output_path)
            timeline_save_path = os.path.join(output_dir, "actual_timeline_used.json")
            try:
                with open(timeline_save_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(timeline_json, f, ensure_ascii=False, indent=2)
                self.logger.info(f"实际使用的时间轴已保存到: {timeline_save_path}")
            except Exception as e:
                self.logger.warning(f"保存时间轴失败: {e}")
            
            # 输出时间轴调试信息
            self.logger.info("=== 时间轴调试信息 ===")
            self.logger.info(f"视频时长: {duration}秒")
            self.logger.info(f"输出分辨率: {resolution['width']}x{resolution['height']}")
            self.logger.info(f"帧率: {fps}fps")
            self.logger.info(f"视频片段数量: {len(video_clips)}")
            self.logger.info(f"音频片段数量: {len(audio_clips)}")
            self.logger.info(f"文字片段数量: {len(text_clips)}")
            
            # 详细输出完整的时间轴信息
            self.logger.info("=== 完整时间轴内容 ===")
            for i, track in enumerate(timeline.get("tracks", [])):
                self.logger.info(f"轨道 {i}: 类型={track.get('type')}, 名称={track.get('name', 'N/A')}, 片段数={len(track.get('clips', []))}")
                for j, clip in enumerate(track.get("clips", [])):
                    clip_info = f"  片段 {j}: {clip.get('start', 0)}-{clip.get('end', 0)}秒"
                    if clip.get('source'):
                        clip_info += f", 源={clip.get('source')}"
                    if clip.get('content'):
                        content = clip.get('content')
                        if content.get('text'):
                            clip_info += f", 文字='{content.get('text')[:20]}...'"
                        if content.get('source'):
                            clip_info += f", 音频源={content.get('source')}"
                    if clip.get('filters'):
                        clip_info += f", 滤镜={clip.get('filters')}"
                    self.logger.info(clip_info)
            self.logger.info("====================")
            
            # 使用固定码率来确保质量
            ffmpeg_params = [
                '-b:v', '2000k',      # 视频码率2Mbps
                '-minrate', '1800k',  # 最小码率
                '-maxrate', '2200k',  # 最大码率  
                '-bufsize', '4000k',  # 缓冲区大小
                '-b:a', '128k',       # 音频码率128k
                '-preset:v', 'fast',  # 明确指定视频预设避免截断问题
                '-profile:v', 'high', # 使用高质量profile
                '-level:v', '4.0'     # H.264 level
            ]
            
            self.logger.info(f"使用ffmpeg参数: {' '.join(ffmpeg_params)}")
            
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                ffmpeg_params=ffmpeg_params,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None
            )
            
            # 清理资源
            final_video.close()
            
            self.logger.info("视频剪辑完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"视频剪辑失败: {e}")
            return False

    def _process_video_track(self, track: Dict, resolution: Dict) -> List:
        """处理视频轨道"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                # 获取视频源
                source = clip_data.get("source", "")
                if not source:
                    # 如果没有源文件，创建纯色片段
                    clip = self._create_color_clip(
                        duration=clip_data["end"] - clip_data["start"],
                        resolution=resolution,
                        color=(0, 0, 0)
                    )
                else:
                    # 加载视频文件
                    video_path = self.resource_dir / source
                    if video_path.exists():
                        clip = VideoFileClip(str(video_path))
                    else:
                        self.logger.warning(f"视频文件不存在: {video_path}")
                        continue
                
                # 裁剪片段
                try:
                    clip = clip.subclipped(
                        clip_data.get("clipIn", 0),
                        clip_data.get("clipOut", clip.duration)
                    )
                except AttributeError:
                    # Fallback for older MoviePy versions
                    clip = clip.subclip(
                        clip_data.get("clipIn", 0),
                        clip_data.get("clipOut", clip.duration)
                    )
                
                # 设置时间
                try:
                    clip = clip.with_start(clip_data["start"])
                    clip = clip.with_duration(clip_data["end"] - clip_data["start"])
                except AttributeError:
                    # Fallback for older MoviePy versions
                    clip = clip.set_start(clip_data["start"])
                    clip = clip.set_duration(clip_data["end"] - clip_data["start"])
                
                # 应用变换
                transform = clip_data.get("transform", {})
                clip = self._apply_transform(clip, transform, resolution)
                
                # 应用滤镜（跳过滤镜应用以避免fx错误）
                filters = clip_data.get("filters", [])
                if filters:
                    self.logger.info(f"跳过滤镜应用: {filters}（避免fx兼容性问题）")
                
                # 应用转场
                if clip_data.get("transition_in"):
                    clip = self._apply_transition(clip, clip_data["transition_in"], "in")
                if clip_data.get("transition_out"):
                    clip = self._apply_transition(clip, clip_data["transition_out"], "out")
                
                # 设置透明度
                if "opacity" in clip_data:
                    try:
                        clip = clip.with_opacity(clip_data["opacity"])
                    except AttributeError:
                        # Fallback for older MoviePy versions
                        clip = clip.set_opacity(clip_data["opacity"])
                
                clips.append(clip)
                
            except Exception as e:
                self.logger.error(f"处理视频片段失败: {e}")
                continue
        
        return clips

    def _process_audio_track(self, track: Dict) -> List:
        """处理音频轨道"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                content = clip_data.get("content", {})
                source = content.get("source", "")
                
                if not source:
                    continue
                
                # 加载音频文件
                audio_path = self.resource_dir / source
                if audio_path.exists():
                    clip = AudioFileClip(str(audio_path))
                else:
                    self.logger.warning(f"音频文件不存在: {audio_path}")
                    continue
                
                # 裁剪片段
                try:
                    clip = clip.subclipped(
                        clip_data.get("clipIn", 0),
                        min(clip_data.get("clipOut", clip.duration), clip.duration)
                    )
                except AttributeError:
                    # Fallback for older MoviePy versions
                    clip = clip.subclip(
                        clip_data.get("clipIn", 0),
                        min(clip_data.get("clipOut", clip.duration), clip.duration)
                    )
                
                # 设置音量
                volume = content.get("volume", 1.0)
                if volume != 1.0:
                    clip = clip.with_effects([MultiplyVolume(volume)])
                
                # 循环处理
                if content.get("loop", False):
                    duration = clip_data["end"] - clip_data["start"]
                    clip = clip.loop(duration=duration)
                
                # 设置时间
                clip = clip.set_start(clip_data["start"])
                
                # 淡入淡出
                fade_in = content.get("fade_in", 0)
                fade_out = content.get("fade_out", 0)
                if fade_in > 0:
                    clip = clip.with_effects([AudioFadeIn(fade_in)])
                if fade_out > 0:
                    clip = clip.with_effects([AudioFadeOut(fade_out)])
                
                clips.append(clip)
                
            except Exception as e:
                self.logger.error(f"处理音频片段失败: {e}")
                continue
        
        return clips

    def _process_text_track(self, track: Dict, resolution: Dict) -> List:
        """处理文字轨道"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                content = clip_data.get("content", {})
                
                # 创建文字片段
                try:
                    # MoviePy 2.x 中的 TextClip 参数（使用正确的参数名）
                    text_clip = TextClip(
                        text=content.get("text", ""),
                        color=content.get("color", "white"),
                        font_size=content.get("size", 50),
                        font=content.get("font", "Arial")
                    )
                except Exception as e:
                    self.logger.warning(f"TextClip创建失败，尝试备用方案: {e}")
                    try:
                        # 备用方案：只使用基本参数
                        text_clip = TextClip(
                            text=content.get("text", ""),
                            color=content.get("color", "white"),
                            font_size=content.get("size", 50)
                        )
                    except Exception as e2:
                        self.logger.error(f"TextClip创建完全失败，跳过文字: {e2}")
                        continue
                
                # 设置位置
                position = content.get("position", "bottom")
                try:
                    if position == "center":
                        text_clip = text_clip.with_position("center")
                    elif position == "bottom":
                        text_clip = text_clip.with_position(("center", resolution["height"] - 100))
                    elif position == "top":
                        text_clip = text_clip.with_position(("center", 50))
                    elif isinstance(position, (list, tuple)):
                        text_clip = text_clip.with_position(position)
                except AttributeError:
                    # Fallback for older MoviePy versions
                    if position == "center":
                        text_clip = text_clip.set_position("center")
                    elif position == "bottom":
                        text_clip = text_clip.set_position(("center", resolution["height"] - 100))
                    elif position == "top":
                        text_clip = text_clip.set_position(("center", 50))
                    elif isinstance(position, (list, tuple)):
                        text_clip = text_clip.set_position(position)
                
                # 设置持续时间
                duration = clip_data["end"] - clip_data["start"]
                try:
                    text_clip = text_clip.with_duration(duration)
                    text_clip = text_clip.with_start(clip_data["start"])
                except AttributeError:
                    # Fallback for older MoviePy versions
                    text_clip = text_clip.set_duration(duration)
                    text_clip = text_clip.set_start(clip_data["start"])
                
                # 应用动画
                animation = content.get("animation", "")
                if animation == "fade_in":
                    text_clip = text_clip.with_effects([FadeIn(0.5)])
                elif animation == "slide_in":
                    text_clip = self._slide_in_text(text_clip)
                
                # 应用滤镜（跳过滤镜应用以避免fx错误）
                filters = clip_data.get("filters", [])
                if filters:
                    self.logger.info(f"跳过文字滤镜应用: {filters}（避免fx兼容性问题）")
                
                clips.append(text_clip)
                
            except Exception as e:
                self.logger.error(f"处理文字片段失败: {e}")
                continue
        
        return clips

    def _composite_video(self, video_clips: List, text_clips: List, audio_clips: List, 
                        duration: float, resolution: Dict, fps: int):
        """合成最终视频"""
        # 创建背景
        background = self._create_color_clip(duration, resolution, (0, 0, 0))
        
        # 合并所有视频片段
        all_clips = [background] + video_clips + text_clips
        
        # 创建合成视频
        final_video = CompositeVideoClip(all_clips, size=(resolution["width"], resolution["height"]))
        
        # 合并音频
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            try:
                final_video = final_video.with_audio(final_audio)
            except AttributeError:
                # Fallback for older MoviePy versions
                final_video = final_video.set_audio(final_audio)
        
        return final_video

    def _create_color_clip(self, duration: float, resolution: Dict, color: Tuple[int, int, int]):
        """创建纯色片段"""
        return ColorClip(
            size=(resolution["width"], resolution["height"]),
            color=color,
            duration=duration
        )

    def _apply_transform(self, clip, transform: Dict, resolution: Dict):
        """应用变换"""
        # 缩放
        scale = transform.get("scale", 1.0)
        if scale != 1.0:
            try:
                # 计算目标尺寸
                target_width = int(resolution["width"] * scale)
                target_height = int(resolution["height"] * scale)
                clip = clip.with_effects([Resize((target_width, target_height))])
            except Exception as e:
                self.logger.warning(f"缩放失败: {e}")
        
        # 位置
        position = transform.get("position", ["center", "center"])
        if position != ["center", "center"]:
            try:
                clip = clip.with_position(position)
            except AttributeError:
                # Fallback for older MoviePy versions
                clip = clip.set_position(position)
        
        # 旋转
        rotation = transform.get("rotation", 0)
        if rotation != 0:
            try:
                clip = clip.with_effects([Rotate(rotation)])
            except Exception as e:
                self.logger.warning(f"旋转失败: {e}")
        
        return clip

    def _apply_filter(self, clip, filter_name: str):
        """应用滤镜效果"""
        # 解析滤镜名称和强度
        parts = filter_name.split("_")
        if len(parts) >= 2:
            effect_type = parts[0]
            try:
                intensity = int(parts[1]) / 10.0  # 转换为0-1的强度
            except:
                intensity = 1.0
        else:
            effect_type = filter_name
            intensity = 1.0
        
        # 应用对应的效果
        if effect_type in self.effect_mapping:
            return self.effect_mapping[effect_type](clip, intensity)
        else:
            self.logger.warning(f"未知的滤镜效果: {effect_type}")
            return clip

    def _apply_transition(self, clip, transition: Dict, direction: str):
        """应用转场效果"""
        transition_type = transition.get("type", "fade")
        duration = transition.get("duration", 1.0)
        
        if transition_type in self.transition_mapping:
            if direction == "in":
                return self.transition_mapping[transition_type](clip, duration)
            else:  # out
                # 对于淡出效果，需要特殊处理
                if transition_type == "fade_out":
                    return clip.with_effects([FadeOut(duration)])
                else:
                    return clip
        else:
            self.logger.warning(f"未知的转场效果: {transition_type}")
            return clip

    # 特效实现
    def _apply_blur(self, clip, intensity: float):
        """应用模糊效果"""
        # MoviePy没有内置模糊，这里用简单的resize实现
        blur_factor = 1 - (intensity * 0.5)  # 最多缩小到50%
        if blur_factor < 1.0:
            small = clip.with_effects([Resize(blur_factor)])
            return small.with_effects([Resize(clip.size)])
        return clip

    def _apply_glow(self, clip, intensity: float):
        """应用光晕效果"""
        # 简单的亮度增强模拟光晕
        return clip.fx(lambda frame: np.clip(frame * (1 + intensity * 0.5), 0, 255).astype('uint8'))

    def _apply_particle(self, clip, intensity: float):
        """应用粒子效果"""
        # 这里需要更复杂的实现，暂时返回原片段
        return clip

    def _apply_fade(self, clip, intensity: float):
        """应用淡入淡出"""
        fade_duration = intensity
        return clip.with_effects([FadeIn(fade_duration), FadeOut(fade_duration)])

    def _apply_zoom(self, clip, intensity: float):
        """应用缩放效果"""
        scale = 1 + intensity * 0.5
        return clip.with_effects([Resize(scale)])

    def _apply_rotate(self, clip, intensity: float):
        """应用旋转效果"""
        angle = intensity * 360
        return clip.with_effects([Rotate(angle)])

    def _apply_shake(self, clip, intensity: float):
        """应用震动效果"""
        # 简单的位置偏移模拟震动
        def shake_effect(get_frame, t):
            frame = get_frame(t)
            if intensity > 0:
                # 随机偏移
                offset_x = int(np.random.randint(-5, 5) * intensity)
                offset_y = int(np.random.randint(-5, 5) * intensity)
                # 这里需要更复杂的实现
            return frame
        
        return clip.fl(shake_effect)

    def _apply_color_correct(self, clip, intensity: float):
        """应用色彩校正"""
        # 简单的对比度和亮度调整
        def color_correct(frame):
            # 增加对比度
            contrast = 1 + intensity * 0.5
            # 调整亮度
            brightness = 1 + intensity * 0.2
            
            frame = frame * contrast
            frame = frame + brightness * 10
            
            return np.clip(frame, 0, 255).astype('uint8')
        
        return clip.fl_image(color_correct)

    # 转场效果实现
    def _cross_fade(self, clip1, clip2, duration: float):
        """交叉淡化转场"""
        # 这个需要两个片段，暂时简化处理
        return clip1.with_effects([FadeIn(duration)])

    def _slide_transition(self, clip, duration: float):
        """滑动转场"""
        # 简化实现
        return clip

    def _zoom_transition(self, clip, duration: float):
        """缩放转场"""
        # 简化实现
        return clip

    def _slide_in_text(self, text_clip):
        """文字滑入动画"""
        # 从右侧滑入
        w, h = text_clip.size
        
        def slide_pos(t):
            if t < 0.5:
                # 滑入阶段
                progress = t / 0.5
                x = w + (1 - progress) * w
                return (x, "center")
            else:
                return ("center", "center")
        
        try:
            return text_clip.with_position(slide_pos)
        except AttributeError:
            # Fallback for older MoviePy versions
            return text_clip.set_position(slide_pos)


def main():
    """测试视频编辑器"""
    # 读取时间轴JSON
    with open("output/final_timeline.json", "r", encoding="utf-8") as f:
        timeline_json = json.load(f)
    
    # 创建编辑器
    editor = VideoEditor(resource_dir="./resources")
    
    # 执行剪辑
    success = editor.execute_timeline(timeline_json, "output/final_video.mp4")
    
    if success:
        print("视频剪辑成功！")
    else:
        print("视频剪辑失败！")


if __name__ == "__main__":
    main()
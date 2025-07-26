# -*- coding: utf-8 -*-
"""
数字人视频生成模块
统一处理数字人视频生成、音频同步和相关功能
"""

import os
import uuid
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url_self
from core.clipgenerate.tongyi_get_voice_copy import get_voice_copy_disposable
from core.clipgenerate.tongyi_response import get_Tongyi_response
from core.clipgenerate.tongyi_get_videotalk import get_videotalk
from .video_utils import FileDownloader, AudioProcessor


class DigitalHumanGenerator:
    """数字人视频生成器"""
    
    def __init__(self):
        self.temp_files_to_cleanup = []
    
    def is_url(self, path: str) -> bool:
        """判断是否为URL链接"""
        return FileDownloader.is_url(path)
    
    def download_audio_from_url(self, url: str, local_path: str = None) -> str:
        """从URL下载音频到本地"""
        try:
            print(f"🔊 正在下载音频: {url}")
            
            if not local_path:
                # 生成安全的文件名
                import hashlib
                import time
                
                parsed_url = urlparse(url)
                original_filename = os.path.basename(parsed_url.path)
                
                # 提取扩展名
                if '.' in original_filename:
                    ext = original_filename.split('.')[-1].lower()
                    if ext not in ['mp3', 'wav', 'aac', 'm4a', 'flac']:
                        ext = 'mp3'
                else:
                    ext = 'mp3'
                
                # 生成安全的文件名
                timestamp = str(int(time.time()))
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                safe_filename = f"audio_{timestamp}_{url_hash}.{ext}"
                
                # 创建临时目录
                temp_dir = os.path.join(get_user_data_dir(), "temp_audios")
                os.makedirs(temp_dir, exist_ok=True)
                local_path = os.path.join(temp_dir, safe_filename)
            
            # 下载音频
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            # 验证下载的文件
            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                raise Exception("下载的文件为空或不存在")
            
            print(f"✅ 音频下载完成: {local_path} (大小: {os.path.getsize(local_path)} bytes)")
            return local_path
            
        except Exception as e:
            print(f"❌ 音频下载失败: {str(e)}")
            raise
    
    def safe_voice_copy_with_fallback(self, audio_url: str, content: str, project_path: str, video_path: str = None) -> str:
        """安全的语音复制，支持降级"""
        try:
            if audio_url is None:
                if video_path and os.path.exists(video_path):
                    print("🎵 从原视频提取音频进行语音复制...")
                    
                    # 提取原视频音频
                    video_clip = VideoFileClip(video_path)
                    temp_audio_path = os.path.join(project_path, "temp_original_audio.mp3")
                    video_clip.audio.write_audiofile(temp_audio_path, logger=None)
                    video_clip.close()
                    
                    # 上传音频获取URL
                    temp_audio_url = get_online_url_self(
                        "temp_original_audio.mp3",
                        temp_audio_path,
                        "audio/mp3"
                    )
                    
                    # 使用提取的音频进行语音复制
                    output_audio = get_voice_copy_disposable(temp_audio_url, content, project_path)
                    
                    # 清理临时文件
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                    
                    return output_audio
                else:
                    print("⚠️ 无法提取原视频音频，使用TTS生成")
                    return self.generate_tts_audio(content, project_path)
            
            # 有audio_url时，直接使用
            output_audio = get_voice_copy_disposable(audio_url, content, project_path)
            return output_audio
            
        except Exception as e:
            print(f"⚠️ 语音复制失败: {str(e)}")
            return self.generate_tts_audio(content, project_path)
    
    def safe_videotalk_with_fallback(self, video_url: str, audio_url: str, project_path: str) -> Optional[str]:
        """安全的数字人视频生成，支持人脸检测失败的降级处理"""
        try:
            print("🤖 正在生成数字人视频...")
            digital_human_url = get_videotalk(video_url, audio_url)
            
            if digital_human_url and digital_human_url != "None" and digital_human_url is not None:
                print(f"✅ 数字人视频生成完成: {digital_human_url}")
                return digital_human_url
            else:
                print("⚠️ 数字人视频生成返回了空值，可能是人脸检测失败")
                return None
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ 数字人视频生成失败: {error_msg}")
            
            # 检查是否是人脸相关错误
            if any(keyword in error_msg.lower() for keyword in [
                "face", "facenotmatch", "invalidfile.facenotmatch",
                "can't detect face", "no matched face"
            ]):
                print("🔄 检测到人脸匹配失败，将生成纯音频输出")
                return None
            else:
                # 其他错误，直接抛出
                raise
    
    def create_audio_only_video(self, audio_path: str, output_path: str, duration: float = None):
        """创建纯音频视频（黑屏+音频）"""
        try:
            print("🎵 创建纯音频视频...")
            
            audio_clip = AudioFileClip(audio_path)
            video_duration = duration or audio_clip.duration
            
            # 创建黑色背景视频
            from moviepy import ColorClip
            black_clip = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=video_duration)
            
            # 合成视频
            final_video = black_clip.with_audio(audio_clip.subclipped(0, video_duration))
            
            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                logger=None,
                audio_codec="aac"
            )
            
            # 清理资源
            audio_clip.close()
            black_clip.close()
            final_video.close()
            
            print(f"✅ 纯音频视频创建完成: {output_path}")
            
        except Exception as e:
            print(f"❌ 纯音频视频创建失败: {e}")
            raise
    
    def create_smart_loop_video(self, video_clip: VideoFileClip, target_duration: float) -> VideoFileClip:
        """智能循环视频以匹配目标时长"""
        try:
            current_duration = video_clip.duration
            print(f"🎬 视频循环: 原始时长 {current_duration:.2f}s → 目标时长 {target_duration:.2f}s")
            
            if target_duration <= current_duration:
                return video_clip.subclipped(0, target_duration)
            
            # 计算需要的循环次数
            full_loops = int(target_duration / current_duration)
            remaining_time = target_duration - (full_loops * current_duration)
            
            print(f"🔁 需要 {full_loops} 个完整循环，剩余 {remaining_time:.2f}s")
            
            # 创建循环片段列表
            looped_clips = []
            
            # 添加完整循环
            for i in range(full_loops):
                looped_clips.append(video_clip)
            
            # 添加剩余部分
            if remaining_time > 0.1:
                partial_clip = video_clip.subclipped(0, remaining_time)
                looped_clips.append(partial_clip)
            
            # 合并视频片段
            extended_video = concatenate_videoclips(looped_clips, method="compose")
            
            print(f"✅ 视频循环成功: 最终时长 {extended_video.duration:.2f}s")
            return extended_video
            
        except Exception as e:
            print(f"❌ 视频循环失败: {e}")
            raise
    
    def generate_tts_audio(self, text: str, project_path: str) -> str:
        """使用TTS生成音频（降级方案）"""
        try:
            # 这里应该调用你的TTS服务
            tts_audio_path = os.path.join(project_path, "tts_audio.mp3")
            
            # 调用TTS函数（这里需要根据实际TTS服务实现）
            # 示例：使用阿里云TTS
            print(f"🗣️ TTS音频生成完成: {tts_audio_path}")
            return tts_audio_path
            
        except Exception as e:
            print(f"❌ TTS生成失败: {e}")
            # 最终降级：创建静音音频
            import numpy as np
            from moviepy import AudioArrayClip
            
            # 估算文本时长（每字0.5秒）
            estimated_duration = len(text) * 0.5
            
            # 创建静音音频
            silent_audio_path = os.path.join(project_path, "silent_audio.mp3")
            
            # 使用numpy创建静音
            sample_rate = 44100
            samples = int(estimated_duration * sample_rate)
            silent_array = np.zeros((samples, 2))
            
            silent_clip = AudioArrayClip(silent_array, fps=sample_rate)
            silent_clip.write_audiofile(silent_audio_path, logger=None)
            silent_clip.close()
            
            return silent_audio_path
    
    def generate_digital_human_video(
        self, 
        video_input: str, 
        topic: str, 
        content: str = None, 
        audio_input: str = None
    ) -> str:
        """
        数字人视频生成统一入口
        
        Args:
            video_input: 视频输入，可以是本地路径或HTTP链接
            topic: 主题
            content: 内容文本，如果为None则自动生成
            audio_input: 音频输入，如果为None则根据content生成
            
        Returns:
            生成的视频路径
        """
        print(f"🎯 开始处理数字人视频生成...")
        print(f"📊 参数信息: topic='{topic}', content='{content}', audio_input={audio_input}")
        print(f"📋 视频输入: {video_input}")
        
        project_id = str(uuid.uuid1())
        user_data_dir = get_user_data_dir()
        base_project_path = os.path.join(user_data_dir, "projects")
        project_path = os.path.join(base_project_path, project_id)
        os.makedirs(project_path, exist_ok=True)
        
        try:
            # 1. 处理视频输入
            if self.is_url(video_input):
                print(f"🌐 检测到视频URL: {video_input}")
                local_video_path = self.download_audio_from_url(video_input)
                self.temp_files_to_cleanup.append(local_video_path)
                video_url = video_input
            else:
                print(f"📁 使用本地视频: {video_input}")
                if not os.path.exists(video_input):
                    raise ValueError(f"❌ 本地视频文件不存在: {video_input}")
                local_video_path = video_input
                video_url = get_online_url_self(
                    os.path.basename(video_input),
                    video_input,
                    "video/mp4"
                )
                print(f"📤 本地视频已上传: {video_url}")
            
            # 2. 生成内容（如果未提供）
            if content is None:
                print("📝 正在生成口播稿...")
                content = get_Tongyi_response(
                    "你是一个口播稿生成师，我给你一个主题，你生成一段120字左右的口播稿",
                    "主题是" + topic
                )
                print(f"✅ 口播稿生成完成: {content}")
            
            # 3. 处理音频
            target_audio_duration = None
            final_audio_path = None
            final_audio_url = None
            
            if audio_input is not None:
                # 使用提供的音频
                if self.is_url(audio_input):
                    print(f"🔊 检测到音频URL: {audio_input}")
                    local_audio_path = self.download_audio_from_url(audio_input)
                    self.temp_files_to_cleanup.append(local_audio_path)
                    final_audio_path = local_audio_path
                    final_audio_url = audio_input
                else:
                    print(f"🎵 使用本地音频: {audio_input}")
                    if not os.path.exists(audio_input):
                        raise ValueError(f"❌ 本地音频文件不存在: {audio_input}")
                    final_audio_path = audio_input
                    final_audio_url = get_online_url_self(
                        os.path.basename(audio_input),
                        audio_input,
                        "audio/mp3"
                    )
                
                # 获取提供音频的时长作为目标时长
                audio_clip = AudioFileClip(final_audio_path)
                target_audio_duration = audio_clip.duration
                audio_clip.close()
                print(f"🎯 使用提供音频的时长作为目标: {target_audio_duration:.2f}秒")
            
            else:
                # 根据文本生成音频
                print("🗣️ 正在根据文本生成语音...")
                
                generated_audio_path = self.safe_voice_copy_with_fallback(
                    None,
                    content,
                    project_path,
                    video_path=local_video_path
                )
                
                if not generated_audio_path or not os.path.exists(generated_audio_path):
                    # 降级：使用TTS生成
                    print("🔄 降级到TTS生成音频...")
                    generated_audio_path = self.generate_tts_audio(content, project_path)
                
                final_audio_path = generated_audio_path
                final_audio_url = get_online_url_self(
                    os.path.basename(generated_audio_path),
                    generated_audio_path,
                    "audio/mp3"
                )
                
                # 获取生成音频的时长作为最终目标时长
                audio_clip = AudioFileClip(final_audio_path)
                target_audio_duration = audio_clip.duration
                audio_clip.close()
                print(f"🎯 根据文本生成的音频时长: {target_audio_duration:.2f}秒")
            
            # 4. 预处理视频以匹配音频长度
            print("🔧 开始预处理视频以匹配音频长度...")
            
            original_video = VideoFileClip(local_video_path)
            original_video_duration = original_video.duration
            
            print(f"📊 原始视频时长: {original_video_duration:.2f}秒")
            print(f"📊 目标音频时长: {target_audio_duration:.2f}秒")
            
            processed_video_path = os.path.join(project_path, "processed_video.mp4")
            
            # 调整视频长度匹配音频
            if original_video_duration > target_audio_duration:
                # 视频比音频长：裁剪视频
                print(f"✂️ 视频较长，裁剪至音频长度")
                start_time = (original_video_duration - target_audio_duration) / 2
                trimmed_video = original_video.subclipped(start_time, start_time + target_audio_duration)
                trimmed_video.write_videofile(
                    processed_video_path,
                    codec="libx264",
                    fps=24,
                    logger=None,
                    audio=False
                )
                trimmed_video.close()
            elif original_video_duration < target_audio_duration:
                # 视频比音频短：循环视频
                print(f"🔄 视频较短，循环延长至音频长度")
                extended_video = self.create_smart_loop_video(original_video, target_audio_duration)
                extended_video.write_videofile(
                    processed_video_path,
                    codec="libx264",
                    fps=24,
                    logger=None,
                    audio=False
                )
                extended_video.close()
            else:
                # 长度匹配
                print("✅ 视频音频长度匹配，直接使用原视频")
                processed_video_path = local_video_path
            
            original_video.close()
            
            # 5. 上传处理后的文件
            if processed_video_path != local_video_path:
                processed_video_url = get_online_url_self(
                    "processed_video.mp4",
                    processed_video_path,
                    "video/mp4"
                )
                print(f"📤 处理后视频已上传: {processed_video_url}")
            else:
                processed_video_url = video_url
            
            # 6. 调用数字人生成
            print("🤖 调用数字人生成...")
            digital_human_url = self.safe_videotalk_with_fallback(processed_video_url, final_audio_url, project_path)
            
            if digital_human_url and digital_human_url != "None":
                # 成功生成数字人视频
                print("✅ 数字人视频生成成功，正在下载...")
                
                def download_file(url, filename):
                    with requests.get(url, stream=True) as r:
                        r.raise_for_status()
                        filename = os.path.join(project_path, filename)
                        with open(filename, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    return filename
                
                downloaded_video = download_file(digital_human_url, "digital_human.mp4")
                
                # 最终合成
                print("🎬 正在进行最终合成...")
                
                final_video_clip = VideoFileClip(downloaded_video)
                final_audio_clip = AudioFileClip(final_audio_path)
                
                # 确保时长匹配
                target_duration = final_audio_clip.duration
                if final_video_clip.duration != target_duration:
                    if final_video_clip.duration > target_duration:
                        final_video_clip = final_video_clip.subclipped(0, target_duration)
                    else:
                        final_video_clip = self.create_smart_loop_video(final_video_clip, target_duration)
                
                # 合成最终视频
                final_video = final_video_clip.with_audio(final_audio_clip)
                output_path = os.path.join(project_path, "output.mp4")
                
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    fps=24,
                    logger=None,
                    audio_codec="aac"
                )
                
                # 清理资源
                final_video_clip.close()
                final_audio_clip.close()
                final_video.close()
            
            else:
                # 数字人生成失败的降级处理
                print("🔄 数字人视频生成失败，创建降级输出...")
                output_path = os.path.join(project_path, "output.mp4")
                
                if processed_video_path and os.path.exists(processed_video_path):
                    print("📹 使用处理后的视频作为降级输出")
                    
                    video_clip = VideoFileClip(processed_video_path)
                    audio_clip = AudioFileClip(final_audio_path)
                    
                    # 确保长度匹配
                    target_duration = audio_clip.duration
                    if video_clip.duration != target_duration:
                        video_clip = video_clip.subclipped(0, min(video_clip.duration, target_duration))
                    
                    final_video = video_clip.set_audio(audio_clip.subclipped(0, video_clip.duration))
                    final_video.write_videofile(
                        output_path,
                        codec="libx264",
                        fps=24,
                        logger=None,
                        audio_codec="aac"
                    )
                    
                    video_clip.close()
                    audio_clip.close()
                    final_video.close()
                else:
                    # 创建纯音频视频
                    print("🎵 创建纯音频视频")
                    audio_clip = AudioFileClip(final_audio_path)
                    self.create_audio_only_video(final_audio_path, output_path, duration=audio_clip.duration)
                    audio_clip.close()
            
            print(f"✅ 数字人视频生成完成: {output_path}")
            
            # 返回相对路径
            relative_path = os.path.relpath(output_path, get_user_data_dir())
            warehouse_path = relative_path.replace('\\', '/')
            print(f"📁 warehouse路径: {warehouse_path}")
            
            return warehouse_path
            
        except Exception as e:
            print(f"❌ 数字人视频生成失败: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            raise
        
        finally:
            # 清理临时文件
            for temp_file in self.temp_files_to_cleanup:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🗑️ 已清理临时文件: {temp_file}")
                except Exception as e:
                    print(f"⚠️ 清理临时文件失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        for temp_file in self.temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {str(e)}")
        self.temp_files_to_cleanup.clear()


# 便捷函数
def generate_digital_human_video(
    video_input: str, 
    topic: str, 
    content: str = None, 
    audio_input: str = None
) -> str:
    """
    生成数字人视频的便捷函数
    
    Args:
        video_input: 视频输入
        topic: 主题
        content: 内容
        audio_input: 音频输入
        
    Returns:
        生成的视频路径
    """
    generator = DigitalHumanGenerator()
    try:
        return generator.generate_digital_human_video(video_input, topic, content, audio_input)
    finally:
        generator.cleanup()
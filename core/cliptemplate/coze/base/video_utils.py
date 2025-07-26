# -*- coding: utf-8 -*-
"""
视频处理工具模块
统一处理视频下载、音频加载、文件管理等常用功能
"""

import os
import subprocess
import tempfile
import hashlib
import time
from typing import Optional, List, Union
from urllib.parse import urlparse
import requests
from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image


class FileDownloader:
    """文件下载器"""
    
    @staticmethod
    def download_file(url: str, filename: str, save_dir: str, timeout: int = 30) -> str:
        """
        下载文件到指定目录
        
        Args:
            url: 文件URL
            filename: 保存的文件名
            save_dir: 保存目录
            timeout: 超时时间（秒）
            
        Returns:
            保存的文件路径
        """
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        
        if os.path.exists(save_path):
            print(f"📁 文件已存在: {save_path}")
            return save_path
        
        try:
            print(f"⬇️ 开始下载: {url}")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 下载完成: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ 下载失败: {url}, 错误: {e}")
            raise
    
    @staticmethod
    def is_url(path: str) -> bool:
        """判断是否为URL链接"""
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def download_image_from_url(url: str, local_path: str = None) -> str:
        """
        从URL下载图片到本地
        
        Args:
            url: 图片URL
            local_path: 本地保存路径（可选）
            
        Returns:
            本地文件路径
        """
        try:
            print(f"🌐 正在下载图片: {url}")
            
            # 如果没有指定本地路径，创建临时文件
            if not local_path:
                # 生成安全的文件名
                parsed_url = urlparse(url)
                original_filename = os.path.basename(parsed_url.path)
                
                # 提取扩展名
                if '.' in original_filename:
                    ext = original_filename.split('.')[-1].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                        ext = 'jpg'
                else:
                    ext = 'jpg'
                
                # 生成安全的文件名：使用时间戳+哈希
                timestamp = str(int(time.time()))
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                safe_filename = f"image_{timestamp}_{url_hash}.{ext}"
                
                # 创建临时目录
                temp_dir = os.path.join(tempfile.gettempdir(), "temp_images")
                os.makedirs(temp_dir, exist_ok=True)
                local_path = os.path.join(temp_dir, safe_filename)
            
            # 下载图片
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            # 验证下载的文件
            if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
                raise Exception("下载的文件为空或不存在")
            
            # 验证文件是否为有效图片
            try:
                with Image.open(local_path) as img:
                    img.verify()
                print(f"✅ 图片验证通过: {local_path} (大小: {os.path.getsize(local_path)} bytes)")
            except Exception as e:
                print(f"⚠️ 图片验证警告: {str(e)}")
            
            print(f"✅ 图片下载完成: {local_path}")
            return local_path
            
        except Exception as e:
            print(f"❌ 图片下载失败: {str(e)}")
            raise
    
    @staticmethod
    def validate_and_convert_image(image_path: str) -> str:
        """
        验证并转换图片格式
        确保图片格式被正确处理
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise Exception(f"图片文件不存在: {image_path}")
            
            # 打开并验证图片
            with Image.open(image_path) as img:
                print(f"📸 原始图片信息 - 格式: {img.format}, 尺寸: {img.size}, 模式: {img.mode}")
                
                # 如果图片格式不是JPEG，转换为JPEG
                if img.format.upper() not in ['JPEG', 'JPG']:
                    print(f"🔄 转换图片格式: {img.format} -> JPEG")
                    
                    # 如果是RGBA模式，转换为RGB
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 生成新的文件路径
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    new_path = os.path.join(os.path.dirname(image_path), f"{base_name}_converted.jpg")
                    
                    # 保存为JPEG格式
                    img.save(new_path, 'JPEG', quality=95)
                    print(f"✅ 图片转换完成: {new_path}")
                    
                    # 删除原文件（如果是临时文件）
                    if "temp_images" in image_path:
                        try:
                            os.remove(image_path)
                            print(f"🗑️ 已删除原始临时文件: {image_path}")
                        except:
                            pass
                    
                    return new_path
                else:
                    print("✅ 图片格式已是JPEG，无需转换")
                    return image_path
                    
        except Exception as e:
            print(f"❌ 图片验证/转换失败: {str(e)}")
            return image_path  # 返回原始路径，让后续流程处理


class AudioProcessor:
    """音频处理器"""
    
    @staticmethod
    def safe_load_audio(audio_path: str) -> Optional[AudioFileClip]:
        """
        安全加载音频文件，处理各种格式问题
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            AudioFileClip对象，失败时返回None
        """
        if not audio_path or not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在: {audio_path}")
            return None
        
        try:
            # 方法1：直接加载
            print(f"🎵 尝试直接加载音频: {audio_path}")
            return AudioFileClip(audio_path)
        except Exception as e1:
            print(f"⚠️ 直接加载音频失败: {e1}")
            
            try:
                # 方法2：使用ffmpeg重新编码
                temp_path = audio_path.replace('.mp3', '_fixed.mp3')
                print(f"🔄 尝试重新编码音频: {temp_path}")
                
                # 重新编码音频文件，去除章节信息
                cmd = [
                    'ffmpeg', '-i', audio_path,
                    '-c:a', 'libmp3lame',  # 使用mp3编码
                    '-b:a', '128k',  # 设置比特率
                    '-ar', '44100',  # 设置采样率
                    '-ac', '2',  # 设置声道数
                    '-map_chapters', '-1',  # 去除章节信息
                    '-y',  # 覆盖输出文件
                    temp_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print(f"✅ 音频重新编码成功: {temp_path}")
                    return AudioFileClip(temp_path)
                else:
                    print(f"❌ FFmpeg重新编码失败: {result.stderr}")
            except Exception as e2:
                print(f"⚠️ 重新编码音频失败: {e2}")
            
            try:
                # 方法3：使用pydub转换
                print("🔄 尝试使用pydub转换...")
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_path)
                temp_wav = audio_path.replace('.mp3', '_temp.wav')
                audio.export(temp_wav, format="wav")
                return AudioFileClip(temp_wav)
            except Exception as e3:
                print(f"⚠️ Pydub转换失败: {e3}")
            
            # 如果所有方法都失败，返回None
            print(f"❌ 所有音频加载方法都失败，跳过音频文件: {audio_path}")
            return None


class VideoClipManager:
    """视频片段管理器"""
    
    @staticmethod
    def get_video_files(folder_path: str, extensions: tuple = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')) -> List[str]:
        """从指定文件夹下读取所有视频文件"""
        try:
            if not os.path.exists(folder_path):
                print(f"❌ 目录不存在: {folder_path}")
                return []
            return [f for f in os.listdir(folder_path) if f.lower().endswith(extensions)]
        except Exception as e:
            print(f"❌ 读取视频文件失败: {e}")
            return []
    
    @staticmethod
    def select_random_videos(video_files: List[str], num_to_select: int) -> List[str]:
        """从中随机挑选若干个视频文件，增加安全检查"""
        import random
        
        if not video_files:
            return []
        
        # 确保选择数量不为负数且不超过可用文件数量
        actual_num = max(0, min(num_to_select, len(video_files)))
        
        if actual_num == 0:
            return []
        
        return random.sample(video_files, actual_num)
    
    @staticmethod
    def resolve_materials(source: Union[str, List[str]], valid_extensions: tuple) -> List[str]:
        """
        解析素材路径（支持文件/文件夹）
        
        Args:
            source: 素材源（文件路径、文件夹路径或路径列表）
            valid_extensions: 有效的文件扩展名
            
        Returns:
            解析后的文件路径列表
        """
        if not source:
            return []
        
        if isinstance(source, str):
            source = [source]
        
        resolved_files = []
        for item in source:
            item = os.path.abspath(item)
            
            if os.path.isfile(item) and item.lower().endswith(valid_extensions):
                resolved_files.append(item)
            elif os.path.isdir(item):
                try:
                    resolved_files.extend([
                        os.path.join(item, f) for f in os.listdir(item)
                        if os.path.isfile(os.path.join(item, f)) and f.lower().endswith(valid_extensions)
                    ])
                except Exception as e:
                    print(f"⚠️ 读取目录失败: {item}, 错误: {e}")
        
        return resolved_files
    
    @staticmethod
    def smart_clip_duration(video_clip: VideoFileClip, target_duration: float) -> VideoFileClip:
        """
        智能调整视频片段时长
        
        Args:
            video_clip: 视频片段
            target_duration: 目标时长
            
        Returns:
            调整后的视频片段
        """
        import random
        from moviepy import vfx
        
        current_duration = video_clip.duration
        
        if current_duration > target_duration:
            # 视频比目标时长长：随机选择起始点进行裁剪
            max_start = current_duration - target_duration - 0.1
            start_time = random.uniform(0, max(0, max_start))
            return video_clip.subclipped(start_time, start_time + target_duration)
        
        elif current_duration < target_duration:
            # 视频比目标时长短：循环播放
            try:
                loop_count = max(1, int(target_duration / current_duration) + 1)
                looped_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * current_duration)])
                return looped_clip.subclipped(0, target_duration)
            except:
                # 如果Loop不可用，手动循环
                print("⚠️ Loop效果不可用，使用手动循环")
                clips_needed = int(target_duration / current_duration) + 1
                looped_clips = [video_clip] * clips_needed
                return concatenate_videoclips(looped_clips).subclipped(0, target_duration)
        
        else:
            # 时长匹配
            return video_clip


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, user_data_dir: str):
        self.user_data_dir = user_data_dir
        self.temp_files = []  # 跟踪临时文件用于清理
    
    def create_project_directory(self, project_id: str) -> str:
        """创建项目目录"""
        project_path = os.path.join(self.user_data_dir, "projects", project_id)
        os.makedirs(project_path, exist_ok=True)
        print(f"📂 项目目录: {project_path}")
        return project_path
    
    def create_materials_directory(self, subdir: str) -> str:
        """创建素材目录"""
        materials_path = os.path.join(self.user_data_dir, "materials", subdir)
        os.makedirs(materials_path, exist_ok=True)
        return materials_path
    
    def add_temp_file(self, file_path: str):
        """添加临时文件到清理列表"""
        self.temp_files.append(file_path)
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {temp_file}, 错误: {e}")
        self.temp_files.clear()
    
    def get_relative_path(self, full_path: str) -> str:
        """获取相对于用户数据目录的路径"""
        try:
            relative_path = os.path.relpath(full_path, self.user_data_dir)
            return relative_path.replace('\\', '/')
        except Exception:
            return full_path


# 便捷函数
def download_file(url: str, filename: str, save_dir: str) -> str:
    """下载文件（便捷函数）"""
    return FileDownloader.download_file(url, filename, save_dir)

def safe_load_audio(audio_path: str) -> Optional[AudioFileClip]:
    """安全加载音频（便捷函数）"""
    return AudioProcessor.safe_load_audio(audio_path)

def resolve_video_materials(source: Union[str, List[str]]) -> List[str]:
    """解析视频素材（便捷函数）"""
    extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
    return VideoClipManager.resolve_materials(source, extensions)

def smart_clip_duration(video_clip: VideoFileClip, target_duration: float) -> VideoFileClip:
    """智能调整视频时长（便捷函数）"""
    return VideoClipManager.smart_clip_duration(video_clip, target_duration)
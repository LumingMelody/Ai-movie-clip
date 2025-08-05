# -*- coding: utf-8 -*-
"""
统一的视频处理器
重构transform目录下的所有视频处理逻辑，消除代码重复
"""

import os
import sys
import uuid
import platform
import warnings
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

# MoviePy相关导入
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, CompositeAudioClip,
    afx, vfx
)
from moviepy.tools import close_all_clips

# 内部导入 
from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url
from core.clipgenerate.tongyi_get_videotalk import get_videotalk

# 忽略MoviePy的资源清理警告
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")


class FontManager:
    """统一的字体管理器"""
    
    def __init__(self):
        self._font_cache = {}
        self._font_paths = self._discover_font_paths()
    
    def _get_script_directory(self) -> str:
        """获取脚本所在目录（适配exe打包）"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))
    
    def _discover_font_paths(self) -> List[str]:
        """发现字体路径"""
        script_dir = self._get_script_directory()
        font_paths = []
        
        # 1. 脚本同级目录
        font_paths.append(script_dir)
        
        # 2. 用户数据目录
        try:
            user_data_dir = get_user_data_dir()
            font_paths.append(os.path.join(user_data_dir, "fonts"))
        except:
            pass
        
        # 3. 系统字体目录
        system_paths = self._get_system_font_paths()
        font_paths.extend(system_paths)
        
        return font_paths
    
    def _get_system_font_paths(self) -> List[str]:
        """获取系统字体目录"""
        system = platform.system()
        
        if system == "Windows":
            return [
                "C:/Windows/Fonts/",
                "C:/Windows/System32/Fonts/",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
            ]
        elif system == "Darwin":  # macOS
            return [
                "/System/Library/Fonts/",
                "/Library/Fonts/",
                os.path.expanduser("~/Library/Fonts/")
            ]
        else:  # Linux
            return [
                "/usr/share/fonts/",
                "/usr/local/share/fonts/",
                os.path.expanduser("~/.fonts/"),
                os.path.expanduser("~/.local/share/fonts/")
            ]
    
    def find_font(self, preferred_fonts: List[str] = None) -> Optional[str]:
        """查找字体文件"""
        if preferred_fonts is None:
            preferred_fonts = ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"]
        
        # 优先使用缓存
        cache_key = ",".join(preferred_fonts)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # 搜索字体
        for font_path in self._font_paths:
            if not os.path.exists(font_path):
                continue
            
            for font_name in preferred_fonts:
                full_path = os.path.join(font_path, font_name)
                if os.path.exists(full_path):
                    print(f"✅ 找到字体: {full_path}")
                    self._font_cache[cache_key] = full_path
                    return full_path
        
        print(f"⚠️ 未找到合适的字体文件")
        return None
    
    def get_default_font(self) -> Optional[str]:
        """获取默认字体"""
        return self.find_font()


class TextClipCreator:
    """文本片段创建器"""
    
    def __init__(self, font_manager: FontManager):
        self.font_manager = font_manager
        self.default_font = self.font_manager.get_default_font()
    
    def create_text_clip_safe(self, text: str, duration: float, 
                             is_title: bool = False, **kwargs) -> TextClip:
        """安全创建文本片段"""
        try:
            # 默认参数
            default_params = {
                'fontsize': 80 if is_title else 60,
                'color': 'white',
                'bg_color': (0, 0, 0, 128) if not is_title else None,
                'method': 'caption',
                'align': 'center',
                'font': self.default_font
            }
            
            # 合并用户参数
            params = {**default_params, **kwargs}
            
            # 移除None值
            params = {k: v for k, v in params.items() if v is not None}
            
            # 创建文本片段
            text_clip = TextClip(
                text=text,
                duration=duration,
                **params
            )
            
            return text_clip
            
        except Exception as e:
            print(f"⚠️ 文本片段创建失败: {e}")
            # 降级处理 - 使用基本参数
            try:
                return TextClip(
                    text=text,
                    duration=duration,
                    fontsize=60,
                    color='white'
                )
            except Exception as e2:
                print(f"❌ 文本片段降级处理也失败: {e2}")
                # 返回空的颜色片段作为占位符
                return ImageClip(color=(0, 0, 0), duration=duration, size=(1280, 100))


class ResourceDownloader:
    """资源下载器"""
    
    @staticmethod
    def download_file(url: str, filename: str, save_dir: str) -> str:
        """下载文件"""
        import requests
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, filename)
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 文件下载成功: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 文件下载失败: {e}")
            raise
    
    @staticmethod
    def safe_load_audio(audio_path: str) -> Optional[AudioFileClip]:
        """安全加载音频"""
        try:
            if not os.path.exists(audio_path):
                print(f"⚠️ 音频文件不存在: {audio_path}")
                return None
            
            audio_clip = AudioFileClip(audio_path)
            if audio_clip.duration <= 0:
                print(f"⚠️ 音频文件无效: {audio_path}")
                return None
            
            return audio_clip
            
        except Exception as e:
            print(f"⚠️ 音频加载失败: {e}")
            return None


class VideoClipManager:
    """视频片段管理器"""
    
    @staticmethod
    def smart_clip_duration(video_clip: VideoFileClip, target_duration: float) -> VideoFileClip:
        """智能调整视频时长"""
        if video_clip.duration <= target_duration:
            # 视频太短，循环播放
            try:
                return video_clip.with_effects([afx.AudioLoop(duration=target_duration)])
            except:
                # 手动循环
                from moviepy import concatenate_videoclips
                repeats = int(target_duration / video_clip.duration) + 1
                clips = [video_clip] * repeats
                return concatenate_videoclips(clips).subclipped(0, target_duration)
        else:
            # 视频太长，裁剪
            return video_clip.subclipped(0, target_duration)
    
    @staticmethod
    def get_video_files(directory: str) -> List[str]:
        """获取目录下的视频文件"""
        if not os.path.exists(directory):
            return []
        
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
        files = []
        
        for file in os.listdir(directory):
            if file.lower().endswith(video_extensions):
                files.append(file)
        
        return sorted(files)
    
    @staticmethod
    def resolve_video_materials(data: Dict[str, Any]) -> Dict[str, str]:
        """解析视频素材路径"""
        materials = {}
        
        # 从数据中提取素材信息
        if 'video_materials' in data:
            materials.update(data['video_materials'])
        
        # 默认素材目录
        default_dirs = {
            'moderator': './materials/moderator/',
            'enterprise': './materials/enterprise/',
            'background': './materials/background/'
        }
        
        for key, default_path in default_dirs.items():
            if key not in materials and os.path.exists(default_path):
                materials[key] = default_path
        
        return materials


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.temp_files = []
    
    def create_project_directory(self, project_id: str) -> str:
        """创建项目目录"""
        project_path = os.path.join(self.base_dir, "projects", project_id)
        os.makedirs(project_path, exist_ok=True)
        return project_path
    
    def create_materials_directory(self, subdir: str) -> str:
        """创建素材目录"""
        materials_path = os.path.join(self.base_dir, "materials", subdir)
        os.makedirs(materials_path, exist_ok=True)
        return materials_path
    
    def get_relative_path(self, full_path: str) -> str:
        """获取相对路径"""
        try:
            return os.path.relpath(full_path, self.base_dir)
        except:
            return full_path
    
    def add_temp_file(self, file_path: str):
        """添加临时文件"""
        self.temp_files.append(file_path)
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"✅ 清理临时文件: {file_path}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {e}")
        
        self.temp_files.clear()


class BaseVideoProcessor(ABC):
    """视频处理器基类"""
    
    def __init__(self, user_data_dir: str = None):
        self.user_data_dir = user_data_dir or get_user_data_dir()
        
        # 初始化组件
        self.font_manager = FontManager()
        self.text_creator = TextClipCreator(self.font_manager)
        self.resource_downloader = ResourceDownloader()
        self.video_manager = VideoClipManager()
        
        # 项目管理
        self.project_id = str(uuid.uuid1())
        self.project_manager = ProjectManager(self.user_data_dir)
        self.project_path = self.project_manager.create_project_directory(self.project_id)
        
        # 资源跟踪
        self.video_clips = []
        self.audio_clips = []
        self.temp_files = []
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> str:
        """处理视频 - 子类必须实现"""
        pass
    
    def download_resources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """下载基础资源"""
        resources = {}
        
        try:
            # 下载背景图
            if 'data' in data and data['data']:
                bg_path = self.resource_downloader.download_file(
                    data['data'], "background.png", self.project_path
                )
                resources['background'] = bg_path
                print(f"✅ 背景图下载完成: {bg_path}")
            
            # 下载音频文件
            if 'audio_urls' in data and data['audio_urls']:
                audio_paths = []
                for i, url in enumerate(data['audio_urls']):
                    audio_path = self.resource_downloader.download_file(
                        url, f"audio_{i}.mp3", self.project_path
                    )
                    audio_clip = self.resource_downloader.safe_load_audio(audio_path)
                    if audio_clip:
                        self.audio_clips.append(audio_clip)
                        audio_paths.append(audio_path)
                        print(f"✅ 音频 {i} 下载完成: {audio_path}")
                resources['audio_paths'] = audio_paths
            
            # 下载背景音乐
            if 'bgm' in data and data['bgm']:
                bgm_path = self.resource_downloader.download_file(
                    data['bgm'], "bgm.mp3", self.project_path
                )
                bgm_clip = self.resource_downloader.safe_load_audio(bgm_path)
                if bgm_clip:
                    resources['bgm_clip'] = bgm_clip
                    resources['bgm_path'] = bgm_path
                    print(f"✅ 背景音乐下载完成: {bgm_path}")
            
        except Exception as e:
            print(f"⚠️ 资源下载警告: {e}")
        
        return resources
    
    def create_text_clip(self, text: str, duration: float, is_title: bool = False) -> TextClip:
        """创建文本片段"""
        return self.text_creator.create_text_clip_safe(text, duration, is_title)
    
    def process_background_music(self, bgm_clip: AudioFileClip, 
                               final_video: VideoFileClip, volume: float = 0.3) -> CompositeAudioClip:
        """处理背景音乐"""
        try:
            # 调整背景音乐长度匹配视频
            if bgm_clip.duration < final_video.duration:
                try:
                    bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
                except:
                    # 手动循环
                    from moviepy import concatenate_audioclips
                    loops_needed = int(final_video.duration / bgm_clip.duration) + 1
                    bgm_clips = [bgm_clip] * loops_needed
                    bgm_clip = concatenate_audioclips(bgm_clips).subclipped(0, final_video.duration)
            else:
                bgm_clip = bgm_clip.subclipped(0, final_video.duration)
            
            # 混合音频
            try:
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.with_effects([afx.MultiplyVolume(volume)])
                ])
            except:
                # 如果MultiplyVolume不可用，使用volumex
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.volumex(volume)
                ])
            
            return final_audio
            
        except Exception as e:
            print(f"❌ 音频混合失败: {e}")
            return final_video.audio
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理视频片段
            for clip in self.video_clips:
                try:
                    clip.close()
                except:
                    pass
            
            # 清理音频片段
            for clip in self.audio_clips:
                try:
                    clip.close()
                except:
                    pass
            
            # 清理临时文件
            self.project_manager.cleanup_temp_files()
            
            # 使用MoviePy的全局清理
            close_all_clips()
            
            print("🗑️ 资源清理完成")
            
        except Exception as e:
            print(f"⚠️ 资源清理失败: {e}")


class AdvertisementVideoProcessor(BaseVideoProcessor):
    """广告视频处理器"""
    
    def __init__(self, use_digital_host: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.use_digital_host = use_digital_host
    
    def process(self, data: Dict[str, Any]) -> str:
        """处理广告视频"""
        try:
            print(f"🎬 [广告视频] 开始处理，项目id: {self.project_id}")
            
            # 1. 下载资源
            resources = self.download_resources(data)
            
            # 2. 创建视频片段
            video_clips = self._create_video_clips(data, resources)
            self.video_clips.extend(video_clips)
            
            # 3. 拼接视频
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # 4. 处理背景音乐
            if 'bgm_clip' in resources:
                final_audio = self.process_background_music(resources['bgm_clip'], final_video)
                final_video = final_video.with_audio(final_audio)
            
            # 5. 输出视频
            output_path = os.path.join(self.project_path, "final_video.mp4")
            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                audio_codec="aac",
                threads=4,
                logger='bar'
            )
            
            # 6. 返回相对路径
            relative_path = self.project_manager.get_relative_path(output_path)
            print(f"✅ [广告视频] 处理完成: {relative_path}")
            
            return relative_path
            
        except Exception as e:
            print(f"❌ [广告视频] 处理失败: {str(e)}")
            raise
        finally:
            self.cleanup()
    
    def _create_video_clips(self, data: Dict[str, Any], resources: Dict[str, Any]) -> List[VideoFileClip]:
        """创建视频片段"""
        video_clips = []
        
        # 设置素材目录
        materials = self.video_manager.resolve_video_materials(data)
        
        # 获取背景图
        bg_image_path = resources.get('background')
        if not bg_image_path or not os.path.exists(bg_image_path):
            raise FileNotFoundError("背景图片未找到")
        
        bg_image = ImageClip(bg_image_path)
        
        # 处理数字人视频（如果启用）
        start_clip = end_clip = None
        if self.use_digital_host:
            # 数字人处理逻辑
            pass
        
        # 创建视频片段
        for i, (text, audio_clip) in enumerate(zip(data["output"], self.audio_clips)):
            print(f"🎬 创建第 {i + 1} 个片段...")
            
            bg = bg_image.with_duration(audio_clip.duration)
            text_clip = self.create_text_clip(text, audio_clip.duration)
            
            composite = CompositeVideoClip([
                bg,
                text_clip.with_position(("center", "center"))
            ]).with_audio(audio_clip)
            
            video_clips.append(composite)
            print(f"✅ 第 {i + 1} 个片段创建完成")
        
        return video_clips


class BigWordVideoProcessor(BaseVideoProcessor):
    """大字视频处理器"""
    
    def process(self, data: Dict[str, Any]) -> str:
        """处理大字视频"""
        try:
            print(f"📝 [大字视频] 开始处理")
            
            # 实现大字视频的具体处理逻辑
            # 这里可以复用广告视频的基本逻辑，但有不同的样式
            resources = self.download_resources(data)
            
            # 创建特定于大字视频的片段
            video_clips = self._create_big_word_clips(data, resources)
            self.video_clips.extend(video_clips)
            
            # 拼接和输出
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            output_path = os.path.join(self.project_path, "big_word_video.mp4")
            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                audio_codec="aac",
                threads=4,
                logger='bar'
            )
            
            relative_path = self.project_manager.get_relative_path(output_path)
            print(f"✅ [大字视频] 处理完成: {relative_path}")
            
            return relative_path
            
        except Exception as e:
            print(f"❌ [大字视频] 处理失败: {str(e)}")
            raise
        finally:
            self.cleanup()
    
    def _create_big_word_clips(self, data: Dict[str, Any], resources: Dict[str, Any]) -> List[VideoFileClip]:
        """创建大字视频片段"""
        # 大字视频特定的处理逻辑
        # 这里需要实现具体的大字效果
        return []


# 工厂模式
class VideoProcessorFactory:
    """视频处理器工厂"""
    
    _processors = {
        'advertisement': AdvertisementVideoProcessor,
        'big_word': BigWordVideoProcessor,
        # 可以继续添加其他处理器
    }
    
    @classmethod
    def create_processor(cls, processor_type: str, **kwargs) -> BaseVideoProcessor:
        """创建视频处理器实例"""
        if processor_type not in cls._processors:
            raise ValueError(f"不支持的处理器类型: {processor_type}")
        
        processor_class = cls._processors[processor_type]
        return processor_class(**kwargs)
    
    @classmethod
    def register_processor(cls, name: str, processor_class: type):
        """注册新的处理器类型"""
        cls._processors[name] = processor_class


# 统一的处理入口
def process_video_unified(processor_type: str, data: Dict[str, Any], **kwargs) -> str:
    """
    统一的视频处理入口
    
    Args:
        processor_type: 处理器类型
        data: 处理数据
        **kwargs: 额外参数
        
    Returns:
        处理后的视频路径
    """
    print(f"🚀 [统一处理器] 开始处理 {processor_type} 视频")
    
    processor = VideoProcessorFactory.create_processor(processor_type, **kwargs)
    result = processor.process(data)
    
    print(f"🎉 [统一处理器] {processor_type} 视频处理完成: {result}")
    return result


# 向后兼容函数
def trans_videos_advertisement(data: Dict[str, Any]) -> str:
    """广告视频转换 - 兼容性函数"""
    return process_video_unified('advertisement', data)


def trans_video_big_word(data: Dict[str, Any]) -> str:
    """大字视频转换 - 兼容性函数"""
    return process_video_unified('big_word', data)


if __name__ == "__main__":
    print("🔧 统一视频处理器模块加载完成")
    print("支持的处理器类型:")
    for proc_type in VideoProcessorFactory._processors.keys():
        print(f"  - {proc_type}")

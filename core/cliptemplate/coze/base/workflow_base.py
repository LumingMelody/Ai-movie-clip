# -*- coding: utf-8 -*-
"""
工作流基础类模块
为不同类型的视频生成工作流提供统一的基础框架
"""

import os
import uuid
import warnings
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, CompositeAudioClip,
    afx
)
from moviepy.tools import close_all_clips

from config import get_user_data_dir
from .coze_client import CozeClient
from .font_manager import FontManager, TextClipCreator, check_font_environment
from .video_utils import (
    FileDownloader, AudioProcessor, VideoClipManager, ProjectManager,
    download_file, safe_load_audio, resolve_video_materials
)
from .digital_human import DigitalHumanGenerator

# 忽略 MoviePy 的资源清理警告
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")


class BaseVideoWorkflow(ABC):
    """视频工作流基础类"""
    
    def __init__(self, user_data_dir: str = None):
        """
        初始化基础工作流
        
        Args:
            user_data_dir: 用户数据目录，如果为None则使用默认配置
        """
        self.user_data_dir = user_data_dir or get_user_data_dir()
        
        # 初始化组件
        self.font_manager = FontManager()
        self.text_creator = TextClipCreator(self.font_manager)
        self.coze_client = CozeClient()
        self.file_downloader = FileDownloader()
        self.audio_processor = AudioProcessor()
        self.video_manager = VideoClipManager()
        self.digital_human = DigitalHumanGenerator()
        
        # 项目管理
        self.project_id = str(uuid.uuid1())
        self.project_manager = ProjectManager(self.user_data_dir)
        self.project_path = self.project_manager.create_project_directory(self.project_id)
        
        # 资源跟踪
        self.video_clips = []
        self.audio_clips = []
        self.temp_files = []
        
        # 初始化字体环境
        check_font_environment()
    
    @abstractmethod
    def get_workflow_id(self) -> str:
        """获取Coze工作流ID"""
        pass
    
    @abstractmethod
    def prepare_workflow_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备工作流参数"""
        pass
    
    @abstractmethod
    def process_workflow_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """处理工作流响应"""
        pass
    
    @abstractmethod
    def create_video_clips(self, data: Dict[str, Any]) -> List[VideoFileClip]:
        """创建视频片段"""
        pass
    
    def setup_materials_directories(self, subdirs: List[str]) -> Dict[str, str]:
        """
        设置素材目录
        
        Args:
            subdirs: 子目录列表，如 ['moderator', 'enterprise']
            
        Returns:
            目录路径字典
        """
        directories = {}
        for subdir in subdirs:
            directories[subdir] = self.project_manager.create_materials_directory(subdir)
        return directories
    
    def download_resources(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        下载基础资源
        
        Args:
            data: 包含资源URL的数据
            
        Returns:
            下载后的本地路径字典
        """
        resources = {}
        
        # 下载背景图
        if 'data' in data and data['data']:
            try:
                bg_path = download_file(data['data'], "background.png", self.project_path)
                resources['background'] = bg_path
                print(f"✅ 背景图下载完成: {bg_path}")
            except Exception as e:
                print(f"⚠️ 背景图下载失败: {e}")
        
        # 下载音频文件
        if 'audio_urls' in data and data['audio_urls']:
            audio_paths = []
            for i, url in enumerate(data['audio_urls']):
                try:
                    audio_path = download_file(url, f"audio_{i}.mp3", self.project_path)
                    audio_clip = safe_load_audio(audio_path)
                    if audio_clip:
                        self.audio_clips.append(audio_clip)
                        audio_paths.append(audio_path)
                        print(f"✅ 音频 {i} 下载完成: {audio_path}")
                    else:
                        print(f"⚠️ 音频 {i} 加载失败: {audio_path}")
                except Exception as e:
                    print(f"⚠️ 音频 {i} 下载失败: {e}")
            resources['audio_paths'] = audio_paths
        
        # 下载背景音乐
        if 'bgm' in data and data['bgm']:
            try:
                bgm_path = download_file(data['bgm'], "bgm.mp3", self.project_path)
                bgm_clip = safe_load_audio(bgm_path)
                if bgm_clip:
                    resources['bgm_clip'] = bgm_clip
                    resources['bgm_path'] = bgm_path
                    print(f"✅ 背景音乐下载完成: {bgm_path}")
                else:
                    print(f"⚠️ 背景音乐加载失败")
            except Exception as e:
                print(f"⚠️ 背景音乐下载失败: {e}")
        
        return resources
    
    def create_text_clip(self, text: str, duration: float, is_title: bool = False) -> TextClip:
        """创建文本片段"""
        return self.text_creator.create_text_clip_safe(text, duration, is_title)
    
    def process_background_music(self, bgm_clip: AudioFileClip, final_video: VideoFileClip, volume: float = 0.3) -> CompositeAudioClip:
        """
        处理背景音乐
        
        Args:
            bgm_clip: 背景音乐片段
            final_video: 最终视频
            volume: 背景音乐音量（0-1）
            
        Returns:
            合成后的音频
        """
        try:
            # 调整背景音乐长度匹配视频
            if bgm_clip.duration < final_video.duration:
                try:
                    bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
                except:
                    # 手动循环
                    print("⚠️ AudioLoop不可用，使用手动循环")
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
                print("⚠️ MultiplyVolume不可用，使用volumex")
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.volumex(volume)
                ])
            
            print("✅ 背景音乐混合成功")
            return final_audio
            
        except Exception as e:
            print(f"❌ 音频混合失败: {e}")
            print("使用原始音频...")
            return final_video.audio
    
    def generate_video(self, data: Dict[str, Any], **kwargs) -> str:
        """
        生成视频的主要流程
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            生成的视频路径（相对路径）
        """
        try:
            print(f"🎬 开始生成视频，项目ID: {self.project_id}")
            
            # 1. 下载基础资源
            print("📥 下载基础资源...")
            resources = self.download_resources(data)
            
            # 2. 调用Coze工作流（如果需要）
            if hasattr(self, 'use_coze_workflow') and self.use_coze_workflow:
                print("🚀 调用Coze工作流...")
                workflow_params = self.prepare_workflow_parameters(data)
                workflow_response = self.coze_client.run_workflow(self.get_workflow_id(), workflow_params)
                processed_data = self.process_workflow_response(workflow_response)
                data.update(processed_data)
            
            # 3. 创建视频片段
            print("🎞️ 创建视频片段...")
            video_clips = self.create_video_clips(data)
            self.video_clips.extend(video_clips)
            
            # 4. 拼接视频
            print("🔗 拼接视频片段...")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # 5. 处理背景音乐
            if 'bgm_clip' in resources:
                print("🎵 处理背景音乐...")
                final_audio = self.process_background_music(resources['bgm_clip'], final_video)
                final_video = final_video.with_audio(final_audio)
            
            # 6. 输出视频
            output_path = os.path.join(self.project_path, "final_video.mp4")
            print(f"💾 开始生成视频: {output_path}")
            
            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                audio_codec="aac",
                threads=4,
                logger='bar'
            )
            
            # 7. 返回相对路径
            relative_path = self.project_manager.get_relative_path(output_path)
            print(f"✅ 视频生成完成: {relative_path}")
            
            return relative_path
            
        except Exception as e:
            print(f"❌ 视频生成失败: {str(e)}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            raise
        
        finally:
            # 清理资源
            self.cleanup()
    
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
            self.digital_human.cleanup()
            
            # 使用MoviePy的全局清理
            close_all_clips()
            
            print("🗑️ 资源清理完成")
            
        except Exception as e:
            print(f"⚠️ 资源清理失败: {e}")


class AdvertisementWorkflow(BaseVideoWorkflow):
    """广告视频工作流"""
    
    def __init__(self, use_digital_host: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.use_digital_host = use_digital_host
        self.use_coze_workflow = True
    
    def get_workflow_id(self) -> str:
        return '7499113029830049819'
    
    def prepare_workflow_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "company_name": data.get("company_name", ""),
            "service": data.get("service", ""),
            "topic": data.get("topic", ""),
            "content": data.get("content"),
            "need_change": data.get("need_change", False)
        }
    
    def process_workflow_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # 这里处理Coze工作流的响应
        return response
    
    def create_video_clips(self, data: Dict[str, Any]) -> List[VideoFileClip]:
        """创建广告视频片段"""
        video_clips = []
        
        # 设置素材目录
        materials = self.setup_materials_directories(['moderator', 'enterprise'])
        
        # 获取背景图
        bg_image_path = os.path.join(self.project_path, "background.png")
        if not os.path.exists(bg_image_path):
            raise FileNotFoundError("背景图片未找到")
        
        bg_image = ImageClip(bg_image_path)
        
        # 处理数字人视频（如果启用）
        start_clip = end_clip = None
        if self.use_digital_host:
            moderator_files = self.video_manager.get_video_files(materials['moderator'])
            if moderator_files:
                import random
                from core.clipgenerate.tongyi_get_online_url import get_online_url
                from core.clipgenerate.tongyi_get_videotalk import get_videotalk
                
                selected_host = random.choice([os.path.join(materials['moderator'], f) for f in moderator_files])
                host_url, _ = get_online_url(selected_host)
                
                # 生成开场和结尾数字人视频
                start_url = get_videotalk(host_url, data["audio_urls"][0])
                end_url = get_videotalk(host_url, data["audio_urls"][-1])
                
                start_clip = VideoFileClip(download_file(start_url, "start.mp4", self.project_path))
                end_clip = VideoFileClip(download_file(end_url, "end.mp4", self.project_path))
        
        # 获取企业素材
        enterprise_files = self.video_manager.get_video_files(materials['enterprise'])
        
        # 创建视频片段
        for i, (text, audio_clip) in enumerate(zip(data["output"], self.audio_clips)):
            print(f"🎬 创建第 {i + 1} 个片段...")
            
            bg = bg_image.with_duration(audio_clip.duration)
            
            if self.use_digital_host:
                if i == 0:
                    # 开场片段
                    company_name = data.get("company_name", "公司名称")
                    title_clip = self.create_text_clip(company_name, audio_clip.duration, is_title=True)
                    text_clip = self.create_text_clip(text, audio_clip.duration)
                    
                    composite = CompositeVideoClip([
                        bg,
                        start_clip.with_position(("center", "center")),
                        title_clip.with_position(("center", 0.2), relative=True),
                        text_clip.with_position(("center", 0.8), relative=True)
                    ]).with_audio(audio_clip)
                
                elif i == len(data["output"]) - 1:
                    # 结尾片段
                    text_clip = self.create_text_clip(text, audio_clip.duration)
                    
                    composite = CompositeVideoClip([
                        bg,
                        end_clip.with_position(("center", "center")),
                        text_clip.with_position(("center", 0.8), relative=True)
                    ]).with_audio(audio_clip)
                
                else:
                    # 中间片段（企业视频）
                    enterprise_video_index = i - 1
                    
                    if enterprise_video_index < len(enterprise_files):
                        # 处理企业视频
                        video_path = os.path.join(materials['enterprise'], enterprise_files[enterprise_video_index])
                        video_clip = VideoFileClip(video_path).resized((1280, 720))
                        
                        # 调整视频时长
                        video_clip = self.video_manager.smart_clip_duration(video_clip, audio_clip.duration)
                        text_clip = self.create_text_clip(text, audio_clip.duration)
                        
                        composite = CompositeVideoClip([
                            bg,
                            video_clip.with_position(("center", "center")),
                            text_clip.with_position(("center", 0.8), relative=True)
                        ]).with_audio(audio_clip)
                    else:
                        # 没有足够的企业视频，使用背景图片
                        text_clip = self.create_text_clip(text, audio_clip.duration)
                        composite = CompositeVideoClip([
                            bg,
                            text_clip.with_position(("center", "center"), relative=True)
                        ]).with_audio(audio_clip)
            else:
                # 不使用数字人
                text_clip = self.create_text_clip(text, audio_clip.duration)
                composite = CompositeVideoClip([
                    bg,
                    text_clip.with_position(("center", "center"), relative=True)
                ]).with_audio(audio_clip)
            
            video_clips.append(composite)
            print(f"✅ 第 {i + 1} 个片段创建完成")
        
        return video_clips


class ClothesSceneWorkflow(BaseVideoWorkflow):
    """服装场景视频工作流"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_coze_workflow = True
    
    def get_workflow_id(self) -> str:
        return '7494924152006295571'
    
    def prepare_workflow_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "has_figure": data.get("has_figure", False),
            "clothes": data.get("clothes"),
            "description": data.get("description", ""),
            "is_down": data.get("is_down", True),
        }
    
    def process_workflow_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # 处理服装场景工作流的响应
        return response
    
    def create_video_clips(self, data: Dict[str, Any]) -> List[VideoFileClip]:
        """创建服装场景视频片段"""
        # 这里实现服装场景特有的视频创建逻辑
        video_clips = []
        # TODO: 实现具体逻辑
        return video_clips


class DigitalHumanWorkflow(BaseVideoWorkflow):
    """数字人视频工作流"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.use_coze_workflow = False  # 数字人工作流不使用Coze
    
    def get_workflow_id(self) -> str:
        return ""  # 数字人不使用工作流
    
    def prepare_workflow_parameters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def process_workflow_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def create_video_clips(self, data: Dict[str, Any]) -> List[VideoFileClip]:
        """创建数字人视频片段"""
        # 直接调用数字人生成器
        result_path = self.digital_human.generate_digital_human_video(
            video_input=data.get("video_input"),
            topic=data.get("topic"),
            content=data.get("content"),
            audio_input=data.get("audio_input")
        )
        
        # 返回生成的视频作为片段
        if result_path and os.path.exists(os.path.join(self.user_data_dir, result_path)):
            full_path = os.path.join(self.user_data_dir, result_path)
            return [VideoFileClip(full_path)]
        else:
            raise Exception("数字人视频生成失败")


# 工作流工厂
class WorkflowFactory:
    """工作流工厂类"""
    
    @staticmethod
    def create_workflow(workflow_type: str, **kwargs) -> BaseVideoWorkflow:
        """
        创建工作流实例
        
        Args:
            workflow_type: 工作流类型 ('advertisement', 'clothes_scene', 'digital_human')
            **kwargs: 工作流参数
            
        Returns:
            工作流实例
        """
        workflows = {
            'advertisement': AdvertisementWorkflow,
            'clothes_scene': ClothesSceneWorkflow,
            'digital_human': DigitalHumanWorkflow,
        }
        
        if workflow_type not in workflows:
            raise ValueError(f"不支持的工作流类型: {workflow_type}")
        
        return workflows[workflow_type](**kwargs)


# 便捷函数
def generate_advertisement_video(data: Dict[str, Any], use_digital_host: bool = False, **kwargs) -> str:
    """生成广告视频的便捷函数"""
    workflow = WorkflowFactory.create_workflow('advertisement', use_digital_host=use_digital_host, **kwargs)
    return workflow.generate_video(data)

def generate_clothes_scene_video(data: Dict[str, Any], **kwargs) -> str:
    """生成服装场景视频的便捷函数"""
    workflow = WorkflowFactory.create_workflow('clothes_scene', **kwargs)
    return workflow.generate_video(data)

def generate_digital_human_video(data: Dict[str, Any], **kwargs) -> str:
    """生成数字人视频的便捷函数"""
    workflow = WorkflowFactory.create_workflow('digital_human', **kwargs)
    return workflow.generate_video(data)
# -*- coding: utf-8 -*-
"""
通用视频生成器模块
为所有视频类型提供统一的生成接口和实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
from .workflow_base import BaseVideoWorkflow
from .coze_client import create_coze_client
from .config import get_workflow_id


class VideoGenerator(ABC):
    """视频生成器抽象基类"""
    
    def __init__(self, workflow_type: str, **kwargs):
        """
        初始化视频生成器
        
        Args:
            workflow_type: 工作流类型
            **kwargs: 其他配置参数
        """
        self.workflow_type = workflow_type
        self.workflow_id = get_workflow_id(workflow_type)
        self.coze_client = create_coze_client()
        self.config = kwargs
    
    @abstractmethod
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        """准备工作流参数"""
        pass
    
    @abstractmethod
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """处理工作流响应"""
        pass
    
    def generate(self, **kwargs) -> str:
        """
        生成视频的主流程
        
        Returns:
            生成的视频路径
        """
        try:
            print(f"🎯 开始生成{self.workflow_type}视频")
            
            # 1. 准备参数
            parameters = self.prepare_parameters(**kwargs)
            
            # 2. 调用Coze工作流
            response = self.coze_client.run_workflow(self.workflow_id, parameters)
            
            # 3. 处理响应
            processed_data = self.process_response(response)
            
            # 4. 生成视频
            from .workflow_base import generate_advertisement_video
            result_path = generate_advertisement_video(processed_data, **self.config)
            
            print(f"✅ {self.workflow_type}视频生成完成: {result_path}")
            return result_path
            
        except Exception as e:
            print(f"❌ {self.workflow_type}视频生成失败: {str(e)}")
            raise


class AdvertisementGenerator(VideoGenerator):
    """广告视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('advertisement', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "company_name": kwargs.get("company_name", ""),
            "service": kwargs.get("service", ""),
            "topic": kwargs.get("topic", ""),
            "content": kwargs.get("content"),
            "need_change": kwargs.get("need_change", False)
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class ClickTypeGenerator(VideoGenerator):
    """点击类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('clicktype', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "title": kwargs.get("title", ""),
            "content": kwargs.get("content", ""),
            "style": kwargs.get("style", "default"),
            "duration": kwargs.get("duration", 30)
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class BigWordGenerator(VideoGenerator):
    """大字报视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('big_word', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "text": kwargs.get("text", ""),
            "font_size": kwargs.get("font_size", 120),
            "background_color": kwargs.get("background_color", "black"),
            "text_color": kwargs.get("text_color", "white")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class CatMemeGenerator(VideoGenerator):
    """猫咪表情包视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('catmeme', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "dialogue": kwargs.get("dialogue", ""),
            "cat_type": kwargs.get("cat_type", "default"),
            "emotion": kwargs.get("emotion", "happy")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class DigitalHumanGenerator(VideoGenerator):
    """数字人视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('digital_human', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "video_input": kwargs.get("video_input", ""),
            "topic": kwargs.get("topic", ""),
            "content": kwargs.get("content"),
            "audio_input": kwargs.get("audio_input")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class ClothesSceneGenerator(VideoGenerator):
    """服装场景视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('clothes_scene', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "has_figure": kwargs.get("has_figure", False),
            "clothes_url": kwargs.get("clothes_url", ""),
            "description": kwargs.get("description", ""),
            "is_down": kwargs.get("is_down", True)
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class IncitementGenerator(VideoGenerator):
    """煽动类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('incitement', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "theme": kwargs.get("theme", ""),
            "intensity": kwargs.get("intensity", "medium"),
            "target_audience": kwargs.get("target_audience", "general")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class IntroductionGenerator(VideoGenerator):
    """介绍类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('introduction', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "subject": kwargs.get("subject", ""),
            "details": kwargs.get("details", ""),
            "style": kwargs.get("style", "professional")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class SinologyGenerator(VideoGenerator):
    """国学类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('sinology', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "classic": kwargs.get("classic", ""),
            "interpretation": kwargs.get("interpretation", ""),
            "background_style": kwargs.get("background_style", "traditional")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class StickmanGenerator(VideoGenerator):
    """火柴人视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('stickman', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "story": kwargs.get("story", ""),
            "animation_style": kwargs.get("animation_style", "simple"),
            "speed": kwargs.get("speed", "normal")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class PPTGenerator(VideoGenerator):
    """PPT视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('ppt', **kwargs)
    
    def prepare_parameters(self, **kwargs) -> Dict[str, Any]:
        return {
            "slides": kwargs.get("slides", []),
            "template": kwargs.get("template", "default"),
            "transition": kwargs.get("transition", "fade")
        }
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        return response


class VideoGeneratorFactory:
    """视频生成器工厂类"""
    
    # 生成器映射
    GENERATORS = {
        'advertisement': AdvertisementGenerator,
        'clicktype': ClickTypeGenerator,
        'big_word': BigWordGenerator,
        'catmeme': CatMemeGenerator,
        'digital_human': DigitalHumanGenerator,
        'clothes_scene': ClothesSceneGenerator,
        'incitement': IncitementGenerator,
        'introduction': IntroductionGenerator,
        'sinology': SinologyGenerator,
        'stickman': StickmanGenerator,
        'ppt': PPTGenerator,
    }
    
    @classmethod
    def create_generator(cls, generator_type: str, **kwargs) -> VideoGenerator:
        """
        创建视频生成器
        
        Args:
            generator_type: 生成器类型
            **kwargs: 生成器配置参数
            
        Returns:
            视频生成器实例
        """
        if generator_type not in cls.GENERATORS:
            raise ValueError(f"不支持的生成器类型: {generator_type}")
        
        generator_class = cls.GENERATORS[generator_type]
        return generator_class(**kwargs)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的生成器类型列表"""
        return list(cls.GENERATORS.keys())


# 便捷函数
def create_video_generator(generator_type: str, **kwargs) -> VideoGenerator:
    """创建视频生成器的便捷函数"""
    return VideoGeneratorFactory.create_generator(generator_type, **kwargs)

def generate_video(generator_type: str, **kwargs) -> str:
    """生成视频的便捷函数"""
    generator = create_video_generator(generator_type, **kwargs)
    return generator.generate(**kwargs)
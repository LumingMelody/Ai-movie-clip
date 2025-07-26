# -*- coding: utf-8 -*-
"""
统一配置管理模块
集中管理所有API密钥、工作流ID和其他配置信息
"""

import os
from typing import Dict, Any


class CozeConfig:
    """Coze配置管理类"""
    
    # 工作流ID常量
    WORKFLOW_IDS = {
        'advertisement': '7499113029830049819',
        'digital_human': '7494924152006295571', 
        'clothes_scene': '7494924152006295571',
        'clicktype': '7499113029830049820',  # 示例ID
        'big_word': '7499113029830049821',   # 示例ID
        'catmeme': '7499113029830049822',    # 示例ID
        'incitement': '7499113029830049823', # 示例ID
        'introduction': '7499113029830049824', # 示例ID
        'sinology': '7499113029830049825',   # 示例ID
        'stickman': '7499113029830049826',   # 示例ID
        'ppt': '7499113029830049827',        # 示例ID
        'cover_analysis': '7499113029830049828', # 示例ID
    }
    
    @classmethod
    def get_workflow_id(cls, workflow_type: str) -> str:
        """获取工作流ID"""
        if workflow_type not in cls.WORKFLOW_IDS:
            raise ValueError(f"未知的工作流类型: {workflow_type}")
        return cls.WORKFLOW_IDS[workflow_type]


class APIConfig:
    """API配置管理类"""
    
    # 默认配置（可以被环境变量覆盖）
    _DEFAULT_CONFIG = {
        # DashScope/百炼API配置
        'dashscope_api_key': os.environ.get('DASHSCOPE_API_KEY', 'YOUR_DASHSCOPE_API_KEY'),
        
        # OSS配置 - 从环境变量读取
        'oss_access_key_id': os.environ.get('OSS_ACCESS_KEY_ID', 'YOUR_ACCESS_KEY_ID'),
        'oss_access_secret': os.environ.get('OSS_ACCESS_KEY_SECRET', 'YOUR_ACCESS_KEY_SECRET'),
        'oss_endpoint': os.environ.get('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com'),
        'oss_bucket_name': os.environ.get('OSS_BUCKET_NAME', 'lan8-e-business'),
        
        # OSS目录配置
        'video_oss_folder': 'agent/resource/video/',
        'ads_oss_folder': 'ads/',
        'output_oss_folder': 'agent/resource',
        
        # 其他配置
        'local_temp_dir': './temp/',
        'default_timeout': 30,
        'chunk_size': 8192,
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取配置值
        优先级：环境变量 > 默认配置 > default参数
        """
        # 首先检查环境变量
        env_key = f"COZE_{key.upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
        
        # 然后检查默认配置
        if key in cls._DEFAULT_CONFIG:
            return cls._DEFAULT_CONFIG[key]
        
        # 最后返回默认值
        return default
    
    @classmethod
    def get_dashscope_api_key(cls) -> str:
        """获取DashScope API密钥"""
        return cls.get('dashscope_api_key')
    
    @classmethod
    def get_oss_config(cls) -> Dict[str, str]:
        """获取OSS配置"""
        return {
            'access_key_id': cls.get('oss_access_key_id'),
            'access_secret': cls.get('oss_access_secret'),
            'endpoint': cls.get('oss_endpoint'),
            'bucket_name': cls.get('oss_bucket_name'),
        }
    
    @classmethod
    def get_oss_folders(cls) -> Dict[str, str]:
        """获取OSS文件夹配置"""
        return {
            'video': cls.get('video_oss_folder'),
            'ads': cls.get('ads_oss_folder'),
            'output': cls.get('output_oss_folder'),
        }


class VideoConfig:
    """视频相关配置"""
    
    # 支持的文件格式
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
    AUDIO_EXTENSIONS = ('.mp3', '.wav', '.aac', '.m4a', '.flac')
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    
    # 默认视频参数
    DEFAULT_VIDEO_PARAMS = {
        'fps': 24,
        'codec': 'libx264',
        'audio_codec': 'aac',
        'resolution': (1280, 720),
        'threads': 4,
    }
    
    # 字体配置
    FONT_NAMES = {
        'windows': ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"],
        'macos': ["PingFang SC", "Hiragino Sans GB", "STHeiti Light", "Arial Unicode MS"],
        'linux': ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"],
    }
    
    # 系统字体目录
    SYSTEM_FONT_PATHS = {
        'windows': [
            "C:/Windows/Fonts/",
            "C:/Windows/System32/Fonts/",
            "~/AppData/Local/Microsoft/Windows/Fonts/"
        ],
        'macos': [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            "~/Library/Fonts/"
        ],
        'linux': [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            "~/.fonts/",
            "~/.local/share/fonts/"
        ]
    }


# 便捷函数
def get_workflow_id(workflow_type: str) -> str:
    """获取工作流ID的便捷函数"""
    return CozeConfig.get_workflow_id(workflow_type)

def get_api_config(key: str, default: Any = None) -> Any:
    """获取API配置的便捷函数"""
    return APIConfig.get(key, default)

def get_dashscope_api_key() -> str:
    """获取DashScope API密钥的便捷函数"""
    return APIConfig.get_dashscope_api_key()

def get_oss_config() -> Dict[str, str]:
    """获取OSS配置的便捷函数"""
    return APIConfig.get_oss_config()
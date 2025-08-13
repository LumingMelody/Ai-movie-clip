# -*- coding: utf-8 -*-
"""
统一的配置管理模块
整合所有AI生成和视频处理相关的配置
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from core.utils.env_config import get_dashscope_api_key


class APIConfig:
    """
API配置管理类
    """
    
    # API服务配置
    _API_SERVICES = {
        # DashScope/百炼API
        'dashscope': {
            'base_url': 'https://dashscope.aliyuncs.com/api/v1',
            'api_key_env': 'DASHSCOPE_API_KEY',
            'timeout': 300,
            'retry_count': 3,
        },
        
        # Coze工作流API
        'coze': {
            'base_url': 'https://api.coze.cn',
            'api_key_env': 'COZE_API_TOKEN',
            'timeout': 180,
            'retry_count': 2,
        },
        
        # OSS存储配置
        'oss': {
            'endpoint': 'oss-cn-hangzhou.aliyuncs.com',
            'access_key_env': 'OSS_ACCESS_KEY_ID',
            'secret_key_env': 'OSS_ACCESS_KEY_SECRET',
            'bucket_name': 'lan8-e-business',
        },
    }
    
    @classmethod
    def get_api_key(cls, service: str) -> str:
        """获取API密钥"""
        if service == 'dashscope':
            # 优先使用环境变量
            api_key = os.environ.get('DASHSCOPE_API_KEY')
            if api_key:
                return api_key
            
            # 其次使用文件
            try:
                return get_dashscope_api_key()
            except:
                pass
            
            # 最后使用默认值
            return 'sk-a48a1d84e015410292d07021f60b9acb'
        
        elif service == 'coze':
            # Coze API使用doubaoconfigs
            try:
                from doubaoconfigs import coze_api_token
                return coze_api_token
            except ImportError:
                return os.environ.get('COZE_API_TOKEN', '')
        
        elif service in cls._API_SERVICES:
            config = cls._API_SERVICES[service]
            return os.environ.get(config.get('api_key_env', ''), '')
        
        else:
            raise ValueError(f"不支持的API服务: {service}")
    
    @classmethod
    def get_service_config(cls, service: str) -> Dict[str, Any]:
        """获取服务配置"""
        if service not in cls._API_SERVICES:
            raise ValueError(f"不支持的API服务: {service}")
        
        config = cls._API_SERVICES[service].copy()
        
        # 添加API密钥
        config['api_key'] = cls.get_api_key(service)
        
        return config
    
    @classmethod
    def get_oss_config(cls) -> Dict[str, str]:
        """获取OSS配置"""
        oss_config = cls._API_SERVICES['oss']
        
        return {
            'endpoint': os.environ.get('OSS_ENDPOINT', oss_config['endpoint']),
            'access_key_id': os.environ.get('OSS_ACCESS_KEY_ID', ''),
            'access_key_secret': os.environ.get('OSS_ACCESS_KEY_SECRET', ''),
            'bucket_name': os.environ.get('OSS_BUCKET_NAME', oss_config['bucket_name']),
        }


class WorkflowConfig:
    """工作流配置管理类"""
    
    # Coze工作流ID配置
    _WORKFLOW_IDS = {
        'advertisement': '7499113029830049819',
        'advertisement_enhance': '7499113029830049819',  # 用同一个工作流
        'big_word': '7502316696242929674',
        'catmeme': '7499113029830049822',
        'clicktype': '7499113029830049820',
        'incitement': '7499113029830049823',
        'introduction': '7499113029830049824',
        'sinology': '7499113029830049825',
        'stickman': '7499113029830049826',
        'clothes_scene': '7494924152006295571',
        'clothes_fast_change': '7494924152006295571',  # 用同一个工作流
        'cover_analysis': '7499113029830049828',
        'ppt': '7499113029830049827',
        'digital_human': '7494924152006295571',
        'dgh_img_insert': '7499113029830049819',  # 示例ID
    }
    
    # 工作流参数模板
    _WORKFLOW_PARAMS = {
        'advertisement': {
            'required': ['company_name', 'service', 'topic'],
            'optional': ['content', 'need_change'],
            'defaults': {'need_change': False}
        },
        
        'big_word': {
            'required': ['company_name', 'title', 'product', 'description'],
            'optional': ['content'],
            'defaults': {}
        },
        
        'catmeme': {
            'required': ['author', 'title'],
            'optional': ['content'],
            'defaults': {}
        },
        
        'clicktype': {
            'required': ['title'],
            'optional': ['content'],
            'defaults': {}
        },
        
        'incitement': {
            'required': ['title'],
            'optional': [],
            'defaults': {}
        },
        
        'introduction': {
            'required': ['title'],
            'optional': ['content'],
            'defaults': {}
        },
        
        'sinology': {
            'required': ['title'],
            'optional': ['content'],
            'defaults': {}
        },
        
        'stickman': {
            'required': ['author', 'title'],
            'optional': ['content', 'lift_text'],
            'defaults': {'lift_text': '科普动画'}
        },
        
        'clothes_scene': {
            'required': ['clothesurl', 'description'],
            'optional': ['has_figure', 'is_down'],
            'defaults': {'has_figure': True, 'is_down': True}
        },
    }
    
    @classmethod
    def get_workflow_id(cls, workflow_type: str) -> str:
        """获取工作流ID"""
        if workflow_type not in cls._WORKFLOW_IDS:
            raise ValueError(f"未知的工作流类型: {workflow_type}")
        return cls._WORKFLOW_IDS[workflow_type]
    
    @classmethod
    def get_workflow_params_template(cls, workflow_type: str) -> Dict[str, Any]:
        """获取工作流参数模板"""
        if workflow_type not in cls._WORKFLOW_PARAMS:
            return {'required': [], 'optional': [], 'defaults': {}}
        return cls._WORKFLOW_PARAMS[workflow_type]
    
    @classmethod
    def validate_workflow_params(cls, workflow_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证并整理工作流参数"""
        template = cls.get_workflow_params_template(workflow_type)
        
        # 检查必需参数
        for required_param in template['required']:
            if required_param not in params or params[required_param] is None:
                raise ValueError(f"缺少必需参数: {required_param}")
        
        # 合并默认参数
        result_params = template['defaults'].copy()
        result_params.update(params)
        
        return result_params
    
    @classmethod
    def get_all_workflow_types(cls) -> List[str]:
        """获取所有工作流类型"""
        return list(cls._WORKFLOW_IDS.keys())


class VideoConfig:
    """视频相关配置"""
    
    # 支持的文件格式
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
    AUDIO_EXTENSIONS = ('.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg')
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
    
    # 默认视频参数
    DEFAULT_VIDEO_PARAMS = {
        'fps': 24,
        'codec': 'libx264',
        'audio_codec': 'aac',
        'resolution': (1280, 720),
        'threads': 4,
        'bitrate': '2M',
        'audio_bitrate': '128k',
    }
    
    # 分辨率预设
    RESOLUTION_PRESETS = {
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '4k': (3840, 2160),
        'mobile': (720, 1280),  # 竖屏
        'square': (1080, 1080),  # 方形
    }
    
    # 字体配置
    FONT_CONFIG = {
        'windows': {
            'names': ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"],
            'paths': [
                "C:/Windows/Fonts/",
                "C:/Windows/System32/Fonts/",
                "~/AppData/Local/Microsoft/Windows/Fonts/"
            ]
        },
        'macos': {
            'names': ["PingFang SC", "Hiragino Sans GB", "STHeiti Light", "Arial Unicode MS"],
            'paths': [
                "/System/Library/Fonts/",
                "/Library/Fonts/",
                "~/Library/Fonts/"
            ]
        },
        'linux': {
            'names': ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"],
            'paths': [
                "/usr/share/fonts/",
                "/usr/local/share/fonts/",
                "~/.fonts/",
                "~/.local/share/fonts/"
            ]
        }
    }
    
    # 文本样式预设
    TEXT_STYLES = {
        'title': {
            'fontsize': 80,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center'
        },
        'subtitle': {
            'fontsize': 60,
            'color': 'white',
            'bg_color': (0, 0, 0, 128),
            'method': 'caption',
            'align': 'center'
        },
        'body': {
            'fontsize': 40,
            'color': 'white',
            'method': 'caption',
            'align': 'left'
        },
        'caption': {
            'fontsize': 30,
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 1,
            'method': 'caption',
            'align': 'center'
        }
    }
    
    @classmethod
    def get_video_params(cls, preset: str = None) -> Dict[str, Any]:
        """获取视频参数"""
        params = cls.DEFAULT_VIDEO_PARAMS.copy()
        
        if preset and preset in cls.RESOLUTION_PRESETS:
            params['resolution'] = cls.RESOLUTION_PRESETS[preset]
        
        return params
    
    @classmethod
    def get_text_style(cls, style_name: str) -> Dict[str, Any]:
        """获取文本样式"""
        if style_name not in cls.TEXT_STYLES:
            return cls.TEXT_STYLES['subtitle']  # 默认样式
        return cls.TEXT_STYLES[style_name].copy()


class PathConfig:
    """路径配置管理类"""
    
    @classmethod
    def get_user_data_dir(cls) -> str:
        """获取用户数据目录"""
        try:
            from config import get_user_data_dir
            return get_user_data_dir()
        except ImportError:
            # 备选方案
            return os.path.expanduser("~/ai_movie_clip_data")
    
    @classmethod
    def get_temp_dir(cls) -> str:
        """获取临时目录"""
        user_data_dir = cls.get_user_data_dir()
        temp_dir = os.path.join(user_data_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    @classmethod
    def get_materials_dir(cls) -> str:
        """获取素材目录"""
        user_data_dir = cls.get_user_data_dir()
        materials_dir = os.path.join(user_data_dir, "materials")
        os.makedirs(materials_dir, exist_ok=True)
        return materials_dir
    
    @classmethod
    def get_projects_dir(cls) -> str:
        """获取项目目录"""
        user_data_dir = cls.get_user_data_dir()
        projects_dir = os.path.join(user_data_dir, "projects")
        os.makedirs(projects_dir, exist_ok=True)
        return projects_dir
    
    @classmethod
    def get_fonts_dir(cls) -> str:
        """获取字体目录"""
        user_data_dir = cls.get_user_data_dir()
        fonts_dir = os.path.join(user_data_dir, "fonts")
        os.makedirs(fonts_dir, exist_ok=True)
        return fonts_dir


class ModelConfig:
    """模型配置管理类"""
    
    # 通义千问模型配置
    TONGYI_MODELS = {
        'qwen-plus': {
            'description': '通义千问Plus模型',
            'max_tokens': 2000,
            'temperature': 0.8,
            'top_p': 0.8,
        },
        'qwen-turbo': {
            'description': '通义千问Turbo模型',
            'max_tokens': 1500,
            'temperature': 0.7,
            'top_p': 0.9,
        },
        'qwen-max': {
            'description': '通义千问Max模型',
            'max_tokens': 6000,
            'temperature': 0.3,
            'top_p': 0.8,
        },
    }
    
    # 通义万相模型配置
    WANXIANG_MODELS = {
        # 文生图模型
        'text_to_image': {
            'wanx-v1': {'description': '通义万相V1', 'max_size': '1024*1024'},
            'wanx2.1-t2i-turbo': {'description': '通义万相V2.1加速版', 'max_size': '2048*2048'},
            'wanx2.1-t2i-plus': {'description': '通义万相V2.1增强版', 'max_size': '2048*2048'},
        },
        
        # 文生视频模型
        'text_to_video': {
            'wanx2.1-t2v-turbo': {'description': '文生视频加速版', 'max_duration': 6},
        },
        
        # 图生视频模型
        'image_to_video': {
            'wanx2.1-i2v-turbo': {'description': '图生视频加速版', 'max_duration': 6},
            'wanx2.1-kf2v-plus': {'description': '首尾帧图生视频', 'max_duration': 10},
        },
        
        # AI试衣模型
        'ai_tryon': {
            'aitryon': {'description': 'AI试衣基础版'},
            'aitryon-plus': {'description': 'AI试衣增强版'},
            'aitryon-refiner': {'description': 'AI试衣精修版'},
        },
    }
    
    @classmethod
    def get_model_config(cls, model_type: str, model_name: str) -> Dict[str, Any]:
        """获取模型配置"""
        if model_type == 'tongyi':
            if model_name not in cls.TONGYI_MODELS:
                raise ValueError(f"不支持的通义千问模型: {model_name}")
            return cls.TONGYI_MODELS[model_name]
        
        elif model_type in cls.WANXIANG_MODELS:
            if model_name not in cls.WANXIANG_MODELS[model_type]:
                raise ValueError(f"不支持的{model_type}模型: {model_name}")
            return cls.WANXIANG_MODELS[model_type][model_name]
        
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    @classmethod
    def get_default_model(cls, model_type: str) -> str:
        """获取默认模型"""
        defaults = {
            'tongyi': 'qwen-plus',
            'text_to_image': 'wanx2.1-t2i-turbo',
            'text_to_video': 'wanx2.1-t2v-turbo',
            'image_to_video': 'wanx2.1-i2v-turbo',
            'ai_tryon': 'aitryon-plus',
        }
        
        return defaults.get(model_type, '')


class UnifiedConfig:
    """统一配置管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.api = APIConfig()
            self.workflow = WorkflowConfig()
            self.video = VideoConfig()
            self.path = PathConfig()
            self.model = ModelConfig()
            self._initialized = True
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'api_services': list(self.api._API_SERVICES.keys()),
            'workflow_types': self.workflow.get_all_workflow_types(),
            'video_extensions': self.video.VIDEO_EXTENSIONS,
            'audio_extensions': self.video.AUDIO_EXTENSIONS,
            'image_extensions': self.video.IMAGE_EXTENSIONS,
            'resolution_presets': list(self.video.RESOLUTION_PRESETS.keys()),
            'text_styles': list(self.video.TEXT_STYLES.keys()),
            'user_data_dir': self.path.get_user_data_dir(),
            'temp_dir': self.path.get_temp_dir(),
        }
    
    def validate_environment(self) -> Dict[str, bool]:
        """验证环境配置"""
        status = {}
        
        # 检查API密钥
        try:
            dashscope_key = self.api.get_api_key('dashscope')
            status['dashscope_api'] = bool(dashscope_key and dashscope_key != 'YOUR_API_KEY')
        except:
            status['dashscope_api'] = False
        
        try:
            coze_key = self.api.get_api_key('coze')
            status['coze_api'] = bool(coze_key)
        except:
            status['coze_api'] = False
        
        # 检查目录权限
        try:
            user_data_dir = self.path.get_user_data_dir()
            status['user_data_dir'] = os.access(user_data_dir, os.W_OK)
        except:
            status['user_data_dir'] = False
        
        # 检查字体可用性
        try:
            from .unified_video_processor import FontManager
            font_manager = FontManager()
            status['fonts_available'] = font_manager.find_font() is not None
        except:
            status['fonts_available'] = False
        
        return status
    
    def export_config(self, file_path: str):
        """导出配置到文件"""
        config_data = {
            'api_services': self.api._API_SERVICES,
            'workflow_ids': self.workflow._WORKFLOW_IDS,
            'workflow_params': self.workflow._WORKFLOW_PARAMS,
            'video_config': {
                'extensions': {
                    'video': self.video.VIDEO_EXTENSIONS,
                    'audio': self.video.AUDIO_EXTENSIONS,
                    'image': self.video.IMAGE_EXTENSIONS,
                },
                'default_params': self.video.DEFAULT_VIDEO_PARAMS,
                'resolution_presets': self.video.RESOLUTION_PRESETS,
                'text_styles': self.video.TEXT_STYLES,
                'font_config': self.video.FONT_CONFIG,
            },
            'model_config': {
                'tongyi': self.model.TONGYI_MODELS,
                'wanxiang': self.model.WANXIANG_MODELS,
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 配置已导出到: {file_path}")


# 全局配置实例
_config = None

def get_config() -> UnifiedConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = UnifiedConfig()
    return _config


# 快捷函数
def get_api_key(service: str) -> str:
    """获取API密钥 - 快捷函数"""
    return get_config().api.get_api_key(service)

def get_workflow_id(workflow_type: str) -> str:
    """获取工作流ID - 快捷函数"""
    return get_config().workflow.get_workflow_id(workflow_type)

def get_video_params(preset: str = None) -> Dict[str, Any]:
    """获取视频参数 - 快捷函数"""
    return get_config().video.get_video_params(preset)

def get_text_style(style_name: str) -> Dict[str, Any]:
    """获取文本样式 - 快捷函数"""
    return get_config().video.get_text_style(style_name)

def validate_workflow_params(workflow_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """验证工作流参数 - 快捷函数"""
    return get_config().workflow.validate_workflow_params(workflow_type, params)


if __name__ == "__main__":
    # 测试配置系统
    print("🔧 统一配置管理模块加载完成")
    
    config = get_config()
    
    print("\n✅ 配置验证结果:")
    status = config.validate_environment()
    for key, value in status.items():
        status_icon = "✅" if value else "❌"
        print(f"  {status_icon} {key}: {value}")
    
    print("\n📊 配置统计:")
    all_config = config.get_all_config()
    for key, value in all_config.items():
        if isinstance(value, (list, tuple)):
            print(f"  - {key}: {len(value)} 个")
        else:
            print(f"  - {key}: {value}")

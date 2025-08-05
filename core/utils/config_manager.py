# -*- coding: utf-8 -*-
"""
统一配置管理器 - 管理所有模块的配置和常量
"""

import os
import sys
from typing import Dict, Any, Optional, List, Union
import json
import logging
from functools import lru_cache
from contextlib import contextmanager
import threading


class ConfigManager:
    """统一配置管理器 - 线程安全的单例模式"""
    
    _instance = None
    _initialized = False
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # 双重检查锁定
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # 双重检查锁定
                    self._load_configurations()
                    self._setup_logging()
                    ConfigManager._initialized = True
    
    def _load_configurations(self):
        """加载所有配置"""
        # 路径配置
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.core_dir = os.path.dirname(self.current_dir)
        self.project_root = os.path.dirname(self.core_dir)
        
        # 视频处理配置
        self.video_config = {
            'supported_extensions': ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'),
            'default_fps': 24,
            'default_target_duration': 30,
            'max_analysis_frames': 30,
            'default_output_dir': 'output',
            'temp_audio_file': 'temp_audio.wav'
        }
        
        # AI模型配置
        self.ai_config = {
            'default_model': 'qwen-max',
            'supported_models': ['qwen-max'],
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'max_retries': 3,
            'timeout': 60,
            'max_tokens': 3000,
            'temperature': 0.8
        }
        
        # 音频配置
        self.audio_config = {
            'sample_rate': 16000,
            'channels': 1,
            'format': 'pcm_s16le',
            'whisper_model': 'base'
        }
        
        # 输出配置
        self.output_config = {
            'video_codec': 'libx264',
            'audio_codec': 'aac',
            'audio_bitrate': '128k',
            'preset': 'medium',
            'threads': 1
        }
        
        # 场景检测配置
        self.scene_detection_config = {
            'default_threshold': 30.0
        }
        
        # API密钥
        self.api_key = self._load_api_key()
    
    def _load_api_key(self) -> Optional[str]:
        """从多个来源加载API密钥"""
        # 1. 环境变量
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            return api_key
        
        # 2. 当前目录的api_key.txt
        api_key_files = [
            os.path.join(self.project_root, "api_key.txt"),
            os.path.join(self.core_dir, "api_key.txt"),
            "api_key.txt"
        ]
        
        for api_key_file in api_key_files:
            if os.path.exists(api_key_file):
                try:
                    with open(api_key_file, 'r', encoding='utf-8') as f:
                        api_key = f.read().strip()
                        if api_key:
                            return api_key
                except Exception as e:
                    print(f"读取{api_key_file}失败: {e}")
        
        return None
    
    def _setup_logging(self):
        """设置日志配置"""
        self.logging_config = {
            'level': logging.INFO,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'handlers': {
                'console': True,
                'file': os.path.join(self.project_root, 'logs', 'app.log')
            }
        }
        
        # 确保日志目录存在
        log_dir = os.path.dirname(self.logging_config['handlers']['file'])
        os.makedirs(log_dir, exist_ok=True)
    
    @lru_cache(maxsize=128)
    def get_cached_config(self, category: str, key: str = None) -> Any:
        """获取缓存的配置项"""
        config_dict = getattr(self, f'{category}_config', {})
        if key:
            return config_dict.get(key)
        return config_dict
    
    def setup_python_path(self):
        """设置Python路径"""
        paths_to_add = [self.project_root, self.core_dir]
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
    
    def get_config(self, category: str) -> Dict[str, Any]:
        """获取指定类别的配置"""
        return getattr(self, f'{category}_config', {})
    
    def get_video_extensions(self) -> tuple:
        """获取支持的视频扩展名"""
        return self.video_config['supported_extensions']
    
    def get_api_key(self) -> Optional[str]:
        """获取API密钥"""
        return self.api_key
    
    def get_project_paths(self) -> Dict[str, str]:
        """获取项目路径信息"""
        return {
            'current_dir': self.current_dir,
            'core_dir': self.core_dir,
            'project_root': self.project_root,
            'temp_dir': os.path.join(self.project_root, 'temp'),
            'output_dir': os.path.join(self.project_root, 'output'),
            'logs_dir': os.path.join(self.project_root, 'logs'),
            'resources_dir': os.path.join(self.project_root, 'resources')
        }
    
    def validate_environment(self) -> List[str]:
        """验证环境配置"""
        issues = []
        
        # 检查API密钥
        if not self.api_key:
            issues.append("未找到DashScope API密钥")
        
        # 检查必要目录
        paths = self.get_project_paths()
        for name, path in paths.items():
            if name != 'current_dir' and not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception as e:
                    issues.append(f"无法创建目录 {name}: {e}")
        
        return issues
    
    @contextmanager
    def temp_config(self, category: str, **kwargs):
        """临时修改配置的上下文管理器"""
        config_dict = getattr(self, f'{category}_config', {})
        original_values = {k: config_dict.get(k) for k in kwargs.keys()}
        
        # 应用临时配置
        config_dict.update(kwargs)
        
        try:
            yield
        finally:
            # 恢复原始配置
            for k, v in original_values.items():
                if v is None:
                    config_dict.pop(k, None)
                else:
                    config_dict[k] = v


class PathHelper:
    """路径处理辅助类"""
    
    @staticmethod
    def ensure_dir_exists(directory: str) -> str:
        """确保目录存在"""
        os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """获取安全的文件名"""
        import re
        # 移除或替换不安全的字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除控制字符
        safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)
        # 限制长度
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:max_length - len(ext)] + ext
        return safe_name.strip()
    
    @staticmethod
    def get_temp_path(suffix: str = '', prefix: str = 'temp_') -> str:
        """获取临时文件路径"""
        import tempfile
        import uuid
        temp_name = f"{prefix}{uuid.uuid4().hex[:8]}{suffix}"
        return os.path.join(tempfile.gettempdir(), temp_name)
    
    @staticmethod
    def get_project_temp_path(suffix: str = '', prefix: str = 'temp_') -> str:
        """获取项目临时文件路径"""
        import uuid
        temp_dir = config.get_project_paths()['temp_dir']
        os.makedirs(temp_dir, exist_ok=True)
        temp_name = f"{prefix}{uuid.uuid4().hex[:8]}{suffix}"
        return os.path.join(temp_dir, temp_name)
    
    @staticmethod
    def cleanup_temp_files(pattern: str = "temp_*", max_age_hours: int = 24):
        """清理过期的临时文件"""
        import glob
        import time
        
        temp_dirs = [
            tempfile.gettempdir(),
            config.get_project_paths()['temp_dir']
        ]
        
        current_time = time.time()
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            pattern_path = os.path.join(temp_dir, pattern)
            for file_path in glob.glob(pattern_path):
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_hours * 3600:  # 转换为秒
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            import shutil
                            shutil.rmtree(file_path)
                        ErrorHandler.log_info(f"清理过期临时文件: {file_path}")
                except Exception as e:
                    ErrorHandler.log_warning(f"清理临时文件失败 {file_path}: {e}")


class ErrorHandler:
    """统一错误处理器 - 支持日志记录和错误统计"""
    
    _error_counts = {}
    _logger = None
    
    @classmethod
    def _get_logger(cls):
        if cls._logger is None:
            cls._logger = logging.getLogger('ErrorHandler')
            if not cls._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                cls._logger.addHandler(handler)
                cls._logger.setLevel(logging.INFO)
        return cls._logger
    
    @classmethod
    def _increment_error_count(cls, error_type: str):
        cls._error_counts[error_type] = cls._error_counts.get(error_type, 0) + 1
    
    @classmethod
    def get_error_statistics(cls) -> Dict[str, int]:
        """获取错误统计"""
        return cls._error_counts.copy()
    
    @classmethod
    def handle_import_error(cls, module_name: str, error: Exception, fallback_action: str = None):
        """处理导入错误"""
        cls._increment_error_count('import_error')
        logger = cls._get_logger()
        logger.error(f"导入{module_name}失败: {error}")
        print(f"❌ 导入{module_name}失败: {error}")
        if fallback_action:
            logger.info(f"备用方案: {fallback_action}")
            print(f"📋 备用方案: {fallback_action}")
    
    @classmethod
    def handle_api_error(cls, api_name: str, error: Exception, retry_count: int = 0):
        """处理API错误"""
        cls._increment_error_count('api_error')
        logger = cls._get_logger()
        error_msg = f"{api_name} API调用失败"
        if retry_count > 0:
            error_msg += f" (重试 {retry_count})"
        error_msg += f": {error}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
    
    @classmethod
    def handle_file_error(cls, operation: str, file_path: str, error: Exception):
        """处理文件操作错误"""
        cls._increment_error_count('file_error')
        logger = cls._get_logger()
        error_msg = f"文件{operation}失败 ({file_path}): {error}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
    
    @classmethod
    def log_warning(cls, message: str):
        """记录警告"""
        logger = cls._get_logger()
        logger.warning(message)
        print(f"⚠️ 警告: {message}")
    
    @classmethod
    def log_success(cls, message: str):
        """记录成功"""
        logger = cls._get_logger()
        logger.info(message)
        print(f"✅ {message}")
    
    @classmethod
    def log_info(cls, message: str):
        """记录信息"""
        logger = cls._get_logger()
        logger.info(message)
        print(f"📝 {message}")
    
    @classmethod
    def reset_error_counts(cls):
        """重置错误计数"""
        cls._error_counts.clear()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """开始计时"""
        import time
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """结束计时并返回耗时"""
        import time
        if operation in self.start_times:
            elapsed = time.time() - self.start_times[operation]
            if operation not in self.metrics:
                self.metrics[operation] = []
            self.metrics[operation].append(elapsed)
            del self.start_times[operation]
            return elapsed
        return 0.0
    
    @contextmanager
    def timer(self, operation: str):
        """上下文管理器式计时器"""
        self.start_timer(operation)
        try:
            yield
        finally:
            elapsed = self.end_timer(operation)
            ErrorHandler.log_info(f"{operation} 耗时: {elapsed:.2f}秒")
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """获取性能统计"""
        stats = {}
        for operation, times in self.metrics.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times)
                }
        return stats
    
    def reset_metrics(self):
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()


# 创建全局实例
config = ConfigManager()
performance_monitor = PerformanceMonitor()
"""
Core utilities module - 统一的工具模块入口
提供所有核心工具类和函数的便捷导入
"""

# 核心配置和错误处理
from .config_manager import (
    ConfigManager, 
    PathHelper, 
    ErrorHandler, 
    PerformanceMonitor,
    config, 
    performance_monitor
)

# 文件操作工具
from .file_utils import (
    FileCache,
    file_cache,
    download_file_with_retry,
    download_file,
    batch_download_files,
    ensure_file_exists,
    get_file_size,
    get_file_extension,
    get_file_info,
    get_file_hash,
    is_video_file,
    is_image_file,
    is_audio_file,
    safe_copy_file,
    safe_move_file,
    temporary_file,
    extract_filename_from_url,
    is_url_accessible
)

# 视频处理工具
from .video_utils import (
    VideoProcessor,
    VideoValidator,
    video_processor,
    video_validator
)

# 版本信息
__version__ = "2.0.0"

# 导出所有工具类
__all__ = [
    # 配置管理
    'ConfigManager', 'PathHelper', 'ErrorHandler', 'PerformanceMonitor',
    'config', 'performance_monitor',
    
    # 文件工具
    'FileCache', 'file_cache', 
    'download_file_with_retry', 'download_file', 'batch_download_files',
    'ensure_file_exists', 'get_file_size', 'get_file_extension', 
    'get_file_info', 'get_file_hash',
    'is_video_file', 'is_image_file', 'is_audio_file',
    'safe_copy_file', 'safe_move_file', 'temporary_file',
    'extract_filename_from_url', 'is_url_accessible',
    
    # 视频工具
    'VideoProcessor', 'VideoValidator', 'video_processor', 'video_validator'
]

def initialize_utils():
    """
    初始化工具模块
    
    执行必要的环境检查和配置设置
    """
    # 验证环境配置
    issues = config.validate_environment()
    if issues:
        ErrorHandler.log_warning("环境配置存在以下问题:")
        for issue in issues:
            ErrorHandler.log_warning(f"  - {issue}")
    
    # 清理过期的临时文件
    PathHelper.cleanup_temp_files()
    
    # 清理文件缓存
    try:
        file_cache.cleanup_cache()
    except Exception as e:
        ErrorHandler.log_warning(f"清理文件缓存失败: {e}")
    
    ErrorHandler.log_info("工具模块初始化完成")

# 自动初始化
try:
    initialize_utils()
except Exception as e:
    print(f"Warning: 工具模块初始化失败: {e}")
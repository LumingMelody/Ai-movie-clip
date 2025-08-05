#!/usr/bin/env python3
"""
工具类使用示例
演示如何使用重构后的统一工具模块
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def demo_config_management():
    """演示配置管理功能"""
    print("=== 配置管理示例 ===")
    
    from core.utils import config, ErrorHandler
    
    # 获取项目路径
    paths = config.get_project_paths()
    print(f"项目根目录: {paths['project_root']}")
    print(f"输出目录: {paths['output_dir']}")
    
    # 获取配置信息
    video_config = config.get_config('video')
    print(f"支持的视频格式: {video_config['supported_extensions']}")
    
    # 验证环境
    issues = config.validate_environment()
    if issues:
        print("环境问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("环境配置正常")
    
    print()


def demo_file_operations():
    """演示文件操作功能"""
    print("=== 文件操作示例 ===")
    
    from core.utils import (
        get_file_info, is_video_file, get_file_hash,
        safe_copy_file, temporary_file, ensure_file_exists
    )
    
    # 获取文件信息
    test_file = __file__  # 使用当前文件作为示例
    if ensure_file_exists(test_file):
        file_info = get_file_info(test_file)
        print(f"文件: {file_info['name']}")
        print(f"大小: {file_info['size_mb']} MB")
        print(f"扩展名: {file_info['extension']}")
        print(f"是否为视频: {file_info['is_video']}")
        
        # 计算文件哈希
        file_hash = get_file_hash(test_file)
        print(f"MD5: {file_hash}")
    
    # 使用临时文件
    with temporary_file(suffix='.txt', prefix='demo_') as temp_path:
        print(f"临时文件路径: {temp_path}")
        # 在这里可以使用临时文件
        with open(temp_path, 'w') as f:
            f.write("这是一个临时文件示例")
        print(f"临时文件已创建: {ensure_file_exists(temp_path)}")
    # 临时文件会在退出上下文时自动删除
    
    print()


def demo_download_functionality():
    """演示下载功能"""
    print("=== 下载功能示例 ===")
    
    from core.utils import download_file_with_retry, batch_download_files
    from core.utils import PathHelper
    
    # 单文件下载示例（使用一个小的公共文件）
    test_url = "https://httpbin.org/uuid"
    save_path = PathHelper.get_project_temp_path('.json', 'test_download_')
    
    print(f"下载测试文件: {test_url}")
    success = download_file_with_retry(
        url=test_url,
        save_path=save_path,
        verbose=True,
        use_cache=True
    )
    
    if success:
        print(f"下载成功: {save_path}")
        # 清理测试文件
        try:
            os.remove(save_path)
        except:
            pass
    else:
        print("下载失败")
    
    print()


def demo_retry_mechanism():
    """演示重试机制"""
    print("=== 重试机制示例 ===")
    
    from video_cut.utils import retry, RetryConfig
    
    # 创建一个可能失败的函数
    call_count = 0
    
    @retry(RetryConfig(max_retries=3, delay=0.5))
    def unstable_function():
        nonlocal call_count
        call_count += 1
        print(f"  尝试第 {call_count} 次...")
        
        if call_count < 3:  # 前两次失败
            raise Exception("模拟失败")
        return "成功!"
    
    try:
        result = unstable_function()
        print(f"最终结果: {result}")
    except Exception as e:
        print(f"所有重试都失败了: {e}")
    
    print()


def demo_video_processing():
    """演示视频处理功能"""
    print("=== 视频处理示例 ===")
    
    from core.utils import VideoValidator, is_video_file
    
    # 验证视频文件
    test_files = [
        "test.mp4",
        "image.jpg", 
        "audio.mp3",
        "document.pdf"
    ]
    
    for file_path in test_files:
        is_valid = VideoValidator.validate_video_file(file_path)
        is_video = is_video_file(file_path)
        print(f"{file_path}: 有效视频={is_valid}, 视频格式={is_video}")
    
    # 验证时间范围
    time_valid = VideoValidator.validate_time_range(0, 30, 60)
    print(f"时间范围 (0-30s, 总长60s): {time_valid}")
    
    print()


def demo_performance_monitoring():
    """演示性能监控功能"""
    print("=== 性能监控示例 ===")
    
    from core.utils import performance_monitor
    from video_cut.utils import timing_context
    import time
    
    # 使用性能监控器
    with performance_monitor.timer("测试操作"):
        time.sleep(0.1)  # 模拟耗时操作
    
    # 使用计时上下文
    with timing_context("另一个测试操作"):
        time.sleep(0.05)  # 模拟另一个操作
    
    # 获取统计信息
    stats = performance_monitor.get_statistics()
    if stats:
        print("性能统计:")
        for operation, metrics in stats.items():
            print(f"  {operation}: {metrics}")
    
    print()


def demo_data_validation():
    """演示数据验证功能"""
    print("=== 数据验证示例 ===")
    
    from video_cut.utils import DataValidator, TimelineUtils
    
    # URL验证
    test_urls = [
        "https://www.example.com",
        "http://localhost:8080",
        "not-a-url",
        "ftp://invalid-protocol.com"
    ]
    
    for url in test_urls:
        is_valid = DataValidator.validate_url(url)
        print(f"URL '{url}': {is_valid}")
    
    # 时间轴验证
    timeline_segments = [
        {"start": 0, "end": 10},      # 有效
        {"start": 15, "end": 5},      # 无效：开始时间大于结束时间
        {"start": -1, "end": 10},     # 无效：负数开始时间
        {"end": 10}                   # 无效：缺少开始时间
    ]
    
    print("\n时间轴片段验证:")
    for i, segment in enumerate(timeline_segments):
        is_valid = TimelineUtils.validate_timeline_segment(segment)
        print(f"片段 {i+1}: {segment} -> {is_valid}")
    
    print()


def demo_error_handling():
    """演示错误处理功能"""
    print("=== 错误处理示例 ===")
    
    from core.utils import ErrorHandler
    
    # 记录不同类型的消息
    ErrorHandler.log_info("这是一条信息消息")
    ErrorHandler.log_warning("这是一条警告消息")
    ErrorHandler.handle_api_error("测试API", Exception("模拟错误"))
    ErrorHandler.handle_file_error("读取", "/不存在的文件.txt", FileNotFoundError("文件未找到"))
    ErrorHandler.log_success("操作成功完成")
    
    # 获取错误统计
    error_stats = ErrorHandler.get_error_statistics()
    if error_stats:
        print(f"错误统计: {error_stats}")
    
    print()


def main():
    """主函数 - 运行所有示例"""
    print("🚀 工具类使用示例")
    print("=" * 50)
    
    try:
        demo_config_management()
        demo_file_operations()
        demo_download_functionality()
        demo_retry_mechanism()
        demo_video_processing()
        demo_performance_monitoring()
        demo_data_validation()
        demo_error_handling()
        
        print("✅ 所有示例运行完成")
        
    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
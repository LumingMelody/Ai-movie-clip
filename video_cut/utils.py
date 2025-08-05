"""
Video Cut 工具模块 - 统一的辅助工具函数
整合并优化了原有的分散工具功能
"""

import time
import functools
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime
import threading
import queue
from contextlib import contextmanager

# 添加父项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.utils.config_manager import ErrorHandler, performance_monitor
except ImportError:
    # 如果无法导入核心模块，提供简单的备用实现
    class ErrorHandler:
        @staticmethod
        def handle_api_error(name, error, retry_count=0):
            print(f"Error in {name}: {error}")
        
        @staticmethod
        def log_warning(message):
            print(f"Warning: {message}")
        
        @staticmethod
        def log_info(message):
            print(f"Info: {message}")
    
    class PerformanceMonitor:
        @contextmanager
        def timer(self, operation):
            start = time.time()
            try:
                yield
            finally:
                elapsed = time.time() - start
                print(f"{operation} took {elapsed:.2f}s")
    
    performance_monitor = PerformanceMonitor()

F = TypeVar('F', bound=Callable[..., Any])


class RetryConfig:
    """重试配置类"""
    
    def __init__(self, max_retries: int = 3, delay: float = 2.0, 
                 backoff_factor: float = 1.5, max_delay: float = 60.0,
                 exceptions: tuple = (Exception,)):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.exceptions = exceptions


def retry(config: Optional[RetryConfig] = None, **kwargs) -> Callable[[F], F]:
    """
    增强的重试装饰器
    
    支持指数退避、自定义异常类型、详细日志等
    
    Args:
        config: 重试配置对象，或者使用关键字参数
        **kwargs: 重试参数 (max_retries, delay, backoff_factor, max_delay, exceptions)
    
    Returns:
        装饰器函数
    """
    if config is None:
        config = RetryConfig(**kwargs)
    elif kwargs:
        # 如果同时提供了config和kwargs，合并参数
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **func_kwargs):
            last_exception = None
            current_delay = config.delay
            
            for attempt in range(config.max_retries + 1):  # +1 包含初始尝试
                try:
                    return func(*args, **func_kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        ErrorHandler.handle_api_error(
                            f"{func.__name__}", e, attempt + 1
                        )
                        
                        # 计算实际延迟时间
                        actual_delay = min(current_delay, config.max_delay)
                        ErrorHandler.log_info(f"等待 {actual_delay:.1f} 秒后重试...")
                        time.sleep(actual_delay)
                        
                        # 指数退避
                        current_delay *= config.backoff_factor
                    else:
                        ErrorHandler.handle_api_error(
                            f"{func.__name__}", e, config.max_retries + 1
                        )
                        break
            
            # 如果所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.running = False
    
    def _worker(self):
        """工作线程"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # 毒丸，停止工作线程
                    break
                
                task_id, func, args, kwargs = task
                try:
                    result = func(*args, **kwargs)
                    self.result_queue.put((task_id, 'success', result))
                except Exception as e:
                    self.result_queue.put((task_id, 'error', str(e)))
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
    
    def start(self):
        """启动工作线程"""
        if self.running:
            return
        
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f'Worker-{i}')
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        ErrorHandler.log_info(f"任务队列已启动，工作线程数: {self.max_workers}")
    
    def stop(self):
        """停止工作线程"""
        if not self.running:
            return
        
        self.running = False
        
        # 发送毒丸停止所有工作线程
        for _ in range(self.max_workers):
            self.task_queue.put(None)
        
        # 等待所有工作线程结束
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        ErrorHandler.log_info("任务队列已停止")
    
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs):
        """提交任务"""
        if not self.running:
            self.start()
        
        self.task_queue.put((task_id, func, args, kwargs))
    
    def get_results(self, timeout: Optional[float] = None) -> List[tuple]:
        """获取所有可用结果"""
        results = []
        while True:
            try:
                result = self.result_queue.get(timeout=timeout)
                results.append(result)
                self.result_queue.task_done()
            except queue.Empty:
                break
        return results


class DataValidator:
    """数据验证工具"""
    
    @staticmethod
    def validate_json_schema(data: dict, schema: dict) -> bool:
        """
        验证JSON数据是否符合schema
        
        Args:
            data: 要验证的数据
            schema: JSON schema
            
        Returns:
            是否验证通过
        """
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            return True
        except (ImportError, ValidationError) as e:
            ErrorHandler.log_warning(f"JSON验证失败: {e}")
            return False
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
        """
        验证文件路径
        
        Args:
            file_path: 文件路径
            must_exist: 文件是否必须存在
            
        Returns:
            是否有效
        """
        if not file_path or not isinstance(file_path, str):
            return False
        
        if must_exist and not os.path.exists(file_path):
            return False
        
        # 检查路径是否包含非法字符
        illegal_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in file_path for char in illegal_chars):
            return False
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            是否有效
        """
        if not url or not isinstance(url, str):
            return False
        
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+' # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


class TimelineUtils:
    """时间轴工具类"""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        将秒数格式化为时间戳字符串
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间戳 (HH:MM:SS.mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> float:
        """
        解析时间戳字符串为秒数
        
        Args:
            timestamp: 时间戳字符串
            
        Returns:
            秒数
        """
        try:
            parts = timestamp.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            else:
                return float(timestamp)
        except (ValueError, AttributeError):
            ErrorHandler.log_warning(f"无法解析时间戳: {timestamp}")
            return 0.0
    
    @staticmethod
    def validate_timeline_segment(segment: dict) -> bool:
        """
        验证时间轴片段数据
        
        Args:
            segment: 片段数据
            
        Returns:
            是否有效
        """
        required_fields = ['start', 'end']
        
        for field in required_fields:
            if field not in segment:
                ErrorHandler.log_warning(f"片段缺少必需字段: {field}")
                return False
        
        start = segment['start']
        end = segment['end']
        
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            ErrorHandler.log_warning("片段时间必须是数字")
            return False
        
        if start >= end:
            ErrorHandler.log_warning(f"片段开始时间({start})必须小于结束时间({end})")
            return False
        
        if start < 0:
            ErrorHandler.log_warning("片段开始时间不能为负数")
            return False
        
        return True


@contextmanager
def timing_context(operation_name: str):
    """
    计时上下文管理器
    
    Args:
        operation_name: 操作名称
    
    Yields:
        计时器对象
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        ErrorHandler.log_info(f"{operation_name} 耗时: {elapsed:.2f}秒")


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        ErrorHandler.log_warning(f"JSON解析失败: {e}")
        return default


def safe_json_dumps(obj: Any, default: str = '{}') -> str:
    """
    安全的JSON序列化
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        JSON字符串或默认值
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        ErrorHandler.log_warning(f"JSON序列化失败: {e}")
        return default


def get_timestamp() -> str:
    """
    获取当前时间戳字符串
    
    Returns:
        格式化的时间戳
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ensure_directory_exists(directory: str) -> bool:
    """
    确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        是否成功创建或已存在
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        ErrorHandler.log_warning(f"创建目录失败 {directory}: {e}")
        return False


# 全局任务队列实例
task_queue = TaskQueue()

# 向后兼容的简单重试装饰器
def simple_retry(max_retries=3, delay=2):
    """简单的重试装饰器，保持向后兼容"""
    return retry(RetryConfig(max_retries=max_retries, delay=delay))

# 别名，保持向后兼容
retry_decorator = simple_retry
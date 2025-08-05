"""
文件工具函数 - 统一的文件操作工具集
"""

import os
import time
import requests
import hashlib
import json
import shutil
from typing import Optional, Dict, List, Union, Callable
from pathlib import Path
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, unquote

from .config_manager import ErrorHandler, config, performance_monitor


class FileCache:
    """文件缓存管理器"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(config.get_project_paths()['temp_dir'], 'file_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_index_file = os.path.join(self.cache_dir, 'cache_index.json')
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Dict]:
        """加载缓存索引"""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache_index(self):
        """保存缓存索引"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            ErrorHandler.log_warning(f"保存缓存索引失败: {e}")
    
    def get_cache_path(self, url: str) -> Optional[str]:
        """获取缓存文件路径"""
        url_hash = self._get_url_hash(url)
        if url_hash in self.cache_index:
            cache_info = self.cache_index[url_hash]
            cache_path = cache_info['path']
            if os.path.exists(cache_path):
                # 更新访问时间
                self.cache_index[url_hash]['last_access'] = time.time()
                self._save_cache_index()
                return cache_path
            else:
                # 缓存文件不存在，清理索引
                del self.cache_index[url_hash]
                self._save_cache_index()
        return None
    
    def add_to_cache(self, url: str, file_path: str) -> str:
        """添加文件到缓存"""
        url_hash = self._get_url_hash(url)
        cache_filename = f"{url_hash}_{os.path.basename(file_path)}"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        try:
            shutil.copy2(file_path, cache_path)
            self.cache_index[url_hash] = {
                'url': url,
                'path': cache_path,
                'created': time.time(),
                'last_access': time.time(),
                'size': os.path.getsize(cache_path)
            }
            self._save_cache_index()
            return cache_path
        except Exception as e:
            ErrorHandler.log_warning(f"添加文件到缓存失败: {e}")
            return file_path
    
    def _get_url_hash(self, url: str) -> str:
        """获取URL的哈希值"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def cleanup_cache(self, max_age_days: int = 7, max_size_mb: int = 1000):
        """清理缓存"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # 按访问时间排序
        cache_items = list(self.cache_index.items())
        cache_items.sort(key=lambda x: x[1]['last_access'])
        
        total_size = sum(item[1]['size'] for item in cache_items)
        removed_count = 0
        
        for url_hash, cache_info in cache_items:
            should_remove = False
            
            # 检查年龄
            if current_time - cache_info['created'] > max_age_seconds:
                should_remove = True
            
            # 检查大小限制
            if total_size > max_size_bytes:
                should_remove = True
                total_size -= cache_info['size']
            
            if should_remove:
                try:
                    if os.path.exists(cache_info['path']):
                        os.remove(cache_info['path'])
                    del self.cache_index[url_hash]
                    removed_count += 1
                except Exception as e:
                    ErrorHandler.log_warning(f"清理缓存文件失败: {e}")
        
        if removed_count > 0:
            self._save_cache_index()
            ErrorHandler.log_info(f"清理了 {removed_count} 个缓存文件")


# 全局文件缓存实例
file_cache = FileCache()


def download_file_with_retry(url: str, save_path: str, max_retries: int = 3, timeout: int = 30, 
                           verbose: bool = True, use_cache: bool = True, 
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """
    下载文件并支持重试、缓存和进度回调
    
    Args:
        url: 文件URL
        save_path: 保存路径
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        verbose: 是否显示详细进度信息
        use_cache: 是否使用缓存
        progress_callback: 进度回调函数(downloaded, total)
        
    Returns:
        是否下载成功
    """
    # 检查缓存
    if use_cache:
        cached_path = file_cache.get_cache_path(url)
        if cached_path:
            try:
                shutil.copy2(cached_path, save_path)
                if verbose:
                    ErrorHandler.log_success(f"从缓存加载文件: {save_path}")
                return True
            except Exception as e:
                ErrorHandler.log_warning(f"从缓存复制文件失败: {e}")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            if verbose:
                print(f"下载文件: {url} -> {save_path} (尝试 {attempt + 1}/{max_retries})")
            
            # 发送请求
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 写入文件
            with open(save_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度和回调
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if verbose:
                                print(f"\r下载进度: {progress:.1f}%", end='', flush=True)
                            if progress_callback:
                                progress_callback(downloaded, total_size)
            
            if verbose:
                print()  # 换行
                ErrorHandler.log_success(f"文件下载成功: {save_path}")
            
            # 添加到缓存
            if use_cache:
                file_cache.add_to_cache(url, save_path)
            
            return True
            
        except requests.exceptions.RequestException as e:
            ErrorHandler.handle_api_error("文件下载", e, attempt + 1)
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                if verbose:
                    print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                return False
        except Exception as e:
            ErrorHandler.handle_file_error("下载", save_path, e)
            return False
    
    return False


def ensure_file_exists(file_path: str) -> bool:
    """
    确保文件存在
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件是否存在
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def get_file_size(file_path: str) -> int:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    if ensure_file_exists(file_path):
        return os.path.getsize(file_path)
    return 0


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（包含点号）
    """
    return Path(file_path).suffix.lower()


def is_video_file(file_path: str) -> bool:
    """
    判断是否为视频文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为视频文件
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg'}
    return get_file_extension(file_path) in video_extensions


def is_image_file(file_path: str) -> bool:
    """
    判断是否为图片文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
    return get_file_extension(file_path) in image_extensions


def is_audio_file(file_path: str) -> bool:
    """
    判断是否为音频文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为音频文件
    """
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'}
    return get_file_extension(file_path) in audio_extensions


def batch_download_files(urls_and_paths: List[tuple], max_workers: int = 4, 
                        use_cache: bool = True, verbose: bool = True) -> Dict[str, bool]:
    """
    批量下载文件
    
    Args:
        urls_and_paths: [(url, save_path), ...] 列表
        max_workers: 最大并发数
        use_cache: 是否使用缓存
        verbose: 是否显示详细信息
        
    Returns:
        下载结果字典 {url: success}
    """
    results = {}
    
    with performance_monitor.timer("批量文件下载"):
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_url = {
                executor.submit(download_file_with_retry, url, path, 
                              use_cache=use_cache, verbose=verbose): url
                for url, path in urls_and_paths
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
                    results[url] = success
                    if verbose:
                        status = "成功" if success else "失败"
                        ErrorHandler.log_info(f"下载{status}: {url}")
                except Exception as e:
                    results[url] = False
                    ErrorHandler.handle_api_error("批量下载", e)
    
    success_count = sum(results.values())
    total_count = len(results)
    ErrorHandler.log_info(f"批量下载完成: {success_count}/{total_count} 成功")
    
    return results


def get_file_info(file_path: str) -> Dict[str, Union[str, int, float]]:
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件信息字典
    """
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        'path': file_path,
        'name': os.path.basename(file_path),
        'extension': get_file_extension(file_path),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'accessed': stat.st_atime,
        'is_video': is_video_file(file_path),
        'is_image': is_image_file(file_path),
        'is_audio': is_audio_file(file_path)
    }


def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """
    获取文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
        
    Returns:
        文件哈希值
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        ErrorHandler.handle_file_error("计算哈希", file_path, e)
        return None


def safe_copy_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """
    安全复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否复制成功
    """
    try:
        if not os.path.exists(src):
            ErrorHandler.log_warning(f"源文件不存在: {src}")
            return False
        
        if os.path.exists(dst) and not overwrite:
            ErrorHandler.log_warning(f"目标文件已存在: {dst}")
            return False
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        shutil.copy2(src, dst)
        ErrorHandler.log_success(f"文件复制成功: {src} -> {dst}")
        return True
        
    except Exception as e:
        ErrorHandler.handle_file_error("复制", f"{src} -> {dst}", e)
        return False


def safe_move_file(src: str, dst: str, overwrite: bool = False) -> bool:
    """
    安全移动文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        是否移动成功
    """
    try:
        if not os.path.exists(src):
            ErrorHandler.log_warning(f"源文件不存在: {src}")
            return False
        
        if os.path.exists(dst) and not overwrite:
            ErrorHandler.log_warning(f"目标文件已存在: {dst}")
            return False
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        shutil.move(src, dst)
        ErrorHandler.log_success(f"文件移动成功: {src} -> {dst}")
        return True
        
    except Exception as e:
        ErrorHandler.handle_file_error("移动", f"{src} -> {dst}", e)
        return False


@contextmanager
def temporary_file(suffix: str = '', prefix: str = 'temp_', directory: str = None):
    """
    临时文件上下文管理器
    
    Args:
        suffix: 文件后缀
        prefix: 文件前缀
        directory: 临时目录
    
    Yields:
        临时文件路径
    """
    from .config_manager import PathHelper
    
    if directory:
        temp_path = os.path.join(directory, f"{prefix}{os.urandom(8).hex()}{suffix}")
    else:
        temp_path = PathHelper.get_project_temp_path(suffix, prefix)
    
    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                ErrorHandler.log_warning(f"清理临时文件失败: {temp_path}, {e}")


def extract_filename_from_url(url: str) -> str:
    """
    从URL中提取文件名
    
    Args:
        url: URL地址
        
    Returns:
        提取的文件名
    """
    try:
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path))
        if not filename or '.' not in filename:
            # 如果没有有效文件名，生成一个
            filename = f"download_{int(time.time())}"
        return filename
    except Exception:
        return f"download_{int(time.time())}"


def is_url_accessible(url: str, timeout: int = 10) -> bool:
    """
    检查URL是否可访问
    
    Args:
        url: URL地址
        timeout: 超时时间
        
    Returns:
        是否可访问
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception:
        return False


# 工具函数别名，保持向后兼容
download_file = download_file_with_retry
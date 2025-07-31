"""
文件工具函数
"""

import os
import time
import requests
from typing import Optional
from pathlib import Path


def download_file_with_retry(url: str, save_path: str, max_retries: int = 3, timeout: int = 30) -> bool:
    """
    下载文件并支持重试
    
    Args:
        url: 文件URL
        save_path: 保存路径
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        
    Returns:
        是否下载成功
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    for attempt in range(max_retries):
        try:
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
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end='', flush=True)
            
            print()  # 换行
            print(f"✅ 文件下载成功: {save_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"❌ 下载失败，已达到最大重试次数")
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
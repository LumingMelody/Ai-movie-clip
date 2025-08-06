"""
性能优化工具
包括流式处理、分段渲染、内存管理等
"""
import os
import gc
import psutil
from typing import Any, Iterator, List, Optional, Tuple
from pathlib import Path
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import lru_cache
import numpy as np


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, max_memory_percent: float = 80.0):
        """
        初始化内存管理器
        
        Args:
            max_memory_percent: 最大内存使用百分比
        """
        self.max_memory_percent = max_memory_percent
        self.logger = logging.getLogger(__name__)
    
    def check_memory_usage(self) -> dict:
        """检查当前内存使用情况"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total / (1024**3),  # GB
            "available": memory.available / (1024**3),  # GB
            "percent": memory.percent,
            "used": memory.used / (1024**3)  # GB
        }
    
    def is_memory_sufficient(self, required_gb: float) -> bool:
        """检查是否有足够的内存"""
        memory_info = self.check_memory_usage()
        return memory_info["available"] >= required_gb
    
    def estimate_video_memory(self, duration: float, resolution: Tuple[int, int], fps: int) -> float:
        """
        估算视频处理所需内存
        
        Args:
            duration: 视频时长（秒）
            resolution: 分辨率(width, height)
            fps: 帧率
            
        Returns:
            估算的内存需求（GB）
        """
        width, height = resolution
        # 每帧字节数 (RGB, 3 bytes per pixel)
        bytes_per_frame = width * height * 3
        # 总帧数
        total_frames = duration * fps
        # 估算内存（考虑处理开销，乘以2）
        estimated_memory_gb = (bytes_per_frame * total_frames * 2) / (1024**3)
        
        return estimated_memory_gb
    
    def optimize_for_memory(self, duration: float, resolution: Tuple[int, int], fps: int) -> dict:
        """
        根据可用内存优化视频参数
        
        Returns:
            优化后的参数
        """
        required_memory = self.estimate_video_memory(duration, resolution, fps)
        memory_info = self.check_memory_usage()
        
        optimized = {
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "chunk_size": None
        }
        
        if required_memory > memory_info["available"]:
            self.logger.warning(f"内存不足: 需要{required_memory:.2f}GB, 可用{memory_info['available']:.2f}GB")
            
            # 建议分段处理
            chunks = int(np.ceil(required_memory / (memory_info["available"] * 0.7)))
            chunk_duration = duration / chunks
            
            optimized["chunk_size"] = chunk_duration
            self.logger.info(f"建议分{chunks}段处理，每段{chunk_duration:.1f}秒")
            
            # 如果还是不够，降低分辨率
            if chunks > 10:
                new_width = int(resolution[0] * 0.75)
                new_height = int(resolution[1] * 0.75)
                optimized["resolution"] = (new_width, new_height)
                self.logger.info(f"建议降低分辨率至{new_width}x{new_height}")
        
        return optimized
    
    def cleanup(self):
        """清理内存"""
        gc.collect()
        self.logger.info("已执行内存清理")


class ChunkedVideoProcessor:
    """分段视频处理器"""
    
    def __init__(self, chunk_duration: float = 30.0):
        """
        初始化分段处理器
        
        Args:
            chunk_duration: 每段的默认时长（秒）
        """
        self.chunk_duration = chunk_duration
        self.temp_dir = tempfile.mkdtemp(prefix="video_chunks_")
        self.logger = logging.getLogger(__name__)
    
    def split_timeline_into_chunks(self, timeline: dict) -> List[dict]:
        """
        将时间轴分割成多个段
        
        Args:
            timeline: 完整的时间轴
            
        Returns:
            分段后的时间轴列表
        """
        total_duration = timeline["timeline"]["duration"]
        
        if total_duration <= self.chunk_duration:
            return [timeline]
        
        chunks = []
        num_chunks = int(np.ceil(total_duration / self.chunk_duration))
        
        for i in range(num_chunks):
            start_time = i * self.chunk_duration
            end_time = min((i + 1) * self.chunk_duration, total_duration)
            
            chunk_timeline = self._create_chunk_timeline(
                timeline, start_time, end_time
            )
            chunks.append(chunk_timeline)
        
        self.logger.info(f"时间轴已分割为{num_chunks}段")
        return chunks
    
    def _create_chunk_timeline(self, timeline: dict, start: float, end: float) -> dict:
        """创建分段时间轴"""
        import copy
        chunk = copy.deepcopy(timeline)
        chunk["timeline"]["duration"] = end - start
        
        # 调整所有轨道的片段
        for track in chunk["timeline"]["tracks"]:
            new_clips = []
            for clip in track.get("clips", []):
                clip_start = clip.get("start", 0)
                clip_end = clip.get("end", 0)
                
                # 检查片段是否在当前段内
                if clip_end > start and clip_start < end:
                    # 调整片段时间
                    adjusted_clip = clip.copy()
                    adjusted_clip["start"] = max(0, clip_start - start)
                    adjusted_clip["end"] = min(end - start, clip_end - start)
                    new_clips.append(adjusted_clip)
            
            track["clips"] = new_clips
        
        return chunk
    
    def process_chunks_parallel(self, chunks: List[dict], process_func, max_workers: int = 2) -> List[Any]:
        """
        并行处理视频段
        
        Args:
            chunks: 分段时间轴列表
            process_func: 处理函数
            max_workers: 最大并行数
            
        Returns:
            处理结果列表
        """
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                chunk_output = os.path.join(self.temp_dir, f"chunk_{i}.mp4")
                future = executor.submit(process_func, chunk, chunk_output)
                futures.append(future)
            
            for i, future in enumerate(futures):
                self.logger.info(f"处理第{i+1}/{len(chunks)}段...")
                result = future.result()
                results.append(result)
        
        return results
    
    def merge_chunks(self, chunk_files: List[str], output_path: str):
        """
        合并视频段
        
        Args:
            chunk_files: 分段视频文件列表
            output_path: 输出路径
        """
        from moviepy import VideoFileClip, concatenate_videoclips
        
        clips = []
        for file_path in chunk_files:
            if os.path.exists(file_path):
                clip = VideoFileClip(file_path)
                clips.append(clip)
        
        if clips:
            final_video = concatenate_videoclips(clips, method="compose")
            final_video.write_videofile(output_path)
            
            # 清理临时文件
            for clip in clips:
                clip.close()
            
            self.logger.info(f"视频段已合并至: {output_path}")
    
    def cleanup(self):
        """清理临时文件"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.logger.info("临时文件已清理")


class StreamingProcessor:
    """流式处理器"""
    
    def __init__(self, buffer_size: int = 1024):
        """
        初始化流式处理器
        
        Args:
            buffer_size: 缓冲区大小
        """
        self.buffer_size = buffer_size
        self.logger = logging.getLogger(__name__)
    
    def process_video_stream(self, input_path: str, process_func) -> Iterator[np.ndarray]:
        """
        流式处理视频
        
        Args:
            input_path: 输入视频路径
            process_func: 帧处理函数
            
        Yields:
            处理后的帧
        """
        import cv2
        
        cap = cv2.VideoCapture(input_path)
        
        try:
            frame_buffer = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 处理帧
                processed_frame = process_func(frame)
                frame_buffer.append(processed_frame)
                
                # 当缓冲区满时，批量输出
                if len(frame_buffer) >= self.buffer_size:
                    for f in frame_buffer:
                        yield f
                    frame_buffer = []
                    gc.collect()  # 清理内存
            
            # 输出剩余帧
            for f in frame_buffer:
                yield f
                
        finally:
            cap.release()
    
    def write_video_stream(self, frames: Iterator[np.ndarray], output_path: str, 
                          fps: int = 30, resolution: Optional[Tuple[int, int]] = None):
        """
        流式写入视频
        
        Args:
            frames: 帧迭代器
            output_path: 输出路径
            fps: 帧率
            resolution: 分辨率
        """
        import cv2
        
        writer = None
        
        try:
            for i, frame in enumerate(frames):
                if writer is None:
                    height, width = frame.shape[:2]
                    if resolution:
                        width, height = resolution
                        frame = cv2.resize(frame, (width, height))
                    
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                
                writer.write(frame)
                
                # 定期清理内存
                if i % 1000 == 0:
                    gc.collect()
                    self.logger.debug(f"已处理{i}帧")
        
        finally:
            if writer:
                writer.release()
                self.logger.info(f"视频已保存至: {output_path}")


class ParallelProcessor:
    """并行处理器"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化并行处理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers or min(4, os.cpu_count() or 1)
        self.logger = logging.getLogger(__name__)
    
    def process_tracks_parallel(self, tracks: List[dict], process_func) -> List[Any]:
        """
        并行处理多个轨道
        
        Args:
            tracks: 轨道列表
            process_func: 处理函数
            
        Returns:
            处理结果列表
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for track in tracks:
                future = executor.submit(process_func, track)
                futures.append(future)
            
            for i, future in enumerate(futures):
                result = future.result()
                results.append(result)
                self.logger.debug(f"轨道{i+1}/{len(tracks)}处理完成")
        
        return results
    
    def batch_process(self, items: List[Any], process_func, batch_size: int = 10) -> List[Any]:
        """
        批量处理项目
        
        Args:
            items: 待处理项目列表
            process_func: 处理函数
            batch_size: 批大小
            
        Returns:
            处理结果列表
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                batch_results = list(executor.map(process_func, batch))
                results.extend(batch_results)
            
            self.logger.info(f"已处理 {min(i + batch_size, len(items))}/{len(items)} 项")
            
            # 批次间清理内存
            gc.collect()
        
        return results


# 缓存装饰器
def cache_result(cache_dir: str = ".cache"):
    """
    缓存函数结果的装饰器
    
    Args:
        cache_dir: 缓存目录
    """
    def decorator(func):
        @lru_cache(maxsize=128)
        def wrapper(*args, **kwargs):
            import hashlib
            import pickle
            
            # 生成缓存键
            cache_key = hashlib.md5(
                f"{func.__name__}_{args}_{kwargs}".encode()
            ).hexdigest()
            
            cache_path = Path(cache_dir) / f"{cache_key}.pkl"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 尝试从缓存读取
            if cache_path.exists():
                try:
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
                except:
                    pass
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存到缓存
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(result, f)
            except:
                pass
            
            return result
        
        return wrapper
    
    return decorator
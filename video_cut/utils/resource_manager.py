"""
资源管理器
优化视频、音频、图片等资源的管理和查找
"""
import os
import json
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import logging
import hashlib
from concurrent.futures import ThreadPoolExecutor


class ResourceManager:
    """统一资源管理器"""
    
    def __init__(self, base_dir: str = "./resources", auto_cleanup: bool = True):
        """
        初始化资源管理器
        
        Args:
            base_dir: 资源基础目录
            auto_cleanup: 是否自动清理临时文件
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.video_dir = self.base_dir / "videos"
        self.audio_dir = self.base_dir / "audios"
        self.image_dir = self.base_dir / "images"
        self.temp_dir = self.base_dir / "temp"
        self.cache_dir = self.base_dir / ".cache"
        
        for dir_path in [self.video_dir, self.audio_dir, self.image_dir, self.temp_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.auto_cleanup = auto_cleanup
        self.logger = logging.getLogger(__name__)
        
        # 资源索引
        self.resource_index = self._build_resource_index()
        
        # 临时文件追踪
        self.temp_files = set()
    
    def _build_resource_index(self) -> Dict[str, List[Path]]:
        """构建资源索引"""
        index = {
            "videos": [],
            "audios": [],
            "images": []
        }
        
        # 视频格式
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        for file_path in self.video_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_exts:
                index["videos"].append(file_path)
        
        # 音频格式
        audio_exts = {'.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg'}
        for file_path in self.audio_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in audio_exts:
                index["audios"].append(file_path)
        
        # 图片格式
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
        for file_path in self.image_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_exts:
                index["images"].append(file_path)
        
        self.logger.info(f"资源索引: {len(index['videos'])}个视频, "
                        f"{len(index['audios'])}个音频, {len(index['images'])}个图片")
        
        return index
    
    def find_resource(self, name: str, resource_type: Optional[str] = None) -> Optional[Path]:
        """
        查找资源文件
        
        Args:
            name: 资源名称或路径
            resource_type: 资源类型 ("video", "audio", "image")
        
        Returns:
            资源文件路径，如果未找到返回None
        """
        # 如果是绝对路径且存在，直接返回
        if os.path.isabs(name):
            path = Path(name)
            if path.exists():
                return path
        
        # 在资源目录中查找
        search_dirs = []
        if resource_type == "video":
            search_dirs = [self.video_dir]
        elif resource_type == "audio":
            search_dirs = [self.audio_dir]
        elif resource_type == "image":
            search_dirs = [self.image_dir]
        else:
            search_dirs = [self.video_dir, self.audio_dir, self.image_dir]
        
        for dir_path in search_dirs:
            # 精确匹配
            exact_path = dir_path / name
            if exact_path.exists():
                return exact_path
            
            # 模糊匹配（忽略扩展名）
            name_without_ext = Path(name).stem
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    if file_path.stem == name_without_ext:
                        return file_path
                    # 部分匹配
                    if name_without_ext.lower() in file_path.stem.lower():
                        return file_path
        
        return None
    
    def add_resource(self, source_path: str, resource_type: str, 
                    copy: bool = True, name: Optional[str] = None) -> Path:
        """
        添加资源到管理器
        
        Args:
            source_path: 源文件路径
            resource_type: 资源类型
            copy: 是否复制文件（False则移动）
            name: 新文件名（可选）
        
        Returns:
            资源在管理器中的路径
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")
        
        # 确定目标目录
        if resource_type == "video":
            target_dir = self.video_dir
        elif resource_type == "audio":
            target_dir = self.audio_dir
        elif resource_type == "image":
            target_dir = self.image_dir
        else:
            target_dir = self.temp_dir
        
        # 确定目标文件名
        if name:
            target_name = name
        else:
            # 使用时间戳和原始名称
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_name = f"{timestamp}_{source.name}"
        
        target_path = target_dir / target_name
        
        # 复制或移动文件
        if copy:
            shutil.copy2(source, target_path)
        else:
            shutil.move(str(source), str(target_path))
        
        # 更新索引
        if resource_type == "video":
            self.resource_index["videos"].append(target_path)
        elif resource_type == "audio":
            self.resource_index["audios"].append(target_path)
        elif resource_type == "image":
            self.resource_index["images"].append(target_path)
        
        self.logger.info(f"添加资源: {target_path}")
        return target_path
    
    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "temp_") -> Path:
        """
        创建临时文件
        
        Args:
            suffix: 文件后缀
            prefix: 文件前缀
        
        Returns:
            临时文件路径
        """
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=self.temp_dir,
            delete=False
        )
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        self.temp_files.add(temp_path)
        return temp_path
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in list(self.temp_files):
            try:
                if temp_file.exists():
                    temp_file.unlink()
                self.temp_files.remove(temp_file)
            except Exception as e:
                self.logger.warning(f"清理临时文件失败: {temp_file}, {e}")
        
        # 清理temp目录中的旧文件（超过24小时）
        import time
        current_time = time.time()
        for file_path in self.temp_dir.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 86400:  # 24小时
                    try:
                        file_path.unlink()
                        self.logger.debug(f"删除旧临时文件: {file_path}")
                    except:
                        pass
    
    def get_resource_info(self, path: Path) -> Dict[str, Any]:
        """
        获取资源文件信息
        
        Args:
            path: 资源路径
        
        Returns:
            资源信息字典
        """
        if not path.exists():
            return {}
        
        stat = path.stat()
        
        info = {
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix.lower()
        }
        
        # 获取媒体文件的详细信息
        if path.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv'}:
            info["type"] = "video"
            info.update(self._get_video_info(path))
        elif path.suffix.lower() in {'.mp3', '.wav', '.aac', '.m4a'}:
            info["type"] = "audio"
            info.update(self._get_audio_info(path))
        elif path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif'}:
            info["type"] = "image"
            info.update(self._get_image_info(path))
        
        return info
    
    def _get_video_info(self, path: Path) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(str(path))
            info = {
                "duration": clip.duration,
                "fps": clip.fps,
                "resolution": {"width": clip.w, "height": clip.h}
            }
            clip.close()
            return info
        except:
            return {}
    
    def _get_audio_info(self, path: Path) -> Dict[str, Any]:
        """获取音频信息"""
        try:
            from moviepy import AudioFileClip
            clip = AudioFileClip(str(path))
            info = {
                "duration": clip.duration,
                "channels": clip.nchannels if hasattr(clip, 'nchannels') else None
            }
            clip.close()
            return info
        except:
            return {}
    
    def _get_image_info(self, path: Path) -> Dict[str, Any]:
        """获取图片信息"""
        try:
            from PIL import Image
            with Image.open(path) as img:
                return {
                    "resolution": {"width": img.width, "height": img.height},
                    "mode": img.mode
                }
        except:
            return {}
    
    def optimize_resource(self, path: Path, target_size: Optional[Tuple[int, int]] = None,
                         quality: int = 85) -> Path:
        """
        优化资源文件（压缩、调整大小等）
        
        Args:
            path: 资源路径
            target_size: 目标尺寸 (width, height)
            quality: 质量（1-100）
        
        Returns:
            优化后的文件路径
        """
        if path.suffix.lower() in {'.jpg', '.jpeg', '.png'}:
            return self._optimize_image(path, target_size, quality)
        elif path.suffix.lower() in {'.mp4', '.avi', '.mov'}:
            return self._optimize_video(path, target_size, quality)
        else:
            return path
    
    def _optimize_image(self, path: Path, target_size: Optional[Tuple[int, int]], 
                       quality: int) -> Path:
        """优化图片"""
        try:
            from PIL import Image
            
            img = Image.open(path)
            
            # 调整大小
            if target_size:
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
            
            # 保存优化后的图片
            optimized_path = self.create_temp_file(suffix=path.suffix, prefix="optimized_")
            img.save(optimized_path, quality=quality, optimize=True)
            
            self.logger.info(f"图片优化完成: {path} -> {optimized_path}")
            return optimized_path
            
        except Exception as e:
            self.logger.error(f"图片优化失败: {e}")
            return path
    
    def _optimize_video(self, path: Path, target_size: Optional[Tuple[int, int]], 
                       quality: int) -> Path:
        """优化视频"""
        # TODO: 实现视频优化
        return path
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        stats = {
            "total_videos": len(self.resource_index["videos"]),
            "total_audios": len(self.resource_index["audios"]),
            "total_images": len(self.resource_index["images"]),
            "temp_files": len(self.temp_files),
            "total_size_mb": 0
        }
        
        # 计算总大小
        for resource_list in self.resource_index.values():
            for path in resource_list:
                if path.exists():
                    stats["total_size_mb"] += path.stat().st_size / (1024 * 1024)
        
        return stats
    
    def export_index(self, output_path: str):
        """导出资源索引"""
        index_data = {
            "created": datetime.now().isoformat(),
            "base_dir": str(self.base_dir),
            "resources": {
                "videos": [str(p) for p in self.resource_index["videos"]],
                "audios": [str(p) for p in self.resource_index["audios"]],
                "images": [str(p) for p in self.resource_index["images"]]
            },
            "statistics": self.get_statistics()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"资源索引已导出: {output_path}")
    
    def __del__(self):
        """析构函数，清理临时文件"""
        if self.auto_cleanup:
            self.cleanup_temp_files()
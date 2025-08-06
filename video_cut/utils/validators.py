"""
输入验证和错误处理工具
"""
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path


class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_duration(duration: Any) -> float:
        """验证并转换时长参数"""
        if duration is None:
            raise ValueError("时长不能为空")
        
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            raise ValueError(f"无效的时长格式: {duration}")
        
        if duration <= 0:
            raise ValueError(f"时长必须大于0，当前值: {duration}")
        
        if duration > 3600:  # 1小时
            raise ValueError(f"时长不能超过1小时，当前值: {duration}秒")
        
        return duration
    
    @staticmethod
    def validate_resolution(resolution: Dict) -> Dict:
        """验证分辨率设置"""
        if not isinstance(resolution, dict):
            raise ValueError("分辨率必须是字典格式")
        
        if 'width' not in resolution or 'height' not in resolution:
            raise ValueError("分辨率必须包含width和height")
        
        width = resolution['width']
        height = resolution['height']
        
        if not isinstance(width, int) or not isinstance(height, int):
            raise ValueError("分辨率宽高必须是整数")
        
        if width <= 0 or height <= 0:
            raise ValueError(f"分辨率必须为正数: {width}x{height}")
        
        if width > 7680 or height > 4320:  # 8K
            raise ValueError(f"分辨率超过8K限制: {width}x{height}")
        
        return resolution
    
    @staticmethod
    def validate_fps(fps: Any) -> int:
        """验证帧率"""
        try:
            fps = int(fps)
        except (TypeError, ValueError):
            raise ValueError(f"无效的帧率格式: {fps}")
        
        if fps not in [24, 25, 30, 48, 50, 60, 120]:
            raise ValueError(f"不支持的帧率: {fps}，支持的帧率: 24,25,30,48,50,60,120")
        
        return fps
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> Path:
        """验证文件路径"""
        if not path:
            raise ValueError("文件路径不能为空")
        
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        # 检查文件扩展名
        if path_obj.suffix:
            ext = path_obj.suffix.lower()
            valid_video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
            valid_audio_exts = ['.mp3', '.wav', '.aac', '.m4a', '.flac']
            valid_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            
            all_valid_exts = valid_video_exts + valid_audio_exts + valid_image_exts
            
            if must_exist and ext not in all_valid_exts:
                raise ValueError(f"不支持的文件格式: {ext}")
        
        return path_obj
    
    @staticmethod
    def validate_natural_language(text: str) -> str:
        """验证自然语言输入"""
        if not text or not isinstance(text, str):
            raise ValueError("输入文本不能为空")
        
        text = text.strip()
        
        if len(text) < 5:
            raise ValueError("描述太短，请提供更详细的描述（至少5个字符）")
        
        if len(text) > 5000:
            raise ValueError("描述太长，请控制在5000字符以内")
        
        # 检查是否包含恶意内容
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onclick=',
            r'onerror=',
            r'__import__',
            r'eval\(',
            r'exec\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("输入包含不安全的内容")
        
        return text
    
    @staticmethod
    def validate_timeline(timeline: Dict) -> Dict:
        """验证时间轴JSON结构"""
        if not isinstance(timeline, dict):
            raise ValueError("时间轴必须是字典格式")
        
        # 检查必要字段
        if 'timeline' not in timeline:
            raise ValueError("时间轴缺少'timeline'字段")
        
        tl = timeline['timeline']
        
        if 'duration' not in tl:
            raise ValueError("时间轴缺少'duration'字段")
        
        if 'tracks' not in tl:
            raise ValueError("时间轴缺少'tracks'字段")
        
        # 验证duration
        InputValidator.validate_duration(tl['duration'])
        
        # 验证tracks
        if not isinstance(tl['tracks'], list):
            raise ValueError("'tracks'必须是列表格式")
        
        for i, track in enumerate(tl['tracks']):
            if not isinstance(track, dict):
                raise ValueError(f"轨道{i}必须是字典格式")
            
            if 'type' not in track:
                raise ValueError(f"轨道{i}缺少'type'字段")
            
            if track['type'] not in ['video', 'audio', 'text', 'effect']:
                raise ValueError(f"轨道{i}的类型'{track['type']}'不支持")
            
            if 'clips' not in track:
                raise ValueError(f"轨道{i}缺少'clips'字段")
            
            # 验证clips时间不重叠
            clips = track.get('clips', [])
            for j, clip in enumerate(clips):
                if 'start' not in clip or 'end' not in clip:
                    raise ValueError(f"轨道{i}的片段{j}缺少时间信息")
                
                if clip['end'] <= clip['start']:
                    raise ValueError(f"轨道{i}的片段{j}结束时间必须大于开始时间")
                
                if clip['end'] > tl['duration']:
                    raise ValueError(f"轨道{i}的片段{j}超出视频总时长")
        
        return timeline


class ResourceValidator:
    """资源验证器"""
    
    @staticmethod
    def check_resource_availability(resource_dir: str) -> Dict[str, List[str]]:
        """检查资源目录中的可用资源"""
        resource_dir = Path(resource_dir)
        
        if not resource_dir.exists():
            os.makedirs(resource_dir, exist_ok=True)
            return {"videos": [], "audios": [], "images": []}
        
        resources = {
            "videos": [],
            "audios": [],
            "images": []
        }
        
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        audio_exts = {'.mp3', '.wav', '.aac', '.m4a', '.flac'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        for file_path in resource_dir.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in video_exts:
                    resources["videos"].append(str(file_path))
                elif ext in audio_exts:
                    resources["audios"].append(str(file_path))
                elif ext in image_exts:
                    resources["images"].append(str(file_path))
        
        return resources
    
    @staticmethod
    def validate_resource_size(file_path: str, max_size_mb: float = 500) -> bool:
        """验证资源文件大小"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        size_mb = path.stat().st_size / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise ValueError(f"文件太大: {size_mb:.2f}MB，最大限制: {max_size_mb}MB")
        
        return True


class ErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def handle_api_error(error: Exception, fallback_func=None):
        """处理API调用错误"""
        error_msg = str(error)
        
        if "API key" in error_msg or "authentication" in error_msg.lower():
            return {
                "error": "API认证失败",
                "message": "请检查API密钥配置",
                "fallback": fallback_func() if fallback_func else None
            }
        
        if "rate limit" in error_msg.lower():
            return {
                "error": "API限流",
                "message": "请求过于频繁，请稍后重试",
                "fallback": fallback_func() if fallback_func else None
            }
        
        if "timeout" in error_msg.lower():
            return {
                "error": "请求超时",
                "message": "网络连接超时，请检查网络",
                "fallback": fallback_func() if fallback_func else None
            }
        
        return {
            "error": "API调用失败",
            "message": error_msg,
            "fallback": fallback_func() if fallback_func else None
        }
    
    @staticmethod
    def handle_file_error(error: Exception):
        """处理文件操作错误"""
        if isinstance(error, FileNotFoundError):
            return {
                "error": "文件不存在",
                "message": str(error),
                "suggestion": "请检查文件路径是否正确"
            }
        
        if isinstance(error, PermissionError):
            return {
                "error": "权限不足",
                "message": str(error),
                "suggestion": "请检查文件权限设置"
            }
        
        return {
            "error": "文件操作失败",
            "message": str(error)
        }
    
    @staticmethod
    def handle_video_processing_error(error: Exception):
        """处理视频处理错误"""
        error_msg = str(error).lower()
        
        if "memory" in error_msg:
            return {
                "error": "内存不足",
                "message": "视频处理需要更多内存",
                "suggestion": "请尝试降低分辨率或缩短时长"
            }
        
        if "codec" in error_msg or "format" in error_msg:
            return {
                "error": "格式不支持",
                "message": "视频格式或编码不支持",
                "suggestion": "请转换为MP4格式后重试"
            }
        
        if "corrupt" in error_msg:
            return {
                "error": "文件损坏",
                "message": "视频文件可能已损坏",
                "suggestion": "请检查原始文件是否完整"
            }
        
        return {
            "error": "视频处理失败",
            "message": str(error)
        }
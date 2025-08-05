# -*- coding: utf-8 -*-
"""
视频处理工具类 - 提供通用的视频操作功能
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from moviepy import VideoFileClip, concatenate_videoclips

from core.utils.config_manager import config, ErrorHandler


class VideoProcessor:
    """视频处理器 - 提供安全的视频操作方法"""
    
    def __init__(self):
        self.output_config = config.get_config('output')
    
    def safe_load_video(self, video_path: str) -> Tuple[Optional[VideoFileClip], bool]:
        """
        安全加载视频文件
        
        Returns:
            Tuple[VideoFileClip, has_audio]: 视频对象和音频状态
        """
        try:
            clip = VideoFileClip(video_path)
            has_audio = self._check_audio_availability(clip)
            
            if not has_audio and clip.audio is not None:
                clip = clip.without_audio()
            
            self._log_video_info(video_path, clip, has_audio)
            return clip, has_audio
            
        except Exception as e:
            ErrorHandler.handle_file_error("视频加载", video_path, e)
            return None, False
    
    def _check_audio_availability(self, clip: VideoFileClip) -> bool:
        """检查音频是否可用"""
        try:
            if clip.audio is None:
                return False
            
            if not hasattr(clip.audio, 'reader') or clip.audio.reader is None:
                return False
            
            # 测试音频是否真的可用
            _ = clip.audio.duration
            return True
            
        except Exception:
            return False
    
    def _log_video_info(self, video_path: str, clip: VideoFileClip, has_audio: bool):
        """记录视频信息"""
        print(f"    📊 视频信息:")
        print(f"      - 文件: {os.path.basename(video_path)}")
        print(f"      - 时长: {clip.duration:.1f}秒")
        print(f"      - 分辨率: {clip.w}x{clip.h}")
        print(f"      - FPS: {clip.fps}")
        print(f"      - 音频: {'有' if has_audio else '无'}")
    
    def safe_clip_segment(self, clip: VideoFileClip, start: float, end: float, 
                         has_audio: bool = False) -> Optional[VideoFileClip]:
        """
        安全剪辑视频片段
        
        Args:
            clip: 视频对象
            start: 开始时间
            end: 结束时间  
            has_audio: 是否有音频
            
        Returns:
            剪辑后的视频片段
        """
        # 确保时间范围有效
        start = max(0, start)
        end = min(end, clip.duration)
        
        if start >= end or (end - start) < 0.5:
            ErrorHandler.log_warning(f"无效的剪辑范围: {start:.1f}s - {end:.1f}s")
            return None
        
        try:
            if has_audio:
                return self._clip_with_audio(clip, start, end)
            else:
                return clip.subclipped(start, end)
                
        except Exception as e:
            ErrorHandler.handle_api_error("视频剪辑", e)
            # 降级到无音频剪辑
            try:
                return clip.without_audio().subclipped(start, end)
            except Exception as fallback_error:
                ErrorHandler.handle_api_error("降级剪辑", fallback_error)
                return None
    
    def _clip_with_audio(self, clip: VideoFileClip, start: float, end: float) -> VideoFileClip:
        """带音频剪辑"""
        try:
            clipped = clip.subclipped(start, end)
            
            # 验证音频剪辑是否成功
            if clipped.audio is not None:
                try:
                    _ = clipped.audio.duration
                    return clipped
                except Exception:
                    ErrorHandler.log_warning("音频剪辑后不可用，移除音频")
                    return clipped.without_audio()
            
            return clipped
            
        except Exception as e:
            ErrorHandler.log_warning(f"含音频剪辑失败，使用无音频版本: {e}")
            return clip.without_audio().subclipped(start, end)
    
    def standardize_clips(self, clips: List[VideoFileClip]) -> List[VideoFileClip]:
        """
        标准化多个视频片段的格式
        
        Args:
            clips: 视频片段列表
            
        Returns:
            标准化后的视频片段列表
        """
        if len(clips) <= 1:
            return clips
        
        # 获取目标格式
        target_format = self._calculate_target_format(clips)
        
        # 标准化所有片段
        standardized_clips = []
        for i, clip in enumerate(clips):
            try:
                standardized_clip = self._standardize_single_clip(clip, target_format, i)
                standardized_clips.append(standardized_clip)
            except Exception as e:
                ErrorHandler.log_warning(f"视频{i+1}标准化失败，使用原视频: {e}")
                standardized_clips.append(clip)
        
        return standardized_clips
    
    def _calculate_target_format(self, clips: List[VideoFileClip]) -> Dict[str, Any]:
        """计算目标格式"""
        # 使用最小公约数确保兼容性
        target_w = min(clip.w for clip in clips)
        target_h = min(clip.h for clip in clips)
        target_fps = config.video_config['default_fps']
        
        # 确保分辨率是偶数（视频编码要求）
        target_w = target_w - (target_w % 2)
        target_h = target_h - (target_h % 2)
        
        return {
            'width': target_w,
            'height': target_h,
            'fps': target_fps
        }
    
    def _standardize_single_clip(self, clip: VideoFileClip, target_format: Dict[str, Any], index: int) -> VideoFileClip:
        """标准化单个视频片段"""
        target_w = target_format['width']
        target_h = target_format['height']
        target_fps = target_format['fps']
        
        needs_resize = clip.w != target_w or clip.h != target_h
        needs_fps_change = clip.fps != target_fps
        
        if needs_resize or needs_fps_change:
            print(f"    🔄 标准化视频{index+1}: {clip.w}x{clip.h}@{clip.fps}fps -> {target_w}x{target_h}@{target_fps}fps")
            
            standardized_clip = clip
            if needs_resize:
                standardized_clip = standardized_clip.resized((target_w, target_h))
            if needs_fps_change:
                standardized_clip = standardized_clip.with_fps(target_fps)
            
            return standardized_clip
        else:
            print(f"    ✅ 视频{index+1}格式已符合要求")
            return clip
    
    def safe_concatenate(self, clips: List[VideoFileClip]) -> Optional[VideoFileClip]:
        """
        安全合并视频片段
        
        Args:
            clips: 视频片段列表
            
        Returns:
            合并后的视频
        """
        if not clips:
            return None
        
        if len(clips) == 1:
            return clips[0]
        
        try:
            # 标准化格式
            standardized_clips = self.standardize_clips(clips)
            
            # 使用chain方法合并，避免格式冲突
            print(f"    🔗 合并{len(standardized_clips)}个视频片段...")
            final_clip = concatenate_videoclips(standardized_clips, method="chain")
            
            ErrorHandler.log_success(f"视频合并成功: {final_clip.duration:.1f}秒")
            return final_clip
            
        except Exception as e:
            ErrorHandler.handle_api_error("视频合并", e)
            return None
    
    def safe_write_video(self, clip: VideoFileClip, output_path: str) -> bool:
        """
        安全输出视频文件
        
        Args:
            clip: 视频对象
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        try:
            # 确保基本属性
            if not hasattr(clip, 'fps') or clip.fps is None:
                clip.fps = config.video_config['default_fps']
            
            # 构建输出参数
            write_params = self._build_write_params(clip)
            
            # 执行输出
            clip.write_videofile(output_path, **write_params)
            
            # 验证输出
            if os.path.exists(output_path):
                file_size = round(os.path.getsize(output_path) / (1024 * 1024), 2)
                ErrorHandler.log_success(f"视频输出成功: {output_path} ({file_size}MB)")
                return True
            else:
                raise Exception("输出文件未成功生成")
                
        except Exception as e:
            ErrorHandler.handle_file_error("视频输出", output_path, e)
            return False
    
    def _build_write_params(self, clip: VideoFileClip) -> Dict[str, Any]:
        """构建输出参数"""
        write_params = {
            "fps": clip.fps,
            "codec": self.output_config['video_codec'],
            "preset": self.output_config['preset'],
            "threads": self.output_config['threads'],
            "logger": None,
            "temp_audiofile": 'temp-audio.m4a',
            "remove_temp": True
        }
        
        # 处理音频
        if clip.audio is not None:
            try:
                # 验证音频可用性
                _ = clip.audio.duration
                write_params["audio_codec"] = self.output_config['audio_codec']
                write_params["audio_bitrate"] = self.output_config['audio_bitrate']
                print("  🎵 音频输出已启用")
            except Exception:
                ErrorHandler.log_warning("音频输出失败，改为无音频输出")
                clip = clip.without_audio()
        
        return write_params


class VideoValidator:
    """视频验证器"""
    
    @staticmethod
    def validate_video_file(video_path: str) -> bool:
        """验证视频文件是否有效"""
        if not os.path.exists(video_path):
            return False
        
        video_extensions = config.get_video_extensions()
        return video_path.lower().endswith(video_extensions)
    
    @staticmethod
    def validate_time_range(start: float, end: float, duration: float) -> bool:
        """验证时间范围是否有效"""
        return (0 <= start < end <= duration and (end - start) >= 0.5)


# 创建全局实例
video_processor = VideoProcessor()
video_validator = VideoValidator()
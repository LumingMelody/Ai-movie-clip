"""
简单的转场效果实现
不改变片段的时长，只在指定时间段应用效果
"""

from moviepy import VideoClip
from moviepy.video.fx import Resize, FadeIn, FadeOut
import numpy as np


def apply_zoom_in_transition(clip, duration=1.0, direction="out"):
    """
    应用放大转场效果，保持片段完整时长
    
    Args:
        clip: 视频片段
        duration: 转场持续时间
        direction: "in"(片段开头) 或 "out"(片段结尾)
    """
    original_duration = clip.duration
    
    def make_frame(t):
        # 获取原始帧
        frame = clip.get_frame(t)
        
        # 计算效果强度
        if direction == "out":
            # 在片段结尾应用效果
            if t >= original_duration - duration:
                # 计算放大比例
                progress = (t - (original_duration - duration)) / duration
                scale = 1.0 + progress * 0.3  # 最多放大30%
                
                # 应用缩放
                h, w = frame.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                
                # 使用OpenCV缩放
                import cv2
                scaled = cv2.resize(frame, (new_w, new_h))
                
                # 居中裁剪
                start_y = (new_h - h) // 2
                start_x = (new_w - w) // 2
                frame = scaled[start_y:start_y+h, start_x:start_x+w]
        
        elif direction == "in":
            # 在片段开头应用效果
            if t <= duration:
                # 从放大状态恢复到正常
                progress = t / duration
                scale = 1.3 - progress * 0.3  # 从1.3倍缩小到1.0
                
                # 应用缩放
                h, w = frame.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                
                import cv2
                scaled = cv2.resize(frame, (new_w, new_h))
                
                # 居中裁剪
                start_y = (new_h - h) // 2
                start_x = (new_w - w) // 2
                frame = scaled[start_y:start_y+h, start_x:start_x+w]
        
        return frame
    
    # 创建新的视频片段，保持原始时长
    result = VideoClip(make_frame, duration=original_duration)
    result.fps = clip.fps
    result.audio = clip.audio
    
    # 保留原始片段的start属性
    if hasattr(clip, 'start'):
        result.start = clip.start
    
    return result


def apply_zoom_out_transition(clip, duration=1.0, direction="in"):
    """
    应用缩小转场效果，保持片段完整时长
    """
    original_duration = clip.duration
    
    def make_frame(t):
        frame = clip.get_frame(t)
        
        if direction == "in":
            # 在片段开头应用效果
            if t <= duration:
                # 从小到大
                progress = t / duration
                scale = 0.7 + progress * 0.3  # 从0.7倍放大到1.0
                
                # 应用缩放
                h, w = frame.shape[:2]
                new_h, new_w = int(h * scale), int(w * scale)
                
                import cv2
                scaled = cv2.resize(frame, (new_w, new_h))
                
                # 添加黑边以保持尺寸
                result = np.zeros_like(frame)
                start_y = (h - new_h) // 2
                start_x = (w - new_w) // 2
                result[start_y:start_y+new_h, start_x:start_x+new_w] = scaled
                frame = result
        
        return frame
    
    result = VideoClip(make_frame, duration=original_duration)
    result.fps = clip.fps
    result.audio = clip.audio
    
    # 保留原始片段的start属性
    if hasattr(clip, 'start'):
        result.start = clip.start
    
    return result


def apply_pan_transition(clip, duration=1.0, direction="left", transition_dir="in"):
    """
    应用平移转场效果，保持片段完整时长
    """
    original_duration = clip.duration
    
    def make_frame(t):
        frame = clip.get_frame(t)
        h, w = frame.shape[:2]
        
        if transition_dir == "in" and t <= duration:
            # 片段开头的转场
            progress = t / duration
            if direction == "left":
                # 从右向左滑入
                offset = int(w * (1 - progress))
                result = np.zeros_like(frame)
                result[:, :w-offset] = frame[:, offset:]
                frame = result
                
        elif transition_dir == "out" and t >= original_duration - duration:
            # 片段结尾的转场
            progress = (t - (original_duration - duration)) / duration
            if direction == "right":
                # 向右滑出
                offset = int(w * progress)
                result = np.zeros_like(frame)
                if offset < w:
                    result[:, offset:] = frame[:, :w-offset]
                frame = result
        
        return frame
    
    result = VideoClip(make_frame, duration=original_duration)
    result.fps = clip.fps
    result.audio = clip.audio
    
    # 保留原始片段的start属性
    if hasattr(clip, 'start'):
        result.start = clip.start
    
    return result
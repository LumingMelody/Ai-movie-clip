"""
场景分割器 - 根据AuraRender设计方案实现
将视频智能分割成多个场景片段，用于应用转场效果
"""
from typing import List, Dict, Tuple
import logging

class SceneSplitter:
    """智能场景分割器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def split_by_duration(self, total_duration: float, 
                          target_segments: int = 3) -> List[Dict]:
        """
        按时长均匀分割场景
        
        Args:
            total_duration: 总时长
            target_segments: 目标片段数
            
        Returns:
            场景片段列表
        """
        segment_duration = total_duration / target_segments
        segments = []
        
        for i in range(target_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, total_duration)
            
            segment = {
                "index": i,
                "start": start_time,
                "end": end_time,
                "duration": end_time - start_time,
                "type": self._get_segment_type(i, target_segments),
                "needs_transition_in": i > 0,
                "needs_transition_out": i < target_segments - 1
            }
            segments.append(segment)
            
        return segments
    
    def _get_segment_type(self, index: int, total: int) -> str:
        """获取片段类型"""
        if index == 0:
            return "intro"
        elif index == total - 1:
            return "outro"
        else:
            return "main_content"
    
    def add_transitions(self, segments: List[Dict], 
                       transition_duration: float = 1.0) -> List[Dict]:
        """
        在片段之间添加转场
        
        Args:
            segments: 场景片段列表
            transition_duration: 转场时长
            
        Returns:
            包含转场信息的片段列表
        """
        enhanced_segments = []
        
        for i, segment in enumerate(segments):
            enhanced_segment = segment.copy()
            
            # 添加转场信息
            if segment.get("needs_transition_out"):
                enhanced_segment["transition_out"] = {
                    "type": self._select_transition(segment["type"], "out"),
                    "duration": transition_duration,
                    "start_time": segment["end"] - transition_duration
                }
            
            if segment.get("needs_transition_in"):
                enhanced_segment["transition_in"] = {
                    "type": self._select_transition(segment["type"], "in"),
                    "duration": transition_duration,
                    "start_time": segment["start"]
                }
            
            enhanced_segments.append(enhanced_segment)
            
        return enhanced_segments
    
    def _select_transition(self, segment_type: str, direction: str) -> str:
        """
        随机选择转场效果
        
        支持多种转场效果，每次随机选择
        """
        import random
        
        # 🔥 所有可用的转场效果列表（随机选择）
        all_transitions = [
            "fade_in",        # 渐显
            "fade_out",       # 渐隐
            "zoom_in",        # 放大
            "zoom_out",       # 缩小
            "slide_in_left",  # 向左滑入
            "slide_in_right", # 向右滑入
            "leaf_flip",      # 叶片翻转
            "glitch",         # 故障转换
            "shake",          # 震动
            "pan_left",       # 向左平移
            "pan_right",      # 向右平移
        ]
        
        # 根据方向过滤合适的转场
        if direction == "in":
            # 进入转场：fade_in, zoom_in, slide_in等
            suitable_transitions = [t for t in all_transitions if "in" in t or t in ["shake", "glitch", "leaf_flip"]]
        elif direction == "out":
            # 退出转场：fade_out, zoom_out, slide等
            suitable_transitions = [t for t in all_transitions if "out" in t or t in ["shake", "glitch", "leaf_flip"]]
        else:
            # 默认使用所有转场
            suitable_transitions = all_transitions
        
        # 随机选择一个转场
        result = random.choice(suitable_transitions)
        
        return result
    
    def generate_timeline_clips(self, segments: List[Dict], 
                               video_source: str,
                               original_clip_attrs: Dict = None) -> List[Dict]:
        """
        生成时间轴片段配置
        
        Args:
            segments: 场景片段列表
            video_source: 视频源
            original_clip_attrs: 原始片段的属性（如artistic_style, filters等）
        
        Returns:
            符合AuraRender时间轴格式的片段列表
        """
        clips = []
        
        # 提取原始属性
        if original_clip_attrs is None:
            original_clip_attrs = {}
        
        for i, segment in enumerate(segments):
            # 🔥 重要修复：为了避免重复，让每个片段从不同的位置开始
            segment_duration = segment["end"] - segment["start"]
            
            # 计算源视频的起始位置，让每个片段显示不同内容
            # 如果是3个10秒的片段，分别从0、10、20秒开始
            clip_in_time = i * segment_duration
            
            clip = {
                "start": segment["start"],
                "end": segment["end"],
                "clipIn": clip_in_time,  # 🔥 每个片段从不同位置开始
                "clipOut": clip_in_time + segment_duration,  # 🔥 播放对应时长
                "source": video_source,
                "filters": original_clip_attrs.get("filters", []),
                "transform": original_clip_attrs.get("transform", {
                    "scale": 1.0,
                    "position": "center"
                })
            }
            
            # 保留原始的艺术风格
            if "artistic_style" in original_clip_attrs:
                clip["artistic_style"] = original_clip_attrs["artistic_style"]
            
            # 保留其他自定义属性
            for key in ["color_grading", "audio_style", "text_style"]:
                if key in original_clip_attrs:
                    clip[key] = original_clip_attrs[key]
            
            # 添加转场滤镜
            if "transition_in" in segment:
                clip["transition_in"] = segment["transition_in"]
            if "transition_out" in segment:
                clip["transition_out"] = segment["transition_out"]
                
            clips.append(clip)
            
        return clips
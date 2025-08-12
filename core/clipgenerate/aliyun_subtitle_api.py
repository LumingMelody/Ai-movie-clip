#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阿里云智能媒体服务字幕API集成
支持九宫格位置设置和自定义字幕效果
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict


@dataclass
class SubtitleConfig:
    """字幕配置类"""
    content: str
    timeline_in: float = 0.0
    timeline_out: float = 10.0
    grid_position: int = 8  # 九宫格位置 (1-9)
    font_size: int = 48
    font_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    outline_width: int = 2
    font_face: str = "Normal"  # Normal, Bold, Italic, Underline
    alignment: str = "BottomCenter"
    custom_x: Optional[float] = None  # 自定义X坐标 (0-1)
    custom_y: Optional[float] = None  # 自定义Y坐标 (0-1)


class AliyunSubtitleAPI:
    """阿里云字幕API封装类"""
    
    def __init__(self, access_key_id: str = None, access_key_secret: str = None):
        """
        初始化阿里云字幕API
        
        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.logger = logging.getLogger(__name__)
        
        # 九宫格位置映射到阿里云坐标系统
        self.grid_position_map = {
            1: {"x": 0.1, "y": 0.1, "alignment": "TopLeft"},      # 左上
            2: {"x": 0.5, "y": 0.1, "alignment": "TopCenter"},    # 中上
            3: {"x": 0.9, "y": 0.1, "alignment": "TopRight"},     # 右上
            4: {"x": 0.1, "y": 0.5, "alignment": "MiddleLeft"},   # 左中
            5: {"x": 0.5, "y": 0.5, "alignment": "MiddleCenter"}, # 中心
            6: {"x": 0.9, "y": 0.5, "alignment": "MiddleRight"},  # 右中
            7: {"x": 0.1, "y": 0.9, "alignment": "BottomLeft"},   # 左下
            8: {"x": 0.5, "y": 0.9, "alignment": "BottomCenter"}, # 中下（默认）
            9: {"x": 0.9, "y": 0.9, "alignment": "BottomRight"},  # 右下
        }
    
    def grid_to_aliyun_position(self, grid_position: int) -> Dict[str, Union[float, str]]:
        """
        将九宫格位置转换为阿里云字幕API的位置参数
        
        Args:
            grid_position: 九宫格位置 (1-9)
            
        Returns:
            包含x, y, alignment的字典
        """
        return self.grid_position_map.get(grid_position, self.grid_position_map[8])
    
    def create_subtitle_timeline(self, 
                                subtitles: List[SubtitleConfig], 
                                video_width: int = 1920, 
                                video_height: int = 1080) -> Dict:
        """
        创建阿里云字幕时间轴配置
        
        Args:
            subtitles: 字幕配置列表
            video_width: 视频宽度
            video_height: 视频高度
            
        Returns:
            阿里云时间轴JSON配置
        """
        timeline = {
            "VideoTracks": [
                {
                    "VideoTrackClips": []
                }
            ],
            "AudioTracks": [],
            "SubtitleTracks": [
                {
                    "SubtitleTrackClips": []
                }
            ]
        }
        
        for subtitle in subtitles:
            # 获取位置信息
            if subtitle.custom_x is not None and subtitle.custom_y is not None:
                # 使用自定义位置
                position = {
                    "x": subtitle.custom_x,
                    "y": subtitle.custom_y,
                    "alignment": subtitle.alignment
                }
            else:
                # 使用九宫格位置
                position = self.grid_to_aliyun_position(subtitle.grid_position)
            
            # 创建字幕片段
            subtitle_clip = {
                "Type": "Text",
                "TimelineIn": subtitle.timeline_in,
                "TimelineOut": subtitle.timeline_out,
                "X": position["x"],
                "Y": position["y"],
                "Width": 0.8,  # 相对宽度
                "Height": 0.1,  # 相对高度
                "Content": subtitle.content,
                "Alignment": position["alignment"],
                "FontSize": subtitle.font_size,
                "FontColor": subtitle.font_color,
                "FontFace": subtitle.font_face,
                "OutlineColor": subtitle.outline_color,
                "OutlineWidth": subtitle.outline_width,
                "AdaptiveThreshold": 0.8,
                "ZOrder": 10
            }
            
            timeline["SubtitleTracks"][0]["SubtitleTrackClips"].append(subtitle_clip)
        
        return timeline
    
    def split_text_for_subtitles(self, 
                                text: str, 
                                video_duration: float,
                                max_chars_per_subtitle: int = 20,
                                min_display_time: float = 2.0) -> List[SubtitleConfig]:
        """
        将长文本分割为适合的字幕片段
        
        Args:
            text: 原始文本
            video_duration: 视频总时长
            max_chars_per_subtitle: 每个字幕的最大字符数
            min_display_time: 最小显示时间
            
        Returns:
            字幕配置列表
        """
        # 按标点符号分句
        import re
        sentences = re.split(r'[。！？!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 创建字幕片段
        subtitles = []
        current_time = 0.0
        
        for sentence in sentences:
            if not sentence:
                continue
                
            # 如果句子太长，进一步分割
            if len(sentence) > max_chars_per_subtitle:
                # 按逗号分割
                parts = re.split(r'[，,；;]', sentence)
                for part in parts:
                    if len(part) > max_chars_per_subtitle:
                        # 按字符数强制分割
                        chunks = [part[i:i+max_chars_per_subtitle] 
                                for i in range(0, len(part), max_chars_per_subtitle)]
                        for chunk in chunks:
                            if chunk.strip():
                                display_time = max(min_display_time, len(chunk) * 0.2)
                                if current_time + display_time <= video_duration:
                                    subtitles.append(SubtitleConfig(
                                        content=chunk.strip(),
                                        timeline_in=current_time,
                                        timeline_out=min(current_time + display_time, video_duration)
                                    ))
                                    current_time += display_time
                    else:
                        if part.strip():
                            display_time = max(min_display_time, len(part) * 0.2)
                            if current_time + display_time <= video_duration:
                                subtitles.append(SubtitleConfig(
                                    content=part.strip(),
                                    timeline_in=current_time,
                                    timeline_out=min(current_time + display_time, video_duration)
                                ))
                                current_time += display_time
            else:
                display_time = max(min_display_time, len(sentence) * 0.2)
                if current_time + display_time <= video_duration:
                    subtitles.append(SubtitleConfig(
                        content=sentence,
                        timeline_in=current_time,
                        timeline_out=min(current_time + display_time, video_duration)
                    ))
                    current_time += display_time
        
        # 如果还有剩余时间，延长最后一个字幕
        if subtitles and current_time < video_duration:
            subtitles[-1].timeline_out = video_duration
        
        return subtitles
    
    def create_production_timeline(self, 
                                  video_url: str,
                                  subtitles: List[SubtitleConfig],
                                  output_config: Optional[Dict] = None) -> Dict:
        """
        创建完整的制作时间轴，包含视频和字幕
        
        Args:
            video_url: 视频URL
            subtitles: 字幕配置列表
            output_config: 输出配置
            
        Returns:
            完整的制作时间轴配置
        """
        if output_config is None:
            output_config = {
                "Width": 1920,
                "Height": 1080,
                "VideoCodec": "H.264",
                "AudioCodec": "AAC"
            }
        
        # 创建基础时间轴
        timeline = self.create_subtitle_timeline(subtitles)
        
        # 添加视频轨道
        timeline["VideoTracks"][0]["VideoTrackClips"].append({
            "Type": "Video",
            "MediaURL": video_url,
            "TimelineIn": 0,
            "TimelineOut": max([s.timeline_out for s in subtitles]) if subtitles else 10,
            "X": 0,
            "Y": 0,
            "Width": 1.0,
            "Height": 1.0
        })
        
        # 添加输出配置
        timeline["OutputConfig"] = output_config
        
        return timeline
    
    def submit_production_job(self, 
                             timeline: Dict,
                             output_bucket: str,
                             output_object: str) -> str:
        """
        提交制作任务到阿里云
        
        Args:
            timeline: 时间轴配置
            output_bucket: 输出OSS桶
            output_object: 输出对象名
            
        Returns:
            任务ID
        """
        # 这里需要实际的阿里云API调用
        # 由于需要具体的SDK配置，这里提供一个示例框架
        
        self.logger.info("提交字幕制作任务到阿里云...")
        self.logger.info(f"Timeline: {json.dumps(timeline, ensure_ascii=False, indent=2)}")
        
        # 示例返回
        return f"job_{hash(json.dumps(timeline)) % 1000000}"
    
    def get_supported_fonts(self) -> List[str]:
        """
        获取支持的字体列表
        
        Returns:
            字体名称列表
        """
        return [
            "Normal",
            "Bold", 
            "Italic",
            "Underline",
            "BoldItalic",
            "BoldUnderline",
            "ItalicUnderline",
            "BoldItalicUnderline"
        ]
    
    def validate_subtitle_config(self, subtitle: SubtitleConfig) -> List[str]:
        """
        验证字幕配置
        
        Args:
            subtitle: 字幕配置
            
        Returns:
            错误信息列表
        """
        errors = []
        
        if not subtitle.content:
            errors.append("字幕内容不能为空")
        
        if subtitle.grid_position not in range(1, 10):
            errors.append("九宫格位置必须在1-9之间")
        
        if subtitle.timeline_in < 0:
            errors.append("开始时间不能为负数")
        
        if subtitle.timeline_out <= subtitle.timeline_in:
            errors.append("结束时间必须大于开始时间")
        
        if subtitle.font_size <= 0:
            errors.append("字体大小必须大于0")
        
        if subtitle.font_face not in self.get_supported_fonts():
            errors.append(f"不支持的字体样式: {subtitle.font_face}")
        
        return errors


def create_grid_subtitle_example():
    """创建九宫格字幕示例"""
    
    api = AliyunSubtitleAPI()
    
    # 创建9个不同位置的字幕示例
    subtitles = []
    positions = [
        "左上角", "顶部中间", "右上角",
        "左侧中间", "正中心", "右侧中间", 
        "左下角", "底部中间", "右下角"
    ]
    
    for i, position_name in enumerate(positions, 1):
        subtitle = SubtitleConfig(
            content=f"位置{i}: {position_name}",
            timeline_in=i * 2.0,
            timeline_out=(i + 1) * 2.0,
            grid_position=i,
            font_size=48,
            font_color="#FFFFFF",
            outline_color="#000000"
        )
        subtitles.append(subtitle)
    
    # 创建时间轴
    timeline = api.create_subtitle_timeline(subtitles)
    
    print("九宫格字幕示例配置:")
    print(json.dumps(timeline, ensure_ascii=False, indent=2))
    
    return timeline


if __name__ == "__main__":
    # 测试九宫格字幕功能
    create_grid_subtitle_example()
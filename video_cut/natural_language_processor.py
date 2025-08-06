"""
自然语言视频时间轴处理器

该模块提供将自然语言描述转换为视频编辑时间轴JSON结构的功能。
支持中文描述的时间、特效、节奏和颜色主题识别。
"""
import json
import re
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import jieba
import logging
from pathlib import Path

# 添加验证器
try:
    from .utils.validators import InputValidator, ErrorHandler
except ImportError:
    # 如果validators还未创建，使用临时占位
    class InputValidator:
        @staticmethod
        def validate_natural_language(text): return text
        @staticmethod
        def validate_duration(d): return float(d)
    class ErrorHandler:
        @staticmethod
        def handle_api_error(e, f=None): return {"error": str(e)}

# 类型别名，提高代码可读性
TimelineDict = Dict[str, Any]
PatternConverter = Union[callable, Tuple[callable, ...]]
DurationPattern = Tuple[str, PatternConverter]
RhythmConfig = Dict[str, Union[int, float, List[str]]]


class VideoEffectType(Enum):
    """视频特效类型枚举
    
    每个枚举值包含该特效的中英文关键词列表
    """
    FADE_IN = ["淡入", "渐入", "fade in"]
    FADE_OUT = ["淡出", "渐出", "fade out"] 
    TRANSITION = ["转场", "过渡", "切换"]
    SUBTITLE = ["字幕", "文字", "标题", "subtitle"]
    BACKGROUND_MUSIC = ["背景音乐", "音乐", "配乐", "bgm"]
    BLUR = ["模糊", "虚化", "blur"]
    ZOOM = ["放大", "缩放", "zoom"]
    ROTATE = ["旋转", "rotate"]
    GLOW = ["发光", "光晕", "glow"]


@dataclass
class VideoTimeSegment:
    """视频时间段数据类
    
    表示视频中的一个时间段，包含时间范围、内容描述和应用的特效
    """
    start_time: float
    end_time: float
    description: str
    effect_list: List[str]
    
    @property
    def duration(self) -> float:
        """获取时间段持续时长"""
        return self.end_time - self.start_time


class VideoTimelineProcessor:
    """自然语言视频时间轴处理器
    
    将用户的自然语言描述解析为结构化的视频编辑时间轴配置。
    支持时间表达式、特效关键词、节奏描述和颜色主题的智能识别。
    """
    
    # 常量定义
    DEFAULT_VIDEO_DURATION = 60.0
    DEFAULT_FPS = 30
    DEFAULT_RESOLUTION = {"width": 1920, "height": 1080}
    DEFAULT_SEGMENT_DURATION = 10.0
    
    def __init__(self):
        """初始化时间轴处理器"""
        self._setup_jieba_tokenizer()
        self._initialize_patterns()
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志器"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
    def _setup_jieba_tokenizer(self) -> None:
        """设置中文分词器"""
        video_editing_terms = [
            "转场", "淡入", "淡出", "字幕", "背景音乐",
            "片头", "片尾", "特效", "滤镜", "动画",
            "税务", "纳税", "依法纳税", "主要税种"
        ]
        
        for term in video_editing_terms:
            jieba.add_word(term, freq=10000)
    
    def _initialize_patterns(self) -> None:
        """初始化各种识别模式"""
        self._duration_patterns: List[DurationPattern] = [
            (r'(\d+)秒', lambda x: float(x)),
            (r'(\d+)s', lambda x: float(x)),
            (r'(\d+)分钟', lambda x: float(x) * 60),
            (r'(\d+)分(\d+)秒', lambda x, y: float(x) * 60 + float(y)),
            (r'(\d+)min', lambda x: float(x) * 60),
            (r'(\d+):(\d+)', lambda x, y: float(x) * 60 + float(y))
        ]
        
        self._time_range_patterns: List[Tuple[str, callable]] = [
            (r'(\d+)-(\d+)秒', lambda x, y: (float(x), float(y))),
            (r'(\d+)到(\d+)秒', lambda x, y: (float(x), float(y))),
            (r'前(\d+)秒', lambda x: (0, float(x))),
            (r'最后(\d+)秒', lambda x: (-float(x), None)),
            (r'第(\d+)秒开始', lambda x: (float(x), None))
        ]
        
        self._rhythm_configurations: Dict[str, RhythmConfig] = {
            "快节奏": {"cuts_per_minute": 12, "transition_duration": 0.3},
            "慢节奏": {"cuts_per_minute": 4, "transition_duration": 1.0},
            "动感": {"cuts_per_minute": 10, "effects": ["shake", "zoom"]},
            "平缓": {"cuts_per_minute": 3, "effects": ["fade"]},
            "紧张": {"cuts_per_minute": 15, "effects": ["glitch", "shake"]}
        }
        
        self._color_palette: Dict[str, str] = {
            "绿色": "#00FF00", "蓝色": "#0000FF", "红色": "#FF0000",
            "黄色": "#FFFF00", "紫色": "#800080", "橙色": "#FFA500",
            "黑白": "#000000", "金色": "#FFD700"
        }

    def generate_timeline_from_text(self, user_description: str) -> TimelineDict:
        """将自然语言描述转换为视频时间轴配置
        
        Args:
            user_description: 用户的自然语言视频描述
            
        Returns:
            包含完整时间轴配置的字典结构
            
        Example:
            >>> processor = VideoTimelineProcessor()
            >>> result = processor.generate_timeline_from_text("制作30秒视频，加转场和字幕")
            >>> result['timeline']['duration']
            30.0
        """
        try:
            # 验证输入
            user_description = InputValidator.validate_natural_language(user_description)
            self.logger.info(f"处理自然语言输入: {user_description[:50]}...")
            
            # 解析用户描述中的各种信息
            video_duration = self._parse_duration(user_description)
            time_segments = self._parse_time_segments(user_description)
            global_effects = self._parse_global_effects(user_description)
            rhythm_config = self._parse_rhythm_style(user_description)
            color_theme = self._parse_color_theme(user_description)
        except Exception as e:
            self.logger.error(f"解析自然语言失败: {e}")
            # 使用默认值继续
            video_duration = self.DEFAULT_VIDEO_DURATION
            time_segments = []
            global_effects = []
            rhythm_config = {}
            color_theme = None
        
        # 构建时间轴结构
        timeline_config = self._build_timeline_structure(
            title=self._extract_video_title(user_description),
            description=self._create_description_summary(user_description),
            duration=video_duration,
            color_theme=color_theme
        )
        
        # 生成视频轨道
        timeline_config["timeline"]["tracks"] = self._generate_video_tracks(
            time_segments, global_effects, video_duration, rhythm_config
        )
        
        return timeline_config
    
    def _build_timeline_structure(self, title: str, description: str, 
                                duration: float, color_theme: Optional[str]) -> TimelineDict:
        """构建基础时间轴结构"""
        return {
            "version": "1.0",
            "metadata": {
                "title": title,
                "description": description,
                "tags": self._extract_content_tags(title + " " + description),
                "generated_from": "natural_language_processing",
                "generator_version": "1.0"
            },
            "timeline": {
                "duration": duration,
                "fps": self.DEFAULT_FPS,
                "resolution": self.DEFAULT_RESOLUTION.copy(),
                "background_color": color_theme or "#000000",
                "tracks": []
            }
        }
    
    def _create_description_summary(self, text: str) -> str:
        """创建描述摘要"""
        max_length = 100
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + "..."

    def _parse_duration(self, text: str) -> float:
        """解析视频总时长
        
        从自然语言中识别时长表达式，如"30秒"、"2分钟"等
        """
        for pattern, converter in self._duration_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return converter(*matches[0])
                else:
                    return converter(matches[0])
        
        return self.DEFAULT_VIDEO_DURATION

    def _parse_time_segments(self, text: str) -> List[VideoTimeSegment]:
        """解析时间段信息
        
        将文本分解为多个时间段，每个段落包含时间范围和内容描述
        """
        segments = []
        sentences = re.split(r'[。；\n]', text)
        
        current_time = 0.0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 解析时间范围
            time_range = self._parse_time_range(sentence)
            
            if time_range:
                start_time, end_time = time_range
                if end_time is None:
                    end_time = start_time + self.DEFAULT_SEGMENT_DURATION
            else:
                # 自动分配时间段
                start_time = current_time
                end_time = current_time + self.DEFAULT_SEGMENT_DURATION
            
            # 识别该段的特效
            segment_effects = self._identify_segment_effects(sentence)
            
            segments.append(VideoTimeSegment(
                start_time=start_time,
                end_time=end_time,
                description=sentence,
                effect_list=segment_effects
            ))
            
            current_time = end_time
        
        return segments

    def _parse_time_range(self, text: str) -> Optional[Tuple[float, Optional[float]]]:
        """解析时间范围表达式
        
        识别如"0-5秒"、"前10秒"等时间范围描述
        """
        for pattern, converter in self._time_range_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    return converter(groups[0])
                else:
                    return converter(*groups)
        return None

    def _identify_segment_effects(self, text: str) -> List[str]:
        """识别片段中的特效关键词
        
        检测文本中提到的特效类型，返回特效名称列表
        """
        detected_effects = []
        
        for effect_type in VideoEffectType:
            for keyword in effect_type.value:
                if keyword in text:
                    detected_effects.append(effect_type.name.lower())
                    break
        
        return detected_effects

    def _parse_global_effects(self, text: str) -> List[str]:
        """解析全局特效
        
        识别应用于整个视频的特效类型
        """
        global_effects = []
        
        # 特效关键词映射
        effect_keyword_map = {
            "模糊": "blur", "发光": "glow", "粒子": "particle",
            "故障": "glitch", "震动": "shake", "缩放": "zoom", "旋转": "rotate"
        }
        
        for keyword, effect_name in effect_keyword_map.items():
            if keyword in text:
                global_effects.append(effect_name)
        
        return global_effects

    def _parse_rhythm_style(self, text: str) -> RhythmConfig:
        """解析节奏风格
        
        根据描述识别视频的节奏类型（快节奏、慢节奏等）
        """
        for rhythm_keyword, config in self._rhythm_configurations.items():
            if rhythm_keyword in text:
                return config
        
        # 返回默认节奏配置
        return {"cuts_per_minute": 6, "transition_duration": 0.5}

    def _parse_color_theme(self, text: str) -> Optional[str]:
        """解析颜色主题
        
        从描述中识别颜色相关的表达，返回对应的颜色代码
        """
        for color_name, color_code in self._color_palette.items():
            if color_name in text:
                return color_code
        return None

    def _extract_video_title(self, text: str) -> str:
        """提取视频标题
        
        从自然语言描述中提取合适的视频标题
        """
        # 从第一句中提取关键信息
        first_sentence = text.split('。')[0].split('，')[0]
        
        # 清理常见的动词前缀
        title = re.sub(r'制作一个|制作|创建|生成', '', first_sentence)
        title = re.sub(r'的视频|视频', '', title)
        
        cleaned_title = title.strip()
        return cleaned_title if cleaned_title else "AI生成视频"

    def _extract_content_tags(self, text: str) -> List[str]:
        """提取内容标签
        
        使用分词技术识别视频内容的关键标签
        """
        # 使用jieba进行中文分词
        word_segments = list(jieba.cut(text))
        
        # 重要关键词列表
        important_keywords = [
            "税务", "产品", "教育", "宣传", "科普", "教学", 
            "广告", "vlog", "介绍", "展示", "演示"
        ]
        
        detected_tags = []
        for word in word_segments:
            if word in important_keywords and word not in detected_tags:
                detected_tags.append(word)
        
        return detected_tags[:5]  # 返回最多5个标签

    def _generate_video_tracks(self, segments: List[VideoTimeSegment], 
                             global_effects: List[str], duration: float, 
                             rhythm_config: RhythmConfig) -> List[Dict]:
        """生成视频轨道
        
        根据解析的时间段和特效配置生成完整的视频轨道结构
        """
        all_tracks = []
        
        # 主视频轨道
        main_video_track = {
            "type": "video",
            "name": "主视频",
            "clips": []
        }
        
        # 为每个时间段生成视频片段
        for segment_index, segment in enumerate(segments):
            video_clip = {
                "start": segment.start_time,
                "end": segment.end_time,
                "clipIn": segment.start_time,
                "clipOut": segment.end_time,
                "filters": self._convert_effects_to_filters(segment.effect_list + global_effects),
                "transform": {"scale": 1.0, "position": [960, 540]}
            }
            
            # 添加转场效果
            if segment_index > 0 and "transition" in segment.effect_list:
                video_clip["transition_in"] = {
                    "type": "fade",
                    "duration": rhythm_config.get("transition_duration", 0.5)
                }
            
            main_video_track["clips"].append(video_clip)
        
        all_tracks.append(main_video_track)
        
        # 字幕轨道生成
        subtitle_clips = []
        for segment in segments:
            needs_subtitle = ("subtitle" in segment.effect_list or 
                            "字幕" in segment.description or
                            "background_music" in segment.effect_list)
            
            if needs_subtitle:
                subtitle_clips.append({
                    "start": segment.start_time,
                    "end": segment.end_time,
                    "clipIn": segment.start_time,
                    "clipOut": segment.end_time,
                    "filters": [],
                    "content": {
                        "text": self._extract_subtitle_text(segment.description),
                        "font": "思源黑体",
                        "size": 36,
                        "color": "#FFFFFF",
                        "position": "bottom",
                        "alignment": "center",
                        "outline": {"color": "#000000", "width": 2}
                    }
                })
        
        if subtitle_clips:
            all_tracks.append({
                "type": "text",
                "name": "字幕轨道",
                "clips": subtitle_clips
            })
        
        # 背景音乐轨道生成
        needs_background_music = any(
            "background_music" in segment.effect_list or "背景音乐" in segment.description 
            for segment in segments
        )
        
        all_descriptions = ' '.join(segment.description for segment in segments)
        if needs_background_music or "背景音乐" in all_descriptions:
            all_tracks.append({
                "type": "audio",
                "name": "背景音乐",
                "clips": [{
                    "start": 0,
                    "end": duration,
                    "clipIn": 0,
                    "clipOut": duration,
                    "filters": [],
                    "content": {
                        "source": "default_background_music.mp3",
                        "volume": 0.3,
                        "loop": True,
                        "fade_in": 2.0,
                        "fade_out": 2.0
                    }
                }]
            })
        
        return all_tracks

    def _convert_effects_to_filters(self, effect_names: List[str]) -> List[str]:
        """将特效名称转换为滤镜标识符
        
        将语义化的特效名称转换为系统可识别的滤镜ID格式
        """
        filter_identifiers = []
        
        # 特效到滤镜的映射表
        effect_to_filter_map = {
            "fade_in": "fade_001",
            "fade_out": "fade_002", 
            "blur": "blur_001",
            "glow": "glow_001",
            "zoom": "zoom_001",
            "rotate": "rotate_001",
            "transition": "transition_001"
        }
        
        for effect_name in effect_names:
            if effect_name in effect_to_filter_map:
                filter_identifiers.append(effect_to_filter_map[effect_name])
        
        return filter_identifiers

    def _extract_subtitle_text(self, content_description: str) -> str:
        """从内容描述中提取字幕文本
        
        智能提取适合作为字幕显示的文本内容
        """
        # 清理时间标记
        cleaned_text = re.sub(r'\d+-\d+秒|第\d+秒|前\d+秒', '', content_description)
        
        # 提取引号中的直接内容
        quoted_content = re.findall(r'["""](.*?)["""]', cleaned_text)
        if quoted_content:
            return quoted_content[0]
        
        # 提取冒号后的说明内容
        if '：' in cleaned_text:
            return cleaned_text.split('：', 1)[1].strip()
        
        # 返回清理后的文本
        return cleaned_text.strip()


def test_video_timeline_processor():
    """测试视频时间轴处理器"""
    processor = VideoTimelineProcessor()
    
    # 测试用例1：简单描述
    simple_description = "制作一个30秒的产品宣传视频，要有转场特效和字幕"
    result1 = processor.generate_timeline_from_text(simple_description)
    print("=== 测试1：简单描述 ===")
    print(f"时长: {result1['timeline']['duration']}秒")
    print(f"轨道数: {len(result1['timeline']['tracks'])}")
    
    # 测试用例2：详细描述
    detailed_description = """
    制作45秒的税务知识科普视频：
    0-5秒：显示标题"税务知识科普"，淡入效果
    5-20秒：介绍税务基础知识，配字幕
    20-35秒：说明纳税义务，使用绿色主题
    35-45秒：总结要点，淡出效果，背景音乐
    """
    result2 = processor.generate_timeline_from_text(detailed_description)
    print("\n=== 测试2：详细描述 ===")
    print(f"标题: {result2['metadata']['title']}")
    print(f"时长: {result2['timeline']['duration']}秒")
    print(f"背景色: {result2['timeline']['background_color']}")
    
    # 输出完整结果用于调试
    print("\n完整时间轴配置:")
    print(json.dumps(result2, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_video_timeline_processor()
"""
自然语言处理器
将自然语言描述转换为时间轴JSON结构
"""
import json
import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import jieba


class EffectKeyword(Enum):
    """特效关键词枚举"""
    FADE_IN = ["淡入", "渐入", "fade in"]
    FADE_OUT = ["淡出", "渐出", "fade out"]
    TRANSITION = ["转场", "过渡", "切换"]
    SUBTITLE = ["字幕", "文字", "标题", "subtitle"]
    BGM = ["背景音乐", "音乐", "配乐", "bgm"]
    BLUR = ["模糊", "虚化", "blur"]
    ZOOM = ["放大", "缩放", "zoom"]
    ROTATE = ["旋转", "rotate"]
    GLOW = ["发光", "光晕", "glow"]


@dataclass
class TimeSegment:
    """时间段"""
    start: float
    end: float
    content: str
    effects: List[str]


class NaturalLanguageProcessor:
    """自然语言处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 初始化分词器
        self._init_jieba()
        
        # 时长模式
        self.duration_patterns = [
            (r'(\d+)秒', lambda x: float(x)),
            (r'(\d+)s', lambda x: float(x)),
            (r'(\d+)分钟', lambda x: float(x) * 60),
            (r'(\d+)分(\d+)秒', lambda x, y: float(x) * 60 + float(y)),
            (r'(\d+)min', lambda x: float(x) * 60),
            (r'(\d+):(\d+)', lambda x, y: float(x) * 60 + float(y))
        ]
        
        # 时间段模式
        self.time_range_patterns = [
            (r'(\d+)-(\d+)秒', lambda x, y: (float(x), float(y))),
            (r'(\d+)到(\d+)秒', lambda x, y: (float(x), float(y))),
            (r'前(\d+)秒', lambda x: (0, float(x))),
            (r'最后(\d+)秒', lambda x: (-float(x), None)),
            (r'第(\d+)秒开始', lambda x: (float(x), None))
        ]
        
        # 节奏关键词
        self.rhythm_keywords = {
            "快节奏": {"cuts_per_minute": 12, "transition_duration": 0.3},
            "慢节奏": {"cuts_per_minute": 4, "transition_duration": 1.0},
            "动感": {"cuts_per_minute": 10, "effects": ["shake", "zoom"]},
            "平缓": {"cuts_per_minute": 3, "effects": ["fade"]},
            "紧张": {"cuts_per_minute": 15, "effects": ["glitch", "shake"]}
        }
        
        # 颜色主题
        self.color_themes = {
            "绿色": "#00FF00",
            "蓝色": "#0000FF",
            "红色": "#FF0000",
            "黄色": "#FFFF00",
            "紫色": "#800080",
            "橙色": "#FFA500",
            "黑白": "#000000",
            "金色": "#FFD700"
        }

    def _init_jieba(self):
        """初始化jieba分词器"""
        # 添加自定义词汇
        custom_words = [
            "转场", "淡入", "淡出", "字幕", "背景音乐",
            "片头", "片尾", "特效", "滤镜", "动画",
            "税务", "纳税", "依法纳税", "主要税种"
        ]
        for word in custom_words:
            jieba.add_word(word, freq=10000)

    def process_natural_language(self, text: str) -> Dict:
        """
        处理自然语言输入，生成时间轴
        
        Args:
            text: 自然语言描述
            
        Returns:
            时间轴JSON结构
        """
        # 提取关键信息
        duration = self._extract_duration(text)
        segments = self._extract_segments(text)
        effects = self._extract_effects(text)
        rhythm = self._extract_rhythm(text)
        color_theme = self._extract_color_theme(text)
        
        # 生成基础时间轴结构
        timeline = {
            "version": "1.0",
            "metadata": {
                "title": self._extract_title(text),
                "description": text[:100] + "..." if len(text) > 100 else text,
                "tags": self._extract_tags(text),
                "generated_from": "natural_language"
            },
            "timeline": {
                "duration": duration,
                "fps": 30,
                "resolution": {"width": 1920, "height": 1080},
                "background_color": color_theme or "#000000",
                "tracks": []
            }
        }
        
        # 生成轨道
        timeline["timeline"]["tracks"] = self._generate_tracks(
            segments, effects, duration, rhythm
        )
        
        return timeline

    def _extract_duration(self, text: str) -> float:
        """提取视频总时长"""
        for pattern, converter in self.duration_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return converter(*matches[0])
                else:
                    return converter(matches[0])
        
        # 默认时长
        return 60.0

    def _extract_segments(self, text: str) -> List[TimeSegment]:
        """提取时间段信息"""
        segments = []
        
        # 分句处理
        sentences = re.split(r'[。；\n]', text)
        
        current_time = 0
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 查找时间范围
            time_range = self._extract_time_range(sentence)
            
            if time_range:
                start, end = time_range
                if end is None:
                    end = start + 10  # 默认持续10秒
            else:
                # 自动分配时间
                start = current_time
                end = current_time + 10
            
            # 提取该段的效果
            segment_effects = self._extract_segment_effects(sentence)
            
            segments.append(TimeSegment(
                start=start,
                end=end,
                content=sentence.strip(),
                effects=segment_effects
            ))
            
            current_time = end
        
        return segments

    def _extract_time_range(self, text: str) -> Optional[Tuple[float, Optional[float]]]:
        """提取时间范围"""
        for pattern, converter in self.time_range_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    return converter(groups[0])
                else:
                    return converter(*groups)
        return None

    def _extract_segment_effects(self, text: str) -> List[str]:
        """提取片段特效"""
        effects = []
        
        for effect_type in EffectKeyword:
            for keyword in effect_type.value:
                if keyword in text:
                    effects.append(effect_type.name.lower())
                    break
        
        return effects

    def _extract_effects(self, text: str) -> List[str]:
        """提取全局特效"""
        effects = []
        
        # 检查特效关键词
        effect_keywords = {
            "模糊": "blur",
            "发光": "glow",
            "粒子": "particle",
            "故障": "glitch",
            "震动": "shake",
            "缩放": "zoom",
            "旋转": "rotate"
        }
        
        for keyword, effect in effect_keywords.items():
            if keyword in text:
                effects.append(effect)
        
        return effects

    def _extract_rhythm(self, text: str) -> Dict:
        """提取节奏信息"""
        for keyword, rhythm_config in self.rhythm_keywords.items():
            if keyword in text:
                return rhythm_config
        
        # 默认节奏
        return {"cuts_per_minute": 6, "transition_duration": 0.5}

    def _extract_color_theme(self, text: str) -> Optional[str]:
        """提取颜色主题"""
        for color_name, color_code in self.color_themes.items():
            if color_name in text:
                return color_code
        return None

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        # 尝试从第一句提取
        first_sentence = text.split('。')[0].split('，')[0]
        
        # 移除"制作"等词汇
        title = re.sub(r'制作一个|制作|创建|生成', '', first_sentence)
        title = re.sub(r'的视频|视频', '', title)
        
        return title.strip() or "未命名视频"

    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        # 使用jieba分词
        words = jieba.cut(text)
        
        # 提取名词作为标签
        tags = []
        important_words = ["税务", "产品", "教育", "宣传", "科普", "教学", "广告", "vlog"]
        
        for word in words:
            if word in important_words and word not in tags:
                tags.append(word)
        
        return tags[:5]  # 最多5个标签

    def _generate_tracks(self, segments: List[TimeSegment], global_effects: List[str],
                        duration: float, rhythm: Dict) -> List[Dict]:
        """生成轨道"""
        tracks = []
        
        # 视频轨道
        video_track = {
            "type": "video",
            "name": "主视频",
            "clips": []
        }
        
        # 为每个片段生成视频剪辑
        for i, segment in enumerate(segments):
            clip = {
                "start": segment.start,
                "end": segment.end,
                "clipIn": segment.start,
                "clipOut": segment.end,
                "filters": self._convert_effects_to_filters(segment.effects + global_effects),
                "transform": {"scale": 1.0, "position": [960, 540]}
            }
            
            # 添加转场
            if i > 0 and "transition" in segment.effects:
                clip["transition_in"] = {
                    "type": "fade",
                    "duration": rhythm.get("transition_duration", 0.5)
                }
            
            video_track["clips"].append(clip)
        
        tracks.append(video_track)
        
        # 字幕轨道
        subtitle_clips = []
        for segment in segments:
            if "subtitle" in segment.effects or "字幕" in segment.content:
                subtitle_clips.append({
                    "start": segment.start,
                    "end": segment.end,
                    "clipIn": segment.start,
                    "clipOut": segment.end,
                    "filters": [],
                    "content": {
                        "text": self._extract_subtitle_text(segment.content),
                        "font": "思源黑体",
                        "size": 36,
                        "color": "#FFFFFF",
                        "position": "bottom",
                        "alignment": "center",
                        "outline": {"color": "#000000", "width": 2}
                    }
                })
        
        if subtitle_clips:
            tracks.append({
                "type": "text",
                "name": "字幕",
                "clips": subtitle_clips
            })
        
        # 音频轨道
        has_bgm = any("bgm" in segment.effects or "背景音乐" in segment.content 
                      for segment in segments)
        
        if has_bgm or "背景音乐" in ' '.join(s.content for s in segments):
            tracks.append({
                "type": "audio",
                "name": "背景音乐",
                "clips": [{
                    "start": 0,
                    "end": duration,
                    "clipIn": 0,
                    "clipOut": duration,
                    "filters": [],
                    "content": {
                        "source": "bgm_default.mp3",
                        "volume": 0.3,
                        "loop": True,
                        "fade_in": 2,
                        "fade_out": 2
                    }
                }]
            })
        
        return tracks

    def _convert_effects_to_filters(self, effects: List[str]) -> List[str]:
        """将效果转换为滤镜格式"""
        filters = []
        
        effect_mapping = {
            "fade_in": "fade_001",
            "fade_out": "fade_002",
            "blur": "blur_001",
            "glow": "glow_001",
            "zoom": "zoom_001",
            "rotate": "rotate_001"
        }
        
        for effect in effects:
            if effect in effect_mapping:
                filters.append(effect_mapping[effect])
        
        return filters

    def _extract_subtitle_text(self, content: str) -> str:
        """提取字幕文本"""
        # 移除时间信息
        text = re.sub(r'\d+-\d+秒|第\d+秒|前\d+秒', '', content)
        
        # 提取引号中的内容
        quotes = re.findall(r'["""](.*?)["""]', text)
        if quotes:
            return quotes[0]
        
        # 提取冒号后的内容
        if '：' in text:
            return text.split('：', 1)[1].strip()
        
        return text.strip()


def test_natural_language_processor():
    """测试自然语言处理器"""
    processor = NaturalLanguageProcessor()
    
    # 测试用例1：简单描述
    test1 = "制作一个30秒的产品宣传视频，要有转场特效和字幕"
    result1 = processor.process_natural_language(test1)
    print("测试1结果：")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试用例2：详细描述
    test2 = """
    制作45秒的税务知识科普视频：
    0-5秒：显示标题"税务知识科普"，淡入效果
    5-20秒：介绍税务基础知识，配字幕
    20-35秒：说明纳税义务，使用绿色主题
    35-45秒：总结要点，淡出效果，背景音乐
    """
    result2 = processor.process_natural_language(test2)
    print("\n测试2结果：")
    print(json.dumps(result2, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_natural_language_processor()
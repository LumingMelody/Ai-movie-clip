"""
高级时间轴生成器
支持复杂的视频剪辑需求，包括多轨道、特效组合、智能时间分配等
"""
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math


class TrackType(Enum):
    """轨道类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    EFFECT = "effect"
    TRANSITION = "transition"


class EffectType(Enum):
    """特效类型枚举"""
    BLUR = "blur"
    GLOW = "glow"
    PARTICLE = "particle"
    ZOOM = "zoom"
    ROTATE = "rotate"
    SHAKE = "shake"
    GLITCH = "glitch"
    COLOR_CORRECT = "color_correct"
    VIGNETTE = "vignette"
    CHROMATIC = "chromatic_aberration"


class TransitionType(Enum):
    """转场类型枚举"""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    CROSS_FADE = "cross_fade"
    CUT = "cut"
    WIPE = "wipe"
    SLIDE = "slide"
    ZOOM = "zoom"
    ROTATE = "rotate"
    DISSOLVE = "dissolve"
    MORPH = "morph"


@dataclass
class TimelineClip:
    """时间轴片段"""
    start: float
    end: float
    clip_in: float
    clip_out: float
    filters: List[str] = field(default_factory=list)
    transform: Dict[str, Any] = field(default_factory=lambda: {"scale": 1.0, "position": [960, 540]})
    content: Optional[Dict[str, Any]] = None
    transition_in: Optional[str] = None
    transition_out: Optional[str] = None
    opacity: float = 1.0
    blend_mode: str = "normal"


@dataclass
class TimelineTrack:
    """时间轴轨道"""
    type: str
    name: str
    clips: List[TimelineClip] = field(default_factory=list)
    enabled: bool = True
    locked: bool = False
    opacity: float = 1.0


class TimelineGenerator:
    """高级时间轴生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.default_resolution = {"width": 1920, "height": 1080}
        self.default_fps = 30
        
        # 预设模板
        self.templates = {
            "vlog": self._create_vlog_template,
            "product": self._create_product_template,
            "education": self._create_education_template,
            "commercial": self._create_commercial_template,
            "social_media": self._create_social_media_template
        }

    def generate_advanced_timeline(self, config: Dict) -> Dict:
        """
        生成高级时间轴
        
        Args:
            config: 配置信息，包含片段、特效、音频等
            
        Returns:
            完整的时间轴JSON
        """
        # 基础结构
        timeline = {
            "version": "1.0",
            "metadata": {
                "created_at": self._get_timestamp(),
                "title": config.get("title", "Untitled"),
                "description": config.get("description", ""),
                "tags": config.get("tags", []),
                "template": config.get("template", "custom")
            },
            "timeline": {
                "duration": config.get("duration", 60),
                "fps": config.get("fps", self.default_fps),
                "resolution": config.get("resolution", self.default_resolution),
                "background_color": config.get("background_color", "#000000"),
                "tracks": []
            }
        }
        
        # 根据模板生成轨道
        if config.get("template") in self.templates:
            timeline["timeline"]["tracks"] = self.templates[config["template"]](config)
        else:
            # 自定义生成
            timeline["timeline"]["tracks"] = self._generate_custom_tracks(config)
        
        # 添加全局特效
        if config.get("global_effects"):
            timeline["timeline"]["global_effects"] = config["global_effects"]
        
        # 添加章节标记
        if config.get("chapters"):
            timeline["timeline"]["chapters"] = self._generate_chapters(config["chapters"])
        
        return timeline

    def _generate_custom_tracks(self, config: Dict) -> List[Dict]:
        """生成自定义轨道"""
        tracks = []
        
        # 视频轨道
        if config.get("video_segments"):
            tracks.extend(self._generate_video_tracks(config["video_segments"]))
        
        # 文字轨道
        if config.get("text_segments"):
            tracks.extend(self._generate_text_tracks(config["text_segments"]))
        
        # 音频轨道
        if config.get("audio_segments"):
            tracks.extend(self._generate_audio_tracks(config["audio_segments"]))
        
        # 特效轨道
        if config.get("effect_segments"):
            tracks.extend(self._generate_effect_tracks(config["effect_segments"]))
        
        return tracks

    def _generate_video_tracks(self, segments: List[Dict]) -> List[Dict]:
        """生成视频轨道"""
        tracks = []
        
        for i, segment in enumerate(segments):
            track = {
                "type": TrackType.VIDEO.value,
                "name": segment.get("name", f"视频轨道{i+1}"),
                "clips": []
            }
            
            # 处理每个片段
            for clip_data in segment.get("clips", []):
                clip = {
                    "start": clip_data.get("start", 0),
                    "end": clip_data.get("end", 10),
                    "clipIn": clip_data.get("clipIn", 0),
                    "clipOut": clip_data.get("clipOut", 10),
                    "filters": self._process_filters(clip_data.get("effects", [])),
                    "transform": self._process_transform(clip_data.get("transform", {})),
                    "opacity": clip_data.get("opacity", 1.0),
                    "blend_mode": clip_data.get("blend_mode", "normal")
                }
                
                # 添加转场
                if clip_data.get("transition_in"):
                    clip["transition_in"] = self._process_transition(clip_data["transition_in"])
                if clip_data.get("transition_out"):
                    clip["transition_out"] = self._process_transition(clip_data["transition_out"])
                
                track["clips"].append(clip)
            
            tracks.append(track)
        
        return tracks

    def _generate_text_tracks(self, segments: List[Dict]) -> List[Dict]:
        """生成文字轨道"""
        tracks = []
        
        for i, segment in enumerate(segments):
            track = {
                "type": TrackType.TEXT.value,
                "name": segment.get("name", f"字幕轨道{i+1}"),
                "clips": []
            }
            
            for text_data in segment.get("texts", []):
                clip = {
                    "start": text_data.get("start", 0),
                    "end": text_data.get("end", 5),
                    "clipIn": text_data.get("start", 0),
                    "clipOut": text_data.get("end", 5),
                    "filters": self._process_filters(text_data.get("effects", [])),
                    "content": {
                        "text": text_data.get("text", ""),
                        "font": text_data.get("font", "思源黑体"),
                        "size": text_data.get("size", 36),
                        "color": text_data.get("color", "#FFFFFF"),
                        "position": text_data.get("position", "bottom"),
                        "alignment": text_data.get("alignment", "center"),
                        "outline": text_data.get("outline", {"color": "#000000", "width": 2}),
                        "shadow": text_data.get("shadow", {"color": "#000000", "offset": [2, 2], "blur": 4}),
                        "animation": text_data.get("animation", "fade_in")
                    }
                }
                
                track["clips"].append(clip)
            
            tracks.append(track)
        
        return tracks

    def _generate_audio_tracks(self, segments: List[Dict]) -> List[Dict]:
        """生成音频轨道"""
        tracks = []
        
        for i, segment in enumerate(segments):
            track = {
                "type": TrackType.AUDIO.value,
                "name": segment.get("name", f"音频轨道{i+1}"),
                "clips": []
            }
            
            for audio_data in segment.get("audios", []):
                clip = {
                    "start": audio_data.get("start", 0),
                    "end": audio_data.get("end", 60),
                    "clipIn": audio_data.get("clipIn", 0),
                    "clipOut": audio_data.get("clipOut", 60),
                    "filters": self._process_audio_filters(audio_data.get("effects", [])),
                    "content": {
                        "source": audio_data.get("source", ""),
                        "volume": audio_data.get("volume", 1.0),
                        "loop": audio_data.get("loop", False),
                        "fade_in": audio_data.get("fade_in", 0),
                        "fade_out": audio_data.get("fade_out", 0),
                        "pitch": audio_data.get("pitch", 0),
                        "tempo": audio_data.get("tempo", 1.0)
                    }
                }
                
                track["clips"].append(clip)
            
            tracks.append(track)
        
        return tracks

    def _generate_effect_tracks(self, segments: List[Dict]) -> List[Dict]:
        """生成特效轨道"""
        tracks = []
        
        for i, segment in enumerate(segments):
            track = {
                "type": TrackType.EFFECT.value,
                "name": segment.get("name", f"特效轨道{i+1}"),
                "clips": []
            }
            
            for effect_data in segment.get("effects", []):
                clip = {
                    "start": effect_data.get("start", 0),
                    "end": effect_data.get("end", 5),
                    "effect_type": effect_data.get("type", "particle"),
                    "parameters": effect_data.get("parameters", {}),
                    "intensity": effect_data.get("intensity", 1.0),
                    "blend_mode": effect_data.get("blend_mode", "screen")
                }
                
                track["clips"].append(clip)
            
            tracks.append(track)
        
        return tracks

    def _process_filters(self, effects: List[Any]) -> List[str]:
        """处理滤镜效果"""
        filters = []
        
        for effect in effects:
            if isinstance(effect, str):
                # 简单效果名称
                filters.append(f"{effect}_001")
            elif isinstance(effect, dict):
                # 复杂效果配置
                effect_type = effect.get("type", "unknown")
                intensity = effect.get("intensity", 1)
                filters.append(f"{effect_type}_{int(intensity * 10):03d}")
        
        return filters

    def _process_transform(self, transform: Dict) -> Dict:
        """处理变换参数"""
        default_transform = {
            "scale": 1.0,
            "position": [960, 540],
            "rotation": 0,
            "anchor": [0.5, 0.5],
            "skew": [0, 0]
        }
        
        # 更新默认值
        default_transform.update(transform)
        
        return default_transform

    def _process_transition(self, transition: Any) -> Dict:
        """处理转场效果"""
        if isinstance(transition, str):
            return {
                "type": transition,
                "duration": 1.0,
                "easing": "ease-in-out"
            }
        elif isinstance(transition, dict):
            return {
                "type": transition.get("type", "fade"),
                "duration": transition.get("duration", 1.0),
                "easing": transition.get("easing", "ease-in-out"),
                "direction": transition.get("direction", "left"),
                "parameters": transition.get("parameters", {})
            }
        
        return {"type": "cut", "duration": 0}

    def _process_audio_filters(self, effects: List[Any]) -> List[Dict]:
        """处理音频滤镜"""
        filters = []
        
        for effect in effects:
            if isinstance(effect, str):
                filters.append({"type": effect, "params": {}})
            elif isinstance(effect, dict):
                filters.append({
                    "type": effect.get("type", "unknown"),
                    "params": effect.get("params", {})
                })
        
        return filters

    def _generate_chapters(self, chapters: List[Dict]) -> List[Dict]:
        """生成章节标记"""
        processed_chapters = []
        
        for chapter in chapters:
            processed_chapters.append({
                "time": chapter.get("time", 0),
                "title": chapter.get("title", ""),
                "description": chapter.get("description", ""),
                "thumbnail": chapter.get("thumbnail", "")
            })
        
        return processed_chapters

    def _create_vlog_template(self, config: Dict) -> List[Dict]:
        """创建Vlog模板"""
        duration = config.get("duration", 180)  # 3分钟
        
        tracks = []
        
        # 主视频轨道
        tracks.append({
            "type": "video",
            "name": "主视频",
            "clips": [
                {
                    "start": 0,
                    "end": duration,
                    "clipIn": 0,
                    "clipOut": duration,
                    "filters": ["color_correct_001"],
                    "transform": {"scale": 1.0, "position": [960, 540]}
                }
            ]
        })
        
        # B-Roll轨道
        tracks.append({
            "type": "video",
            "name": "B-Roll",
            "clips": self._generate_broll_clips(duration)
        })
        
        # 字幕轨道
        tracks.append({
            "type": "text",
            "name": "字幕",
            "clips": self._generate_subtitle_clips(config.get("subtitles", []))
        })
        
        # 背景音乐
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
                    "source": "vlog_bgm.mp3",
                    "volume": 0.3,
                    "loop": True
                }
            }]
        })
        
        return tracks

    def _create_product_template(self, config: Dict) -> List[Dict]:
        """创建产品介绍模板"""
        duration = config.get("duration", 60)
        
        tracks = []
        
        # 产品展示轨道
        tracks.append({
            "type": "video",
            "name": "产品展示",
            "clips": [
                {
                    "start": 0,
                    "end": 5,
                    "clipIn": 0,
                    "clipOut": 5,
                    "filters": ["glow_002"],
                    "transform": {"scale": 1.2, "position": [960, 540]},
                    "transition_in": {"type": "zoom", "duration": 1}
                },
                {
                    "start": 5,
                    "end": duration - 5,
                    "clipIn": 5,
                    "clipOut": duration - 5,
                    "filters": ["blur_001"],
                    "transform": {"scale": 1.0, "position": [960, 540]}
                },
                {
                    "start": duration - 5,
                    "end": duration,
                    "clipIn": duration - 5,
                    "clipOut": duration,
                    "filters": ["glow_003"],
                    "transform": {"scale": 1.0, "position": [960, 540]},
                    "transition_out": {"type": "fade", "duration": 1}
                }
            ]
        })
        
        # 特性说明文字
        tracks.append({
            "type": "text",
            "name": "产品特性",
            "clips": self._generate_feature_text_clips(config.get("features", []))
        })
        
        return tracks

    def _create_education_template(self, config: Dict) -> List[Dict]:
        """创建教育视频模板"""
        # 实现教育视频模板
        pass

    def _create_commercial_template(self, config: Dict) -> List[Dict]:
        """创建商业广告模板"""
        # 实现商业广告模板
        pass

    def _create_social_media_template(self, config: Dict) -> List[Dict]:
        """创建社交媒体模板"""
        # 实现社交媒体模板
        pass

    def _generate_broll_clips(self, total_duration: float) -> List[Dict]:
        """生成B-Roll片段"""
        clips = []
        # 每30秒插入一个5秒的B-Roll
        for i in range(30, int(total_duration), 30):
            if i + 5 <= total_duration:
                clips.append({
                    "start": i,
                    "end": i + 5,
                    "clipIn": 0,
                    "clipOut": 5,
                    "filters": ["blur_002"],
                    "transform": {"scale": 1.1, "position": [960, 540]},
                    "opacity": 0.8
                })
        return clips

    def _generate_subtitle_clips(self, subtitles: List[Dict]) -> List[Dict]:
        """生成字幕片段"""
        clips = []
        for subtitle in subtitles:
            clips.append({
                "start": subtitle.get("start", 0),
                "end": subtitle.get("end", 5),
                "clipIn": subtitle.get("start", 0),
                "clipOut": subtitle.get("end", 5),
                "filters": [],
                "content": {
                    "text": subtitle.get("text", ""),
                    "font": "思源黑体",
                    "size": 24,
                    "color": "#FFFFFF",
                    "position": "bottom",
                    "outline": {"color": "#000000", "width": 2}
                }
            })
        return clips

    def _generate_feature_text_clips(self, features: List[str]) -> List[Dict]:
        """生成产品特性文字片段"""
        clips = []
        time_per_feature = 10
        
        for i, feature in enumerate(features):
            clips.append({
                "start": i * time_per_feature + 5,
                "end": (i + 1) * time_per_feature + 5,
                "clipIn": 0,
                "clipOut": time_per_feature,
                "filters": ["glow_001"],
                "content": {
                    "text": feature,
                    "font": "思源黑体",
                    "size": 48,
                    "color": "#00FF00",
                    "position": "center",
                    "animation": "slide_in"
                }
            })
        
        return clips

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def optimize_timeline(self, timeline: Dict) -> Dict:
        """优化时间轴，去除冲突、调整时间等"""
        # 检查并修复时间冲突
        for track in timeline["timeline"]["tracks"]:
            if track["type"] in ["video", "text"]:
                track["clips"] = self._fix_time_conflicts(track["clips"])
        
        # 优化转场时间
        self._optimize_transitions(timeline)
        
        # 添加智能建议
        timeline["suggestions"] = self._generate_suggestions(timeline)
        
        return timeline

    def _fix_time_conflicts(self, clips: List[Dict]) -> List[Dict]:
        """修复时间冲突"""
        # 按开始时间排序
        sorted_clips = sorted(clips, key=lambda x: x["start"])
        
        # 检查并修复重叠
        for i in range(1, len(sorted_clips)):
            if sorted_clips[i]["start"] < sorted_clips[i-1]["end"]:
                # 调整开始时间
                sorted_clips[i]["start"] = sorted_clips[i-1]["end"]
                sorted_clips[i]["clipIn"] = sorted_clips[i]["start"]
        
        return sorted_clips

    def _optimize_transitions(self, timeline: Dict) -> None:
        """优化转场效果"""
        for track in timeline["timeline"]["tracks"]:
            if track["type"] == "video":
                for i in range(len(track["clips"]) - 1):
                    current_clip = track["clips"][i]
                    next_clip = track["clips"][i + 1]
                    
                    # 如果两个片段相邻，添加转场
                    if abs(current_clip["end"] - next_clip["start"]) < 0.1:
                        if "transition_out" not in current_clip:
                            current_clip["transition_out"] = {"type": "fade", "duration": 0.5}
                        if "transition_in" not in next_clip:
                            next_clip["transition_in"] = {"type": "fade", "duration": 0.5}

    def _generate_suggestions(self, timeline: Dict) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 检查总时长
        duration = timeline["timeline"]["duration"]
        if duration > 300:
            suggestions.append("视频时长超过5分钟，建议精简内容以提高观看完成率")
        
        # 检查特效使用
        effect_count = sum(len(clip.get("filters", [])) for track in timeline["timeline"]["tracks"] 
                          for clip in track.get("clips", []))
        if effect_count > 20:
            suggestions.append("特效使用较多，可能影响视频流畅度，建议适当减少")
        
        # 检查音频轨道
        audio_tracks = [t for t in timeline["timeline"]["tracks"] if t["type"] == "audio"]
        if len(audio_tracks) > 3:
            suggestions.append("音频轨道较多，注意音量平衡避免混音问题")
        
        return suggestions


def test_generator():
    """测试时间轴生成器"""
    generator = TimelineGenerator()
    
    # 测试配置
    config = {
        "title": "产品介绍视频",
        "duration": 60,
        "template": "product",
        "features": [
            "智能AI驱动",
            "一键生成视频",
            "多种模板选择",
            "专业级效果"
        ],
        "video_segments": [{
            "name": "主视频",
            "clips": [{
                "start": 0,
                "end": 60,
                "effects": ["color_correct", "vignette"],
                "transform": {"scale": 1.0, "position": [960, 540]}
            }]
        }],
        "text_segments": [{
            "name": "标题字幕",
            "texts": [{
                "start": 0,
                "end": 5,
                "text": "AI视频剪辑系统",
                "size": 48,
                "color": "#FFD700",
                "position": "center",
                "effects": ["glow"]
            }]
        }],
        "audio_segments": [{
            "name": "背景音乐",
            "audios": [{
                "start": 0,
                "end": 60,
                "source": "epic_bgm.mp3",
                "volume": 0.6,
                "loop": True
            }]
        }]
    }
    
    # 生成时间轴
    timeline = generator.generate_advanced_timeline(config)
    
    # 优化时间轴
    timeline = generator.optimize_timeline(timeline)
    
    # 保存结果
    with open("output/advanced_timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print("高级时间轴已生成并保存到 output/advanced_timeline.json")


if __name__ == "__main__":
    test_generator()
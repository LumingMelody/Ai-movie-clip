"""
AuraRender 8大艺术风格系统实现
按照设计文档要求，实现8种独特的艺术风格
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class StyleConfig:
    """风格配置"""
    name: str
    filters: List[str]
    color_grading: Dict[str, Any]
    effects: List[str]
    transitions: List[str]
    audio_style: str
    font_style: str


class ArtisticStyleSystem:
    """8大艺术风格系统"""
    
    def __init__(self):
        self.styles = self._initialize_styles()
        
    def _initialize_styles(self) -> Dict[str, StyleConfig]:
        """初始化8种艺术风格"""
        return {
            "复古赛博": StyleConfig(
                name="Retro Cyberpunk",
                filters=["neon_glow", "chromatic_aberration", "grain"],
                color_grading={
                    "highlights": {"r": 255, "g": 0, "b": 128},  # 霓虹粉
                    "shadows": {"r": 0, "g": 30, "b": 60},  # 深蓝
                    "contrast": 1.3,
                    "saturation": 1.5
                },
                effects=["glitch", "scan_lines", "digital_noise"],
                transitions=["glitch", "digital_wipe", "pixelate"],
                audio_style="synthwave",
                font_style="tech_mono"
            ),
            
            "黑白默片": StyleConfig(
                name="Silent Film",
                filters=["black_white", "vignette", "film_grain"],
                color_grading={
                    "desaturate": True,
                    "contrast": 1.4,
                    "brightness": 0.9,
                    "sepia_tone": 0.2
                },
                effects=["film_scratches", "flicker", "speed_variation"],
                transitions=["iris_wipe", "fade_to_black", "title_card"],
                audio_style="silent_piano",
                font_style="vintage_serif"
            ),
            
            "梦幻仙境": StyleConfig(
                name="Dreamland Fantasy",
                filters=["soft_focus", "bloom", "fairy_dust"],
                color_grading={
                    "highlights": {"r": 255, "g": 230, "b": 240},  # 柔和粉色
                    "shadows": {"r": 100, "g": 80, "b": 120},  # 紫色阴影
                    "saturation": 0.8,
                    "luminance": 1.1
                },
                effects=["sparkles", "lens_flare", "bokeh"],
                transitions=["dissolve", "dream_blur", "fairy_wipe"],
                audio_style="ethereal",
                font_style="fantasy_script"
            ),
            
            "手绘动画": StyleConfig(
                name="Hand Drawn Animation",
                filters=["pencil_sketch", "watercolor", "paper_texture"],
                color_grading={
                    "saturation": 0.7,
                    "contrast": 0.9,
                    "roughness": 0.3
                },
                effects=["brush_strokes", "ink_splatter", "sketch_lines"],
                transitions=["page_turn", "sketch_reveal", "paint_wipe"],
                audio_style="acoustic",
                font_style="handwritten"
            ),
            
            "极简扁平": StyleConfig(
                name="Minimal Flat",
                filters=["posterize", "flat_color", "clean_edges"],
                color_grading={
                    "palette_limit": 5,  # 限制调色板
                    "contrast": 1.5,
                    "saturation": 1.2,
                    "no_gradients": True
                },
                effects=["geometric_shapes", "solid_shadows", "vector_graphics"],
                transitions=["slide", "push", "geometric_wipe"],
                audio_style="minimal_electronic",
                font_style="sans_serif_bold"
            ),
            
            "胶片质感": StyleConfig(
                name="Film Aesthetic",
                filters=["35mm_film", "halation", "film_grain"],
                color_grading={
                    "highlights": {"r": 255, "g": 245, "b": 230},  # 暖色高光
                    "shadows": {"r": 20, "g": 30, "b": 40},  # 冷色阴影
                    "orange_teal": True,
                    "film_curve": "kodak"
                },
                effects=["lens_distortion", "anamorphic_flare", "film_burn"],
                transitions=["film_burn", "light_leak", "cross_process"],
                audio_style="cinematic",
                font_style="cinema_classic"
            ),
            
            "故障艺术": StyleConfig(
                name="Glitch Art",
                filters=["datamosh", "pixel_sort", "rgb_shift"],
                color_grading={
                    "rgb_split": 5,  # RGB通道分离
                    "bit_crush": 6,  # 位深度压缩
                    "contrast": 1.6
                },
                effects=["corrupted_data", "screen_tear", "compression_artifacts"],
                transitions=["data_corruption", "signal_loss", "pixel_explosion"],
                audio_style="glitch_electronic",
                font_style="corrupted_mono"
            ),
            
            "蒸汽波": StyleConfig(
                name="Vaporwave",
                filters=["vhs_effect", "crt_screen", "pastel_gradient"],
                color_grading={
                    "highlights": {"r": 255, "g": 150, "b": 200},  # 粉紫色
                    "shadows": {"r": 100, "g": 0, "b": 100},  # 深紫
                    "saturation": 1.8,
                    "hue_shift": 20
                },
                effects=["vhs_tracking", "japanese_text", "geometric_patterns"],
                transitions=["vhs_rewind", "crt_switch", "wave_distortion"],
                audio_style="vaporwave",
                font_style="retro_japanese"
            )
        }
    
    def apply_style(self, clip_data: Dict[str, Any], style_name: str) -> Dict[str, Any]:
        """
        将艺术风格应用到视频片段
        
        Args:
            clip_data: 视频片段数据
            style_name: 风格名称
            
        Returns:
            应用风格后的片段数据
        """
        if style_name not in self.styles:
            return clip_data
            
        style = self.styles[style_name]
        
        # 应用滤镜
        if "filters" not in clip_data:
            clip_data["filters"] = []
        clip_data["filters"].extend(style.filters)
        
        # 应用颜色分级
        clip_data["color_grading"] = style.color_grading
        
        # 应用特效
        if "effects" not in clip_data:
            clip_data["effects"] = []
        clip_data["effects"].extend(style.effects)
        
        # 设置转场
        clip_data["transition_style"] = style.transitions[0]
        
        # 设置音频风格
        clip_data["audio_style"] = style.audio_style
        
        # 设置字体风格
        if "text_style" in clip_data:
            clip_data["text_style"]["font"] = style.font_style
            
        return clip_data
    
    def get_style_filters(self, style_name: str) -> List[str]:
        """获取风格的滤镜列表"""
        if style_name in self.styles:
            return self.styles[style_name].filters
        return []
    
    def get_style_transitions(self, style_name: str) -> List[str]:
        """获取风格的转场列表"""
        if style_name in self.styles:
            return self.styles[style_name].transitions
        return []
    
    def get_color_grading(self, style_name: str) -> Dict[str, Any]:
        """获取风格的调色参数"""
        if style_name in self.styles:
            return self.styles[style_name].color_grading
        return {}
    
    def mix_styles(self, style1: str, style2: str, ratio: float = 0.5) -> StyleConfig:
        """
        混合两种风格
        
        Args:
            style1: 第一种风格
            style2: 第二种风格
            ratio: 混合比例 (0-1)，0表示完全style1，1表示完全style2
            
        Returns:
            混合后的风格配置
        """
        if style1 not in self.styles or style2 not in self.styles:
            return self.styles.get(style1, self.styles.get(style2))
            
        s1 = self.styles[style1]
        s2 = self.styles[style2]
        
        # 混合滤镜（按比例选择）
        filter_count1 = int(len(s1.filters) * (1 - ratio))
        filter_count2 = int(len(s2.filters) * ratio)
        mixed_filters = s1.filters[:filter_count1] + s2.filters[:filter_count2]
        
        # 混合颜色分级（线性插值）
        mixed_color = self._mix_color_grading(s1.color_grading, s2.color_grading, ratio)
        
        # 混合特效
        effect_count1 = int(len(s1.effects) * (1 - ratio))
        effect_count2 = int(len(s2.effects) * ratio)
        mixed_effects = s1.effects[:effect_count1] + s2.effects[:effect_count2]
        
        return StyleConfig(
            name=f"{s1.name}_{s2.name}_mix",
            filters=mixed_filters,
            color_grading=mixed_color,
            effects=mixed_effects,
            transitions=s1.transitions if ratio < 0.5 else s2.transitions,
            audio_style=s1.audio_style if ratio < 0.5 else s2.audio_style,
            font_style=s1.font_style if ratio < 0.5 else s2.font_style
        )
    
    def _mix_color_grading(self, cg1: Dict, cg2: Dict, ratio: float) -> Dict:
        """混合两个调色参数"""
        mixed = {}
        
        # 处理数值型参数
        for key in ["contrast", "saturation", "brightness", "luminance"]:
            if key in cg1 and key in cg2:
                if isinstance(cg1[key], (int, float)) and isinstance(cg2[key], (int, float)):
                    mixed[key] = cg1[key] * (1 - ratio) + cg2[key] * ratio
            elif key in cg1:
                mixed[key] = cg1[key]
            elif key in cg2:
                mixed[key] = cg2[key]
        
        # 处理颜色值
        for key in ["highlights", "shadows"]:
            if key in cg1 and key in cg2:
                mixed[key] = self._mix_colors(cg1[key], cg2[key], ratio)
            elif key in cg1:
                mixed[key] = cg1[key]
            elif key in cg2:
                mixed[key] = cg2[key]
                
        return mixed
    
    def _mix_colors(self, color1: Dict, color2: Dict, ratio: float) -> Dict:
        """混合两个RGB颜色"""
        return {
            "r": int(color1["r"] * (1 - ratio) + color2["r"] * ratio),
            "g": int(color1["g"] * (1 - ratio) + color2["g"] * ratio),
            "b": int(color1["b"] * (1 - ratio) + color2["b"] * ratio)
        }
    
    def get_style_intensity(self, style_name: str, intensity: str = "medium") -> Dict[str, float]:
        """
        获取风格强度参数
        
        Args:
            style_name: 风格名称
            intensity: 强度级别 ("light", "medium", "heavy")
            
        Returns:
            强度参数字典
        """
        intensity_map = {
            "light": 0.3,
            "medium": 0.7,
            "heavy": 1.0
        }
        
        base_intensity = intensity_map.get(intensity, 0.7)
        
        return {
            "filter_opacity": base_intensity,
            "effect_strength": base_intensity,
            "color_grading_amount": base_intensity,
            "transition_duration": 1.0 + base_intensity  # 1-2秒
        }
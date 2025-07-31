"""
产品广告视频模板

适用于：商品展示、产品介绍、促销广告
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class ProductAdTemplate(BaseVideoTemplate):
    """产品广告模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的产品广告策划师。请根据用户的产品描述，生成一个吸引人的产品广告视频大纲。
        大纲应包含：
        1. 开场钩子（3-5秒）- 吸引注意力
        2. 产品展示（10-15秒）- 展示产品外观和特点
        3. 功能演示（10-15秒）- 展示核心功能和优势
        4. 用户场景（5-10秒）- 展示使用场景
        5. 行动号召（3-5秒）- 促进购买行动
        
        请确保整体节奏紧凑，视觉冲击力强。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 30,
            'sections': [
                {
                    'name': '开场钩子',
                    'duration': 5,
                    'description': '震撼的产品特写或问题场景',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '还在为XX烦恼吗？',
                    'text_style': {
                        'size': 60,
                        'color': '#FFFFFF',
                        'animation': 'slide_in'
                    },
                    'effects': ['zoom_in', 'blur_background']
                },
                {
                    'name': '产品展示',
                    'duration': 10,
                    'description': '360度展示产品外观',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '全新设计，品质之选',
                    'effects': ['slow_motion', 'glow']
                },
                {
                    'name': '功能演示',
                    'duration': 10,
                    'description': '展示3个核心功能点',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '强大功能，一触即发',
                    'effects': ['split_screen', 'highlight']
                },
                {
                    'name': '行动号召',
                    'duration': 5,
                    'description': '促销信息和购买引导',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '限时优惠，立即抢购！',
                    'text_style': {
                        'size': 80,
                        'color': '#FF4444',
                        'animation': 'pulse'
                    },
                    'effects': ['flash', 'countdown']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'modern',
            'color_scheme': 'vibrant',
            'transition_style': 'dynamic',
            'music_style': 'upbeat_electronic',
            'text_animation': 'energetic',
            'camera_movement': 'dynamic',
            'effects_intensity': 'high'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'product_shots': 3,
                'usage_scenes': 2,
                'detail_shots': 4
            },
            'images': {
                'product_images': 5,
                'logo': 1,
                'background': 2
            },
            'audio': {
                'background_music': 'energetic',
                'sound_effects': ['whoosh', 'impact', 'chime']
            },
            'graphics': {
                'price_tags': True,
                'feature_icons': True,
                'cta_buttons': True
            }
        }
"""
品牌宣传视频模板

适用于：企业形象、品牌故事、公司介绍
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class BrandPromoTemplate(BaseVideoTemplate):
    """品牌宣传模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的品牌营销策划师。请根据用户的品牌描述，生成一个有感染力的品牌宣传视频大纲。
        大纲应包含：
        1. 品牌引入（5-8秒）- 展示品牌标识和理念
        2. 企业故事（15-20秒）- 讲述品牌历史或创始故事
        3. 核心价值（10-15秒）- 展示品牌价值观和使命
        4. 产品/服务展示（15-20秒）- 展示主要产品或服务
        5. 未来愿景（5-10秒）- 展望品牌未来
        
        整体风格应专业、有温度、能引起共鸣。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 60,
            'sections': [
                {
                    'name': '品牌引入',
                    'duration': 8,
                    'description': 'Logo动画和品牌标语',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '创新引领未来',
                    'text_style': {
                        'size': 72,
                        'color': '#FFFFFF',
                        'font': 'elegant',
                        'animation': 'fade_in'
                    },
                    'effects': ['logo_reveal', 'light_rays']
                },
                {
                    'name': '企业故事',
                    'duration': 20,
                    'description': '创始人故事或企业发展历程',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '从梦想到现实的征程',
                    'effects': ['vintage_filter', 'smooth_transition']
                },
                {
                    'name': '核心价值',
                    'duration': 15,
                    'description': '展示企业文化和价值观',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '品质、创新、责任',
                    'effects': ['parallax', 'color_overlay']
                },
                {
                    'name': '产品服务',
                    'duration': 12,
                    'description': '主要产品和服务展示',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['multi_screen', 'smooth_zoom']
                },
                {
                    'name': '未来愿景',
                    'duration': 5,
                    'description': '品牌愿景和号召',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '携手共创美好未来',
                    'text_style': {
                        'size': 60,
                        'color': '#GOLD',
                        'animation': 'scale_up'
                    },
                    'effects': ['sunrise', 'lens_flare']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'professional',
            'color_scheme': 'corporate',
            'transition_style': 'smooth',
            'music_style': 'inspirational_orchestral',
            'text_animation': 'elegant',
            'camera_movement': 'cinematic',
            'effects_intensity': 'moderate'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'office_shots': 3,
                'team_shots': 4,
                'product_shots': 5,
                'customer_testimonials': 2
            },
            'images': {
                'company_logo': 1,
                'milestone_images': 5,
                'team_photos': 3,
                'product_images': 4
            },
            'audio': {
                'background_music': 'inspirational',
                'narration': 'professional_male',
                'sound_effects': ['swoosh', 'ambient']
            },
            'graphics': {
                'timeline': True,
                'statistics': True,
                'awards': True,
                'map_animation': True
            }
        }
"""
概念展示视频模板

适用于：创意展示、设计作品、概念演示
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class ConceptShowTemplate(BaseVideoTemplate):
    """概念展示模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个创意总监。请根据用户的概念描述，生成一个视觉震撼的概念展示视频大纲。
        大纲应包含：
        1. 概念引入（8秒）- 神秘感的开场
        2. 灵感来源（12秒）- 展示创意灵感
        3. 设计过程（20秒）- 展现创作过程
        4. 成品展示（15秒）- 多角度展示作品
        5. 应用场景（10秒）- 展示实际应用
        
        强调视觉创新、设计美学和概念传达。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 65,
            'sections': [
                {
                    'name': '概念引入',
                    'duration': 8,
                    'description': '抽象视觉引入概念',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'CONCEPT',
                    'text_style': {
                        'size': 72,
                        'color': '#FFFFFF',
                        'font': 'futuristic',
                        'animation': 'glitch'
                    },
                    'effects': ['abstract_visuals', 'particle_effects']
                },
                {
                    'name': '灵感来源',
                    'duration': 12,
                    'description': '展示灵感和参考',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'Inspired by...',
                    'effects': ['mood_board', 'overlay_blend']
                },
                {
                    'name': '设计过程',
                    'duration': 20,
                    'description': '创作过程展示',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['speed_ramp', 'process_visualization']
                },
                {
                    'name': '成品展示',
                    'duration': 15,
                    'description': '360度展示最终作品',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['3d_rotation', 'studio_lighting']
                },
                {
                    'name': '应用场景',
                    'duration': 10,
                    'description': '实际应用展示',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'In Real World',
                    'effects': ['mockup_animation', 'environment_composite']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'avant_garde',
            'color_scheme': 'bold_contrast',
            'transition_style': 'experimental',
            'music_style': 'electronic_ambient',
            'text_animation': 'innovative',
            'camera_movement': 'geometric',
            'effects_intensity': 'very_high',
            'visual_style': 'cutting_edge'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'concept_animation': 8,
                'process_footage': 6,
                'product_shots': 10,
                'environment_shots': 4
            },
            'images': {
                'sketches': 8,
                'mood_board': 5,
                '3d_renders': 6,
                'mockups': 4
            },
            'audio': {
                'background_music': 'futuristic',
                'sound_design': 'experimental',
                'whoosh_effects': True
            },
            'graphics': {
                '3d_elements': True,
                'particle_systems': True,
                'data_visualization': True,
                'holographic_effects': True,
                'ui_animations': True
            }
        }
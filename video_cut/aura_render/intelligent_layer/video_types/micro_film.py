"""
微电影视频模板

适用于：创意短片、艺术短片、实验影像
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class MicroFilmTemplate(BaseVideoTemplate):
    """微电影模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个独立电影导演。请根据用户的创意概念，生成一个有艺术性的微电影大纲。
        大纲应包含：
        1. 序幕（15秒）- 氛围建立和世界观展示
        2. 起承（30秒）- 角色和情境介绍
        3. 转折（40秒）- 核心事件和情感转变
        4. 高潮（30秒）- 戏剧冲突的顶点
        5. 尾声（15秒）- 意味深长的结尾
        
        追求视觉美学、情感深度和艺术表达。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 130,
            'sections': [
                {
                    'name': '序幕',
                    'duration': 15,
                    'description': '诗意的开场，建立基调',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['cinematic_bars', 'color_grade_artistic']
                },
                {
                    'name': '起承',
                    'duration': 30,
                    'description': '展开故事世界',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['depth_of_field', 'ambient_sound_design']
                },
                {
                    'name': '转折',
                    'duration': 40,
                    'description': '情感和剧情的转变',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['match_cut', 'symbolic_imagery']
                },
                {
                    'name': '高潮',
                    'duration': 30,
                    'description': '情感爆发点',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['dramatic_lighting', 'time_distortion']
                },
                {
                    'name': '尾声',
                    'duration': 15,
                    'description': '留白与思考',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'A Film by...',
                    'text_style': {
                        'size': 36,
                        'color': '#FFFFFF',
                        'font': 'serif',
                        'animation': 'fade_in_slow'
                    },
                    'effects': ['long_take', 'fade_to_credits']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'cinematic',
            'color_scheme': 'artistic_palette',
            'transition_style': 'poetic',
            'music_style': 'atmospheric_score',
            'text_animation': 'minimal',
            'camera_movement': 'deliberate',
            'effects_intensity': 'subtle',
            'aspect_ratio': '2.35:1',
            'film_grain': True
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'establishing_shots': 5,
                'character_studies': 8,
                'symbolic_shots': 6,
                'landscape_shots': 4,
                'detail_shots': 10
            },
            'images': {
                'stills': 5,
                'texture_overlays': 3
            },
            'audio': {
                'original_score': 'cinematic',
                'ambient_sounds': 'layered',
                'dialogue': 'minimal',
                'sound_design': 'artistic'
            },
            'graphics': {
                'title_design': True,
                'credits_roll': True,
                'festival_laurels': True,
                'artistic_overlays': True
            }
        }
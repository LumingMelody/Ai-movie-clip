"""
短剧视频模板

适用于：剧情短片、创意故事、情景剧
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class ShortDramaTemplate(BaseVideoTemplate):
    """短剧模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的短剧编剧。请根据用户的故事概念，生成一个吸引人的短剧视频大纲。
        大纲应包含：
        1. 开场设置（10秒）- 建立场景和人物
        2. 冲突引入（15秒）- 引入矛盾或问题
        3. 情节发展（20秒）- 故事推进和转折
        4. 高潮时刻（10秒）- 矛盾达到顶点
        5. 结局收尾（5秒）- 解决或留白
        
        确保故事紧凑、情感真实、有记忆点。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 60,
            'sections': [
                {
                    'name': '开场设置',
                    'duration': 10,
                    'description': '展示环境和主角',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['establishing_shot', 'ambient_sound']
                },
                {
                    'name': '冲突引入',
                    'duration': 15,
                    'description': '出现问题或意外',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['dramatic_music', 'quick_cuts']
                },
                {
                    'name': '情节发展',
                    'duration': 20,
                    'description': '角色应对和故事推进',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['emotional_close_up', 'tension_build']
                },
                {
                    'name': '高潮时刻',
                    'duration': 10,
                    'description': '冲突达到顶峰',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['slow_motion', 'dramatic_pause']
                },
                {
                    'name': '结局收尾',
                    'duration': 5,
                    'description': '故事结束或悬念',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '未完待续...',
                    'text_style': {
                        'size': 48,
                        'color': '#FFFFFF',
                        'animation': 'fade_in'
                    },
                    'effects': ['fade_out', 'end_card']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'cinematic',
            'color_scheme': 'dramatic',
            'transition_style': 'narrative',
            'music_style': 'emotional_score',
            'text_animation': 'minimal',
            'camera_movement': 'dynamic',
            'effects_intensity': 'high',
            'lighting_style': 'moody'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'character_shots': 8,
                'environment_shots': 4,
                'action_sequences': 5,
                'reaction_shots': 6
            },
            'images': {
                'storyboard': 10,
                'location_photos': 3
            },
            'audio': {
                'background_music': 'dramatic',
                'dialogue': 'character_voices',
                'sound_effects': ['footsteps', 'door_slam', 'ambient'],
                'foley': True
            },
            'graphics': {
                'title_card': True,
                'credits': True,
                'subtitle_options': True
            }
        }
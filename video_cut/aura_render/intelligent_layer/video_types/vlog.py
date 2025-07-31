"""
Vlog视频模板

适用于：日常记录、旅行日志、生活分享
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class VlogTemplate(BaseVideoTemplate):
    """Vlog模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的Vlog创作者。请根据用户的主题，生成一个有个人特色的Vlog视频大纲。
        大纲应包含：
        1. 开场打招呼（5-8秒）- 个人风格的开场
        2. 今日主题（8-10秒）- 介绍本期内容
        3. 主要内容（30-40秒）- 核心记录内容
        4. 感受分享（10-15秒）- 个人感想和心得
        5. 结尾互动（5-8秒）- 观众互动和预告
        
        保持真实、轻松、有亲和力的风格。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 75,
            'sections': [
                {
                    'name': '开场打招呼',
                    'duration': 8,
                    'description': '面对镜头打招呼',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'Hello大家好！',
                    'text_style': {
                        'size': 48,
                        'color': '#FFD700',
                        'font': 'casual',
                        'animation': 'bounce_in'
                    },
                    'effects': ['handheld_shake', 'warm_filter']
                },
                {
                    'name': '今日主题',
                    'duration': 10,
                    'description': '介绍今天要做什么',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '今天带大家去...',
                    'effects': ['location_tag', 'date_stamp']
                },
                {
                    'name': '主要内容',
                    'duration': 35,
                    'description': '记录主要活动',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['time_lapse', 'montage', 'background_music']
                },
                {
                    'name': '感受分享',
                    'duration': 15,
                    'description': '分享个人感受',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '今天真的太开心了',
                    'effects': ['slow_motion_highlight', 'emotional_music']
                },
                {
                    'name': '结尾互动',
                    'duration': 7,
                    'description': '和观众说再见',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '下期见！记得点赞哦',
                    'text_style': {
                        'size': 42,
                        'color': '#FF69B4',
                        'animation': 'wave'
                    },
                    'effects': ['subscribe_reminder', 'end_screen']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'casual',
            'color_scheme': 'natural_warm',
            'transition_style': 'smooth_cut',
            'music_style': 'upbeat_casual',
            'text_animation': 'playful',
            'camera_movement': 'handheld',
            'effects_intensity': 'moderate',
            'filter_style': 'lifestyle'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'talking_head': 5,
                'b_roll': 15,
                'time_lapse': 3,
                'slow_motion': 4
            },
            'images': {
                'thumbnail': 1,
                'location_photos': 5,
                'food_photos': 3,
                'selfies': 4
            },
            'audio': {
                'background_music': 'vlog_style',
                'ambient_sound': True,
                'voice_over': 'natural'
            },
            'graphics': {
                'location_tags': True,
                'time_stamps': True,
                'emoji_stickers': True,
                'social_media_tags': True,
                'subscribe_button': True
            }
        }
"""
音乐MV视频模板

适用于：歌曲MV、音乐视频、节奏剪辑
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class MusicMVTemplate(BaseVideoTemplate):
    """音乐MV模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的MV导演。请根据用户的音乐风格和主题，生成一个有视觉冲击力的MV大纲。
        大纲应包含：
        1. 前奏部分（10-15秒）- 建立氛围
        2. 主歌部分（30-40秒）- 展现主题
        3. 副歌部分（20-30秒）- 视觉高潮
        4. 间奏/桥段（15-20秒）- 情绪转换
        5. 尾奏部分（10-15秒）- 情感升华
        
        确保画面节奏与音乐完美契合，视觉效果震撼。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 120,
            'sections': [
                {
                    'name': '前奏',
                    'duration': 15,
                    'description': '氛围营造和视觉引入',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['slow_fade_in', 'atmospheric_filter']
                },
                {
                    'name': '主歌A',
                    'duration': 30,
                    'description': '故事或情感展开',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '歌词字幕',
                    'text_style': {
                        'size': 36,
                        'color': '#FFFFFF',
                        'animation': 'sync_with_beat'
                    },
                    'effects': ['color_grading', 'rhythm_cuts']
                },
                {
                    'name': '副歌',
                    'duration': 25,
                    'description': '视觉和情感高潮',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '歌词字幕',
                    'effects': ['fast_cuts', 'light_effects', 'slow_motion']
                },
                {
                    'name': '主歌B',
                    'duration': 25,
                    'description': '深化主题',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '歌词字幕',
                    'effects': ['cross_fade', 'double_exposure']
                },
                {
                    'name': '桥段',
                    'duration': 15,
                    'description': '情绪转折点',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['artistic_filter', 'time_lapse']
                },
                {
                    'name': '尾奏',
                    'duration': 10,
                    'description': '情感收束',
                    'has_video': True,
                    'has_text': False,
                    'effects': ['fade_to_black', 'echo_effect']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'artistic',
            'color_scheme': 'mood_based',
            'transition_style': 'beat_sync',
            'music_style': 'primary_track',
            'text_animation': 'rhythmic',
            'camera_movement': 'dynamic',
            'effects_intensity': 'very_high',
            'visual_style': 'music_genre_specific'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'performance_shots': 10,
                'narrative_shots': 8,
                'abstract_visuals': 6,
                'location_shots': 5
            },
            'images': {
                'artist_photos': 5,
                'album_artwork': 1,
                'visual_elements': 10
            },
            'audio': {
                'main_track': 'user_provided',
                'sound_effects': ['reverb', 'echo', 'filter_sweep']
            },
            'graphics': {
                'lyric_animations': True,
                'visual_effects': True,
                'particle_systems': True,
                'color_overlays': True,
                'beat_visualizer': True
            }
        }
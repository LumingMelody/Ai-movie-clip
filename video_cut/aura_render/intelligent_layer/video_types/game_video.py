"""
游戏视频模板

适用于：游戏实况、游戏剪辑、电竞集锦
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class GameVideoTemplate(BaseVideoTemplate):
    """游戏视频模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个游戏视频编辑师。请根据用户的游戏内容，生成一个精彩刺激的游戏视频大纲。
        大纲应包含：
        1. 炫酷开场（5秒）- 吸引眼球的片头
        2. 精彩预览（8秒）- 本期高光时刻预告
        3. 主要内容（35秒）- 游戏精彩片段
        4. 技巧展示（10秒）- 操作技巧或攻略
        5. 结尾彩蛋（5秒）- 搞笑或意外时刻
        
        确保节奏快速、剪辑炫酷、充满能量。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 63,
            'sections': [
                {
                    'name': '炫酷开场',
                    'duration': 5,
                    'description': '动感片头动画',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'GAME ON!',
                    'text_style': {
                        'size': 84,
                        'color': '#FF0000',
                        'font': 'gaming',
                        'animation': 'explosion'
                    },
                    'effects': ['logo_animation', 'fire_effect']
                },
                {
                    'name': '精彩预览',
                    'duration': 8,
                    'description': '快速剪辑高光时刻',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '本期精彩',
                    'effects': ['fast_cuts', 'epic_music_sync']
                },
                {
                    'name': '主要内容',
                    'duration': 35,
                    'description': '游戏精彩瞬间',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '击杀时刻！',
                    'effects': ['slow_motion_kills', 'damage_numbers']
                },
                {
                    'name': '技巧展示',
                    'duration': 10,
                    'description': '操作技巧讲解',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'PRO TIPS',
                    'text_style': {
                        'size': 48,
                        'color': '#00FF00',
                        'animation': 'type_on'
                    },
                    'effects': ['replay_analysis', 'arrow_indicators']
                },
                {
                    'name': '结尾彩蛋',
                    'duration': 5,
                    'description': '搞笑失误或彩蛋',
                    'has_video': True,
                    'has_text': True,
                    'text_content': 'FAIL!',
                    'effects': ['meme_overlay', 'funny_sound']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'gaming',
            'color_scheme': 'neon_rgb',
            'transition_style': 'glitch',
            'music_style': 'electronic_dubstep',
            'text_animation': 'aggressive',
            'camera_movement': 'dynamic',
            'effects_intensity': 'extreme',
            'fps_display': True
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'gameplay_footage': 20,
                'kill_montage': 10,
                'funny_moments': 5,
                'victory_screens': 3
            },
            'images': {
                'game_logo': 1,
                'rank_badges': 3,
                'achievement_icons': 5
            },
            'audio': {
                'background_music': 'epic_gaming',
                'sound_effects': ['headshot', 'level_up', 'combo'],
                'voice_commentary': 'energetic'
            },
            'graphics': {
                'kill_counter': True,
                'health_bars': True,
                'crosshair_overlay': True,
                'combo_text': True,
                'rank_display': True,
                'minimap_highlight': True
            }
        }
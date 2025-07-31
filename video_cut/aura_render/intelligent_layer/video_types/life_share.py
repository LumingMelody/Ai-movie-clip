"""
生活分享视频模板

适用于：生活技巧、经验分享、日常记录
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class LifeShareTemplate(BaseVideoTemplate):
    """生活分享模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个生活方式博主。请根据用户的分享主题，生成一个实用有趣的生活分享视频大纲。
        大纲应包含：
        1. 话题引入（5-8秒）- 引出今天的分享主题
        2. 问题展示（8-10秒）- 展示常见问题或痛点
        3. 解决方案（25-30秒）- 详细展示解决方法
        4. 效果对比（10-15秒）- 展示前后对比
        5. 小贴士（5-8秒）- 额外的实用建议
        
        确保内容实用、步骤清晰、容易跟随。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 60,
            'sections': [
                {
                    'name': '话题引入',
                    'duration': 8,
                    'description': '轻松引入今天的分享',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '今天分享一个超实用的小技巧',
                    'text_style': {
                        'size': 44,
                        'color': '#FF6B6B',
                        'font': 'friendly',
                        'animation': 'slide_up'
                    },
                    'effects': ['zoom_in', 'bright_filter']
                },
                {
                    'name': '问题展示',
                    'duration': 10,
                    'description': '展示大家都会遇到的问题',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '你是不是也有这个困扰？',
                    'effects': ['problem_highlight', 'question_mark']
                },
                {
                    'name': '解决方案',
                    'duration': 27,
                    'description': '步骤详解',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '步骤1、2、3...',
                    'effects': ['step_counter', 'close_up_detail']
                },
                {
                    'name': '效果对比',
                    'duration': 10,
                    'description': '展示使用前后的对比',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '看看效果对比',
                    'effects': ['split_screen', 'before_after']
                },
                {
                    'name': '小贴士',
                    'duration': 5,
                    'description': '额外的实用建议',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '记住这个小窍门哦',
                    'text_style': {
                        'size': 40,
                        'color': '#4ECDC4',
                        'animation': 'pop'
                    },
                    'effects': ['tips_icon', 'save_reminder']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'lifestyle',
            'color_scheme': 'bright_cheerful',
            'transition_style': 'smooth',
            'music_style': 'light_positive',
            'text_animation': 'friendly',
            'camera_movement': 'steady',
            'effects_intensity': 'moderate',
            'lighting': 'bright_natural'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'demonstration': 8,
                'close_ups': 6,
                'result_shots': 4,
                'process_shots': 10
            },
            'images': {
                'before_after': 4,
                'materials_list': 2,
                'step_photos': 6
            },
            'audio': {
                'background_music': 'uplifting',
                'voice_over': 'friendly_guide',
                'sound_effects': ['pop', 'ding', 'success']
            },
            'graphics': {
                'step_numbers': True,
                'material_list': True,
                'timer': True,
                'tips_bubbles': True,
                'save_button': True
            }
        }
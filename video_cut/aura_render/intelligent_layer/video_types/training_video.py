"""
培训视频模板

适用于：企业培训、操作指导、流程说明
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class TrainingVideoTemplate(BaseVideoTemplate):
    """培训视频模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个企业培训内容设计师。请根据用户的培训主题，生成一个专业清晰的培训视频大纲。
        大纲应包含：
        1. 培训介绍（10秒）- 目标和大纲
        2. 背景知识（15秒）- 必要的前置知识
        3. 核心内容（40秒）- 分步骤详细讲解
        4. 实践演练（20秒）- 实际操作演示
        5. 总结要点（10秒）- 知识点回顾
        
        确保逻辑清晰、步骤详细、易于理解和执行。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 95,
            'sections': [
                {
                    'name': '培训介绍',
                    'duration': 10,
                    'description': '展示培训目标和内容概览',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '培训目标：掌握...',
                    'text_style': {
                        'size': 48,
                        'color': '#003366',
                        'font': 'corporate',
                        'animation': 'fade_in'
                    },
                    'effects': ['title_slide', 'agenda_display']
                },
                {
                    'name': '背景知识',
                    'duration': 15,
                    'description': '介绍相关背景和重要性',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '为什么这很重要',
                    'effects': ['infographic', 'statistics_display']
                },
                {
                    'name': '核心内容',
                    'duration': 40,
                    'description': '详细步骤讲解',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '步骤详解',
                    'effects': ['numbered_steps', 'highlight_important']
                },
                {
                    'name': '实践演练',
                    'duration': 20,
                    'description': '实际操作演示',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '让我们实际操作一遍',
                    'effects': ['screen_recording', 'cursor_tracking']
                },
                {
                    'name': '总结要点',
                    'duration': 10,
                    'description': '关键点回顾和后续步骤',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '记住这些关键点',
                    'text_style': {
                        'size': 44,
                        'color': '#009900',
                        'animation': 'checklist'
                    },
                    'effects': ['key_points_summary', 'next_steps']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'corporate',
            'color_scheme': 'professional_blue',
            'transition_style': 'clean',
            'music_style': 'corporate_background',
            'text_animation': 'professional',
            'camera_movement': 'minimal',
            'effects_intensity': 'low',
            'clarity_focus': 'high'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'presenter_video': 5,
                'screen_recording': 8,
                'workplace_footage': 3,
                'animation_explainer': 4
            },
            'images': {
                'company_logo': 1,
                'process_diagrams': 6,
                'screenshots': 10,
                'icons': 15
            },
            'audio': {
                'background_music': 'subtle_corporate',
                'narration': 'professional_clear',
                'sound_effects': ['click', 'transition', 'success']
            },
            'graphics': {
                'bullet_points': True,
                'flowcharts': True,
                'progress_bar': True,
                'checklist': True,
                'warning_highlights': True,
                'quiz_elements': True
            }
        }
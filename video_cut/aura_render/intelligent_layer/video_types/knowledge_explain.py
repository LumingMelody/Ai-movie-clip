"""
知识科普视频模板

适用于：科学解释、知识分享、教育内容
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class KnowledgeExplainTemplate(BaseVideoTemplate):
    """知识科普模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的科普内容创作者。请根据用户的知识主题，生成一个易懂有趣的科普视频大纲。
        大纲应包含：
        1. 引入问题（5-8秒）- 提出引人思考的问题
        2. 基础概念（15-20秒）- 解释基本概念和原理
        3. 深入解析（20-25秒）- 详细讲解核心知识点
        4. 实例说明（15-20秒）- 用生活实例说明
        5. 总结回顾（5-10秒）- 总结要点，引导思考
        
        确保内容准确、逻辑清晰、通俗易懂。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 90,
            'sections': [
                {
                    'name': '引入问题',
                    'duration': 8,
                    'description': '提出有趣的问题引起好奇',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '你知道为什么...？',
                    'text_style': {
                        'size': 56,
                        'color': '#FFFFFF',
                        'font': 'modern',
                        'animation': 'typewriter'
                    },
                    'effects': ['question_mark', 'thinking_bubble']
                },
                {
                    'name': '基础概念',
                    'duration': 20,
                    'description': '用图解说明基本原理',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '首先，我们需要了解...',
                    'effects': ['diagram_animation', 'highlight_key_points']
                },
                {
                    'name': '深入解析',
                    'duration': 25,
                    'description': '详细解释核心知识',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '深入研究后发现...',
                    'effects': ['split_screen', 'data_visualization']
                },
                {
                    'name': '实例说明',
                    'duration': 20,
                    'description': '生活化的例子',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '在日常生活中...',
                    'effects': ['comparison', 'real_world_footage']
                },
                {
                    'name': '总结回顾',
                    'duration': 17,
                    'description': '要点总结和延伸思考',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '记住这三个要点...',
                    'text_style': {
                        'size': 48,
                        'color': '#00FF00',
                        'animation': 'highlight'
                    },
                    'effects': ['checklist', 'mind_map']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'educational',
            'color_scheme': 'bright_clean',
            'transition_style': 'informative',
            'music_style': 'light_educational',
            'text_animation': 'clear',
            'camera_movement': 'steady',
            'effects_intensity': 'moderate',
            'graphics_style': 'infographic'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'explanation_animations': 5,
                'real_world_examples': 3,
                'experiment_footage': 2,
                'expert_interviews': 1
            },
            'images': {
                'diagrams': 8,
                'charts': 4,
                'illustrations': 6,
                'photos': 5
            },
            'audio': {
                'background_music': 'educational',
                'narration': 'clear_friendly',
                'sound_effects': ['pop', 'ding', 'whoosh']
            },
            'graphics': {
                'animated_diagrams': True,
                'data_charts': True,
                'comparison_tables': True,
                'progress_indicators': True,
                'key_point_highlights': True
            }
        }
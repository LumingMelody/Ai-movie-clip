"""
在线课程视频模板

适用于：教学课程、技能培训、专业教程
"""

from .base_template import BaseVideoTemplate
from typing import Dict, Any


class OnlineCourseTemplate(BaseVideoTemplate):
    """在线课程模板"""
    
    def get_outline_prompt(self) -> str:
        return """
        你是一个专业的在线教育内容设计师。请根据用户的课程主题，生成一个结构化的教学视频大纲。
        大纲应包含：
        1. 课程导入（10秒）- 介绍学习目标
        2. 知识讲解（40秒）- 分步骤讲解知识点
        3. 实操演示（30秒）- 具体操作演示
        4. 练习指导（15秒）- 布置练习任务
        5. 课程总结（5秒）- 回顾重点
        
        确保教学目标明确，步骤清晰，便于学习者跟随。
        """
    
    def get_default_structure(self) -> Dict[str, Any]:
        return {
            'total_duration': 100,
            'sections': [
                {
                    'name': '课程导入',
                    'duration': 10,
                    'description': '展示课程标题和学习目标',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '本节课你将学会...',
                    'text_style': {
                        'size': 52,
                        'color': '#FFFFFF',
                        'font': 'professional',
                        'animation': 'slide_in'
                    },
                    'effects': ['title_card', 'objective_list']
                },
                {
                    'name': '知识讲解',
                    'duration': 40,
                    'description': '系统讲解理论知识',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '第一步：基础概念...',
                    'effects': ['whiteboard', 'step_by_step']
                },
                {
                    'name': '实操演示',
                    'duration': 30,
                    'description': '屏幕录制或实际操作',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '让我们来实际操作一下',
                    'effects': ['screen_recording', 'cursor_highlight']
                },
                {
                    'name': '练习指导',
                    'duration': 15,
                    'description': '作业布置和练习要求',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '课后练习：请完成以下任务',
                    'effects': ['task_list', 'timer']
                },
                {
                    'name': '课程总结',
                    'duration': 5,
                    'description': '回顾本课重点',
                    'has_video': True,
                    'has_text': True,
                    'text_content': '记住今天的三个要点',
                    'effects': ['summary_card', 'next_lesson_preview']
                }
            ]
        }
    
    def get_style_preferences(self) -> Dict[str, Any]:
        return {
            'primary_style': 'educational',
            'color_scheme': 'professional_clean',
            'transition_style': 'smooth',
            'music_style': 'calm_focus',
            'text_animation': 'clear',
            'camera_movement': 'minimal',
            'effects_intensity': 'low'
        }
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        return {
            'video_clips': {
                'instructor_video': 3,
                'screen_recording': 5,
                'demonstration': 4,
                'student_examples': 2
            },
            'images': {
                'slides': 10,
                'diagrams': 6,
                'screenshots': 8,
                'course_logo': 1
            },
            'audio': {
                'background_music': 'subtle',
                'narration': 'instructor_voice',
                'sound_effects': ['click', 'transition']
            },
            'graphics': {
                'progress_bar': True,
                'chapter_markers': True,
                'quiz_elements': True,
                'code_snippets': True
            }
        }
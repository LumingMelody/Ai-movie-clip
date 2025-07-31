"""
基础视频模板类

所有视频类型模板的基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseVideoTemplate(ABC):
    """视频模板基类"""
    
    def __init__(self):
        self.type_name = self.__class__.__name__.replace('Template', '').lower()
        
    @abstractmethod
    def get_outline_prompt(self) -> str:
        """获取大纲生成提示词"""
        pass
    
    @abstractmethod
    def get_default_structure(self) -> Dict[str, Any]:
        """获取默认的视频结构"""
        pass
    
    @abstractmethod
    def get_style_preferences(self) -> Dict[str, Any]:
        """获取风格偏好设置"""
        pass
    
    @abstractmethod
    def get_resource_requirements(self) -> Dict[str, Any]:
        """获取资源需求"""
        pass
    
    def generate_outline(self, user_input: str) -> str:
        """
        生成视频大纲
        
        Args:
            user_input: 用户输入的自然语言描述
            
        Returns:
            视频大纲文本
        """
        prompt = self.get_outline_prompt()
        # 这里可以调用AI模型生成大纲
        # 简化处理，返回模板化的大纲
        return self._format_outline(user_input)
    
    def _format_outline(self, user_input: str) -> str:
        """格式化大纲"""
        structure = self.get_default_structure()
        sections = []
        
        for section in structure['sections']:
            sections.append(f"【{section['name']}】")
            sections.append(f"时长：{section['duration']}秒")
            sections.append(f"内容：{section['description']}")
            sections.append("")
        
        return "\n".join(sections)
    
    def get_timeline_template(self) -> List[Dict[str, Any]]:
        """获取时间轴模板"""
        structure = self.get_default_structure()
        timeline = []
        current_time = 0
        
        for section in structure['sections']:
            duration = section['duration']
            timeline.append({
                'start': current_time,
                'end': current_time + duration,
                'name': section['name'],
                'layers': self._get_section_layers(section)
            })
            current_time += duration
            
        return timeline
    
    def _get_section_layers(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取片段的图层配置"""
        layers = []
        
        # 主视频层
        if section.get('has_video', True):
            layers.append({
                'type': 'video',
                'resource_id': f"video_{section['name']}",
                'effects': section.get('effects', [])
            })
        
        # 文字层
        if section.get('has_text', False):
            layers.append({
                'type': 'text',
                'content': section.get('text_content', ''),
                'style': section.get('text_style', {})
            })
            
        return layers
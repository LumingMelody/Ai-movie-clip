"""
自然语言处理器
将用户的自然语言输入转换为DAG系统可理解的大纲内容
"""
import os
import json
import dashscope
from dashscope import Generation
from typing import Dict, Optional


class NLProcessor:
    """自然语言处理器，将用户输入转换为视频大纲"""
    
    def __init__(self):
        """初始化处理器"""
        # 获取API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            try:
                api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'api_key.txt')
                if os.path.exists(api_key_path):
                    with open(api_key_path, 'r') as f:
                        api_key = f.read().strip()
            except:
                pass
        
        if api_key:
            dashscope.api_key = api_key
        else:
            raise Exception("未找到 DashScope API Key")

    def process_natural_language(self, user_input: str) -> str:
        """
        将自然语言描述转换为视频大纲
        
        Args:
            user_input: 用户的自然语言描述
            
        Returns:
            格式化的视频大纲文本
        """
        prompt = f"""
        你是一个专业的视频策划师。用户想要制作一个视频，描述如下：
        
        "{user_input}"
        
        请将用户的描述转换为一个结构化的视频大纲，包含以下要素：
        1. 视频主题和目标
        2. 视频时长
        3. 目标受众
        4. 视频风格
        5. 内容结构（分段描述）
        6. 特效和转场需求
        7. 音频需求（背景音乐、音效）
        8. 字幕和文字需求
        9. 品牌元素（如logo、标语）
        
        请用清晰的中文描述，格式如下：
        这是一个[主题]的[类型]视频，时长[X]秒，面向[受众]，风格[风格描述]。
        
        内容结构：
        - 第1部分（X秒）：[内容描述]，[特效/转场]
        - 第2部分（X秒）：[内容描述]，[特效/转场]
        ...
        
        音频：[背景音乐类型]，[音效需求]
        字幕：[字幕样式和语言]
        品牌：[logo位置和展示方式]
        
        特殊要求：[其他特殊需求]
        """
        
        try:
            response = Generation.call(
                model="qwen-plus",
                prompt=prompt
            )
            
            outline = response.output.text.strip()
            return outline
            
        except Exception as e:
            print(f"处理自然语言时出错: {e}")
            # 返回一个默认大纲
            return self._create_default_outline(user_input)

    def _create_default_outline(self, user_input: str) -> str:
        """创建默认大纲"""
        return f"这是一个基于用户描述的视频，时长60秒，面向大众，风格简洁。用户描述：{user_input}"

    def extract_key_elements(self, outline: str) -> Dict[str, any]:
        """
        从大纲中提取关键元素
        
        Args:
            outline: 视频大纲文本
            
        Returns:
            包含关键元素的字典
        """
        prompt = f"""
        从以下视频大纲中提取关键信息，并以JSON格式返回：
        
        大纲：
        {outline}
        
        请提取并返回以下JSON格式：
        {{
            "title": "视频标题",
            "duration": "时长（秒）",
            "target_audience": "目标受众",
            "style": "视频风格",
            "has_logo": true/false,
            "has_subtitles": true/false,
            "background_music": "音乐类型",
            "main_sections": ["主要内容段落"],
            "effects": ["使用的特效"],
            "transitions": ["转场效果"]
        }}
        """
        
        try:
            response = Generation.call(
                model="qwen-plus",
                prompt=prompt
            )
            
            result = response.output.text
            # 提取JSON部分
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
            
        except Exception as e:
            print(f"提取关键元素时出错: {e}")
        
        return {}

    def enhance_outline_with_details(self, outline: str, style: Optional[str] = None) -> str:
        """
        根据风格增强大纲细节
        
        Args:
            outline: 基础大纲
            style: 视频风格（如：抖音风、专业、温馨等）
            
        Returns:
            增强后的大纲
        """
        if not style:
            return outline
        
        style_prompts = {
            "抖音风": "快节奏、炫酷特效、动感音乐、醒目字幕",
            "专业": "稳重大气、专业配音、简洁转场、品牌展示",
            "温馨": "柔和色调、舒缓音乐、温暖画面、情感共鸣",
            "科技感": "未来感画面、数据可视化、电子音效、蓝色调",
            "教育": "清晰结构、知识点标注、图表说明、专业解说"
        }
        
        style_desc = style_prompts.get(style, style)
        
        enhanced_prompt = f"""
        请根据以下风格要求，增强这个视频大纲：
        
        原始大纲：
        {outline}
        
        风格要求：{style_desc}
        
        请在保持原有内容的基础上，添加更多符合该风格的细节描述，包括：
        - 具体的视觉效果
        - 音效和音乐建议
        - 转场方式
        - 字幕样式
        - 色彩方案
        """
        
        try:
            response = Generation.call(
                model="qwen-plus",
                prompt=enhanced_prompt
            )
            
            return response.output.text.strip()
            
        except Exception as e:
            print(f"增强大纲时出错: {e}")
            return outline


def test_nl_processor():
    """测试自然语言处理器"""
    processor = NLProcessor()
    
    # 测试用例
    test_cases = [
        "我想做一个1分钟的产品介绍视频，展示我们的新款智能手表",
        "制作一个30秒的抖音风格美食探店视频，要有快切和动感音乐",
        "创建一个3分钟的Python教程，讲解列表和字典的使用",
        "做一个温馨的家庭相册视频，配上舒缓的背景音乐"
    ]
    
    for i, test_input in enumerate(test_cases):
        print(f"\n{'='*50}")
        print(f"测试用例 {i+1}: {test_input}")
        print(f"{'='*50}")
        
        # 处理自然语言
        outline = processor.process_natural_language(test_input)
        print(f"\n生成的大纲：\n{outline}")
        
        # 提取关键元素
        elements = processor.extract_key_elements(outline)
        print(f"\n提取的关键元素：\n{json.dumps(elements, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    test_nl_processor()
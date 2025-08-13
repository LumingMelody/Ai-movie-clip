import dashscope
from dashscope import Generation
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.utils.env_config import get_dashscope_api_key

# 初始化 DashScope API Key
dashscope.api_key = get_dashscope_api_key() or os.getenv('DASHSCOPE_API_KEY')

def call_qwen(prompt):

    """
    调用 Qwen 模型生成文案
    :param prompt: 提示词
    :return: 生成结果文本
    """
    try:
        response = Generation.call(
            model="qwen-max",  # 可选：qwen-turbo / qwen-max
            prompt=prompt
        )
        return response.output.text.strip()
    except Exception as e:
        return f"调用失败: {str(e)}"
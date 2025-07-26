import dashscope
from dashscope import Generation
import os

from get_api_key import get_api_key_from_file

# 初始化 DashScope API Key
dashscope.api_key = get_api_key_from_file()

def call_qwen(prompt):
    """
    调用 Qwen 模型生成文案
    :param prompt: 提示词
    :return: 生成结果文本
    """
    try:
        response = Generation.call(
            model="qwen-plus",  # 可选：qwen-turbo / qwen-max
            prompt=prompt
        )
        return response.output.text.strip()
    except Exception as e:
        return f"调用失败: {str(e)}"
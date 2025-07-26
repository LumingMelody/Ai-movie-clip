# -*- coding: utf-8 -*-
"""
重构后的数字人视频生成模块（简易版）
"""

from .base.video_generator import generate_video


def get_video_digital_human_easy_refactored(
    video_input: str,
    topic: str,
    content: str = None,
    audio_input: str = None
) -> str:
    """
    🔥 重构后的数字人视频生成函数
    
    Args:
        video_input: 视频输入路径或URL
        topic: 主题
        content: 内容文本
        audio_input: 音频输入路径或URL
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='digital_human',
        video_input=video_input,
        topic=topic,
        content=content,
        audio_input=audio_input
    )


# 保持向后兼容
def get_video_digital_huamn_easy(video_url, topic, content=None, audio_url=None):
    """原始函数的兼容性包装器"""
    return get_video_digital_human_easy_refactored(video_url, topic, content, audio_url)

def get_video_digital_huamn_easy_local(file_path, topic, content=None, audio_url=None):
    """本地文件处理的兼容性包装器"""
    return get_video_digital_human_easy_refactored(file_path, topic, content, audio_url)


if __name__ == "__main__":
    try:
        result = get_video_digital_human_easy_refactored(
            video_input="test_video.mp4",
            topic="财税知识",
            content="这是一段测试内容"
        )
        print(f"✅ 数字人视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
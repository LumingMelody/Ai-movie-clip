# -*- coding: utf-8 -*-
"""
重构后的大字报视频生成模块
"""

from .base.video_generator import generate_video


def get_video_big_word_refactored(
    text: str,
    font_size: int = 120,
    background_color: str = "black",
    text_color: str = "white"
) -> str:
    """
    🔥 重构后的大字报视频生成函数
    
    Args:
        text: 显示文本
        font_size: 字体大小
        background_color: 背景颜色
        text_color: 文字颜色
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='big_word',
        text=text,
        font_size=font_size,
        background_color=background_color,
        text_color=text_color
    )


# 保持向后兼容
def get_video_big_word(text, font_size=120, background_color="black", text_color="white"):
    """原始函数的兼容性包装器"""
    return get_video_big_word_refactored(text, font_size, background_color, text_color)


if __name__ == "__main__":
    try:
        result = get_video_big_word_refactored(
            text="震撼标题",
            font_size=150,
            background_color="red",
            text_color="yellow"
        )
        print(f"✅ 大字报视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
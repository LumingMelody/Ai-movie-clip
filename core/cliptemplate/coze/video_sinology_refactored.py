# -*- coding: utf-8 -*-
"""
重构后的国学类视频生成模块
"""

from .base.video_generator import generate_video


def get_video_sinology_refactored(
    classic: str,
    interpretation: str,
    background_style: str = "traditional"
) -> str:
    """
    🔥 重构后的国学类视频生成函数
    
    Args:
        classic: 经典内容
        interpretation: 解读内容
        background_style: 背景风格
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='sinology',
        classic=classic,
        interpretation=interpretation,
        background_style=background_style
    )


# 保持向后兼容
def get_video_sinology(classic, interpretation, background_style="traditional"):
    """原始函数的兼容性包装器"""
    return get_video_sinology_refactored(classic, interpretation, background_style)


if __name__ == "__main__":
    try:
        result = get_video_sinology_refactored(
            classic="学而时习之，不亦说乎",
            interpretation="学习了知识要经常复习，这不是很快乐的事情吗",
            background_style="ancient"
        )
        print(f"✅ 国学类视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
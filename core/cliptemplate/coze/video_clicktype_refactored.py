# -*- coding: utf-8 -*-
"""
重构后的点击类视频生成模块
"""

from .base.video_generator import generate_video


def get_video_clicktype_refactored(
    title: str,
    content: str,
    style: str = "default",
    duration: int = 30
) -> str:
    """
    🔥 重构后的点击类视频生成函数
    
    Args:
        title: 标题
        content: 内容
        style: 风格
        duration: 时长
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='clicktype',
        title=title,
        content=content,
        style=style,
        duration=duration
    )


# 保持向后兼容
def get_video_clicktype(title, content, style="default", duration=30):
    """原始函数的兼容性包装器"""
    return get_video_clicktype_refactored(title, content, style, duration)


if __name__ == "__main__":
    try:
        result = get_video_clicktype_refactored(
            title="点击必看",
            content="震惊！这个方法竟然...",
            style="exciting"
        )
        print(f"✅ 点击类视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
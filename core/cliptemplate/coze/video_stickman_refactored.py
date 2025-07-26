# -*- coding: utf-8 -*-
"""
重构后的火柴人视频生成模块
"""

from .base.video_generator import generate_video


def get_video_stickman_refactored(
    story: str,
    animation_style: str = "simple",
    speed: str = "normal"
) -> str:
    """
    🔥 重构后的火柴人视频生成函数
    
    Args:
        story: 故事内容
        animation_style: 动画风格
        speed: 播放速度
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='stickman',
        story=story,
        animation_style=animation_style,
        speed=speed
    )


# 保持向后兼容
def get_video_stickman(story, animation_style="simple", speed="normal"):
    """原始函数的兼容性包装器"""
    return get_video_stickman_refactored(story, animation_style, speed)


if __name__ == "__main__":
    try:
        result = get_video_stickman_refactored(
            story="火柴人的冒险之旅",
            animation_style="dynamic",
            speed="fast"
        )
        print(f"✅ 火柴人视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
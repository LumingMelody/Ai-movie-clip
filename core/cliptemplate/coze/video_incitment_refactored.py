# -*- coding: utf-8 -*-
"""
重构后的煽动类视频生成模块
"""

from .base.video_generator import generate_video


def get_video_incitment_refactored(
    theme: str,
    intensity: str = "medium",
    target_audience: str = "general"
) -> str:
    """
    🔥 重构后的煽动类视频生成函数
    
    Args:
        theme: 主题
        intensity: 强度级别
        target_audience: 目标受众
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='incitement',
        theme=theme,
        intensity=intensity,
        target_audience=target_audience
    )


# 保持向后兼容
def get_video_incitment(theme, intensity="medium", target_audience="general"):
    """原始函数的兼容性包装器"""
    return get_video_incitment_refactored(theme, intensity, target_audience)


if __name__ == "__main__":
    try:
        result = get_video_incitment_refactored(
            theme="运动健身",
            intensity="high",
            target_audience="young_adults"
        )
        print(f"✅ 煽动类视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
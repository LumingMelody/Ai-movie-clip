# -*- coding: utf-8 -*-
"""
重构后的介绍类视频生成模块
"""

from .base.video_generator import generate_video


def get_video_introduction_refactored(
    subject: str,
    details: str,
    style: str = "professional"
) -> str:
    """
    🔥 重构后的介绍类视频生成函数
    
    Args:
        subject: 介绍主体
        details: 详细信息
        style: 风格类型
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='introduction',
        subject=subject,
        details=details,
        style=style
    )


# 保持向后兼容
def get_video_introduction(subject, details, style="professional"):
    """原始函数的兼容性包装器"""
    return get_video_introduction_refactored(subject, details, style)


if __name__ == "__main__":
    try:
        result = get_video_introduction_refactored(
            subject="新产品发布",
            details="这是我们最新推出的革命性产品",
            style="modern"
        )
        print(f"✅ 介绍类视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
# -*- coding: utf-8 -*-
"""
重构后的直播视频生成模块
"""

from .base.video_generator import generate_video


def get_video_generate_live_refactored(
    live_content: str,
    host_style: str = "professional",
    interaction_level: str = "medium"
) -> str:
    """
    🔥 重构后的直播视频生成函数
    
    Args:
        live_content: 直播内容
        host_style: 主播风格
        interaction_level: 互动级别
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='live',
        live_content=live_content,
        host_style=host_style,
        interaction_level=interaction_level
    )


# 保持向后兼容
def get_video_generate_live(live_content, host_style="professional", interaction_level="medium"):
    """原始函数的兼容性包装器"""
    return get_video_generate_live_refactored(live_content, host_style, interaction_level)


if __name__ == "__main__":
    try:
        result = get_video_generate_live_refactored(
            live_content="今天我们来聊聊最新的科技趋势",
            host_style="casual",
            interaction_level="high"
        )
        print(f"✅ 直播视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
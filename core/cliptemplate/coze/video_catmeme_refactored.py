# -*- coding: utf-8 -*-
"""
重构后的猫咪表情包视频生成模块
"""

from .base.video_generator import generate_video


def get_video_catmeme_refactored(
    dialogue: str,
    cat_type: str = "default",
    emotion: str = "happy"
) -> str:
    """
    🔥 重构后的猫咪表情包视频生成函数
    
    Args:
        dialogue: 对话内容
        cat_type: 猫咪类型
        emotion: 情感类型
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='catmeme',
        dialogue=dialogue,
        cat_type=cat_type,
        emotion=emotion
    )


# 保持向后兼容
def get_video_catmeme(dialogue, cat_type="default", emotion="happy"):
    """原始函数的兼容性包装器"""
    return get_video_catmeme_refactored(dialogue, cat_type, emotion)


if __name__ == "__main__":
    try:
        result = get_video_catmeme_refactored(
            dialogue="主人，我饿了~",
            cat_type="orange",
            emotion="sad"
        )
        print(f"✅ 猫咪表情包视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
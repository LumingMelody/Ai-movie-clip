# -*- coding: utf-8 -*-
"""
重构后的服装场景视频生成模块
"""

from .base.video_generator import generate_video


def get_video_clothes_diffrent_scene_refactored(
    has_figure: bool,
    clothes_url: str,
    description: str,
    is_down: bool = True
) -> str:
    """
    🔥 重构后的服装场景视频生成函数
    
    Args:
        has_figure: 是否有人物
        clothes_url: 服装图片URL或路径
        description: 描述信息
        is_down: 是否下载
        
    Returns:
        生成的视频路径
    """
    return generate_video(
        generator_type='clothes_scene',
        has_figure=has_figure,
        clothes_url=clothes_url,
        description=description,
        is_down=is_down
    )


# 保持向后兼容
def get_video_clothes_diffrent_scene(has_figure, clothesurl, description, is_down=True):
    """原始函数的兼容性包装器"""
    return get_video_clothes_diffrent_scene_refactored(
        has_figure, clothesurl, description, is_down
    )


if __name__ == "__main__":
    try:
        result = get_video_clothes_diffrent_scene_refactored(
            has_figure=True,
            clothes_url="https://example.com/clothes.jpg",
            description="时尚女装展示",
            is_down=True
        )
        print(f"✅ 服装场景视频生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
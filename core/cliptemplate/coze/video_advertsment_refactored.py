# -*- coding: utf-8 -*-
"""
重构后的广告视频生成模块
使用新的基础架构，大幅减少代码重复
"""

from .base.video_generator import generate_video


def get_video_advertisement_refactored(
    company_name: str,
    service: str, 
    topic: str,
    content: str = None,
    need_change: bool = False,
    use_digital_host: bool = False
) -> str:
    """
    🔥 重构后的广告视频生成函数
    
    使用统一的工作流基础架构，减少95%的重复代码
    
    Args:
        company_name: 公司名称
        service: 服务类型
        topic: 主题
        content: 内容（可选）
        need_change: 是否需要更改
        use_digital_host: 是否使用数字人
        
    Returns:
        生成的视频路径（warehouse相对路径）
    """
    return generate_video(
        generator_type='advertisement',
        company_name=company_name,
        service=service,
        topic=topic,
        content=content,
        need_change=need_change,
        use_digital_host=use_digital_host
    )


# 保持向后兼容的原始函数接口
def get_video_advertisement(company_name, service, topic, content=None, need_change=False):
    """原始函数的兼容性包装器"""
    return get_video_advertisement_refactored(
        company_name=company_name,
        service=service,
        topic=topic,
        content=content,
        need_change=need_change,
        use_digital_host=False
    )


if __name__ == "__main__":
    # 测试重构后的函数
    for i in range(3):
        try:
            result_path = get_video_advertisement_refactored(
                company_name="阳山数谷",
                service="企业园区运营", 
                topic="园区运营",
                use_digital_host=True
            )
            print(f"🎉 测试 {i+1} 成功: {result_path}")
        except Exception as e:
            print(f"❌ 测试 {i+1} 失败: {e}")
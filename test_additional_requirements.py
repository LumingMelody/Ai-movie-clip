#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试额外参数处理功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text_generate.generator import get_copy_generation


def test_basic_template():
    """测试基础模板生成（无额外参数）"""
    print("="*60)
    print("测试1: 基础模板生成（无额外参数）")
    print("="*60)

    params = {
        "商品名称": "重庆火锅",
        "商品亮点": "新鲜毛肚",
        "适用人群": "美食爱好者"
    }

    result = get_copy_generation(
        category="ecom",
        style="knowledge",
        input_data=params,
        use_template=True,
        ai_enhance=False
    )

    print(f"\n生成结果:")
    print(f"{result}")
    print(f"\n字数: {len(result)}")


def test_with_extra_params():
    """测试带额外参数的模板生成"""
    print("\n" + "="*60)
    print("测试2: 带额外参数的模板生成")
    print("="*60)

    params = {
        # 模板参数
        "商品名称": "重庆火锅",
        "商品亮点": "新鲜毛肚、特色底料",
        "适用人群": "美食爱好者",

        # 额外参数
        "店位置": "天灵路25号",
        "活动主题": "199元单人畅享",
        "活动内容": "火锅自助，畅大胃囊",
        "营业时间": "10:00-22:00",
        "配送方式": "外卖+堂食",
        "联系电话": "138-1234-5678"
    }

    result = get_copy_generation(
        category="ecom",
        style="knowledge",
        input_data=params,
        use_template=True,
        ai_enhance=False
    )

    print(f"\n生成结果:")
    print(f"{result}")
    print(f"\n字数: {len(result)}")


def test_with_ai_enhance():
    """测试AI增强功能（带额外参数）"""
    print("\n" + "="*60)
    print("测试3: AI增强功能（带额外参数）")
    print("="*60)

    params = {
        # 模板参数
        "商品名称": "重庆火锅",
        "商品亮点": "新鲜毛肚、特色底料",
        "适用人群": "美食爱好者",

        # 额外参数
        "店位置": "苏州天灵路25号",
        "活动主���": "限时特惠",
        "活动内容": "199元单人畅享火锅自助",
        "视频时长": "30"
    }

    result = get_copy_generation(
        category="ecom",
        style="knowledge",
        input_data=params,
        use_template=True,
        ai_enhance=True
    )

    print(f"\n生成结果:")
    print(f"{result}")
    print(f"\n字数: {len(result)}")


def test_different_category():
    """测试不同类别的模板"""
    print("\n" + "="*60)
    print("测试4: 不同类别模板（activity类别）")
    print("="*60)

    params = {
        # 模板参数
        "店名称": "重庆火锅",
        "所在城市": "苏州",
        "店位置": "天灵路25号",
        "主营产品": "毛肚、鸭肠",
        "活动主题": "开业大酬宾",
        "活动内容": "全场8折优惠",
        "视频时长": "15",

        # 额外参数
        "营业时间": "10:00-22:00",
        "停车信息": "免费停车位充足",
        "优惠券": "满200减50"
    }

    result = get_copy_generation(
        category="activity",
        style="knowledge",
        input_data=params,
        use_template=True,
        ai_enhance=False
    )

    print(f"\n生成结果:")
    print(f"{result}")
    print(f"\n字数: {len(result)}")


if __name__ == "__main__":
    try:
        print("\n🚀 开始测试额外参数处理功能\n")

        # 测试1: 基础模板生成
        test_basic_template()

        # 测试2: 带额外参数
        test_with_extra_params()

        # 测试3: AI增强（如果配置了API密钥）
        # test_with_ai_enhance()

        # 测试4: 不同类别
        test_different_category()

        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

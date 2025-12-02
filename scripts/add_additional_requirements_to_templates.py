#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修改模板文件，添加额外需求区块
"""

import os
import sys


def add_additional_requirements_block(template_path):
    """
    在模板文件末尾添��额外需求区块

    Args:
        template_path: 模板文件路径
    """
    try:
        # 读取原始内容
        with open(template_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 检查是否已经有额外需求区块
        if 'additional_requirements' in original_content:
            print(f"⏭️  跳过 {template_path} (已包含额外需求区块)")
            return False

        # 添加额外需求区块
        additional_block = """

{% if additional_requirements %}

{{ additional_requirements }}
{% endif %}"""

        new_content = original_content.rstrip() + additional_block

        # 写回文件
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ 已修改 {template_path}")
        return True

    except Exception as e:
        print(f"❌ 修改失败 {template_path}: {e}")
        return False


def batch_modify_templates(templates_dir):
    """
    批量修改所有模板文件

    Args:
        templates_dir: 模板根目录
    """
    modified_count = 0
    skipped_count = 0
    failed_count = 0

    print(f"🚀 开始批量修改模板文件...")
    print(f"📁 模板目录: {templates_dir}\n")

    # 遍历所有.j2文件
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.j2'):
                template_path = os.path.join(root, file)
                result = add_additional_requirements_block(template_path)

                if result is True:
                    modified_count += 1
                elif result is False:
                    skipped_count += 1
                else:
                    failed_count += 1

    print(f"\n" + "="*60)
    print(f"📊 批量修改完成:")
    print(f"   ✅ 成功修改: {modified_count} 个文件")
    print(f"   ⏭️  跳过: {skipped_count} 个文件")
    print(f"   ❌ 失败: {failed_count} 个文件")
    print("="*60)


if __name__ == "__main__":
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    templates_dir = os.path.join(project_root, "templates")

    if not os.path.exists(templates_dir):
        print(f"❌ 模板目录不存在: {templates_dir}")
        sys.exit(1)

    batch_modify_templates(templates_dir)

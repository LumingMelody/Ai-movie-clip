#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试标签视频生成器的per-tag duration功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_cut.tag_video_generator.tag_video_generator import TagVideoGenerator

def test_per_tag_duration():
    """测试每个标签单独设置时长"""
    
    generator = TagVideoGenerator(tag_materials_dir="tag_materials")
    
    # 测试配置 - 每个标签不同的时长
    test_config = {
        "黄山风景": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "徽州特色餐": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "屯溪老街": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        }
    }
    
    # 测试1: 统一时长（原有功能）
    print("测试1: 所有标签使用统一时长 5秒")
    output_path1 = "/tmp/test_uniform_duration.mp4"
    try:
        generator.generate_video_from_tags(
            tag_config=test_config,
            output_path=output_path1,
            duration_per_tag=5.0,  # 统一5秒
            clip_duration_range=(2.0, 4.0)
        )
        print(f"✅ 统一时长测试成功: {output_path1}")
    except Exception as e:
        print(f"❌ 统一时长测试失败: {e}")
    
    # 测试2: 每个标签单独设置时长
    print("\n测试2: 每个标签单独设置时长")
    output_path2 = "/tmp/test_per_tag_duration.mp4"
    per_tag_durations = {
        "黄山风景": 5.0,      # 5秒
        "徽州特色餐": 10.0,   # 10秒
        "屯溪老街": 3.0       # 3秒
    }
    
    try:
        generator.generate_video_from_tags(
            tag_config=test_config,
            output_path=output_path2,
            duration_per_tag=per_tag_durations,  # 字典形式的时长设置
            clip_duration_range=(2.0, 4.0)
        )
        print(f"✅ 分别设置时长测试成功: {output_path2}")
        print(f"   预期总时长: {sum(per_tag_durations.values())}秒")
    except Exception as e:
        print(f"❌ 分别设置时长测试失败: {e}")
    
    # 测试3: 部分标签有自定义时长，其他使用默认值
    print("\n测试3: 部分标签自定义时长")
    output_path3 = "/tmp/test_partial_duration.mp4"
    partial_durations = {
        "黄山风景": 8.0,      # 自定义8秒
        # "徽州特色餐" 将使用默认的5秒
        "屯溪老街": 2.0       # 自定义2秒
    }
    
    try:
        generator.generate_video_from_tags(
            tag_config=test_config,
            output_path=output_path3,
            duration_per_tag=partial_durations,
            clip_duration_range=(1.0, 3.0)
        )
        print(f"✅ 部分自定义时长测试成功: {output_path3}")
    except Exception as e:
        print(f"❌ 部分自定义时长测试失败: {e}")

if __name__ == "__main__":
    test_per_tag_duration()
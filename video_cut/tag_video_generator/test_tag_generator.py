#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试标签视频生成器
"""

import json
from tag_video_generator import TagVideoGenerator
from api_handler import TagVideoAPIHandler


def test_basic_generation():
    """测试基础视频生成"""
    print("=" * 50)
    print("测试基础视频生成")
    print("=" * 50)
    
    generator = TagVideoGenerator()
    
    # 测试配置 - 使用相同的视频文件模拟不同景点
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
    
    try:
        output_path = "/tmp/test_tag_video_basic.mp4"
        result = generator.generate_video_from_tags(
            tag_config=test_config,
            output_path=output_path,
            duration_per_tag=2.0,  # 每个标签2秒
            clip_duration_range=(0.5, 1.0),  # 片段长度0.5-1秒
            text_content="探索黄山美景，品味徽州美食，漫步千年古街。"
        )
        print(f"✅ 基础测试成功: {result}")
    except Exception as e:
        print(f"❌ 基础测试失败: {e}")


def test_api_handler():
    """测试API处理器"""
    print("\n" + "=" * 50)
    print("测试API处理器")
    print("=" * 50)
    
    handler = TagVideoAPIHandler()
    
    # 模拟前端请求
    request = {
        "tags": ["黄山风景", "徽州特色餐", "屯溪老街", "无边泳池", "峡谷漂流"],
        "tag_videos": {
            "黄山风景": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "徽州特色餐": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "屯溪老街": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "无边泳池": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "峡谷漂流": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            }
        },
        "duration_per_tag": 2.0,
        "dynamic_tags": ["黄山", "美食", "古街", "泳池", "漂流"],
        "subtitle_config": {
            "font_size": 56,
            "color": "yellow",
            "position": ("center", "bottom"),
            "margin": 80
        }
    }
    
    try:
        result = handler.handle_request(request)
        print(f"API处理结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result['success']:
            print(f"✅ API测试成功")
        else:
            print(f"❌ API测试失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ API测试异常: {e}")


def test_ai_text_generation():
    """测试AI文案生成"""
    print("\n" + "=" * 50)
    print("测试AI文案生成")
    print("=" * 50)
    
    generator = TagVideoGenerator()
    
    # 测试标签
    tags = ["黄山风景", "徽州特色餐", "屯溪老街", "无边泳池", "峡谷漂流"]
    
    try:
        text = generator._generate_text_content(tags)
        print(f"生成的文案: {text}")
        print(f"✅ AI文案生成测试成功")
    except Exception as e:
        print(f"❌ AI文案生成测试失败: {e}")


def test_random_extraction():
    """测试随机片段提取"""
    print("\n" + "=" * 50)
    print("测试随机片段提取")
    print("=" * 50)
    
    generator = TagVideoGenerator()
    
    # 测试配置
    test_config = {
        "测试标签1": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "测试标签2": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        }
    }
    
    try:
        clips = generator._extract_clips_by_tags(
            tag_config=test_config,
            duration_per_tag=3.0,
            clip_duration_range=(0.5, 1.5)
        )
        
        total_duration = sum(clip.duration for clip in clips)
        print(f"提取了 {len(clips)} 个片段组")
        print(f"总时长: {total_duration:.2f} 秒")
        print(f"✅ 随机提取测试成功")
    except Exception as e:
        print(f"❌ 随机提取测试失败: {e}")


if __name__ == "__main__":
    print("开始测试标签视频生成器")
    print("=" * 50)
    
    # 运行所有测试
    test_basic_generation()
    test_api_handler()
    test_ai_text_generation()
    test_random_extraction()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
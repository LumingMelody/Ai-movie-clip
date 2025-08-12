#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试九宫格字幕位置功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_cut.tag_video_generator.tag_video_generator import TagVideoGenerator

def test_grid_subtitle_positions():
    """测试不同的九宫格字幕位置"""
    
    generator = TagVideoGenerator(tag_materials_dir="tag_materials")
    
    # 测试配置
    test_config = {
        "黄山风景": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "徽州特色餐": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        }
    }
    
    # 测试不同的九宫格位置
    positions = {
        1: "左上角",
        2: "顶部中间", 
        3: "右上角",
        4: "左侧中间",
        5: "正中心",
        6: "右侧中间",
        7: "左下角",
        8: "底部中间（默认）",
        9: "右下角"
    }
    
    # 测试位置 1, 5, 8, 9
    test_positions = [1, 5, 8, 9]
    
    for pos in test_positions:
        print(f"\n测试九宫格位置 {pos}: {positions[pos]}")
        
        # 配置字幕位置
        subtitle_config = {
            'font_size': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'grid_position': pos  # 设置九宫格位置
        }
        
        output_path = f"/tmp/test_grid_pos_{pos}.mp4"
        
        try:
            generator.generate_video_from_tags(
                tag_config=test_config,
                output_path=output_path,
                duration_per_tag=5.0,
                text_content=f"测试字幕位置：{positions[pos]}",
                subtitle_config=subtitle_config,
                clip_duration_range=(2.0, 4.0)
            )
            print(f"✅ 位置 {pos} 测试成功: {output_path}")
        except Exception as e:
            print(f"❌ 位置 {pos} 测试失败: {e}")

def test_api_request():
    """测试API请求格式"""
    
    # 示例API请求体
    request_example = {
        "tags": ["黄山风景", "徽州特色餐", "屯溪老街"],
        "tag_videos": {
            "黄山风景": {
                "video": ["https://example.com/video1.mp4"]
            },
            "徽州特色餐": {
                "video": ["https://example.com/video2.mp4"]
            },
            "屯溪老街": {
                "video": ["https://example.com/video3.mp4"]
            }
        },
        "text_content": "探索黄山美景，品味徽州美食",
        "subtitle_config": {
            "font_size": 48,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 2,
            "grid_position": 3  # 右上角
        },
        "duration_per_tag": {
            "黄山风景": 10.0,
            "徽州特色餐": 8.0,
            "屯溪老街": 6.0
        }
    }
    
    print("\n=== API请求示例 ===")
    print("九宫格字幕位置说明：")
    print("1 | 2 | 3")
    print("---------")
    print("4 | 5 | 6")
    print("---------")
    print("7 | 8 | 9")
    print("\n在subtitle_config中设置grid_position (1-9)即可")
    print("\n示例请求体：")
    import json
    print(json.dumps(request_example, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试九宫格字幕位置")
    parser.add_argument("--test", choices=["position", "api", "all"], 
                       default="api", help="选择测试类型")
    
    args = parser.parse_args()
    
    if args.test == "position":
        test_grid_subtitle_positions()
    elif args.test == "api":
        test_api_request()
    else:
        test_grid_subtitle_positions()
        test_api_request()
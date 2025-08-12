#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试阿里云字幕API集成功能
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.clipgenerate.aliyun_subtitle_api import AliyunSubtitleAPI, SubtitleConfig, create_grid_subtitle_example
from video_cut.tag_video_generator.tag_video_generator import TagVideoGenerator

def test_aliyun_subtitle_api():
    """测试阿里云字幕API基础功能"""
    print("=== 测试阿里云字幕API基础功能 ===")
    
    api = AliyunSubtitleAPI()
    
    # 测试九宫格位置转换
    print("\n九宫格位置映射测试:")
    for i in range(1, 10):
        position = api.grid_to_aliyun_position(i)
        print(f"位置 {i}: x={position['x']}, y={position['y']}, alignment={position['alignment']}")
    
    # 测试文本分割
    print("\n文本分割测试:")
    text = "探秘黄山云海奇观，品味徽州地道美食；漫步屯溪老街古韵，畅游无边泳池美景；体验峡谷漂流刺激，尽享旅程无限乐趣。"
    subtitles = api.split_text_for_subtitles(text, video_duration=30.0)
    
    for i, subtitle in enumerate(subtitles):
        print(f"字幕 {i+1}: '{subtitle.content}' ({subtitle.timeline_in:.1f}s - {subtitle.timeline_out:.1f}s)")
    
    # 测试字幕配置验证
    print("\n字幕配置验证测试:")
    valid_subtitle = SubtitleConfig(
        content="测试字幕",
        timeline_in=0.0,
        timeline_out=5.0,
        grid_position=5,
        font_size=48
    )
    
    errors = api.validate_subtitle_config(valid_subtitle)
    print(f"有效配置验证结果: {len(errors)} 个错误")
    
    invalid_subtitle = SubtitleConfig(
        content="",  # 空内容
        timeline_in=5.0,
        timeline_out=2.0,  # 时间错误
        grid_position=10,  # 无效位置
        font_size=0  # 无效字体大小
    )
    
    errors = api.validate_subtitle_config(invalid_subtitle)
    print(f"无效配置验证结果: {len(errors)} 个错误:")
    for error in errors:
        print(f"  - {error}")

def test_tag_video_generator_with_aliyun():
    """测试TagVideoGenerator集成阿里云字幕"""
    print("\n=== 测试TagVideoGenerator集成阿里云字幕 ===")
    
    # 使用阿里云字幕的生成器
    generator = TagVideoGenerator(use_aliyun_subtitle=True)
    
    test_config = {
        "黄山风景": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "徽州特色餐": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        }
    }
    
    # 测试不同九宫格位置
    test_positions = [1, 3, 5, 7, 9]  # 四角和中心
    
    for pos in test_positions:
        print(f"\n测试九宫格位置 {pos}")
        
        subtitle_config = {
            'grid_position': pos,
            'font_size': 48,
            'color': '#FFFFFF',
            'stroke_color': '#000000',
            'stroke_width': 2,
            'max_chars_per_subtitle': 15,
            'min_display_time': 2.0
        }
        
        try:
            # 不实际生成视频，只测试字幕配置生成
            from moviepy import VideoFileClip
            
            # 创建一个虚拟视频来测试字幕
            test_video = VideoFileClip("/Users/luming/Downloads/老登.mp4").subclipped(0, 10)
            test_text = f"测试九宫格位置{pos}的字幕效果"
            
            # 调用阿里云字幕生成
            subtitle_json = generator._create_aliyun_subtitles(test_video, test_text, subtitle_config)
            
            if subtitle_json:
                print(f"✅ 位置 {pos} 字幕配置生成成功")
                
                # 解析生成的配置
                timeline = json.loads(subtitle_json)
                clips = timeline.get("SubtitleTracks", [{}])[0].get("SubtitleTrackClips", [])
                print(f"   生成了 {len(clips)} 个字幕片段")
                
                if clips:
                    first_clip = clips[0]
                    print(f"   第一个字幕: '{first_clip['Content']}'")
                    print(f"   位置: x={first_clip['X']}, y={first_clip['Y']}")
                    print(f"   对齐: {first_clip['Alignment']}")
            else:
                print(f"❌ 位置 {pos} 字幕配置生成失败")
                
            test_video.close()
            
        except Exception as e:
            print(f"❌ 位置 {pos} 测试失败: {e}")

def test_full_api_workflow():
    """测试完整的API工作流程"""
    print("\n=== 测试完整API工作流程 ===")
    
    api = AliyunSubtitleAPI()
    
    # 1. 创建字幕配置
    subtitles = [
        SubtitleConfig(
            content="欢迎观看我们的视频",
            timeline_in=0.0,
            timeline_out=3.0,
            grid_position=2,  # 顶部中间
            font_size=52,
            font_color="#FFFF00"  # 黄色
        ),
        SubtitleConfig(
            content="请关注我们获取更多内容",
            timeline_in=3.0,
            timeline_out=6.0,
            grid_position=8,  # 底部中间
            font_size=48,
            font_color="#FFFFFF"
        ),
        SubtitleConfig(
            content="谢谢观看！",
            timeline_in=6.0,
            timeline_out=9.0,
            grid_position=5,  # 中心
            font_size=56,
            font_color="#FF0000"  # 红色
        )
    ]
    
    # 2. 创建字幕时间轴
    timeline = api.create_subtitle_timeline(subtitles)
    
    print("生成的阿里云字幕时间轴:")
    print(json.dumps(timeline, ensure_ascii=False, indent=2))
    
    # 3. 创建完整制作时间轴
    production_timeline = api.create_production_timeline(
        video_url="https://example.com/test-video.mp4",
        subtitles=subtitles
    )
    
    print(f"\n完整制作时间轴包含:")
    print(f"- 视频轨道片段: {len(production_timeline['VideoTracks'][0]['VideoTrackClips'])}")
    print(f"- 字幕轨道片段: {len(production_timeline['SubtitleTracks'][0]['SubtitleTrackClips'])}")
    
    # 4. 保存配置到文件
    output_file = "output/test_aliyun_timeline.json"
    os.makedirs("output", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(production_timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整时间轴已保存到: {output_file}")

def main():
    """主测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试阿里云字幕API功能")
    parser.add_argument("--test", choices=["api", "generator", "workflow", "all"], 
                       default="all", help="选择测试类型")
    
    args = parser.parse_args()
    
    print("🎬 阿里云字幕API测试")
    print("="*50)
    
    if args.test in ["api", "all"]:
        test_aliyun_subtitle_api()
    
    if args.test in ["generator", "all"]:
        test_tag_video_generator_with_aliyun()
    
    if args.test in ["workflow", "all"]:
        test_full_api_workflow()
    
    print("\n✅ 测试完成!")
    print("\n📝 使用说明:")
    print("1. 阿里云字幕API已集成到TagVideoGenerator中")
    print("2. 在subtitle_config中设置grid_position (1-9)选择字幕位置")
    print("3. 生成的字幕配置保存在output/aliyun_subtitles/目录")
    print("4. 实际字幕制作需要调用阿里云的制作API")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
自然语言时间轴生成演示
展示如何通过自然语言描述生成视频编辑时间轴
"""
import json
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from video_cut.natural_language_processor import NaturalLanguageProcessor


def print_timeline_summary(timeline: dict):
    """打印时间轴摘要信息"""
    print("\n📊 时间轴摘要:")
    print(f"  • 标题: {timeline['metadata']['title']}")
    print(f"  • 时长: {timeline['timeline']['duration']}秒")
    print(f"  • 帧率: {timeline['timeline']['fps']}fps")
    print(f"  • 分辨率: {timeline['timeline']['resolution']['width']}x{timeline['timeline']['resolution']['height']}")
    
    # 统计轨道
    track_counts = {}
    for track in timeline['timeline']['tracks']:
        track_type = track['type']
        track_counts[track_type] = track_counts.get(track_type, 0) + 1
    
    print("\n📌 轨道信息:")
    for track_type, count in track_counts.items():
        print(f"  • {track_type}轨道: {count}个")
    
    # 统计效果
    all_effects = []
    for track in timeline['timeline']['tracks']:
        for clip in track.get('clips', []):
            all_effects.extend(clip.get('filters', []))
    
    if all_effects:
        unique_effects = list(set(all_effects))
        print(f"\n✨ 使用的特效: {', '.join(unique_effects)}")


def demo1_simple_edit():
    """演示1: 简单的视频编辑"""
    print("\n" + "="*60)
    print("📹 演示1: 简单视频编辑")
    print("="*60)
    
    user_input = "我要给这个视频加上转场特效和字幕"
    print(f"\n💬 用户输入: {user_input}")
    
    processor = NaturalLanguageProcessor()
    timeline = processor.process_natural_language(user_input)
    
    print_timeline_summary(timeline)
    
    # 保存结果
    output_dir = Path("output/demos")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "demo1_simple.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'demo1_simple.json'}")


def demo2_detailed_edit():
    """演示2: 详细的视频编辑描述"""
    print("\n" + "="*60)
    print("🎬 演示2: 详细视频编辑")
    print("="*60)
    
    user_input = """
    制作一个45秒的产品介绍视频：
    0-5秒：公司logo淡入，背景音乐开始
    5-15秒：产品外观展示，360度旋转效果
    15-30秒：功能演示，每个功能配字幕说明
    30-40秒：用户好评展示，使用发光特效
    40-45秒：购买信息和二维码，淡出结束
    整体使用科技感的蓝色主题，快节奏剪辑
    """
    
    print(f"\n💬 用户输入: {user_input}")
    
    processor = NaturalLanguageProcessor()
    timeline = processor.process_natural_language(user_input)
    
    print_timeline_summary(timeline)
    
    # 详细展示片段信息
    print("\n📋 详细片段信息:")
    for i, track in enumerate(timeline['timeline']['tracks']):
        print(f"\n  轨道{i+1} - {track['name']} ({track['type']}):")
        for j, clip in enumerate(track['clips'][:3]):  # 只显示前3个片段
            print(f"    片段{j+1}: {clip['start']}-{clip['end']}秒")
            if 'content' in clip and 'text' in clip['content']:
                print(f"      文字: {clip['content']['text'][:30]}...")
            if clip.get('filters'):
                print(f"      特效: {', '.join(clip['filters'])}")
    
    # 保存结果
    output_dir = Path("output/demos")
    with open(output_dir / "demo2_detailed.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'demo2_detailed.json'}")


def demo3_educational_video():
    """演示3: 教育视频制作"""
    print("\n" + "="*60)
    print("📚 演示3: 教育视频制作")
    print("="*60)
    
    user_input = """
    制作2分钟的Python编程入门教程：
    0-15秒：课程介绍，显示"Python基础教程"标题
    15-45秒：什么是Python，展示Python logo和特点
    45-75秒：安装Python环境，分步骤展示，配字幕
    75-105秒：第一个程序Hello World，代码高亮显示
    105-120秒：课程总结和下节预告
    使用绿色护眼主题，平缓的节奏，轻松的背景音乐
    """
    
    print(f"\n💬 用户输入: {user_input}")
    
    processor = NaturalLanguageProcessor()
    timeline = processor.process_natural_language(user_input)
    
    print_timeline_summary(timeline)
    
    # 保存结果
    output_dir = Path("output/demos")
    with open(output_dir / "demo3_education.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'demo3_education.json'}")


def demo4_social_media():
    """演示4: 社交媒体短视频"""
    print("\n" + "="*60)
    print("📱 演示4: 抖音风格短视频")
    print("="*60)
    
    user_input = """
    制作15秒的美食探店视频：
    0-2秒：店铺外观，快速缩放效果吸引眼球
    2-8秒：特色菜品展示，每个菜品1-2秒快切
    8-12秒：试吃反应，加表情特效和字幕
    12-15秒：店铺信息和位置，号召关注
    使用暖色调，动感音乐，快节奏剪辑，加粒子特效
    """
    
    print(f"\n💬 用户输入: {user_input}")
    
    processor = NaturalLanguageProcessor()
    timeline = processor.process_natural_language(user_input)
    
    print_timeline_summary(timeline)
    
    # 分析节奏
    video_clips = [c for t in timeline['timeline']['tracks'] 
                   if t['type'] == 'video' for c in t['clips']]
    if video_clips:
        avg_clip_duration = sum(c['end'] - c['start'] for c in video_clips) / len(video_clips)
        print(f"\n⚡ 节奏分析: 平均片段时长 {avg_clip_duration:.1f}秒")
    
    # 保存结果
    output_dir = Path("output/demos")
    with open(output_dir / "demo4_social.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'demo4_social.json'}")


def demo5_complex_effects():
    """演示5: 复杂特效组合"""
    print("\n" + "="*60)
    print("🎨 演示5: 复杂特效组合")
    print("="*60)
    
    user_input = """
    制作30秒的游戏宣传片：
    开头5秒logo展示，使用发光和粒子特效
    5-10秒游戏画面，加震动和故障效果营造紧张感
    10-20秒精彩战斗场面，快速剪辑配合音效
    20-25秒角色展示，慢动作加模糊背景
    最后5秒游戏信息，炫酷的文字动画
    整体使用暗色调配合霓虹色彩，节奏感强烈
    """
    
    print(f"\n💬 用户输入: {user_input}")
    
    processor = NaturalLanguageProcessor()
    timeline = processor.process_natural_language(user_input)
    
    print_timeline_summary(timeline)
    
    # 统计特效使用
    effect_count = {}
    for track in timeline['timeline']['tracks']:
        for clip in track.get('clips', []):
            for effect in clip.get('filters', []):
                effect_count[effect] = effect_count.get(effect, 0) + 1
    
    if effect_count:
        print("\n🎯 特效使用统计:")
        for effect, count in sorted(effect_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {effect}: {count}次")
    
    # 保存结果
    output_dir = Path("output/demos")
    with open(output_dir / "demo5_effects.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'demo5_effects.json'}")


def interactive_mode():
    """交互模式"""
    print("\n" + "="*60)
    print("🎭 交互模式 - 自然语言视频编辑")
    print("="*60)
    print("\n输入您的视频编辑需求，我会生成对应的时间轴。")
    print("提示：可以描述视频类型、时长、特效、字幕等需求。")
    print("输入 'quit' 或 '退出' 结束程序。\n")
    
    processor = NaturalLanguageProcessor()
    output_dir = Path("output/demos/interactive")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    session_count = 0
    
    while True:
        try:
            user_input = input("🎬 请输入您的需求: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 感谢使用！再见！")
                break
            
            if not user_input:
                continue
            
            # 处理输入
            print("\n⏳ 正在处理...")
            timeline = processor.process_natural_language(user_input)
            
            # 显示结果
            print_timeline_summary(timeline)
            
            # 保存
            session_count += 1
            filename = f"session_{session_count}.json"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(timeline, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 时间轴已保存到: {filepath}")
            print("\n" + "-"*60)
            
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断！")
            break
        except Exception as e:
            print(f"\n❌ 处理出错: {e}")
            print("请重试或调整您的描述。\n")


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="自然语言时间轴生成演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python demo_nl_timeline.py --demo all      # 运行所有演示
  python demo_nl_timeline.py --demo 1        # 运行演示1
  python demo_nl_timeline.py --interactive   # 进入交互模式
        """
    )
    
    parser.add_argument("--demo", choices=["1", "2", "3", "4", "5", "all"],
                       help="选择要运行的演示")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="进入交互模式")
    
    args = parser.parse_args()
    
    print("\n🎬 自然语言视频时间轴生成系统")
    print("   通过描述您的需求，自动生成视频编辑时间轴")
    
    if args.interactive:
        interactive_mode()
    elif args.demo == "1":
        demo1_simple_edit()
    elif args.demo == "2":
        demo2_detailed_edit()
    elif args.demo == "3":
        demo3_educational_video()
    elif args.demo == "4":
        demo4_social_media()
    elif args.demo == "5":
        demo5_complex_effects()
    elif args.demo == "all":
        demo1_simple_edit()
        demo2_detailed_edit()
        demo3_educational_video()
        demo4_social_media()
        demo5_complex_effects()
        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("💡 提示：使用 --interactive 进入交互模式")
    else:
        # 默认进入交互模式
        interactive_mode()


if __name__ == "__main__":
    main()
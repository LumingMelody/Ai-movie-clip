"""
自然语言视频编辑测试脚本
演示如何通过自然语言描述生成视频时间轴
"""
import json
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from video_cut.natural_language_processor import NaturalLanguageProcessor


def test_simple_video_edit():
    """测试简单的视频编辑描述"""
    print("=== 测试1: 简单视频编辑 ===")
    
    processor = NaturalLanguageProcessor()
    
    # 用户输入的自然语言描述
    user_input = "我要给这个视频加上转场特效和字幕"
    
    print(f"用户输入: {user_input}")
    
    # 处理自然语言
    timeline = processor.process_natural_language(user_input)
    
    # 输出生成的时间轴
    print("\n生成的时间轴:")
    print(json.dumps(timeline, ensure_ascii=False, indent=2))
    
    # 保存到文件
    output_dir = Path("output/nl_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "simple_edit.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'simple_edit.json'}")


def test_complex_video_edit():
    """测试复杂的视频编辑描述"""
    print("\n=== 测试2: 复杂视频编辑 ===")
    
    processor = NaturalLanguageProcessor()
    
    # 更复杂的描述
    user_input = """
    制作一个30秒的产品宣传视频：
    前5秒展示公司logo，使用淡入效果
    5-20秒介绍产品功能，加字幕说明
    20-25秒展示用户评价，使用发光特效
    最后5秒显示购买信息，配背景音乐，淡出结束
    整体使用蓝色主题，快节奏剪辑
    """
    
    print(f"用户输入: {user_input}")
    
    # 处理自然语言
    timeline = processor.process_natural_language(user_input)
    
    print("\n生成的时间轴摘要:")
    print(f"- 总时长: {timeline['timeline']['duration']}秒")
    print(f"- 轨道数: {len(timeline['timeline']['tracks'])}")
    print(f"- 背景色: {timeline['timeline']['background_color']}")
    
    # 输出轨道信息
    print("\n轨道详情:")
    for i, track in enumerate(timeline['timeline']['tracks']):
        print(f"  {i+1}. {track['name']} ({track['type']}轨道)")
        print(f"     - 片段数: {len(track['clips'])}")
        
        # 显示前两个片段
        for j, clip in enumerate(track['clips'][:2]):
            print(f"     - 片段{j+1}: {clip['start']}-{clip['end']}秒")
            if 'content' in clip and 'text' in clip['content']:
                print(f"       文字: {clip['content']['text']}")
    
    # 保存到文件
    output_dir = Path("output/nl_tests")
    with open(output_dir / "complex_edit.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'complex_edit.json'}")


def test_education_video():
    """测试教育视频制作"""
    print("\n=== 测试3: 教育视频 ===")
    
    processor = NaturalLanguageProcessor()
    
    user_input = """
    制作60秒的Python编程教学视频：
    0-10秒：介绍什么是Python，显示Python logo
    10-30秒：演示Hello World代码，需要代码高亮
    30-50秒：讲解变量和数据类型，配字幕
    50-60秒：总结并预告下节课内容
    使用平缓节奏，绿色主题，加背景音乐
    """
    
    print(f"用户输入: {user_input}")
    
    timeline = processor.process_natural_language(user_input)
    
    # 分析教育视频特点
    print("\n教育视频分析:")
    print(f"- 标题: {timeline['metadata']['title']}")
    print(f"- 标签: {', '.join(timeline['metadata']['tags'])}")
    
    # 保存
    output_dir = Path("output/nl_tests")
    with open(output_dir / "education_video.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'education_video.json'}")


def test_social_media_video():
    """测试社交媒体短视频"""
    print("\n=== 测试4: 抖音风格短视频 ===")
    
    processor = NaturalLanguageProcessor()
    
    user_input = """
    制作15秒的抖音风格视频：
    开头2秒吸引眼球，使用震动特效
    3-10秒展示主要内容，快节奏剪辑
    最后5秒号召关注，加发光特效
    全程配动感背景音乐，使用金色主题
    """
    
    print(f"用户输入: {user_input}")
    
    timeline = processor.process_natural_language(user_input)
    
    # 分析短视频特点
    video_clips = [c for t in timeline['timeline']['tracks'] 
                   if t['type'] == 'video' for c in t['clips']]
    
    print("\n短视频特效分析:")
    for i, clip in enumerate(video_clips):
        if clip['filters']:
            print(f"  片段{i+1} ({clip['start']}-{clip['end']}秒): {', '.join(clip['filters'])}")
    
    # 保存
    output_dir = Path("output/nl_tests")
    with open(output_dir / "social_media_video.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'social_media_video.json'}")


def test_vlog_style():
    """测试Vlog风格视频"""
    print("\n=== 测试5: Vlog风格 ===")
    
    processor = NaturalLanguageProcessor()
    
    user_input = """
    制作3分钟的旅行vlog：
    0-30秒：展示目的地风景，慢节奏，配轻音乐
    30-90秒：记录美食体验，加字幕介绍
    90-150秒：分享旅行感受，使用模糊背景
    最后30秒：总结和预告，淡出效果
    整体使用温暖的橙色调
    """
    
    print(f"用户输入: {user_input}")
    
    timeline = processor.process_natural_language(user_input)
    
    print(f"\nVlog视频信息:")
    print(f"- 总时长: {timeline['timeline']['duration']}秒 ({timeline['timeline']['duration']/60:.1f}分钟)")
    print(f"- 主题色: {timeline['timeline']['background_color']}")
    
    # 统计各类轨道
    track_types = {}
    for track in timeline['timeline']['tracks']:
        track_types[track['type']] = track_types.get(track['type'], 0) + 1
    
    print("\n轨道统计:")
    for track_type, count in track_types.items():
        print(f"  - {track_type}: {count}个")
    
    # 保存
    output_dir = Path("output/nl_tests")
    with open(output_dir / "vlog_video.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 时间轴已保存到: {output_dir / 'vlog_video.json'}")


def interactive_test():
    """交互式测试"""
    print("\n=== 交互式测试 ===")
    print("请输入您的视频编辑需求（输入'退出'结束）：")
    
    processor = NaturalLanguageProcessor()
    output_dir = Path("output/nl_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    while True:
        user_input = input("\n> ")
        
        if user_input.lower() in ['退出', 'exit', 'quit']:
            print("感谢使用！")
            break
        
        if not user_input.strip():
            continue
        
        try:
            # 处理输入
            timeline = processor.process_natural_language(user_input)
            
            # 显示结果
            print("\n生成的时间轴信息:")
            print(f"- 标题: {timeline['metadata']['title']}")
            print(f"- 时长: {timeline['timeline']['duration']}秒")
            print(f"- 轨道: {len(timeline['timeline']['tracks'])}个")
            
            # 保存文件
            import time
            filename = f"interactive_{int(time.time())}.json"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(timeline, f, ensure_ascii=False, indent=2)
            
            print(f"- 已保存到: {filepath}")
            
        except Exception as e:
            print(f"处理出错: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自然语言视频编辑测试")
    parser.add_argument("--test", choices=["simple", "complex", "education", "social", "vlog", "interactive", "all"],
                       default="all", help="选择测试类型")
    
    args = parser.parse_args()
    
    if args.test == "simple":
        test_simple_video_edit()
    elif args.test == "complex":
        test_complex_video_edit()
    elif args.test == "education":
        test_education_video()
    elif args.test == "social":
        test_social_media_video()
    elif args.test == "vlog":
        test_vlog_style()
    elif args.test == "interactive":
        interactive_test()
    else:
        # 运行所有测试
        test_simple_video_edit()
        test_complex_video_edit()
        test_education_video()
        test_social_media_video()
        test_vlog_style()
        
        print("\n" + "="*60)
        print("所有测试完成！")
        print("您可以使用 --test interactive 进入交互模式")
        print("="*60)


if __name__ == "__main__":
    main()
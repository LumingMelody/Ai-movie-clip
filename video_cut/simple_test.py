#!/usr/bin/env python
"""
简单测试脚本 - 最基础的视频剪辑测试
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_basic_video(video_path: str):
    """基础视频测试"""
    print(f"\n📹 测试视频: {video_path}")
    
    # 检查文件
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 创建输出目录
    os.makedirs("output", exist_ok=True)
    
    # 导入必要的模块
    from video_cut.natural_language_processor import VideoTimelineProcessor
    from video_cut.video_editor import VideoEditor
    
    print("\n1️⃣ 生成时间轴...")
    
    # 创建一个简单的时间轴
    processor = VideoTimelineProcessor()
    timeline = processor.generate_timeline_from_text(
        "制作一个30秒的测试视频，添加淡入淡出效果"
    )
    
    # 添加视频源
    if timeline["timeline"]["tracks"]:
        for track in timeline["timeline"]["tracks"]:
            if track["type"] == "video" and track.get("clips"):
                for clip in track["clips"]:
                    clip["source"] = video_path
                    # 确保时间在视频范围内
                    clip["clip_in"] = 0
                    clip["clip_out"] = min(30, clip["end"] - clip["start"])
    
    print("✅ 时间轴生成完成")
    print(f"   时长: {timeline['timeline']['duration']}秒")
    print(f"   轨道数: {len(timeline['timeline']['tracks'])}")
    
    print("\n2️⃣ 执行视频剪辑...")
    
    # 创建编辑器
    editor = VideoEditor(enable_memory_optimization=False)  # 简单测试不需要优化
    
    # 执行剪辑
    output_path = "output/test_simple_output.mp4"
    
    try:
        success = editor.execute_timeline(timeline, output_path)
        
        if success:
            print(f"\n✅ 视频剪辑成功！")
            print(f"   输出文件: {output_path}")
            
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024*1024)
                print(f"   文件大小: {size_mb:.2f} MB")
        else:
            print("❌ 视频剪辑失败")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="简单视频剪辑测试")
    parser.add_argument("video", help="视频文件路径")
    
    args = parser.parse_args()
    
    print("""
    ========================================
         简单视频剪辑测试
    ========================================
    """)
    
    test_basic_video(args.video)
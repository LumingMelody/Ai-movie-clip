#!/usr/bin/env python3
"""
使用真实视频测试火山引擎转场特效
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

from core.clipeffects.volcano_effects_improved import create_volcano_effects_v2

def find_test_video():
    """查找可用的测试视频"""
    # 可能的视频文件位置
    possible_paths = [
        # 项目中的测试视频
        "test_video.mp4",
        "demo.mp4", 
        "sample.mp4",
        
        # macOS系统视频
        "/System/Library/Compositions/Ripple.mov",
        "/System/Library/Compositions/Sunset.mov",
        
        # 常见下载目录
        os.path.expanduser("~/Downloads/test.mp4"),
        os.path.expanduser("~/Downloads/demo.mp4"),
        
        # 桌面
        os.path.expanduser("~/Desktop/test.mp4"),
        os.path.expanduser("~/Desktop/demo.mp4"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ 找到测试视频: {path}")
            return path
    
    return None

def test_with_real_video(video_path: str):
    """使用真实视频测试转场效果"""
    print(f"\n🎬 使用真实视频测试转场效果")
    print(f"视频文件: {video_path}")
    print("=" * 60)
    
    try:
        from moviepy import VideoFileClip
        
        # 加载视频
        full_clip = VideoFileClip(video_path)
        print(f"📊 视频信息:")
        print(f"   - 时长: {full_clip.duration:.2f}秒")
        print(f"   - 分辨率: {full_clip.size}")
        print(f"   - FPS: {full_clip.fps}")
        
        # 创建两个测试片段
        segment_duration = min(3.0, full_clip.duration / 3)  # 每段3秒或视频长度的1/3
        
        clip1 = full_clip.subclipped(0, segment_duration)
        clip2 = full_clip.subclipped(segment_duration, segment_duration * 2)
        
        print(f"   - 测试片段1: 0-{segment_duration:.1f}秒")
        print(f"   - 测试片段2: {segment_duration:.1f}-{segment_duration*2:.1f}秒")
        
        # 创建火山引擎特效管理器
        volcano = create_volcano_effects_v2()
        
        # 测试不同转场效果
        transitions_to_test = [
            ("fade", "淡入淡出", 1.0),
            ("slide_left", "左滑动", 0.8),
            ("slide_right", "右滑动", 0.8),
        ]
        
        results = []
        
        for transition_name, display_name, duration in transitions_to_test:
            print(f"\n🔄 测试转场: {display_name}")
            
            try:
                # 应用转场效果
                result_clip = volcano.apply_transition_effect(
                    clip1, clip2,
                    transition_name,
                    duration=duration,
                    use_api=False  # 使用本地实现
                )
                
                print(f"✅ {display_name} 转场成功")
                print(f"   - 转场时长: {duration}秒")
                print(f"   - 输出总长: {result_clip.duration:.2f}秒")
                print(f"   - 输出分辨率: {result_clip.size}")
                
                # 保存测试结果（可选）
                output_filename = f"transition_test_{transition_name}.mp4"
                print(f"   - 保存为: {output_filename}")
                
                # 实际保存到文件
                result_clip.write_videofile(
                    output_filename,
                    fps=24,
                    codec='libx264', 
                    audio_codec='aac'
                )
                
                results.append({
                    'name': display_name,
                    'transition': transition_name,
                    'duration': result_clip.duration,
                    'success': True
                })
                
                # 清理结果剪辑
                result_clip.close()
                
            except Exception as e:
                print(f"❌ {display_name} 转场失败: {str(e)}")
                results.append({
                    'name': display_name,
                    'transition': transition_name,
                    'success': False,
                    'error': str(e)
                })
        
        # 清理测试片段
        clip1.close()
        clip2.close()
        full_clip.close()
        
        # 总结测试结果
        print(f"\n📊 测试结果总结:")
        print("=" * 40)
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        print(f"✅ 成功: {success_count}/{total_count} 个转场效果")
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            if result['success']:
                print(f"{status} {result['name']}: {result['duration']:.2f}秒")
            else:
                print(f"{status} {result['name']}: {result.get('error', '未知错误')}")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ 视频测试失败: {str(e)}")
        return False

def create_demo_video():
    """创建演示视频用于测试"""
    print(f"\n🎬 创建演示视频")
    print("=" * 60)
    
    try:
        from moviepy import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips
        import tempfile
        
        # 创建多个不同颜色的片段
        segments = []
        colors = [
            ((255, 0, 0), "红色片段"),
            ((0, 255, 0), "绿色片段"), 
            ((0, 0, 255), "蓝色片段"),
            ((255, 255, 0), "黄色片段")
        ]
        
        for (color, text) in colors:
            # 创建彩色背景
            bg = ColorClip(size=(640, 480), color=color, duration=3)
            
            # 添加文字
            txt = TextClip(
                text=text,
                font_size=50,
                color='white',
                font='Arial'  # 使用系统字体
            ).with_position('center').with_duration(3)
            
            # 合成
            segment = CompositeVideoClip([bg, txt])
            segments.append(segment)
        
        # 连接所有片段
        demo_video = concatenate_videoclips(segments)
        
        # 保存演示视频
        demo_path = "demo_test_video.mp4"
        print(f"💾 保存演示视频: {demo_path}")
        
        demo_video.write_videofile(
            demo_path,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        
        # 清理
        demo_video.close()
        for segment in segments:
            segment.close()
        
        print(f"✅ 演示视频创建成功")
        print(f"   - 文件: {demo_path}")
        print(f"   - 时长: {len(segments) * 3}秒")
        print(f"   - 分辨率: 640x480")
        
        return demo_path
        
    except Exception as e:
        print(f"❌ 演示视频创建失败: {str(e)}")
        return None

def main():
    """主测试函数"""
    print("🚀 火山引擎转场特效真实视频测试")
    print("=" * 60)
    
    # 查找测试视频
    video_path = find_test_video()
    
    if not video_path:
        print("⚠️ 未找到测试视频，尝试创建演示视频...")
        video_path = create_demo_video()
    
    if video_path:
        success = test_with_real_video(video_path)
        
        if success:
            print(f"\n🎉 所有转场测试成功完成！")
        else:
            print(f"\n⚠️ 部分转场测试失败，请检查日志")
    else:
        print(f"\n❌ 无法获取测试视频，请手动提供视频文件")
        print(f"建议：将视频文件命名为 'test_video.mp4' 并放在项目根目录")
    
    print("=" * 60)

if __name__ == "__main__":
    # main()
    test_with_real_video("/Users/luming/Downloads/老登.mp4")
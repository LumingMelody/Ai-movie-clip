#!/usr/bin/env python
"""
超简单的在线视频测试
一行命令即可测试
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_with_url(url: str = None):
    """使用URL测试"""
    
    if not url:
        # 使用一个公开的测试视频
        url = "https://www.w3schools.com/html/mov_bbb.mp4"
        print(f"使用测试视频: {url}")
    
    print("\n🎬 开始在线视频剪辑测试...\n")
    
    # 导入必要模块
    from video_cut.video_editor import VideoEditor
    import os
    import json
    from datetime import datetime
    
    # 创建输出目录
    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # 创建最简单的时间轴 - 直接使用URL
    timeline = {
        "version": "1.0",
        "metadata": {
            "title": "快速测试",
            "created_at": datetime.now().isoformat()
        },
        "timeline": {
            "duration": 10,  # 只剪10秒
            "fps": 30,
            "resolution": {"width": 1280, "height": 720},  # 使用较小分辨率加快处理
            "tracks": [
                {
                    "type": "video",
                    "name": "主视频",
                    "clips": [
                        {
                            "start": 0,
                            "end": 10,
                            "source": url,  # 直接使用URL
                            "clip_in": 0,
                            "clip_out": 10,
                            "filters": []
                        }
                    ]
                },
                {
                    "type": "text",
                    "name": "标题",
                    "clips": [
                        {
                            "start": 1,
                            "end": 5,
                            "content": {
                                "text": "视频剪辑测试",
                                "font": "Arial",
                                "size": 48,
                                "color": "#FFFFFF",
                                "position": "center"
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    # 保存时间轴
    timeline_file = "output/quick_test_timeline.json"
    with open(timeline_file, 'w') as f:
        json.dump(timeline, f, indent=2)
    print(f"✅ 时间轴已创建: {timeline_file}")
    
    # 先尝试下载视频
    print("\n⬇️  下载视频中...")
    import urllib.request
    
    local_video = "temp/test_video.mp4"
    try:
        urllib.request.urlretrieve(url, local_video)
        print(f"✅ 视频已下载到: {local_video}")
        
        # 更新时间轴使用本地路径
        timeline["timeline"]["tracks"][0]["clips"][0]["source"] = local_video
        
    except Exception as e:
        print(f"⚠️  下载失败: {e}")
        print("将尝试直接使用URL...")
    
    # 执行剪辑
    print("\n🎬 开始剪辑...")
    editor = VideoEditor(enable_memory_optimization=False)
    
    output_file = f"output/quick_test_{datetime.now().strftime('%H%M%S')}.mp4"
    
    try:
        success = editor.execute_timeline(timeline, output_file)
        
        if success:
            print(f"\n✅ 剪辑成功！")
            print(f"📁 输出文件: {output_file}")
            
            if os.path.exists(output_file):
                size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"📊 文件大小: {size:.2f} MB")
        else:
            print("\n❌ 剪辑失败")
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        
        # 如果是因为找不到视频，提供帮助
        if "不存在" in str(e) or "not found" in str(e).lower():
            print("\n💡 提示：")
            print("1. 确保视频URL可以访问")
            print("2. 或者先下载视频到本地")
            print("3. 使用本地视频路径测试")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="快速在线视频测试")
    parser.add_argument("--url", "-u", help="视频URL（可选）")
    
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════╗
║        快速在线视频剪辑测试                ║
╚════════════════════════════════════════════╝
    """)
    
    test_with_url(args.url)
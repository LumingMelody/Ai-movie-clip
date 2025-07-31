#!/usr/bin/env python3
"""
测试音频播放和删除功能
"""

import sys
import os
import time
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

from core.cliptemplate.coze.audio_player import AudioPlayer, play_audio_async

def create_test_audio():
    """创建一个测试音频文件"""
    test_file = "test_audio.txt"  # 文本文件模拟
    with open(test_file, 'w') as f:
        f.write("测试音频文件内容")
    return test_file

def test_audio_operations():
    """测试音频播放和删除操作"""
    print("🎵 测试音频播放和删除功能...")
    
    # 创建测试文件
    test_file = create_test_audio()
    print(f"📁 创建测试文件: {test_file}")
    
    # 测试同步播放
    print("\n🔊 测试同步播放（应该快速失败）...")
    result = AudioPlayer.play(test_file, block=False)
    print(f"结果: {result}")
    
    # 测试异步播放和删除
    print("\n🔊 测试异步播放和删除...")
    if os.path.exists(test_file):
        print(f"✅ 文件存在: {test_file}")
        thread = play_audio_async(test_file, delete_after=True)
        print(f"✅ 异步任务启动: {thread}")
        
        # 等待一会儿看删除结果
        print("⏳ 等待5秒查看结果...")
        time.sleep(5)
        
        if os.path.exists(test_file):
            print(f"⚠️ 文件仍然存在: {test_file}")
            os.remove(test_file)
            print(f"🗑️ 手动删除文件")
        else:
            print(f"✅ 文件已被自动删除")
    else:
        print(f"❌ 测试文件不存在")
    
    print("\n🎉 测试完成")

if __name__ == "__main__":
    test_audio_operations()
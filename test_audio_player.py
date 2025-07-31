#!/usr/bin/env python3
"""
测试跨平台音频播放器
"""

import sys
import os
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

from core.cliptemplate.coze.audio_player import AudioPlayer, play_audio_async

def test_audio_player():
    """测试音频播放器"""
    print("🎵 测试跨平台音频播放器...")
    
    # 创建一个测试音频文件路径
    # 注意：这只是测试API，不会实际播放不存在的文件
    test_file = "test_audio.mp3"
    
    print(f"📱 当前平台: {os.name}")
    
    # 测试同步播放
    print("🔊 测试同步播放...")
    try:
        result = AudioPlayer.play(test_file, block=False)
        print(f"✅ 同步播放结果: {result}")
    except Exception as e:
        print(f"❌ 同步播放出错: {e}")
    
    # 测试异步播放
    print("🔊 测试异步播放...")
    try:
        thread = play_audio_async(test_file, delete_after=False)
        print(f"✅ 异步播放线程已启动: {thread}")
    except Exception as e:
        print(f"❌ 异步播放出错: {e}")
    
    print("🎉 音频播放器测试完成")

if __name__ == "__main__":
    test_audio_player()
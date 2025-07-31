#!/usr/bin/env python3
"""
测试改进后的音频播放功能
"""

import sys
import os
import platform
import time

# 确保能找到我们的模块
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

def test_audio_player():
    """测试音频播放器的各种方法"""
    from core.cliptemplate.coze.audio_player import AudioPlayer
    
    print("🎵 测试改进后的音频播放器")
    print("=" * 50)
    print(f"操作系统: {platform.system()}")
    
    # 查找测试音频文件
    test_files = []
    for ext in ['.mp3', '.wav', '.m4a']:
        files = [f for f in os.listdir('.') if f.endswith(ext)]
        test_files.extend(files)
    
    if not test_files:
        print("❌ 没有找到音频文件进行测试")
        print("请确保当前目录有音频文件 (.mp3, .wav, .m4a)")
        return
    
    test_file = test_files[0]
    print(f"📁 使用测试文件: {test_file}")
    
    # 检查文件
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    file_size = os.path.getsize(test_file)
    print(f"📊 文件大小: {file_size} 字节")
    
    if file_size == 0:
        print("❌ 文件为空，无法测试")
        return
    
    # 测试播放
    print(f"\n🔊 开始测试音频播放...")
    print("注意：如果听到声音，说明修复成功！")
    
    try:
        print("⏯️ 测试非阻塞播放...")
        result1 = AudioPlayer.play(test_file, block=False)
        print(f"非阻塞播放结果: {result1}")
        
        if result1:
            print("⏳ 等待3秒让音频播放...")
            time.sleep(3)
        
        print("\n⏯️ 测试阻塞播放...")
        result2 = AudioPlayer.play(test_file, block=True)
        print(f"阻塞播放结果: {result2}")
        
        if result1 or result2:
            print("✅ 至少有一种播放方式成功")
        else:
            print("❌ 所有播放方式都失败")
            
    except Exception as e:
        print(f"❌ 播放测试异常: {e}")
    
    print("\n🎉 测试完成")

def test_async_play():
    """测试异步播放和删除功能"""
    from core.cliptemplate.coze.audio_player import play_audio_async
    
    print("\n🔄 测试异步播放...")
    
    # 创建一个临时音频文件（实际上是文本文件，但可以测试删除功能）
    temp_file = "temp_audio_test.txt"
    with open(temp_file, 'w') as f:
        f.write("这是一个测试文件，用来验证删除功能")
    
    print(f"📁 创建临时文件: {temp_file}")
    
    # 测试异步播放和删除
    thread = play_audio_async(temp_file, delete_after=True)
    print(f"🔄 异步任务启动: {thread}")
    
    # 等待看结果
    print("⏳ 等待5秒查看删除结果...")
    time.sleep(5)
    
    if os.path.exists(temp_file):
        print(f"⚠️ 临时文件仍然存在: {temp_file}")
        try:
            os.remove(temp_file)
            print("🗑️ 手动删除成功")
        except Exception as e:
            print(f"❌ 手动删除失败: {e}")
    else:
        print("✅ 临时文件已被自动删除")

if __name__ == "__main__":
    print("🖥️ 音频播放器修复测试")
    print("=" * 50)
    
    test_audio_player()
    test_async_play()
    
    print("\n" + "=" * 50)
    print("🏁 所有测试完成")
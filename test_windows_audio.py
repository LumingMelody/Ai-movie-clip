#!/usr/bin/env python3
"""
Windows音频播放测试脚本
"""

import sys
import os
import platform

# 检查是否在Windows上运行
if platform.system() != 'Windows':
    print("⚠️ 此脚本专为Windows设计，当前系统:", platform.system())
    exit(1)

sys.path.append(os.path.dirname(__file__))

def test_windows_audio():
    """测试Windows音频播放功能"""
    from core.cliptemplate.coze.audio_player import AudioPlayer
    
    print("🎵 Windows音频播放测试")
    print("=" * 50)
    
    # 检查是否有MP3文件
    mp3_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    
    if not mp3_files:
        print("❌ 没有找到MP3文件进行测试")
        print("请确保当前目录有MP3音频文件")
        return
    
    test_file = mp3_files[0]
    print(f"📁 使用测试文件: {test_file}")
    
    # 检查文件大小
    file_size = os.path.getsize(test_file)
    print(f"📊 文件大小: {file_size} 字节")
    
    # 测试播放
    print(f"\n🔊 开始测试音频播放...")
    try:
        result = AudioPlayer.play(test_file, block=True)
        if result:
            print("✅ 音频播放测试完成")
        else:
            print("❌ 音频播放失败")
    except Exception as e:
        print(f"❌ 音频播放异常: {e}")
    
    print("\n🎉 测试结束")

def check_audio_system():
    """检查Windows音频系统"""
    print("🔍 检查Windows音频系统...")
    
    try:
        # 检查Windows Media Player COM
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        try:
            wmp = win32com.client.Dispatch("WMPlayer.OCX")
            print("✅ Windows Media Player COM 可用")
            print(f"🔊 当前音量设置: {wmp.settings.volume}")
        except Exception as e:
            print(f"❌ Windows Media Player COM 不可用: {e}")
        finally:
            pythoncom.CoUninitialize()
            
    except ImportError:
        print("❌ win32com 库未安装")
    
    try:
        # 检查pygame
        import pygame
        pygame.mixer.init()
        print("✅ pygame 音频系统可用")
        print(f"🎮 pygame mixer设置: {pygame.mixer.get_init()}")
        pygame.mixer.quit()
    except ImportError:
        print("❌ pygame 库未安装")
    except Exception as e:
        print(f"❌ pygame 音频系统错误: {e}")

if __name__ == "__main__":
    print("🖥️ Windows音频系统诊断")
    print("=" * 50)
    check_audio_system()
    print("\n" + "=" * 50)
    test_windows_audio()
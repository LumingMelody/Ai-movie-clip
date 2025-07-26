#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试声音克隆缓存功能
"""
import os
import time
import shutil

# 清理之前的缓存文件（用于测试）
voice_id_file = "live_config/xiaozong_voice_id.txt"
if os.path.exists(voice_id_file):
    backup_file = f"live_config/xiaozong_voice_id_backup_{int(time.time())}.txt"
    shutil.copy(voice_id_file, backup_file)
    print(f"✅ 已备份原有voice_id文件到: {backup_file}")
    os.remove(voice_id_file)
    print(f"🗑️ 已删除原有voice_id文件: {voice_id_file}")

# 导入测试模块
from core.cliptemplate.coze.auto_live_reply import WebSocketClient, SocketServer

print("\n" + "="*50)
print("🧪 测试声音克隆缓存功能")
print("="*50 + "\n")

# 测试1: WebSocketClient 首次创建voice克隆
print("📝 测试1: WebSocketClient 首次创建voice克隆")
client = WebSocketClient(use_voice_cloning=True)
test_text = "你好，这是一个测试"

try:
    audio_file = client.generate_audio(test_text)
    if audio_file:
        print(f"✅ 首次生成音频成功: {audio_file}")
        # 检查是否创建了voice_id文件
        if os.path.exists(voice_id_file):
            with open(voice_id_file, 'r') as f:
                saved_voice_id = f.read().strip()
            print(f"✅ voice_id已保存到文件: {saved_voice_id}")
        else:
            print("❌ voice_id文件未创建")
        
        # 清理音频文件
        if os.path.exists(audio_file):
            os.remove(audio_file)
    else:
        print("❌ 音频生成失败")
except Exception as e:
    print(f"❌ 测试1失败: {e}")

print("\n" + "-"*50 + "\n")

# 测试2: WebSocketClient 使用缓存的voice_id
print("📝 测试2: WebSocketClient 使用缓存的voice_id")
client2 = WebSocketClient(use_voice_cloning=True)
test_text2 = "这是第二次测试，应该使用缓存的voice_id"

try:
    audio_file2 = client2.generate_audio(test_text2)
    if audio_file2:
        print(f"✅ 使用缓存生成音频成功: {audio_file2}")
        # 清理音频文件
        if os.path.exists(audio_file2):
            os.remove(audio_file2)
    else:
        print("❌ 音频生成失败")
except Exception as e:
    print(f"❌ 测试2失败: {e}")

print("\n" + "-"*50 + "\n")

# 测试3: SocketServer 使用缓存的voice_id
print("📝 测试3: SocketServer 使用缓存的voice_id")
server = SocketServer(use_voice_cloning=True)
test_text3 = "这是SocketServer测试，也应该使用缓存的voice_id"

try:
    audio_file3 = server.generate_audio(test_text3)
    if audio_file3:
        print(f"✅ SocketServer使用缓存生成音频成功: {audio_file3}")
        # 清理音频文件
        if os.path.exists(audio_file3):
            os.remove(audio_file3)
    else:
        print("❌ 音频生成失败")
except Exception as e:
    print(f"❌ 测试3失败: {e}")

print("\n" + "="*50)
print("🎉 测试完成！")
print("="*50)

# 显示最终的voice_id
if os.path.exists(voice_id_file):
    with open(voice_id_file, 'r') as f:
        final_voice_id = f.read().strip()
    print(f"\n📋 最终保存的voice_id: {final_voice_id}")
else:
    print("\n❌ 未找到voice_id文件")
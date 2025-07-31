#!/usr/bin/env python3
"""
调试AuraRender视频资源加载问题
"""

import sys
import os
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

from video_cut.aura_render.aura_interface import AuraRenderInterface

def test_aura_render():
    """测试AuraRender视频生成"""
    
    # 测试请求
    request = {
        'natural_language': '创建一个30秒的智能手表广告视频，展示心率监测、消息提醒和运动追踪功能，风格现代科技感',
        'video_url': 'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4',
        'duration': 30,
        'mode': 'sync',
        'upload_oss': False
    }
    
    print("🎬 开始测试AuraRender...")
    print(f"请求参数: {request}")
    
    # 创建AuraRender接口
    aura_interface = AuraRenderInterface()
    
    # 执行视频创建
    result = aura_interface.create_video(request)
    
    print("\n📊 执行结果:")
    if result['status'] == 'success':
        print(f"✅ 生成成功!")
        print(f"📹 视频路径: {result['video_url']}")
        print(f"🎯 视频类型: {result['metadata']['video_type']}")
        print(f"🎨 视频风格: {result['metadata']['style']}")
        print(f"⏱️ 视频时长: {result['metadata']['duration']}s")
        
        # 检查文件是否存在
        if os.path.exists(result['video_url']):
            file_size = os.path.getsize(result['video_url'])
            print(f"📁 文件大小: {file_size/1024/1024:.2f} MB")
        else:
            print("❌ 生成的视频文件不存在!")
            
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")
    
    return result

if __name__ == "__main__":
    result = test_aura_render()
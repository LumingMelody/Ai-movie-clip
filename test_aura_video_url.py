#!/usr/bin/env python3
"""
测试AuraRender视频URL处理
"""

import sys
import os
import requests
import json

# 确保能找到我们的模块
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

def test_video_url_processing():
    """测试视频URL处理逻辑"""
    print("🧪 测试AuraRender视频URL处理")
    print("=" * 60)
    
    # 测试用例1：视频截图接口URL
    test_cases = [
        {
            "name": "视频截图接口",
            "url": "https://resource.meihua.info/2SxYJ5jka40dYgykSYASyV3Rrik=/lpiQ2r5c_D1le3yAmYhWEMYu7HVb?vframe/jpg/offset/7/w/1100",
            "description": "包含vframe/jpg的截图接口，应该被转换为视频URL"
        },
        {
            "name": "正常视频URL", 
            "url": "https://example.com/video.mp4",
            "description": "正常的视频文件URL"
        },
        {
            "name": "无扩展名URL",
            "url": "https://resource.meihua.info/2SxYJ5jka40dYgykSYASyV3Rrik=/lpiQ2r5c_D1le3yAmYhWEMYu7HVb",
            "description": "没有文件扩展名的URL"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {case['name']}")
        print(f"   URL: {case['url']}")
        print(f"   说明: {case['description']}")
        
        # 检测逻辑
        url = case['url']
        if 'vframe/jpg' in url or 'vframe/png' in url:
            print("   ⚠️ 检测到视频截图接口")
            processed_url = url.split('?')[0]
            print(f"   🔄 转换后URL: {processed_url}")
        else:
            print("   ✅ 正常视频URL")
            processed_url = url
        
        # 文件名处理逻辑
        filename = os.path.basename(processed_url.split('?')[0])
        if not filename or '.' not in filename:
            filename = f"downloaded_{i}.mp4"
            print(f"   📁 生成文件名: {filename}")
        elif not any(filename.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']):
            filename += '.mp4'
            print(f"   📁 添加扩展名: {filename}")
        else:
            print(f"   📁 使用原文件名: {filename}")

def test_aura_interface():
    """测试AuraRender接口处理"""
    print("\n🎬 测试AuraRender接口处理")
    print("=" * 60)
    
    try:
        from video_cut.aura_render.aura_interface import AuraRenderInterface
        
        # 创建接口实例
        aura = AuraRenderInterface()
        
        # 测试请求
        test_request = {
            'natural_language': '制作一个30秒的炫酷视频',
            'video_url': 'https://resource.meihua.info/2SxYJ5jka40dYgykSYASyV3Rrik=/lpiQ2r5c_D1le3yAmYhWEMYu7HVb?vframe/jpg/offset/7/w/1100',
            'preferences': {}
        }
        
        print("📝 测试请求:")
        print(json.dumps(test_request, indent=2, ensure_ascii=False))
        
        print("\n🔍 模拟URL检测逻辑...")
        video_url = test_request['video_url']
        print(f"原始URL: {video_url}")
        
        if 'vframe/jpg' in video_url or 'vframe/png' in video_url:
            print("⚠️  检测到视频截图接口，将在执行层处理URL转换")
        
        print("\n✅ URL处理逻辑测试完成")
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """测试API端点"""
    print("\n🌐 测试API端点")
    print("=" * 60)
    
    # 测试数据
    test_data = {
        "natural_language": "制作一个30秒的炫酷视频",
        "video_url": "https://resource.meihua.info/2SxYJ5jka40dYgykSYASyV3Rrik=/lpiQ2r5c_D1le3yAmYhWEMYu7HVb?vframe/jpg/offset/7/w/1100",
        "duration": 30,
        "style": "炫酷",
        "mode": "sync"
    }
    
    print("📝 测试数据:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:8100/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正在运行")
            
            # 发送测试请求
            print("\n📡 发送测试请求...")
            response = requests.post(
                "http://localhost:8100/video/natural-language-edit",
                json=test_data,
                timeout=120
            )
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 请求成功")
                print(f"状态: {result.get('status', 'unknown')}")
                if 'video_url' in result:
                    print(f"视频URL: {result['video_url']}")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        else:
            print(f"⚠️ 服务响应异常: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务正在运行")
        print("   启动命令: python app_0715.py 或 uvicorn app_0715:app --port 8100")
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    print("🧪 AuraRender视频URL处理测试套件")
    print("=" * 60)
    
    test_video_url_processing()
    test_aura_interface()
    test_api_endpoint()
    
    print("\n🏁 所有测试完成")
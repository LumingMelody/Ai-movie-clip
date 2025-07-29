import requests
import json

# 测试 /video/highlight-clip 接口
def test_highlight_clip_api():
    # API 端点
    url = "http://localhost:8000/video/highlight-clip"
    
    # 测试数据 - 使用本地文件
    data = {
        "video_source": "test.mp4",
        "excel_source": "test2.xlsx", 
        "target_duration": 30,
        "mode": "sync"  # 同步模式测试
    }
    
    print("🔧 测试视频高光剪辑API...")
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送POST请求
        response = requests.post(url, json=data)
        
        # 打印响应
        print(f"\n📡 响应状态码: {response.status_code}")
        print(f"📄 响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        # 测试异步模式
        print("\n\n🔧 测试异步模式...")
        data["mode"] = "async"
        response_async = requests.post(url, json=data)
        
        print(f"📡 异步响应状态码: {response_async.status_code}")
        print(f"📄 异步响应内容:")
        print(json.dumps(response_async.json(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    test_highlight_clip_api()
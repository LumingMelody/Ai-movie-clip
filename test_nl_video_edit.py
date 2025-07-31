"""
测试自然语言视频剪辑接口
"""
import requests
import json
import time


def test_natural_language_video_edit():
    """测试自然语言视频剪辑接口"""
    
    # API地址
    base_url = "http://localhost:8100"
    endpoint = "/video/natural-language-edit"
    
    # 测试用例
    test_cases = [
        {
            "name": "产品介绍视频 - 同步模式",
            "request": {
                "natural_language": "制作一个30秒的产品介绍视频，开头5秒展示logo带光晕特效，然后介绍产品功能",
                "video_url": "https://example.com/test_video.mp4",  # 需要替换为真实的视频URL
                "mode": "sync",
                "output_duration": 30,
                "style": "科技感",
                "use_timeline_editor": True,
                "tenant_id": "test_tenant",
                "id": "test_business_001"
            }
        },
        {
            "name": "Vlog视频 - 异步模式",
            "request": {
                "natural_language": "制作一个1分钟的旅行vlog，要有温馨的背景音乐和手写风格字幕",
                "video_url": "https://example.com/test_video2.mp4",  # 需要替换为真实的视频URL
                "mode": "async",
                "output_duration": 60,
                "style": "温馨",
                "use_timeline_editor": True,
                "tenant_id": "test_tenant",
                "id": "test_business_002"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*50}")
        print(f"测试用例: {test_case['name']}")
        print(f"{'='*50}")
        
        try:
            # 发送请求
            response = requests.post(
                f"{base_url}{endpoint}",
                json=test_case["request"],
                headers={"Content-Type": "application/json"}
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 请求成功!")
                print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 如果是异步模式，获取任务ID
                if test_case["request"]["mode"] == "async" and "task_id" in result:
                    task_id = result["task_id"]
                    print(f"\n📋 任务ID: {task_id}")
                    
                    # 查询任务状态
                    check_task_status(base_url, task_id)
                    
            else:
                print(f"❌ 请求失败!")
                print(f"状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 测试出错: {e}")


def check_task_status(base_url: str, task_id: str):
    """查询异步任务状态"""
    status_endpoint = f"/get-result/{task_id}"
    max_attempts = 10
    attempt = 0
    
    print(f"\n⏳ 查询任务状态...")
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}{status_endpoint}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")
                
                print(f"   尝试 {attempt + 1}: 状态 = {status}")
                
                if status == "completed":
                    print(f"\n✅ 任务完成!")
                    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    break
                elif status == "failed":
                    print(f"\n❌ 任务失败!")
                    print(f"错误: {result.get('error', '未知错误')}")
                    break
                    
            time.sleep(5)  # 等待5秒再查询
            attempt += 1
            
        except Exception as e:
            print(f"查询状态出错: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"\n⏱️ 查询超时，请稍后再试")


def test_with_real_video():
    """使用真实视频URL测试"""
    print("\n" + "="*60)
    print("使用真实视频测试")
    print("="*60)
    
    # 使用真实的视频URL
    real_request = {
        "natural_language": "制作一个30秒的产品介绍视频，展示产品的主要功能，要有科技感的特效和动感音乐",
        "video_url": "https://your-oss.oss-cn-beijing.aliyuncs.com/test/sample_video.mp4",  # 替换为真实URL
        "mode": "sync",
        "output_duration": 30,
        "use_timeline_editor": True,
        "tenant_id": "test_tenant_123",
        "id": "test_business_123"
    }
    
    base_url = "http://localhost:8100"
    endpoint = "/video/natural-language-edit"
    
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json=real_request,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"生成的视频URL: {result.get('data', {}).get('video_url', '未找到')}")
            print(f"\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def main():
    """主测试函数"""
    print("🎬 自然语言视频剪辑接口测试")
    print("确保服务运行在 http://localhost:8100")
    
    # 基础测试
    test_natural_language_video_edit()
    
    # 如果有真实视频URL，可以取消下面的注释
    # test_with_real_video()


if __name__ == "__main__":
    main()
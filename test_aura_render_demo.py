"""
AuraRender 完整测试演示

使用公开的测试视频展示AuraRender的各种功能
"""

import requests
import json
import time
import os

# API基础配置
BASE_URL = "http://localhost:8100"
API_ENDPOINT = "/video/natural-language-edit"

# 公开的测试视频URL（使用常见的示例视频）
TEST_VIDEO_URLS = {
    "product_demo": "https://www.w3schools.com/html/mov_bbb.mp4",  # Big Buck Bunny 示例片段
    "nature": "https://www.w3schools.com/html/movie.mp4",  # 花朵视频
    "pexels_coffee": "https://www.pexels.com/download/video/854221/",  # Pexels 免费咖啡视频
    "sample_1080p": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"  # 1080p示例
}

def test_product_ad():
    """测试1：产品广告视频"""
    print("\n" + "="*60)
    print("测试1：智能手表产品广告")
    print("="*60)
    
    request_data = {
        "natural_language": "制作一个30秒的智能手表产品广告。开头5秒展示品牌logo带光晕特效，然后15秒展示手表的健康监测功能，包括心率监测、睡眠追踪和运动记录，要有数据可视化效果。接下来8秒展示手表的时尚外观，360度旋转展示。最后2秒展示购买信息和二维码。整体风格要科技感十足，使用蓝紫色调，配上动感的电子音乐。",
        "video_url": TEST_VIDEO_URLS["sample_1080p"],
        "mode": "sync",
        "use_aura_render": True,
        "video_type": "product_ad",
        "style": "futuristic",
        "output_duration": 30
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def test_knowledge_explain():
    """测试2：知识科普视频"""
    print("\n" + "="*60)
    print("测试2：AI技术科普视频")
    print("="*60)
    
    request_data = {
        "natural_language": "制作一个90秒的AI技术科普视频，用通俗易懂的方式讲解机器学习的基本原理。视频分为5个部分：1.引入问题(10秒)-用生活中的例子引出AI话题；2.基础概念(20秒)-用图解说明什么是机器学习；3.工作原理(30秒)-展示神经网络的工作过程；4.实际应用(20秒)-展示AI在日常生活中的应用；5.总结展望(10秒)-总结要点并展望未来。使用清新的配色，加入动画图表，背景音乐轻松愉快。",
        "video_url": TEST_VIDEO_URLS["nature"],
        "mode": "sync",
        "use_aura_render": True,
        "video_type": "knowledge_explain",
        "output_duration": 90
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def test_vlog():
    """测试3：Vlog视频"""
    print("\n" + "="*60)
    print("测试3：咖啡店探店Vlog")
    print("="*60)
    
    request_data = {
        "natural_language": "用这段素材制作一个75秒的咖啡店探店vlog。开头8秒自我介绍和今日主题，配上活泼的标题动画。接下来20秒展示咖啡店的环境，要有温馨的滤镜。然后25秒详细记录点单和制作过程，加入慢动作特写。再15秒分享品尝感受，加入表情贴纸。最后7秒总结推荐，提醒观众点赞关注。整体风格温馨轻松，使用暖色调滤镜，配上轻快的背景音乐。",
        "video_url": TEST_VIDEO_URLS["sample_1080p"],
        "mode": "sync", 
        "use_aura_render": True,
        "video_type": "vlog",
        "style": "warm",
        "output_duration": 75
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def test_brand_promo():
    """测试4：品牌宣传视频"""
    print("\n" + "="*60)
    print("测试4：企业品牌宣传片")
    print("="*60)
    
    request_data = {
        "natural_language": "制作一个2分钟的科技公司品牌宣传片。片头8秒展示公司logo动画和企业愿景'科技改变生活'。第一部分(30秒)介绍公司发展历程，用时间轴展示重要里程碑。第二部分(40秒)展示核心技术和产品，包括AI、云计算、物联网解决方案。第三部分(30秒)展示企业文化和团队风采，突出创新精神。结尾12秒展望未来，呼吁'携手共创智能未来'。整体风格大气专业，使用企业蓝色主色调，配上激励人心的管弦乐背景音乐。",
        "video_url": TEST_VIDEO_URLS["sample_1080p"],
        "mode": "sync",
        "use_aura_render": True,
        "video_type": "brand_promo",
        "style": "professional",
        "output_duration": 120
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def test_auto_recognition():
    """测试5：自动识别视频类型"""
    print("\n" + "="*60)
    print("测试5：自动识别视频类型")
    print("="*60)
    
    request_data = {
        "natural_language": "帮我把这个视频剪辑成一个吸引人的短视频，时长控制在45秒左右。要有抓人眼球的开头，中间部分节奏紧凑，结尾要有号召行动的元素。自动分析内容选择合适的风格和音乐。",
        "video_url": TEST_VIDEO_URLS["sample_1080p"],
        "mode": "sync",
        "use_aura_render": True,
        # 不指定video_type，让系统自动识别
        "output_duration": 45
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def test_mixed_generation():
    """测试6：混合生成（需要AI生成素材）"""
    print("\n" + "="*60)
    print("测试6：混合生成 - 部分内容需要AI生成")
    print("="*60)
    
    request_data = {
        "natural_language": "制作一个60秒的未来科技概念展示视频。开头10秒展示'2050年的世界'标题，要有科幻感的文字动画。接下来20秒展示未来城市场景，如果素材中没有合适的画面，用AI生成赛博朋克风格的城市图片。然后20秒展示各种未来科技产品，包括全息投影、脑机接口、量子计算机等概念。最后10秒展示'未来已来'的结语。整体采用赛博朋克风格，霓虹色彩，配上富有未来感的电子音乐。",
        "video_url": TEST_VIDEO_URLS["sample_1080p"],
        "mode": "sync",
        "use_aura_render": True,
        "video_type": "concept_show",
        "style": "futuristic",
        "output_duration": 60
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

def send_request(data):
    """发送请求到API"""
    try:
        print(f"\n发送请求到: {BASE_URL}{API_ENDPOINT}")
        response = requests.post(
            f"{BASE_URL}{API_ENDPOINT}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n响应结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 提取关键信息
            if result.get("code") == 0:
                data = result.get("data", {})
                print("\n✅ 处理成功!")
                print(f"📹 输出视频: {data.get('video_url', 'N/A')}")
                print(f"🎬 视频类型: {data.get('video_info', {}).get('video_type', 'N/A')}")
                print(f"⏱️ 视频时长: {data.get('video_info', {}).get('duration', 'N/A')}秒")
                print(f"🎨 视频风格: {data.get('video_info', {}).get('style', 'N/A')}")
                print(f"📝 脚本路径: {data.get('process_info', {}).get('script_path', 'N/A')}")
                
                # 显示部分时间轴
                timeline = data.get('timeline', [])
                if timeline:
                    print(f"\n📊 时间轴片段数: {len(timeline)}")
                    print("前3个片段预览:")
                    for i, segment in enumerate(timeline[:3]):
                        print(f"  片段{i+1}: {segment.get('start', 0)}-{segment.get('end', 0)}秒")
            else:
                print(f"\n❌ 处理失败: {result.get('message', 'Unknown error')}")
                
        else:
            print(f"\n❌ 请求失败: {response.text}")
            
        return response
        
    except Exception as e:
        print(f"\n❌ 发送请求时出错: {str(e)}")
        return None

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🎬 AuraRender 测试演示 🎬".center(60, "="))
    print("使用公开测试视频展示各种功能")
    print("="*60)
    
    # 确认服务是否运行
    print("\n⚠️  请确保已经启动了服务:")
    print("   python app_0715.py")
    print("\n按Enter继续，或Ctrl+C退出...")
    input()
    
    tests = [
        test_product_ad,
        test_knowledge_explain,
        test_vlog,
        test_brand_promo,
        test_auto_recognition,
        test_mixed_generation
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n\n{'='*20} 测试 {i}/{len(tests)} {'='*20}")
        test()
        
        if i < len(tests):
            print("\n⏸️  按Enter继续下一个测试...")
            input()
    
    print("\n\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

def test_single_case():
    """测试单个用例（用于快速测试）"""
    print("\n🚀 快速测试 - 30秒产品广告")
    
    request_data = {
        "natural_language": "制作一个30秒的产品介绍视频，展示产品特点，要有科技感",
        "video_url": "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "mode": "sync",
        "use_aura_render": True,
        "output_duration": 30
    }
    
    print(f"请求内容：")
    print(json.dumps(request_data, ensure_ascii=False, indent=2))
    
    return send_request(request_data)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # 快速测试单个用例
        test_single_case()
    else:
        # 运行所有测试
        run_all_tests()
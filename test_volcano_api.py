#!/usr/bin/env python3
"""
火山引擎API测试脚本
演示如何使用真实的火山引擎视频编辑API
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

from core.clipeffects.volcano_effects import create_volcano_effects


def test_volcano_api_auth():
    """测试火山引擎API认证"""
    print("🔐 测试火山引擎API认证")
    print("=" * 60)
    
    # 从环境变量或配置文件读取密钥
    # 注意：请勿在代码中硬编码密钥！
    access_key_id = os.environ.get('VOLCANO_ACCESS_KEY_ID', 'your_access_key_id')
    secret_access_key = os.environ.get('VOLCANO_SECRET_ACCESS_KEY', 'your_secret_access_key')
    
    if access_key_id == 'your_access_key_id':
        print("⚠️  请设置环境变量:")
        print("   export VOLCANO_ACCESS_KEY_ID=你的访问密钥ID")
        print("   export VOLCANO_SECRET_ACCESS_KEY=你的访问密钥Secret")
        print("\n📝 获取密钥步骤:")
        print("   1. 登录火山引擎控制台: https://console.volcengine.com")
        print("   2. 进入'密钥管理'页面")
        print("   3. 创建新的访问密钥")
        print("   4. 保存密钥信息并设置环境变量")
        return None
    
    print(f"✅ 访问密钥ID: {access_key_id[:10]}...")
    print(f"✅ 访问密钥Secret: {'*' * 20}")
    
    # 创建火山引擎特效管理器
    volcano = create_volcano_effects(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key
    )
    
    print(f"✅ API配置:")
    print(f"   - 服务区域: {volcano.region}")
    print(f"   - API地址: {volcano.api_url}")
    print(f"   - API版本: {volcano.api_version}")
    
    return volcano


def test_api_connectivity(volcano):
    """测试API连通性"""
    print(f"\n🌐 测试API连通性")
    print("=" * 60)
    
    try:
        # 构建测试请求
        test_body = json.dumps({
            "Action": "ListMediaInfo",
            "Version": volcano.api_version,
            "Limit": 1
        })
        
        headers = volcano._get_signed_headers("POST", "/", test_body)
        
        print(f"📡 发送测试请求...")
        response = requests.post(
            f"{volcano.api_url}/",
            headers=headers,
            data=test_body,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "ResponseMetadata" in result:
                error = result["ResponseMetadata"].get("Error")
                if error:
                    print(f"❌ API错误: {error}")
                    if error.get("Code") == "SignatureDoesNotMatch":
                        print("   提示: 请检查访问密钥是否正确")
                else:
                    print(f"✅ API连接成功")
                    return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
    
    return False


def prepare_video_for_api(video_path):
    """准备视频文件用于API调用"""
    print(f"\n📦 准备视频文件")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return None
    
    # 火山引擎通常需要先上传视频到他们的存储服务
    print(f"📁 本地视频: {video_path}")
    print(f"   - 大小: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
    
    print(f"\n💡 提示: 火山引擎视频编辑通常需要:")
    print(f"   1. 先将视频上传到火山引擎存储 (TOS)")
    print(f"   2. 获取视频的 FileId 或 URL")
    print(f"   3. 使用 FileId/URL 调用编辑API")
    
    # 这里返回一个模拟的FileId
    # 实际使用时需要通过火山引擎存储API上传视频
    return {
        "FileId": "simulated_file_id_12345",
        "LocalPath": video_path,
        "Url": "tos://your-bucket/videos/test.mp4"
    }


def test_direct_edit_api(volcano, video_info):
    """测试直接编辑API"""
    print(f"\n🎬 测试直接编辑API")
    print("=" * 60)
    
    # 构建编辑参数
    edit_params = {
        "TemplateId": "system:direct_edit",  # 系统模板
        "CallbackUrl": "",  # 回调URL（可选）
        "EditParam": {
            # 视频轨道
            "VideoTrack": [{
                "VideoTrackClips": [{
                    "Type": "video",
                    "Source": {
                        "Type": "file",
                        "FileId": video_info["FileId"]
                    },
                    "Timeline": {
                        "Start": 0,
                        "Duration": 5000  # 5秒，单位毫秒
                    },
                    "Operations": []
                }]
            }],
            
            # 添加转场效果
            "GlobalOperations": [{
                "Type": "transition",
                "Config": {
                    "Name": "1182355",  # 叶片翻转转场
                    "Duration": 1000  # 1秒
                }
            }],
            
            # 输出参数
            "Output": {
                "Format": "mp4",
                "VideoCodec": "h264",
                "AudioCodec": "aac",
                "Resolution": "1080x1920",
                "Fps": 30,
                "Bitrate": 5000000  # 5Mbps
            }
        }
    }
    
    print(f"📋 编辑配置:")
    print(f"   - 视频源: {video_info['FileId']}")
    print(f"   - 转场效果: 叶片翻转 (ID: 1182355)")
    print(f"   - 输出格式: MP4 1080x1920 @30fps")
    
    # 调用API
    print(f"\n🚀 提交编辑任务...")
    
    # 模拟API调用结果
    print(f"⚠️  模拟模式: 实际API调用需要有效的密钥和上传的视频")
    
    mock_result = {
        "TaskId": f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "Status": "Processing",
        "CreateTime": datetime.now().isoformat()
    }
    
    print(f"✅ 任务已提交:")
    print(f"   - 任务ID: {mock_result['TaskId']}")
    print(f"   - 状态: {mock_result['Status']}")
    print(f"   - 创建时间: {mock_result['CreateTime']}")
    
    return mock_result


def demonstrate_api_workflow():
    """演示完整的API工作流程"""
    print(f"\n📚 火山引擎视频编辑API工作流程")
    print("=" * 60)
    
    print("""
1️⃣ 准备阶段:
   - 获取火山引擎访问密钥
   - 配置存储服务 (TOS)
   - 准备待编辑的视频文件

2️⃣ 上传视频:
   ```python
   # 使用火山引擎 TOS SDK 上传视频
   import tos
   
   client = tos.TosClientV2(ak, sk, endpoint, region)
   client.put_object_from_file(bucket, key, file_path)
   ```

3️⃣ 创建编辑任务:
   ```python
   # 构建编辑参数
   edit_param = {
       "VideoTrack": [...],  # 视频轨道
       "AudioTrack": [...],  # 音频轨道
       "GlobalOperations": [  # 全局特效
           {
               "Type": "filter",
               "Config": {"Name": "1184003"}  # 清晰滤镜
           }
       ]
   }
   
   # 提交任务
   response = volcano.submit_direct_edit_task(file_id, edit_param)
   task_id = response["TaskId"]
   ```

4️⃣ 查询任务状态:
   ```python
   # 轮询任务状态
   while True:
       result = volcano.get_direct_edit_result(task_id)
       if result["Status"] in ["Success", "Failed"]:
           break
       time.sleep(5)
   ```

5️⃣ 获取结果:
   ```python
   if result["Status"] == "Success":
       output_url = result["OutputUrl"]
       # 下载或使用编辑后的视频
   ```
""")


def test_effect_combinations():
    """测试特效组合"""
    print(f"\n🎨 特效组合示例")
    print("=" * 60)
    
    examples = [
        {
            "name": "抖音风格短视频",
            "effects": [
                {"type": "filter", "id": "1183991", "name": "香港滤镜"},
                {"type": "transition", "id": "1182367", "name": "故障转换"},
                {"type": "text_animation", "id": "1181434", "name": "文字渐显"}
            ]
        },
        {
            "name": "产品展示视频",
            "effects": [
                {"type": "filter", "id": "1184003", "name": "清晰滤镜"},
                {"type": "transition", "id": "1182355", "name": "叶片翻转"},
                {"type": "video_animation", "id": "1180338", "name": "放大入场"}
            ]
        },
        {
            "name": "美食分享视频",
            "effects": [
                {"type": "filter", "id": "1183953", "name": "暖食滤镜"},
                {"type": "transition", "id": "1182376", "name": "圆形打开"},
                {"type": "effect", "id": "1188885", "name": "四分屏展示"}
            ]
        }
    ]
    
    for example in examples:
        print(f"\n📹 {example['name']}:")
        for effect in example['effects']:
            print(f"   - {effect['type']}: {effect['name']} (ID: {effect['id']})")


def create_api_test_script():
    """创建API测试脚本模板"""
    print(f"\n📝 生成API测试脚本模板")
    print("=" * 60)
    
    script_content = '''#!/usr/bin/env python3
"""
火山引擎视频编辑API测试脚本
请根据您的实际需求修改此脚本
"""

import os
import json
import time
import volcengine

# 配置您的访问密钥
ACCESS_KEY_ID = os.environ.get('VOLCANO_ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.environ.get('VOLCANO_SECRET_ACCESS_KEY')

# 初始化客户端
client = volcengine.Client(
    access_key_id=ACCESS_KEY_ID,
    secret_access_key=SECRET_ACCESS_KEY,
    region='cn-north-1',
    service='vod'
)

def upload_video(local_path):
    """上传视频到火山引擎"""
    # 1. 申请上传
    response = client.request('ApplyUploadInfo', {
        'FileType': 'video',
        'FileExtension': '.mp4'
    })
    
    upload_info = response['Result']
    
    # 2. 上传文件
    # 使用返回的上传地址上传文件
    
    return upload_info['FileId']

def create_edit_task(file_id):
    """创建编辑任务"""
    edit_param = {
        "VideoTrack": [{
            "VideoTrackClips": [{
                "Type": "video",
                "Source": {"Type": "file", "FileId": file_id},
                "Timeline": {"Start": 0, "Duration": 5000}
            }]
        }],
        "GlobalOperations": [{
            "Type": "filter",
            "Config": {"Name": "1184003"}  # 清晰滤镜
        }]
    }
    
    response = client.request('SubmitDirectEditTaskAsync', {
        'EditParam': json.dumps(edit_param)
    })
    
    return response['Result']['TaskId']

def main():
    # 1. 上传视频
    file_id = upload_video('test_video.mp4')
    print(f"视频已上传: {file_id}")
    
    # 2. 创建编辑任务
    task_id = create_edit_task(file_id)
    print(f"编辑任务已创建: {task_id}")
    
    # 3. 等待任务完成
    while True:
        response = client.request('GetDirectEditResult', {'TaskId': task_id})
        status = response['Result']['Status']
        
        if status == 'Success':
            output_url = response['Result']['OutputUrl']
            print(f"编辑完成: {output_url}")
            break
        elif status == 'Failed':
            print("编辑失败")
            break
        
        time.sleep(5)

if __name__ == "__main__":
    main()
'''
    
    # 保存模板脚本
    template_path = "volcano_api_template.py"
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ 模板已保存到: {template_path}")
    print(f"   请根据您的实际需求修改此脚本")


def main():
    """主测试函数"""
    print("🚀 火山引擎视频编辑API测试")
    print("=" * 60)
    
    # 1. 测试API认证
    volcano = test_volcano_api_auth()
    
    if volcano:
        # 2. 测试API连通性
        if test_api_connectivity(volcano):
            # 3. 准备测试视频
            video_path = "/Users/luming/Downloads/老登.mp4"
            video_info = prepare_video_for_api(video_path)
            
            if video_info:
                # 4. 测试编辑API
                test_direct_edit_api(volcano, video_info)
    
    # 5. 演示API工作流程
    demonstrate_api_workflow()
    
    # 6. 展示特效组合
    test_effect_combinations()
    
    # 7. 创建测试脚本模板
    create_api_test_script()
    
    print(f"\n📌 重要提示:")
    print(f"   1. 使用真实API需要有效的火山引擎账号和密钥")
    print(f"   2. 视频需要先上传到火山引擎存储服务")
    print(f"   3. 编辑任务是异步的，需要轮询获取结果")
    print(f"   4. 详细文档: https://www.volcengine.com/docs/4/102412")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
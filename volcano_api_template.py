#!/usr/bin/env python3
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

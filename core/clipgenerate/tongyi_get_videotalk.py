import requests
import json
import os
import time
from dotenv import load_dotenv

from core.utils.env_config import get_dashscope_api_key

video_path = "03.mp4"  # 替换为你的视频文件路径
# video_url = get_online_url(video_path)  # 上传视频并获取公网URL
audio_url = "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/29bf1e90a1db4c21ac7f1ef52296f0ea.mp3"

# 从文件获取 API 密钥
API_KEY = get_dashscope_api_key()
if not API_KEY:
    raise ValueError("API Key 未配置，请设置 DASHSCOPE_API_KEY 环境变量或检查 api_key.txt 文件")


def get_insert_videotalk_task(video_url, audio_url):
    """获取视频合成任务"""
    # 设置请求的URL和头部信息

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"

    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-OssResourceResolve": "enable"
    }

    data = {
        "model": "videoretalk",
        "input": {
            "video_url": video_url,
            "audio_url": audio_url,
            "ref_image_url": ""
        },
        "parameters": {
            "video_extension": False
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 打印响应结果
    print("Status Code:", response.status_code)
    print("Response Body:", response.text)
    if response.status_code != 200:
        raise Exception(f"Failed to get task: {response.text}")

    response_json = response.json()
    task_id = response_json['output']['task_id']
    task_status = response_json['output']['task_status']
    return task_id


def get_videotalk_task_result(TASK_ID):
    url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{TASK_ID}"

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    def get_task_result(task_id):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            result = response.json()
            print("Task result:", result)
            # 检查任务是否完成，不同API返回的任务状态字段可能不同，请根据实际情况调整
            if 'task_status' in result['output'] and result['output']['task_status'] in ['SUCCEEDED', 'completed']:
                return result['output']['video_url']
            elif 'task_status' in result['output'] and result['output']['task_status'] == 'FAILED':
                print("Task failed.")
                return False
        else:
            print(f"Received status code {response.status_code}")
            return None

    # 轮询间隔时间（秒）
    poll_interval = 5

    while True:
        print(f"Polling task status, waiting for {poll_interval} seconds...")
        time.sleep(poll_interval)
        result = get_task_result(TASK_ID)
        if result:
            print("Task completed successfully!")
            print("Result:", result)
            return result
            break
        elif result == False:
            print("Task completed FAILED!")
            print("Result:", result)
            break
        # 如果需要更复杂的错误处理或者超时机制，可以在此扩展


def get_videotalk(video_url, audio_url):
    task_id = get_insert_videotalk_task(video_url, audio_url)
    print("Task ID:", task_id)
    result_url = get_videotalk_task_result(task_id)
    return result_url

# video_url="oss://dashscope-instant/199c0377709dff7f853b95132d561dfe/2025-05-01/895f83e1-39cb-999c-baf6-897db720b69e/03.mp4"
# video_path="04.mp4"  # 替换为你的视频文件路径
# video_url=get_online_url(video_path)  # 上传视频并获取公网URL
# audio_url="https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/29bf1e90a1db4c21ac7f1ef52296f0ea.mp3"
# res=get_videotalk(video_url, audio_url)
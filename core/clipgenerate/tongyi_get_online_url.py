import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
from get_api_key import get_api_key_from_file


def get_upload_policy(api_key, model_name):
    """获取文件上传凭证"""
    url = "https://dashscope.aliyuncs.com/api/v1/uploads"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    params = {
        "action": "getPolicy",
        "model": model_name
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get upload policy: {response.text}")

    return response.json()['data']


def oss_to_http_url(oss_path, oss_domain):
    """
    将 OSS 地址转换为基于提供的 OSS 域名的 HTTP(S) URL。

    :param oss_path: str, 如 'oss://bucket-name/object-key'
    :param oss_domain: str, 如 'https://dashscope-file-mgr.oss-cn-beijing.aliyuncs.com'
    :return: str, HTTP(S) URL
    """
    if not oss_path.startswith("oss://"):
        raise ValueError("OSS 路径必须以 oss:// 开头")

    # 去掉 oss://，分割 bucket 和 object key
    path_parts = oss_path[6:].split("/", 1)
    # 注意这里不再需要处理bucket名称，因为我们已经有了完整的域名
    object_key = path_parts[1] if len(path_parts) > 1 else ""

    # 确保对象键前面没有斜杠，如果有的话去掉
    if object_key.startswith("/"):
        object_key = object_key[1:]

    # 拼接完整 URL
    http_url = f"{oss_domain}/{object_key}"

    return http_url


def upload_file_to_oss(policy_data, file_path):
    """将文件上传到临时存储OSS"""
    file_name = Path(file_path).name
    key = f"{policy_data['upload_dir']}/{file_name}"

    with open(file_path, 'rb') as file:
        files = {
            'OSSAccessKeyId': (None, policy_data['oss_access_key_id']),
            'Signature': (None, policy_data['signature']),
            'policy': (None, policy_data['policy']),
            'x-oss-object-acl': (None, policy_data['x_oss_object_acl']),
            'x-oss-forbid-overwrite': (None, policy_data['x_oss_forbid_overwrite']),
            'key': (None, key),
            'success_action_status': (None, '200'),
            'file': (file_name, file)
        }

        response = requests.post(policy_data['upload_host'], files=files)
        if response.status_code != 200:
            raise Exception(f"Failed to upload file: {response.text}")
    oss_url = f"oss://{key}"
    httpurl = oss_to_http_url(oss_url, policy_data['upload_host'])
    return oss_url, httpurl


def upload_file_and_get_url(api_key, model_name, file_path):
    """上传文件并获取公网URL"""
    # 1. 获取上传凭证
    policy_data = get_upload_policy(api_key, model_name)
    # 2. 上传文件到OSS
    oss_url, http_url = upload_file_to_oss(policy_data, file_path)

    return oss_url, http_url


def get_online_url(file_path):
    # 从环境变量中获取API Key 或者 在代码中设置 api_key = "your_api_key"
    # api_key = os.getenv("DASHSCOPE_API_KEY")

    # 替换为你的 API 密钥
    api_key = get_api_key_from_file()
    if not api_key:
        raise Exception("请设置DASHSCOPE_API_KEY环境变量")

    # 设置model名称
    model_name = "qwen-vl-plus"

    # 待上传的文件路径

    try:
        public_url_oss, public_url_http = upload_file_and_get_url(api_key, model_name, file_path)
        expire_time = datetime.now() + timedelta(hours=48)
        print(f"文件上传成功，有效期为48小时，过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"公网URL: {public_url_oss}")
        return public_url_oss, public_url_http

    except Exception as e:
        print(f"Error: {str(e)}")


def get_online_url_self(file_name: str, file_path: str, filetype: str):
    url = "https://agent.cstlanbaai.com/gateway/admin-api/infra/file/upload/private?path=eqiai/dgh_videos"

    headers = {
        'tenant-id': '1',
        'Authorization': 'test1',
        'x-auth-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI1MzczNGU4MDEzYWI0MjI0N2VjMzc5ZjRiNDJhMmNjOCIsInN1YiI6IjUzNzM0ZTgwMTNhYjQyMjQ3ZWMzNzlmNGI0MmEyY2M4IiwiaWF0IjoxNzMyMDY2MjA2LCJyb2xlcyI6W10sImF1dGhvcml0aWVzIjpbXSwiZXhwIjoxNzMyNjcxMDA2fQ.FvwxMpuGlxmIi1o4oCdMLxBwWVqluvYuFYSp0f4uiIs',
    }

    # 打开并读取文件
    with open(file_path, 'rb') as f:
        # 准备文件数据
        files = {
            'file': (file_name, f, filetype)  # 根据实际情况修改文件名和MIME类型
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, files=files)

    print('Status Code:', response.status_code)
    print('Response Body:', response.text)
    res = response.json()["data"]["tempUrl"]
    return res


# 使用示例
if __name__ == "__main__":
    # # 从环境变量中获取API Key 或者 在代码中设置 api_key = "your_api_key"
    # api_key = os.getenv("DASHSCOPE_API_KEY")
    # if not api_key:
    #     raise Exception("请设置DASHSCOPE_API_KEY环境变量")

    # # 设置model名称
    # model_name="qwen-vl-plus"

    # # 待上传的文件路径
    # file_path = "03.mp4"  # 替换为实际文件路径

    # try:
    #     public_url = upload_file_and_get_url(api_key, model_name, file_path)
    #     expire_time = datetime.now() + timedelta(hours=48)
    #     print(f"文件上传成功，有效期为48小时，过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
    #     print(f"公网URL: {public_url}")

    # except Exception as e:
    #     print(f"Error: {str(e)}")
    # get_online_url_self("优帮logo.png","优帮logo.png","image/png")
    get_online_url_self("03.mp4", "03.mp4", "video/mp4")
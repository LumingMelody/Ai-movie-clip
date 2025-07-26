# -*- coding: utf-8 -*-
"""
OSS 配置文件
注意：请将此文件添加到 .gitignore 中，避免泄露密钥
"""

import os

# 从环境变量或配置文件读取密钥
# 优先使用环境变量，其次使用配置文件
OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', 'YOUR_ACCESS_KEY_ID')
OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', 'YOUR_ACCESS_KEY_SECRET')
OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', 'lan8-e-business')

# 如果环境变量未设置，尝试从本地配置文件读取
if OSS_ACCESS_KEY_ID == 'YOUR_ACCESS_KEY_ID':
    try:
        # 尝试从 .env 文件读取
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_file = os.path.join(project_root, '.env')
        
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith('#') or '=' not in line:
                        continue
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'OSS_ACCESS_KEY_ID':
                        OSS_ACCESS_KEY_ID = value
                    elif key == 'OSS_ACCESS_KEY_SECRET':
                        OSS_ACCESS_KEY_SECRET = value
                    elif key == 'OSS_ENDPOINT':
                        OSS_ENDPOINT = value
                    elif key == 'OSS_BUCKET_NAME':
                        OSS_BUCKET_NAME = value
    except:
        pass

# 文件夹配置
VIDEO_OSS_FOLDER = 'agent/resource/video/'
ADS_OSS_FOLDER = 'ads/'
OUTPUT_OSS_FOLDER = 'agent/resource'
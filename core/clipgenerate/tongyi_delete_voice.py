# -*- coding: utf-8 -*-
# @Time    : 2025/7/25 10:53
# @Author  : 蔍鸣霸霸
# @FileName: tongyi_delete_voice.py
# @Software: PyCharm
# @Blog    ：只因你太美

import os
import dashscope
from dashscope.audio.tts_v2 import VoiceEnrollmentService
from main import get_api_key_from_file

dashscope.api_key = get_dashscope_api_key()  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
prefix = 'prefix' # 请按实际情况进行替换

# 创建语音注册服务实例
service = VoiceEnrollmentService()

voices = service.list_voices(prefix=prefix, page_index=0, page_size=10)
print("request id为：", service.get_last_request_id())
print(f"查询到的音色为：{voices}")
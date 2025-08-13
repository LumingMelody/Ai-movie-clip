from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
from core.clipgenerate.tongyi_get_online_url import get_online_url
import dashscope
import os
from moviepy import VideoFileClip

from core.utils.env_config import get_dashscope_api_key

target_model = "cosyvoice-v2"

def get_voice_copy_disposable(aduio_url,content,project_path):
   
    # voiceEnrollmentService=VoiceEnrollmentService()
    # voice_id=voiceEnrollmentService.create_voice("cosyvoice-v2","temp",aduio_url)
    dashscope.api_key = get_dashscope_api_key()  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换

    url = aduio_url  # 请按实际情况进行替换
    prefix = 'prefix'
    target_model = "cosyvoice-v2"

    # 创建语音注册服务实例
    service = VoiceEnrollmentService()

    # 调用create_voice方法复刻声音，并生成voice_id
    # 避免频繁调用 create_voice 方法。每次调用都会创建新音色，每个阿里云主账号最多可复刻 1000 个音色，超额时请删除不用的音色或申请扩容。
    voice_id = service.create_voice(target_model=target_model, prefix=prefix, url=url)
    print("requestId: ", service.get_last_request_id())
    print(f"your voice id is {voice_id}")

    # 使用复刻的声音进行语音合成
    synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)
    audio = synthesizer.call(content)
    print("requestId: ", synthesizer.get_last_request_id())
    output_path_audio=os.path.join(project_path,"output.mp3")
    # 将合成的音频文件保存到本地文件
    with open(output_path_audio, "wb") as f:
        f.write(audio)
    service.delete_voice(voice_id)
    return output_path_audio

def generate_voice_copy(voice_id,content,project_path):
    service = VoiceEnrollmentService()
    print("requestId: ", service.get_last_request_id())
    print(f"your voice id is {voice_id}")

    # 使用复刻的声音进行语音合成
    synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)
    audio = synthesizer.call(content)
    print("requestId: ", synthesizer.get_last_request_id())
    output_path_audio=os.path.join(project_path,"output.mp3")
    # 将合成的音频文件保存到本地文件
    with open(output_path_audio, "wb") as f:
        f.write(audio)
    return output_path_audio


def create_voice_copy(aduio_url):
    dashscope.api_key = get_dashscope_api_key()
    url = aduio_url  # 请按实际情况进行替换
    prefix = 'prefix'
    
    # 创建语音注册服务实例
    service = VoiceEnrollmentService()

    # 调用create_voice方法复刻声音，并生成voice_id
    # 避免频繁调用 create_voice 方法。每次调用都会创建新音色，每个阿里云主账号最多可复刻 1000 个音色，超额时请删除不用的音色或申请扩容。
    voice_id = service.create_voice(target_model=target_model, prefix=prefix, url=url)
    return voice_id


def delete_voice_copy(voice_id):
    dashscope.api_key = get_dashscope_api_key()  # 如果您没有配置环境变量，请在此处用您的API-KEY进行替换
    service = VoiceEnrollmentService()
    service.delete_voice(voice_id)
    print("requestId: ", service.get_last_request_id())
    return True
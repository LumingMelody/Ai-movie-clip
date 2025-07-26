from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer

from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url,get_online_url_self
from core.clipgenerate.tongyi_get_voice_copy import get_voice_copy_disposable,generate_voice_copy,create_voice_copy,delete_voice_copy
from core.clipgenerate.tongyi_response import get_Tongyi_response
from core.clipgenerate.tongyi_get_videotalk import get_videotalk
import dashscope
import os
import uuid
from moviepy import *
import requests
import random
import json

import re

def split_text_by_punctuation(text, remove_empty=True):
    """
    根据常见中英文标点符号对文本进行切分
    :param text: 输入文本
    :param remove_empty: 是否移除空字符串结果
    :return: 切分后的句子列表
    """
    # 正则模式：匹配所有常见标点作为分隔符
    pattern = r'[。！？:，]+'
    
    # 使用正则切分
    parts = re.split(pattern, text)
    
    # 去除首尾空白并过滤空字符串
    if remove_empty:
        parts = [p.strip() for p in parts if p.strip()]
    else:
        parts = [p.strip() for p in parts]
    
    return parts



# 支持的视频扩展名（可按需添加）
# VIDEO_EXTS = {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv'}
VIDEO_EXTS = {'.mp4'}


def get_video_files(folder):
    """ 获取文件夹中所有视频文件 """
    videos = []
    for root, _, files in os.walk(folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VIDEO_EXTS:
                videos.append(os.path.join(root, file))
    return videos

def random_video_picker(filepath,videos=None):
    """ 随机选择器生成器，用完自动打乱重来 """
    while True:
        if not videos:
            videos = get_video_files(filepath)
            random.shuffle(videos)
        yield videos.pop()


def calculate_text_durations(video_duration, text_list):
    # 计算所有文本的总字符数
    total_chars = sum(len(text) for text in text_list)
    
    # 创建一个列表用于存储每个文本及其对应的持续时间
    text_durations = []
    
    # 遍历每个文本，并根据其字符数占总字符数的比例分配视频时长
    for text in text_list:
        char_count = len(text)
        duration = (char_count / total_chars) * video_duration
        text_durations.append({"text": text, "duration": duration})
    
    return text_durations




def get_video_digital_huamn_clips(video_file_path,topic,audio_path,content=None,)->str:
    project_id=str(uuid.uuid1())
    # base_project_path="projects"
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path=os.path.join(base_project_path,project_id)
    os.makedirs(project_path,exist_ok=True)

    if content is None:
        content=get_Tongyi_response("你是一个口播稿生成师，我给你一个主题，你生成一段120字左右的口播稿","主题是"+topic)

    contents_response=get_Tongyi_response("你是一个语义分段师，我给你一段文本，你将其切分成不超过30字的数组段给我，以json返回，不要包含其他内容，返回示例:\"contents\":[\"段落1\",\"段落2\",\"段落3\"]","你要切分的段落是"+content)

    contents=json.loads(contents_response[contents_response.find("{"):contents_response.rfind("}")+1])["contents"]

    # online_url=get_online_url(file_path)
    audio_url=get_online_url_self(audio_path.split("//")[-1],audio_path,"audio/mp3")

    voice_id=create_voice_copy(audio_url)


    rv_picker=random_video_picker(video_file_path)

    
    def download_file(url, filename):

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            filename=os.path.join(project_path, filename)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    
    compostive_list=[]
    i=0
    for c in contents:
        c_c=split_text_by_punctuation(c)
        video_path=next(rv_picker)
        
        
        output_audio_path=generate_voice_copy(voice_id,c,project_path)
        output_audio_url=get_online_url_self(output_audio_path.split("//")[-1],output_audio_path,"audio/mp3")
        # audio_clip_temp=AudioFileClip(output_audio_path)
        # video_clip_temp=VideoFileClip(video_path)
        # if video_clip_temp.duration<audio_clip_temp.duration:
        #     audio_clip_temp
            # speed_factor = video_clip_temp.duration / audio_clip_temp.duration
            # video_clip_temp=video_clip_temp.with_speed_scaled(speed_factor).without_audio()
            # temp_path=os.path.join(project_path,"temp_video"+str(i)+".mp4")
            # video_clip_temp.write_videofile(temp_path, fps=24, codec="libx264")
            # video_path=temp_path

        video_url=get_online_url_self(video_path.split("//")[-1],video_path,"video/mp4")
        while True:
            try:
                digital_human_url=get_videotalk(video_url,output_audio_url)
                video_clip=VideoFileClip(download_file(digital_human_url, "dgh"+str(i)+".mp4"))
                break
            except Exception as e:
                print(e)
            
        audio_clip=AudioFileClip(output_audio_path)
        video_clip.with_audio(audio_clip)
        total_chars = sum(len(text) for text in c_c)
        texts=[]
        for c_cs in c_c:
            
           
            text_c= TextClip(
                "微软雅黑.ttf",
                c_cs,
                font_size=60,
                color='yellow',   # 中文字体需支持中文（如 Windows 上可用 SimHei）
                stroke_color='black',
                stroke_width=1
            ).with_duration((len(c_cs)/total_chars)*audio_clip.duration)
            texts.append(text_c)
        text_cs = concatenate_videoclips(texts)
        comp_clip=CompositeVideoClip([video_clip,text_cs.with_position(("center",0.8),relative=True)])
        compostive_list.append(comp_clip)
        i=i+1
    
    # output_audio_url=get_online_url_self(output_audio.split("//")[-1],output_audio,"audio/mp3")
    # digital_human_url=get_videotalk(video_url,output_audio_url)
    # video_clip=VideoFileClip(download_file(digital_human_url, "dgh.mp4"))
    # audio_clip=AudioFileClip(output_audio)
    # video_clip.with_audio(audio_clip)
    video_clip=concatenate_videoclips(compostive_list)
    output_path=os.path.join(project_path,"output.mp4")
    video_clip.write_videofile(output_path, codec="libx264", fps=24)
    return output_path
    
# def get_video_digital_huamn_easy_local(file_path:str,topic,content=None,audio_path=None)->str:
#     http_url=get_online_url_self(file_path.split("\\")[-1],file_path,"videp/mp4")
#     audio_url=get_online_url_self(audio_path.split("\\")[-1],audio_path,"audio/mp3")
#     output_path=get_video_digital_huamn_clips(http_url,topic,content,audio_url=audio_url)
#     return output_path

if __name__ == "__main__":
    url="序列 01_4.mp4"
    topic="财税知识"
    clip=VideoFileClip(url)
    output_mp3="output.mp3"
    clip.audio.write_audiofile(output_mp3)
    # output_path=get_video_digital_huamn_easy_local(url,topic,audio_path=output_mp3)
    output_path=get_video_digital_huamn_clips("temp\clips","兵之家","temp\clips\序列 08.mp3",'''餐饮老板您好！我们是昆山兵之家创业孵化基地旗下的当鲜仓，专注于饭店、食堂的食材配送，涵盖海鲜品类。我们平台的创立旨在解决军人就业问题，助力他们快速适应职场环境，实现从“橄榄绿”到“职场精英”的转变，在新领域续写辉煌。让军人成为全社会尊崇的职业，为退伍军人打造坚实社会后盾，也是我们始终践行的使命。   在运营模式上，我们深耕传统行业供应链管理领域，以创新商业模式为驱动，打造了集仓储管理、食材配送、拍摄剪辑上视频，客户服务于一体的专业化供应链服务平台。   我们的核心优势在于以解决军人就业为首要目标，而非单纯追求利益；价格方面，通过集中采购，发挥量大价优的优势；服务上，提供每日送货的便利。
 ''')
    # print("")

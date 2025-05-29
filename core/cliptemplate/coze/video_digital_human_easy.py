from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
from tongyi_get_online_url import get_online_url,get_online_url_self
from tongyi_get_voice_copy import get_voice_copy_disposable
from tongyi_response import get_Tongyi_response
from tongyi_get_videotalk import get_videotalk
import dashscope
import os
import uuid
from moviepy import *
import requests


# file_path = "C:/Users/Administrator/Desktop/1.mp3"

def get_video_digital_huamn_easy(video_url,topic,content=None,audio_url:str=None)->str:
    project_id=str(uuid.uuid1())
    base_project_path="projects"
    project_path=os.path.join(base_project_path,project_id)
    os.makedirs(project_path,exist_ok=True)

    if content is None:
        content=get_Tongyi_response("你是一个口播稿生成师，我给你一个主题，你生成一段120字左右的口播稿","主题是"+topic)
    # online_url=get_online_url(file_path)
    if audio_url is None:
        output_audio=get_voice_copy_disposable(video_url,content,project_path)
    else:
        output_audio=get_voice_copy_disposable(audio_url,content,project_path)

    def download_file(url, filename):

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            filename=os.path.join(project_path, filename)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    
    output_audio_url=get_online_url_self(output_audio.split("//")[-1],output_audio,"audio/mp3")
    digital_human_url=get_videotalk(video_url,output_audio_url)
    video_clip=VideoFileClip(download_file(digital_human_url, "dgh.mp4"))
    audio_clip=AudioFileClip(output_audio)
    
    video_clip.with_audio(audio_clip)
    output_path=os.path.join(project_path,"output.mp4")
    video_clip.write_videofile(output_path, codec="libx264", fps=24)
    return output_path
    
def get_video_digital_huamn_easy_local(file_path:str,topic,content=None,audio_path=None)->str:
    http_url=get_online_url_self(file_path.split("\\")[-1],file_path,"videp/mp4")
    audio_url=get_online_url_self(audio_path.split("\\")[-1],audio_path,"audio/mp3")
    output_path=get_video_digital_huamn_easy(http_url,topic,content,audio_url=audio_url)
    return output_path

if __name__ == "__main__":
    url="序列 01_4.mp4"
    topic="财税知识"
    clip=VideoFileClip(url)
    output_mp3="output.mp3"
    clip.audio.write_audiofile(output_mp3)
    output_path=get_video_digital_huamn_easy_local(url,topic,audio_path=output_mp3)
    print(output_path)

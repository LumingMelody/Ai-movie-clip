import requests
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip, afx,concatenate_audioclips,TextClip,CompositeVideoClip,VideoFileClip
import uuid
import os

from config import get_resource_path, get_user_data_dir

# JSON数据
data1= {
  "audio_durations": [
    9888000,
    7488000,
    5160000
  ],
  "audio_lists": [
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265134768179_1e9543f2-fee5-4b32-b0e5-de84f85b34a1.mp3?lk3s=da27ec82&x-expires=1745067315&x-signature=t6rh8aqVibpzEdiOscWjFQ5tJWA%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265134768179_acffbe1b-80e4-429e-86bc-3e8e506455f3.mp3?lk3s=da27ec82&x-expires=1745067315&x-signature=bp%2Fdy4qZB%2FOwhJOmYXBC3VXySSk%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265134768179_abf5c766-acb1-4165-bd81-5ed503dfdf59.mp3?lk3s=da27ec82&x-expires=1745067314&x-signature=rve%2Bw1RbHHER8AtIuEl1OwaUqrk%3D"
  ],
  "base_img": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e52a65c1e97148f1a58ad30414d1077b.jpg~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1776161691&x-signature=RZ9IXKiJu1ySr2wW%2F%2FqaCuLC7Sc%3D&x-wf-file_name=v2-311f156bc93f8eeecbde57914439fd6d_720w.jpg",
  "bgm_audio": "https://coze-tmp-file.oss-cn-shenzhen.aliyuncs.com/2025_03_20/732558dd-30dd-402f-880d-3a49f44fc71e.mp3",
  "img_lists": [
    "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/bc/20250419/e736178b/1749f6a2-b73f-4aaa-8377-321b832eeab0_tryon.jpg?Expires=1745150127&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=g%2BDtTXJEmMBdckuaXoRm7S0KZnc%3D",
    "http://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/1d/9c/20250419/e736178b/92f51684-6869-4752-9426-341007bc7d4f_tryon.jpg?Expires=1745150125&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=RfrxNHmEE%2FsNM%2BJeDwAkN5pDgt4%3D"
  ],
  "subtitle_list": [
    {
      "cap": "穿上这件蓝色棉质上衣前，你或许只是人群中平凡的身影。但当它上身，瞬间为你增添清新与优雅。",
      "name": "产品对比分镜",
      "scene": "全景"
    },
    {
      "cap": "在宁静的蓝色调海边咖啡馆，这款上衣让你成为焦点，展现独特魅力。",
      "name": "适配场景 1",
      "scene": "中景"
    },
    {
      "cap": "在充满文艺气息的书店，它也能让你尽显优雅，散发魅力。",
      "name": "适配场景 2",
      "scene": "中景"
    }
  ]
}


def get_trans_video_clothes_diffrent_scene(input:str):
    project_id=str(uuid.uuid1())
    # base_project_path = "projects"
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")

    project_path=os.path.join(base_project_path,project_id)
    os.makedirs(project_path,exist_ok=True)
    # 下载并拼接音频
    audios = []
    for i, audio_url in enumerate(input['audio_lists']):
        response = requests.get(audio_url)
        audio_file_name = os.path.join(project_path,f"audio_{i}.mp3")
        with open(audio_file_name, 'wb') as f:
            f.write(response.content)
        audios.append(AudioFileClip(audio_file_name))
    final_audio = concatenate_audioclips(audios)

    # 下载图片并生成视频片段
    video_clips = []
    video_file_clips=VideoFileClip("openscene.mp4")
    video_clips.append(video_file_clips)

    response_baseimg = requests.get(input["base_img"])
    baseimg_file_name = os.path.join(project_path,"base_img.jpg")
    with open(baseimg_file_name, 'wb') as f:
        f.write(response_baseimg.content)
    oriimg_video_clip = ImageClip(baseimg_file_name, duration=input['audio_durations'][0]/1000000)
    caption_ori=input['subtitle_list'][0]['cap']
    half_caption_ori=int(len(caption_ori)/2)
    txt_clip1_ori = TextClip(font="微软雅黑.ttf",text=caption_ori[:half_caption_ori], font_size=20, color="black",duration=oriimg_video_clip.duration, stroke_color='black')
    txt_clip2_ori = TextClip(font="微软雅黑.ttf",text=caption_ori[half_caption_ori:], font_size=20, color="black",duration=oriimg_video_clip.duration, stroke_color='black')
    video_clip_ori = CompositeVideoClip([oriimg_video_clip,txt_clip1_ori.with_position(("center",0.85), relative=True),txt_clip2_ori.with_position(("center",0.9), relative=True)])
    video_clips.append(video_clip_ori)

    for i, img_url in enumerate(input['img_lists']):
        response = requests.get(img_url)
        img_file_name = os.path.join(project_path,f"img_{i}.jpg")
        with open(img_file_name, 'wb') as f:
            f.write(response.content)
        video_clip = ImageClip(img_file_name, duration=input['audio_durations'][i+1]/1000000)
        caption=input['subtitle_list'][i+1]['cap']
        half_caption=int(len(caption)/2)
        txt_clip1 = TextClip('微软雅黑.ttf',caption[:half_caption], font_size=20, color='black', duration=video_clip.duration, stroke_color='black')
        txt_clip2 = TextClip('微软雅黑.ttf',caption[half_caption:], font_size=20, color='black', duration=video_clip.duration, stroke_color='black')
        # txt_clip = TextClip(font="微软雅黑.ttf",text=data['subtitle_list'][i+1]['cap'], font_size=20, color="white",duration=video_clip.duration)
        video_clip1 = CompositeVideoClip([video_clip, txt_clip1.with_position(("center",0.85), relative=True),txt_clip2.with_position(("center",0.9), relative=True)])
        video_clips.append(video_clip1)

    # 合并视频片段
    final_video = concatenate_videoclips(video_clips,method="compose")

    # 添加背景音乐
    response = requests.get(input['bgm_audio'])
    with open(get_resource_path("bgm.mp3"), 'wb') as f:
        f.write(response.content)
    bgm = AudioFileClip(get_resource_path("bgm.mp3")).subclipped(0, final_audio.duration).with_effects([afx.MultiplyVolume(0.2)]) # 调整背景音乐音量
    final_audio = CompositeAudioClip([final_audio, bgm])
    final_audio=concatenate_audioclips([video_file_clips.audio,final_audio])
    # 设置最终视频的音频轨道
    final_video = final_video.with_audio(final_audio)

    # 输出最终视频文件
    final_video.write_videofile(os.path.join(project_path,"final_video_with_bgm.mp4"), fps=24)

    # 清理资源
    for audio in audios:
        audio.close()
    return os.path.join(project_path,"final_video_with_bgm.mp4")

# if __name__ == "__main__":
#     get_trans_video_clothes_diffrent_scene(input)
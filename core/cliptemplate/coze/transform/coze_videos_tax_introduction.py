import os
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, TextClip, concatenate_audioclips,CompositeAudioClip,afx
import uuid

from config import get_user_data_dir


# 加载json数据（这里直接用字典代替）


def trans_video_tax_news_introduction(data:dict)->str:
  project_id=str(uuid.uuid1())
  # base_project_path="projects"
  user_data_dir = get_user_data_dir()
  base_project_path = os.path.join(user_data_dir, "projects")
  project_path=os.path.join(base_project_path,project_id)
  os.makedirs(project_path,exist_ok=True)
  def download_file(url, local_filename):
      import requests
      with requests.get(url, stream=True) as r:
          r.raise_for_status()
          local_filename=os.path.join(project_path, local_filename)
          with open(local_filename, 'wb') as f:
              for chunk in r.iter_content(chunk_size=8192): 
                  f.write(chunk)
      return local_filename

  # 下载所有资源
  background_audios = [download_file(data['bg_audio'], "bg_audio.mp3")]
  audio_clips = []
  for i, mp3_url in enumerate(data['mp3_urls']):
      audio_clips.append(AudioFileClip(download_file(mp3_url, f"audio_{i}.mp3")))

  image_clips = []
  text_clips = []
  total_duration = 0
  img2_path = download_file(data['images2'], f"img2.png")
  # 创建每个片段的图片、音频和字幕
  for i, (img_url,  text, audio_clip) in enumerate(zip(data['images'], data['texts'], audio_clips)):
      img_path = download_file(img_url, f"img_{i}.png")
      img2_path = img2_path

      # 创建背景图片clip
      background_clip = ImageClip(img2_path,duration=audio_clip.duration)
      
      # 创建前景图片clip
      foreground_clip = ImageClip(img_path,duration=audio_clip.duration)

      # 创建字幕clip
      txt_clip = TextClip('微软雅黑.ttf',text, font_size=36, color="black", duration=audio_clip.duration)
      txt_clip = txt_clip.with_position(("center",0.85), relative=True)

      # 合成当前片段
      # composite_clip = CompositeVideoClip([background_clip, foreground_clip.set_position("center"), txt_clip])
      composite_clip = CompositeVideoClip([background_clip, foreground_clip.with_position("center"), txt_clip])
      
      image_clips.append(composite_clip)
      total_duration += audio_clip.duration

  # 将所有片段拼接起来
  final_video = concatenate_videoclips(image_clips)

  # 处理背景音乐
  background_audio = AudioFileClip(background_audios[0])
  if background_audio.duration > total_duration:
      background_audio = background_audio.subclipped(0, total_duration)
  else:
      # 如果背景音乐时长短于总时长，则循环播放背景音乐直到覆盖整个视频长度
      while background_audio.duration < total_duration:
          background_audio = concatenate_audioclips([background_audio, background_audio.subclipped(0, total_duration - background_audio.duration)])
  final_audio = concatenate_audioclips(audio_clips)

  # 混合音频：将背景音乐和配音混合
  final_audio = CompositeAudioClip([background_audio.with_effects([afx.MultiplyVolume(0.2)]) ,final_audio])

  # 添加最终音频到视频
  final_video = final_video.with_audio(final_audio)

  output_path = os.path.join(project_path, "output.mp4")  
  # 输出最终视频
  final_video.write_videofile(output_path, codec="libx264", fps=24)


if __name__ == "__main__":
  data ={
  "bg_audio": "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oA0MLCbLN8YV62ZPtXg8QKeDzXjnykljnfAuBs",
  "images": [
    "https://s.coze.cn/t/iiIiOu-lbvU/",
    "https://s.coze.cn/t/NZM3vWAwRw0/",
    "https://s.coze.cn/t/bbyv5ANoUO0/",
    "https://s.coze.cn/t/IKnMwYjPqCc/",
    "https://s.coze.cn/t/1qq3-vCrypI/",
    "https://s.coze.cn/t/4YdMsAJAbsI/"
  ],
  "images2": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/d4cb657693ac427aabe70b601f78f6ba.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778754905&x-signature=tiOQlctMl2VM1kCSaVFVsykMPp4%3D",
  "mp3_durations": [
    6.264,
    4.416,
    4.248,
    4.416,
    3.144,
    5.88
  ],
  "mp3_urls": [
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_66d69fd8-b930-490a-8038-2baf07b4757c.mp3?lk3s=da27ec82&x-expires=1747654507&x-signature=OgD94OOtk9b3x5sSlmn9%2Faugkgw%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_be2b5660-2694-45e1-8af9-284d6d72c3a0.mp3?lk3s=da27ec82&x-expires=1747654509&x-signature=zd1q4CPK9fvV1JdpshvWMB2QeVM%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_a914c44c-8c88-4878-a664-8ca7e1784173.mp3?lk3s=da27ec82&x-expires=1747654511&x-signature=34oIUpDmk7iCZV88avnCAoCfS%2Bs%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_f80ec8be-c17a-446a-8f82-ab9f38a17d34.mp3?lk3s=da27ec82&x-expires=1747654514&x-signature=aL5hpFoVP96Z3w7YMaALELq8vJY%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_069cb6f1-49b9-407d-975f-c14844afd1bd.mp3?lk3s=da27ec82&x-expires=1747654515&x-signature=sJZAEONNa5j53IYaesOO2pvXkOo%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_89ea0f52-b697-42a4-9b45-07f4515124d1.mp3?lk3s=da27ec82&x-expires=1747654518&x-signature=JJ%2BBfR5gBrFghbHF5gsFhu%2FKJkg%3D"
  ],
  "texts": [
    "2023年11月，南京市税务局在对一家纺织品制造企业的税务审查中发现，",
    "该企业存在向非农业生产者开具农产品收购发票的情况。",
    "具体表现为从城市零售商处购买羊毛并开具了收购发票。",
    "鉴于此类发票仅能提供给直接从事农业生产的个人，",
    "该企业不得不进行进项税额转出处理，",
    "金额总计达到4.75万元，并补缴了相应的增值税和滞纳金。"
  ]
}
  trans_video_tax_news_introduction(data)
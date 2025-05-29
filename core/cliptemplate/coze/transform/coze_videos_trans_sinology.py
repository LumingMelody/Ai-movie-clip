import os
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip,concatenate_audioclips,VideoFileClip
import uuid

# 加载json数据（这里直接用字典代替）
data1 = {
  "audio_list": [
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_063f07d2-4f2f-49d7-9691-8ad707b97b02.mp3?lk3s=da27ec82&x-expires=1745090947&x-signature=yPyZB8D5c%2Fsh7HYH%2F8%2BtbRij7jU%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_c03c8d8a-d75f-4885-9e5c-9c4f71fa0ac5.mp3?lk3s=da27ec82&x-expires=1745090950&x-signature=bm93pFPuVzhaBJ2UFkzXxjcrzes%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_2cf5d342-0927-4194-93fa-f280febf2fea.mp3?lk3s=da27ec82&x-expires=1745090953&x-signature=%2B5q024zBrjQEePmB1UKLz%2BZTNRo%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_4080dabc-fb8b-46a9-8785-925cb3d817c8.mp3?lk3s=da27ec82&x-expires=1745090957&x-signature=sErw4fWe0NM2PFbA8%2Buo8Q%2BUYLU%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_8b43484e-df55-4762-aefc-341b0113e622.mp3?lk3s=da27ec82&x-expires=1745090959&x-signature=gPRkorS8paELv3vU0NkeQg13KdA%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7468512265151741979_6220de31-368e-410e-8869-4d1ca745ee89.mp3?lk3s=da27ec82&x-expires=1745090962&x-signature=LNwy7314ffo%2BAowxM30%2B4at2%2Fwg%3D"
  ],
  "duration_list": [
    17520000,
    23544000,
    15408000,
    22944000,
    8736000,
    18216000
  ],
  "image_list": [
    "https://s.coze.cn/t/knH-_miAwVQ/",
    "https://s.coze.cn/t/aaza4S3oq6g/",
    "https://s.coze.cn/t/WqH2Wos4tnU/",
    "https://s.coze.cn/t/OOohifF6J2g/",
    "https://s.coze.cn/t/Kq1HiwGDjgI/",
    "https://s.coze.cn/t/VA2Mirnl2wY/"
  ],
  "list": [
    {
      "cap": "中国古典服装是国学宝库中一颗璀璨明珠，承载着深厚文化内涵与传统审美。它不仅是遮体御寒之物，更反映着不同时代的社会风貌、礼仪制度和价值观念。",
      "desc": "画面渐亮，展现一张古朴的书桌，桌上摊开一本线装古籍，旁边放着一支毛笔和一方砚台。镜头慢慢拉近古籍，古籍上绘有各种古典服装的图案。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒古籍、书桌、毛笔和砚台的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于古朴物件之上。背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为一张古朴书桌，桌上摊开绘有古典服装图案的线装古籍，旁边有毛笔和砚台",
      "story_name": "古典服装开篇"
    },
    {
      "cap": "春秋战国时期流行深衣，《礼记·深衣》记载：‘制十有二幅，以应十二月；袂圜以应规，曲袷如矩以应方。’深衣上下连属，象征天人合一、恢宏大度、公平正直和包容万物的东方美德。",
      "desc": "场景切换至古代学堂，夫子站在讲台上，手持竹简讲解，台下学生们认真聆听。画面中出现几位身着深衣的学生走动，深衣上下连属，线条流畅。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒夫子、学生和深衣的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于素衣之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为古代学堂，夫子讲学，身着深衣的学生走动",
      "story_name": "春秋战国深衣"
    },
    {
      "cap": "赵武灵王推行‘胡服骑射’，让士兵着短衣、束皮带、用带钩、穿皮靴，利于骑射活动，这一变革体现了对不同文化的包容与融合。",
      "desc": "画面来到战场，赵武灵王身着短衣、束皮带、用带钩、穿皮靴，骑在战马上指挥士兵操练骑射。士兵们也都穿着同样的胡服，动作整齐划一。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒赵武灵王、士兵和战马的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于胡服之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为战场，赵武灵王骑在马上指挥穿胡服的士兵操练骑射",
      "story_name": "胡服骑射变革"
    },
    {
      "cap": "唐朝是中国古典服装发展的鼎盛时期，女装款式多样，有襦裙、半臂等。当时社会开放，女性服饰色彩鲜艳、图案精美。杨贵妃喜爱华丽服饰，其着装引领时尚潮流，展现出唐朝的繁荣昌盛和自信包容。",
      "desc": "场景转换到唐朝的宫廷花园，杨贵妃身着华丽的襦裙、半臂，色彩鲜艳，图案精美，在花丛中漫步，周围有宫女陪伴。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒杨贵妃、宫女和花园景色的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于华丽服饰之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为唐朝宫廷花园，杨贵妃身着华丽女装漫步，周围有宫女陪伴",
      "story_name": "唐朝女装风采"
    },
    {
      "cap": "而宋代服装则趋于保守，强调端庄、儒雅，体现了理学对社会生活的影响。",
      "desc": "画面呈现宋代的书院，书生们穿着色调淡雅、款式端庄的服装，在书院中读书、讨论。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒书生和书院的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于淡雅服装之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面为宋代书院，书生们穿着端庄服装读书讨论",
      "story_name": "宋代保守服装"
    },
    {
      "cap": "中国古典服装蕴含着丰富的国学智慧，它教会我们尊重传统、包容多元，在当代生活中，我们可从古典服装中汲取灵感，提升个人修养与审美，传承中华民族的文化基因。",
      "desc": "画面回到现代，一位年轻人在博物馆里看着古典服装的展品，若有所思。随后画面切换至年轻人穿着融入古典元素的现代服装，自信地走在街头。",
      "desc_promopt": "Prompt : 采用传统工笔技法绘制，在仿古宣纸纹理背景上呈现具有东方韵味的简逸场景。以墨色骨法勾勒年轻人、博物馆展品和现代街道的轮廓，线条蕴含书法笔意，施以丹青设色之法，着朱砂、石青、赭黄等传统矿物色于服装和场景之上。人物造型取法汉代画像石之简朴动态，背景融入水墨氤氲的祥云纹样，画面四隅点缀金石篆刻印章与梅花小景，整体营造出墨彩交融、文气盎然的古典美学意境. 画面先为年轻人在博物馆看古典服装展品，后为年轻人穿融入古典元素的现代服装走在街头",
      "story_name": "当代传承启示"
    }
  ]
}

def get_trans_video_sinology(input:str):
  project_id=str(uuid.uuid1())
  base_project_path="projects"
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
  audio_clips = [AudioFileClip(download_file(audio_url, f"audio_{i}.mp3")) for i, audio_url in enumerate(input['audio_list'])]
  image_clips = []


  for i, (img_url, duration_ms) in enumerate(zip(input['image_list'], input['duration_list'])):
      img_path = download_file(img_url, f"img_{i}.png")
      img_clip = ImageClip(img_path,duration=duration_ms / 1000000.0)  # 将毫秒转换为秒
      image_clips.append(img_clip)

  # 创建带有字幕的视频片段
  clips_with_captions = []
  for i, (img_clip, item) in enumerate(zip(image_clips, input['list'])):
      caption = item['cap']
      half_caption=int(len(caption)/2)
      txt_clip1 = TextClip('微软雅黑.ttf',caption[:half_caption], font_size=20, color='black', duration=duration_ms/1000000.0)
      txt_clip2 = TextClip('微软雅黑.ttf',caption[half_caption:], font_size=20, color='black', duration=duration_ms/1000000.0)
      # txt_clip = TextClip('微软雅黑.ttf',caption, font_size=20, color='black', duration=img_clip.duration)
      clip_with_caption = CompositeVideoClip([img_clip, txt_clip1.with_position(("center",0.85), relative=True),txt_clip2.with_position(("center",0.9), relative=True)])
      clips_with_captions.append(clip_with_caption)

  # 合并所有视频片段
  final_video = concatenate_videoclips(clips_with_captions)

  # 组合所有音频片段
  final_audio = concatenate_audioclips(audio_clips)

  # 如果音频总时长超过视频时长，则裁剪音频
  if final_audio.duration > final_video.duration:
      final_audio = final_audio.subclipped(0, final_video.duration)
  else:
      # 若视频时长超过音频时长，则重复最后一个音频片段直到覆盖整个视频长度
      while final_audio.duration < final_video.duration:
          final_audio = concatenate_audioclips([final_audio, audio_clips[-1].subclipped(0, final_video.duration - final_audio.duration)])

  # 添加音频到视频
  final_video = final_video.with_audio(final_audio)

  # 输出最终视频
  final_video.write_videofile(os.path.join(project_path,"output.mp4"), fps=24,codec="libx264")
  return os.path.join(project_path,"output.mp4")

if __name__ == "__main__":
  input=data1
  get_trans_video_sinology(input)
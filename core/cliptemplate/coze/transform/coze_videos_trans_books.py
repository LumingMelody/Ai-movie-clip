import os
import uuid
from moviepy import VideoFileClip,concatenate_videoclips, CompositeVideoClip, ImageClip, afx, AudioFileClip, CompositeAudioClip, TextClip,AudioClip,vfx,ColorClip,VideoClip,concatenate_audioclips
from moviepy.video.tools.drawing import color_gradient
from moviepy.video.tools.subtitles import SubtitlesClip

from config import get_user_data_dir

data={
  "bg_audio": "https://coze-tmp-file.oss-cn-shenzhen.aliyuncs.com/2025_03_20/732558dd-30dd-402f-880d-3a49f44fc71e.mp3",
  "images": [
    "https://s.coze.cn/t/wTSgNdfhkc4/",
    "https://s.coze.cn/t/BB7MQs9Sc-8/",
    "https://s.coze.cn/t/UM3I_wB4wII/",
    "https://s.coze.cn/t/nPZLVldjz3U/",
    "https://s.coze.cn/t/_eel83GfSQQ/",
    "https://s.coze.cn/t/OKiKr3i_wJw/",
    "https://s.coze.cn/t/HIZ9AMn5rLQ/",
    "https://s.coze.cn/t/ViCX6GpbmAQ/",
    "https://s.coze.cn/t/WfI5ROnacd8/",
    "https://s.coze.cn/t/D1YDIR7xYdU/",
    "https://s.coze.cn/t/MKlOqTJXKjo/",
    "https://s.coze.cn/t/Za0ovxaMHyc/",
    "https://s.coze.cn/t/Ggm5HA5ZcRg/",
    "https://s.coze.cn/t/Od2eQla0if0/",
    "https://s.coze.cn/t/HxqBzmNqFc0/",
    "https://s.coze.cn/t/DlZ9lM0YVQM/",
    "https://s.coze.cn/t/r_vwRDfICbU/",
    "https://s.coze.cn/t/oqSZNMJ2Mb8/",
    "https://s.coze.cn/t/_e7-CjEvWvI/",
    "https://s.coze.cn/t/jfCkq1m3kW0/"
  ],
  "images_bg": "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/9e9c2d0869b643f2bd82ae2862911cc4.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1776191664&x-signature=A1wPWBRH6ocLLREgL0%2FeEFuMD9g%3D",
  "mp3_durations": [
    6.288,
    4.224,
    6.96,
    6.528,
    5.016,
    6.384,
    5.04,
    7.344,
    6,
    3.312,
    3.624,
    3.984,
    4.56,
    4.8,
    6.192,
    7.584,
    5.952,
    1.776,
    7.584,
    7.704
  ],
  "mp3_urls": [
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_bab4f9db-86a0-49a2-8cb7-97cf793fc9e5.mp3?lk3s=da27ec82&x-expires=1745091265&x-signature=HFUqj7%2FCyyvlcHFVG3m10d8VH8M%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_110872ea-bb9e-468d-99f7-1cbac073f4c7.mp3?lk3s=da27ec82&x-expires=1745091268&x-signature=zjqd0vO8UbCr2o8a0LzPmmSyt00%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_8dbfff45-b0fe-4a6f-92b4-8a7bb326540a.mp3?lk3s=da27ec82&x-expires=1745091271&x-signature=gjUY4MDRgSHj%2BA%2BqxBvHIu41sZA%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_e06d6b88-c169-4d7e-8472-17ea963974d9.mp3?lk3s=da27ec82&x-expires=1745091273&x-signature=HKEFic79WCgG5XOBI3TUrigP8Tk%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_8abfb86e-0f36-4c7b-86bb-1b7612bb70e1.mp3?lk3s=da27ec82&x-expires=1745091275&x-signature=9i1M9S%2B1c91vb%2Bm2meeSIFTVpsc%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d13599e0-e74c-42ab-aca8-d4982f5acf43.mp3?lk3s=da27ec82&x-expires=1745091277&x-signature=NN5A8BDFYCPfd3RhbX%2B0eIOGVoE%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d32d91bc-e549-45b3-81f6-14833a018be4.mp3?lk3s=da27ec82&x-expires=1745091280&x-signature=7N3J0KIkhig%2FMhUgpR5EiO58EIM%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_ba75bb43-54c3-403d-ab7d-6d810575213a.mp3?lk3s=da27ec82&x-expires=1745091283&x-signature=%2B%2FthzAP8wjSA3VyyyO59Nxu6qEE%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_f805c69a-628c-4ce3-9d46-e91f680b0928.mp3?lk3s=da27ec82&x-expires=1745091285&x-signature=NOYFeoP1%2BUbkjmiHzbO1PaEUaKw%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_98286ef6-779a-4e80-b2ea-971a71bae1b9.mp3?lk3s=da27ec82&x-expires=1745091287&x-signature=6Y4ushMfpZ3OiZt7NUuQ3XA8Swo%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_6de82af4-3ac5-4174-a044-3d933a669ce3.mp3?lk3s=da27ec82&x-expires=1745091289&x-signature=nBmgo1SZ27px9Kj0jbUeIBmrbTo%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d707542d-8caf-42c0-b563-e6c428084c84.mp3?lk3s=da27ec82&x-expires=1745091292&x-signature=5K3Vvck8Me87daQ1rGiDbwM5dTw%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_3da460d4-71dd-46b5-98a1-4fa81e9c8d5e.mp3?lk3s=da27ec82&x-expires=1745091294&x-signature=woelPE2Newk%2BJ2q32HBwgbD8W2Q%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_495eace7-57a4-4708-b43d-ac49c5f05055.mp3?lk3s=da27ec82&x-expires=1745091296&x-signature=7kxel1cfGJ2crIvpUa9LumtsWmA%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_55335c8c-2394-487f-9a53-d4352078d5a0.mp3?lk3s=da27ec82&x-expires=1745091298&x-signature=MpVTQR%2BVgS4Vy9SHHgvEP4le22Y%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_107c320e-6d2c-41aa-9643-a66884f27abf.mp3?lk3s=da27ec82&x-expires=1745091301&x-signature=w1EbVktFE%2FEhd2ORMmI2QiKX5nQ%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_42258735-1b56-4df7-a9aa-f2f6dd7cf353.mp3?lk3s=da27ec82&x-expires=1745091303&x-signature=mhJe5oQQFqRlWEpl8CCHLHhYXjs%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_bbe133b4-c9a1-4868-af95-b5e90d4601bb.mp3?lk3s=da27ec82&x-expires=1745091304&x-signature=JYBs%2F93JS4ZX21ahW1eOrBce3ls%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_dba3fe2c-9bba-4855-9f08-d7aad4c7c4cc.mp3?lk3s=da27ec82&x-expires=1745091306&x-signature=buWcLcMJMBzr09gkIy3G1K%2FW7CM%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_0c6f286a-9849-40ec-83d0-7977555a43bc.mp3?lk3s=da27ec82&x-expires=1745091310&x-signature=iAOjTy1RY1f%2BFri12is5AicUCXo%3D"
  ],
  "texts": [
    "你有没有发现，那些真正会穿的女人，衣橱里永远只有三件外套、五条裙子？",
    "秘密就藏在亚历山大·唐纳德写的这本时尚圣经里。",
    "1955年，迪奥先生从巴黎世家三角裙里偷了个灵感，创造出了风靡全球的A字裙。",
    "这条能藏起小肚子、修饰梨形身材的魔法裙，至今仍是纽约名媛衣橱里的战袍。",
    "搭配黑色裤袜蹬双踝靴，下雨天也能穿出赫本式的优雅。",
    "书中揭晓的豹纹穿搭法则堪称教科书级别：永远只用一件动物纹单品。",
    "底色要像拿铁咖啡般柔和，其他配饰必须素净得像清晨的雪地。",
    "想象一下，当你在会议室甩出豹纹手拿包，瞬间就能把黑白套装穿出华尔街女魔头的气场。",
    "更绝的是飞行眼镜的挑选秘诀——去古董市场淘一副二战时期的雷朋原版。",
    "镜腿上的岁月刮痕比任何logo都值钱。",
    "书中藏着个颠覆认知的时尚公式：减即是加。",
    "芭蕾平底鞋要选裸粉色，让脚背成为腿长的延伸。",
    "腰带不是束腰工具，而是分割黄金比例的魔法线。",
    "在oversize毛衣外系条细皮带，瞬间从慵懒变精致。",
    "作者反复强调：真正的时尚不是追着潮流跑，而是找到那件能穿十年的战衣。",
    "就像书中第83件单品——小羊皮机车夹克，二十年后再穿，破洞都是勋章。",
    "这本书最动人的不是百件单品清单，而是教会我们：衣橱是女人的战场。",
    "每件衣服都是盔甲。",
    "当你知道白衬衫要选90支棉、小黑裙必须过膝三公分，这份底气比任何奢侈品都耀眼。",
    "正如唐纳德在书末写的：风格不是天生的，是懂得在纷繁世界里，守住属于自己的那抹剪影。"
  ]
}


def coze_video_transfrom_books(data:dict):
  project_id=str(uuid.uuid1())
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



  # 下载并加载所有资源
  bg_audio_path = download_file(data['bg_audio'], "bg_audio.mp3")
  audio_clips = [AudioFileClip(download_file(mp3_url, f"mp3_{i}.mp3")) for i, mp3_url in enumerate(data['mp3_urls'])]
  image_clips = [ImageClip(download_file(image_url, f"img_{i}.png"),duration=duration) for i, (image_url, duration) in enumerate(zip(data['images'], data['mp3_durations']))]
  background_image = ImageClip(download_file(data['images_bg'], "background.png"),duration=sum(data['mp3_durations']))


  ##以下为测试代码

  # images = []
  # musics = []
  # # 使用函数，传入你的文件夹路径
  # directory = "projects\\6ab33ade-16e9-11f0-8aec-44fa66e560cc"
  # # 加载音频剪辑
  # audio_clips = [AudioFileClip(os.path.join(directory, f)) for f in os.listdir(directory) if f.lower().startswith("mp3")]

  # # 加载图像剪辑
  # image_clips = [ImageClip(os.path.join(directory, img), duration=duration,transparent=True) 
  #                 for img, duration in zip((f for f in os.listdir(directory) if f.lower().startswith("img")), data['mp3_durations'])]
      
  # background_image = ImageClip(os.path.join(directory,"background.png"),duration=sum(data['mp3_durations'][:5]))
  # bg_audio_path = os.path.join(directory, "bg_audio.mp3")

  # image_clips[0].write_videofile(os.path.join(directory, "out2.mp4"), fps=24, codec="libx264", audio_codec="aac")



  # # 打印结果验证
  # print(f"共找到{len(audio_clips)}个音频剪辑，{len(image_clips)}个图像剪辑。")

  # image_clips=image_clips[:5]
  # audio_clips=audio_clips[:5]
  ##以上为测试代码


  # 创建主视频A
  video_a = concatenate_videoclips(image_clips)
  half_w=video_a.w/1.5
  half_h=video_a.h/1.5
  video_a = video_a.resized((half_w, half_h))

  # 将视频A叠加在背景图上
  final_video = CompositeVideoClip([background_image, video_a.with_position(("center", "center"))])
  # final_video.write_videofile(os.path.join(project_path,"output1.mp4"), fps=24, codec="libx264", audio_codec="aac")

  # 组合解说音频
  final_audio:CompositeAudioClip = concatenate_audioclips(audio_clips)

  # 添加背景音乐，并调整音量
  background_music:AudioFileClip =  AudioFileClip(bg_audio_path).subclipped(0, final_audio.duration)

  f_volumn=final_audio.max_volume()
  b_volumn=background_music.max_volume()
  volumn_scale=2*b_volumn/f_volumn

  final_audio = CompositeAudioClip([final_audio.with_effects([afx.MultiplyVolume(1)]), background_music.with_effects([afx.MultiplyVolume(1/volumn_scale)])])

  # 将音频添加到视频中
  final_video:CompositeVideoClip = final_video.with_audio(final_audio)

  temp_path=os.path.join(project_path,"output2.mp4")

  final_video.write_videofile(temp_path, fps=24, codec="libx264")


  # def create_subtitle_clips(subtitles, fontsize=70, font='微软雅黑.ttf', color='black',):
  #     """
  #     根据提供的字幕信息创建TextClip列表。
  #     """
  #     subtitle_clips = []
      
  #     for subtitle in subtitles:
  #         text_clip = TextClip(subtitle["text"], 
  #                              fontsize=fontsize, 
  #                              font=font, 
  #                              color=color,
  #                              method="label",
  #                              size=(1920, 1080),  # 假设你的视频是1080p的，调整尺寸以适应你的视频
  #                              align="center", interline=-1)
  #         text_clip = text_clip.set_start(subtitle["start"]).set_end(subtitle["end"])
  #         text_clip = text_clip.set_position(('center', 'bottom'))  # 设置字幕位置
          
  #         subtitle_clips.append(text_clip)
      
  #     return subtitle_clips


  final_video1 = VideoFileClip(temp_path)
  subtitle_clips = []
  # 添加字幕
  for i, (text) in enumerate(data['texts']):
      

      txt_clip = TextClip("微软雅黑.ttf",text, 
                              font_size=50, 
                              color='black',
                              size=final_video.size,
                              duration=data['mp3_durations'][i]  # 调整尺寸以适应你的视频
                              )

      txt_clip = TextClip("微软雅黑.ttf",text, font_size=50, color='black',duration=data['mp3_durations'][i])
    #   txt_clip_eng:TextClip = TextClip("微软雅黑.ttf",text_english, font_size=50, color='black',duration=data['mp3_durations'][i])
      txt_clip = txt_clip.with_position('center','bottom')
      subtitle_clips.append(txt_clip)
      # txt_clip_eng = txt_clip_eng.with_position(('center', 'bottom')).with_position(lambda t: (0,50+t))
      # txt_clip_eng.margin=50
  # subtitle_clips=subtitle_clips[:5]
  video_s=concatenate_videoclips(subtitle_clips)

  # 计算文本位置，使其距离视频底部有50像素的间隙
  text_height = video_s.h  # 获取文本的高度
  margin_bottom = 50    # 底部边距
  text_y_position = final_video1.h - text_height - margin_bottom  # 文本Y轴位置

  # 设置文本位置为水平居中、垂直方向上距离底部50像素


  final_video2 = CompositeVideoClip([final_video1 ,video_s.with_position(("center",0.85), relative=True)], size=final_video.size)
  # final_video = CompositeVideoClip([final_video]+ subtitle_clips, size=final_video.size)
  result_path=os.path.join(project_path,"output.mp4")
  # 输出最终视频
  final_video2.write_videofile(result_path, fps=24,codec="libx264")
  return result_path

if __name__ == "__main__":
  # 测试代码

  result_path = coze_video_transfrom_books(data)
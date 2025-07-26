import os
import uuid
from moviepy import VideoFileClip,concatenate_videoclips, CompositeVideoClip, ImageClip, afx, AudioFileClip, CompositeAudioClip, TextClip,AudioClip,vfx,ColorClip,VideoClip,concatenate_audioclips
from moviepy.video.tools.drawing import color_gradient
from moviepy.video.tools.subtitles import SubtitlesClip

from config import get_user_data_dir

data={
  "bg_audio": "https://coze-tmp-file.oss-cn-shenzhen.aliyuncs.com/2025_03_20/732558dd-30dd-402f-880d-3a49f44fc71e.mp3",
  "images": [
    "https://s.coze.cn/t/-ImAoLc0Jho/",
    "https://s.coze.cn/t/Ccv4zIFdRBw/",
    "https://s.coze.cn/t/WKNXnpbn4SY/",
    "https://s.coze.cn/t/hQpNGIrVqa8/",
    "https://s.coze.cn/t/ezyh040XJlw/",
    "https://s.coze.cn/t/0e-PIyqo95E/",
    "https://s.coze.cn/t/xo3sEvzobGI/",
    "https://s.coze.cn/t/YVEWJU8JNCo/",
    "https://s.coze.cn/t/YygZcWsaYuA/",
    "https://s.coze.cn/t/WY9IUTsaEh4/",
    "https://s.coze.cn/t/3hUGJZqjNGU/",
    "https://s.coze.cn/t/77F3DV4bltA/",
    "https://s.coze.cn/t/-4xG5t8jpNY/",
    "https://s.coze.cn/t/qcvcZU-FXKY/",
    "https://s.coze.cn/t/4sL2n289aKk/",
    "https://s.coze.cn/t/4OKhs1YuIcA/",
    "https://s.coze.cn/t/a0E8e6nloJ8/",
    "https://s.coze.cn/t/97Wgr9eifLI/",
    "https://s.coze.cn/t/xj7u-5pGDBY/",
    "https://s.coze.cn/t/eZuiafAFlM4/",
    "https://s.coze.cn/t/d8bqw2uhv3c/",
    "https://s.coze.cn/t/ti0-szGqKeY/",
    "https://s.coze.cn/t/l_y7A4sFRv4/"
  ],
  "images_bg": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/99b3fbeaf21b4681b244d88ff495bb78.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1776192424&x-signature=AsuiJN%2BheXayEF1k1T77udp5BJQ%3D",
  "mp3_durations": [
    6.768,
    2.352,
    6.36,
    4.296,
    4.008,
    3.648,
    6.24,
    6.504,
    5.112,
    3.672,
    3.288,
    3.936,
    3.192,
    4.2,
    5.304,
    3.6,
    3.624,
    2.808,
    3.672,
    2.496,
    3.552,
    4.824,
    6.144
  ],
  "mp3_urls": [
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1ed97bd0-c2a4-494f-ae0e-95d6b6b15039.mp3?lk3s=da27ec82&x-expires=1745092026&x-signature=F1vAdWE29wTNbVyZFeJsB0clk6o%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_95211c63-5789-4a6b-b4d0-493a8f7d8a46.mp3?lk3s=da27ec82&x-expires=1745092028&x-signature=Tc8VUF58oyYEP6Zmk3on6X6Pq50%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_b02ca726-d684-4491-8b4b-cde4bb7b3009.mp3?lk3s=da27ec82&x-expires=1745092031&x-signature=LiKv3xmft0xAc4ZRrE%2BwFPqnmk4%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_8a009341-aa5e-4772-b594-973ab9d7c189.mp3?lk3s=da27ec82&x-expires=1745092033&x-signature=V85sFFW4L6Dml938zCiEB2k4hXc%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d3c023ed-8f2a-41c0-9e02-8573a2ee27fb.mp3?lk3s=da27ec82&x-expires=1745092035&x-signature=DwukMQpgMRzdHEQ%2B%2B9L4%2Fcht1XQ%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_52044312-7ddd-495e-b109-8db39bc7fdfe.mp3?lk3s=da27ec82&x-expires=1745092037&x-signature=55B8IKWrPcaCwu0PrJtLlbZZVZ0%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_99a4dd24-ff3f-4ca1-a549-1cbdf67b4f43.mp3?lk3s=da27ec82&x-expires=1745092039&x-signature=wiQgkPTsP5gdEnYs3gkFuskSbi0%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_e299f4dc-6757-4c32-8f13-e7934a4410b1.mp3?lk3s=da27ec82&x-expires=1745092042&x-signature=RSYFhWZ9vFXXYxNKHhUWVCRgMqM%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_774b0414-440f-47c4-bace-8f5780a74063.mp3?lk3s=da27ec82&x-expires=1745092044&x-signature=p%2BrEF9jHY41wEXL7OIayTYXlc%2FQ%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_f32a1278-8d52-4507-9144-916602a34b04.mp3?lk3s=da27ec82&x-expires=1745092046&x-signature=Kj0%2FD%2F1EZZ4kraWwY1GfrZ23PZA%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_6bf2fa1a-0436-4200-a153-410f1d621cce.mp3?lk3s=da27ec82&x-expires=1745092048&x-signature=xNq5f0NSx2Em%2B9apyKgl2QRMkXs%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_e524da66-dd64-439f-8e35-e7feb116c712.mp3?lk3s=da27ec82&x-expires=1745092049&x-signature=f9eWG7qRkY0jLXfK5fdpb1KIt6A%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_717bd235-6575-431b-a94f-3a035459e68e.mp3?lk3s=da27ec82&x-expires=1745092051&x-signature=Ef17BYIQYuaCyKTluljXzLCWiVQ%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1b6f62cf-bc9a-4c6c-92c3-2d58eb3d5bbd.mp3?lk3s=da27ec82&x-expires=1745092053&x-signature=xwkZf9e6abL4ZPYHt2M%2Fr5oCFY8%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_835f10d8-0684-4b27-8fbe-02ca22d86443.mp3?lk3s=da27ec82&x-expires=1745092055&x-signature=ciUlGzcvWNhLxuJl9NXODL3K3w4%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_89b17498-17de-435d-a3ed-d408740a1f0a.mp3?lk3s=da27ec82&x-expires=1745092056&x-signature=N1iu8H%2FJVQCXc1ZwxTeMi9k5hro%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1b41b6af-e2a6-45b4-b012-ce751c298378.mp3?lk3s=da27ec82&x-expires=1745092058&x-signature=n%2BS8fAp%2Bz%2Bxa%2BymQfCh8CuVdrQU%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_b89a38ee-3a4b-4386-9ef9-1dbc4aacec1c.mp3?lk3s=da27ec82&x-expires=1745092059&x-signature=LQJTWbzs8aWoyq%2FFSY6BIiO0wBE%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_2e503289-190c-4b63-816c-93d771dc764c.mp3?lk3s=da27ec82&x-expires=1745092061&x-signature=RKQPY5u95FCE6BcfToh5nXOAPhE%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_c2b7fe90-cbfb-4566-a90f-1ff1526a4b6c.mp3?lk3s=da27ec82&x-expires=1745092063&x-signature=%2Fw9TYW0oONjQqRcO0FjzDvrdZqM%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_2bf034e1-5f3d-4d0e-9f06-b1bd5d8f4ad1.mp3?lk3s=da27ec82&x-expires=1745092064&x-signature=of5S2qZmBatOe50IvLt4f76INwo%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_c3e53638-fb61-499d-9e46-849f6a214ccd.mp3?lk3s=da27ec82&x-expires=1745092066&x-signature=av%2BoKe%2FpvCmC7J1d%2FaXR9vqEiFA%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_0d913a58-8c02-4c79-bef9-83b226ed7f25.mp3?lk3s=da27ec82&x-expires=1745092069&x-signature=SVeT2nneEU3N%2BeDAm50HI8LR%2BaQ%3D"
  ],
  "texts": [
    "当晨曦透过苏州河畔的梧桐树影，58岁的陈美华总会穿上月白色提花外套。",
    "轻抚袖口精致的盘扣。",
    "二十年前，正是母亲衣襟处松脱的盘扣，让林婉清萌生了创业念头。",
    "「雅致年华」工作室承载着三代女性的时装理想。",
    "林婉清记得外婆压在樟木箱底的香云纱旗袍。",
    "记得母亲总把新衣改制三次才能合身的叹息。",
    "2013年首个系列亮相时，她创新性地将非遗苏绣与记忆弹性纤维结合。",
    "改良式旗袍既能勾勒东方女性的曲线美，又能在广场舞转身时伸展自如。",
    "品牌最受欢迎的「云舒」系列选用新疆长绒棉与蚕丝混纺面料。",
    "经过27道水洗工艺，触感如第二层肌肤。",
    "设计师团队每月深入社区与客户对话。",
    "发现中年女性更渴望能自如转换场景的着装。",
    "接送孙辈的连帽风衣藏着珍珠胸针。",
    "跳交谊舞的渐变长裙配备隐形收纳袋。",
    "2023年推出的智能温控马甲，内嵌石墨烯发热模块。",
    "智能温控马甲成为北方市场的爆款。",
    "如今，品牌在全国开设了68家体验店。",
    "每间试衣间都配有专业形象顾问。",
    "68岁的退休教师王阿姨说：这里的衣服会说话。",
    "它记得我的肩周炎不宜穿套头衫。",
    "记得我女儿婚礼需要藏蓝色的庄重。",
    "从米兰时装周特别邀请展，到社区旗袍裁剪课堂。",
    "雅致年华正重新定义「银发时尚」——不是岁月的妥协，而是生命力的盛放。"
  ]
}

def coze_video_transfrom_Aunts(data:dict):
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
  try:
    f_volumn=final_audio.max_volume()
    b_volumn=background_music.max_volume()
    volumn_scale=2*b_volumn/f_volumn
  except:
    volumn_scale=1

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

  result_path = coze_video_transfrom_Aunts(data)
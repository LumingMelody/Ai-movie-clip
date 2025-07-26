import os
import uuid
from moviepy import VideoFileClip,concatenate_videoclips, CompositeVideoClip, ImageClip, afx, AudioFileClip, CompositeAudioClip, TextClip,AudioClip,vfx,ColorClip,VideoClip,concatenate_audioclips
from moviepy.video.tools.drawing import color_gradient
from moviepy.video.tools.subtitles import SubtitlesClip

from config import get_user_data_dir


# 加载json数据（这里直接用字典代替）


def coze_stickman_video_transfrom(data: dict):
  project_id = str(uuid.uuid1())
  user_data_dir = get_user_data_dir()
  base_project_path = os.path.join(user_data_dir, "projects")
  project_path = os.path.join(base_project_path, project_id)
  os.makedirs(project_path, exist_ok=True)

  def download_file(url, local_filename):
    import requests
    # 🔥 检查URL是否为空或无效
    if not url or url.strip() == "" or url == '""':
      print(f"⚠️ 跳过空URL: {url}")
      return None

    try:
      with requests.get(url, stream=True) as r:
        r.raise_for_status()
        local_filename = os.path.join(project_path, local_filename)
        with open(local_filename, 'wb') as f:
          for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
      return local_filename
    except Exception as e:
      print(f"❌ 下载失败 {url}: {str(e)}")
      return None

  # 下载并加载所有资源
  bg_audio_path = download_file(data['bg_audio'], "bg_audio.mp3")
  audio_clips = []

  # 🔥 下载音频文件，跳过失败的
  for i, mp3_url in enumerate(data['mp3_urls']):
    audio_path = download_file(mp3_url, f"mp3_{i}.mp3")
    if audio_path:
      try:
        audio_clips.append(AudioFileClip(audio_path))
      except Exception as e:
        print(f"❌ 音频加载失败 {audio_path}: {str(e)}")

  # 🔥 下载图片文件，跳过空URL和失败的下载
  image_clips = []
  valid_durations = []

  for i, (image_url, duration) in enumerate(zip(data['images'], data['mp3_durations'])):
    # 跳过空URL
    if not image_url or image_url.strip() == "" or image_url == '""':
      print(f"⚠️ 跳过空图片URL，索引: {i}")
      continue

    image_path = download_file(image_url, f"img_{i}.png")
    if image_path:
      try:
        image_clips.append(ImageClip(image_path, duration=duration))
        valid_durations.append(duration)
      except Exception as e:
        print(f"❌ 图片加载失败 {image_path}: {str(e)}")

  # 下载背景图片
  background_path = download_file(data['images2'], "background.png")
  if background_path:
    background_image = ImageClip(background_path, duration=sum(valid_durations))
  else:
    # 如果背景图片下载失败，创建一个纯色背景
    background_image = ColorClip(size=(1920, 1080), color=(255, 255, 255), duration=sum(valid_durations))

  # 🔥 检查是否有有效的图片剪辑
  if not image_clips:
    raise ValueError("❌ 没有有效的图片可以处理")

  print(f"✅ 成功处理了 {len(image_clips)} 个图片剪辑")

  # 继续原有的处理逻辑...
  # 创建主视频A
  video_a = concatenate_videoclips(image_clips)
  half_w = video_a.w / 1.5
  half_h = video_a.h / 1.5
  video_a = video_a.resized((half_w, half_h))

  # 将视频A叠加在背景图上
  final_video = CompositeVideoClip([background_image, video_a.with_position(("center", "center"))])

  # 组合解说音频
  if audio_clips:
    final_audio = concatenate_audioclips(audio_clips)
  else:
    raise ValueError("❌ 没有有效的音频可以处理")

  # 添加背景音乐，并调整音量
  if bg_audio_path:
    background_music = AudioFileClip(bg_audio_path)
    if background_music.duration > final_video.duration:
      background_music = background_music.subclipped(0, final_audio.duration)
    else:
      background_music = background_music.with_effects([afx.AudioLoop(int(final_audio.duration) + 1)])
      background_music = background_music.subclipped(0, final_audio.duration)

    f_volumn = final_audio.max_volume()
    b_volumn = background_music.max_volume()
    volumn_scale = 2 * b_volumn / f_volumn

    final_audio = CompositeAudioClip([
      final_audio.with_effects([afx.MultiplyVolume(1)]),
      background_music.with_effects([afx.MultiplyVolume(1 / volumn_scale)])
    ])

  # 将音频添加到视频中
  final_video = final_video.with_audio(final_audio)

  temp_path = os.path.join(project_path, "output2.mp4")
  final_video.write_videofile(temp_path, fps=24, codec="libx264")

  # 添加字幕部分...
  final_video1 = VideoFileClip(temp_path)
  subtitle_clips = []

  # 🔥 只处理有效图片对应的文本
  valid_texts = []
  valid_texts_english = []

  for i, (image_url, text, text_english) in enumerate(zip(data['images'], data['texts'], data['texts_english'])):
    # 只保留非空图片对应的文本
    if image_url and image_url.strip() != "" and image_url != '""':
      valid_texts.append(text)
      valid_texts_english.append(text_english)

  # 添加字幕
  for i, (text, text_english, duration) in enumerate(zip(valid_texts, valid_texts_english, valid_durations)):
    txt_clip = TextClip("微软雅黑.ttf", text, font_size=50, color='black', duration=duration)
    txt_clip = txt_clip.with_position('center', 'bottom')
    subtitle_clips.append(txt_clip)

  if subtitle_clips:
    video_s = concatenate_videoclips(subtitle_clips)
    final_video2 = CompositeVideoClip([final_video1, video_s.with_position(("center", 0.85), relative=True)],
                                      size=final_video.size)
  else:
    final_video2 = final_video1

  result_path = os.path.join(project_path, "output.mp4")
  final_video2.write_videofile(result_path, fps=24, codec="libx264")
  return result_path

if __name__ == "__main__":
  # 测试代码
  data={
  "bg_audio": "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o0TWPfYrqQLsB0BMQS6iBWAmGgFiIBEX0Vyr2g",
  "images": [
    "https://s.coze.cn/t/0dfVUhxnAIo/",
    "https://s.coze.cn/t/5gladRSubyg/",
    "https://s.coze.cn/t/oPOnBpF1lGM/",
    "https://s.coze.cn/t/Zsur7U_YCdU/",
    "https://s.coze.cn/t/yikaNZoX7os/",
    "https://s.coze.cn/t/jlZzkWs98lI/",
    "https://s.coze.cn/t/qWJXnDHQbgM/",
    "https://s.coze.cn/t/1rPbz8Mh58o/",
    "https://s.coze.cn/t/3sLwbHRS8JQ/",
    "https://s.coze.cn/t/vZ3G0dZKjIk/",
    "https://s.coze.cn/t/XrCNu_rXoR4/",
    "https://s.coze.cn/t/L6kK4EJ2bS0/",
    "https://s.coze.cn/t/DZrijiARl4U/",
    "https://s.coze.cn/t/PEBHwEroMck/",
    "https://s.coze.cn/t/Ft_HN9emokQ/",
    "https://s.coze.cn/t/XvCo31R9mqs/",
    "https://s.coze.cn/t/SObOn-AxcuI/",
    "https://s.coze.cn/t/Fpj6NvPID7M/"
  ],
  "images2": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/5a3696c62b104227bd03e44247980d84.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778903874&x-signature=YEec%2FdPKIyBFmgKai4j2zbcwYR0%3D",
  "mp3_durations": [
    5.112,
    4.488,
    6.024,
    6,
    5.544,
    6.576,
    2.664,
    4.824,
    3.504,
    3.936,
    3.48,
    4.128,
    2.568,
    2.904,
    2.664,
    4.008,
    6.168,
    2.856
  ],
  "mp3_urls": [
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1ca24af7-1d02-489e-ab19-ced4ae21d04a.mp3?lk3s=da27ec82&x-expires=1747803476&x-signature=kdaCoIzN9eGeob28ELhqrS%2FLpAI%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_3f907514-4ae8-4c14-9b6c-62539aa60165.mp3?lk3s=da27ec82&x-expires=1747803478&x-signature=MY3DSvOYnqFQ7R3mDzqSWSHc9Ks%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_382d6476-efdc-439f-a4c3-c9bac620b8bd.mp3?lk3s=da27ec82&x-expires=1747803480&x-signature=fQAa4kUQtKjdBvuLyY%2FXvzGdGbM%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_2776fc39-4073-4b80-9a9b-f980652d7e17.mp3?lk3s=da27ec82&x-expires=1747803484&x-signature=aZU19mt3f6TbQVkVt6h5gPrG5A8%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_9ce46541-a6dd-40a4-8177-025635feb946.mp3?lk3s=da27ec82&x-expires=1747803486&x-signature=OoUc4Qwg2xMWOnG28w6SBTG22a4%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_37c826f8-d844-48c4-802a-1acb6d4c7456.mp3?lk3s=da27ec82&x-expires=1747803488&x-signature=v6F0V96LYzJjARhYc6Ck6ZE0%2FYI%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_16431698-e487-45d6-ba18-1afd34555bb0.mp3?lk3s=da27ec82&x-expires=1747803490&x-signature=8u%2FUR5jNWPCWwPMDx03ZIF1VpIE%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_f8d478a4-798b-4f81-9200-2465b37296f1.mp3?lk3s=da27ec82&x-expires=1747803491&x-signature=RtFiSndIS06%2FsH7XORgF%2Bvqj7uQ%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_0d662fe7-d48a-4d38-842d-084c5adf2db4.mp3?lk3s=da27ec82&x-expires=1747803493&x-signature=CwqO2HJQhrda1%2FLuleGqAc2LK0w%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1da039a0-189d-4c14-8db1-6c275c9f37d6.mp3?lk3s=da27ec82&x-expires=1747803495&x-signature=YAjwUNdKOgvbDKDiePiIpFqr5is%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_77d18215-03ab-45da-ade5-5aa3db81d03f.mp3?lk3s=da27ec82&x-expires=1747803497&x-signature=B6zYLvMROplh0K%2FDyBZIF7aOxak%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_cac8bcc2-aad2-40e2-8035-de64c4c63106.mp3?lk3s=da27ec82&x-expires=1747803499&x-signature=tTn1Llrd0g8j2asyAS49C1duTGQ%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_1ec10ab7-57ef-454b-a551-ef1d53b45806.mp3?lk3s=da27ec82&x-expires=1747803500&x-signature=jHLAjXPMrdjji%2F7F8HaAYBTvS7o%3D",
    "https://lf3-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d8b9635a-199e-4954-8f6e-8408b1b75e43.mp3?lk3s=da27ec82&x-expires=1747803502&x-signature=BpdQMSi9mE%2BMu6V%2FskK1AvEFMt4%3D",
    "https://lf6-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_d99e5557-abb8-4eae-b089-f0a070e6d167.mp3?lk3s=da27ec82&x-expires=1747803503&x-signature=M3W1yCV3db52g4jYSmo2kC0PL0Q%3D",
    "https://lf9-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_8a7da97f-5fd0-48ed-8534-08f3e3b7d798.mp3?lk3s=da27ec82&x-expires=1747803505&x-signature=2alPh0mjZBjnKqDLBYNldqXDmYM%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_886889cf-0af4-49ac-bb09-26c1e04121ab.mp3?lk3s=da27ec82&x-expires=1747803509&x-signature=0gJP%2FSTIDmwNkQFKfByoYBIxFTY%3D",
    "https://lf26-appstore-sign.oceancloudapi.com/ocean-cloud-tos/VolcanoUserVoice/speech_7426720361733177353_db5df58d-46d7-4b3d-ae78-ccea3b3ceb8f.mp3?lk3s=da27ec82&x-expires=1747803510&x-signature=eWX8l%2F3IQX9%2BJcw%2FSJPDkKBomCU%3D"
  ],
  "texts": [
    "在创业和经营的道路上，很多企业主都面临着财税合规的问题。",
    "有些企业主可能会觉得，财税合规就是各种复杂的条条框框，",
    "严格的规定束缚了企业的发展，一不小心还可能面临罚款等风险，让人头疼不已。",
    "但换个角度看，财税合规并非是限制，而是企业健康发展的“保护罩”。",
    "从心理学的“路径依赖”理论来说，企业早期若形成合规的财税习惯，",
    "后续发展会更顺畅。合规的财税流程，就像是为企业发展铺就的一条平坦大道，",
    "能避免许多潜在的风险与危机。",
    "那么该如何做到财税合规呢？首先，要建立正确的认知，",
    "意识到财税合规对企业长远发展的重要性。",
    "可以聘请专业的财税人员，或者委托靠谱的财税机构，",
    "定期对企业的财务状况进行梳理和审查。",
    "同时，企业主自身也要加强对财税知识的学习，",
    "了解基本的税收政策和财务规范。",
    "企业主们，不要把财税合规当作负担，",
    "它实则是企业稳健前行的保障。",
    "每一次合规操作，都是在为企业的未来筑牢基石。",
    "相信通过重视和落实财税合规，你的企业一定能在健康发展的道路上越走越稳。",
    "我是常熟优帮财税，我们下期见。"
  ],
  "texts_english": [
    "On the path of entrepreneurship and business operations, many business owners face issues of financial and tax compliance.",
    "Some business owners might think that financial and tax compliance is just a set of complex rules and regulations,",
    "strict provisions that constrain the development of the enterprise, and if not careful, may face risks such as fines, causing headaches.",
    "But from another perspective, financial and tax compliance is not a restriction but a 'protective shield' for the healthy development of the enterprise.",
    "From the psychological theory of 'path dependence,' if a company forms compliant financial and tax habits early on,",
    "its subsequent development will be smoother. Compliant financial and tax processes are like a smooth road paved for the development of the enterprise,",
    "avoiding many potential risks and crises.",
    "So how can financial and tax compliance be achieved? First, establish the correct understanding,",
    "recognizing the importance of financial and tax compliance for the long-term development of the enterprise.",
    "Hire professional financial and tax personnel or entrust reliable financial and tax institutions,",
    "to regularly sort out and review the financial status of the enterprise.",
    "At the same time, business owners themselves should strengthen their learning of financial and tax knowledge,",
    "understanding basic tax policies and financial norms.",
    "Business owners, do not regard financial and tax compliance as a burden,",
    "it is actually a guarantee for the steady progress of the enterprise.",
    "Every compliant operation is laying a solid foundation for the future of the enterprise.",
    "Believe that by valuing and implementing financial and tax compliance, your enterprise will surely walk steadily on the path of healthy development.",
    "I am Changshu Youbang Financial and Tax, see you next time."
  ]
}

  # 测试函数
  result_path = coze_stickman_video_transfrom(data)
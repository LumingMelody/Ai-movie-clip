# -*- coding: utf-8 -*-
# @Time    : 2025/5/22 14:53
# @Author  : 蔍鸣霸霸
# @FileName: coze_videos_advertsment.py
# @Software: PyCharm
# @Blog    ：只因你太美

import os
import platform
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips,afx,VideoFileClip,CompositeAudioClip,VideoClip,vfx
import requests
import random
import uuid
# 导入配置模块
from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url
from core.clipgenerate.tongyi_get_videotalk import get_videotalk



def get_video_files(folder_path):
    """从指定文件夹下读取所有视频文件"""
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    try:
        return [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
    except FileNotFoundError:
        print(f"错误：目录 {folder_path} 不存在")
        return []


def select_random_videos(video_files, num_to_select):
    """从中随机挑选若干个视频文件"""
    if not video_files:
        raise ValueError("视频文件列表为空")
    return random.sample(video_files, min(num_to_select, len(video_files)))


def create_font_path(font_name="Microsoft YaHei"):
    """获取字体路径，支持系统字体或自定义字体文件"""
    # 优先使用系统字体
    if platform.system() == "Windows":
        return font_name  # Windows 直接使用字体名称

    # 其他系统或自定义字体文件的处理
    # 例如：return os.path.join(get_user_data_dir(), "fonts", "msyh.ttf")
    return font_name  # 默认使用系统字体


def download_file(url, filename, target_dir):
    """下载远程文件到指定目录"""
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    try:
        print(f"开始下载: {url}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"下载完成: {filepath}")
        return filepath
    except Exception as e:
        print(f"下载失败: {e}")
        raise


def trans_videos_advertisement(data: dict) -> str:
    """生成视频广告"""
    # 创建项目目录
    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    # 创建素材目录
    materials_dir = os.path.join(user_data_dir, "materials")
    moderator_folder_path = os.path.join(materials_dir, "moderator")
    enterprise_folder_path = os.path.join(materials_dir, "enterprise")

    for dir_path in [materials_dir, moderator_folder_path, enterprise_folder_path, base_project_path]:
        os.makedirs(dir_path, exist_ok=True)

    print(f"项目目录: {project_path}")
    print(f"主持人素材目录: {moderator_folder_path}")
    print(f"企业素材目录: {enterprise_folder_path}")

    # 下载背景图
    bg_image_path = download_file(data["data"], "background.png", project_path)

    # 下载所有音频
    audio_clips = []
    audio_paths = []

    for i, url in enumerate(data["audio_urls"]):
        path = f"audio_{i}.mp3"
        file_path = download_file(url, path, project_path)
        audio_clip = AudioFileClip(file_path)
        audio_clips.append(audio_clip)
        audio_paths.append(file_path)

    # 下载背景音乐
    bgm_path = download_file(data["bgm"], "bgm.mp3", project_path)
    bgm_clip = AudioFileClip(bgm_path)

    # 检查并选择主持人视频
    moderator_files = get_video_files(moderator_folder_path)
    if not moderator_files:
        raise FileNotFoundError(f"主持人素材目录为空: {moderator_folder_path}")

    selected_moderator_files = select_random_videos(moderator_files, 1)
    moderator_local_path = os.path.join(moderator_folder_path, selected_moderator_files[0])
    moderator_url, moderator_http = get_online_url(moderator_local_path)

    # 生成开场和结尾视频
    start_film_url = get_videotalk(moderator_url, data["audio_urls"][0])
    end_film_url = get_videotalk(moderator_url, data["audio_urls"][-1])

    start_clip = VideoFileClip(download_file(start_film_url, "start.mp4", project_path))
    end_clip = VideoFileClip(download_file(end_film_url, "end.mp4", project_path))

    # 检查并选择企业视频
    enterprise_files = get_video_files(enterprise_folder_path)
    if not enterprise_files:
        raise FileNotFoundError(f"企业素材目录为空: {enterprise_folder_path}")

    selected_enterprise_files = select_random_videos(enterprise_files, len(data["output"]) - 2)

    # 创建字幕片段
    def create_text_clip(text, duration, is_title=False):
        """创建带样式的文字片段"""
        font = create_font_path()  # 获取字体路径或名称
        font_size = 80 if is_title else 48
        color = 'black' if is_title else 'yellow'
        stroke_color = 'yellow' if is_title else 'black'
        stroke_width = 3 if is_title else 1

        return TextClip(
            text,
            font=font,
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method="caption",  # 优化多行文本显示
            size=(1280, None),  # 限制宽度
            align="center"
        ).with_duration(duration)

    # 构建视频片段
    video_clips = []

    for i, (text, audio_clip) in enumerate(zip(data["output"], audio_clips)):
        bg = ImageClip(bg_image_path).with_duration(audio_clip.duration)

        if i == 0:
            # 标题片段
            video_clip = start_clip
            title_clip = create_text_clip(data["conpany_name"], audio_clip.duration, is_title=True)
            text_clip = create_text_clip(text, audio_clip.duration)

            composite = CompositeVideoClip([
                bg,
                video_clip.with_position(("center", "center"), relative=True),
                title_clip.with_position(("center", 0.2), relative=True),  # 标题位置
                text_clip.with_position(("center", 0.8), relative=True)  # 字幕位置
            ]).with_audio(audio_clip)

        elif i == len(data["output"]) - 1:
            # 结尾片段
            video_clip = end_clip
            text_clip = create_text_clip(text, audio_clip.duration)

            composite = CompositeVideoClip([
                bg,
                video_clip.with_position(("center", "center"), relative=True),
                text_clip.with_position(("center", 0.8), relative=True)
            ]).with_audio(audio_clip)

        else:
            # 中间片段
            video_path = os.path.join(enterprise_folder_path, selected_enterprise_files[i - 1])
            video_clip = VideoFileClip(video_path).resize((1280, 720))  # 统一视频尺寸

            # 根据音频长度裁剪视频
            target_duration = audio_clip.duration
            if video_clip.duration > target_duration:
                # 如果视频超过目标时长，随机选择片段
                start_time = random.uniform(0, video_clip.duration - target_duration - 0.1)
                video_clip = video_clip.subclip(start_time, start_time + target_duration)
            else:
                # 如果视频不足，循环播放
                loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                video_clip = video_clip.subclip(0, target_duration)

            text_clip = create_text_clip(text, audio_clip.duration)

            composite = CompositeVideoClip([
                bg,
                video_clip.with_position(("center", "center"), relative=True),
                text_clip.with_position(("center", 0.8), relative=True)
            ]).with_audio(audio_clip)

        video_clips.append(composite)

    # 拼接所有片段
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 调整背景音乐长度
    if bgm_clip.duration < final_video.duration:
        bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
    else:
        bgm_clip = bgm_clip.subclip(0, final_video.duration)

    # 混合音频
    try:
        origin_max_volume = final_video.audio.max_volume()
        bgm_max_volume = bgm_clip.max_volume()

        if bgm_max_volume == 0:
            volume_rate = 1
        else:
            volume_rate = origin_max_volume / (bgm_max_volume * 2)

        final_audio = CompositeAudioClip([
            final_video.audio,
            bgm_clip.with_effects([afx.MultiplyVolume(volume_rate)])
        ])

        final_video = final_video.with_audio(final_audio)
    except Exception as e:
        print(f"音频混合失败: {e}")
        print("使用原始音频...")

    # 输出视频
    output_path = os.path.join(project_path, "final_video.mp4")

    try:
        print(f"开始生成视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4,  # 多线程加速
            verbose=False,
            progress_bar=True
        )
        print(f"✅ 视频已生成: {output_path}")
        return output_path
    except Exception as e:
        print(f"视频生成失败: {e}")
        raise


if __name__ == "__main__":
    json_data = {
        "audio_urls": [
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/74f133ee014744b4a50114e534b1ee5f.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/36a5f3c5310f43af8b2720939e63140b.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/66714b354acb438c8f34e9314b9715bb.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/91693b099d814244aa02e29bd1ebe85b.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/22cefdd470f743dfa5181fe832e6b758.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/d0ecb37928c546629cdd754bfbc680e8.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/7dd2c834afdc4aa08d599a76561275e4.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/d7a777ecb3814bd493a4635349fe022f.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/e0dd6eace6ab42ba9cf623c77be4f29a.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/4a5c6624763d42cb9eb0cfca844c6437.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/b02f0ace38e14ef892a99f62492019bd.mp3"
        ],
        "bgm": "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ocM2U8riP8GkR1w5RQQWIQBxrBMmIA6t7CinZ",
        "conpany_name": "常熟优帮财税",
        "data": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/9dc6b146a0c94ffc890996d32dea6ecb.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778204059&x-signature=lnyYwUBJmGPE8xF4bo0J6Febaw4%3D",
        "output": [
            "在企业财税领域，当下正遭遇着重重挑战",
            "伴随智慧税务推进，税务机关掌控企业各类数据",
            "往昔不规范处易被察觉，企业涉税风险增加",
            "财政压力传导，监管更严，企业财税合规成趋势",
            "常熟优帮财税脱颖而出，有20多年专业经验",
            "精心组建专业团队，全方位为企业提供服务",
            "从基础业务到税务架构设计，提供全流程服务",
            "针对重大交易筹划，应对风险，开展审计等",
            "如同打造专属科室，提升企业财税风险能力",
            "秉持诚信原则，坚守客户至上，维护商业秘密",
            "助力企业合规经营，达成可持续发展目标"
        ]
    }

    try:
        trans_videos_advertisement(json_data)
    except Exception as e:
        print(f"程序执行失败: {e}")
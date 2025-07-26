import os
import random
import requests
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, vfx, VideoClip, \
    ColorClip
from urllib.parse import urlparse
import uuid
import numpy as np
import cv2
from config import get_user_data_dir

# -----------------------------
# 用户配置区
# -----------------------------
IMAGE_FOLDER = "images"  # 图片缓存目录
AUDIO_FOLDER = "audios"  # 音乐缓存目录

DURATION_PER_CLIP = 8  # 每个背景视频片段的时长（秒）
folder_path = os.path.join(get_user_data_dir(), 'materials/enterprise')


# -----------------------------
# 工具函数
# -----------------------------

def download_file(url, folder, ext=None):
    filename = os.path.basename(urlparse(url).path)
    if ext:
        filename = f"{os.path.splitext(filename)[0]}.{ext}"
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        print(f"Downloading {url} to {path}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
    return path


def blur(clip, sigma=3):
    """
    对视频剪辑中的每一帧应用高斯模糊。

    参数:
        clip (VideoClip): 要处理的视频剪辑。
        sigma (int/float): 高斯模糊的标准差，值越大越模糊。

    返回:
        VideoClip: 经过高斯模糊处理的新视频剪辑。
    """

    def blurred_frame(t):
        frame = clip.get_frame(t)
        # 使用OpenCV进行高斯模糊
        return cv2.GaussianBlur(frame, (0, 0), sigmaX=sigma)

    blurred_clip = VideoClip(
        frame_function=blurred_frame,
        duration=clip.duration,
    )

    return blurred_clip


# 创建带黑色半透明遮罩的复合视频
def apply_black_overlay(clip, opacity=50):
    """
    在视频上叠加一个黑色半透明遮罩。

    参数:
        clip: 原始视频剪辑。
        opacity: 透明度 (0 完全透明, 100完全不透明)

    返回:
        新的合成视频剪辑
    """
    opacity = int(opacity / 100 * 255)
    overlay = ColorClip(size=clip.size, color=(0, 0, 0, opacity), duration=clip.duration)
    return CompositeVideoClip([clip, overlay])


def random_background_clip(duration):
    video_files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.avi', '.mov'))]
    clips = []
    total = 0
    while total < duration:
        file = random.choice(video_files)
        clip = VideoFileClip(os.path.join(folder_path, file)).without_audio()
        max_start = max(0, clip.duration - DURATION_PER_CLIP)
        start = random.uniform(0, max_start)
        subclip = clip.subclipped(start, min(start + DURATION_PER_CLIP, clip.duration))
        clips.append(subclip)
        total += subclip.duration
    return concatenate_videoclips(clips).subclipped(0, duration)


def wave_frame(img, t):
    """
    对单帧图像应用水波抖动效果
    :param img: numpy array 格式的图像 (H, W, C)
    :param t: 当前时间
    :return: 处理后的图像
    """
    height, width = img.shape[:2]

    # 创建一个与原图大小相同的空白图像
    distorted = np.zeros_like(img)

    # 创建网格坐标
    x, y = np.meshgrid(np.arange(width), np.arange(height))

    # 添加正弦扰动
    dx = 5 * np.sin(2 * np.pi * t + y / 20)  # 水平方向波动
    dy = 3 * np.cos(2 * np.pi * t + x / 20)  # 垂直方向波动

    map_x = (x + dx).astype(np.float32)
    map_y = (y + dy).astype(np.float32)

    # 应用重映射（remap）
    distorted = cv2.remap(img, map_x, map_y, interpolation=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REFLECT)

    return distorted


def make_wavy_image_func(clip):
    def func(get_frame, t):
        frame = get_frame(t)
        return wave_frame(frame, t)

    return func


# -----------------------------
# 主函数：处理每组图片+音乐
# -----------------------------
def trans_video_inciment(json_data: dict) -> str:
    """
    🔥 修改：添加返回值，返回warehouse路径

    Args:
        json_data (dict): 包含图片和音频URL的数据

    Returns:
        str: warehouse路径 或 生成的视频文件列表
    """
    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, IMAGE_FOLDER), exist_ok=True)
    os.makedirs(os.path.join(project_path, AUDIO_FOLDER), exist_ok=True)

    image_urls = json_data["output"]
    audio_urls = json_data["res"]

    # 🔥 新增：存储生成的视频文件路径
    generated_videos = []

    for i, (image_url, audio_url) in enumerate(zip(image_urls, audio_urls)):
        print(f"\n--- 正在处理第 {i + 1} 组 ---")

        # 下载图片和音频
        image_path = download_file(image_url, os.path.join(project_path, IMAGE_FOLDER), "png")
        audio_path = download_file(audio_url, os.path.join(project_path, AUDIO_FOLDER), "mp3")

        # 创建背景视频
        bg_video = random_background_clip(DURATION_PER_CLIP)
        bg_video = bg_video.with_effects(
            [vfx.HeadBlur(fx=lambda t: 540, fy=lambda t: 960, radius=5, intensity=3.0)])

        bg_video = blur(bg_video, sigma=20)
        bg_video = apply_black_overlay(bg_video, opacity=50)

        # 加载图片并设置位置和持续时间
        img_clip: VideoClip = ImageClip(image_path).with_duration(DURATION_PER_CLIP).resized(
            height=bg_video.h).with_position("center")

        effect_clip = img_clip.transform(make_wavy_image_func(img_clip))
        effect_clip = effect_clip.with_effects([vfx.FadeIn(1)])
        final_clip = concatenate_videoclips([effect_clip.subclipped(0, 1), img_clip.subclipped(1, DURATION_PER_CLIP)])

        # 叠加图片到背景视频上
        final_video = CompositeVideoClip([final_clip, bg_video, final_clip])

        # 加载音频
        audio = AudioFileClip(audio_path).subclipped(0, DURATION_PER_CLIP)
        final_video = final_video.with_audio(audio)

        # 导出最终视频
        output_path = os.path.join(project_path, f"video_{i + 1}.mp4")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        print(f"✅ 第 {i + 1} 个视频已生成：{output_path}")

        # 🔥 新增：添加到生成的视频列表
        generated_videos.append(output_path)

    print("\n🎉 所有视频生成完毕！")

    # 🔥 新增：返回warehouse路径
    if len(generated_videos) == 1:
        # 如果只有一个视频，返回单个文件的warehouse路径
        relative_path = os.path.relpath(generated_videos[0], user_data_dir)
        warehouse_path = relative_path.replace('\\', '/')
        print(f"📁 返回单个视频warehouse路径: {warehouse_path}")
        return warehouse_path
    else:
        # 如果有多个视频，返回项目目录的warehouse路径
        relative_path = os.path.relpath(project_path, user_data_dir)
        warehouse_path = relative_path.replace('\\', '/')
        print(f"📁 返回项目目录warehouse路径: {warehouse_path}")
        print(f"📋 生成的视频文件: {len(generated_videos)} 个")
        for i, video_path in enumerate(generated_videos, 1):
            video_warehouse_path = os.path.relpath(video_path, user_data_dir).replace('\\', '/')
            print(f"  {i}. {video_warehouse_path}")
        return warehouse_path


def trans_video_inciment_single_output(json_data: dict) -> str:
    """
    🔥 新增：合并所有视频为单个输出文件

    Args:
        json_data (dict): 包含图片和音频URL的数据

    Returns:
        str: 合并后视频的warehouse路径
    """
    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, IMAGE_FOLDER), exist_ok=True)
    os.makedirs(os.path.join(project_path, AUDIO_FOLDER), exist_ok=True)

    image_urls = json_data["output"]
    audio_urls = json_data["res"]

    # 存储所有视频剪辑
    all_video_clips = []

    for i, (image_url, audio_url) in enumerate(zip(image_urls, audio_urls)):
        print(f"\n--- 正在处理第 {i + 1} 组 ---")

        # 下载图片和音频
        image_path = download_file(image_url, os.path.join(project_path, IMAGE_FOLDER), "png")
        audio_path = download_file(audio_url, os.path.join(project_path, AUDIO_FOLDER), "mp3")

        # 创建背景视频
        bg_video = random_background_clip(DURATION_PER_CLIP)
        bg_video = bg_video.with_effects(
            [vfx.HeadBlur(fx=lambda t: 540, fy=lambda t: 960, radius=5, intensity=3.0)])

        bg_video = blur(bg_video, sigma=20)
        bg_video = apply_black_overlay(bg_video, opacity=50)

        # 加载图片并设置位置和持续时间
        img_clip: VideoClip = ImageClip(image_path).with_duration(DURATION_PER_CLIP).resized(
            height=bg_video.h).with_position("center")

        effect_clip = img_clip.transform(make_wavy_image_func(img_clip))
        effect_clip = effect_clip.with_effects([vfx.FadeIn(1)])
        final_clip = concatenate_videoclips([effect_clip.subclipped(0, 1), img_clip.subclipped(1, DURATION_PER_CLIP)])

        # 叠加图片到背景视频上
        final_video = CompositeVideoClip([final_clip, bg_video, final_clip])

        # 加载音频
        audio = AudioFileClip(audio_path).subclipped(0, DURATION_PER_CLIP)
        final_video = final_video.with_audio(audio)

        # 添加到总视频列表
        all_video_clips.append(final_video)
        print(f"✅ 第 {i + 1} 个视频片段已准备")

    print("\n🎬 开始合并所有视频片段...")

    # 合并所有视频片段
    if len(all_video_clips) == 1:
        merged_video = all_video_clips[0]
    else:
        merged_video = concatenate_videoclips(all_video_clips)

    # 导出合并后的视频
    final_output_path = os.path.join(project_path, "merged_video.mp4")
    merged_video.write_videofile(final_output_path, fps=24, codec="libx264", audio_codec="aac")

    print(f"✅ 合并视频已生成：{final_output_path}")
    print(f"🎯 总时长: {merged_video.duration:.2f}秒")
    print(f"📊 包含片段: {len(all_video_clips)} 个")

    # 返回warehouse路径
    relative_path = os.path.relpath(final_output_path, user_data_dir)
    warehouse_path = relative_path.replace('\\', '/')
    print(f"📁 warehouse路径: {warehouse_path}")

    return warehouse_path


if __name__ == "__main__":
    json_data = {
        "bgm": [
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/okIJWdCisB0A7AC1BOC0PNIQirniZMLbUYQt4"
        ],
        "output": [
            "https://p9-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/ced8ac9d81ef4765b09a7a3649ff0d11.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1780286206&x-signature=vupWhc0xvFBBt4CKpx%2BjCo4gHAE%3D"
        ],
        "res": [
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/okIJWdCisB0A7AC1BOC0PNIQirniZMLbUYQt4"
        ]
    }

    # 🔥 示例1：生成多个视频文件（返回项目目录路径）
    result_path = trans_video_inciment(json_data)
    print(f"✅ 返回的warehouse路径: {result_path}")

    # 🔥 示例2：生成单个合并视频文件
    # result_path = trans_video_inciment_single_output(json_data)
    # print(f"✅ 合并视频warehouse路径: {result_path}")
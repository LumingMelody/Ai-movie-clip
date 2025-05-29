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
# VIDEO_FOLDER = "videos"            # 本地视频文件夹路径
# OUTPUT_FOLDER = "output_videos"    # 输出视频保存路径
IMAGE_FOLDER = "images"  # 图片缓存目录
AUDIO_FOLDER = "audios"  # 音乐缓存目录

DURATION_PER_CLIP = 8  # 每个背景视频片段的时长（秒）
# folder_path = 'materials/enterprise'
folder_path = os.path.join(get_user_data_dir(), 'materials/enterprise')


# TOTAL_BACKGROUND_DURATION = 15     # 合成背景视频总时长（秒）
# IMAGE_DURATION = 15                # 每张图片展示时间（与背景视频、音乐同步）

# os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# -----------------------------
# 输入数据（来自你的 JSON）
# -----------------------------


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
    # overlay = overlay.set_opacity(opacity)  # 设置透明度
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
# 主循环：处理每组图片+音乐
# -----------------------------
def trans_video_inciment(json_data: dict) -> str:
    project_id = str(uuid.uuid1())
    base_project_path = "projects"
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, IMAGE_FOLDER), exist_ok=True)
    os.makedirs(os.path.join(project_path, AUDIO_FOLDER), exist_ok=True)

    image_urls = json_data["output"]
    audio_urls = json_data["res"]
    for i, (image_url, audio_url) in enumerate(zip(image_urls, audio_urls)):
        print(f"\n--- 正在处理第 {i + 1} 组 ---")

        # 下载图片和音频
        image_path = download_file(image_url, os.path.join(project_path, IMAGE_FOLDER), "png")
        audio_path = download_file(audio_url, os.path.join(project_path, AUDIO_FOLDER), "mp3")  # 假设是mp3格式

        # 创建背景视频
        bg_video = random_background_clip(DURATION_PER_CLIP)
        bg_video = bg_video.with_effects(
            [vfx.HeadBlur(fx=lambda t: 540, fy=lambda t: 960, radius=5, intensity=3.0)])  # 添加淡入效果

        bg_video = blur(bg_video, sigma=20)  # 添加淡入效果
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

    print("\n🎉 所有视频生成完毕！")


if __name__ == "__main__":
    json_data = {
        "bgm": [
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o01P9bQAMBKeUDf973mdOfbINRnWCEhoCSFNDf",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ocyiUPK0wrqAiE512IAOZrpWUBhMYkPBiSitR",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oERlDACeyIUODZMgWot5uLMBteEHnbNBDsTk1k",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEe8yzAhcDwFMQeJF8O4M5Izb4avJCBE9nOz5e",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEe8yzAhcDwFMQeJF8O4M5Izb4avJCBE9nOz5e",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEI2MQArZpwdClnkoeF0bEu3fZCtzDDgNiqnBp",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oIcGC9XdDIkespwFXABIf68RzJfInBIcablU6a",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oQYtGbAA7glZn2eYHsDDCHBCCAAeQT9glnma9I",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oMi0FFbhabMQIRz2aeAfIGeDwSCRxJ2GnBBICU",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ef190e6471c14c2e816ac35ea249b153"
        ],
        "output": [
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/d5faf3251ad948cf936cb639e4ee27dd.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846870&x-signature=EM53ciEBAU3nV2cvHhu8QZN8t9g%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/c1c1b551a2824ffbaea928d2de3fa1c5.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846876&x-signature=tVkDaxISZC%2BP9jt9aM6VdPPI5g8%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/eeef7fbdf11748308b151b38edda7f57.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846882&x-signature=2IJveNFa9aODpkj6kttuRcwTV9M%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/83fed2d630f34abdbd471bbb6b92121b.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846889&x-signature=FUHJKaQyUantQlLRc1MtjBBoPjc%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/0dee0c6bff7a47059be541201041fdb3.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846894&x-signature=cKmW7kH9xpyN90U9vAL8R1xP03A%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/b20fdad4f38c41e2877ae3be9bc5c9b5.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846901&x-signature=XJ5wsuLo9Gw%2FIzDokZqzmaUVhbs%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/1e6b434ebad84938b4d0610cb678c018.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846907&x-signature=nXJdGPVoehIbxQmeJ1UOv1AyK38%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/b0890cd5264f4fc4a0b83d33519e74d1.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846914&x-signature=d2Kode5%2FC6hjbOeW7ynnr4EQBck%3D",
            "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/c6581190139c48969bd09b3923f78086.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846920&x-signature=je6He7jheUE7A9N3cIsgRip8JJQ%3D",
            "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/9fb4962bbbb44f58b05dfee1ddda808a.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846925&x-signature=jwonJZn1ryaYVutxdn0iWN%2BWOqk%3D"
        ],
        "res": [
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o01P9bQAMBKeUDf973mdOfbINRnWCEhoCSFNDf",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ocyiUPK0wrqAiE512IAOZrpWUBhMYkPBiSitR",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oERlDACeyIUODZMgWot5uLMBteEHnbNBDsTk1k",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEe8yzAhcDwFMQeJF8O4M5Izb4avJCBE9nOz5e",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEe8yzAhcDwFMQeJF8O4M5Izb4avJCBE9nOz5e",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oEI2MQArZpwdClnkoeF0bEu3fZCtzDDgNiqnBp",
            "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oIcGC9XdDIkespwFXABIf68RzJfInBIcablU6a",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oQYtGbAA7glZn2eYHsDDCHBCCAAeQT9glnma9I",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/oMi0FFbhabMQIRz2aeAfIGeDwSCRxJ2GnBBICU",
            "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ef190e6471c14c2e816ac35ea249b153"
        ]
    }

    # json_data={
    # "bgm": [
    #     "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o01P9bQAMBKeUDf973mdOfbINRnWCEhoCSFNDf",

    # ],
    # "output": [
    #     "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/d5faf3251ad948cf936cb639e4ee27dd.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778846870&x-signature=EM53ciEBAU3nV2cvHhu8QZN8t9g%3D",

    # ],
    # "res": [
    #     "https://lf3-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o01P9bQAMBKeUDf973mdOfbINRnWCEhoCSFNDf",

    # ]
    # }

    trans_video_inciment(json_data)
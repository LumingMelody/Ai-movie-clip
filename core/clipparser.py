import os
import json
import uuid
import shutil
from urllib.parse import urlparse
import requests
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
    CompositeAudioClip
)
from moviepy.video import fx as vfx
from moviepy.audio import fx as afx  # 音频特效模块
from PIL import Image, ImageDraw  # 图像处理
import numpy as np  # 数值计算


# === 工具函数 ===

def download_file(url, target_dir="downloaded_resources"):
    """下载远程文件到本地
    Args:
        url: 文件URL地址
        target_dir: 本地保存目录
    Returns:
        本地文件路径
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)  # 创建目录如果不存在

    parsed = urlparse(url)
    # 生成唯一文件名避免冲突
    filename = f"{uuid.uuid4()}_{os.path.basename(parsed.path)}"
    filepath = os.path.join(target_dir, filename)

    print(f"正在下载 {url} 到 {filepath}")
    response = requests.get(url, stream=True)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 分块下载
            if chunk:
                f.write(chunk)
    return filepath


def hex_to_rgb(hex_color):
    """将十六进制颜色代码转换为RGB元组
    Args:
        hex_color: 十六进制颜色代码(如#FFFFFF)
    Returns:
        RGB元组(如(255,255,255))
    """
    hex_color = hex_color.lstrip('#')  # 去除#号
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def resolve_source(source_data):
    """解析资源来源
    Args:
        source_data: 包含type和path的字典
    Returns:
        本地文件路径
    Raises:
        FileNotFoundError: 本地文件不存在
        ValueError: 未知的资源类型
    """
    src_type = source_data["type"]
    path = source_data["path"]

    if src_type == "network":  # 网络资源
        return download_file(path)
    elif src_type == "local":  # 本地资源
        if not os.path.exists(path):
            raise FileNotFoundError(f"本地资源未找到: {path}")
        return path
    else:
        raise ValueError(f"未知的资源类型: {src_type}")


# === 基础元素创建 ===

def create_background(data):
    """创建背景剪辑
    Args:
        data: 背景配置数据
    Returns:
        背景剪辑对象
    """
    bg_type = data["type"]
    source_path = resolve_source(data["source"])  # 解析资源路径

    props = data.get("properties", {})
    duration = props.get("duration", 10)  # 默认10秒
    color = props.get("color")
    opacity = props.get("opacity", 1.0)  # 默认不透明
    loop = props.get("loop", False)  # 默认不循环

    if bg_type == "color":  # 纯色背景
        color = hex_to_rgb(color or "#000000")  # 默认黑色
        return ColorClip(size=(1080, 1920), color=color, duration=duration)
    elif bg_type == "image":  # 图片背景
        img_clip = ImageClip(source_path).set_duration(duration)
        if opacity < 1.0:  # 设置透明度
            img_clip = img_clip.set_opacity(opacity)
        return img_clip.resize(newsize=(1080, 1920))  # 调整到1080x1920
    elif bg_type == "video":  # 视频背景
        vid_clip = VideoFileClip(source_path)
        if loop and duration > vid_clip.duration:  # 需要循环
            loops_needed = int(duration // vid_clip.duration) + 1
            clips = [vid_clip] * loops_needed
            vid_clip = concatenate_videoclips(clips)  # 拼接视频实现循环
        return vid_clip.subclip(0, duration)  # 截取指定时长
    elif bg_type == "gradient":  # 渐变背景
        def make_frame(t):
            """生成渐变帧"""
            img = Image.new("RGB", (1080, 1920))
            draw = ImageDraw.Draw(img)
            for y in range(1920):
                r = int(255 * (y / 1920))
                g = int(128 * (y / 1920))
                b = int(64 * (y / 1920))
                draw.line((0, y, 1080, y), fill=(r, g, b))
            return np.array(img)
        return ColorClip(size=(1080, 1920), duration=duration, make_frame=make_frame)
    else:
        raise ValueError(f"不支持的背景类型: {bg_type}")


def create_main_video(data):
    """创建主视频剪辑
    Args:
        data: 主视频配置数据
    Returns:
        主视频剪辑对象
    """
    source_path = resolve_source(data["source"])
    main_clip = VideoFileClip(source_path).subclip(
        data["in_point"],
        data["in_point"] + data["duration"]
    )
    if "speed" in data:  # 调整播放速度
        main_clip = main_clip.fx(vfx.speedx, factor=data["speed"])
    return main_clip


def add_sticker(base_clip, sticker_data):
    """添加贴纸到视频
    Args:
        base_clip: 基础视频剪辑
        sticker_data: 贴纸配置数据
    Returns:
        合成后的视频剪辑
    """
    source_path = resolve_source(sticker_data["source"])
    sticker = ImageClip(source_path)
    # 设置贴纸位置和大小
    sticker = sticker.set_position((
        sticker_data["position"]["x"],
        sticker_data["position"]["y"]
    ))
    sticker = sticker.resize(width=sticker_data["size"]["width"])
    sticker = sticker.set_duration(sticker_data["duration"])
    return CompositeVideoClip([base_clip, sticker])  # 合成贴纸和视频


def apply_effect(clip, effect_data):
    """应用视频特效
    Args:
        clip: 视频剪辑
        effect_data: 特效配置数据
    Returns:
        应用特效后的视频剪辑
    """
    name = effect_data["name"]
    params = effect_data.get("parameters", {})

    if name == "blur":  # 模糊特效
        radius = params.get("radius", 0)
        return clip.fx(vfx.gaussian_blur, radius)
    return clip


def apply_transition(clip, transition_data, is_outgoing=True):
    """应用转场效果
    Args:
        clip: 视频剪辑
        transition_data: 转场配置数据
        is_outgoing: 是否为出场转场
    Returns:
        应用转场后的视频剪辑
    """
    t_type = transition_data["type"]
    duration = transition_data["duration"]

    if t_type == "fade_in":  # 淡入效果
        return clip.fx(vfx.fadein, duration)
    elif t_type == "fade_out":  # 淡出效果
        return clip.fx(vfx.fadeout, duration)
    elif t_type == "wipe":  # 擦除效果(需要自定义实现)
        pass
    return clip


def audio_loop(audio_clip, duration):
    """循环音频到指定时长
    Args:
        audio_clip: 音频剪辑
        duration: 目标时长
    Returns:
        循环后的音频剪辑
    """
    loops_needed = int(duration // audio_clip.duration) + 1
    looped_audio = concatenate_videoclips([audio_clip] * loops_needed)
    return looped_audio.set_duration(duration)


def set_background_music(audio_data):
    """设置背景音乐
    Args:
        audio_data: 音频配置数据
    Returns:
        音频剪辑对象
    """
    source_path = resolve_source(audio_data["source"])
    audio_clip = AudioFileClip(source_path)
    if audio_data.get("loop", False):  # 需要循环
        audio_clip = audio_loop(audio_clip, duration=audio_data.get("duration", 10))
    return audio_clip.fx(afx.volumex, audio_data["volume"])  # 调整音量


def set_voiceover(audio_data):
    """设置旁白/配音
    Args:
        audio_data: 音频配置数据
    Returns:
        音频剪辑对象
    """
    source_path = resolve_source(audio_data["source"])
    return AudioFileClip(source_path).fx(afx.volumex, audio_data["volume"])


def add_sound_effect(effect_data):
    """添加音效
    Args:
        effect_data: 音效配置数据
    Returns:
        音效剪辑对象
    """
    source_path = resolve_source(effect_data["source"])
    return AudioFileClip(source_path).fx(afx.volumex, effect_data["volume"])


def add_subtitle(base_clip, subtitle_data):
    """添加字幕到视频
    Args:
        base_clip: 基础视频剪辑
        subtitle_data: 字幕配置数据
    Returns:
        合成后的视频剪辑
    """
    style = subtitle_data["style"]

    # 处理背景色透明度
    bg_color = style.get("background_color", "#000000")
    if len(bg_color) > 7:  # 包含透明度信息(如#00000080)
        hex_opacity = bg_color[7:9]
        opacity = int(hex_opacity, 16) / 255
        bg_color = bg_color[:7]
    else:
        opacity = 0.5  # 默认半透明

    # 创建文字剪辑
    txt_clip = TextClip(
        subtitle_data["text"],
        fontsize=style.get("size", 24),
        font=style.get("font", "Arial"),
        color=style.get("color", "#FFFFFF").lstrip("#"),
        bg_color=bg_color.lstrip("#"),
        method="caption",  # 自动换行
        size=(1080 * 0.8, None)  # 宽度为视频宽度的80%，高度自动
    )

    # 设置位置和时间
    txt_clip = txt_clip.set_position(("center", subtitle_data["position"]["y"]))
    txt_clip = txt_clip.set_start(subtitle_data["start_time"])
    txt_clip = txt_clip.set_duration(subtitle_data["end_time"] - subtitle_data["start_time"])

    # 设置透明度
    if opacity < 1.0:
        txt_clip = txt_clip.set_opacity(opacity)

    return CompositeVideoClip([base_clip, txt_clip])  # 合成字幕和视频


# === 主解析器 ===

def parse_video_segment(json_data):
    """解析视频片段配置
    Args:
        json_data: JSON配置数据
    Returns:
        合成后的视频剪辑对象
    """
    segment = json_data["video_segment"]

    # 1. 创建背景
    background_clip = create_background(segment["background"])

    # 2. 创建主视频
    main_clip = create_main_video(segment["main_video"])

    # 调整主视频速度
    if "speed" in segment["main_video"]:
        main_clip = main_clip.fx(vfx.speedx, factor=segment["main_video"]["speed"])

    # 设置主视频转场
    if "transition_in" in segment["main_video"]:
        main_clip = main_clip.fx(vfx.fadein, segment["main_video"]["transition_in"])
    if "transition_out" in segment["main_video"]:
        main_clip = main_clip.fx(vfx.fadeout, segment["main_video"]["transition_out"])

    # 合成背景和主视频
    combined_clip = CompositeVideoClip([background_clip, main_clip])

    # 3. 添加贴纸
    for sticker in segment.get("stickers", []):
        combined_clip = add_sticker(combined_clip, sticker)

    # 4. 添加特效
    for effect in segment.get("effects", []):
        combined_clip = apply_effect(combined_clip, effect)

    # 5. 处理转场
    if "transition" in segment:
        combined_clip = apply_transition(combined_clip, segment["transition"], is_outgoing=True)

    # 6. 处理音频
    bg_audio = None
    voice_audio = None
    se_audios = []

    if "audio" in segment:
        if "background_music" in segment["audio"]:
            bg_audio = set_background_music(segment["audio"]["background_music"])
        if "voiceover" in segment["audio"]:
            voice_audio = set_voiceover(segment["audio"]["voiceover"])
        if "sound_effects" in segment["audio"]:
            se_audios = [add_sound_effect(se) for se in segment["audio"]["sound_effects"]]

    # 合并所有音频轨道
    all_audios = []
    if bg_audio:
        all_audios.append(bg_audio.set_duration(segment["duration"]))
    if voice_audio:
        all_audios.append(voice_audio.set_start(0))
    all_audios.extend(se_audios)

    if all_audios:
        final_audio = CompositeAudioClip(all_audios).set_duration(segment["duration"])
        combined_clip = combined_clip.set_audio(final_audio)

    # 7. 添加字幕
    for subtitle in segment.get("subtitles", []):
        combined_clip = add_subtitle(combined_clip, subtitle)

    # 设置最终时长
    combined_clip = combined_clip.set_duration(segment["duration"])

    return combined_clip


# === 使用示例 ===

if __name__ == "__main__":
    # 示例：从JSON文件加载配置
    try:
        with open("segment.json", "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # 解析为视频剪辑对象
        final_clip = parse_video_segment(json_data)

        # 导出视频
        output_path = "output.mp4"
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )

        print(f"✅ 视频已成功导出到: {output_path}")
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists("downloaded_resources"):
            shutil.rmtree("downloaded_resources")
            print("✅ 临时文件已清理")
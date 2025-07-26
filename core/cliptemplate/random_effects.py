import random
from functools import partial
from moviepy import VideoClip,ImageClip,VideoFileClip,concatenate_videoclips
import uuid

from core.clipeffects.easy_clip_effects import (
    zoom_in, zoom_out, pan, rotate, apply_fisheye_and_pan,
    ease_in_out_quad
)
# 权重+参数配置的特效列表
effects = [
    {
        "name": "zoom_in",
        "func": zoom_in,
        "weight": 15,
        "params": {
            "duration": lambda: random.choice([1, 2, 3]),
            "intensity": lambda: random.uniform(0.1, 0.5),
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "zoom_out",
        "func": zoom_out,
        "weight": 15,
        "params": {
            "duration": lambda: random.choice([1, 2, 3]),
            "intensity": lambda: random.uniform(0.1, 0.5),
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "pan_left",
        "func": pan,
        "weight": 10,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "intensity": lambda: random.randint(50, 200),
            "direction": lambda: "left",
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "pan_right",
        "func": pan,
        "weight": 10,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "intensity": lambda: random.randint(50, 200),
            "direction": lambda: "right",
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "rotate_90",
        "func": rotate,
        "weight": 10,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "degrees": lambda: 90,
           
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "rotate_180",
        "func": rotate,
        "weight": 10,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "degrees": lambda: 180,
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "fisheye_pan_left",
        "func": apply_fisheye_and_pan,
        "weight": 1,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "intensity": lambda: random.randint(50, 150),
            "direction": lambda: "left",
            
        },
        "easing": ease_in_out_quad
    },
    {
        "name": "fisheye_pan_right",
        "func": apply_fisheye_and_pan,
        "weight": 1,
        "params": {
            "duration": lambda: random.choice([2, 3]),
            "intensity": lambda: random.randint(50, 150),
            "direction": lambda: "right",
            
        },
        "easing": ease_in_out_quad
    },
]


def apply_random_effects(clip: VideoClip, count=1):
    names = [e["name"] for e in effects]
    weights = [e["weight"] for e in effects]

    selected_indices = random.choices(range(len(effects)), weights=weights, k=count)
    selected_effects = [effects[i] for i in selected_indices]

    print("Selected Effects:", [e["name"] for e in selected_effects])

    for effect in selected_effects:
        func = effect["func"]
        
        # 构造参数：仅调用那些无参可调用项（比如 lambda: random.xxx）
        params = {
            k: v() if callable(v) and not isinstance(v, partial) and v.__name__ == '<lambda>' else v
            for k, v in effect.get("params", {}).items()
        }
        
        # 添加 easing 参数（保持函数本身，不调用）
        if "easing" in effect:
            params["easing"] = effect["easing"]

        clip = func(clip, **params)

    return clip

##TODO:目前特效还是待优化
def create_video_from_media(media_path, target_duration=20):
    """
    根据输入的图片或视频创建一个带有特效的20秒视频。
    
    :param media_path: 输入媒体文件路径（图片或视频）
    :param output_path: 输出视频文件路径
    :param target_duration: 目标视频时长（秒）
    """
    if media_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        # 处理图片
        clip = ImageClip(media_path).with_duration(5)
    else:
        # 处理视频
        clip = VideoFileClip(media_path)

    if clip.duration < target_duration:
        # 视频长度不足则循环播放
        loops = int(target_duration // clip.duration) + 1
        clips = []
        for i in range(loops):
            temp_clip=apply_random_effects(clip, count=random.randint(1, 2))
            outputpath="temp/"+str(uuid.uuid1())+".mp4"
            
            temp_clip.write_videofile(outputpath, codec="libx264", fps=24)
            clips.append(VideoFileClip(outputpath))
        final_clip = concatenate_videoclips(clips)
        if  final_clip.duration>target_duration:
            clip_with_effects = final_clip.subclipped(0, target_duration)
        else:
            clip_with_effects = final_clip
        
        
    else:
        # 裁剪视频到目标时长
        clip = clip.subclipped(0, target_duration)
        # 应用随机特效
        clip_with_effects = apply_random_effects(clip, count=random.randint(1, 2))

    # # 应用特效
    # clip_with_effects = apply_random_effects(clip, count=random.randint(1, 2))

    # 输出视频
    # clip_with_effects.write_videofile(output_path, codec="libx264", fps=clip.fps)
    return clip_with_effects

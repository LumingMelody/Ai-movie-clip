from moviepy import ImageClip, ColorClip, VideoFileClip, CompositeVideoClip, AudioFileClip, TextClip


def create_background(data):
    """
    data: 包含 background 信息的字典
    返回：一个 VideoClip 对象
    """
    print("Creating background:", data)
    # 示例逻辑：
    if data["type"] == "color":
        return ColorClip(size=(1080, 1920), color=hex_to_rgb(data["source"]), duration=data.get("duration", 10))
    elif data["type"] == "image":
        return ImageClip(data["source"], duration=data.get("duration", 10))
    elif data["type"] == "video":
        return VideoFileClip(data["source"]).subclip(0, data.get("duration", None))
    elif data["type"] == "gradient":
        # 自定义渐变背景
        pass

def create_main_video(data):
    """
    data: main_video 字段数据
    返回：裁剪后的主视频 clip
    """
    print("Creating main video:", data)
    return VideoFileClip(data["source"]).subclip(data["in_point"], data["in_point"] + data["duration"])

def apply_speed_effect(clip, speed):
    print("Applying speed effect:", speed)
    return clip.fx(vfx.speedx, speed)

def add_sticker(clip, sticker_data):
    """
    添加贴花（叠加图层）
    """
    print("Adding sticker:", sticker_data)
    sticker = ImageClip(sticker_data["source"])
    sticker = sticker.set_position((sticker_data["position"]["x"], sticker_data["position"]["y"]))
    sticker = sticker.resize(width=sticker_data["size"]["width"])
    sticker = sticker.set_duration(sticker_data["duration"])
    if "animation" in sticker_data:
        # 动画效果比如缩放、淡入等
        pass
    return CompositeVideoClip([clip, sticker])

def apply_effect(clip, effect_data):
    """
    应用滤镜/特效
    """
    print("Applying effect:", effect_data)
    if effect_data["name"] == "blur":
        radius = effect_data["parameters"].get("radius", 0)
        return clip.fx(vfx.blur, radius)
    return clip

def apply_transition(clip, transition_data, is_outgoing=True):
    """
    应用转场效果
    """
    print("Applying transition:", transition_data)
    transition_type = transition_data["type"]
    duration = transition_data["duration"]
    if transition_type == "fade_in":
        return clip.crossfadein(duration)
    elif transition_type == "fade_out":
        return clip.crossfadeout(duration)
    return clip

def set_background_music(audio_data):
    """
    加载背景音乐
    """
    print("Setting background music:", audio_data)
    return AudioFileClip(audio_data["source"]).volumex(audio_data["volume"])

def set_voiceover(audio_data):
    """
    加载语音旁白
    """
    print("Setting voiceover:", audio_data)
    return AudioFileClip(audio_data["source"]).volumex(audio_data["volume"])

def add_sound_effect(effect_data):
    """
    添加音效
    """
    print("Adding sound effect:", effect_data)
    return AudioFileClip(effect_data["source"]).volumex(effect_data["volume"])

def add_subtitle(clip, subtitle_data):
    """
    添加字幕
    """
    print("Adding subtitle:", subtitle_data["text"])
    txt_clip = TextClip(
        subtitle_data["text"],
        fontsize=subtitle_data["style"]["size"],
        font=subtitle_data["style"]["font"],
        color=subtitle_data["style"]["color"].lstrip("#"),
        bg_color=subtitle_data["style"]["background_color"].lstrip("#")
    )
    txt_clip = txt_clip.set_position((subtitle_data["position"]["x"], subtitle_data["position"]["y"]))
    txt_clip = txt_clip.set_duration(subtitle_data["end_time"] - subtitle_data["start_time"])
    txt_clip = txt_clip.set_start(subtitle_data["start_time"])
    return CompositeVideoClip([clip, txt_clip])
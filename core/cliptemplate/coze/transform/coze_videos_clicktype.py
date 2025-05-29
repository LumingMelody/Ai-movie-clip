from moviepy import *
import numpy as np
import os
import uuid

from config import get_user_data_dir

# 参数设置

fontsize = 60
title_size = 100
text_color = 'white'
text_bg_color = 'transparent'  # 文字背景透明
cursor_char = '|'  # 光标字符
cursor_color = 'white'
cursor_color_rgb = (255, 255, 255)
interval_per_char = 0.2  # 每个字符间隔（秒）
background_duration = 5  # 每张背景持续时间（秒）
blink_duration = 0.5  # 光标闪烁周期（秒）
fps = 24  # 帧率
video_size = (1080, 1920)  # 竖版视频尺寸
# audio_path = 'materials\\keyboard\\keyboard-typing-3-292593.mp3'  # 背景音乐路径
audio_path = os.path.join(get_user_data_dir(), 'materials', 'keyboard', 'keyboard-typing-3-292593.mp3')
text_widths = []
text_heights = []


# 创建背景轮换视频
def create_background_clips(background_images, total_duration):
    clips = []
    for img in background_images:
        clip = (ImageClip(img, duration=background_duration)
                .resized(height=video_size[1])  # 保持宽高比
                .with_position('center')
                )
        clips.append(clip)
    return concatenate_videoclips(clips, method='chain').with_duration(total_duration)


def crate_title_clip(title, total_duration):
    if len(title) > 8:
        result = []
        for i in range(0, len(title), 8):
            result.append(title[i:i + 8])  # 截取一段文本
        res = '\n'.join(result)  # 使用换行符连接
    else:
        res = title
    title_clip = TextClip(font="simhei", text=res, font_size=title_size, margin=(16, 16), color="Black",
                          bg_color="Yellow", text_align="center", method='label')
    title_clip.with_position(("center", 0.15), relative=True)  # 设置标题位置
    return CompositeVideoClip([title_clip], size=video_size).with_duration(total_duration)


# 创建打字动画
def create_typing_animation(text, total_duration):
    clips = []
    global text_widths  # 存储每个文本片段的宽度
    global text_heights  # 存储每个文本片段的高度

    text_h_last = 4
    origin_w = 0
    aign_i = 0
    for i in range(len(text) + 1):
        current_text = text[:i]
        # generator = lambda txt: TextClip(font=font_name, text=txt,font_size=font_size, color=font_color, stroke_color='Black', stroke_width=4, size=(1920,500),vertical_align="bottom", method='caption')
        text_clip = TextClip("微软雅黑.ttf", current_text,
                             font_size=fontsize,
                             color=text_color,
                             stroke_color='Yellow',
                             stroke_width=2,
                             # bg_color=text_bg_color,
                             text_align='left')

        if i == 1:
            origin_w = int(text_clip.w)
        # 计算位置：水平居中，垂直在1/3处
        text_w = text_clip.w
        text_h = text_clip.h
        # if current_text=="/n":
        #     text_h=text_h+text_h

        x = (video_size[0] - text_w) // 2
        y = video_size[1] // 3  # 垂直三分之一处

        text_clip = text_clip.with_position((x, y))
        if text[i - 1:i] == "\n":
            text_w = 0
            aign_i = 0
        text_w = origin_w * aign_i
        text_widths.append(text_w)
        text_heights.append(text_h)

        # 设置片段时长和起始时间
        clip = text_clip.with_duration(interval_per_char) \
            .with_start(i * interval_per_char)
        clips.append(clip)
        text_h_last = text_h
        aign_i += 1

    return CompositeVideoClip(clips, size=video_size).with_duration(total_duration)


# 创建闪烁光标
def create_blinking_cursor(text_widths, text, total_duration):
    cursor = TextClip("微软雅黑.ttf", cursor_char,
                      font_size=fontsize,
                      color=cursor_color,
                      transparent=True)

    cursor_clips = []
    origin_h = text_heights[3]
    max_w = max(text_widths)
    lines = 0
    for i in range(len(text) + 1):
        # 计算当前位置
        text_w = text_widths[i]
        text_h = text_heights[i]
        if text_h > origin_h:
            x = (video_size[0] - max_w) // 2 + text_w
        else:
            x = (video_size[0] - text_w) // 2 + text_w
        # x = (video_size[0] - text_w) // 2 + text_w
        y = (video_size[1] // 3) - origin_h + text_h

        # 创建闪烁片段
        start_time = i * interval_per_char
        end_time = start_time + interval_per_char

        # 光标闪烁周期
        blink_on = cursor.with_position((x, y)) \
            .with_start(start_time) \
            .with_duration(blink_duration / 2)
        blink_off = cursor.with_position((x + 80, y)) \
            .with_start(start_time + blink_duration / 2) \
            .with_duration(blink_duration / 2) \
            .with_effects([vfx.MaskColor(color=cursor_color_rgb, stiffness=0)])

        cursor_clips.append(blink_on)
        cursor_clips.append(blink_off)

    return CompositeVideoClip(cursor_clips, size=video_size) \
        .with_duration(total_duration)


def get_video_clicktype_var(text, title, background_images, bgm_path, project_path):
    result = []
    result_text = ''
    # 遍历数据中的每个条目
    for item in text:
        # 提取标题和内容
        title = item['p_title']
        content = item['p_content']

        # 拼接当前条目
        line = title

        # 如果内容长度超过10，追加换行符
        if len(content) > 10:
            for i in range(0, len(content), 10):
                line += content[i:i + 10] + '\n'
        else:
            line += content
        #

        # 将当前条目添加到结果中
        result_text += line

    # 所有条目拼接完成后，最后添加一个换行符
    result_text += '\n'
    # for i in range(0, len(text), 10):

    #     result.append(text[i:i + 10])  # 截取一段文本
    # res= '\n'.join(result)  # 使用换行符连接
    res = result_text
    # 计算总时长
    total_text_duration = len(res) * interval_per_char + 1
    total_background_duration = background_duration * len(background_images)
    total_duration = min(total_text_duration, total_background_duration)
    # 创建各部分
    background = create_background_clips(background_images, total_duration)
    typing = create_typing_animation(res, total_duration)
    cursor = create_blinking_cursor(text_widths, res, total_duration)
    title = crate_title_clip(title, total_duration)

    # 组合视频
    final_video = CompositeVideoClip([
        background,
        typing,
        cursor,
        title.with_position(("center", 0.15), relative=True)
    ], size=video_size).with_duration(total_duration)

    # 添加背景音乐

    audio = AudioFileClip(audio_path)
    # audio = audio.with_duration(total_duration).with_start(0)
    audio = audio.with_effects([afx.AudioLoop(duration=total_duration)])
    final_audio = CompositeAudioClip([audio, AudioFileClip(bgm_path).subclipped(0, total_duration)])
    final_video = final_video.with_audio(final_audio)

    output_path = os.path.join(project_path, "final_video_with_bgm.mp4")
    # 导出视频
    final_video.write_videofile(output_path,
                                fps=fps,
                                codec='libx264',
                                threads=4)
    return output_path


def trans_video_clicktype(data: dict):
    # data = {
    #     "text": "这是一段竖版打字效果文字示例,这是一段竖版打字效果文字示例",
    #     "background_images": ['1.png', '2.png', '3.png'],
    #     "bgm_path": 'bgm_audio.mp3'
    # }

    project_id = str(uuid.uuid1())
    base_project_path = "projects"
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    def download_file(url, local_filename):
        import requests
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            local_filename = os.path.join(project_path, local_filename)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename

    # 下载并加载所有资源
    bgm_path = download_file(data['bgm_audio'], "bg_audio.mp3")
    # audio_clips = [AudioFileClip(download_file(mp3_url, f"mp3_{i}.mp3")) for i, mp3_url in enumerate(data['mp3_urls'])]
    background_images = [download_file(image_url, f"img_{i}.png") for i, image_url in enumerate(data['image_url'])]
    # background_image = ImageClip(download_file(data['images2'], "background.png"),duration=sum(data['mp3_durations']))
    text = data['content']  # 要显示的文字
    title = data['title']

    output_path = get_video_clicktype_var(text, title, background_images, bgm_path, project_path)
    return output_path


# 主程序
def main():
    background_images = ['1.png', '2.png', '3.png']  # 背景图片路径
    text = "这是一段竖版打字效果\n文字示例\n,这是一段竖版打\n字效果\n文字示例"  # 要显示的文字
    bgm_path = 'bgm_audio.mp3'

    # 计算总时长
    total_text_duration = len(text) * interval_per_char
    total_background_duration = background_duration * len(background_images)
    total_duration = min(total_text_duration, total_background_duration)
    # 创建各部分
    background = create_background_clips()
    typing = create_typing_animation()
    cursor = create_blinking_cursor(text_widths)

    # 组合视频
    final_video = CompositeVideoClip([
        background,
        typing,
        cursor
    ], size=video_size).with_duration(total_duration)

    # 添加背景音乐

    audio = AudioFileClip(audio_path)
    # audio = audio.with_duration(total_duration).with_start(0)
    audio = audio.with_effects([afx.AudioLoop(duration=total_duration)])
    final_audio = CompositeAudioClip([audio, AudioFileClip(bgm_path)])
    final_video = final_video.with_audio(final_audio)

    # 导出视频
    final_video.write_videofile("vertical_typing.mp4",
                                fps=fps,
                                codec='libx264',
                                threads=4)


if __name__ == "__main__":
    # # main()
    # get_video_clicktype("这是一段竖版打字效果文字示例,这是一段竖版打字效果文字示例", ['1.png', '2.png', '3.png'], 'bgm_audio.mp3')
    data = {
        "bgm_audio": "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/o05OFVeDEizyOMrIaCeOFtNnAgaE1BI4bWnaeS",
        "content": [
            {
                "p_content": "你知道吗？在商业江湖里，财税宛如神秘密钥。",
                "p_title": "财税在商业江湖的地位"
            },
            {
                "p_content": "无数企业因它起起落落，这里面藏着怎样惊心动魄的秘密？",
                "p_title": "财税对企业的影响"
            },
            {
                "p_content": "快来一探究竟！",
                "p_title": "呼吁探索财税秘密"
            }
        ],
        "image_url": [
            "https://s.coze.cn/t/TNXW9iRFSHA/",
            "https://s.coze.cn/t/U4BoMykGP1w/",
            "https://s.coze.cn/t/jXAH8OKo_cg/"
        ],
        "title": "财税"
    }
    trans_video_clicktype(data)
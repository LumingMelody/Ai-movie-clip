from moviepy import *
import numpy as np
import os
import uuid
import textwrap

from config import get_user_data_dir

# 参数设置
fontsize = 48
title_fontsize = 60
content_fontsize = 40
main_title_size = 80
text_color = 'white'
title_color = '#FFD700'
content_color = '#FFFFFF'
interval_per_char = 0.12
pause_between_sections = 1.5
background_duration = 8
fps = 24
video_size = (1080, 1920)
audio_path = os.path.join(get_user_data_dir(), 'materials', 'keyboard', 'keyboard-typing-3-292593.mp3')

# 文本区域设置
TEXT_MARGIN = 60
TEXT_START_Y = video_size[1] // 4


def safe_text_clip(text, **kwargs):
    """安全创建文本clip"""
    try:
        if not text or len(text.strip()) == 0:
            text = " "
        clip = TextClip(text=text, **kwargs)
        if hasattr(clip, 'size') and (clip.size[0] <= 0 or clip.size[1] <= 0):
            print(f"⚠️ TextClip尺寸异常: {clip.size}")
            clip = clip.resize((max(clip.size[0], 50), max(clip.size[1], 50)))
        return clip
    except Exception as e:
        print(f"❌ 创建TextClip失败: {e}")
        return TextClip(text=" ", font_size=kwargs.get('font_size', 50), color=kwargs.get('color', 'white'))


def wrap_text_to_width(text, max_width_chars=20):
    """文本换行"""
    if not text:
        return ""
    return textwrap.fill(text, width=max_width_chars, break_long_words=True)


def create_background_clips(background_images, total_duration):
    """创建背景"""
    clips = []
    try:
        for i, img in enumerate(background_images):
            if not os.path.exists(img):
                print(f"⚠️ 背景图片不存在: {img}")
                continue
            clip = (ImageClip(img, duration=background_duration)
                    .resized(height=video_size[1])
                    .with_position('center'))
            clips.append(clip)

        if not clips:
            print("🔧 创建默认背景")
            default_bg = ImageClip([[0, 0, 0] for _ in range(100)], duration=total_duration).resize(video_size)
            return default_bg

        return concatenate_videoclips(clips, method='chain').with_duration(total_duration)
    except Exception as e:
        print(f"❌ 创建背景失败: {e}")
        return ImageClip([[0, 0, 0] for _ in range(100)], duration=total_duration).resize(video_size)


def create_main_title_clip(title, total_duration):
    """创建主标题"""
    try:
        if not title:
            title = "默认标题"
        wrapped_title = wrap_text_to_width(title, 12)
        title_clip = safe_text_clip(
            text=wrapped_title,
            font="simhei",
            font_size=main_title_size,
            margin=(20, 20),
            color="Black",
            bg_color="Yellow",
            text_align="center",
            method='label'
        )
        if title_clip.size[0] <= 0 or title_clip.size[1] <= 0:
            title_clip = title_clip.resize((400, 100))
        return title_clip.with_position(("center", 0.08), relative=True).with_duration(total_duration)
    except Exception as e:
        print(f"❌ 创建主标题失败: {e}")
        default_title = safe_text_clip(text="标题", font_size=main_title_size, color="white")
        return default_title.with_position('center').with_duration(total_duration)


def create_no_overlap_typing_effect(sections_data, total_duration):
    """创建无重叠的打字效果，去掉光标"""
    print("🔤 创建无重叠打字效果（无光标）")

    all_clips = []
    current_time = 0
    current_y = TEXT_START_Y

    for section_idx, section in enumerate(sections_data):
        section_title = section.get('p_title', '').strip()
        section_content = section.get('p_content', '').strip()

        print(f"📝 处理第 {section_idx + 1} 段")

        # 处理标题
        if section_title:
            wrapped_title = wrap_text_to_width(section_title, 18)
            title_clips = create_text_sequence(
                wrapped_title, current_time, current_y,
                title_fontsize, title_color
            )
            all_clips.extend(title_clips)

            # 更新时间和位置
            title_char_count = len(wrapped_title.replace('\n', ''))
            current_time += title_char_count * interval_per_char + 0.5
            current_y += 80

        # 处理内容
        if section_content:
            wrapped_content = wrap_text_to_width(section_content, 22)
            content_clips = create_text_sequence(
                wrapped_content, current_time, current_y,
                content_fontsize, content_color
            )
            all_clips.extend(content_clips)

            # 更新时间和位置
            content_char_count = len(wrapped_content.replace('\n', ''))
            current_time += content_char_count * interval_per_char + 0.5
            current_y += 100

        # 段落间停顿
        current_time += pause_between_sections
        current_y += 40

        # 检查是否需要换屏
        if current_y > video_size[1] - 200:
            current_y = TEXT_START_Y

    if not all_clips:
        default_clip = safe_text_clip(text="默认内容", font_size=content_fontsize, color=content_color)
        default_clip = default_clip.with_position('center').with_duration(total_duration)
        all_clips = [default_clip]

    return CompositeVideoClip(all_clips, size=video_size).with_duration(total_duration)


def create_text_sequence(text, start_time, y_pos, font_size, color):
    """为文本创建打字序列 - 最简单的方法"""
    clips = []

    if not text.strip():
        return clips

    # 处理多行
    lines = text.split('\n')
    line_start_time = start_time
    line_y = y_pos

    for line in lines:
        if not line.strip():
            continue

        line_clips = create_line_sequence(line, line_start_time, line_y, font_size, color)
        clips.extend(line_clips)

        # 更新时间和位置
        line_start_time += len(line) * interval_per_char + 0.2
        line_y += font_size + 15

    return clips


def create_line_sequence(line, start_time, y_pos, font_size, color):
    """为单行创建打字序列 - 超级简单版本"""
    clips = []

    if not line.strip():
        return clips

    # 最关键：为每个字符位置只创建一个clip，避免重叠
    for i in range(len(line)):
        # 当前要显示的完整文本（从开头到第i个字符）
        current_text = line[:i + 1]

        # 创建文本clip
        text_clip = safe_text_clip(
            text=current_text,
            font="微软雅黑.ttf",
            font_size=font_size,
            color=color,
            stroke_color='black',
            stroke_width=1,
            text_align='left'
        )

        # 计算位置（居中）
        text_x = (video_size[0] - text_clip.size[0]) // 2
        text_y = y_pos

        # 确保在边界内
        text_x = max(TEXT_MARGIN, min(text_x, video_size[0] - text_clip.size[0] - TEXT_MARGIN))
        text_y = max(50, min(text_y, video_size[1] - text_clip.size[1] - 50))

        # 设置时间 - 关键点：每个clip只显示很短的时间
        clip_start = start_time + i * interval_per_char

        # 重要：只有最后一个字符的clip需要持续显示
        if i == len(line) - 1:
            # 最后一个字符持续显示到下一段开始
            clip_duration = interval_per_char * 5  # 持续一段时间
        else:
            # 中间的字符只显示到下一个字符出现
            clip_duration = interval_per_char

        # 创建clip
        text_clip = text_clip.with_position((text_x, text_y)).with_start(clip_start).with_duration(clip_duration)
        clips.append(text_clip)

    return clips


def get_video_clicktype_simple_no_cursor(sections, title, background_images, bgm_path, project_path):
    """生成无光标的简单视频"""
    try:
        print("🎬 开始生成无光标版本视频")

        # 估算时长
        total_chars = sum(len(s.get('p_title', '') + s.get('p_content', '')) for s in sections)
        estimated_duration = total_chars * interval_per_char + len(sections) * pause_between_sections + 10
        total_background_duration = background_duration * len(background_images)
        total_duration = min(estimated_duration, total_background_duration)

        print(f"⏱️ 总时长: {total_duration:.2f}秒")

        # 创建各部分
        print("🖼️ 创建背景...")
        background = create_background_clips(background_images, total_duration)

        print("🔤 创建打字动画...")
        typing_animation = create_no_overlap_typing_effect(sections, total_duration)

        print("🏷️ 创建主标题...")
        main_title = create_main_title_clip(title, total_duration)

        # 组合视频 - 不包括光标
        print("🎬 组合视频...")
        final_clips = [background, typing_animation, main_title]

        final_video = CompositeVideoClip(final_clips, size=video_size).with_duration(total_duration)

        # 处理音频
        print("🎵 处理音频...")
        try:
            audio_clips = []

            if os.path.exists(audio_path):
                keyboard_audio = AudioFileClip(audio_path)
                keyboard_audio = keyboard_audio.with_effects([afx.AudioLoop(duration=total_duration)])
                keyboard_audio = keyboard_audio.with_effects([afx.MultiplyVolume(0.3)])
                audio_clips.append(keyboard_audio)

            if bgm_path and os.path.exists(bgm_path):
                bgm_audio = AudioFileClip(bgm_path)
                if bgm_audio.duration > total_duration:
                    bgm_audio = bgm_audio.subclipped(0, total_duration)
                else:
                    loops = int(total_duration / bgm_audio.duration) + 1
                    bgm_audio = concatenate_audioclips([bgm_audio] * loops).subclipped(0, total_duration)
                bgm_audio = bgm_audio.with_effects([afx.MultiplyVolume(0.6)])
                audio_clips.append(bgm_audio)

            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                final_video = final_video.with_audio(final_audio)

        except Exception as e:
            print(f"⚠️ 音频处理失败: {e}")

        # 输出视频
        output_path = os.path.join(project_path, "final_video_no_cursor.mp4")
        print(f"💾 开始输出视频: {output_path}")

        final_video.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            threads=4
        )

        print(f"✅ 视频生成成功: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 视频生成失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def trans_video_clicktype_no_cursor(data: dict):
    """无光标版本的主函数"""
    try:
        print("🚀 开始处理无光标版本视频请求")

        project_id = str(uuid.uuid1())
        # base_project_path = "projects"
        user_data_dir = get_user_data_dir()
        base_project_path = os.path.join(user_data_dir, "projects")
        project_path = os.path.join(base_project_path, project_id)
        os.makedirs(project_path, exist_ok=True)

        def download_file(url, local_filename):
            import requests
            try:
                print(f"⬇️ 下载文件: {url}")
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    local_filename = os.path.join(project_path, local_filename)
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"✅ 下载完成: {local_filename}")
                return local_filename
            except Exception as e:
                print(f"❌ 下载失败: {e}")
                raise

        # 下载资源
        bgm_path = download_file(data['bgm_audio'], "bg_audio.mp3")
        background_images = []

        for i, image_url in enumerate(data['image_url']):
            try:
                img_path = download_file(image_url, f"img_{i}.png")
                background_images.append(img_path)
            except Exception as e:
                print(f"⚠️ 下载第{i}张背景图失败: {e}")

        if not background_images:
            raise ValueError("没有成功下载任何背景图片")

        sections = data['content']
        title = data['title']

        # 验证数据
        print(f"📝 标题: {title}")
        for i, section in enumerate(sections):
            print(
                f"   段落 {i + 1}: 标题='{section.get('p_title', '')}', 内容='{section.get('p_content', '')[:50]}...'")

        output_path = get_video_clicktype_simple_no_cursor(sections, title, background_images, bgm_path, project_path)
        return output_path

    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        raise


# 替换原函数
trans_video_clicktype = trans_video_clicktype_no_cursor
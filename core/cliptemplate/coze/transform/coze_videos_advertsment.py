# -*- coding: utf-8 -*-
# @Time    : 2025/5/22 14:53
# @Author  : 蔍鸣霸霸
# @FileName: coze_videos_advertsment.py
# @Software: PyCharm
# @Blog    ：只因你太美

import os
import platform
import sys
from moviepy import ImageClip, TextClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips, \
    concatenate_videoclips, afx, VideoFileClip, CompositeAudioClip, VideoClip, vfx
import requests
import random
import uuid
# 导入配置模块
from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url
from core.clipgenerate.tongyi_get_videotalk import get_videotalk


def get_script_directory():
    """
    🔥 获取脚本所在目录（适配exe打包）
    支持PyInstaller打包后的路径获取
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接运行的python脚本
        return os.path.dirname(os.path.abspath(__file__))


def find_font_file():
    """
    🔥 查找微软雅黑字体文件
    优先级：
    1. 脚本同级目录下的微软雅黑.ttf
    2. 脚本同级目录下的msyh.ttf
    3. 用户数据目录下的字体文件
    4. 系统字体目录
    """
    script_dir = get_script_directory()
    print(f"🔍 脚本目录: {script_dir}")

    # 可能的字体文件名
    font_names = ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"]

    # 1. 优先检查脚本同级目录
    for font_name in font_names:
        font_path = os.path.join(script_dir, font_name)
        if os.path.exists(font_path):
            print(f"✅ 找到同级目录字体: {font_path}")
            return font_path

    # 2. 检查用户数据目录
    try:
        user_data_dir = get_user_data_dir()
        fonts_dir = os.path.join(user_data_dir, "fonts")
        for font_name in font_names:
            font_path = os.path.join(fonts_dir, font_name)
            if os.path.exists(font_path):
                print(f"✅ 找到用户数据目录字体: {font_path}")
                return font_path
    except:
        pass

    # 3. 检查常见系统字体目录
    system_font_paths = []

    if platform.system() == "Windows":
        system_font_paths = [
            "C:/Windows/Fonts/",
            "C:/Windows/System32/Fonts/",
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
        ]
    elif platform.system() == "Darwin":  # macOS
        system_font_paths = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/")
        ]
    else:  # Linux
        system_font_paths = [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            os.path.expanduser("~/.fonts/"),
            os.path.expanduser("~/.local/share/fonts/")
        ]

    for sys_path in system_font_paths:
        if os.path.exists(sys_path):
            for font_name in font_names:
                font_path = os.path.join(sys_path, font_name)
                if os.path.exists(font_path):
                    print(f"✅ 找到系统字体: {font_path}")
                    return font_path

    print("⚠️ 未找到微软雅黑字体文件")
    return None


def get_system_font_name():
    """
    🔥 获取系统字体名称
    """
    system = platform.system()

    if system == "Windows":
        return [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",  # 黑体
            "SimSun",  # 宋体
            "KaiTi",  # 楷体
            "Arial Unicode MS",  # Arial Unicode
        ]
    elif system == "Darwin":  # macOS
        return [
            "PingFang SC",  # 苹方
            "Hiragino Sans GB",  # 冬青黑体
            "STHeiti Light",  # 华文黑体
            "Arial Unicode MS",  # Arial Unicode
        ]
    else:  # Linux
        return [
            "Noto Sans CJK SC",  # 思源黑体
            "WenQuanYi Micro Hei",  # 文泉驿微米黑
            "DejaVu Sans",  # DejaVu Sans
        ]


def create_font_path_fixed():
    """
    🔥 修复版字体路径获取函数
    优先级：字体文件 > 系统字体名称 > 默认字体
    """
    # 1. 优先尝试找到字体文件
    font_file = find_font_file()
    if font_file:
        return font_file

    # 2. 使用系统字体名称
    system_fonts = get_system_font_name()
    for font_name in system_fonts:
        print(f"🔍 尝试系统字体: {font_name}")
        return font_name

    # 3. 最后降级到None
    print("⚠️ 未找到合适字体，使用默认字体")
    return None


def get_video_files(folder_path):
    """从指定文件夹下读取所有视频文件"""
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    try:
        return [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
    except FileNotFoundError:
        print(f"错误：目录 {folder_path} 不存在")
        return []


def select_random_videos(video_files, num_to_select):
    """从中随机挑选若干个视频文件，增加安全检查"""
    if not video_files:
        raise ValueError("视频文件列表为空")

    # 确保选择数量不为负数且不超过可用文件数量
    actual_num = max(0, min(num_to_select, len(video_files)))

    if actual_num == 0:
        return []

    return random.sample(video_files, actual_num)


def download_file(url, filename, target_dir):
    """下载远程文件到指定目录"""
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, filename)

    try:
        print(f"⬇️ 开始下载: {url}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ 下载完成: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        raise


def create_text_clip_robust(text, duration, is_title=False):
    """
    🔥 鲁棒性增强的文字片段创建函数
    多级降级策略确保文字能正常显示
    """
    print(f"📝 创建文字片段: {text[:30]}{'...' if len(text) > 30 else ''}")

    # 基础参数
    font_size = 80 if is_title else 48
    color = 'black' if is_title else 'yellow'
    stroke_color = 'yellow' if is_title else 'black'
    stroke_width = 3 if is_title else 1

    # 策略1: 尝试使用字体文件或系统字体
    try:
        font_name = create_font_path_fixed()

        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
            'stroke_color': stroke_color,
            'stroke_width': stroke_width,
            'method': "caption",
            'size': (1280, None),
        }

        # 只有在有有效字体时才添加font参数
        if font_name:
            text_clip_params['font'] = font_name

        print(f"🎯 尝试策略1 - 字体: {font_name or '默认'}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)

        # 测试渲染（检查是否会出现字体问题）
        try:
            # 尝试获取第一帧来验证字体渲染
            test_frame = text_clip.get_frame(0)
            print("✅ 策略1成功 - 字体渲染正常")
            return text_clip
        except Exception as e:
            print(f"⚠️ 策略1字体渲染测试失败: {e}")
            try:
                text_clip.close()
            except:
                pass
            raise e

    except Exception as e:
        print(f"❌ 策略1失败: {e}")

    # 策略2: 使用简化参数（去掉描边）
    try:
        font_name = create_font_path_fixed()

        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
            'method': "caption",
            'size': (1280, None),
        }

        if font_name:
            text_clip_params['font'] = font_name

        print(f"🎯 尝试策略2 - 简化参数，字体: {font_name or '默认'}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略2成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略2失败: {e}")

    # 策略3: 使用最基本参数（无字体指定）
    try:
        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
        }

        print("🎯 尝试策略3 - 最基本参数")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略3成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略3失败: {e}")

    # 策略4: 终极降级 - 使用纯英文字体
    try:
        # 将中文字符替换为拼音或英文描述（这是最后的降级方案）
        fallback_text = translate_to_safe_text(text)

        text_clip_params = {
            'text': fallback_text,
            'font_size': font_size,
            'color': color,
            'font': 'Arial',  # 使用最安全的英文字体
        }

        print(f"🎯 尝试策略4 - 降级文本: {fallback_text}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略4成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略4失败: {e}")

        # 最终降级：创建空白文本
        try:
            text_clip = TextClip(
                text="Text Display Error",
                font_size=font_size,
                color=color,
            ).with_duration(duration)
            print("⚠️ 使用错误提示文本")
            return text_clip
        except:
            # 如果连这个都失败，返回None
            print("❌ 完全无法创建文本片段")
            return None


def translate_to_safe_text(text):
    """
    🔄 将中文文本转换为安全的英文文本（降级方案）
    """
    char_map = {
        '企业': 'Enterprise',
        '财税': 'Finance & Tax',
        '服务': 'Service',
        '公司': 'Company',
        '专业': 'Professional',
        '团队': 'Team',
        '管理': 'Management',
        '发展': 'Development',
        '创新': 'Innovation',
        '优质': 'Quality',
        '优帮': 'YouBang',
        '常熟': 'Changshu',
        '园区': 'Park',
        '运营': 'Operation',
        '阳山': 'Yangshan',
        '数谷': 'Digital Valley',
    }

    # 简单替换
    safe_text = text
    for chinese, english in char_map.items():
        safe_text = safe_text.replace(chinese, english)

    # 如果仍有中文字符，截断到安全长度
    if len(safe_text) > 50:
        safe_text = safe_text[:47] + "..."

    return safe_text


def check_font_environment():
    """
    🔧 检查字体环境
    """
    print("🔍 检查字体环境...")
    script_dir = get_script_directory()
    print(f"📂 脚本目录: {script_dir}")

    # 检查同级目录下的字体文件
    font_files = []
    font_extensions = ['.ttf', '.ttc', '.otf']

    for file in os.listdir(script_dir):
        if any(file.lower().endswith(ext) for ext in font_extensions):
            font_files.append(file)

    if font_files:
        print(f"✅ 找到同级目录字体文件: {font_files}")
    else:
        print("⚠️ 同级目录未找到字体文件")
        print("💡 建议将微软雅黑.ttf放置到以下目录:")
        print(f"   {script_dir}")

    # 检查字体文件
    font_file = find_font_file()
    if font_file:
        print(f"✅ 将使用字体文件: {font_file}")
    else:
        print("⚠️ 未找到字体文件，将使用系统字体")
        system_fonts = get_system_font_name()
        print(f"📋 系统字体候选: {system_fonts}")

    return font_file is not None


def trans_videos_advertisement(data: dict) -> str:
    """🔥 生成视频广告，修复版本"""
    # 🔥 在开始前检查字体环境
    print("🔍 初始化字体环境...")
    check_font_environment()

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

    print(f"📂 项目目录: {project_path}")
    print(f"📂 主持人素材目录: {moderator_folder_path}")
    print(f"📂 企业素材目录: {enterprise_folder_path}")

    # 验证数据完整性
    if not data.get("output") or len(data["output"]) == 0:
        raise ValueError("output数据为空，无法生成视频")

    print(f"📊 输出段落数量: {len(data['output'])}")
    print(f"📊 音频URL数量: {len(data.get('audio_urls', []))}")

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
    print(f"📊 企业素材文件数量: {len(enterprise_files)}")

    # 计算需要的企业视频数量（避免负数）
    total_segments = len(data["output"])
    print(f"📊 总段落数: {total_segments}")

    if total_segments <= 2:
        needed_enterprise_videos = 0
        print("📝 段落数量较少，不使用企业素材视频")
    else:
        needed_enterprise_videos = total_segments - 2
        print(f"📊 需要企业视频数量: {needed_enterprise_videos}")

    # 选择企业视频文件
    if needed_enterprise_videos > 0:
        if not enterprise_files:
            print("⚠️ 警告：企业素材目录为空，中间段落将使用背景图片")
            selected_enterprise_files = []
        else:
            selected_enterprise_files = select_random_videos(enterprise_files, needed_enterprise_videos)
            print(f"✅ 已选择企业视频: {len(selected_enterprise_files)} 个")
    else:
        selected_enterprise_files = []

    # 🔥 构建视频片段 - 使用修复的文本创建函数
    video_clips = []

    for i, (text, audio_clip) in enumerate(zip(data["output"], audio_clips)):
        print(f"\n🎬 创建第 {i + 1} 个片段...")

        bg = ImageClip(bg_image_path).with_duration(audio_clip.duration)

        if i == 0:
            # 第一个片段 - 开场
            video_clip = start_clip

            # 🔥 修复：正确获取公司名称字段
            company_name = data.get("company_name") or data.get("conpany_name", "公司名称")
            title_clip = create_text_clip_robust(company_name, audio_clip.duration, is_title=True)
            text_clip = create_text_clip_robust(text, audio_clip.duration)

            # 只添加成功创建的文本片段
            overlay_clips = [bg, video_clip.with_position(("center", "center"), relative=True)]

            if title_clip:
                overlay_clips.append(title_clip.with_position(("center", 0.2), relative=True))

            if text_clip:
                overlay_clips.append(text_clip.with_position(("center", 0.8), relative=True))

            composite = CompositeVideoClip(overlay_clips).with_audio(audio_clip)

        elif i == len(data["output"]) - 1:
            # 最后一个片段 - 结尾
            video_clip = end_clip
            text_clip = create_text_clip_robust(text, audio_clip.duration)

            overlay_clips = [bg, video_clip.with_position(("center", "center"), relative=True)]

            if text_clip:
                overlay_clips.append(text_clip.with_position(("center", 0.8), relative=True))

            composite = CompositeVideoClip(overlay_clips).with_audio(audio_clip)

        else:
            # 中间片段
            enterprise_video_index = i - 1

            if enterprise_video_index < len(selected_enterprise_files):
                # 有企业视频可用
                video_path = os.path.join(enterprise_folder_path, selected_enterprise_files[enterprise_video_index])
                video_clip = VideoFileClip(video_path).resized((1280, 720))

                # 根据音频长度裁剪视频
                target_duration = audio_clip.duration
                if video_clip.duration > target_duration:
                    start_time = random.uniform(0, max(0, video_clip.duration - target_duration - 0.1))
                    video_clip = video_clip.subclipped(start_time, start_time + target_duration)
                else:
                    try:
                        loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                        video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                        video_clip = video_clip.subclipped(0, target_duration)
                    except:
                        # 如果Loop不可用，手动循环
                        print("⚠️ Loop效果不可用，使用手动循环")
                        clips_needed = int(target_duration / video_clip.duration) + 1
                        looped_clips = [video_clip] * clips_needed
                        video_clip = concatenate_videoclips(looped_clips).subclipped(0, target_duration)

                text_clip = create_text_clip_robust(text, audio_clip.duration)

                overlay_clips = [bg, video_clip.with_position(("center", "center"), relative=True)]

                if text_clip:
                    overlay_clips.append(text_clip.with_position(("center", 0.8), relative=True))

                composite = CompositeVideoClip(overlay_clips).with_audio(audio_clip)
            else:
                # 没有足够的企业视频，使用背景图片
                print(f"⚠️ 中间片段 {i} 缺少企业视频，使用背景图片")
                text_clip = create_text_clip_robust(text, audio_clip.duration)

                overlay_clips = [bg]

                if text_clip:
                    overlay_clips.append(text_clip.with_position(("center", "center"), relative=True))

                composite = CompositeVideoClip(overlay_clips).with_audio(audio_clip)

        video_clips.append(composite)
        print(f"✅ 第 {i + 1} 个片段创建完成")

    # 拼接所有片段
    print("\n🔗 开始拼接所有视频片段...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 🔥 调整背景音乐长度 - 修复AudioLoop兼容性
    print("🎵 处理背景音乐...")
    try:
        if bgm_clip.duration < final_video.duration:
            # 尝试使用AudioLoop
            try:
                bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
            except:
                # 手动循环
                print("⚠️ AudioLoop不可用，使用手动循环")
                loops_needed = int(final_video.duration / bgm_clip.duration) + 1
                bgm_clips = [bgm_clip] * loops_needed
                bgm_clip = concatenate_audioclips(bgm_clips).subclipped(0, final_video.duration)
        else:
            bgm_clip = bgm_clip.subclipped(0, final_video.duration)

        # 🔥 混合音频 - 修复MultiplyVolume兼容性
        try:
            origin_max_volume = final_video.audio.max_volume()
            bgm_max_volume = bgm_clip.max_volume()

            if bgm_max_volume == 0:
                volume_rate = 1
            else:
                volume_rate = origin_max_volume / (bgm_max_volume * 2)

            try:
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.with_effects([afx.MultiplyVolume(volume_rate)])
                ])
            except:
                # 如果MultiplyVolume不可用，使用volumex
                print("⚠️ MultiplyVolume不可用，使用volumex")
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.volumex(volume_rate)
                ])

            final_video = final_video.with_audio(final_audio)
        except Exception as e:
            print(f"❌ 音频混合失败: {e}")
            print("⚠️ 使用原始音频...")
    except Exception as e:
        print(f"❌ 背景音乐处理失败: {e}")

    # 输出视频
    output_path = os.path.join(project_path, "final_video.mp4")

    try:
        print(f"🎬 开始生成视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4
        )
        print(f"✅ 视频已生成: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ 视频生成失败: {e}")
        raise
    finally:
        # 🔥 清理资源
        try:
            for clip in video_clips:
                clip.close()
            for audio_clip in audio_clips:
                audio_clip.close()
            bgm_clip.close()
            final_video.close()
            start_clip.close()
            end_clip.close()
        except:
            pass


def copy_font_to_script_dir():
    """
    🔧 将字体文件复制到脚本目录（可选的辅助函数）
    """
    script_dir = get_script_directory()
    target_font_path = os.path.join(script_dir, "微软雅黑.ttf")

    if os.path.exists(target_font_path):
        print(f"✅ 字体文件已存在: {target_font_path}")
        return target_font_path

    # 尝试从用户数据目录复制
    try:
        user_data_dir = get_user_data_dir()
        source_font_path = os.path.join(user_data_dir, "fonts", "微软雅黑.ttf")

        if os.path.exists(source_font_path):
            import shutil
            shutil.copy2(source_font_path, target_font_path)
            print(f"✅ 字体文件已复制到: {target_font_path}")
            return target_font_path
    except Exception as e:
        print(f"⚠️ 字体文件复制失败: {e}")

    print(f"💡 请手动将微软雅黑.ttf复制到: {script_dir}")
    return None


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
        "company_name": "常熟优帮财税",
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
        result_path = trans_videos_advertisement(json_data)
        print(f"🎉 视频生成成功: {result_path}")
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback

        print(f"错误详情: {traceback.format_exc()}")
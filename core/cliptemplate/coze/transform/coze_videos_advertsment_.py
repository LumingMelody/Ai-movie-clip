import os
import random
import uuid
import warnings

import requests
import platform
from typing import List, Union, Optional

from moviepy import CompositeAudioClip
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips,
    afx, vfx
)
from moviepy.tools import close_all_clips

from config import get_user_data_dir, create_font_path
from core.clipgenerate.tongyi_get_online_url import get_online_url
from core.clipgenerate.tongyi_get_videotalk import get_videotalk
from core.cliptemplate.smart_clip_with_vocals import smart_clips

# 支持的视频文件扩展名
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

# 忽略 MoviePy 的资源清理警告
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")



def download_file(url: str, filename: str, save_dir: str) -> str:
    """下载文件到指定目录"""
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        print(f"文件已存在: {save_path}")
        return save_path

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"下载完成: {save_path}")
        return save_path
    except Exception as e:
        print(f"下载失败: {url}, 错误: {e}")
        raise


def select_random_videos(files: List[str], count: int) -> List[str]:
    """随机选择指定数量的视频文件"""
    if not files:
        return []
    if len(files) <= count:
        return files
    return random.sample(files, count)


def resolve_materials(source: Union[str, List[str]], valid_extensions: tuple) -> List[str]:
    """解析素材路径（支持文件/文件夹）"""
    if not source:
        return []

    if isinstance(source, str):
        source = [source]

    resolved_files = []
    for item in source:
        item = os.path.abspath(item)

        if os.path.isfile(item) and item.lower().endswith(valid_extensions):
            resolved_files.append(item)

        elif os.path.isdir(item):
            resolved_files.extend([
                os.path.join(item, f) for f in os.listdir(item)
                if os.path.isfile(os.path.join(item, f)) and f.lower().endswith(valid_extensions)
            ])

    return resolved_files


def create_text_clip(text: str, duration: float, is_title: bool = False) -> TextClip:
    font_name = create_font_path()
    return TextClip(
        text=text,  # 传递文本内容
        font=font_name,
        font_size=80 if is_title else 48,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(1280, None)
    ).with_duration(duration)


def trans_videos_advertisement(
        data: dict,
        add_digital_host: bool = False,
        use_temp_materials: bool = False,
        clip_mode: bool = False,
        upload_digital_host: bool = False,  # True=使用materials/upload目录，False=使用materials/digital_host
        moderator_source: Optional[Union[str, List[str]]] = None,  # 可选：指定其他上传目录路径
        enterprise_source: Optional[Union[str, List[str]]] = None,  # 企业素材路径
) -> str:
    """生成视频广告"""
    # 确保中文显示正常
    os.environ["IMAGEIO_FT_LIB"] = "freeimage"

    user_data_dir = get_user_data_dir()
    project_id = str(uuid.uuid1())
    project_path = os.path.join(user_data_dir, "projects", project_id)
    os.makedirs(project_path, exist_ok=True)

    print(f"项目路径: {project_path}")

    # ---------------------- 素材目录设置 ----------------------
    materials_root = "materials"
    base_materials_dir = os.path.join(user_data_dir, materials_root)

    # 系统默认素材目录
    system_digital_host_folder = os.path.join(base_materials_dir, "moderator")
    system_enterprise_folder = os.path.join(base_materials_dir, "enterprise")

    # 上传素材目录（固定为materials/upload）
    upload_folder = os.path.join(base_materials_dir, "upload")

    # 创建必要的目录
    os.makedirs(system_digital_host_folder, exist_ok=True)
    os.makedirs(system_enterprise_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)

    print(f"素材模式: {'临时' if use_temp_materials else '正式'}")
    print(f"上传素材目录: {upload_folder}")

    # ---------------------- 下载基础资源 ----------------------
    try:
        bg_image_path = download_file(data.get("data", ""), "background.png", project_path)
        bg_image = ImageClip(bg_image_path).resized((1280, 720))

        audio_clips = []
        for i, url in enumerate(data.get("audio_urls", [])):
            audio_path = download_file(url, f"audio_{i}.mp3", project_path)
            audio_clips.append(AudioFileClip(audio_path))

        bgm_path = download_file(data.get("bgm", ""), "bgm.mp3", project_path)
        bgm_clip = AudioFileClip(bgm_path) if bgm_path else None

    except Exception as e:
        print(f"基础资源下载失败: {e}")
        raise

    # ---------------------- 处理数字人素材 ----------------------
    if upload_digital_host:
        # 使用materials/upload目录的素材
        print(f"使用上传目录的数字人素材: {upload_folder}")
        digital_host_files = resolve_materials(
            source=moderator_source or upload_folder,  # 优先使用用户指定路径，否则使用upload_folder
            valid_extensions=VIDEO_EXTENSIONS
        )
    else:
        # 使用系统默认目录的素材
        print(f"使用系统目录的数字人素材: {system_digital_host_folder}")
        digital_host_files = resolve_materials(
            source=system_digital_host_folder,
            valid_extensions=VIDEO_EXTENSIONS
        )

    if add_digital_host and not digital_host_files:
        raise FileNotFoundError(
            f"数字人素材为空: {moderator_source or upload_folder if upload_digital_host else system_digital_host_folder}")

    # ---------------------- 处理企业素材 ----------------------
    # ---------------------- 处理企业素材 ----------------------
    if enterprise_source:
        # 使用指定路径的素材
        print(f"📂 使用指定路径的企业素材: {enterprise_source}")

        # 🔥 新增：处理URL下载逻辑
        processed_enterprise_source = []

        for es in enterprise_source:
            if es.startswith(("http://", "https://")):
                # URL: 需要下载到本地
                try:
                    # 从URL中提取或生成文件名
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(es)
                    filename = os.path.basename(parsed_url.path)

                    # 如果没有合适的文件名，生成一个
                    if not filename or '.' not in filename:
                        if '/files/' in es:
                            hash_part = es.split('/files/')[1].split('?')[0]
                            filename = f"{hash_part}.mp4"
                        else:
                            filename = f"enterprise_{len(processed_enterprise_source)}.mp4"

                    # 确保有视频扩展名
                    if not filename.lower().endswith(VIDEO_EXTENSIONS):
                        if '.' not in filename:
                            filename += '.mp4'

                    print(f"📥 下载企业素材: {filename}")
                    local_path = download_file(es, filename, project_path)
                    processed_enterprise_source.append(local_path)
                    print(f"✅ 企业素材下载成功: {filename}")

                except Exception as e:
                    print(f"❌ 企业素材下载失败: {es}, 错误: {e}")
                    continue
            else:
                # 本地路径：检查是否存在
                if not os.path.isabs(es):
                    # 相对路径，添加到用户数据目录
                    full_path = os.path.join(user_data_dir, es)
                else:
                    # 绝对路径
                    full_path = es

                if os.path.exists(full_path):
                    processed_enterprise_source.append(full_path)
                    print(f"✅ 找到本地企业素材: {full_path}")
                else:
                    print(f"❌ 本地企业素材不存在: {full_path}")

        # 更新enterprise_source为处理后的本地路径列表
        enterprise_source = processed_enterprise_source
        print(f"📋 处理后的企业素材路径: {enterprise_source}")

        # 解析素材文件
        enterprise_files = resolve_materials(
            source=enterprise_source,
            valid_extensions=VIDEO_EXTENSIONS
        )

        # 检查是否有可用的企业素材
        if not enterprise_files:
            print(f"⚠️ 指定的企业素材处理后为空，回退到系统默认素材")
            enterprise_source = None  # 重置，让下面的逻辑处理默认素材

    # 如果没有指定enterprise_source或处理失败后回退
    if not enterprise_source:
        # 使用系统目录的企业素材
        print(f"📂 使用系统目录的企业素材: {system_enterprise_folder}")
        enterprise_files = resolve_materials(
            source=system_enterprise_folder,
            valid_extensions=VIDEO_EXTENSIONS
        )

    # 最终检查
    if not enterprise_files:
        raise FileNotFoundError(f"企业素材为空: {enterprise_source or system_enterprise_folder}")

    print(f"✅ 找到有效企业素材文件: {len(enterprise_files)} 个")

    # ---------------------- 数字人视频生成 ----------------------
    start_clip = end_clip = None

    if add_digital_host:
        try:
            selected_host = random.choice(digital_host_files)
            host_url, _ = get_online_url(selected_host)

            start_url = get_videotalk(host_url, data["audio_urls"][0])
            end_url = get_videotalk(host_url, data["audio_urls"][-1])

            start_clip = VideoFileClip(download_file(start_url, "start.mp4", project_path))
            end_clip = VideoFileClip(download_file(end_url, "end.mp4", project_path))

        except Exception as e:
            print(f"数字人视频生成失败: {e}")
            raise

    # ---------------------- 剪辑逻辑 ----------------------
    num_enterprise_clips = len(data["output"]) - (2 if add_digital_host else 0)

    if num_enterprise_clips < 0:
        raise ValueError("音频数量与输出文本数量不匹配")

    enterprise_clips = []

    if not clip_mode:  # 智能剪辑模式
        try:
            enterprise_clips = smart_clips(
                enterprise_files=enterprise_files,
                audio_clips=audio_clips[1:-1] if add_digital_host else audio_clips,
                project_dir=project_path,
                num_clips=num_enterprise_clips
            )
        except Exception as e:
            print(f"智能剪辑失败: {e}")
            print("回退到随机剪辑模式")
            clip_mode = True  # 智能剪辑失败时回退到随机剪辑

    if clip_mode:  # 随机剪辑模式
        selected_files = select_random_videos(enterprise_files, num_enterprise_clips)

        for idx, audio_clip in enumerate(audio_clips):
            # 跳过数字人对应的首尾音频
            if add_digital_host and (idx == 0 or idx == len(audio_clips) - 1):
                continue

            # 获取当前企业素材文件
            video_idx = idx - (1 if add_digital_host else 0)
            if video_idx >= len(selected_files):
                video_idx = video_idx % len(selected_files)

            video_path = selected_files[video_idx]
            video_clip = VideoFileClip(video_path).resized((1280, 720))

            # 按音频长度裁剪视频
            target_duration = audio_clip.duration

            if video_clip.duration > target_duration:
                # 随机截取片段
                start_time = random.uniform(0, video_clip.duration - target_duration - 0.1)
                video_clip = video_clip.subclipped(start_time, start_time + target_duration)
            else:
                # 循环播放直到匹配音频长度
                loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                video_clip = video_clip.subclipped(0, target_duration)

            # 绑定音频
            video_clip = video_clip.with_audio(audio_clip)
            enterprise_clips.append(video_clip)

    # ---------------------- 视频组装 ----------------------
    video_clips = []

    for idx, (text, audio_clip) in enumerate(zip(data["output"], audio_clips)):
        current_bg = bg_image.with_duration(audio_clip.duration)
        text_clip = create_text_clip(text, audio_clip.duration)

        if add_digital_host:
            if idx == 0:  # 开场片段
                composite = CompositeVideoClip([
                    current_bg,
                    start_clip.with_position(("center", "center")),
                    create_text_clip(data["conpany_name"], audio_clip.duration, is_title=True).with_position(
                        ("center", 0.2), relative=True),
                    text_clip.with_position(("center", 0.8), relative=True)
                ]).with_audio(audio_clip)

            elif idx == len(data["output"]) - 1:  # 结尾片段
                composite = CompositeVideoClip([
                    current_bg,
                    end_clip.with_position(("center", "center")),
                    text_clip.with_position(("center", 0.8), relative=True)
                ]).with_audio(audio_clip)

            else:  # 中间企业片段
                enterprise_idx = idx - 1
                composite = CompositeVideoClip([
                    current_bg,
                    enterprise_clips[enterprise_idx].with_position(("center", "center")),
                    text_clip.with_position(("center", 0.8), relative=True)
                ]).with_audio(audio_clip)

        else:
            if idx == 0:  # 无数字人时的标题片段
                composite = CompositeVideoClip([
                    current_bg,
                    create_text_clip(data["conpany_name"], audio_clip.duration, is_title=True).with_position(
                        ("center", 0.5), relative=True),
                    text_clip.with_position(("center", 0.8), relative=True)
                ]).with_audio(audio_clip)

            else:  # 普通企业片段
                composite = CompositeVideoClip([
                    current_bg,
                    enterprise_clips[idx - 1].with_position(("center", "center")),
                    text_clip.with_position(("center", 0.8), relative=True)
                ]).with_audio(audio_clip)

        video_clips.append(composite)

    # ---------------------- 最终视频处理 ----------------------
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 处理背景音乐
    if bgm_clip:
        # 调整背景音乐长度匹配视频
        if bgm_clip.duration < final_video.duration:
            bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
        else:
            bgm_clip = bgm_clip.subclipped(0, final_video.duration)

        # 混合音频（背景音量设为30%）
        try:
            final_audio = CompositeAudioClip([
                final_video.audio,
                bgm_clip.with_effects([afx.MultiplyVolume(0.3)])
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
            threads=4,
        )
        print(f"✅ 视频生成完成: {output_path}")
        return output_path
    except Exception as e:
        print(f"视频生成失败: {e}")
        raise
    finally:
        # 手动关闭所有剪辑资源
        close_all_clips()

if __name__ == '__main__':

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

    # try:
    output_path = trans_videos_advertisement(
        data=json_data,
        add_digital_host=True,  # 添加数字人
        use_temp_materials=False,  # 使用正式素材目录 (materials)
        clip_mode=True,  # 使用随机剪辑模式
        upload_digital_host=False,  # ✅ 使用系统默认目录（而非上传目录）
        moderator_source=None,  # 不指定其他路径，使用默认系统目录
        enterprise_source=None  # 使用默认企业素材目录
    )
    print(f"视频生成成功，保存路径: {output_path}")
    # except Exception as e:
    #     print(f"视频生成失败: {e}")
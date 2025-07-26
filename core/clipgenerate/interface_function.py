# -*- coding: utf-8 -*-
# @Time    : 2025/7/14 09:46
# @Author  : 蔍鸣霸霸
# @FileName: interface_function.py
# @Software: PyCharm
# @Blog    ：只因你太美
import os
# 解决 OpenMP 库冲突问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import uuid
from typing import Optional
import oss2

import config
from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator
from main import get_api_key_from_file

UPLOAD_DIR = os.path.join(config.get_user_data_dir(), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ============ 配置信息 ============
# 从配置文件导入，避免硬编码密钥
try:
    from config.oss_config import (
        OSS_ACCESS_KEY_ID,
        OSS_ACCESS_KEY_SECRET,
        OSS_ENDPOINT,
        OSS_BUCKET_NAME
    )
except ImportError:
    # 兼容旧的配置方式
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID', 'YOUR_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET', 'YOUR_ACCESS_KEY_SECRET')
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME', 'lan8-e-business')


# 初始化OSS
auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

def upload_to_oss(local_path, oss_path):
    """OSS上传函数"""
    try:
        bucket.put_object_from_file(oss_path, local_path)
        print(f"✅ 上传成功 {local_path} -> {oss_path}")
        return True
    except Exception as e:
        print(f"❌ 上传失败 {local_path}: {str(e)}")
        return False

def get_file_info(file_path: str) -> Optional[dict]:
    """获取文件信息"""
    try:
        if not os.path.exists(file_path):
            return None

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # 根据文件扩展名确定资源类型
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        audio_exts = ['.mp3', '.wav', '.aac', '.m4a']

        if file_ext in video_exts:
            resource_type = "1"  # 视频
        elif file_ext in image_exts:
            resource_type = "2"  # 图片
        elif file_ext in audio_exts:
            resource_type = "3"  # 音频
        else:
            resource_type = "4"  # 其他

        return {
            'name': file_name,
            'size': file_size,
            'file_type': file_ext[1:],  # 去掉点号
            'resource_type': resource_type
        }

    except Exception as e:
        print(f"❌ 获取文件信息失败: {file_path}, 错误: {str(e)}")
        return None

def check_dependencies():
    """检查依赖库"""
    try:
        import moviepy
        print(f"MoviePy 版本: {moviepy.__version__}")

        # 检查 ffmpeg
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg 可用")
        else:
            print("❌ FFmpeg 不可用")

    except ImportError as e:
        print(f"❌ 依赖库缺失: {e}")
    except Exception as e:
        print(f"❌ 依赖检查失败: {e}")

def download_file_from_url(url, timeout=300):
    """
    🔥 从URL下载文件到临时位置

    Args:
        url: 文件URL
        timeout: 超时时间（秒）

    Returns:
        str: 临时文件路径
    """
    import requests
    import tempfile
    import os
    from urllib.parse import urlparse

    print(f"⬇️ 开始下载文件: {url}")

    try:
        # 创建临时文件
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = "downloaded_video.mp4"  # 默认文件名

        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = '.mp4'

        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix=ext, prefix='smart_clip_')
        os.close(temp_fd)  # 关闭文件描述符

        # 下载文件
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 显示进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"\r📥 下载进度: {progress:.1f}%", end='', flush=True)

        print(f"\n✅ 文件下载完成: {temp_path}")
        print(f"📊 文件大小: {downloaded_size / (1024 * 1024):.2f}MB")

        return temp_path

    except requests.exceptions.RequestException as e:
        print(f"❌ 下载失败: {e}")
        raise
    except Exception as e:
        print(f"❌ 下载处理失败: {e}")
        raise


def get_smart_clip_video(input_source, is_directory=True, company_name="测试公司",
                               text_list=None, audio_durations=None, clip_mode="random",
                               target_resolution=(1920, 1080)):
    """
    🔥 修复后的智能剪辑函数 - 解决VideoFileClip关闭问题
    """
    print(f"🎬 智能剪辑请求:")
    print(f"   输入源: {input_source}")
    print(f"   剪辑模式: {clip_mode}")
    print(f"   音频时长: {audio_durations}")
    print(f"   是否目录: {is_directory}")

    temp_files_to_cleanup = []

    try:
        # 处理输入源
        # 处理输入源（兼容列表和单个URL）
        processed_input_source = input_source

        if isinstance(input_source, list):
            # 处理列表中的URL或文件路径
            local_files = []
            for item in input_source:
                if item.startswith(('http://', 'https://')):
                    try:
                        temp_path = download_file_from_url(item)
                        temp_files_to_cleanup.append(temp_path)
                        local_files.append(temp_path)
                    except Exception as e:
                        raise ValueError(f"URL下载失败: {item}, 错误: {e}")
                else:
                    local_files.append(item)
            processed_input_source = local_files
            is_directory = False  # 强制设为False，因为现在是文件列表

        elif isinstance(input_source, str) and input_source.startswith(('http://', 'https://')):
            # 处理单个URL
            temp_path = download_file_from_url(input_source)
            temp_files_to_cleanup.append(temp_path)
            processed_input_source = temp_path
            is_directory = False

        # 生成输出路径
        output_dir = os.path.join(config.get_user_data_dir(), "projects", str(uuid.uuid4()))
        os.makedirs(output_dir, exist_ok=True)

        if clip_mode == "smart":
            print("🧠 使用智能剪辑模式")

            # 设置默认音频时长
            if not audio_durations:
                print("⚠️ 未提供音频时长，使用默认值")
                audio_durations = [3.0, 4.0, 2.5, 3.5, 5.0]

            print(f"🎵 目标片段时长: {audio_durations}")

            output_path = os.path.join(output_dir, "smart_clip_video.mp4")

            def smart_clips_fixed_v2(input_source, output_path, audio_durations, target_resolution, is_directory=True):
                """🔥 修复后的智能剪辑函数 V2 - 解决资源管理问题"""
                from moviepy import VideoFileClip, concatenate_videoclips, vfx
                import random

                def resolve_materials_inline(source, valid_extensions):
                    if not source:
                        return []

                    resolved_files = []
                    if isinstance(source, list):
                        for file_path in source:
                            if os.path.isfile(file_path) and file_path.lower().endswith(valid_extensions):
                                resolved_files.append(file_path)
                    elif os.path.isfile(source) and source.lower().endswith(valid_extensions):
                        resolved_files.append(source)
                    elif os.path.isdir(source):
                        for f in os.listdir(source):
                            file_path = os.path.join(source, f)
                            if os.path.isfile(file_path) and f.lower().endswith(valid_extensions):
                                resolved_files.append(file_path)
                    return resolved_files

                VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

                # 获取视频文件列表
                if isinstance(input_source, list):
                    video_paths = input_source
                elif is_directory:
                    video_paths = resolve_materials_inline(input_source, VIDEO_EXTENSIONS)
                else:
                    video_paths = [input_source]

                if not video_paths:
                    raise ValueError("没有找到有效的视频文件!")

                print(f"📁 找到 {len(video_paths)} 个视频文件")

                # 按照audio_durations创建片段
                final_clips = []
                total_target_duration = sum(audio_durations)

                print(f"🎯 目标总时长: {total_target_duration:.1f}秒")
                print(f"🔪 需要创建 {len(audio_durations)} 个片段")

                # 🔥 关键修复：不要在循环中提前关闭视频
                video_clips_cache = {}  # 缓存已加载的视频

                try:
                    for i, target_duration in enumerate(audio_durations):
                        print(f"\n🎬 处理片段 {i + 1}/{len(audio_durations)}, 目标时长: {target_duration}秒")

                        # 智能选择视频文件
                        if len(video_paths) == 1:
                            video_path = video_paths[0]
                        else:
                            video_index = i % len(video_paths)
                            video_path = video_paths[video_index]

                        # 🔥 使用缓存避免重复加载和提前关闭
                        if video_path not in video_clips_cache:
                            video_clips_cache[video_path] = VideoFileClip(video_path)
                            print(
                                f"📹 加载视频: {os.path.basename(video_path)}, 时长: {video_clips_cache[video_path].duration:.1f}秒")

                        source_clip = video_clips_cache[video_path]

                        # 🔥 创建子剪辑，但不关闭源视频
                        if source_clip.duration <= target_duration:
                            # 视频太短，循环播放
                            print(f"⚠️ 视频较短，进行循环播放")
                            loop_count = int(target_duration / source_clip.duration) + 1
                            clip = source_clip.with_effects([vfx.Loop(duration=loop_count * source_clip.duration)])
                            clip = clip.subclipped(0, target_duration)
                        else:
                            # 智能选择起始点
                            available_duration = source_clip.duration - target_duration
                            if available_duration > 0:
                                if len(video_paths) == 1:
                                    # 单视频：均匀分布起始点
                                    start_ratio = i / len(audio_durations) if len(audio_durations) > 1 else 0
                                    start_time = start_ratio * available_duration

                                    # 添加随机偏移
                                    max_offset = min(5.0, available_duration / len(audio_durations) * 0.5)
                                    random_offset = random.uniform(-max_offset, max_offset)
                                    start_time = max(0, min(available_duration, start_time + random_offset))
                                else:
                                    # 多视频：随机选择起始点
                                    start_time = random.uniform(0, available_duration)

                                print(f"✂️ 截取片段: {start_time:.1f}s - {start_time + target_duration:.1f}s")
                                clip = source_clip.subclipped(start_time, start_time + target_duration)
                            else:
                                clip = source_clip.subclipped(0, target_duration)

                        # 调整分辨率
                        if clip.size[0] > clip.size[1]:
                            # 横屏视频
                            clip = clip.resized(target_resolution)
                        else:
                            # 竖屏视频
                            vertical_resolution = (target_resolution[1], target_resolution[0])
                            clip = clip.resized(vertical_resolution)

                        final_clips.append(clip)
                        print(f"✅ 片段 {i + 1} 创建完成: {clip.duration:.1f}秒")

                    if not final_clips:
                        raise ValueError("没有成功创建任何视频片段")

                    # 拼接所有片段
                    print(f"\n🔗 拼接 {len(final_clips)} 个片段...")
                    final_video = concatenate_videoclips(final_clips, method="compose")

                    actual_duration = final_video.duration
                    print(f"📊 拼接后总时长: {actual_duration:.1f}秒 (目标: {total_target_duration:.1f}秒)")

                    # 生成最终视频
                    print(f"🎬 开始生成最终视频: {output_path}")
                    final_video.write_videofile(
                        output_path,
                        codec="libx264",
                        fps=24,
                        audio_codec="aac",
                        threads=1,  # 减少线程数避免死锁
                        verbose=False,  # 禁用详细输出
                        logger=None,  # 禁用进度条
                        temp_audiofile='temp-audio.m4a',  # 指定临时音频文件
                        remove_temp=True  # 自动清理临时文件
                    )

                    # 文件信息
                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"✅ 智能剪辑完成!")
                    print(f"📄 文件路径: {output_path}")
                    print(f"📊 文件大小: {file_size:.1f}MB")
                    print(f"⏱️  最终时长: {actual_duration:.1f}秒")
                    print(f"🎯 时长匹配度: {(actual_duration / total_target_duration) * 100:.1f}%")

                except Exception as e:
                    print(f"❌ 智能剪辑过程中出错: {e}")
                    raise e

                finally:
                    # 🔥 关键修复：在最后统一清理资源
                    print("🧹 开始清理视频资源...")

                    # 先清理子剪辑
                    for clip in final_clips:
                        try:
                            clip.close()
                        except:
                            pass

                    # 再清理最终视频
                    try:
                        final_video.close()
                    except:
                        pass

                    # 最后清理缓存的源视频
                    for video_path, video_clip in video_clips_cache.items():
                        try:
                            video_clip.close()
                            print(f"🗑️ 已关闭: {os.path.basename(video_path)}")
                        except Exception as e:
                            print(f"⚠️ 关闭视频失败: {e}")

                    print("✅ 资源清理完成")

            # 调用修复后的智能剪辑函数
            smart_clips_fixed_v2(
                input_source=processed_input_source,
                output_path=output_path,
                audio_durations=audio_durations,
                target_resolution=target_resolution,
                is_directory=is_directory
            )

            # 返回相对路径
            relative_path = os.path.relpath(output_path, config.get_user_data_dir())
            return relative_path.replace('\\', '/')

        elif clip_mode == "random":
            # 随机剪辑模式
            print("🎲 使用随机剪辑模式")

            def create_test_audio_clips_inline(durations):
                """创建测试用的音频片段"""
                import numpy as np
                from moviepy import AudioArrayClip

                audio_clips = []
                for i, duration in enumerate(durations):
                    sample_rate = 44100
                    samples = int(duration * sample_rate)
                    audio_array = np.zeros((samples, 2))
                    audio_clip = AudioArrayClip(audio_array, fps=sample_rate)
                    audio_clips.append(audio_clip)
                    print(f"🎵 创建测试音频 {i + 1}: {duration}秒")
                return audio_clips

            def create_complete_advertisement_video_no_text_inline(
                    enterprise_source, audio_clips, add_digital_host=False,
                    target_resolution=(1920, 1080), output_path="final_advertisement_no_text.mp4"):
                """随机剪辑并拼接视频"""
                from moviepy import VideoFileClip, concatenate_videoclips, vfx
                import random

                def resolve_materials_inline(source, valid_extensions):
                    if not source:
                        return []

                    resolved_files = []
                    if isinstance(source, list):
                        for file_path in source:
                            if os.path.isfile(file_path) and file_path.lower().endswith(valid_extensions):
                                resolved_files.append(file_path)
                    elif os.path.isfile(source) and source.lower().endswith(valid_extensions):
                        resolved_files.append(source)
                    elif os.path.isdir(source):
                        for f in os.listdir(source):
                            file_path = os.path.join(source, f)
                            if os.path.isfile(file_path) and f.lower().endswith(valid_extensions):
                                resolved_files.append(file_path)
                    return resolved_files

                VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
                enterprise_files = resolve_materials_inline(enterprise_source, VIDEO_EXTENSIONS)

                if not enterprise_files:
                    raise ValueError(f"没有找到有效的视频文件: {enterprise_source}")

                print(f"📁 找到 {len(enterprise_files)} 个企业素材文件")

                selected_files = random.sample(enterprise_files, min(len(enterprise_files), len(audio_clips)))
                enterprise_clips = []

                # 🔥 同样的修复：使用资源缓存
                video_clips_cache = {}

                try:
                    for idx, audio_clip in enumerate(audio_clips):
                        if idx >= len(selected_files):
                            break

                        video_path = selected_files[idx]

                        # 使用缓存
                        if video_path not in video_clips_cache:
                            video_clips_cache[video_path] = VideoFileClip(video_path)

                        source_video = video_clips_cache[video_path]

                        if source_video.size[0] > source_video.size[1]:
                            video_clip = source_video.resized(target_resolution)
                        else:
                            vertical_resolution = (target_resolution[1], target_resolution[0])
                            video_clip = source_video.resized(vertical_resolution)

                        target_duration = audio_clip.duration

                        if video_clip.duration > target_duration:
                            max_start_time = max(0, video_clip.duration - target_duration - 0.1)
                            start_time = random.uniform(0, max_start_time) if max_start_time > 0 else 0
                            video_clip = video_clip.subclipped(start_time, start_time + target_duration)
                        else:
                            loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                            video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                            video_clip = video_clip.subclipped(0, target_duration)

                        video_clip = video_clip.with_audio(audio_clip)
                        enterprise_clips.append(video_clip)
                        print(f"✅ 创建企业片段 {len(enterprise_clips)}: {os.path.basename(video_path)}")

                    if not enterprise_clips:
                        raise ValueError("没有成功创建任何视频片段")

                    print("🔗 开始拼接所有视频片段...")
                    final_video = concatenate_videoclips(enterprise_clips, method="compose")

                    print(f"🎬 开始生成最终视频: {output_path}")
                    final_video.write_videofile(
                        output_path,
                        codec="libx264",
                        fps=24,
                        audio_codec="aac",
                        threads=1,  # 减少线程数避免死锁
                        verbose=False,  # 禁用详细输出
                        logger=None,  # 禁用进度条
                        temp_audiofile='temp-audio.m4a',  # 指定临时音频文件
                        remove_temp=True  # 自动清理临时文件
                    )

                    file_size = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"✅ 最终视频生成完成!")
                    print(f"📄 文件路径: {output_path}")
                    print(f"📊 文件大小: {file_size:.1f}MB")
                    print(f"⏱️  视频时长: {final_video.duration:.1f}秒")

                except Exception as e:
                    print(f"❌ 随机剪辑失败: {e}")
                    raise e

                finally:
                    # 清理资源
                    try:
                        for clip in enterprise_clips:
                            clip.close()
                        final_video.close()
                        for video_clip in video_clips_cache.values():
                            video_clip.close()
                    except:
                        pass

                return output_path

            if audio_durations:
                audio_duration_list = audio_durations
            else:
                audio_duration_list = [3.0, 4.0, 2.5, 3.5, 5.0]

            audio_clips = create_test_audio_clips_inline(audio_duration_list)
            output_path = os.path.join(output_dir, "random_clip_video.mp4")

            try:
                result_path = create_complete_advertisement_video_no_text_inline(
                    enterprise_source=processed_input_source,
                    audio_clips=audio_clips,
                    add_digital_host=False,
                    target_resolution=target_resolution,
                    output_path=output_path
                )

                for audio_clip in audio_clips:
                    audio_clip.close()

                relative_path = os.path.relpath(result_path, config.get_user_data_dir())
                return relative_path.replace('\\', '/')

            except Exception as e:
                for audio_clip in audio_clips:
                    audio_clip.close()
                raise e

        else:
            raise ValueError(f"不支持的剪辑模式: {clip_mode}")

    finally:
        # 清理临时文件
        for temp_file in temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {str(e)}")

def get_video_edit_simple(video_sources, duration=30, style="抖音风", purpose="社交媒体",
                            use_local_ai=True, api_key=None):
    """
    🔥 灵活的视频编辑函数 - 支持单文件或多文件
    """
    print(f"🎬 开始视频编辑:")
    print(f"   视频源: {video_sources}")
    print(f"   目标时长: {duration}秒")
    print(f"   风格: {style}")

    try:
        check_dependencies()
        # 1. 统一处理输入源
        if isinstance(video_sources, str):
            input_paths = [video_sources]
        else:
            input_paths = video_sources

        # 2. 处理每个路径
        processed_paths = []
        for path in input_paths:

            # 检查是否是URL
            if isinstance(path, str) and (path.startswith('http://') or path.startswith('https://')):
                try:
                    # 下载视频到临时目录
                    downloaded_path = download_file_from_url(path)
                    processed_paths.append(downloaded_path)
                    continue
                except Exception as e:
                    print(f"⚠️ 无法处理URL {path}, 跳过: {str(e)}")
                    continue

            if path.startswith("uploads/"):
                # 转换上传路径
                full_path = os.path.join(UPLOAD_DIR, path.replace("uploads/", ""))
                processed_paths.append(full_path)
            elif os.path.isabs(path):
                # 绝对路径直接使用
                processed_paths.append(path)
            else:
                # 相对路径搜索
                possible_paths = [
                    path,
                    os.path.join(UPLOAD_DIR, path),
                    os.path.join(config.get_user_data_dir(), path),
                    os.path.join(config.get_user_data_dir(), "materials", path),
                ]

                found_path = None
                for possible_path in possible_paths:
                    if os.path.exists(possible_path):
                        found_path = possible_path
                        break

                if found_path:
                    processed_paths.append(found_path)
                else:
                    print(f"⚠️ 文件不存在，将尝试处理: {path}")
                    processed_paths.append(path)

        print(f"📁 处理后的路径: {processed_paths}")

        # 3. 验证文件存在
        valid_files = []
        for path in processed_paths:
            if os.path.exists(path):
                # 验证文件格式
                video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
                if path.lower().endswith(video_extensions):
                    valid_files.append(path)
                    print(f"✅ 找到有效视频: {os.path.basename(path)}")
                else:
                    print(f"⚠️ 不支持的格式: {path}")
            else:
                print(f"❌ 文件不存在: {path}")

        if not valid_files:
            raise ValueError("没有找到有效的视频文件")

        # 4. 创建输出目录
        output_dir = os.path.join(config.get_user_data_dir(), "video_edit_output", str(uuid.uuid4()))
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 5. 准备用户选项
            user_options = {
                "target_duration": duration,
                "target_style": style,
                "target_purpose": purpose
            }

            # 6. 获取API密钥

            final_api_key = api_key or get_api_key_from_file()

            # 7. 创建工作流程编排器
            orchestrator = VideoEditingOrchestrator(
                video_files=valid_files,
                output_dir=output_dir,
                analysis_results=None
            )

            # 8. 执行编辑
            result = orchestrator.run_complete_workflow(
                user_options=user_options,
                api_key=final_api_key,
                use_local_ai=use_local_ai,
                merge_videos=(len(valid_files) > 1)  # 多文件才合并
            )

            print(f"🎉 视频编辑完成: {result}")

            # 9. 处理结果
            if result["status"] == "success":
                output_video = result.get("output_video")
                if output_video and os.path.exists(output_video):
                    # 转换为相对路径
                    user_data_dir = config.get_user_data_dir()
                    relative_path = os.path.relpath(output_video, user_data_dir)
                    warehouse_path = relative_path.replace('\\', '/')

                    print(f"✅ 编辑成功，输出路径: {warehouse_path}")
                    return warehouse_path
                else:
                    raise Exception("输出文件不存在")
            else:
                raise Exception(result.get("error", "编辑失败"))

        finally:
            # 10. 清理资源
            if 'orchestrator' in locals():
                orchestrator.cleanup()

    except Exception as e:
        print(f"❌ 视频编辑失败: {str(e)}")
        raise e
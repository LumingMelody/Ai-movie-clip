from moviepy import TextClip, CompositeVideoClip, ImageClip, ColorClip, concatenate_videoclips, VideoFileClip
import json
import math
import os
import uuid
import requests
import tempfile
from urllib.parse import urlparse
import hashlib
import shutil
import re
import numpy as np

from config import get_user_data_dir
from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_huamn_easy_local
from download_material import download_materials_from_api  # 🔥 统一使用这个下载函数
from get_api_key import get_api_key_from_file


def calculate_text_durations(video_duration, text_list):
    """计算每个文本段落的时间"""
    total_chars = sum(len(text) for text in text_list)
    durations = []
    start_time = 0.0
    for text in text_list:
        char_count = len(text)
        duration = (char_count / total_chars) * video_duration
        end_time = start_time + duration
        durations.append((start_time, end_time))
        start_time = end_time
    return durations


def split_text_for_progressive_subtitles(text, max_chars_per_line=25, max_lines=2):
    """
    🔥 将长文本分割成适合逐段显示的字幕片段
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数（增加到25以减少分段）
        max_lines: 每个字幕片段的最大行数
    
    Returns:
        分割后的文本列表
    """
    import re
    
    # 定义句子结束的标点符号
    sentence_endings = r'[。！？!?]'
    # 定义可以分段的标点符号
    segment_markers = r'[，、,;；]'
    
    # 先按句子结束符分句
    sentences = re.split(f'({sentence_endings})', text)
    
    # 重新组合句子（保留标点）
    combined_sentences = []
    for i in range(0, len(sentences), 2):
        if i + 1 < len(sentences):
            combined_sentences.append(sentences[i] + sentences[i + 1])
        else:
            if sentences[i].strip():
                combined_sentences.append(sentences[i])
    
    # 处理每个句子
    segments = []
    max_segment_length = max_chars_per_line * max_lines
    
    for sentence in combined_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(sentence) <= max_segment_length:
            # 句子不长，直接作为一个片段
            segments.append(sentence)
        else:
            # 句子太长，需要进一步分割
            # 先尝试按次要标点分割
            sub_parts = re.split(f'({segment_markers})', sentence)
            
            current_segment = ""
            for i, part in enumerate(sub_parts):
                if len(current_segment + part) <= max_segment_length:
                    current_segment += part
                else:
                    # 当前段落已满
                    if current_segment.strip():
                        segments.append(current_segment.strip())
                    current_segment = part
            
            # 添加最后一个片段
            if current_segment.strip():
                segments.append(current_segment.strip())
    
    # 后处理：合并过短的片段
    final_segments = []
    i = 0
    while i < len(segments):
        current = segments[i]
        
        # 如果当前片段太短且不是最后一个，尝试与下一个合并
        if len(current) < 10 and i + 1 < len(segments):
            next_segment = segments[i + 1]
            if len(current + next_segment) <= max_segment_length:
                final_segments.append(current + next_segment)
                i += 2
                continue
        
        final_segments.append(current)
        i += 1
    
    return final_segments


def calculate_progressive_subtitle_timings(audio_duration, text_segments, speech_rate=4.0):
    """
    🔥 根据语音速度计算每个字幕片段的显示时间
    
    Args:
        audio_duration: 音频总时长
        text_segments: 字幕片段列表
        speech_rate: 语速（字/秒），中文普通语速约3-5字/秒
    
    Returns:
        每个片段的(开始时间, 结束时间)列表
    """
    timings = []
    current_time = 0
    
    # 计算每个片段需要的时间
    segment_durations = []
    for segment in text_segments:
        # 估算说这段话需要的时间
        estimated_duration = len(segment) / speech_rate
        segment_durations.append(estimated_duration)
    
    # 计算总估算时长
    total_estimated = sum(segment_durations)
    
    # 如果估算时长与实际音频时长差异较大，调整速率
    if total_estimated > 0:
        adjustment_factor = audio_duration / total_estimated
    else:
        adjustment_factor = 1.0
    
    # 分配实际时间
    for i, segment in enumerate(text_segments):
        duration = segment_durations[i] * adjustment_factor
        start_time = current_time
        end_time = current_time + duration
        
        # 确保不超过音频时长
        if end_time > audio_duration:
            end_time = audio_duration
        
        timings.append((start_time, end_time))
        current_time = end_time
        
        # 如果已经达到音频时长，剩余的片段时间设为最后一帧
        if current_time >= audio_duration:
            for j in range(i + 1, len(text_segments)):
                timings.append((audio_duration - 0.1, audio_duration))
            break
    
    return timings


def upload_to_aliyun_oss(local_file_path):
    """
    上传文件到阿里云OSS - 使用你的配置
    """
    try:
        import oss2
        import uuid

        # 🔥 使用你的OSS配置
        # 从环境变量或配置文件读取
        access_key_id = os.environ.get('OSS_ACCESS_KEY_ID', 'YOUR_ACCESS_KEY_ID')
        access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET', 'YOUR_ACCESS_KEY_SECRET')
        endpoint = os.environ.get('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com').replace('https://', '')
        bucket_name = os.environ.get('OSS_BUCKET_NAME', 'lan8-e-business')

        print(f"📤 开始上传到OSS: {local_file_path}")

        # 创建Bucket对象
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)

        # 生成唯一的对象名
        file_extension = os.path.splitext(local_file_path)[1]
        object_name = f"voice_cloning/{uuid.uuid4()}{file_extension}"

        # 上传文件
        result = bucket.put_object_from_file(object_name, local_file_path)
        url = f"https://{bucket_name}.{endpoint.replace('https://', '')}/{object_name}"

        print(url)
        if result.status == 200:
            # 生成可访问的URL
            url = f"https://{bucket_name}.{endpoint.replace('https://', '')}/{object_name}"
            print(f"✅ OSS上传成功: {url}")
            return url
        else:
            print(f"❌ OSS上传失败，状态码: {result.status}")
            return None

    except ImportError:
        print("❌ 需要安装OSS SDK: pip install oss2")
        return None
    except Exception as e:
        print(f"❌ OSS上传失败: {str(e)}")
        return None


def synthesize_speech_with_bailian(text, output_path, reference_audio_path=None, voice_id_cache=None):
    """
    🔥 使用阿里百炼CosyVoice SDK合成语音 - 完整声音克隆实现

    Args:
        text: 要合成的文本
        output_path: 输出音频路径
        reference_audio_path: 参考音频路径（用于声音克隆，可选）
        voice_id_cache: 声音ID缓存字典（可选，用于避免重复克隆）
    """
    try:
        from dashscope.audio.tts_v2 import SpeechSynthesizer, VoiceEnrollmentService
        import dashscope

        # 获取API Key
        api_key = get_api_key_from_file()
        dashscope.api_key = api_key
        os.environ['DASHSCOPE_API_KEY'] = api_key

        print(f"🎤 开始语音合成...")
        if reference_audio_path:
            print(f"🔊 使用声音克隆模式，参考音频: {reference_audio_path}")
        else:
            print(f"🎵 使用普通合成模式")

        # 🔥 根据是否有参考音频选择不同的合成方式
        if reference_audio_path and os.path.exists(reference_audio_path):
            # 声音克隆模式
            try:
                voice_id = None
                
                # 🔥 检查是否有缓存的voice_id
                if voice_id_cache is None:
                    voice_id_cache = {}
                
                # 生成缓存键（基于参考音频路径）
                cache_key = os.path.abspath(reference_audio_path)
                
                # 🔥 尝试从缓存文件加载voice_id
                cache_dir = os.path.join(get_user_data_dir(), "voice_cache")
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, "voice_id_cache.json")
                
                # 加载缓存文件
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r') as f:
                            file_cache = json.load(f)
                            voice_id_cache.update(file_cache)
                    except:
                        pass
                
                if cache_key in voice_id_cache:
                    voice_id = voice_id_cache[cache_key]
                    print(f"🎯 使用缓存的voice_id: {voice_id}")
                else:
                    print("🎯 第一步：上传参考音频到OSS...")

                    # 上传参考音频到OSS获取URL
                    reference_url = upload_to_aliyun_oss(reference_audio_path)

                    if not reference_url:
                        raise Exception("参考音频上传OSS失败")

                    print("🎯 第二步：创建声音克隆...")

                    # 创建语音注册服务实例
                    service = VoiceEnrollmentService()

                    # 调用create_voice方法复刻声音，并生成voice_id
                    voice_id = service.create_voice(
                        target_model="cosyvoice-v1",  # 使用CosyVoice v1模型
                        prefix="cloned",  # 音色前缀
                        url=reference_url  # 参考音频的OSS URL
                    )

                    print(f"✅ 声音克隆创建成功，voice_id: {voice_id}")
                    
                    # 🔥 保存到缓存
                    voice_id_cache[cache_key] = voice_id
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump(voice_id_cache, f)
                        print(f"💾 voice_id已保存到缓存文件")
                    except Exception as e:
                        print(f"⚠️ 保存缓存失败: {e}")

                print("🎯 使用克隆音色合成语音...")

                # 使用克隆的音色进行语音合成
                synthesizer = SpeechSynthesizer(
                    model="cosyvoice-v1",
                    voice=voice_id  # 🔥 使用克隆的voice_id
                )

                audio_data = synthesizer.call(text)
                print(f"🎉 声音克隆合成成功！")

            except Exception as clone_error:
                print(f"⚠️ 声音克隆失败: {str(clone_error)}")
                print(f"🔄 回退到普通语音合成...")

                # 回退到普通合成
                synthesizer = SpeechSynthesizer(
                    model='cosyvoice-v1',
                    voice='longwan'  # 使用默认音色
                )
                audio_data = synthesizer.call(text)
                print(f"✅ 普通语音合成成功")
        else:
            # 普通合成模式
            print(f"🎵 使用普通语音合成")
            synthesizer = SpeechSynthesizer(
                model='cosyvoice-v1',
                voice='longwan'
            )
            audio_data = synthesizer.call(text)
            print(f"✅ 普通语音合成成功")

        # 保存音频文件
        with open(output_path, 'wb') as f:
            f.write(audio_data)

        print(f"✅ 音频保存成功: {output_path}")
        return True

    except ImportError as e:
        print(f"❌ 百炼SDK未安装: {str(e)}")
        print("💡 请运行: pip install dashscope")
        return False
    except Exception as e:
        print(f"❌ 阿里百炼语音合成失败: {str(e)}")
        return False

def create_subtitles_clips(text_list, durations, fontsize=40, font='江西拙楷2.0.ttf', color='Yellow',
                           stroke_color='black'):
    """创建字幕剪辑列表"""
    clips = []
    
    # 获取项目根目录的字体文件路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    font_path = os.path.join(project_root, '微软雅黑.ttf')
    
    # 字体优先级：项目字体 -> 系统中文字体 -> Arial
    if os.path.exists(font_path):
        font_to_use = font_path
    else:
        font_to_use = 'Arial-Unicode-MS'  # macOS 系统中文字体
    
    for i, text in enumerate(text_list):
        start, end = durations[i]
        txt_clip = TextClip(
            text=text,  # 🔥 修复：text 参数在前
            font=font_to_use,  # 🔥 修复：使用正确的字体路径
            font_size=fontsize,
            color=color,
            stroke_color=stroke_color,
            stroke_width=1,
            size=(1000, None),
            method='caption'
        ).with_start(start).with_end(end).with_position(("center", 0.7), relative=True)
        clips.append(txt_clip)
    return clips


def create_title_clip(title, duration, fontsize=140, font='江西拙楷2.0.ttf', color='Yellow', stroke_color='black',
                      bg_color=(0, 0, 0, 30)):
    """创建标题剪辑"""
    
    # 获取项目根目录的字体文件路径
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
    font_path = os.path.join(project_root, '微软雅黑.ttf')
    
    # 字体优先级：项目字体 -> 系统中文字体 -> Arial
    if os.path.exists(font_path):
        font_to_use = font_path
    else:
        font_to_use = 'Arial-Unicode-MS'  # macOS 系统中文字体
    
    return TextClip(
        text=title,  # 🔥 修复：text 参数在前
        font=font_to_use,  # 🔥 修复：使用正确的字体路径
        font_size=fontsize,
        stroke_color=stroke_color,
        stroke_width=5,
        color=color,
        bg_color=bg_color,
    ).with_duration(duration).with_position(("center", 0.08), relative=True)


def is_url(filepath):
    """判断是否为URL链接"""
    try:
        result = urlparse(filepath)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_cache_filename(url):
    """🔥 根据URL生成缓存文件名，避免重复下载"""
    # 使用URL的MD5哈希作为文件名的一部分
    url_hash = hashlib.md5(url.encode()).hexdigest()

    # 从URL中提取原始文件名
    parsed_url = urlparse(url)
    original_filename = os.path.basename(parsed_url.path.split('?')[0])  # 去掉查询参数

    if not original_filename or not original_filename.endswith('.mp4'):
        original_filename = "video.mp4"

    # 组合文件名：哈希值_原始文件名
    cache_filename = f"{url_hash}_{original_filename}"
    return cache_filename


def get_cached_video(url, custom_headers=None):
    """🔥 获取缓存的视频文件，避免重复下载"""
    user_data_dir = get_user_data_dir()
    cache_dir = os.path.join(user_data_dir, "video_cache")
    os.makedirs(cache_dir, exist_ok=True)

    cache_filename = get_cache_filename(url)
    cache_path = os.path.join(cache_dir, cache_filename)

    # 如果缓存文件存在且有效，直接返回
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        print(f"🔄 使用缓存视频: {cache_path}")
        return cache_path

    # 否则下载新文件
    print(f"🌐 下载视频到缓存: {url}")
    try:
        headers = custom_headers if custom_headers else {}

        with requests.get(url, stream=True, headers=headers, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            with open(cache_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"📥 下载进度: {progress:.1f}%", end='\r')

        print(f"\n✅ 视频下载完成: {cache_path}")
        return cache_path
    except Exception as e:
        print(f"❌ 视频下载失败: {str(e)}")
        # 删除不完整的文件
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except:
                pass
        raise


def download_video_from_url_to_temp(url, custom_headers=None):
    """🔥 从URL下载视频到临时文件（兼容原有接口）"""
    try:
        print(f"📥 开始下载视频: {url}")

        # 发送HTTP请求下载文件
        headers = custom_headers if custom_headers else {}
        response = requests.get(url.strip(), stream=True, headers=headers, timeout=60)
        response.raise_for_status()

        # 从URL获取文件扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            ext = os.path.splitext(path)[1]
            # 如果扩展名包含查询参数，只取扩展名部分
            if '?' in ext:
                ext = ext.split('?')[0]
        else:
            ext = '.mp4'  # 默认扩展名

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            suffix=ext,
            delete=False
        )

        # 写入文件内容
        total_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                total_size += len(chunk)

        temp_file.close()

        print(f"✅ 视频下载完成: {temp_file.name} ({total_size / 1024 / 1024:.2f}MB)")
        return temp_file.name

    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        raise Exception(f"无法下载视频文件: {str(e)}")


def check_audio_volume(audio_path):
    """🔥 检查音频文件的音量，判断是否静音"""
    try:
        from moviepy import AudioFileClip

        audio = AudioFileClip(audio_path)

        # 获取音频数据
        audio_array = audio.to_soundarray()

        # 计算RMS音量
        if len(audio_array) > 0:
            rms = np.sqrt(np.mean(audio_array ** 2))
            max_amplitude = np.max(np.abs(audio_array))

            print(f"🔊 音频分析 - RMS: {rms:.6f}, Max: {max_amplitude:.6f}")

            # 如果RMS和最大振幅都很小，认为是静音
            is_silent = rms < 0.001 and max_amplitude < 0.001

            audio.close()
            return is_silent, rms, max_amplitude
        else:
            audio.close()
            return True, 0, 0

    except Exception as e:
        print(f"⚠️ 音频检查失败: {str(e)}")
        return False, 0, 0


def download_file_with_headers(url, local_filename, project_path, custom_headers=None):
    """🔥 图片下载也使用相同的请求头逻辑"""
    try:
        headers = custom_headers if custom_headers else {}
        with requests.get(url, stream=True, headers=headers, timeout=10) as r:
            r.raise_for_status()
            local_filename = os.path.join(project_path, local_filename)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"⚠️ 图片下载失败 {url}: {str(e)}")
        return None


def create_image_clips(pics, durations, text_positions, project_path, custom_headers=None):
    """创建图片剪辑列表"""
    image_clips = []
    for i, url in enumerate(pics):
        if url == "\"\"" or not url:
            continue

        downloaded_path = download_file_with_headers(url, f"img_{i}.png", project_path, custom_headers)
        if downloaded_path:
            # 图片出现在对应文本的开始时刻
            start = text_positions[i][0] if i < len(text_positions) else 0
            try:
                img_clip = ImageClip(downloaded_path).resized(width=800).with_start(start).with_duration(
                    3).with_position(("center", 0.6), relative=True)
                image_clips.append(img_clip)
            except Exception as e:
                print(f"⚠️ 图片处理失败 {downloaded_path}: {str(e)}")
    return image_clips


def handle_digital_human_generation(local_video_path, project_path, data, full_text, output_mp3, user_data_dir):
    """🔥 处理数字人生成的复杂逻辑"""
    print(f"🎬 开始生成数字人视频...")

    try:
        base_video_path = get_video_digital_huamn_easy_local(local_video_path, data["title"], full_text, output_mp3)

        # 🔥 关键修复：确保 base_video_path 是绝对路径
        if not os.path.isabs(base_video_path):
            # 如果返回的是相对路径，转换为绝对路径
            if base_video_path.startswith('projects/'):
                base_video_path = os.path.join(user_data_dir, base_video_path)
            else:
                # 假设路径相对于当前工作目录
                base_video_path = os.path.abspath(base_video_path)

        print(f"📋 数字人视频绝对路径: {base_video_path}")

        # 🔥 验证文件是否存在
        if not os.path.exists(base_video_path):
            raise FileNotFoundError(f"数字人视频文件不存在: {base_video_path}")

        return VideoFileClip(base_video_path), base_video_path

    except Exception as e:
        error_msg = str(e)

        # 处理静音错误
        if "silent audio error" in error_msg or "Audio.AudioSilentError" in error_msg:
            print(f"⚠️ 数字人API检测到音频静音，尝试使用百炼合成语音重新生成")
            return handle_silent_audio_retry(local_video_path, project_path, data, full_text, user_data_dir, error_msg)

        # 处理路径错误
        elif "not found" in error_msg and "projects/" in error_msg:
            print("🔧 尝试修复路径问题...")
            return handle_path_error(error_msg, user_data_dir, local_video_path)

        # 其他错误
        else:
            print(f"❌ 数字人视频生成失败: {error_msg}")
            print("🔄 发生其他错误，回退到使用原视频")
            return VideoFileClip(local_video_path), local_video_path


def handle_silent_audio_retry(local_video_path, project_path, data, full_text, user_data_dir, error_msg):
    """处理静音音频重试逻辑"""
    synthesized_path = os.path.join(project_path, "bailian_synthesized_audio.mp3")
    if synthesize_speech_with_bailian(full_text, synthesized_path):
        print("✅ 百炼语音合成成功，重新调用数字人API")
        try:
            base_video_path = get_video_digital_huamn_easy_local(local_video_path, data["title"], full_text,
                                                                 synthesized_path)

            # 🔥 关键修复：确保 base_video_path 是绝对路径
            if not os.path.isabs(base_video_path):
                if base_video_path.startswith('projects/'):
                    base_video_path = os.path.join(user_data_dir, base_video_path)
                else:
                    base_video_path = os.path.abspath(base_video_path)

            print(f"📋 重试后数字人视频绝对路径: {base_video_path}")

            if not os.path.exists(base_video_path):
                raise FileNotFoundError(f"重试后数字人视频文件不存在: {base_video_path}")

            print("🎉 使用合成语音成功生成数字人视频")
            return VideoFileClip(base_video_path), base_video_path

        except Exception as retry_e:
            print(f"⚠️ 使用合成语音仍然失败，使用原视频: {str(retry_e)}")
            return VideoFileClip(local_video_path), local_video_path
    else:
        print(f"⚠️ 百炼语音合成失败，使用原视频: {error_msg}")
        return VideoFileClip(local_video_path), local_video_path


def handle_path_error(error_msg, user_data_dir, local_video_path):
    """处理路径错误"""
    # 从错误信息中提取相对路径
    path_match = re.search(r"'(projects/[^']+)'", error_msg)
    if path_match:
        relative_path = path_match.group(1)
        corrected_path = os.path.join(user_data_dir, relative_path)
        print(f"🔧 修正路径: {relative_path} → {corrected_path}")
        if os.path.exists(corrected_path):
            print("✅ 路径修复成功")
            return VideoFileClip(corrected_path), corrected_path
        else:
            print(f"❌ 修正后的路径仍不存在: {corrected_path}")
            print("🔄 回退到使用原视频")
            return VideoFileClip(local_video_path), local_video_path
    else:
        # 使用原视频作为fallback
        print("🔄 无法提取路径，回退到使用原视频")
        return VideoFileClip(local_video_path), local_video_path

def safe_set_audio(video_clip, audio_clip):
    """安全地设置音频，兼容不同版本的MoviePy"""
    try:
        return video_clip.set_audio(audio_clip)
    except AttributeError:
        try:
            return video_clip.with_audio(audio_clip)
        except AttributeError:
            print("⚠️ 无法设置音频，可能需要更新MoviePy版本")
            return video_clip

def safe_set_duration(video_clip, duration):
    """安全地设置时长，兼容不同版本的MoviePy"""
    try:
        return video_clip.set_duration(duration)
    except AttributeError:
        try:
            return video_clip.with_duration(duration)
        except AttributeError:
            print(f"⚠️ 无法设置时长，使用原始时长: {video_clip.duration:.2f}秒")
            return video_clip

def safe_without_audio(video_clip):
    """安全地移除音频，兼容不同版本的MoviePy"""
    try:
        return video_clip.without_audio()
    except AttributeError:
        try:
            return video_clip.set_audio(None)
        except AttributeError:
            print("⚠️ 无法移除音频")
            return video_clip


def trans_dgh_img_insert(data: dict, filepath, custom_headers=None, audio_strategy="voice_cloning", add_subtitle=True,
                         insert_image=True) -> str:
    """
    🔥 完整版的数字人视频生成函数 - 支持OSS声音克隆
    """

    print(f"🎵 音频处理策略: {audio_strategy}")
    
    # 🔥 根据音频策略验证输入数据
    if audio_strategy in ["use_provided_audio", "keep_original_audio"]:
        # 使用提供的音频或保留原音频，不需要合成
        print(f"🎵 策略 {audio_strategy}，跳过语音文本验证")
        audio_text = data.get('audio_text', data.get('title', ''))
        subtitle_texts = data.get('text', [data.get('title', '')])
    else:
        # 需要合成语音，验证文本内容
        if not data.get('audio_text'):
            raise ValueError("❌ 语音文本内容为空，无法生成语音")
        
        audio_text = data['audio_text']
        if not audio_text.strip():
            raise ValueError("❌ 语音文本内容为空白，无法生成语音")
        
        print(f"🎵 要合成语音的文本: {audio_text[:100]}...")
        subtitle_texts = data.get('text', [audio_text])
    
    print(f"📝 字幕显示文本: {subtitle_texts}")

    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    project_path = os.path.join(user_data_dir, "projects", project_id)
    os.makedirs(project_path, exist_ok=True)

    # 🔥 预先清理当前目录下的MoviePy临时文件，防止冲突
    import glob
    try:
        temp_audio_files = glob.glob("*TEMP_MPY_wvf_snd*") + glob.glob("temp-audio*.m4a")
        for temp_file in temp_audio_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🧹 预清理MoviePy临时文件: {temp_file}")
            except:
                pass
    except:
        pass

    local_video_path = None
    temp_file_path = None
    
    # 初始化变量，避免作用域问题
    new_audio_clip = None
    base_video = None
    final_video = None
    new_audio_path = None

    try:
        # 处理视频文件
        if is_url(filepath):
            print(f"🌐 检测到HTTP链接: {filepath}")
            try:
                cached_video_path = get_cached_video(filepath, custom_headers)
                local_video_path = os.path.join(project_path, "input_video.mp4")
                shutil.copy2(cached_video_path, local_video_path)
                print(f"📋 已复制缓存视频到项目目录")
            except Exception as e:
                print(f"⚠️ 缓存下载失败，尝试临时下载: {str(e)}")
                temp_file_path = download_video_from_url_to_temp(filepath, custom_headers)
                local_video_path = os.path.join(project_path, "input_video.mp4")
                shutil.copy2(temp_file_path, local_video_path)
        else:
            print(f"📁 使用本地文件: {filepath}")
            if not os.path.exists(filepath):
                raise ValueError(f"❌ 本地视频文件不存在: {filepath}")
            local_video_path = os.path.join(project_path, "input_video.mp4")
            shutil.copy2(filepath, local_video_path)

        from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

        # 🔥 根据音频策略决定音频处理方式
        if audio_strategy == "use_provided_audio":
            # 策略1：使用提供的音频URL作为声音克隆参考
            voice_reference_url = data.get('voice_reference_url')
            if not voice_reference_url:
                raise ValueError("❌ 音频策略为use_provided_audio但未提供音频URL")
            
            print(f"🎵 使用提供的音频URL作为声音克隆参考: {voice_reference_url}")
            
            # 下载参考音频文件到项目目录
            reference_audio_path = os.path.join(project_path, "voice_reference.mp3")
            print(f"🌐 下载参考音频: {voice_reference_url}")
            import requests
            response = requests.get(voice_reference_url)
            with open(reference_audio_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ 参考音频下载成功: {reference_audio_path}")
            # 将标记设置为需要语音合成，使用下载的参考音频
            audio_strategy = "synthesis_with_reference"  # 🔥 修改策略标记
            
        elif audio_strategy == "keep_original_audio":
            # 策略2：保留原视频音频
            print(f"🎵 保留原视频音频")
            original_video = VideoFileClip(local_video_path)
            
            if original_video.audio is None:
                print(f"⚠️ 原视频没有音频，回退到使用title生成语音")
                # 回退到语音合成
                audio_strategy = "synthesis_required"
                original_video.close()
            else:
                # 直接使用原视频的时长
                target_duration = original_video.duration
                print(f"🎵 原视频时长: {target_duration:.2f}秒")
                new_audio_path = None  # 标记不需要新音频
                original_video.close()

        if audio_strategy not in ["keep_original_audio"]:
            # 策略3：语音合成（包括声音克隆）
            if audio_strategy == "synthesis_with_reference":
                # 使用之前下载的参考音频
                print(f"🎤 使用提供的音频作为声音克隆参考...")
                has_reference_audio = True
            else:
                # 🔥 关键步骤1：提取原视频音频作为声音克隆参考
                print(f"🎤 提取原视频音频作为声音克隆参考...")
                reference_audio_path = os.path.join(project_path, "reference_audio.mp3")

                # 从原视频提取音频
                original_video_for_audio = VideoFileClip(local_video_path)

                if original_video_for_audio.audio is not None:
                    try:
                        # 提取前10秒音频作为参考（或者整个音频如果很短）
                        reference_duration = min(10, original_video_for_audio.duration)
                        reference_audio_clip = original_video_for_audio.audio.subclipped(0, reference_duration)
                        reference_audio_clip.write_audiofile(reference_audio_path, logger=None)
                        reference_audio_clip.close()
                        print(f"✅ 参考音频提取成功: {reference_audio_path}")
                        has_reference_audio = True
                    except Exception as e:
                        print(f"⚠️ 参考音频提取失败: {str(e)}")
                        reference_audio_path = None
                        has_reference_audio = False
                else:
                    print(f"⚠️ 原视频没有音频，将使用普通语音合成")
                    reference_audio_path = None
                    has_reference_audio = False

                original_video_for_audio.close()

            # 🔥 关键步骤2：使用OSS声音克隆合成新语音
            print(f"🎵 开始OSS声音克隆合成...")
            new_audio_path = os.path.join(project_path, "cloned_audio.mp3")

            synthesis_success = synthesize_speech_with_bailian(
                audio_text,
                new_audio_path,
                reference_audio_path if has_reference_audio else None  # 🔥 传入参考音频
            )

            if not synthesis_success:
                raise Exception("❌ 声音克隆合成失败")

            print(f"✅ 声音克隆合成成功: {new_audio_path}")

            # 🔥 关键步骤3：获取新语音时长，处理视频匹配
            new_audio_clip = AudioFileClip(new_audio_path)
            target_duration = new_audio_clip.duration
            print(f"🎵 克隆语音时长: {target_duration:.2f}秒")

        # 🔥 根据音频策略处理视频
        if audio_strategy == "keep_original_audio":
            # 保留原音频，使用原视频时长
            print(f"📹 保留原视频和音频，无需调整时长")
            base_video = VideoFileClip(local_video_path)
            video_duration = base_video.duration
        else:
            # 处理原始视频以匹配新音频时长
            original_video = VideoFileClip(local_video_path)
            original_duration = original_video.duration
            print(f"📹 原始视频时长: {original_duration:.2f}秒")

            # 🔥 关键步骤4：视频循环匹配语音时长
            if original_duration < target_duration:
                # 需要循环视频
                loop_count = int(np.ceil(target_duration / original_duration))
                print(f"🔁 需要循环视频 {loop_count} 次匹配语音时长")

                video_clips = []
                remaining_duration = target_duration

                for i in range(loop_count):
                    if remaining_duration >= original_duration:
                        video_clips.append(original_video)
                        remaining_duration -= original_duration
                    else:
                        video_clips.append(original_video.subclipped(0, remaining_duration))
                        break

                base_video = concatenate_videoclips(video_clips)
                print(f"✅ 视频循环完成，最终时长: {base_video.duration:.2f}秒")

                # 释放资源
                original_video.close()
                for clip in video_clips:
                    try:
                        clip.close()
                    except:
                        pass

            elif original_duration > target_duration:
                # 视频比语音长，截取到语音时长
                print(f"✂️ 视频较长，截取到语音时长: {target_duration:.2f}秒")
                base_video = original_video.subclipped(0, target_duration)
                original_video.close()
            else:
                print(f"✅ 视频和语音时长匹配: {original_duration:.2f}秒")
                base_video = original_video
            
            video_duration = target_duration

        # 🔥 关键步骤5：根据音频策略处理音频
        if audio_strategy == "keep_original_audio":
            print(f"🔊 保留原始视频音频")
            # 不做任何音频操作，保持原有音频
        elif new_audio_path and os.path.exists(new_audio_path):
            print(f"🔊 移除原始音频，使用新音频: {new_audio_path}")
            base_video = safe_without_audio(base_video)
            if not new_audio_clip:
                new_audio_clip = AudioFileClip(new_audio_path)
            base_video = safe_set_audio(base_video, new_audio_clip)
        else:
            print(f"🔊 保留原始音频（未提供新音频）")

        # 🔥 关键步骤6：尝试数字人处理（可选）
        if audio_strategy != "keep_original_audio" and new_audio_path:
            try:
                print(f"🤖 尝试调用数字人生成...")

                dh_result = get_video_digital_huamn_easy_local(
                    local_video_path,
                    data.get("title", ""),
                    audio_text,
                    new_audio_path  # 使用新音频
                )

                if dh_result:
                    if dh_result.startswith('projects/'):
                        dh_full_path = os.path.join(user_data_dir, dh_result)
                    else:
                        dh_full_path = dh_result

                    if os.path.exists(dh_full_path):
                        print(f"✅ 数字人视频生成成功，使用数字人视频")

                        try:
                            # 先尝试加载数字人视频
                            dh_video = VideoFileClip(dh_full_path)
                            
                            # 只有加载成功后才关闭原视频
                            base_video.close()
                            if new_audio_clip:
                                new_audio_clip.close()
                                new_audio_clip = None  # 清空引用
                            
                            # 使用数字人视频替换base_video
                            base_video = dh_video

                            # 确保数字人视频时长正确
                            if abs(base_video.duration - target_duration) > 0.1:  # 允许0.1秒误差
                                print(f"🔧 调整数字人视频时长: {base_video.duration:.2f}s -> {target_duration:.2f}s")
                                base_video = base_video.subclipped(0, target_duration)

                            # 重新加载音频，确保使用克隆的音频
                            if new_audio_path and os.path.exists(new_audio_path):
                                new_audio_clip = AudioFileClip(new_audio_path)
                                base_video = safe_set_audio(base_video, new_audio_clip)
                            
                        except Exception as e:
                            print(f"⚠️ 加载数字人视频失败: {str(e)}，继续使用原视频")
                            # 如果加载失败，base_video保持不变

                    else:
                        print(f"⚠️ 数字人视频文件不存在: {dh_full_path}")
                else:
                    print(f"⚠️ 数字人生成返回空结果")

            except Exception as dh_error:
                print(f"⚠️ 数字人处理失败: {str(dh_error)}，使用普通视频")
        else:
            print(f"🎵 音频策略为 {audio_strategy}，跳过数字人处理")

        # 设置最终视频时长（已在上面根据策略设置）
        # video_duration 已在音频策略处理中设置

        # 🔥 确保base_video有效
        if not base_video:
            raise ValueError("基础视频处理失败，base_video为空")

        # 🔥 关键步骤7：处理字幕
        clips_to_compose = [base_video]

        if add_subtitle:
            print(f"📝 创建字幕...")

            # 🔥 使用渐进式字幕显示
            # 如果只有一个长文本，先进行智能分段
            if len(subtitle_texts) == 1:
                print(f"🔪 对长文本进行智能分段...")
                print(f"📄 原始文本: {subtitle_texts[0][:100]}...")
                
                progressive_segments = split_text_for_progressive_subtitles(subtitle_texts[0])
                print(f"📊 分段结果: {len(progressive_segments)} 个片段")
                
                for i, segment in enumerate(progressive_segments):
                    print(f"   片段{i+1}: {segment}")
                
                # 计算每个片段的显示时间
                segment_timings = calculate_progressive_subtitle_timings(video_duration, progressive_segments)
                
                print(f"⏰ 时间分配:")
                for i, (start, end) in enumerate(segment_timings):
                    print(f"   片段{i+1}: {start:.2f}s - {end:.2f}s ({end-start:.2f}s)")
                
                # 创建字幕剪辑
                subtitle_clips = create_subtitles_clips(progressive_segments, segment_timings)
            else:
                # 如果已经是多段文本，直接使用原有逻辑
                print(f"📝 使用多段文本模式: {len(subtitle_texts)} 个片段")
                text_durations = calculate_text_durations(video_duration, subtitle_texts)
                subtitle_clips = create_subtitles_clips(subtitle_texts, text_durations)
            
            clips_to_compose.extend(subtitle_clips)

            # 创建标题
            if data.get("title"):
                print(f"🏷️ 创建标题...")
                title_clip = create_title_clip(data["title"], video_duration)
                clips_to_compose.append(title_clip)
        else:
            print(f"⏭️ 跳过字幕创建")

        # 🔥 关键步骤8：处理图片插入
        if insert_image:
            print(f"🔍 检查图片插入条件: insert_image={insert_image}, pics存在={bool(data.get('pics'))}")
            
            # 如果用户明确要求插入图片但没有提供pics，尝试从文本自动生成图片
            if not data.get("pics") and data.get("text"):
                print(f"🎨 用户要求插入图片但未提供pics，尝试从文本自动生成图片")
                try:
                    # 尝试从文本内容生成相关图片
                    from core.clipgenerate.tongyi_wangxiang import get_text_to_image_v2
                    text_content = ' '.join(data["text"]) if isinstance(data["text"], list) else str(data["text"])
                    
                    # 生成2-3张图片
                    generated_pics = []
                    for i in range(3):  # 生成3张图片
                        try:
                            # 为每张图片添加不同的描述词以增加多样性
                            variations = ["", "，高质量细节", "，商业摄影风格"]
                            enhanced_prompt = text_content + variations[i]
                            
                            result = get_text_to_image_v2(
                                prompt=enhanced_prompt,
                                model="wanx2.1-t2i-turbo", 
                                n=1,
                                size="1024*1024"
                            )
                            
                            if result:
                                # get_text_to_image_v2 直接返回图片URL字符串
                                generated_pics.append(result)
                                print(f"✅ 生成第{i+1}张图片成功")
                            else:
                                print(f"⚠️ 第{i+1}张图片生成失败")
                        except Exception as img_e:
                            print(f"⚠️ 第{i+1}张图片生成异常: {str(img_e)}")
                    
                    if generated_pics:
                        data["pics"] = generated_pics
                        print(f"✅ 自动生成了 {len(generated_pics)} 张图片用于插入")
                    else:
                        print(f"⚠️ 自动图片生成失败，跳过图片插入")
                except Exception as e:
                    print(f"⚠️ 自动图片生成异常: {str(e)}，跳过图片插入")
            
            # 检查是否有图片可以插入
            if data.get("pics"):
                print(f"🖼️ 处理图片插入，图片数量: {len(data['pics'])}")
                # 使用相同的时间分配逻辑
                if 'segment_timings' in locals():
                    # 如果使用了渐进式字幕，使用相同的时间分配
                    image_clips = create_image_clips(data["pics"], video_duration, segment_timings[:len(data["pics"])], project_path, custom_headers)
                else:
                    # 否则使用原有逻辑
                    text_durations = calculate_text_durations(video_duration, subtitle_texts)
                    image_clips = create_image_clips(data["pics"], video_duration, text_durations, project_path, custom_headers)
                clips_to_compose.extend(image_clips)
            else:
                print(f"⏭️ 跳过图片插入 - 未找到图片数据")
        else:
            print(f"⏭️ 跳过图片插入 - insert_image=False")

        # 🔥 关键步骤9：合成最终视频
        print(f"🎬 合成最终视频...")
        
        # 检查clips_to_compose中是否有None值
        valid_clips = [clip for clip in clips_to_compose if clip is not None]
        if not valid_clips:
            raise ValueError("没有有效的视频片段可以合成")
        
        # 检查base_video是否存在且有效
        if not base_video or base_video.duration <= 0:
            raise ValueError("基础视频无效或已被释放")
        
        final_video = CompositeVideoClip(valid_clips)
        final_video = safe_set_duration(final_video, video_duration)

        # 输出视频
        output_path = os.path.join(project_path, "final_video.mp4")

        try:
            import tempfile
            import threading

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_audio_name = f"temp_audio_{threading.current_thread().ident}.m4a"
                temp_audio_path = os.path.join(temp_dir, temp_audio_name)

                final_video.write_videofile(
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=temp_audio_path,
                    remove_temp=True,
                    logger=None
                )
            print(f"✅ 视频生成成功: {output_path}")

        finally:
            # 🔥 重要：手动释放MoviePy资源，防止文件占用
            try:
                if 'final_video' in locals() and final_video is not None:
                    final_video.close()
                    print("🔧 已释放final_video资源")
            except:
                pass

            try:
                if 'base_video' in locals() and base_video is not None:
                    base_video.close()
                    print("🔧 已释放base_video资源")
            except:
                pass

            # 释放音频资源
            try:
                if 'new_audio_clip' in locals() and new_audio_clip is not None:
                    new_audio_clip.close()
                    print("🔧 已释放audio_clip资源")
            except:
                pass

            # 释放所有clip资源
            for clip in clips_to_compose:
                try:
                    clip.close()
                except:
                    pass
            print("🔧 已释放所有clip资源")

        # 🔥 返回相对于warehouse的路径
        relative_path = os.path.relpath(output_path, user_data_dir)
        warehouse_path = relative_path.replace('\\', '/')

        print(f"📁 warehouse路径: {warehouse_path}")
        return warehouse_path

    finally:
        # 🔥 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"🗑️ 已清理临时文件: {temp_file_path}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {str(e)}")

        # 🔥 额外清理：删除可能残留的MoviePy临时文件
        import glob
        try:
            temp_audio_files = glob.glob("temp-audio*.m4a") + glob.glob("*TEMP_MPY_wvf_snd*")
            for temp_file in temp_audio_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🗑️ 清理MoviePy临时文件: {temp_file}")
                except Exception as e:
                    print(f"⚠️ 清理MoviePy临时文件失败: {temp_file} - {e}")
        except Exception as e:
            print(f"⚠️ 清理临时文件时出错: {e}")

def get_materials_by_tag(tag="", custom_headers=None):
    """🔥 使用download_materials_from_api获取指定标签的素材"""
    try:
        print(f"🏷️ 使用download_materials_from_api获取标签 '{tag}' 的素材...")
        downloaded_files = download_materials_from_api(tag, custom_headers)
        print(f"✅ 获取到 {len(downloaded_files)} 个素材文件")
        return downloaded_files
    except Exception as e:
        print(f"❌ 获取素材失败: {str(e)}")
        return []


def trans_dgh_img_insert_with_materials(data: dict, filepath, material_tag="", custom_headers=None,
                                        audio_strategy="prefer_original") -> str:
    """🔥 增强版本：结合素材下载功能"""
    # 如果指定了素材标签，先下载素材
    if material_tag:
        print(f"🎯 开始下载素材标签: {material_tag}")
        materials = get_materials_by_tag(material_tag, custom_headers)
        if materials:
            print(f"📦 素材下载完成，可用文件: {len(materials)} 个")
        else:
            print(f"⚠️ 未获取到标签 '{material_tag}' 的素材")

    # 继续执行原有的视频生成逻辑，传递所有参数
    return trans_dgh_img_insert(data, filepath, custom_headers, audio_strategy)


def trans_dgh_img_insert_with_material_video(data: dict, material_tag="", custom_headers=None, video_index=0,
                                             audio_strategy="prefer_original") -> str:
    """🔥 新增：直接使用download_materials_from_api下载的视频作为输入"""
    # 先下载指定标签的素材
    if not material_tag:
        raise ValueError("❌ 必须指定素材标签")

    print(f"🎯 下载素材标签: {material_tag}")
    materials = get_materials_by_tag(material_tag, custom_headers)

    if not materials:
        raise ValueError(f"❌ 未找到标签 '{material_tag}' 的素材")

    # 过滤出视频文件
    video_files = [f for f in materials if f.endswith('.mp4')]

    if not video_files:
        raise ValueError(f"❌ 标签 '{material_tag}' 中没有找到视频文件")

    # 选择指定索引的视频文件
    if video_index >= len(video_files):
        video_index = 0  # 如果索引超出范围，使用第一个

    selected_video = video_files[video_index]
    print(f"🎬 选择视频文件: {selected_video}")

    # 使用选择的视频文件进行处理
    return trans_dgh_img_insert(data, selected_video, custom_headers, audio_strategy)


def clear_video_cache():
    """🔥 清理视频缓存"""
    user_data_dir = get_user_data_dir()
    cache_dir = os.path.join(user_data_dir, "video_cache")

    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print("🗑️ 视频缓存已清理")
        except Exception as e:
            print(f"⚠️ 清理缓存失败: {str(e)}")
    else:
        print("📁 缓存目录不存在")


# 🔥 使用示例
if __name__ == "__main__":
    data = {
        "pics": [
            "https://img0.baidu.com/it/u=1414677129,166969041&fm=253&fmt=auto&app=120&f=JPEG?w=1101&h=800",
            "https://img0.baidu.com/it/u=175547649,566518480&fm=253&fmt=auto&app=120&f=JPEG?w=889&h=500",
        ],
        "text": [
            "各位朋友，今天来聊聊财税。",
            "财税就是财政和税收，它对国家和企业都至关重要。",
        ],
        "title": "财税"
    }

    # 设置请求头
    custom_headers = {
        'Authorization': 'Bearer test1',
        'tenant-id': '1'
    }
    filepath = ''
    # 🔥 使用示例：完整的音频处理测试
    result_path = trans_dgh_img_insert(data, filepath, custom_headers)
    print(f"✅ 返回的warehouse路径: {result_path}")

    # 🔥 验证输出视频是否有音频
    try:
        from moviepy import VideoFileClip

        user_data_dir = get_user_data_dir()
        full_output_path = os.path.join(user_data_dir, result_path)

        if os.path.exists(full_output_path):
            test_clip = VideoFileClip(full_output_path)
            if test_clip.audio is not None:
                print("🔊 输出视频包含音频轨道")
                # 简单检查音频是否有声音
                audio_array = test_clip.audio.to_soundarray()
                if len(audio_array) > 0:
                    rms = np.sqrt(np.mean(audio_array ** 2))
                    print(f"🔊 输出音频RMS: {rms:.6f}")
                    if rms > 0.001:
                        print("✅ 输出视频音频正常")
                    else:
                        print("⚠️ 输出视频音频可能静音")
                else:
                    print("⚠️ 输出视频音频数据为空")
            else:
                print("❌ 输出视频没有音频轨道")
            test_clip.close()
        else:
            print(f"❌ 输出文件不存在: {full_output_path}")
    except Exception as e:
        print(f"⚠️ 音频验证失败: {str(e)}")

# 🔥 清理缓存（可选）
# clear_video_cache()
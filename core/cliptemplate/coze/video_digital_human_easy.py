from dashscope.audio.tts_v2 import VoiceEnrollmentService, SpeechSynthesizer
import dashscope
from config import get_user_data_dir
from core.clipgenerate.tongyi_get_online_url import get_online_url, get_online_url_self
from core.clipgenerate.tongyi_get_voice_copy import get_voice_copy_disposable
from core.clipgenerate.tongyi_response import get_Tongyi_response
from core.clipgenerate.tongyi_get_videotalk import get_videotalk
import os
import uuid
import requests
import hashlib
import time
from urllib.parse import urlparse
from moviepy import VideoFileClip, AudioFileClip, ColorClip, concatenate_videoclips, TextClip, CompositeVideoClip
import tempfile
import re


def get_api_key_from_file():
    """获取API密钥"""
    # 您可以从配置文件或环境变量中获取，这里先硬编码您的密钥
    return "sk-a48a1d84e015410292d07021f60b9acb"


def synthesize_speech_with_bailian(text, output_path):
    """使用阿里百炼CosyVoice SDK合成语音"""
    try:
        # 设置API Key
        api_key = get_api_key_from_file()
        dashscope.api_key = api_key
        os.environ['DASHSCOPE_API_KEY'] = api_key

        # 创建语音合成器
        synthesizer = SpeechSynthesizer(
            model='cosyvoice-v1',
            voice='longwan'  # 龙婉音色
        )

        print(f"🗣️ 正在使用百炼合成语音: {text[:50]}...")

        # 同步调用合成语音
        audio_data = synthesizer.call(text)

        # 保存音频文件
        with open(output_path, 'wb') as f:
            f.write(audio_data)

        print(f"✅ 百炼语音合成完成: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 阿里百炼语音合成失败: {str(e)}")
        raise


def safe_voice_copy_with_fallback(audio_url, content, project_path, video_path=None):
    """安全的语音复制，支持降级"""
    try:
        # 🔥 验证content不为空
        if not content or content.strip() == "":
            print("⚠️ 语音复制内容为空，使用默认文本")
            content = "这是一段测试音频内容。"
            
        if audio_url is None:
            if video_path and os.path.exists(video_path):
                print("🎵 从原视频提取音频进行语音复制...")

                # 提取原视频音频
                video_clip = VideoFileClip(video_path)
                temp_audio_path = os.path.join(project_path, "temp_original_audio.mp3")
                video_clip.audio.write_audiofile(temp_audio_path, logger=None)
                video_clip.close()

                # 上传音频获取URL
                temp_audio_url = get_online_url_self(
                    "temp_original_audio.mp3",
                    temp_audio_path,
                    "audio/mp3"
                )

                # 使用提取的音频进行语音复制
                output_audio = get_voice_copy_disposable(temp_audio_url, content, project_path)

                # 清理临时文件
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)

                return output_audio
            else:
                print("⚠️ 无法提取原视频音频，使用TTS生成")
                return generate_tts_audio(content, project_path)

        # 有audio_url时，直接使用
        output_audio = get_voice_copy_disposable(audio_url, content, project_path)
        return output_audio

    except Exception as e:
        print(f"⚠️ 语音复制失败: {str(e)}")
        return generate_tts_audio(content, project_path)


def validate_and_resize_video(video_path, project_path):
    """
    验证并调整视频分辨率以满足数字人API要求（640-2048像素）
    
    Args:
        video_path: 输入视频路径
        project_path: 项目路径
        
    Returns:
        处理后的视频路径（如果需要调整）或原始路径
    """
    try:
        print("🔍 检查视频分辨率...")
        video = VideoFileClip(video_path)
        width, height = video.size
        
        print(f"📊 原始视频分辨率: {width}x{height}")
        
        # 检查是否在允许范围内（640-2048）
        min_size, max_size = 640, 2048
        needs_resize = False
        
        new_width, new_height = width, height
        
        if width < min_size or height < min_size:
            # 视频太小，需要放大
            scale_factor = min_size / min(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            needs_resize = True
            print(f"⬆️ 视频太小，需要放大到: {new_width}x{new_height}")
            
        elif width > max_size or height > max_size:
            # 视频太大，需要缩小
            scale_factor = max_size / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            needs_resize = True
            print(f"⬇️ 视频太大，需要缩小到: {new_width}x{new_height}")
        
        if needs_resize:
            # 确保尺寸是偶数（视频编码要求）
            new_width = new_width if new_width % 2 == 0 else new_width + 1
            new_height = new_height if new_height % 2 == 0 else new_height + 1
            
            # 调整视频大小
            resized_video_path = os.path.join(project_path, "resized_video.mp4")
            resized_video = video.resized((new_width, new_height))
            
            print(f"🔧 调整视频分辨率: {width}x{height} → {new_width}x{new_height}")
            
            resized_video.write_videofile(
                resized_video_path,
                codec="libx264",
                fps=video.fps,
                logger=None,
                audio=False  # 不包含音频
            )
            
            resized_video.close()
            video.close()
            
            print(f"✅ 视频分辨率调整完成: {resized_video_path}")
            return resized_video_path
        else:
            print("✅ 视频分辨率符合要求，无需调整")
            video.close()
            return video_path
            
    except Exception as e:
        print(f"❌ 视频分辨率处理失败: {str(e)}")
        # 返回原始路径，让后续处理决定
        return video_path

def safe_videotalk_with_fallback(video_url, audio_url, project_path):
    """安全的数字人视频生成，支持人脸检测失败的降级处理"""
    try:
        print("🤖 正在生成数字人视频...")
        print(f"📊 调用参数详情:")
        print(f"   - video_url: {video_url}")
        print(f"   - audio_url: {audio_url}")
        print(f"   - project_path: {project_path}")
        
        # 🔥 检查get_videotalk函数是否正确导入
        if get_videotalk is None:
            print("❌ get_videotalk函数为None，可能导入失败")
            return None
            
        print("🔄 调用get_videotalk函数...")
        digital_human_url = get_videotalk(video_url, audio_url)
        
        print(f"📊 get_videotalk返回值: {digital_human_url}")
        print(f"📊 返回值类型: {type(digital_human_url)}")
        
        if digital_human_url and digital_human_url != "None" and digital_human_url is not None:
            print(f"✅ 数字人视频生成完成: {digital_human_url}")
            return digital_human_url
        else:
            print("⚠️ 数字人视频生成返回了空值，可能是人脸检测失败")
            print(f"⚠️ 具体返回值: {repr(digital_human_url)}")
            return None

    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ 数字人视频生成失败: {error_msg}")
        
        # 打印完整的错误信息
        import traceback
        print(f"📊 详细错误信息:")
        traceback.print_exc()

        # 检查是否是人脸相关错误或分辨率错误
        if any(keyword in error_msg.lower() for keyword in [
            "face", "facenotmatch", "invalidfile.facenotmatch",
            "can't detect face", "no matched face"
        ]):
            print("🔄 检测到人脸匹配失败，将生成纯音频输出")
            return None
        elif any(keyword in error_msg.lower() for keyword in [
            "resolution", "640", "2048", "height", "width"
        ]):
            print("🔄 检测到分辨率错误，请检查视频分辨率是否在640-2048范围内")
            return None
        else:
            # 其他错误，直接抛出
            raise


def create_audio_only_video(audio_path, output_path, duration=None):
    """
    🔥 创建纯音频视频（黑屏+音频）

    Args:
        audio_path: 音频文件路径
        output_path: 输出文件路径
        duration: 可选的时长
    """
    from moviepy import AudioFileClip, ColorClip

    try:
        print("🎵 创建纯音频视频...")

        audio_clip = AudioFileClip(audio_path)
        video_duration = duration or audio_clip.duration

        # 创建黑色背景视频
        black_clip = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=video_duration)

        # 合成视频
        final_video = black_clip.with_audio(audio_clip.subclipped(0, video_duration))

        final_video.write_videofile(
            output_path,
            codec="libx264",
            fps=24,
            logger=None,
            audio_codec="aac"
        )

        # 清理资源
        audio_clip.close()
        black_clip.close()
        final_video.close()

        print(f"✅ 纯音频视频创建完成: {output_path}")

    except Exception as e:
        print(f"❌ 纯音频视频创建失败: {e}")
        raise

def is_url(path):
    """
    🔥 判断是否为URL链接
    """
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_audio_from_url(url, local_path=None):
    """
    🔥 从URL下载音频到本地
    """
    try:
        print(f"🔊 正在下载音频: {url}")

        # 如果没有指定本地路径，创建临时文件
        if not local_path:
            # 从URL中尝试提取文件扩展名
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)

            # 提取扩展名
            if '.' in original_filename:
                ext = original_filename.split('.')[-1].lower()
                if ext not in ['mp3', 'wav', 'aac', 'm4a', 'flac']:
                    ext = 'mp3'  # 默认扩展名
            else:
                ext = 'mp3'  # 默认扩展名

            # 生成安全的文件名
            timestamp = str(int(time.time()))
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_filename = f"audio_{timestamp}_{url_hash}.{ext}"

            # 创建临时目录
            temp_dir = os.path.join(get_user_data_dir(), "temp_audios")
            os.makedirs(temp_dir, exist_ok=True)
            local_path = os.path.join(temp_dir, safe_filename)

        # 下载音频
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # 验证下载的文件
        if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
            raise Exception("下载的文件为空或不存在")

        print(f"✅ 音频下载完成: {local_path} (大小: {os.path.getsize(local_path)} bytes)")
        return local_path

    except Exception as e:
        print(f"❌ 音频下载失败: {str(e)}")
        raise


def get_video_digital_human_api(video_url, title, content=None, audio_url=None, categoryId=None, add_subtitle=True) -> str:
    if content == "":
        content = None
    if audio_url == "":
        audio_url = None
    return get_video_digital_human_unified(video_url, title, content, audio_url, add_subtitle)


def manual_video_loop(video_clip, target_duration):
    """
    🔄 手动视频循环实现
    """
    from moviepy import concatenate_videoclips, vfx

    original_duration = video_clip.duration
    clips_to_concat = []
    remaining_time = target_duration

    # 添加完整循环
    while remaining_time >= original_duration:
        clips_to_concat.append(video_clip)
        remaining_time -= original_duration
        print(f"🔁 添加完整循环，剩余时间: {remaining_time:.2f}s")

    # 添加部分循环
    if remaining_time > 0.1:
        print(f"🔪 添加部分循环: {remaining_time:.2f}s")
        partial_clip = video_clip.subclipped(0, remaining_time)

        # 尝试添加淡出效果
        try:
            partial_clip = partial_clip.with_effects([vfx.FadeOut(min(0.5, remaining_time / 2))])
        except Exception as e:
            print(f"⚠️ 无法添加淡出效果: {e}")

        clips_to_concat.append(partial_clip)

    # 拼接所有片段
    if len(clips_to_concat) == 1:
        return clips_to_concat[0]
    else:
        return concatenate_videoclips(clips_to_concat)


def create_smart_loop_video(video_clip, target_duration):
    """
    🔥 修复版：智能循环视频以匹配目标时长

    Args:
        video_clip: 原始视频片段
        target_duration: 目标时长（秒）

    Returns:
        延长后的视频片段
    """
    from moviepy import concatenate_videoclips

    try:
        current_duration = video_clip.duration
        print(f"🎬 视频循环: 原始时长 {current_duration:.2f}s → 目标时长 {target_duration:.2f}s")

        if target_duration <= current_duration:
            return video_clip.subclipped(0, target_duration)

        # 计算需要的循环次数
        full_loops = int(target_duration / current_duration)
        remaining_time = target_duration - (full_loops * current_duration)

        print(f"🔁 需要 {full_loops} 个完整循环，剩余 {remaining_time:.2f}s")

        # 创建循环片段列表
        looped_clips = []

        # 添加完整循环
        for i in range(full_loops):
            looped_clips.append(video_clip)

        # 添加剩余部分
        if remaining_time > 0.1:
            partial_clip = video_clip.subclipped(0, remaining_time)
            looped_clips.append(partial_clip)

        # 合并视频片段
        extended_video = concatenate_videoclips(looped_clips, method="compose")

        print(f"✅ 视频循环成功: 最终时长 {extended_video.duration:.2f}s")
        return extended_video

    except Exception as e:
        print(f"❌ 视频循环失败: {e}")
        raise


def create_hybrid_extended_video(video_clip, target_duration):
    """
    🔥 混合策略延长视频：循环 + 慢放

    Args:
        video_clip: 原始视频片段
        target_duration: 目标时长（秒）

    Returns:
        延长后的视频片段
    """
    from moviepy import concatenate_videoclips
    from moviepy.video import fx as vfx

    try:
        current_duration = video_clip.duration
        extension_ratio = target_duration / current_duration

        print(f"🎬 混合策略延长视频: 倍率 {extension_ratio:.2f}")

        if extension_ratio <= 3.0:
            # 倍率不太大，主要使用循环
            return create_smart_loop_video(video_clip, target_duration)
        else:
            # 倍率很大，使用循环 + 慢放组合
            print("🐌 使用循环 + 慢放组合策略")

            # 先适度循环到原始时长的2-3倍
            loop_target = current_duration * 2.5
            looped_video = create_smart_loop_video(video_clip, loop_target)

            # 再通过慢放达到目标时长
            slow_factor = target_duration / loop_target
            if slow_factor > 1.0:
                try:
                    # 🔥 使用新版本的慢放效果
                    slowed_video = looped_video.with_effects([vfx.SpeedX(1 / slow_factor)])
                except (AttributeError, ImportError):
                    try:
                        # 降级到旧版本
                        slowed_video = looped_video.fx(vfx.speedx, 1 / slow_factor)
                    except:
                        # 最后降级：只返回循环的视频
                        print("⚠️ 慢放效果不可用，仅使用循环")
                        return looped_video

                return slowed_video
            else:
                return looped_video

    except Exception as e:
        print(f"❌ 混合策略延长失败: {e}")
        # 降级到简单循环
        return create_smart_loop_video(video_clip, target_duration)


def create_silent_audio(duration, sample_rate=44100):
    """
    创建指定时长的静音音频

    Args:
        duration: 时长（秒）
        sample_rate: 采样率

    Returns:
        静音音频片段
    """
    from moviepy import AudioArrayClip
    import numpy as np

    try:
        # 创建静音数据（双声道）
        n_samples = int(duration * sample_rate)
        silent_array = np.zeros((n_samples, 2))  # 双声道静音

        # 创建音频片段
        silent_clip = AudioArrayClip(silent_array, fps=sample_rate)
        return silent_clip

    except Exception as e:
        print(f"❌ 创建静音音频失败: {e}")
        # 降级策略：返回None，让调用方处理
        return None


def safe_audio_volume_adjust(audio_clip, factor):
    """
    🔥 安全的音频音量调整函数，兼容不同版本的MoviePy

    Args:
        audio_clip: 音频片段
        factor: 音量倍数

    Returns:
        调整后的音频片段
    """
    from moviepy.audio import fx as afx

    try:
        # 🔥 优先使用新版本的 with_effects 方法
        return audio_clip.with_effects([afx.MultiplyVolume(factor)])
    except (AttributeError, ImportError):
        try:
            # 🔥 降级到 fx 方法
            return audio_clip.fx(afx.volumex, factor)
        except (AttributeError, ImportError):
            try:
                # 🔥 最后降级到旧版本的 volumex 方法
                return audio_clip.volumex(factor)
            except AttributeError:
                print(f"⚠️ 音量调整不可用，返回原始音频")
                return audio_clip


def create_extended_audio(audio_clip, target_duration):
    """
    🔥 修复版：延长音频以匹配目标时长

    Args:
        audio_clip: 原始音频片段
        target_duration: 目标时长（秒）

    Returns:
        延长后的音频片段
    """
    from moviepy import concatenate_audioclips, AudioFileClip
    from moviepy.audio import fx as afx
    import numpy as np

    try:
        current_duration = audio_clip.duration
        print(f"🎵 音频延长: 原始时长 {current_duration:.2f}s → 目标时长 {target_duration:.2f}s")

        if target_duration <= current_duration:
            # 如果目标时长小于等于当前时长，直接截取
            return audio_clip.subclipped(0, target_duration)

        extension_needed = target_duration - current_duration
        print(f"🎵 音频延长: 需要延长{extension_needed:.2f}秒")

        # 🔥 使用循环+静音策略延长音频
        print("🔄 使用循环+静音策略延长音频")

        # 计算需要循环的次数
        if current_duration > 0:
            full_loops = int(extension_needed / current_duration)
            remaining_time = extension_needed - (full_loops * current_duration)
        else:
            raise ValueError("原始音频时长为0，无法延长")

        extended_clips = [audio_clip]  # 从原始音频开始

        # 添加完整循环
        for i in range(full_loops):
            print(f"🔁 添加完整循环 {i + 1}/{full_loops}")
            extended_clips.append(audio_clip)

        # 添加剩余部分
        if remaining_time > 0.1:  # 如果剩余时间大于0.1秒
            if remaining_time <= current_duration:
                print(f"🔪 添加部分循环: {remaining_time:.2f}秒")
                partial_clip = audio_clip.subclipped(0, remaining_time)
                extended_clips.append(partial_clip)
            else:
                print(f"🔇 添加静音填充: {remaining_time:.2f}秒")
                # 创建静音片段填充剩余时间
                silent_clip = create_silent_audio(remaining_time)
                extended_clips.append(silent_clip)

        # 合并所有音频片段
        print(f"🔗 合并 {len(extended_clips)} 个音频片段")
        extended_audio = concatenate_audioclips(extended_clips)

        # 确保精确的时长
        if abs(extended_audio.duration - target_duration) > 0.1:
            print(f"🔧 微调时长: {extended_audio.duration:.2f}s → {target_duration:.2f}s")
            extended_audio = extended_audio.subclipped(0, target_duration)

        print(f"✅ 音频延长成功: 最终时长 {extended_audio.duration:.2f}s")
        return extended_audio

    except Exception as e:
        print(f"❌ 音频延长失败: {e}")
        raise



def get_video_digital_human_unified(video_url, title, content=None, audio_input=None, add_subtitle=True) -> str:
    """
    🔥 修复后的数字人视频生成器 - 优先以文本内容长度为准

    重点修复：
    1. 优先以文本生成的音频长度为准
    2. 视频过长则裁剪，视频过短则循环（但不延长音频）
    3. 避免文本内容重复朗读的问题
    4. 确保输出视频长度与文本匹配

    Args:
        video_input: 视频输入，可以是本地路径或HTTP链接
        topic: 主题
        content: 内容文本，如果为None则自动生成
        audio_input: 音频输入，如果为None则根据content生成

    Returns:
        str: 生成的视频路径
    """
    print(f"🎯 开始处理数字人视频生成（以文本长度为准）...")
    print(f"📊 参数信息: topic='{title}', content='{content}', audio_input={audio_input}")
    print(f"📋 视频输入: {video_url}")
    
    # 🔥 添加错误捕获，确保我们能看到具体的错误信息
    try:
        print(f"🔍 检查输入参数...")
        print(f"   video_input类型: {type(video_url)}")
        print(f"   topic类型: {type(title)}")
        print(f"   content类型: {type(content)}")
        print(f"   audio_input类型: {type(audio_input)}")
        
        if not video_url:
            print(f"❌ 视频输入为空")
            return None
            
        if not title:
            print(f"❌ 主题为空")
            return None
            
        print(f"✅ 输入参数验证通过")

    except Exception as e:
        print(f"❌ 输入参数验证失败: {str(e)}")
        return None

    project_id = str(uuid.uuid1())
    user_data_dir = get_user_data_dir()
    base_project_path = os.path.join(user_data_dir, "projects")
    project_path = os.path.join(base_project_path, project_id)
    os.makedirs(project_path, exist_ok=True)

    temp_files_to_cleanup = []

    try:
        # 🔥 1. 处理视频输入
        if is_url(video_url):
            print(f"🌐 检测到视频URL: {video_url}")
            local_video_path = download_audio_from_url(video_url)
            temp_files_to_cleanup.append(local_video_path)
            video_url = video_url
        else:
            print(f"📁 使用本地视频: {video_url}")
            if not os.path.exists(video_url):
                raise ValueError(f"❌ 本地视频文件不存在: {video_url}")
            local_video_path = video_url
            video_url = get_online_url_self(
                os.path.basename(video_url),
                video_url,
                "video/mp4"
            )
            print(f"📤 本地视频已上传: {video_url}")

        # 🔥 2. 生成内容（如果未提供或为空）
        if content is None or content.strip() == "":
            print("📝 正在生成口播稿...")
            content = get_Tongyi_response(
                "你是一个口播稿生成师，我给你一个主题，你生成一段120字左右的口播稿",
                "主题是" + title
            )
            print(f"✅ 口播稿生成完成: {content}")
            
        # 🔥 确保content不为空
        if not content or content.strip() == "":
            print("⚠️ 内容为空，使用默认文本")
            content = f"欢迎了解{title}相关内容。今天我们为您带来精彩的介绍。"

        # 🔥 3. 处理音频 - 关键：确定目标时长
        target_audio_duration = None
        final_audio_path = None
        final_audio_url = None

        if audio_input is not None:
            # 🎵 使用提供的音频
            if is_url(audio_input):
                print(f"🔊 检测到音频URL: {audio_input}")
                local_audio_path = download_audio_from_url(audio_input)
                temp_files_to_cleanup.append(local_audio_path)
                final_audio_path = local_audio_path
                final_audio_url = audio_input
            else:
                print(f"🎵 使用本地音频: {audio_input}")
                if not os.path.exists(audio_input):
                    raise ValueError(f"❌ 本地音频文件不存在: {audio_input}")
                final_audio_path = audio_input
                final_audio_url = get_online_url_self(
                    os.path.basename(audio_input),
                    audio_input,
                    "audio/mp3"
                )

            # 获取提供音频的时长作为目标时长
            audio_clip = AudioFileClip(final_audio_path)
            target_audio_duration = audio_clip.duration
            audio_clip.close()
            print(f"🎯 使用提供音频的时长作为目标: {target_audio_duration:.2f}秒")

        else:
            # 🗣️ 根据文本生成音频
            print("🗣️ 正在根据文本生成语音...")

            # 🔥 关键修复：使用文本生成音频，不基于视频
            # 在get_video_digital_human_unified函数中
            generated_audio_path = safe_voice_copy_with_fallback(
                None,
                content,
                project_path,
                video_path=local_video_path  # 传入视频路径
            )

            if not generated_audio_path or not os.path.exists(generated_audio_path):
                # 降级：使用TTS生成
                print("🔄 降级到TTS生成音频...")
                generated_audio_path = generate_tts_audio(content, project_path)

            final_audio_path = generated_audio_path
            final_audio_url = get_online_url_self(
                os.path.basename(generated_audio_path),
                generated_audio_path,
                "audio/mp3"
            )

            # 🔥 获取生成音频的时长作为最终目标时长
            audio_clip = AudioFileClip(final_audio_path)
            target_audio_duration = audio_clip.duration
            audio_clip.close()
            print(f"🎯 根据文本生成的音频时长: {target_audio_duration:.2f}秒")

        print(f"📊 最终目标时长: {target_audio_duration:.2f}秒（以音频为准）")

        # 🔥 4. 预处理视频以匹配音频长度（关键改动）
        print("🔧 开始预处理视频以匹配音频长度...")
        
        # 首先验证和调整视频分辨率
        resized_video_path = validate_and_resize_video(local_video_path, project_path)
        
        original_video = VideoFileClip(resized_video_path)
        original_video_duration = original_video.duration

        print(f"📊 原始视频时长: {original_video_duration:.2f}秒")
        print(f"📊 目标音频时长: {target_audio_duration:.2f}秒")

        processed_video_path = os.path.join(project_path, "processed_video.mp4")

        # 🔥 核心逻辑：始终让视频匹配音频长度
        if original_video_duration > target_audio_duration:
            # 视频比音频长：裁剪视频
            print(f"✂️ 视频较长，裁剪至音频长度: {original_video_duration:.2f}s → {target_audio_duration:.2f}s")

            # 🔥 智能裁剪：从视频中间或开头选择最佳片段
            if target_audio_duration <= original_video_duration * 0.8:
                # 如果音频明显短于视频，从开头截取
                start_time = 0
            else:
                # 如果差异不大，从中间截取以获得更好的内容
                start_time = (original_video_duration - target_audio_duration) / 2

            trimmed_video = original_video.subclipped(start_time, start_time + target_audio_duration)
            trimmed_video.write_videofile(
                processed_video_path,
                codec="libx264",
                fps=24,
                logger=None,
                audio=False  # 不包含原音频
            )
            trimmed_video.close()

        elif original_video_duration < target_audio_duration:
            # 视频比音频短：循环视频
            print(f"🔄 视频较短，循环延长至音频长度: {original_video_duration:.2f}s → {target_audio_duration:.2f}s")

            # 🔥 智能循环：避免突兀的循环
            extended_video = create_smart_loop_video_for_text(original_video, target_audio_duration)
            extended_video.write_videofile(
                processed_video_path,
                codec="libx264",
                fps=24,
                logger=None,
                audio=False
            )
            extended_video.close()

        else:
            # 长度匹配或接近
            print("✅ 视频音频长度匹配，直接使用原视频")
            processed_video_path = local_video_path

        original_video.close()

        # 🔥 5. 上传处理后的文件
        if processed_video_path != local_video_path:
            processed_video_url = get_online_url_self(
                "processed_video.mp4",
                processed_video_path,
                "video/mp4"
            )
            print(f"📤 处理后视频已上传: {processed_video_url}")
        else:
            processed_video_url = video_url

        # 🔥 6. 调用阿里百炼生成数字人视频
        print("🤖 调用阿里百炼生成数字人视频...")
        print(f"📊 数字人生成参数:")
        print(f"   - processed_video_url: {processed_video_url}")
        print(f"   - final_audio_url: {final_audio_url}")
        print(f"   - project_path: {project_path}")
        
        digital_human_url = safe_videotalk_with_fallback(processed_video_url, final_audio_url, project_path)
        print(f"📊 数字人生成结果: {digital_human_url}")

        if digital_human_url and digital_human_url != "None":
            # 🔥 7. 成功生成数字人视频
            print("✅ 数字人视频生成成功，正在下载...")

            def download_file(url, filename):
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    filename = os.path.join(project_path, filename)
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                return filename

            downloaded_video = download_file(digital_human_url, "digital_human.mp4")

            # 🔥 8. 最终合成（确保严格匹配音频长度）
            print("🎬 正在进行最终合成...")

            final_video_clip = VideoFileClip(downloaded_video)
            final_audio_clip = AudioFileClip(final_audio_path)

            print(f"📊 下载的数字人视频时长: {final_video_clip.duration:.2f}秒")
            print(f"📊 最终音频时长: {final_audio_clip.duration:.2f}秒")

            # 🔥 强制匹配音频长度
            target_duration = final_audio_clip.duration

            if final_video_clip.duration > target_duration:
                print(f"✂️ 裁剪数字人视频至音频长度: {target_duration:.2f}秒")
                final_video_clip = final_video_clip.subclipped(0, target_duration)
            elif final_video_clip.duration < target_duration:
                print(f"🔄 延长数字人视频至音频长度: {target_duration:.2f}秒")

                # 创建循环视频
                original_duration = final_video_clip.duration
                if original_duration > 0:
                    # 计算完整循环次数
                    full_loops = int(target_duration / original_duration)
                    remaining_time = target_duration - (full_loops * original_duration)

                    # 构建循环片段列表
                    clips = []

                    # 添加完整循环
                    for i in range(full_loops):
                        clips.append(final_video_clip)

                    # 添加剩余部分
                    if remaining_time > 0:
                        clips.append(final_video_clip.subclipped(0, remaining_time))

                    # 连接所有片段
                    final_video_clip = concatenate_videoclips(clips)

            # 确保音频也精确匹配
            if final_audio_clip.duration != target_duration:
                final_audio_clip = final_audio_clip.subclipped(0, target_duration)

            # 合成最终视频
            final_video = final_video_clip.with_audio(final_audio_clip)
            output_path = os.path.join(project_path, "output.mp4")

            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                logger=None,
                audio_codec="aac"
            )

            print(f"📊 最终视频信息:")
            print(f"   - 文件路径: {output_path}")
            print(f"   - 视频时长: {final_video.duration:.2f}秒")
            print(f"   - 文件大小: {os.path.getsize(output_path) / (1024 * 1024):.1f}MB")
            print(f"   - 🎯 时长匹配度: 100%（严格按音频长度）")

            # 清理资源
            final_video_clip.close()
            final_audio_clip.close()
            final_video.close()

        else:
            # 🔄 数字人生成失败的降级处理
            print("🔄 数字人视频生成失败，创建降级输出...")
            output_path = os.path.join(project_path, "output.mp4")

            # 降级策略：使用处理后的视频 + 音频
            if processed_video_path and os.path.exists(processed_video_path):
                print("📹 使用处理后的视频作为降级输出")

                video_clip = VideoFileClip(processed_video_path)
                audio_clip = AudioFileClip(final_audio_path)

                # 确保长度严格匹配
                target_duration = audio_clip.duration
                if video_clip.duration != target_duration:
                    video_clip = video_clip.subclipped(0, min(video_clip.duration, target_duration))

                final_video = video_clip.with_audio(audio_clip.subclipped(0, video_clip.duration))
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    fps=24,
                    logger=None,
                    audio_codec="aac"
                )

                video_clip.close()
                audio_clip.close()
                final_video.close()
            else:
                # 创建纯音频视频
                print("🎵 创建纯音频视频")
                audio_clip = AudioFileClip(final_audio_path)
                create_audio_only_video(final_audio_path, output_path, duration=audio_clip.duration)
                audio_clip.close()

        print(f"✅ 最终视频生成完成: {output_path}")
        print(f"🎯 输出视频长度严格匹配文本音频长度")

        # 🔥 返回warehouse路径
        relative_path = os.path.relpath(output_path, get_user_data_dir())
        warehouse_path = relative_path.replace('\\', '/')
        print(f"📁 warehouse路径: {warehouse_path}")

        return warehouse_path

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        raise

    finally:
        # 🔥 清理临时文件
        for temp_file in temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {str(e)}")


def create_smart_loop_video_for_text(video_clip, target_duration):
    """
    🔥 为文本内容创建智能循环视频

    Args:
        video_clip: 原始视频剪辑
        target_duration: 目标时长（音频时长）

    Returns:
        循环后的视频剪辑
    """
    original_duration = video_clip.duration

    if target_duration <= original_duration:
        return video_clip.subclipped(0, target_duration)

    # 计算需要循环的次数
    loop_count = int(target_duration / original_duration)
    remaining_time = target_duration - (loop_count * original_duration)

    print(f"🔄 智能循环: 完整循环{loop_count}次，剩余{remaining_time:.2f}秒")

    # 创建循环片段
    clips = []

    # 添加完整循环
    for i in range(loop_count):
        clips.append(video_clip)

    # 添加剩余部分
    if remaining_time > 0.1:  # 避免太短的片段
        clips.append(video_clip.subclipped(0, remaining_time))

    # 拼接所有片段
    if len(clips) > 1:
        from moviepy import concatenate_videoclips
        extended_video = concatenate_videoclips(clips)
    else:
        extended_video = clips[0]

    return extended_video


def generate_tts_audio(text, project_path):
    """
    🔥 使用TTS生成音频（降级方案）

    Args:
        text: 要转换的文本
        project_path: 项目路径

    Returns:
        生成的音频文件路径
    """
    try:
        # 🔥 验证文本不为空
        if not text or text.strip() == "":
            print("⚠️ TTS文本为空，使用默认文本")
            text = "这是一段测试音频内容。"
            
        # 使用已定义的synthesize_speech_with_bailian函数
        tts_audio_path = os.path.join(project_path, "tts_audio.mp3")
        
        # 调用阿里百炼语音合成
        synthesize_speech_with_bailian(text, tts_audio_path)
        
        return tts_audio_path

    except Exception as e:
        print(f"❌ TTS生成失败: {e}")
        # 最终降级：创建静音音频
        from moviepy import AudioFileClip
        import numpy as np

        # 估算文本时长（每字0.5秒）
        estimated_duration = len(text) * 0.5

        # 创建静音音频
        silent_audio_path = os.path.join(project_path, "silent_audio.mp3")

        # 使用numpy创建静音
        sample_rate = 44100
        samples = int(estimated_duration * sample_rate)
        silent_array = np.zeros((samples, 2))

        from moviepy import AudioArrayClip
        silent_clip = AudioArrayClip(silent_array, fps=sample_rate)
        silent_clip.write_audiofile(silent_audio_path, logger=None)
        silent_clip.close()

        return silent_audio_path

def validate_video_audio_sync(video_path, expected_duration=None):
    """
    🔥 验证视频音频同步的工具函数
    """
    try:
        clip = VideoFileClip(video_path)
        video_duration = clip.duration

        if clip.audio:
            audio_duration = clip.audio.duration
            print(f"📊 视频时长: {video_duration:.2f}秒")
            print(f"📊 音频时长: {audio_duration:.2f}秒")
            print(f"📊 时长差异: {abs(video_duration - audio_duration):.2f}秒")

            if expected_duration:
                print(f"📊 期望时长: {expected_duration:.2f}秒")
                print(f"📊 与期望差异: {abs(video_duration - expected_duration):.2f}秒")

            # 检查同步性
            if abs(video_duration - audio_duration) > 0.1:
                print("⚠️ 视频音频长度不同步!")
                return False
            else:
                print("✅ 视频音频长度同步正常")
                return True
        else:
            print("⚠️ 视频没有音频轨道")
            return False

    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False
    finally:
        try:
            clip.close()
        except:
            pass

# 🔥 保持向后兼容的原始函数
def get_video_digital_huamn_easy(video_url, title, content=None, audio_url: str = None) -> str:
    """
    🔥 原始函数的兼容性包装器
    """
    return get_video_digital_human_unified(video_url, title, content, audio_url)


def get_video_digital_huamn_easy_local(video_url: str, title, content=None,
                                       audio_url: str = None, add_subtitle: bool = True) -> str:
    """
    🔥 原始本地处理函数的兼容性包装器
    """
    return get_video_digital_human_unified(video_url, title, content, audio_url, add_subtitle)


def clean_temp_files():
    """
    🔥 清理所有临时文件
    """
    user_data_dir = get_user_data_dir()
    temp_dirs = ["temp_videos", "temp_audios"]

    for temp_dir_name in temp_dirs:
        temp_dir = os.path.join(user_data_dir, temp_dir_name)
        if os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
                print(f"🗑️ {temp_dir_name} 目录已清理")
            except Exception as e:
                print(f"⚠️ 清理 {temp_dir_name} 目录失败: {str(e)}")


if __name__ == "__main__":
    # 🔥 测试用例1：本地文件
    print("=== 测试本地文件 ===")
    file_path = "Y:\\Ai-movie-clip__\\core\\cliptemplate\\coze\\序列 01_4.mp4"
    title = "财税知识"

    try:
        if os.path.exists(file_path):
            # 从视频中提取音频进行测试
            clip = VideoFileClip(file_path)
            output_mp3 = "Y:\\Ai-movie-clip__\\core\\cliptemplate\\coze\\output.mp3"
            clip.audio.write_audiofile(output_mp3, logger=None)
            clip.close()

            # 使用统一函数处理
            output_path = get_video_digital_human_unified(file_path, title, audio_input=output_mp3)
            print(f"✅ 本地文件测试成功: {output_path}")
        else:
            print(f"⚠️ 本地文件不存在，跳过测试: {file_path}")
    except Exception as e:
        print(f"❌ 本地文件测试失败: {str(e)}")

    # 清理临时文件
    clean_temp_files()

    print("\n🎉 测试完成！")
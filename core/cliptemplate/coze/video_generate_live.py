import os
import random
import re
import tempfile
import time
import json
from urllib import request
from datetime import datetime
from urllib.parse import urlparse

import cv2
import numpy as np
import torch
import whisper
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
import oss2
import requests
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from http import HTTPStatus

# 导入数字人生成函数
try:
    from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_human_unified
except ImportError:
    print("⚠️ 数字人模块导入失败，将跳过数字人生成功能")


    def get_video_digital_human_unified(*args, **kwargs):
        return None

# ============ 配置信息 ============
# 从环境变量读取配置
ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', 'YOUR_ACCESS_KEY_ID')
ACCESS_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', 'YOUR_ACCESS_SECRET')
OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'https://oss-cn-hangzhou.aliyuncs.com').replace('https://', '')
BUCKET_NAME = os.getenv('OSS_BUCKET_NAME', 'lan8-e-business')
VIDEO_OSS_FOLDER = 'agent/resource/video/'
ADS_OSS_FOLDER = 'ads/'
OUTPUT_OSS_FOLDER = 'agent/resource'

# 百炼平台配置
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-a48a1d84e015410292d07021f60b9acb')

# ============ 本地临时目录 ============
LOCAL_DIR = './temp/'
os.makedirs(LOCAL_DIR, exist_ok=True)

# 全局变量，用于缓存模型
_whisper_model = None

# ============ 初始化 OSS ============
auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, BUCKET_NAME)


# ============ 工具函数 ============

def list_oss_videos():
    """列出OSS中的所有视频文件"""
    try:
        video_files = []
        print(f"🔍 扫描OSS目录: {VIDEO_OSS_FOLDER}")

        for obj in bucket.list_objects(VIDEO_OSS_FOLDER).object_list:
            if obj.key.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_files.append(obj.key)
                print(f"  找到视频: {obj.key}")

        if not video_files:
            print(f"⚠️ 在 {VIDEO_OSS_FOLDER} 中没有找到视频文件")
            print("🔍 尝试扫描根目录...")
            for obj in bucket.list_objects().object_list:
                if obj.key.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    video_files.append(obj.key)
                    print(f"  根目录找到视频: {obj.key}")

        return video_files
    except Exception as e:
        print(f"❌ 列出视频文件失败: {str(e)}")
        return []


def format_size(bytes_size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f}TB"


def download_from_oss(oss_path, local_path):
    """OSS下载函数"""
    try:
        bucket.get_object_to_file(oss_path, local_path)
        print(f"✅ 下载成功 {oss_path} -> {local_path}")
        return True
    except oss2.exceptions.NoSuchKey:
        print(f"❌ OSS文件不存在: {oss_path}")
        return False
    except Exception as e:
        print(f"❌ 下载失败 {oss_path}: {str(e)}")
        return False


def load_whisper_model(model_name="base"):
    """加载Whisper模型，支持模型缓存"""
    global _whisper_model

    try:
        if _whisper_model is None:
            print(f"🤖 正在加载Whisper模型: {model_name}")

            # 检查CUDA是否可用
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"📱 使用设备: {device}")

            # 加载模型
            _whisper_model = whisper.load_model(model_name, device=device)
            print(f"✅ Whisper模型加载成功: {model_name}")

        return _whisper_model
    except Exception as e:
        print(f"❌ Whisper模型加载失败: {str(e)}")
        return None

def upload_to_oss(local_path, oss_path):
    """OSS上传函数"""
    try:
        bucket.put_object_from_file(oss_path, local_path)
        print(f"✅ 上传成功 {local_path} -> {oss_path}")
        return True
    except Exception as e:
        print(f"❌ 上传失败 {local_path}: {str(e)}")
        return False


def verify_oss_upload(oss_path):
    """验证OSS文件是否上传成功并返回完整URL"""
    try:
        # 获取文件信息
        metadata = bucket.get_object_meta(oss_path)
        file_size = metadata.content_length
        
        # 生成完整的访问URL
        full_url = f"https://{BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}"
        
        print(f"📊 OSS文件信息: {oss_path} ({format_size(file_size)})")
        print(f"🔗 完整访问URL: {full_url}")
        return True
    except Exception as e:
        print(f"❌ OSS文件验证失败: {e}")
        return False


def parse_oss_url(url_or_path):
    """
    解析OSS URL或路径，返回OSS内部路径

    Args:
        url_or_path: 可以是以下几种格式：
            - 完整URL: "https://bucket.endpoint/path/file.mp4"
            - OSS路径: "path/file.mp4"
            - 带签名URL: "https://bucket.endpoint/path/file.mp4?Expires=..."

    Returns:
        str: OSS内部路径，如 "agent/resource/video/my_video.mp4.mkv"
    """
    try:
        # 如果是完整的HTTP/HTTPS URL
        if url_or_path.startswith(('http://', 'https://')):
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url_or_path)

            # 提取路径部分，去掉开头的 '/'
            oss_path = parsed.path.lstrip('/')

            print(f"🔄 URL解析: {url_or_path} -> {oss_path}")
            return oss_path
        else:
            # 已经是OSS内部路径
            print(f"✅ 直接使用OSS路径: {url_or_path}")
            return url_or_path

    except Exception as e:
        print(f"❌ URL解析失败: {str(e)}")
        print(f"   原始输入: {url_or_path}")
        return url_or_path


def get_video_duration(video_path):
    """获取视频时长"""
    video = VideoFileClip(video_path)
    duration = video.duration
    video.close()
    return duration

def cleanup_oss_file(oss_path):
    """清理临时OSS文件"""
    try:
        bucket.delete_object(oss_path)
        print(f"🗑️ 清理OSS临时文件: {oss_path}")
    except Exception as e:
        print(f"⚠️ 清理OSS文件失败: {str(e)}")


def whisper_asr(audio_path, model_name="base", language="zh"):
    """
    使用Whisper进行语音识别

    参数:
    - audio_path: 音频文件路径
    - model_name: Whisper模型名称 (tiny, base, small, medium, large, large-v2, large-v3)
    - language: 目标语言 ('zh'中文, 'en'英文, None自动检测)

    返回:
    - 识别的文本内容
    """
    try:
        print(f"🎙️ 开始使用Whisper识别音频: {audio_path}")

        # 检查音频文件是否存在且有效
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            print("⚠️ 音频文件不存在或为空，使用默认文本")
            return generate_fallback_text(audio_path)

        # 加载Whisper模型
        model = load_whisper_model(model_name)
        if model is None:
            print("⚠️ 模型加载失败，使用备用方案")
            return generate_fallback_text(audio_path)

        # 方法1: 直接使用Whisper识别
        try:
            print("🔄 正在进行Whisper语音识别...")

            # 设置识别参数
            options = {
                "language": language if language != "auto" else None,
                "task": "transcribe",  # 转录任务
                "fp16": torch.cuda.is_available(),  # 如果有GPU则使用fp16加速
            }

            # 执行识别
            result = model.transcribe(audio_path, **options)

            # 提取文本
            text = result.get("text", "").strip()

            if text:
                print(f"✅ Whisper识别成功: {text}")
                print(f"🌍 检测到的语言: {result.get('language', 'unknown')}")
                return text
            else:
                print("⚠️ Whisper识别返回空文本")

        except Exception as e1:
            print(f"⚠️ Whisper识别失败: {str(e1)}")

        # 方法2: 预处理音频后重试
        try:
            print("🔄 尝试预处理音频后重新识别...")

            # 转换音频格式
            processed_audio = preprocess_audio(audio_path)
            if processed_audio and processed_audio != audio_path:
                result = model.transcribe(processed_audio, **options)
                text = result.get("text", "").strip()

                if text:
                    print(f"✅ 预处理后Whisper识别成功: {text}")
                    # 清理临时文件
                    try:
                        os.remove(processed_audio)
                    except:
                        pass
                    return text

                # 清理临时文件
                try:
                    os.remove(processed_audio)
                except:
                    pass

        except Exception as e2:
            print(f"⚠️ 预处理后识别失败: {str(e2)}")

        # 方法3: 尝试不同的模型参数
        try:
            print("🔄 尝试调整参数重新识别...")

            # 更宽松的参数
            options_relaxed = {
                "language": None,  # 自动检测语言
                "task": "transcribe",
                "fp16": False,  # 禁用fp16
                "temperature": 0.0,  # 降低随机性
                "best_of": 1,
                "beam_size": 1,
            }

            result = model.transcribe(audio_path, **options_relaxed)
            text = result.get("text", "").strip()

            if text:
                print(f"✅ 调整参数后识别成功: {text}")
                return text

        except Exception as e3:
            print(f"⚠️ 调整参数后识别失败: {str(e3)}")

        # 方法4: 使用更小的模型重试
        if model_name != "tiny":
            try:
                print("🔄 尝试使用tiny模型...")
                tiny_model = whisper.load_model("tiny")
                result = tiny_model.transcribe(audio_path, language=language)
                text = result.get("text", "").strip()

                if text:
                    print(f"✅ tiny模型识别成功: {text}")
                    return text

            except Exception as e4:
                print(f"⚠️ tiny模型识别失败: {str(e4)}")

        # 备用方案：根据音频长度生成文本
        print("🔄 使用备用文本生成方案...")
        return generate_fallback_text(audio_path)

    except Exception as e:
        print(f"❌ Whisper识别异常: {str(e)}")
        return generate_fallback_text(audio_path)


def preprocess_audio(audio_path):
    """预处理音频文件，转换为Whisper友好的格式"""
    try:
        print("🔧 预处理音频文件...")

        # 加载音频
        audio_clip = AudioFileClip(audio_path)

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # 转换为16kHz单声道WAV
        audio_clip.audio.write_audiofile(
            temp_path,
            fps=16000,  # 16kHz采样率
            nbytes=2,  # 16bit
            codec='pcm_s16le',  # PCM编码
            verbose=False,
            logger=None
        )

        audio_clip.close()

        print(f"✅ 音频预处理完成: {temp_path}")
        return temp_path

    except Exception as e:
        print(f"⚠️ 音频预处理失败: {str(e)}")
        return audio_path


def generate_fallback_text(audio_path):
    """根据音频长度生成备用文本"""
    try:
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()

        # 根据音频长度生成相应的文本
        if duration < 3:
            text = "这是一段短音频内容。"
        elif duration < 10:
            text = "这是一段测试音频的内容，用于演示数字人视频生成功能。"
        elif duration < 30:
            text = "这是一段中等长度的音频内容，包含了丰富的语音信息，适合用于数字人视频的生成和处理。"
        else:
            text = "这是一段较长的音频内容，包含了丰富的语音信息，适合用于数字人视频的生成和处理。我们将使用这段音频来创建高质量的数字人视频效果，展现出自然流畅的语音表达。"

        print(f"✅ 使用备用方案生成文本 (时长{duration:.1f}s): {text}")
        return text

    except Exception as e:
        print(f"⚠️ 备用方案失败: {str(e)}")
        return "这是一段测试音频的内容，用于演示数字人视频生成功能。"


def get_available_whisper_models():
    """获取可用的Whisper模型列表"""
    return {
        "tiny": "最快，准确度较低，39MB",
        "base": "平衡速度和准确度，74MB",
        "small": "较好准确度，244MB",
        "medium": "更好准确度，769MB",
        "large": "最佳准确度，1550MB",
        "large-v2": "改进版large模型，1550MB",
        "large-v3": "最新版large模型，1550MB"
    }


def clear_whisper_model():
    """清理模型缓存，释放内存"""
    global _whisper_model
    if _whisper_model is not None:
        del _whisper_model
        _whisper_model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("🗑️ 已清理Whisper模型缓存")

# ============ 内存优化的 TTS ============
def cosyvoice_tts_memory_optimized(text, output_audio, min_duration=5):
    """内存优化的CosyVoice TTS"""
    try:
        print(f"🎵 开始语音合成: {text[:50]}...")

        # 限制文本长度，避免内存溢出
        if len(text) > 200:
            text = text[:200] + "..."
            print(f"🔄 文本过长，截取前200字符")
        elif len(text) < 20:
            text = text + "。" + text
            print(f"🔄 文本较短，适当扩展")

        # 创建语音合成器
        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v2",
            voice="longxiaochun_v2"
        )

        # 进行语音合成
        audio_data = synthesizer.call(text)

        # 保存音频文件
        with open(output_audio, 'wb') as f:
            f.write(audio_data)

        # 检查音频长度
        try:
            from moviepy import AudioFileClip
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            audio_clip.close()

            print(f"✅ 语音合成成功: {output_audio} (时长: {duration:.2f}s)")
            return output_audio

        except Exception as check_e:
            print(f"⚠️ 音频长度检查失败: {check_e}")
            return output_audio

    except Exception as e:
        print(f"❌ 语音合成失败: {str(e)}")
        return None


# ============ 内存优化的视频截取 ============
def random_clip_memory_safe_with_info(video_path, output_path, min_len=30, max_len=120):
    """
    内存安全的随机截取，返回截取信息

    Returns:
        tuple: (start_time, end_time) 截取的开始和结束时间
    """
    try:
        video = VideoFileClip(video_path)
        duration = video.duration
        print(f"📹 原视频时长: {duration:.2f}s")

        # 限制最大截取长度，避免内存问题
        max_safe_len = min(max_len, 60)  # 最多60秒

        if duration < min_len:
            print(f"⚠️ 视频太短，使用完整视频")
            clip_duration = duration
            start_time = 0
        else:
            clip_duration = min(random.randint(min_len, max_safe_len), duration)
            start_time = random.uniform(0, max(0, duration - clip_duration))

        end_time = start_time + clip_duration
        print(f"🎬 截取片段: {start_time:.2f}s - {end_time:.2f}s")

        if start_time == 0 and clip_duration == duration:
            # 直接使用完整视频
            video.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                  temp_audiofile=f'{output_path}.temp-audio.m4a')
        else:
            # 截取片段
            subclip = video.subclipped(start_time, end_time)
            subclip.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                    temp_audiofile=f'{output_path}.temp-audio.m4a')
            subclip.close()

        video.close()
        return start_time, end_time

    except Exception as e:
        print(f"❌ 视频截取失败: {str(e)}")
        raise


def replace_video_audio_safe(video_path, new_audio_path, output_path):
    """安全的视频音频替换函数"""
    try:
        video = VideoFileClip(video_path)

        if new_audio_path and os.path.exists(new_audio_path) and os.path.getsize(new_audio_path) > 0:
            try:
                new_audio_clip = AudioFileClip(new_audio_path)
                # 使用正确的方法名
                try:
                    final_video = video.set_audio(new_audio_clip)
                except AttributeError:
                    # 如果set_audio不存在，尝试with_audio
                    final_video = video.with_audio(new_audio_clip)

                final_video.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                            temp_audiofile=f'{output_path}.temp-audio.m4a')
                new_audio_clip.close()
                final_video.close()
                print(f"✅ 音频替换成功")
                return True
            except Exception as e:
                print(f"⚠️ 音频替换失败: {e}")
                # 如果音频替换失败，直接复制原视频
                video.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                      temp_audiofile=f'{output_path}.temp-audio.m4a')
                return False
        else:
            print("⚠️ 新音频文件无效，使用原音频")
            video.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                  temp_audiofile=f'{output_path}.temp-audio.m4a')
            return False

        video.close()
        return True

    except Exception as e:
        print(f"❌ 视频音频替换失败: {str(e)}")
        return False


# ============ 数字人相关函数 ============
def find_digital_human_output(digital_human_result):
    """
    查找数字人生成的输出文件

    Args:
        digital_human_result: 数字人生成函数返回的结果

    Returns:
        str or None: 找到的文件路径，如果没找到返回None
    """
    if not digital_human_result:
        return None

    print(f"🔍 查找数字人输出文件...")

    # 可能的路径列表
    possible_paths = []

    # 如果返回的是字符串路径
    if isinstance(digital_human_result, str):
        possible_paths.extend([
            digital_human_result,  # 直接路径
            os.path.abspath(digital_human_result),  # 绝对路径
        ])

        # 检查是否是相对路径，尝试在不同目录查找
        if not os.path.isabs(digital_human_result):
            possible_paths.extend([
                os.path.join("./", digital_human_result),
                os.path.join("./temp/", digital_human_result),
                os.path.join("./ikun/", digital_human_result),
            ])

    # 如果有config模块，也尝试用户数据目录
    try:
        import live_config
        user_data_dir = live_config.get_user_data_dir()
        if isinstance(digital_human_result, str):
            possible_paths.extend([
                os.path.join(user_data_dir, digital_human_result.replace('/', os.path.sep)),
                os.path.join(user_data_dir, os.path.basename(digital_human_result))
            ])
    except:
        pass

    # 查找数字人输出目录中的最新文件
    try:
        ikun_dir = "./ikun"
        if os.path.exists(ikun_dir):
            # 查找projects目录下的最新项目
            projects_dir = os.path.join(ikun_dir, "projects")
            if os.path.exists(projects_dir):
                project_dirs = [d for d in os.listdir(projects_dir)
                                if os.path.isdir(os.path.join(projects_dir, d))]

                if project_dirs:
                    # 按修改时间排序，获取最新的项目目录
                    project_dirs.sort(key=lambda x: os.path.getmtime(os.path.join(projects_dir, x)), reverse=True)
                    latest_project = project_dirs[0]
                    latest_project_path = os.path.join(projects_dir, latest_project)

                    # 查找output.mp4文件
                    output_file = os.path.join(latest_project_path, "output.mp4")
                    possible_paths.append(output_file)

                    print(f"🔍 检查最新项目目录: {latest_project_path}")
    except Exception as e:
        print(f"⚠️ 查找项目目录失败: {e}")

    # 逐一检查路径
    for path in possible_paths:
        print(f"🔍 检查路径: {path}")
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            print(f"✅ 找到数字人视频: {path} ({format_size(file_size)})")
            return path

    print(f"❌ 未找到数字人视频文件")
    print(f"📋 尝试的路径:")
    for path in possible_paths:
        print(f"  - {path}")

    return None


def generate_digital_human_video_safe(video_url, text, audio_path=None):
    """安全的数字人视频生成"""
    try:
        print(f"🤖 生成数字人视频...")
        print(f"📹 视频: {video_url}")
        print(f"📝 文本: {text[:50]}...")
        print(f"🎵 音频: {audio_path}")

        if not os.path.exists(video_url):
            print(f"❌ 视频文件不存在: {video_url}")
            return None

        # 调用数字人生成函数
        print(f"🔄 调用数字人生成函数...")
        print(f"📊 参数详情:")
        print(f"   - video_input: {video_url}")
        print(f"   - title: {text[:30]}")  # 修改日志显示
        print(f"   - content: {text}")
        print(f"   - audio_input: {audio_path}")
        
        result = get_video_digital_human_unified(
            video_url=video_url,
            title=text[:30],  # 修改为正确的参数名
            content=text,
            audio_input=audio_path
        )

        print(f"📊 数字人生成函数返回结果: {result}")
        print(f"📊 返回结果类型: {type(result)}")
        
        # 查找实际的输出文件
        digital_human_output = find_digital_human_output(result)
        print(f"📁 数字人输出文件: {digital_human_output}")
        
        return digital_human_output

    except Exception as e:
        print(f"❌ 数字人生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# ============ 视频片段替换功能 ============
def replace_video_segment_safe(original_video_path, processed_segment_path, start_time, end_time, output_path):
    """
    安全的视频片段替换函数，避免资源管理问题

    Args:
        original_video_path: 原始完整视频路径
        processed_segment_path: 处理后的片段路径
        start_time: 片段在原视频中的开始时间（秒）
        end_time: 片段在原视频中的结束时间（秒）
        output_path: 输出的新视频路径

    Returns:
        bool: 是否成功替换
    """
    original_video = None
    processed_segment = None
    final_video = None
    video_parts = []

    try:
        print(f"🔄 开始替换视频片段...")
        print(f"📹 原视频: {original_video_path}")
        print(f"🎬 处理片段: {processed_segment_path}")
        print(f"⏰ 替换时间段: {start_time:.2f}s - {end_time:.2f}s")

        # 验证文件存在
        if not os.path.exists(original_video_path):
            print(f"❌ 原视频文件不存在: {original_video_path}")
            return False

        if not os.path.exists(processed_segment_path):
            print(f"❌ 处理片段文件不存在: {processed_segment_path}")
            return False

        # 加载原视频
        original_video = VideoFileClip(original_video_path)
        original_duration = original_video.duration

        # 加载处理后的片段
        processed_segment = VideoFileClip(processed_segment_path)
        segment_duration = processed_segment.duration

        print(f"📊 原视频时长: {original_duration:.2f}s")
        print(f"📊 处理片段时长: {segment_duration:.2f}s")

        # 验证时间范围
        if start_time < 0 or end_time > original_duration or start_time >= end_time:
            print(f"❌ 时间范围无效")
            return False

        # 创建视频片段列表
        video_parts = []

        # 第一部分：开始到替换点之前
        if start_time > 0:
            part1 = original_video.subclipped(0, start_time)
            video_parts.append(part1)
            print(f"✅ 添加前段: 0s - {start_time:.2f}s")

        # 第二部分：处理后的片段
        video_parts.append(processed_segment)
        print(f"✅ 添加处理片段: {segment_duration:.2f}s")

        # 第三部分：替换点之后到结尾
        if end_time < original_duration:
            part3 = original_video.subclipped(end_time, original_duration)
            video_parts.append(part3)
            print(f"✅ 添加后段: {end_time:.2f}s - {original_duration:.2f}s")

        # 合并所有部分
        print(f"🔧 开始合并 {len(video_parts)} 个视频片段...")
        for i, part in enumerate(video_parts):
            try:
                duration = part.duration
                print(f"  片段 {i}: {duration:.2f}秒")
            except Exception as e:
                print(f"  片段 {i}: 无法获取时长 - {e}")

        if len(video_parts) > 1:
            print(f"🔗 使用 concatenate_videoclips 合并视频...")
            final_video = concatenate_videoclips(video_parts, method="compose")
        else:
            print(f"📹 只有一个片段，直接使用...")
            final_video = video_parts[0]

        # 检查最终视频时长
        try:
            final_duration = final_video.duration
            print(f"📊 合并后视频时长: {final_duration:.2f}秒")
        except Exception as e:
            print(f"⚠️ 无法获取合并后视频时长: {e}")

        # 输出最终视频
        print(f"💾 开始写入最终视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=f'{output_path}.temp-audio.m4a',
            remove_temp=True,
            logger='bar'  # 显示进度条
        )

        # 验证输出文件
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            # 重新检查输出文件的实际时长
            try:
                verification_video = VideoFileClip(output_path)
                actual_duration = verification_video.duration
                verification_video.close()
                print(f"✅ 输出文件验证:")
                print(f"   - 文件大小: {format_size(file_size)}")
                print(f"   - 实际时长: {actual_duration:.2f}秒")
            except Exception as e:
                print(f"⚠️ 无法验证输出文件: {e}")
        else:
            print(f"❌ 输出文件不存在: {output_path}")
            return False

        print(f"✅ 视频片段替换成功: {output_path}")
        return True

    except Exception as e:
        print(f"❌ 视频片段替换失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 安全清理资源 - 使用 try-except 包装每个清理操作
        cleanup_objects = [
            ("final_video", final_video),
            ("processed_segment", processed_segment),
            ("original_video", original_video)
        ]

        for name, obj in cleanup_objects:
            if obj is not None:
                try:
                    obj.close()
                    print(f"🗑️ 清理 {name}")
                except Exception as e:
                    print(f"⚠️ {name} 清理失败: {e}")

        # 清理视频片段
        for i, part in enumerate(video_parts):
            try:
                # 只清理子片段，不清理原始的processed_segment
                if part is not processed_segment:
                    part.close()
                    print(f"🗑️ 清理片段 {i}")
            except Exception as e:
                print(f"⚠️ 片段 {i} 清理失败: {e}")


def download_video_http(video_url, local_path, timeout=300, chunk_size=8192):
    """
    通用HTTP视频下载函数

    Args:
        video_url: 视频URL
        local_path: 本地保存路径
        timeout: 超时时间（秒）
        chunk_size: 下载块大小

    Returns:
        bool: 是否下载成功
    """
    try:
        print(f"🌐 HTTP下载: {video_url}")

        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',  # 避免压缩，确保文件完整性
            'Connection': 'keep-alive'
        }

        # 发送HTTP请求
        print(f"📡 发送HTTP请求...")
        response = requests.get(video_url, headers=headers, stream=True, timeout=timeout)

        # 检查响应状态
        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            return False

        # 检查Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        if 'image' in content_type:
            print(f"❌ 检测到图片类型: {content_type}")
            print(f"   这不是一个视频文件")
            return False
            
        # 获取文件大小（如果可用）
        content_length = response.headers.get('Content-Length')
        if content_length:
            total_size = int(content_length)
            print(f"📊 文件大小: {format_size(total_size)}")
        else:
            total_size = None
            print(f"📊 文件大小: 未知")

        # 下载文件
        print(f"⬇️ 开始下载到: {local_path}")
        downloaded_size = 0

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # 过滤掉keep-alive的新块
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 显示进度（每10MB显示一次）
                    if downloaded_size % (10 * 1024 * 1024) == 0:
                        if total_size:
                            progress = (downloaded_size / total_size) * 100
                            print(
                                f"📥 下载进度: {format_size(downloaded_size)}/{format_size(total_size)} ({progress:.1f}%)")
                        else:
                            print(f"📥 已下载: {format_size(downloaded_size)}")

        # 验证下载结果
        if os.path.exists(local_path):
            final_size = os.path.getsize(local_path)
            print(f"✅ 下载完成: {format_size(final_size)}")

            # 检查文件大小是否匹配（如果有Content-Length）
            if total_size and final_size != total_size:
                print(f"⚠️ 文件大小不匹配: 期望{format_size(total_size)}，实际{format_size(final_size)}")
                # 但是不抛出错误，可能是服务器压缩等原因

            # 检查文件是否为空
            if final_size == 0:
                print(f"❌ 下载的文件为空")
                return False

            return True
        else:
            print(f"❌ 下载文件不存在")
            return False

    except requests.exceptions.Timeout:
        print(f"❌ 下载超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP请求异常: {e}")
        return False
    except Exception as e:
        print(f"❌ 下载异常: {e}")
        return False

# ============ 主要处理流程 ============
def process_single_video_by_url(video_url, tenant_id, id, custom_index=None, preserve_duration=False):
    """
    修改后的基于视频URL的处理流程 - 使用HTTP下载

    Args:
        video_url: 视频URL，支持任何HTTP/HTTPS链接
        custom_index: 自定义索引，用于文件命名
        preserve_duration: 是否保持原始视频时长，默认False
    """
    # 使用时间戳作为默认索引
    index = custom_index if custom_index is not None else int(time.time()) % 10000

    print(f"\n🤖 处理视频URL: {video_url}")
    print(f"   索引: {index}")

    # 记录片段信息
    segment_info = {}

    try:
        # 检查URL中的文件扩展名
        from urllib.parse import urlparse
        parsed_url = urlparse(video_url)
        url_path = parsed_url.path.lower()
        
        # 判断是否为图片文件
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        if any(url_path.endswith(ext) for ext in image_extensions):
            print(f"❌ 检测到图片文件而非视频: {url_path}")
            print(f"   跳过此文件")
            return None
            
        # Step 1: 直接使用HTTP下载视频
        original_video_local = os.path.join(LOCAL_DIR, f"original_{index}.mp4")
        if not download_video_http(video_url, original_video_local):
            print(f"❌ 视频下载失败")
            return None

        # Step 2: 始终进行随机截取
        clipped_video = os.path.join(LOCAL_DIR, f"clipped_{index}.mp4")

        # 随机截取模式
        start_time, end_time = random_clip_memory_safe_with_info(
            original_video_local, clipped_video, min_len=20, max_len=45
        )

        # 保存片段信息
        segment_info = {
            'start_time': start_time,
            'end_time': end_time,
            'original_video': original_video_local,
            'source_url': video_url,
            'preserve_duration': False
        }

        print(f"📝 记录片段信息: {start_time:.2f}s - {end_time:.2f}s")

        # Step 3: 提取音频
        audio_path = os.path.join(LOCAL_DIR, f"audio_{index}.wav")
        video = VideoFileClip(clipped_video)
        video.audio.write_audiofile(audio_path)
        video.close()

        # Step 4: ASR识别
        text = whisper_asr(audio_path)
        print(f"🎙️ 识别文本: {text}")

        # Step 5: 数字人应该使用原始音频，不需要TTS合成
        print(f"🎵 数字人使用原始音频: {audio_path}")

        # Step 6: 生成数字人视频（使用原始音频）
        processed_segment_path = None
        video_type = "original_clipped"

        print(f"🤖 开始生成数字人视频...")
        digital_human_path = generate_digital_human_video_safe(
            video_url=clipped_video,
            text=text,
            audio_path=audio_path  # 使用原始音频而不是TTS音频
        )

        if digital_human_path:
            processed_segment_path = digital_human_path
            video_type = "digital_human"
            print(f"✅ 数字人视频生成成功")
        else:
            # 数字人失败，直接使用原始视频（不需要TTS）
            processed_segment_path = clipped_video
            video_type = "original_clipped"
            print(f"⚠️ 数字人生成失败，使用原始截取片段")

        # Step 7: 始终进行片段替换，将处理后的片段替换回原视频
        final_upload_path = processed_segment_path  # 默认上传处理后的片段

        if processed_segment_path and segment_info:
            # 随机截取模式 - 需要片段替换
            final_video_path = os.path.join(LOCAL_DIR, f"final_{index}.mp4")

            print(f"🔄 尝试将处理片段替换回原视频...")
            print(f"📊 替换参数:")
            print(f"   - 原视频: {segment_info['original_video']}")
            print(f"   - 处理片段: {processed_segment_path}")
            print(f"   - 开始时间: {segment_info['start_time']:.2f}s")
            print(f"   - 结束时间: {segment_info['end_time']:.2f}s")
            print(f"   - 输出路径: {final_video_path}")

            replacement_success = replace_video_segment_safe(
                original_video_path=segment_info['original_video'],
                processed_segment_path=processed_segment_path,
                start_time=segment_info['start_time'],
                end_time=segment_info['end_time'],
                output_path=final_video_path
            )

            if replacement_success and os.path.exists(final_video_path):
                # 验证最终视频
                try:
                    final_check_video = VideoFileClip(final_video_path)
                    final_check_duration = final_check_video.duration
                    final_check_video.close()

                    print(f"✅ 片段替换成功!")
                    print(f"📊 最终视频统计:")
                    print(f"   - 原视频时长: {VideoFileClip(segment_info['original_video']).duration:.2f}s")
                    print(f"   - 最终视频时长: {final_check_duration:.2f}s")
                    print(f"   - 文件大小: {format_size(os.path.getsize(final_video_path))}")

                    final_upload_path = final_video_path
                    video_type = f"{video_type}_replaced"

                except Exception as verify_e:
                    print(f"⚠️ 最终视频验证失败: {verify_e}")
                    print(f"⚠️ 使用处理后的片段")
                    final_upload_path = processed_segment_path
            else:
                print(f"⚠️ 片段替换失败，使用处理后的片段")
                final_upload_path = processed_segment_path
        else:
            print(f"⚠️ 无法替换片段，使用处理后的片段")
            final_upload_path = processed_segment_path

        # Step 8: 上传到OSS并保存本地副本
        timestamp = int(time.time())

        # 从URL中提取文件名（不含扩展名）作为标识
        from urllib.parse import urlparse
        parsed_url = urlparse(video_url)
        video_name = os.path.splitext(os.path.basename(parsed_url.path))[0]

        # 如果无法从URL获取文件名，使用默认名称
        if not video_name:
            video_name = f"video_{index}"

        # 清理文件名，去除特殊字符
        video_name = re.sub(r'[^\w\-_]', '_', video_name)

        output_oss_path = f"{OUTPUT_OSS_FOLDER}{video_type}_{video_name}_{timestamp}.mp4"

        # 保存本地副本到warehouse目录
        warehouse_dir = "./ikun/outputs/"
        os.makedirs(warehouse_dir, exist_ok=True)
        local_warehouse_path = os.path.join(warehouse_dir, f"{video_type}_{video_name}_{timestamp}.mp4")

        if os.path.exists(final_upload_path):
            file_size = os.path.getsize(final_upload_path)
            print(f"📁 文件大小: {format_size(file_size)}")

            # 先复制到warehouse目录
            import shutil
            try:
                shutil.copy2(final_upload_path, local_warehouse_path)
                print(f"💾 本地副本保存: {local_warehouse_path}")
            except Exception as copy_e:
                print(f"⚠️ 保存本地副本失败: {copy_e}")

            # 然后上传到OSS
            if upload_to_oss(final_upload_path, output_oss_path):
                print(f"✅ 视频上传成功: {output_oss_path}")
                print(f"🎯 视频类型: {video_type}")
                headers = {
                    'tenant-id': tenant_id,
                    'Authorization': 'Bearer test1'
                }
                url = 'https://agent.cstlanbaai.com/gateway/admin-api/agent/task-video-edit/update'
                # 验证上传
                if verify_oss_upload(output_oss_path):
                    print(f"✅ OSS文件验证成功")
                    data = {
                        'status': 1,
                        'id': id,
                        'videoUrls': output_oss_path,
                        'localPath;': local_warehouse_path
                    }
                    print(f"请求data为{data}")
                    resp = requests.put(url, headers=headers, json=data)
                    print(resp.json())
                    print(resp.status_code)
                else:
                    data = {
                        'status': 2,
                        'id': id,
                        'output_oss_path': ''
                    }
                    resp = requests.put(url, headers=headers, data=data)
                    print(f"⚠️ OSS文件验证失败")

                # 返回处理结果信息
                result_info = {
                    'warehouse_path': f"outputs/{video_type}_{video_name}_{timestamp}.mp4",
                    'oss_path': output_oss_path,
                    'video_type': video_type,
                    'source_url': video_url,
                    'segment_info': segment_info,
                    'local_path': local_warehouse_path,
                    'recognized_text': text
                }

                print(f"📂 返回warehouse路径: {result_info['warehouse_path']}")
                return result_info
            else:
                print(f"❌ 视频上传失败")
                # 即使上传失败，也返回本地路径
                if os.path.exists(local_warehouse_path):
                    result_info = {
                        'warehouse_path': f"outputs/{video_type}_{video_name}_{timestamp}.mp4",
                        'oss_path': None,
                        'video_type': video_type,
                        'source_url': video_url,
                        'segment_info': segment_info,
                        'local_path': local_warehouse_path,
                        'recognized_text': text
                    }
                    return result_info
        else:
            print(f"❌ 要上传的文件不存在: {final_upload_path}")
            return None

    except Exception as e:
        print(f"❌ 处理视频失败: {str(e)}")
        import traceback
        traceback.print_exc()

        # 应急措施：至少上传原始截取的视频
        if 'clipped_video' in locals() and os.path.exists(clipped_video):
            emergency_timestamp = int(time.time())

            # 从URL中提取文件名
            from urllib.parse import urlparse
            parsed_url = urlparse(video_url)
            video_name = os.path.splitext(os.path.basename(parsed_url.path))[0]

            if not video_name:
                video_name = f"video_{index}"

            video_name = re.sub(r'[^\w\-_]', '_', video_name)

            emergency_oss_path = f"{OUTPUT_OSS_FOLDER}emergency_{video_name}_{emergency_timestamp}.mp4"
            emergency_warehouse_path = f"./ikun/outputs/emergency_{video_name}_{emergency_timestamp}.mp4"

            # 保存应急本地副本
            try:
                import shutil
                shutil.copy2(clipped_video, emergency_warehouse_path)
                print(f"💾 应急本地副本: {emergency_warehouse_path}")
            except Exception as copy_e:
                print(f"⚠️ 应急本地副本失败: {copy_e}")

            if upload_to_oss(clipped_video, emergency_oss_path):
                print(f"🚨 应急上传成功: {emergency_oss_path}")
                return {
                    'warehouse_path': f"outputs/emergency_{video_name}_{emergency_timestamp}.mp4",
                    'oss_path': emergency_oss_path,
                    'video_type': 'emergency',
                    'source_url': video_url,
                    'segment_info': segment_info,
                    'local_path': emergency_warehouse_path,
                    'recognized_text': None
                }

        return None

    finally:
        # 保留所有本地文件，仅打印保留信息
        print(f"💾 保留本地文件:")
        temp_files = [
            os.path.join(LOCAL_DIR, f"original_{index}.mp4"),
            os.path.join(LOCAL_DIR, f"clipped_{index}.mp4"),
            os.path.join(LOCAL_DIR, f"audio_{index}.wav"),
            os.path.join(LOCAL_DIR, f"new_audio_{index}.wav"),
            os.path.join(LOCAL_DIR, f"tts_enhanced_{index}.mp4"),
            os.path.join(LOCAL_DIR, f"final_{index}.mp4"),
        ]

        for temp_file in temp_files:
            if os.path.exists(temp_file):
                file_size = os.path.getsize(temp_file)
                print(f"  📁 {temp_file} ({format_size(file_size)})")

        # 也保留数字人生成的文件
        if 'processed_segment_path' in locals() and processed_segment_path:
            if os.path.exists(processed_segment_path) and 'ikun/projects' in processed_segment_path:
                file_size = os.path.getsize(processed_segment_path)
                print(f"  🤖 {processed_segment_path} ({format_size(file_size)})")

def process_videos_by_urls(video_urls):
    """
    基于视频URL列表的批量处理

    Args:
        video_urls: 视频URL列表，如:
            ["agent/resource/video/my_video.mp4.mkv", "agent/resource/video/another.mp4"]
            或者单个URL字符串

    Returns:
        list: 处理结果列表
    """
    # 支持单个URL或URL列表
    if isinstance(video_urls, str):
        video_urls = [video_urls]

    if not video_urls:
        print("❌ 没有提供视频URL")
        return []

    print(f"🤖 开始批量处理 {len(video_urls)} 个视频 (基于URL)")
    results = []

    for i, video_url in enumerate(video_urls):
        try:
            print(f"\n{'=' * 60}")
            print(f"🎬 处理第 {i + 1}/{len(video_urls)} 个视频")
            print(f"📹 视频URL: {video_url}")

            result = process_single_video_by_url(video_url, custom_index=i)
            if result:
                results.append(result)
                print(f"✅ 视频处理完成: {result['warehouse_path']}")
            else:
                print(f"⚠️ 视频处理失败")

            # 每个视频处理完后暂停
            if i < len(video_urls) - 1:  # 不是最后一个视频
                print(f"⏱️ 等待 3 秒后处理下一个视频...")
                time.sleep(3)

        except Exception as e:
            print(f"❌ 视频处理异常: {str(e)}")
            continue

    print(f"\n🎉 批量处理完成!")
    print(f"📊 成功处理 {len(results)} 个视频:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['warehouse_path']} (类型: {result['video_type']})")
        if result['recognized_text']:
            print(f"     识别文本: {result['recognized_text'][:50]}...")

    return results


# ============ 配置验证 ============
def validate_config():
    """验证配置"""
    print("🔍 验证配置...")

    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR, exist_ok=True)

    try:
        video_files = list_oss_videos()
        print(f"✅ 找到 {len(video_files)} 个视频文件")
        return True
    except Exception as e:
        print(f"⚠️ OSS连接失败: {e}")
        return False


def list_all_files(folder_path="", file_types=None, show_details=True):
    """
    列出OSS中的所有文件

    Args:
        folder_path: 指定文件夹路径，如 "outputs/" 或 "" (根目录)
        file_types: 文件类型过滤，如 ['.mp4', '.wav', '.jpg'] 或 None (所有文件)
        show_details: 是否显示详细信息（大小、修改时间等）
    """
    try:
        print(f"🔍 扫描路径: {'根目录' if not folder_path else folder_path}")

        files = []
        total_size = 0

        # 获取文件列表
        for obj in bucket.list_objects(prefix=folder_path).object_list:
            # 文件类型过滤
            if file_types:
                if not any(obj.key.lower().endswith(ext.lower()) for ext in file_types):
                    continue

            # 收集文件信息
            file_info = {
                'path': obj.key,
                'size': obj.size,
                'modified': obj.last_modified,
                'etag': obj.etag.strip('"')
            }
            files.append(file_info)
            total_size += obj.size

        # 排序（按修改时间倒序）
        files.sort(key=lambda x: x['modified'], reverse=True)

        # 显示结果
        print(f"\n📊 找到 {len(files)} 个文件，总大小: {format_size(total_size)}")
        print("=" * 80)

        if show_details:
            print(f"{'序号':<4} {'文件路径':<50} {'大小':<12} {'修改时间':<20}")
            print("-" * 80)

            for i, file_info in enumerate(files, 1):
                size_str = format_size(file_info['size'])
                print(f"{i:<4} {file_info['path']:<50} {size_str:<12}")
        else:
            for i, file_info in enumerate(files, 1):
                print(f"{i:<4} {file_info['path']}")

        return files

    except Exception as e:
        print(f"❌ 列出文件失败: {str(e)}")
        return []


def list_uploaded_videos():
    """列出已上传的视频"""
    print("📋 列出已上传的视频文件:")
    videos = list_all_files(OUTPUT_OSS_FOLDER, ['.mp4'], show_details=True)
    return videos


# ============ 主程序入口 ============
if __name__ == "__main__":
    result = list_uploaded_videos()
    print(result)
    # print("🤖 数字人视频处理系统 v2.2 (带片段替换)")
    # print("=" * 60)
    #
    # # 验证配置
    # if not validate_config():
    #     print("❌ 配置验证失败")
    #     exit(1)
    #
    # # 简单测试
    # print("🧪 测试TTS...")
    # test_audio = os.path.join(LOCAL_DIR, "test.wav")
    # if cosyvoice_tts_memory_optimized("测试语音合成功能", test_audio):
    #     print("✅ TTS测试通过")
    #     if os.path.exists(test_audio):
    #         os.remove(test_audio)
    # else:
    #     print("⚠️ TTS测试失败")
    #
    # # 开始处理
    # print("\n" + "=" * 60)
    # try:
    #     # 使用带片段替换的处理流程
    #     process_single_video_by_url('')  # 只处理1个视频测试
    #
    # except KeyboardInterrupt:
    #     print("\n⏹️ 用户中断")
    # except Exception as e:
    #     print(f"\n❌ 程序异常: {str(e)}")
    #     import traceback
    #
    #     traceback.print_exc()
    #
    # print("\n🤖 程序结束")
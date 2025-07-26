import os
import random
import re
import time
import json
import base64
from datetime import datetime
import cv2
import numpy as np
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
import oss2
import nls  # 新的阿里云智能语音交互SDK
import requests

# ============ 配置信息 ============
ACCESS_KEY_ID = 'your-access-key-id'
ACCESS_SECRET = 'your-access-secret'
OSS_ENDPOINT = 'oss-cn-beijing.aliyuncs.com'
BUCKET_NAME = 'your-bucket-name'
VIDEO_OSS_PATH = 'videos/original.mp4'  # 原始视频路径
ADS_OSS_FOLDER = 'ads/'  # 广告图片目录
OUTPUT_OSS_FOLDER = 'outputs/'  # 输出目录

# 智能语音交互配置
NLS_URL = "wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1"
TOKEN = "your-token"  # 需要通过阿里云获取Token
APPKEY = "your-appkey"  # 从智能语音交互控制台获取

# ============ 本地临时目录 ============
LOCAL_DIR = './temp/'
os.makedirs(LOCAL_DIR, exist_ok=True)

# ============ 初始化 OSS ============
auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, BUCKET_NAME)


# ============ 工具函数 ============

def download_from_oss(oss_path, local_path):
    bucket.download_file(oss_path, local_path)
    print(f"Downloaded {oss_path} to {local_path}")


def upload_to_oss(local_path, oss_path):
    bucket.upload_file(oss_path, local_path)
    print(f"Uploaded {local_path} to {oss_path}")


def get_video_duration(video_path):
    video = VideoFileClip(video_path)
    duration = video.duration
    video.close()
    return duration


# ============ 获取Token函数 ============
def get_ali_token():
    """获取阿里云智能语音交互Token"""
    url = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'AccessKeyId': ACCESS_KEY_ID,
        'AccessKeySecret': ACCESS_SECRET
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            return result.get('Token', {}).get('Id', '')
        else:
            print(f"获取Token失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取Token异常: {e}")
        return None


# ============ ASR 提取语音文本 ============
class ASRProcessor:
    def __init__(self):
        self.result_text = ""

    def on_sentence_end(self, message, *args):
        """语音识别句子结束回调"""
        try:
            msg = json.loads(message)
            if 'payload' in msg and 'result' in msg['payload']:
                self.result_text += msg['payload']['result']
        except:
            pass

    def on_error(self, message, *args):
        print(f"ASR Error: {message}")

    def on_completed(self, message, *args):
        print("ASR识别完成")


def ali_asr(audio_path):
    """使用新SDK进行语音识别"""
    processor = ASRProcessor()

    # 创建语音识别器
    transcriber = nls.NlsSpeechTranscriber(
        url=NLS_URL,
        token=TOKEN,
        appkey=APPKEY,
        on_sentence_end=processor.on_sentence_end,
        on_error=processor.on_error,
        on_completed=processor.on_completed
    )

    try:
        # 开始识别
        transcriber.start(
            aformat="pcm",
            sample_rate=16000,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True
        )

        # 读取音频文件并发送
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        # 分片发送音频数据
        chunk_size = 3200  # 每次发送3200字节
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            transcriber.send_audio(chunk)
            time.sleep(0.04)  # 控制发送速度

        # 停止识别
        transcriber.stop()
        time.sleep(1)

        return processor.result_text if processor.result_text else "识别失败"

    except Exception as e:
        print(f"ASR识别异常: {e}")
        return "识别失败"
    finally:
        transcriber.shutdown()


# ============ TTS 合成新语音 ============
class TTSProcessor:
    def __init__(self, output_path):
        self.output_path = output_path
        self.audio_data = b''

    def on_data(self, data, *args):
        """接收合成的音频数据"""
        self.audio_data += data

    def on_error(self, message, *args):
        print(f"TTS Error: {message}")

    def on_completed(self, message, *args):
        """合成完成，保存音频文件"""
        try:
            with open(self.output_path, 'wb') as f:
                f.write(self.audio_data)
            print(f"TTS音频已保存到: {self.output_path}")
        except Exception as e:
            print(f"保存TTS音频失败: {e}")


def ali_tts(text, output_audio):
    """使用新SDK进行语音合成"""
    processor = TTSProcessor(output_audio)

    # 创建语音合成器
    synthesizer = nls.NlsSpeechSynthesizer(
        url=NLS_URL,
        token=TOKEN,
        appkey=APPKEY,
        on_data=processor.on_data,
        on_error=processor.on_error,
        on_completed=processor.on_completed
    )

    try:
        # 开始合成
        synthesizer.start(
            text=text,
            aformat="wav",
            voice="xiaoyun",
            sample_rate=16000,
            volume=50,
            speech_rate=0,
            pitch_rate=0
        )

        time.sleep(2)  # 等待合成完成
        print(f"TTS generated: {output_audio}")

    except Exception as e:
        print(f"TTS合成异常: {e}")
    finally:
        synthesizer.shutdown()


# ============ 随机截取片段 ============
def random_clip(video_path, output_path, min_len=60, max_len=300):
    video = VideoFileClip(video_path)
    duration = video.duration
    clip_len = random.randint(min_len, max_len)
    start_time = random.uniform(0, duration - clip_len)
    subclip = video.subclip(start_time, start_time + clip_len)
    subclip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    subclip.close()
    return output_path


# ============ 插入语义边界广告图 ============
def insert_ads_on_boundaries(video_path, images, output_path):
    video = VideoFileClip(video_path)

    # 提取音频并进行ASR识别
    temp_audio = LOCAL_DIR + 'temp_for_asr.wav'
    extract_audio(video_path, temp_audio)
    text = ali_asr(temp_audio)

    # 按标点符号分割句子
    sentences = re.split(r'[。！？]', text)
    clips = []

    sentence_duration = video.duration / len([s for s in sentences if s.strip()])

    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue

        start_time = i * sentence_duration
        end_time = min((i + 1) * sentence_duration, video.duration)
        subclip = video.subclip(start_time, end_time)
        clips.append(subclip)

        # 随机插入广告图
        if i < len(sentences) - 1 and random.random() < 0.5 and images:
            img_url = random.choice(images)
            img_local = LOCAL_DIR + os.path.basename(img_url)
            download_from_oss(img_url, img_local)

            img_clip = ImageClip(img_local).set_duration(2).set_position(("center", "bottom")).resize(
                width=video.w * 0.4)
            clips.append(img_clip)

    if clips:
        final = concatenate_videoclips(clips)
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        final.close()

    video.close()
    # 清理临时音频文件
    if os.path.exists(temp_audio):
        os.remove(temp_audio)


# ============ 缓慢亮度变化 ============
def apply_brightness_curve(frame, t, total_frames):
    factor = 0.8 + 0.4 * np.sin(t / total_frames * 2 * np.pi)
    bright_frame = cv2.convertScaleAbs(frame, alpha=factor, beta=20)
    return bright_frame


# ============ 边角模糊 ============
def apply_edge_blur(frame, blur_size=15):
    h, w = frame.shape[:2]
    mask = np.zeros_like(frame)
    mask[blur_size:h - blur_size, blur_size:w - blur_size] = 1
    blurred = cv2.GaussianBlur(frame, (15, 15), 10)
    blended = np.where(mask == 0, blurred, frame)
    return blended


# ============ 抽帧 & 保存 ============
def extract_audio(video_path, output_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_path)
    video.close()
    return output_path


# ============ 主流程 ============
def process_and_upload_video(index):
    print(f"\nProcessing video #{index}...")

    # 获取Token（每次处理时刷新）
    global TOKEN
    token = get_ali_token()
    if token:
        TOKEN = token
    else:
        print("无法获取Token，使用默认Token")

    # Step 1: 下载原始视频
    original_video_local = os.path.join(LOCAL_DIR, f"original_{index}.mp4")
    download_from_oss(VIDEO_OSS_PATH, original_video_local)

    # Step 2: 随机截取片段
    clipped_video = os.path.join(LOCAL_DIR, f"clipped_{index}.mp4")
    random_clip(original_video_local, clipped_video)

    # Step 3: 提取音频并 ASR
    audio_path = os.path.join(LOCAL_DIR, f"audio_{index}.wav")
    extract_audio(clipped_video, audio_path)
    text = ali_asr(audio_path)
    print("ASR Result:", text)

    # Step 4: TTS 生成新语音
    new_audio = os.path.join(LOCAL_DIR, f"new_audio_{index}.wav")
    ali_tts(text, new_audio)

    # Step 5: 替换音频
    temp_video = os.path.join(LOCAL_DIR, f"temp_audio_{index}.mp4")
    video = VideoFileClip(clipped_video)
    new_audio_clip = AudioFileClip(new_audio)
    final_video = video.set_audio(new_audio_clip)
    final_video.write_videofile(temp_video, codec='libx264', audio_codec='aac')
    video.close()
    new_audio_clip.close()
    final_video.close()

    # Step 6: 获取广告图链接
    try:
        ads_list = [f"{ADS_OSS_FOLDER}{obj.key}" for obj in bucket.list_objects(ADS_OSS_FOLDER).object_list]
    except:
        ads_list = []

    # Step 7: 插入语义广告图
    after_ads_video = os.path.join(LOCAL_DIR, f"with_ads_{index}.mp4")
    insert_ads_on_boundaries(temp_video, ads_list, after_ads_video)

    # Step 8: 添加扰动（亮度、边角模糊）
    cap = cv2.VideoCapture(after_ads_video)
    out_path = os.path.join(LOCAL_DIR, f"final_{index}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = apply_brightness_curve(frame, frame_count, total_frames)
        frame = apply_edge_blur(frame)
        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()

    # Step 9: 上传到 OSS
    output_oss_path = f"{OUTPUT_OSS_FOLDER}output_{index}.mp4"
    upload_to_oss(out_path, output_oss_path)

    # 清理临时文件
    temp_files = [original_video_local, clipped_video, audio_path, new_audio, temp_video, after_ads_video]
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"删除临时文件失败 {temp_file}: {e}")


# ============ 批量生成 ============
if __name__ == "__main__":
    for i in range(2):
        try:
            process_and_upload_video(i)
        except Exception as e:
            print(f"Error processing video #{i}: {e}")
            continue
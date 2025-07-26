import os
from typing import List

import numpy as np
import cv2
import librosa
import webrtcvad
from moviepy import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip, vfx,VideoClip
from pydub import AudioSegment
from skimage import filters, morphology
import wave
from core.cliptemplate.random_transition import apply_random_transition
from core.cliptransition.easy_clip_transitions import black_transition
import uuid

# =================== 1. 视频与音频处理 ===================

def load_video_and_audio(video_path):
    """加载视频和音频"""
    video = VideoFileClip(video_path)
    audio_path = "temp_audio.wav"
    video.audio.write_audiofile(audio_path)
    return video, audio_path

def process_audio_for_vad(audio_path):
    """将音频转换为单声道16kHz，供VAD使用"""
    audio = AudioSegment.from_wav(audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    processed_path = "processed_audio.wav"
    audio.export(processed_path, format="wav")
    return processed_path

# =================== 2. 人声检测 ===================

def detect_speech_webrtcvad(audio_path):
    """使用WebRTC VAD检测人声片段"""
    vad = webrtcvad.Vad()
    vad.set_mode(3)  # 模式3：最严格，适合嘈杂环境

    speech_segments = []

    with wave.open(audio_path, 'rb') as wf:
        # 确保音频格式符合要求
        if wf.getnchannels() != 1:
            raise ValueError("Audio must be mono")
        if wf.getsampwidth() != 2:
            raise ValueError("Audio must be 16-bit PCM")
        if wf.getframerate() not in (8000, 16000, 32000):
            raise ValueError("Sample rate must be 8000, 16000 or 32000")

        sample_rate = wf.getframerate()
        frame_duration_ms = 30  # 可选 10、20 或 30 毫秒
        frame_size_bytes = int(sample_rate * (frame_duration_ms / 1000) * 2)  # 每帧字节数 = 样本数 × 2字节

        current_time = 0.0
        frame_count = 0
        is_previous_speech = False
        segment_start = None

        while True:
            frame_bytes = wf.readframes(frame_size_bytes // 2)  # readframes 参数是样本数
            if len(frame_bytes) < frame_size_bytes:
                break  # 结束

            is_speech = vad.is_speech(frame_bytes, sample_rate)

            if is_speech:
                if not is_previous_speech:
                    segment_start = current_time
                is_previous_speech = True
            else:
                if is_previous_speech:
                    speech_segments.append((segment_start, current_time))
                is_previous_speech = False

            current_time += frame_duration_ms / 1000.0
            frame_count += 1

        # 如果最后一段是语音，也要加进去
        if is_previous_speech:
            speech_segments.append((segment_start, current_time))

    return speech_segments

# =================== 3. 高潮片段检测 ===================

def detect_audio_peaks(audio_path, sr=16000):
    """检测音频能量突变"""
    y, _ = librosa.load(audio_path, sr=sr)
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    rms_diff = np.diff(rms_db[0])
    mean_diff = np.mean(np.abs(rms_diff))
    threshold = 2 * mean_diff
    peak_frames = np.where(np.abs(rms_diff) > threshold)[0]
    peak_times = librosa.frames_to_time(peak_frames, sr=sr, hop_length=512)
    return peak_times

def detect_visual_motion(video_path):
    """检测视觉运动强度"""
    cap = cv2.VideoCapture(video_path)
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    motion_times = []
    count = 0
    while cap.isOpened():
        ret, frame3 = cap.read()
        if not ret:
            break
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        gray3 = cv2.cvtColor(frame3, cv2.COLOR_BGR2GRAY)
        diff1 = cv2.absdiff(gray1, gray2)
        diff2 = cv2.absdiff(gray2, gray3)
        diff = cv2.bitwise_and(diff1, diff2)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        motion_strength = np.mean(thresh)
        if motion_strength > 100:
            motion_times.append(count / cap.get(cv2.CAP_PROP_FPS))
        frame1 = frame2
        frame2 = frame3
        count += 1
    cap.release()
    return motion_times

# =================== 4. 权重计算 ===================

def segment_video(video, segment_duration=1.0):
    """将视频按固定时长切分片段"""
    duration = video.duration
    segments = []
    for i in range(int(duration // segment_duration) + 1):
        start = i * segment_duration
        end = min((i + 1) * segment_duration, duration)
        if start >= end:
            break
        segments.append((start, end))
    return segments

def calculate_weights(segments, speech_times, peak_times, motion_times):
    """计算每个片段的权重"""
    weights = []
    for start, end in segments:
        # 计算人声权重
        speech_duration = 0
        for s_start, s_end in speech_times:
            overlap_start = max(start, s_start)
            overlap_end = min(end, s_end)
            if overlap_start < overlap_end:
                speech_duration += overlap_end - overlap_start
        speech_weight = 0.4 * (1 + 0.1 * (speech_duration / (end - start))) if (end - start) > 0 else 0
        
        # 计算高潮权重（音频+视觉）
        peak_count = sum(1 for t in peak_times if start <= t <= end)
        motion_count = sum(1 for t in motion_times if start <= t <= end)
        peak_weight = 0.6 * (1 + 0.2 * (peak_count + motion_count) / (end - start)) if (end - start) > 0 else 0
        
        total_weight = speech_weight + peak_weight
        weights.append((start, end, total_weight))
    return weights

# =================== 5. 贪心算法筛选片段 ===================

def greedy_select_segments(weights, min_gap=0.5,amount=100):
    """贪心算法选择互不冲突的高权重片段"""
    # 按权重降序排序
    sorted_weights = sorted(weights, key=lambda x: x[2], reverse=True)
    selected = []
    last_end = 0
    # for start, end, weight in sorted_weights:
    #     if start >= last_end:
    #         selected.append((start, end))
    #         last_end = end
    #     elif end - last_end < min_gap:
    #         continue  # 确保片段间有一定间隔
    #     if len(selected) >= amount:  # 剪切数量达到要求，结束循环
    #         break
    return sorted_weights[0:amount]

# =================== 6. 剪辑与输出 ===================

def apply_transition(clip1:VideoClip, clip2:VideoClip, motion_strength,duration=0.5):
    """根据运动强度选择转场效果"""
    # if motion_strength > 150:
    #     transition = clip1.with_effects([vfx.FadeOut(duration)])
    # elif motion_strength > 100:
    #     transition = CompositeVideoClip([clip1.subclipped(start_time=clip1.duration-duration,end_time=duration), clip2.with_opacity(0.5).subclipped(start_time=0, end_time=duration)])
    # else:
    #     transition = CompositeVideoClip([clip1.subclipped(start_time=clip1.duration-duration,end_time=duration), clip2.with_opacity(0.7).subclipped(start_time=0, end_time=duration)])
    transition = apply_random_transition(clip1, clip2, duration=duration)
    # return concatenate_videoclips([clip1, clip2])
    return transition

def smart_cut_video(videos, selected_segments, output_path):
    """根据选中的片段剪辑视频"""
    clips = []
    # for i, (start, end) in enumerate(selected_segments):
    #     clip = video.subclipped(start, end)
    #     if i > 0:
    #         # 获取上一个片段的运动强度（示例逻辑）
    #         motion_strength = 120  # 可根据实际检测结果替换
    #         transition_clip = apply_transition(clips[-1], clip, motion_strength)
    #         clips[-1] = transition_clip
    #     #     clips.append(transition_clip)
    #     #     apply_random_transition()
    #     else:
    #         clips.append(clip)
    for i in range(len(selected_segments)):
        if i>0:
            clip=videos.subclipped(selected_segments[i][0], selected_segments[i][1])
            # clips.append(clip)
            # clip1=videos.subclipped(selected_segments[i+1][0], selected_segments[i+1][1])
            transition = apply_random_transition(clips, clip)

            clips=transition

        else:
            clip = videos.subclipped(selected_segments[i][0], selected_segments[i][1])
            clips=clip

            # transition = black_transition(clip)
            # clips.append(transition)



    # final_clip = concatenate_videoclips(clips)
    final_clip=clips
    final_clip.write_videofile(output_path, codec="libx264")

# =================== 7. 主流程 ===================

def smart_clip(video_path, output_path):
    # 1. 加载视频和音频
    video, audio_path = load_video_and_audio(video_path)
    
    # 2. 处理音频并检测人声
    processed_audio_path = process_audio_for_vad(audio_path)
    speech_times = detect_speech_webrtcvad(processed_audio_path)
    
    # 3. 检测高潮片段
    peak_times = detect_audio_peaks(audio_path)
    motion_times = detect_visual_motion(video_path)
    
    # 4. 切分视频片段并计算权重
    segments = segment_video(video, segment_duration=3.0)  # 3秒一段
    weights = calculate_weights(segments, speech_times, peak_times, motion_times)
    
    # 5. 贪心算法选择高权重片段
    selected_segments = greedy_select_segments(weights,amount=5)
    
    # 6. 剪辑并输出
    smart_cut_video(video, selected_segments, output_path)
    
    # 清理临时文件
    os.remove(audio_path)
    os.remove(processed_audio_path)


def smart_clips(
        enterprise_files: List[str],
        audio_clips: List,
        project_dir: str,
        num_clips: int
) -> List:
    """
    智能剪辑函数 - 根据音频片段生成对应的视频片段

    参数:
        enterprise_files: 企业素材文件路径列表
        audio_clips: 音频片段列表
        project_dir: 项目目录路径
        num_clips: 需要生成的片段数量

    返回:
        List: 处理好的视频片段列表
    """
    from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip
    import random
    import os

    print(f"🎬 开始智能剪辑处理...")
    print(f"   企业素材数量: {len(enterprise_files)}")
    print(f"   音频片段数量: {len(audio_clips)}")
    print(f"   需要生成片段: {num_clips}")

    if not enterprise_files:
        raise ValueError("企业素材文件列表为空")

    if len(audio_clips) != num_clips:
        print(f"⚠️ 音频片段数量({len(audio_clips)})与需要生成的片段数量({num_clips})不匹配")

    # 初始化视频片段列表
    enterprise_clips = []

    try:
        # 为每个音频片段生成对应的视频片段
        for idx, audio_clip in enumerate(audio_clips[:num_clips]):
            print(f"🎯 处理第 {idx + 1}/{num_clips} 个片段...")

            # 随机选择一个企业素材文件
            video_path = random.choice(enterprise_files)
            print(f"   选中素材: {os.path.basename(video_path)}")

            # 加载视频
            video_clip = VideoFileClip(video_path)

            # 调整视频尺寸
            if video_clip.size[0] > video_clip.size[1]:
                # 横屏视频
                video_clip = video_clip.resized((1920, 1080))
            else:
                # 竖屏视频
                video_clip = video_clip.resized((1080, 1920))

            # 获取音频长度
            target_duration = audio_clip.duration
            print(f"   目标时长: {target_duration:.2f}秒")

            # 调整视频长度匹配音频
            if video_clip.duration > target_duration:
                # 视频较长，随机截取片段
                max_start = video_clip.duration - target_duration - 0.1
                start_time = random.uniform(0, max(0, max_start))
                video_clip = video_clip.subclipped(start_time, start_time + target_duration)
                print(f"   截取片段: {start_time:.2f}s - {start_time + target_duration:.2f}s")
            else:
                # 视频较短，循环播放
                print(f"   视频较短({video_clip.duration:.2f}s)，需要循环播放")
                try:
                    # 计算需要循环的次数
                    loop_count = int(target_duration / video_clip.duration) + 1

                    # 手动创建循环
                    looped_clips = []
                    remaining_duration = target_duration

                    while remaining_duration > 0:
                        if remaining_duration >= video_clip.duration:
                            # 完整循环
                            looped_clips.append(video_clip)
                            remaining_duration -= video_clip.duration
                        else:
                            # 部分循环
                            looped_clips.append(video_clip.subclipped(0, remaining_duration))
                            remaining_duration = 0

                    video_clip = concatenate_videoclips(looped_clips, method="compose")
                    print(f"   循环完成，最终时长: {video_clip.duration:.2f}s")

                except Exception as loop_error:
                    print(f"   ⚠️ 循环处理失败: {loop_error}")
                    # 如果循环失败，直接使用原视频并调整到目标时长
                    if video_clip.duration < target_duration:
                        # 简单重复最后一帧
                        video_clip = video_clip.with_duration(target_duration)
                    else:
                        video_clip = video_clip.subclipped(0, target_duration)

            # 绑定音频到视频
            video_clip = video_clip.with_audio(audio_clip)
            enterprise_clips.append(video_clip)

            print(f"   ✅ 第 {idx + 1} 个片段处理完成")

        print(f"🎉 智能剪辑完成，生成 {len(enterprise_clips)} 个片段")
        return enterprise_clips

    except Exception as e:
        print(f"❌ 智能剪辑处理失败: {e}")
        # 抛出异常，让调用方处理回退逻辑
        raise

# =================== 8. 运行示例 ===================

if __name__ == "__main__":
    # input_video = "/Users/luming/PycharmProjects/AI-Movie-Clip/cliptest/装修行业/装修1.mp4"
    # output_video = "output_smart_cut.mp4"
    # smart_clip(input_video, output_video)

    directory_path = "//cliptest/装修行业"
    smart_clips(directory_path, "output10.mp4", is_directory=True)

    # 打印目录中的所有文件（调试用）
    # directory_path = "/Users/luming/PycharmProjects/AI-Movie-Clip/cliptest/装修行业"
    # print("目录中的文件：")
    # for file in os.listdir(directory_path):
    #     print(f"- {file}")
import os
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


def smart_clips(input_source: str, output_path: str, is_directory: bool = False):
    """
    批量处理视频文件或目录中的所有视频

    参数:
        input_source: 输入文件路径或目录路径
        output_path: 输出视频路径
        is_directory: 是否为目录（默认: False）
    """
    # 初始化视频片段列表
    clips = []

    # 处理目录输入
    if is_directory:
        print(f"Processing directory: {input_source}")
        # 支持的视频文件扩展名（可根据需求扩展）
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        # 遍历目录下的所有文件
        for root, _, files in os.walk(input_source):
            for file in files:
                file_path = os.path.join(root, file)
                # 检查文件扩展名是否为视频格式
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    print(f"Found video: {file_path}")
                    clip = VideoFileClip(file_path)
                    if clip.size[0] > clip.size[1]:
                        clip = clip.resized(height=1080, width=1920)
                    else:
                        clip = clip.resized(width=1080, height=1920)
                    clips.append(clip)

    # 处理文件列表输入
    else:
        if isinstance(input_source, list):
            video_paths = input_source
        else:
            video_paths = [input_source]  # 兼容单个文件路径输入

        print(f"Processing {len(video_paths)} video(s):")
        for video_path in video_paths:
            print(f"- {video_path}")
            clip=VideoFileClip(video_path)
            if clip.size[0]>clip.size[1]:
                clip=clip.resized(height=1080, width=1920)
            else:
                clip=clip.resized(width=1080, height=1920)
            clips.append(clip)

    # 检查是否有有效视频片段
    if not clips:
        raise ValueError("No valid video files found!")

    # 创建临时目录
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_output = os.path.join(temp_dir, f"{uuid.uuid1()}.mp4")

    # try:
    # 拼接视频片段
    concatenated_clip = concatenate_videoclips(clips,"compose")
    concatenated_clip.write_videofile(
        temp_output,
        codec="libx264",
        fps=24,
    )
    print(f"Temporary concatenated video saved to: {temp_output}")

    # 调用智能处理函数（示例：假设 smart_clip 是你的自定义处理函数）
    # 注意：这里需要将临时文件路径传入 smart_clip
    smart_clip(temp_output, output_path)  # 假设 smart_clip 处理单个视频

    print(f"✅ 处理完成，结果保存至: {output_path}")


    # finally:
    # 清理临时文件（可选）
    if os.path.exists(temp_output):
        os.remove(temp_output)
        print("临时文件已清理")

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
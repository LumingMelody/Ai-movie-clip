import librosa
import numpy as np
import requests  # 用于调用通义千问 API
import os

# =================== 1. 特征提取函数 ===================
def extract_audio_features(audio_path):
    y, sr = librosa.load(audio_path, duration=30)  # 最多30秒

    # 常用声学特征
    pitches, _ = librosa.piptrack(y=y, sr=sr)
    non_zero_pitches = pitches[pitches > 0]
    mean_pitch = np.mean(non_zero_pitches) if len(non_zero_pitches) > 0 else 0

    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    mean_spectral_centroid = np.mean(spectral_centroids)  # 亮度（越高越“亮”）

    zcr = librosa.feature.zero_crossing_rate(y)[0]
    mean_zcr = np.mean(zcr)

    rms = librosa.feature.rms(y=y)[0]
    mean_rms = np.mean(rms)  # 能量（响度）

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # 返回可读的特征字典
    features = {
        "平均音高 (Hz)": float(mean_pitch),
        "频谱质心 (Hz)": float(mean_spectral_centroid),  # 感知亮度
        "节奏 (BPM)": float(tempo),
        "能量 (RMS)": float(mean_rms),
        "零交叉率": float(mean_zcr)
    }
    return features

# =================== 2. 调用 Qwen API（通义千问）===================
def classify_with_qwen(features_desc, api_key=None):
    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")  # 推荐：设置环境变量
        if not api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量或传入 API Key")

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = f"""
    你是一个专业的音乐情绪分析专家。请根据以下音频特征，判断这段音乐最可能是哪种风格：

    {features_desc}

    请从以下类别中选择一个最合适的：
    - 舒缓柔美（慢节奏、低能量、低亮度）
    - 雄壮有力（中高能量、中高速节奏）
    - 活泼欢快（高节奏、中等能量、明亮）
    - 刺耳/尖锐（高频集中、高亮度、高零交叉）
    - 嘈杂混乱（高零交叉、低和谐性）

    请只回答类别名称，不要解释。
    """

    data = {
        "model": "qwen-max",  # 或 qwen-plus, qwen-turbo
        "input": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "temperature": 0.1  # 降低随机性，更稳定
        }
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    if "output" in result and "text" in result["output"]:
        return result["output"]["text"].strip()
    else:
        raise Exception(f"API Error: {result}")

# =================== 3. 主函数 ===================
def classify_music_with_qwen(audio_path, api_key=None):
    print(f"正在分析音频：{audio_path}")
    
    # 提取特征
    features = extract_audio_features(audio_path)
    
    # 转为自然语言描述
    desc = (
        f"平均音高: {features['平均音高 (Hz)']:.1f} Hz\n"
        f"频谱质心（亮度）: {features['频谱质心 (Hz)']:.1f} Hz\n"
        f"节奏（BPM）: {features['节奏 (BPM)']:.1f}\n"
        f"能量（RMS）: {features['能量 (RMS)']:.3f}\n"
        f"零交叉率: {features['零交叉率']:.3f}"
    )
    print("提取特征：\n" + desc)

    # 调用 Qwen 判断
    try:
        result = classify_with_qwen(desc, api_key)
        print(f"\n🎵 音乐风格判断：{result}")
        return result
    except Exception as e:
        print(f"调用 Qwen 失败：{e}")
        return None

# =================== 使用示例 ===================
if __name__ == "__main__":
    # 请先获取 DashScope API Key：https://dashscope.console.aliyun.com/
    # 并设置环境变量：export DASHSCOPE_API_KEY="your-api-key-here"
    
    classify_music_with_qwen("sample.mp3")
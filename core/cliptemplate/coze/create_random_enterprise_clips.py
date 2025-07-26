# -*- coding: utf-8 -*-
# 完整的视频合并功能：随机剪辑 + 文字叠加 + 拼接成完整视频

import os
import random
import numpy as np
from typing import List, Union
from moviepy import (
    VideoFileClip, AudioFileClip, AudioArrayClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips, CompositeAudioClip,
    afx, vfx
)

# 支持的视频文件扩展名
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')


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


def select_random_videos(files: List[str], count: int) -> List[str]:
    """随机选择指定数量的视频文件"""
    if not files:
        return []
    if len(files) <= count:
        return files
    return random.sample(files, count)


def create_single_video_clip(
        video_path: str,
        audio_clip,
        target_resolution: tuple = (1920, 1080)
) -> VideoFileClip:
    """创建单个视频片段"""
    video_clip = VideoFileClip(video_path)

    # 根据视频方向调整分辨率
    if video_clip.size[0] > video_clip.size[1]:
        video_clip = video_clip.resized(target_resolution)
    else:
        vertical_resolution = (target_resolution[1], target_resolution[0])
        video_clip = video_clip.resized(vertical_resolution)

    # 按音频长度裁剪视频
    target_duration = audio_clip.duration

    if video_clip.duration > target_duration:
        max_start_time = max(0, video_clip.duration - target_duration - 0.1)
        start_time = random.uniform(0, max_start_time) if max_start_time > 0 else 0
        video_clip = video_clip.subclipped(start_time, start_time + target_duration)
    else:
        loop_count = max(1, int(target_duration / video_clip.duration) + 1)
        video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
        video_clip = video_clip.subclipped(0, target_duration)

    # 绑定音频
    video_clip = video_clip.with_audio(audio_clip)
    return video_clip


def create_text_clip(text: str, duration: float, is_title: bool = False) -> TextClip:
    """创建文字片段"""
    # 简化版文字创建（你可以根据需要添加字体路径）
    if len(text) > 20:
        text = text[:20] + "\n" + text[20:]

    return TextClip(
        text=text,
        font_size=80 if is_title else 48,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(1080, None)
    ).with_duration(duration)


def create_background_image() -> ImageClip:
    """创建测试用的背景图片"""
    # 创建一个简单的背景色
    import numpy as np
    from moviepy import ImageClip

    # 创建纯色背景 (深蓝色)
    bg_array = np.full((1080, 1920, 3), [30, 60, 120], dtype=np.uint8)
    return ImageClip(bg_array, duration=1)


def create_random_enterprise_clips(
        enterprise_source: Union[str, List[str]],
        audio_clips: List,
        add_digital_host: bool = False,
        target_resolution: tuple = (1920, 1080)
) -> List[VideoFileClip]:
    """
    🔥 核心函数：随机剪辑模式生成企业视频片段
    """
    # 解析企业素材文件
    if isinstance(enterprise_source, list):
        enterprise_files = []
        for item in enterprise_source:
            if isinstance(item, str) and os.path.isfile(item):
                enterprise_files.append(item)
            else:
                enterprise_files.extend(resolve_materials(item, VIDEO_EXTENSIONS))
    else:
        enterprise_files = resolve_materials(enterprise_source, VIDEO_EXTENSIONS)

    if not enterprise_files:
        raise ValueError(f"企业素材文件列表为空: {enterprise_source}")

    if not audio_clips:
        raise ValueError("音频片段列表不能为空")

    print(f"📁 找到 {len(enterprise_files)} 个企业素材文件")

    # 计算需要的企业片段数量
    num_enterprise_clips = len(audio_clips) - (2 if add_digital_host else 0)

    if num_enterprise_clips <= 0:
        raise ValueError(f"音频数量不足，需要 {2 if add_digital_host else 0} + 企业片段数")

    print(f"🎯 需要生成 {num_enterprise_clips} 个企业片段")

    # 随机选择企业视频文件
    selected_files = select_random_videos(enterprise_files, num_enterprise_clips)
    enterprise_clips = []

    for idx, audio_clip in enumerate(audio_clips):
        # 跳过数字人对应的首尾音频
        if add_digital_host and (idx == 0 or idx == len(audio_clips) - 1):
            continue

        # 随机选择一个企业素材文件
        video_idx = random.randint(0, len(selected_files) - 1)
        video_path = selected_files[video_idx]

        try:
            video_clip = create_single_video_clip(
                video_path=video_path,
                audio_clip=audio_clip,
                target_resolution=target_resolution
            )
            enterprise_clips.append(video_clip)
            print(f"✅ 创建企业片段 {len(enterprise_clips)}: {os.path.basename(video_path)}")

        except Exception as e:
            print(f"❌ 创建企业片段失败: {video_path}, 错误: {e}")
            raise

    print(f"✅ 随机剪辑完成，共生成 {len(enterprise_clips)} 个企业片段")
    return enterprise_clips


def create_complete_advertisement_video_no_text(
        enterprise_source: Union[str, List[str]],
        audio_clips: List,
        add_digital_host: bool = False,
        target_resolution: tuple = (1920, 1080),
        output_path: str = "final_advertisement_no_text.mp4"
) -> str:
    """
    🔥 无文字版本：生成完整的广告视频（仅视频拼接，不添加文字）
    """

    print("🎬 开始生成完整广告视频（无文字版）...")

    # 1. 生成企业视频片段
    enterprise_clips = create_random_enterprise_clips(
        enterprise_source=enterprise_source,
        audio_clips=audio_clips,
        add_digital_host=add_digital_host,
        target_resolution=target_resolution
    )

    # 2. 🔥 直接拼接视频片段（不添加文字叠加）
    print("🔗 开始拼接所有视频片段...")
    final_video = concatenate_videoclips(enterprise_clips, method="compose")

    # 3. 输出最终视频
    print(f"🎬 开始生成最终视频: {output_path}")
    final_video.write_videofile(
        output_path,
        codec="libx264",
        fps=24,
        audio_codec="aac",
        threads=4,
    )

    # 显示结果信息
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ 最终视频生成完成!")
    print(f"📄 文件路径: {output_path}")
    print(f"📊 文件大小: {file_size:.1f}MB")
    print(f"⏱️  视频时长: {final_video.duration:.1f}秒")

    # 清理资源
    try:
        for clip in enterprise_clips:
            clip.close()
        final_video.close()
    except:
        pass

    return output_path


def create_test_audio_clips(durations: List[float]) -> List:
    """创建测试用的音频片段"""
    audio_clips = []

    for i, duration in enumerate(durations):
        # 生成静音音频
        sample_rate = 44100
        samples = int(duration * sample_rate)
        audio_array = np.zeros((samples, 2))
        audio_clip = AudioArrayClip(audio_array, fps=sample_rate)
        audio_clips.append(audio_clip)
        print(f"🎵 创建测试音频 {i + 1}: {duration}秒")

    return audio_clips


def test_no_text_version():
    """测试无文字版本"""
    enterprise_folder = "/Users/luming/PycharmProjects/Ai-movie-clip__/cliptest/装修行业"

    # 创建测试音频
    test_durations = [3.0, 4.0, 2.5, 3.5]  # 4个音频片段
    audio_clips = create_test_audio_clips(test_durations)

    # 输出路径
    output_dir = "/Users/luming/PycharmProjects/Ai-movie-clip__/final_videos"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "test_no_text.mp4")

    try:
        final_video_path = create_complete_advertisement_video_no_text(
            enterprise_source=enterprise_folder,
            audio_clips=audio_clips,
            add_digital_host=False,
            target_resolution=(1920, 1080),
            output_path=output_path
        )

        print(f"✅ 无文字版本视频生成成功: {final_video_path}")

        # 清理音频资源
        for audio_clip in audio_clips:
            audio_clip.close()

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("🚀 开始测试完整视频生成功能")
    print("=" * 60)

    # 检查企业素材目录
    test_path = "/Users/luming/PycharmProjects/Ai-movie-clip__/cliptest/装修行业"
    if not os.path.exists(test_path):
        print(f"❌ 企业素材目录不存在: {test_path}")
        return

    # 测试完整视频创建
    test_no_text_version()


if __name__ == '__main__':
    main()
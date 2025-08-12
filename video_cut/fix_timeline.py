"""
修复时间轴的辅助函数
确保3个片段正确拼接成30秒视频
"""

from moviepy import concatenate_videoclips


def build_sequential_video(clips_data, video_editor):
    """
    按顺序构建视频，而不依赖start属性
    
    Args:
        clips_data: 片段数据列表
        video_editor: VideoEditor实例
        
    Returns:
        拼接好的30秒视频
    """
    processed_clips = []
    
    for i, clip_data in enumerate(clips_data):
        # 处理每个片段
        clip = video_editor._process_video_clip(clip_data)
        if clip:
            video_editor.logger.info(f"片段{i+1}: 时长={clip.duration}s")
            processed_clips.append(clip)
    
    if not processed_clips:
        return None
        
    # 直接顺序拼接，不使用CompositeVideoClip
    final_video = concatenate_videoclips(processed_clips, method="compose")
    video_editor.logger.info(f"最终视频时长: {final_video.duration}s")
    
    return final_video
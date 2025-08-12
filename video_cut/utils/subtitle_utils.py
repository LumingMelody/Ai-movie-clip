"""
字幕处理工具
从coze系统中提取的字幕处理函数
"""
import re
from typing import List, Tuple
from moviepy import TextClip, CompositeVideoClip


def split_text_for_progressive_subtitles(text: str, max_chars_per_line: int = 25, max_lines: int = 2) -> List[str]:
    """
    将长文本分割成适合逐段显示的字幕片段
    
    Args:
        text: 原始文本
        max_chars_per_line: 每行最大字符数
        max_lines: 每个字幕片段的最大行数
    
    Returns:
        分割后的文本列表
    """
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
        # 如果当前片段太短（少于10个字符）且不是最后一个片段
        if len(current) < 10 and i < len(segments) - 1:
            next_segment = segments[i + 1]
            # 如果合并后不会太长
            if len(current + next_segment) <= max_segment_length:
                final_segments.append(current + next_segment)
                i += 2
                continue
        
        final_segments.append(current)
        i += 1
    
    return final_segments if final_segments else [text]


def calculate_progressive_subtitle_timings(video_duration: float, segments: List[str]) -> List[Tuple[float, float]]:
    """
    计算渐进式字幕的时间分配
    
    Args:
        video_duration: 视频总时长
        segments: 字幕片段列表
    
    Returns:
        每个片段的(开始时间, 结束时间)列表
    """
    # 基于字符数分配时间
    total_chars = sum(len(seg) for seg in segments)
    
    if total_chars == 0:
        return []
    
    timings = []
    current_time = 0.0
    
    for segment in segments:
        # 基于字符比例分配时间，但确保最短显示时间
        char_ratio = len(segment) / total_chars
        duration = max(1.5, video_duration * char_ratio)  # 至少显示1.5秒
        
        # 确保不超过视频总时长
        if current_time + duration > video_duration:
            duration = video_duration - current_time
        
        timings.append((current_time, current_time + duration))
        current_time += duration
        
        # 如果已经到达视频末尾，停止
        if current_time >= video_duration:
            break
    
    return timings


def create_subtitle_clips(segments: List[str], timings: List[Tuple[float, float]], 
                         font: str = "Arial", font_size: int = 36, 
                         color: str = "white", stroke_color: str = "black",
                         stroke_width: int = 2) -> List[TextClip]:
    """
    创建字幕剪辑列表 - 使用coze系统的实现方式
    
    Args:
        segments: 字幕文本片段
        timings: 时间分配列表
        font: 字体
        font_size: 字体大小
        color: 字体颜色
        stroke_color: 描边颜色
        stroke_width: 描边宽度
    
    Returns:
        字幕剪辑列表
    """
    import os
    subtitle_clips = []
    
    # 🔥 直接使用江西拙楷2.0.ttf字体（与/video/ai-avatar一致）
    # video_cut/utils/subtitle_utils.py -> 项目根目录需要往上2级
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    font_path = os.path.join(project_root, '江西拙楷2.0.ttf')
    
    # 备用字体路径
    alt_font_path = os.path.join(project_root, 'core/cliptemplate/coze/transform/江西拙楷2.0.ttf')
    
    print(f"🔍 字体路径计算: project_root={project_root}")
    print(f"🔍 主字体路径: {font_path}, 存在: {os.path.exists(font_path)}")
    print(f"🔍 备用字体路径: {alt_font_path}, 存在: {os.path.exists(alt_font_path)}")
    
    # 字体优先级：江西拙楷2.0.ttf -> 备用路径 -> 系统中文字体
    if os.path.exists(font_path):
        font_to_use = font_path
        print(f"✅ 使用主字体路径: {font_path}")
    elif os.path.exists(alt_font_path):
        font_to_use = alt_font_path
        print(f"✅ 使用备用字体路径: {alt_font_path}")
    else:
        # macOS 系统中文字体路径
        system_fonts = [
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/PingFang.ttc',
            '/Library/Fonts/Arial Unicode.ttf'
        ]
        
        font_to_use = None
        for sys_font in system_fonts:
            if os.path.exists(sys_font):
                font_to_use = sys_font
                print(f"✅ 使用系统字体: {sys_font}")
                break
        
        if not font_to_use:
            # 最后的备选：使用不带路径的字体名称，让moviepy自己查找
            font_to_use = 'Helvetica'
            print(f"⚠️ 江西拙楷字体未找到，使用默认字体: {font_to_use}")
    
    print(f"🎨 字幕字体: {font_to_use}")
    
    for i, (segment, (start_time, end_time)) in enumerate(zip(segments, timings)):
        try:
            # 🔥 完全按照coze系统的TextClip参数设置
            txt_clip = TextClip(
                text=segment,  # 🔥 text参数在前
                font=font_to_use,  # 🔥 使用江西拙楷字体路径
                font_size=font_size,
                color=color,
                stroke_color=stroke_color,
                stroke_width=1,  # 🔥 与coze系统一致使用stroke_width=1
                size=(1000, None),  # 🔥 使用固定宽度
                method='caption'
            )
            
            # 🔥 使用coze系统的时间和位置设置
            txt_clip = txt_clip.with_start(start_time).with_end(end_time)
            txt_clip = txt_clip.with_position(("center", 0.7), relative=True)  # 🔥 使用相对位置
            
            subtitle_clips.append(txt_clip)
            print(f"✅ 创建字幕片段{i+1}: '{segment[:20]}...' ({start_time:.1f}s-{end_time:.1f}s)")
            
        except Exception as e:
            print(f"⚠️ 创建字幕片段{i+1}失败: {e}")
            print(f"   错误详情: {str(e)}")
            
            # 🔥 创建备用字幕片段 - 不使用自定义字体
            try:
                print(f"   尝试备用方案（无自定义字体）...")
                txt_clip = TextClip(
                    text=segment,
                    font_size=font_size,
                    color=color,
                    stroke_color=stroke_color,
                    stroke_width=1,
                    size=(1000, None),
                    method='caption'
                ).with_start(start_time).with_end(end_time).with_position(("center", 0.7), relative=True)
                subtitle_clips.append(txt_clip)
                print(f"✅ 创建备用字幕片段{i+1}")
            except Exception as e2:
                print(f"❌ 备用字幕片段{i+1}也失败: {e2}")
                
                # 🔥 最后的备用方案 - 最简单的TextClip
                try:
                    print(f"   尝试最简方案...")
                    txt_clip = TextClip(
                        text=segment,
                        font_size=font_size,
                        color=color
                    ).with_start(start_time).with_end(end_time).with_position(("center", 0.8), relative=True)
                    subtitle_clips.append(txt_clip)
                    print(f"✅ 创建最简字幕片段{i+1}")
                except Exception as e3:
                    print(f"❌ 最简字幕片段{i+1}也失败: {e3}")
                    continue
    
    return subtitle_clips


def add_subtitles_to_video(video_clip, text: str, duration: float = None,
                          font: str = "Arial", font_size: int = 36,
                          color: str = "white", position: str = "bottom") -> CompositeVideoClip:
    """
    为视频添加字幕（简化版接口）
    
    Args:
        video_clip: 视频剪辑
        text: 字幕文本
        duration: 视频时长（如果为None，使用video_clip的时长）
        font: 字体
        font_size: 字体大小
        color: 字体颜色
        position: 位置（bottom/center/top）
    
    Returns:
        合成后的视频
    """
    if duration is None:
        duration = video_clip.duration
    
    # 分割文本
    segments = split_text_for_progressive_subtitles(text)
    
    # 计算时间
    timings = calculate_progressive_subtitle_timings(duration, segments)
    
    # 创建字幕剪辑
    subtitle_clips = create_subtitle_clips(segments, timings, font, font_size, color)
    
    # 合成视频
    if subtitle_clips:
        all_clips = [video_clip] + subtitle_clips
        return CompositeVideoClip(all_clips)
    else:
        return video_clip
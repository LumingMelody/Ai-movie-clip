"""
自然语言视频剪辑功能
集成video_cut的DAG系统和自然语言处理能力
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
import uuid
from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip, AudioFileClip

# 添加video_cut到Python路径
video_cut_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'video_cut')
if video_cut_path not in sys.path:
    sys.path.insert(0, video_cut_path)

# 导入video_cut的组件
try:
    from video_cut.config import DAG, NODES
    from video_cut.core.controller import UnifiedController
    from video_cut.core.nl_processor import NLProcessor
except ImportError as e:
    print(f"警告：无法导入video_cut组件: {e}")
    # 提供降级方案
    DAG = None
    NODES = None
    UnifiedController = None
    NLProcessor = None

from core.clipgenerate.interface_function import download_file_from_url, upload_to_oss, get_file_info


def process_natural_language_video_edit(
    natural_language: str,
    video_url: str,
    output_duration: Optional[int] = None,
    style: Optional[str] = None,
    use_timeline_editor: bool = True
) -> Dict:
    """
    处理自然语言视频剪辑请求
    
    Args:
        natural_language: 自然语言描述
        video_url: 视频URL
        output_duration: 输出时长（秒）
        style: 视频风格
        use_timeline_editor: 是否使用时间轴编辑器
        
    Returns:
        处理结果字典
    """
    try:
        # 1. 下载视频文件
        print(f"🎬 [NL视频剪辑] 开始处理...")
        print(f"   描述: {natural_language}")
        print(f"   视频URL: {video_url}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="nl_video_edit_")
        video_path = os.path.join(temp_dir, "input_video.mp4")
        
        # 下载视频
        print(f"📥 下载视频文件...")
        download_file_from_url(video_url, video_path)
        
        # 获取视频信息
        video_info = get_file_info(video_path)
        print(f"📊 视频信息: 时长={video_info.get('duration')}秒, 分辨率={video_info.get('width')}x{video_info.get('height')}")
        
        # 2. 处理自然语言生成时间轴
        timeline_json = None
        
        if use_timeline_editor and NLProcessor and UnifiedController:
            print(f"🤖 使用高级时间轴编辑器...")
            
            # 使用video_cut的自然语言处理器
            controller = UnifiedController(DAG, NODES)
            
            # 构建输入
            user_input = {
                "type": "nl_generate",
                "natural_language": natural_language
            }
            
            # 生成时间轴
            result = controller.handle_input(user_input)
            
            # 获取最终时间轴
            if 'node12' in result:
                timeline_json = result['node12']
                print(f"✅ 时间轴生成成功")
                
                # 保存时间轴（调试用）
                timeline_path = os.path.join(temp_dir, "timeline.json")
                with open(timeline_path, 'w', encoding='utf-8') as f:
                    json.dump(timeline_json, f, ensure_ascii=False, indent=2)
        else:
            print(f"⚠️ 时间轴编辑器不可用，使用简单剪辑模式")
        
        # 3. 根据时间轴执行视频剪辑
        output_path = os.path.join(temp_dir, "output_video.mp4")
        
        if timeline_json:
            # 基于时间轴的高级剪辑
            output_path = execute_timeline_edit(video_path, timeline_json, output_path, temp_dir)
        else:
            # 简单剪辑模式
            output_path = execute_simple_edit(
                video_path, 
                natural_language, 
                output_path, 
                output_duration, 
                style
            )
        
        # 4. 上传结果
        print(f"📤 上传处理后的视频...")
        oss_url = upload_to_oss(output_path)
        
        # 获取输出视频信息
        output_info = get_file_info(output_path)
        
        # 5. 构建返回结果
        result = {
            "success": True,
            "video_url": oss_url,
            "timeline": timeline_json,
            "video_info": {
                "duration": output_info.get("duration", 0),
                "width": output_info.get("width", 1920),
                "height": output_info.get("height", 1080),
                "fps": output_info.get("fps", 30)
            },
            "process_info": {
                "natural_language": natural_language,
                "used_timeline_editor": use_timeline_editor and timeline_json is not None,
                "original_duration": video_info.get("duration", 0)
            }
        }
        
        # 清理临时文件
        shutil.rmtree(temp_dir)
        
        print(f"✅ [NL视频剪辑] 处理完成!")
        return result
        
    except Exception as e:
        print(f"❌ [NL视频剪辑] 处理失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理临时文件
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        
        return {
            "success": False,
            "error": str(e),
            "video_url": None
        }


def execute_timeline_edit(video_path: str, timeline_json: Dict, output_path: str, temp_dir: str) -> str:
    """
    基于时间轴执行视频剪辑
    
    Args:
        video_path: 输入视频路径
        timeline_json: 时间轴JSON
        output_path: 输出路径
        temp_dir: 临时目录
        
    Returns:
        输出视频路径
    """
    try:
        print(f"🎬 执行基于时间轴的视频剪辑...")
        
        # 加载原始视频
        video = VideoFileClip(video_path)
        
        # 解析时间轴
        timeline = timeline_json.get("timeline", {})
        total_duration = timeline.get("duration", 60)
        fps = timeline.get("fps", 30)
        
        # 收集所有视频片段
        clips = []
        
        # 处理视频轨道
        for track in timeline.get("tracks", []):
            if track.get("type") == "video":
                for clip_info in track.get("clips", []):
                    start = clip_info.get("start", 0)
                    end = clip_info.get("end", 10)
                    
                    # 确保不超过原视频长度
                    if start < video.duration:
                        clip_end = min(end, video.duration)
                        if clip_end > start:
                            # 创建子片段
                            subclip = video.subclip(start, clip_end)
                            
                            # 设置持续时间
                            subclip = subclip.set_duration(end - start)
                            
                            clips.append((start, subclip))
        
        # 如果没有片段，使用整个视频
        if not clips:
            print(f"⚠️ 时间轴中没有视频片段，使用完整视频")
            if total_duration and total_duration < video.duration:
                video = video.subclip(0, total_duration)
            video.write_videofile(output_path, fps=fps)
        else:
            # 按时间排序片段
            clips.sort(key=lambda x: x[0])
            
            # 提取视频片段
            video_clips = [clip[1] for clip in clips]
            
            # 连接片段
            final_video = concatenate_videoclips(video_clips)
            
            # 限制总时长
            if total_duration and final_video.duration > total_duration:
                final_video = final_video.subclip(0, total_duration)
            
            # 输出视频
            final_video.write_videofile(output_path, fps=fps)
            final_video.close()
        
        video.close()
        
        print(f"✅ 视频剪辑完成: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ 时间轴剪辑失败: {e}")
        # 降级到简单剪辑
        return execute_simple_edit(video_path, "", output_path, None, None)


def execute_simple_edit(
    video_path: str, 
    natural_language: str, 
    output_path: str,
    output_duration: Optional[int] = None,
    style: Optional[str] = None
) -> str:
    """
    执行简单的视频剪辑
    
    Args:
        video_path: 输入视频路径
        natural_language: 自然语言描述
        output_path: 输出路径
        output_duration: 输出时长
        style: 视频风格
        
    Returns:
        输出视频路径
    """
    try:
        print(f"🎬 执行简单视频剪辑...")
        
        # 加载视频
        video = VideoFileClip(video_path)
        
        # 解析自然语言中的时长
        if not output_duration:
            # 尝试从描述中提取时长
            import re
            duration_match = re.search(r'(\d+)\s*分钟', natural_language)
            if duration_match:
                output_duration = int(duration_match.group(1)) * 60
            else:
                duration_match = re.search(r'(\d+)\s*秒', natural_language)
                if duration_match:
                    output_duration = int(duration_match.group(1))
                else:
                    output_duration = 60  # 默认60秒
        
        print(f"📏 目标时长: {output_duration}秒")
        
        # 裁剪视频
        if output_duration < video.duration:
            # 简单策略：取视频的前N秒
            video = video.subclip(0, output_duration)
        
        # 应用简单效果（根据风格）
        if style:
            if "快" in style or "动感" in style:
                # 稍微加速
                video = video.speedx(1.1)
            elif "慢" in style or "温馨" in style:
                # 稍微减速
                video = video.speedx(0.9)
        
        # 输出视频
        video.write_videofile(output_path, fps=30)
        video.close()
        
        print(f"✅ 简单剪辑完成: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ 简单剪辑失败: {e}")
        raise


# 测试函数
def test_natural_language_edit():
    """测试自然语言视频剪辑"""
    test_cases = [
        {
            "natural_language": "制作一个30秒的产品介绍视频，要有动感音乐",
            "video_url": "https://example.com/test.mp4",
            "use_timeline_editor": True
        },
        {
            "natural_language": "剪辑一个1分钟的vlog，温馨风格",
            "video_url": "https://example.com/test2.mp4",
            "output_duration": 60,
            "style": "温馨"
        }
    ]
    
    for case in test_cases:
        print(f"\n测试用例: {case}")
        result = process_natural_language_video_edit(**case)
        print(f"结果: {result}")


if __name__ == "__main__":
    test_natural_language_edit()
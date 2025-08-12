"""
自然语言视频剪辑功能
完整集成video_cut的功能，支持时间轴生成、视频剪辑、特效添加等
"""
import os
import sys
import json
import tempfile
import shutil
import traceback
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import uuid
from datetime import datetime
import urllib.request

# 添加项目根路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入video_cut的组件
try:
    from video_cut.unified_nl_processor import UnifiedNLProcessor
    from video_cut.timeline_generator import TimelineGenerator
    from video_cut.video_editor import VideoEditor
    from video_cut.utils.resource_manager import ResourceManager
    from video_cut.utils.validators import InputValidator, ErrorHandler
    VIDEO_CUT_AVAILABLE = True
except ImportError as e:
    print(f"警告：无法导入video_cut组件: {e}")
    VIDEO_CUT_AVAILABLE = False
    UnifiedNLProcessor = None
    TimelineGenerator = None
    VideoEditor = None
    ResourceManager = None

from core.clipgenerate.interface_function import download_file_from_url, upload_to_oss, get_file_info, OSS_BUCKET_NAME, OSS_ENDPOINT

# 导入moviepy用于简单剪辑
try:
    from moviepy import VideoFileClip, concatenate_videoclips
except ImportError:
    VideoFileClip = None
    concatenate_videoclips = None


def process_natural_language_video_edit(
    natural_language: str,
    video_url: str,
    output_duration: Optional[int] = None,
    style: Optional[str] = None,
    use_timeline_editor: bool = True,
    use_ai: bool = True,
    template: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理自然语言视频剪辑请求 - 完整集成video_cut功能
    
    Args:
        natural_language: 自然语言描述
        video_url: 视频URL
        output_duration: 输出时长（秒）
        style: 视频风格
        use_timeline_editor: 是否使用时间轴编辑器
        use_ai: 是否使用AI处理器
        template: 视频模板类型
        use_timeline_editor: 是否使用时间轴编辑器
        
    Returns:
        处理结果字典
    """
    temp_files = []
    resource_manager = None
    
    try:
        print(f"🎬 [NL视频剪辑] 开始处理...")
        print(f"   描述: {natural_language[:100]}...")
        print(f"   视频URL: {video_url}")
        print(f"   使用AI: {use_ai}")
        print(f"   模板: {template}")
        
        # 检查video_cut是否可用
        if not VIDEO_CUT_AVAILABLE:
            return {
                "success": False,
                "error": "video_cut模块不可用，请检查安装",
                "error_type": "module_error"
            }
        
        # 步骤1: 验证输入
        try:
            natural_language = InputValidator.validate_natural_language(natural_language)
            if output_duration:
                output_duration = InputValidator.validate_duration(output_duration)
        except ValueError as e:
            return {
                "success": False,
                "error": f"输入验证失败: {e}",
                "error_type": "validation_error"
            }
        
        # 从描述中提取时长
        if not output_duration:
            import re
            duration_match = re.search(r'(\d+)秒|(\d+)s|(\d+)分钟?', natural_language)
            if duration_match:
                if duration_match.group(1):
                    output_duration = int(duration_match.group(1))
                elif duration_match.group(2):
                    output_duration = int(duration_match.group(2))
                elif duration_match.group(3):
                    output_duration = int(duration_match.group(3)) * 60
        
        # 默认时长30秒
        output_duration = output_duration or 30
        
        # 步骤2: 下载视频到本地
        print(f"📥 下载视频文件...")
        temp_dir = tempfile.mkdtemp(prefix="nl_video_edit_")
        video_path = download_video_for_edit(video_url, temp_dir)
        temp_files.append(video_path)
        
        # 获取视频信息
        video_info = get_file_info(video_path)
        actual_duration = video_info.get('duration', output_duration)
        output_duration = min(output_duration, actual_duration) if actual_duration else output_duration
        
        print(f"📊 视频信息: 时长={actual_duration}秒, 输出时长={output_duration}秒")
        
        # 步骤3: 初始化资源管理器
        resource_manager = ResourceManager(auto_cleanup=True)
        video_resource = resource_manager.add_resource(
            video_path,
            resource_type="video",
            copy=False
        )
        
        # 步骤4: 生成时间轴
        timeline_json = None
        
        if use_timeline_editor:
            print(f"🤖 使用高级时间轴编辑器...")
            
            # 使用统一的NL处理器
            nl_processor = UnifiedNLProcessor(use_ai=use_ai, cache_enabled=True)
            
            # 增强描述
            enhanced_description = f"{natural_language}，时长{output_duration}秒"
            if style:
                enhanced_description += f"，风格{style}"
            
            # 生成时间轴
            timeline_json = nl_processor.process(enhanced_description, mode="auto", duration=output_duration)
            
            # 🔥 调试：检查生成的时间轴是否包含转场效果
            if timeline_json and timeline_json.get("metadata"):
                transition_effect = timeline_json["metadata"].get("transition_effect")
                if transition_effect:
                    print(f"✅ 时间轴包含转场效果: {transition_effect}")
                else:
                    print(f"⚠️ 时间轴未包含转场效果，检查metadata: {timeline_json['metadata']}")
            
            # 如果有模板，进一步优化
            if template and timeline_json:
                generator = TimelineGenerator()
                config = {
                    "title": timeline_json.get("metadata", {}).get("title", "视频"),
                    "duration": output_duration,
                    "template": template,
                    "resolution": timeline_json["timeline"]["resolution"],
                    "fps": timeline_json["timeline"]["fps"]
                }
                timeline_json = generator.generate_advanced_timeline(config)
                timeline_json = generator.optimize_timeline(timeline_json)
            
            # 保存时间轴
            if timeline_json:
                timeline_path = os.path.join(temp_dir, "timeline.json")
                with open(timeline_path, 'w', encoding='utf-8') as f:
                    json.dump(timeline_json, f, ensure_ascii=False, indent=2)
                print(f"✅ 时间轴生成成功: {timeline_path}")
        
        if not timeline_json:
            print(f"⚠️ 使用简单时间轴模式...")
            timeline_json = create_simple_timeline(
                natural_language, str(video_resource), output_duration, style
            )
        
        # 更新时间轴的视频源
        # 如果描述中有转场需求，使用智能转场
        if "转场" in natural_language or "过渡" in natural_language or "transition" in natural_language.lower():
            update_timeline_video_source_with_smart_transitions(timeline_json, str(video_resource), output_duration)
        else:
            update_timeline_video_source(timeline_json, str(video_resource), output_duration)
        
        # 步骤5: 执行视频剪辑
        output_path = os.path.join(temp_dir, "output_video.mp4")
        temp_files.append(output_path)
        
        print(f"🎬 执行视频剪辑...")
        
        # 使用VideoEditor执行剪辑
        editor = VideoEditor(
            resource_dir=str(resource_manager.base_dir),
            enable_memory_optimization=True
        )
        
        success = editor.execute_timeline(timeline_json, output_path)
        
        if not success:
            # 如果高级剪辑失败，尝试简单剪辑
            print(f"⚠️ 高级剪辑失败，尝试简单剪辑...")
            
            # 确保video_path指向resource_manager中的实际文件
            if video_resource:
                actual_video_path = str(video_resource)  # video_resource 是 PosixPath 对象
            else:
                actual_video_path = video_path
                
            # 检查文件是否存在
            if not os.path.exists(actual_video_path):
                print(f"❌ 视频文件不存在: {actual_video_path}")
                # 尝试重新下载
                print(f"📥 重新下载视频...")
                actual_video_path = download_video_for_edit(video_url, temp_dir)
            
            output_path = execute_simple_edit(
                actual_video_path, natural_language, output_path, output_duration, style
            )
        
        # 步骤6: 上传结果
        print(f"📤 上传处理后的视频...")
        # 生成OSS路径
        oss_filename = f"nl_video/{datetime.now().strftime('%Y%m%d')}/{os.path.basename(output_path)}"
        upload_to_oss(output_path, oss_filename)
        # 使用正确的OSS URL格式
        oss_url = f"https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/{oss_filename}"
        
        # 获取输出视频信息
        output_info = get_file_info(output_path)
        
        # 🔥 步骤6.5: 保存时间轴到固定目录
        timeline_save_path = None
        if timeline_json:
            # 创建时间轴保存目录
            timeline_dir = os.path.join(os.getcwd(), "output", "timelines")
            os.makedirs(timeline_dir, exist_ok=True)
            
            # 生成时间轴文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timeline_filename = f"timeline_{timestamp}.json"
            timeline_save_path = os.path.join(timeline_dir, timeline_filename)
            
            # 保存时间轴
            try:
                with open(timeline_save_path, 'w', encoding='utf-8') as f:
                    json.dump(timeline_json, f, ensure_ascii=False, indent=2)
                print(f"📋 时间轴已保存: {timeline_save_path}")
            except Exception as e:
                print(f"⚠️ 时间轴保存失败: {e}")
                timeline_save_path = None

        # 步骤7: 构建返回结果
        result = {
            "success": True,
            "video_url": oss_url,
            "timeline": timeline_json,
            "video_info": {
                "duration": output_info.get("duration", output_duration),
                "original_duration": actual_duration,
                "width": output_info.get("width", 1920),
                "height": output_info.get("height", 1080),
                "fps": output_info.get("fps", 30),
                "style": style or "auto"
            },
            "process_info": {
                "engine": "video_cut",
                "natural_language": natural_language,
                "used_timeline_editor": use_timeline_editor,
                "used_ai": use_ai,
                "template": template,
                "timeline_path": timeline_save_path,  # 🔥 返回永久保存的路径
                "created_at": datetime.now().isoformat()
            }
        }
        
        print(f"✅ [NL视频剪辑] 处理完成! 输出: {oss_url}")
        return result
        
    except Exception as e:
        print(f"❌ [NL视频剪辑] 处理失败: {e}")
        traceback.print_exc()
        
        # 使用错误处理器
        error_info = ErrorHandler.handle_video_processing_error(e) if VIDEO_CUT_AVAILABLE else {"error": str(e), "message": str(e)}
        
        return {
            "success": False,
            "error": error_info.get("error", str(e)),
            "error_message": error_info.get("message", ""),
            "error_type": "processing_error",
            "suggestion": error_info.get("suggestion", ""),
            "video_url": None
        }
    
    finally:
        # 清理临时文件
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # 清理资源管理器
        if resource_manager:
            resource_manager.cleanup_temp_files()


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
                            subclipped = video.subclipped(start, clip_end)
                            
                            # 设置持续时间
                            subclipped = subclipped.set_duration(end - start)
                            
                            clips.append((start, subclipped))
        
        # 如果没有片段，使用整个视频
        if not clips:
            print(f"⚠️ 时间轴中没有视频片段，使用完整视频")
            if total_duration and total_duration < video.duration:
                video = video.subclipped(0, total_duration)
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
                final_video = final_video.subclipped(0, total_duration)
            
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


def download_video_for_edit(video_url: str, temp_dir: str) -> str:
    """下载视频用于编辑"""
    video_path = os.path.join(temp_dir, "input_video.mp4")
    
    # 检查是否是OSS URL
    if "aliyuncs.com" in video_url or "oss-" in video_url:
        download_file_from_url(video_url, video_path)
    else:
        # 普通URL下载
        try:
            urllib.request.urlretrieve(video_url, video_path)
        except:
            import requests
            response = requests.get(video_url, stream=True)
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    
    return video_path


def create_simple_timeline(description: str, video_source: str, duration: int, style: Optional[str] = None) -> Dict:
    """创建简单的时间轴"""
    import random
    filters = []
    if "淡入" in description or "fade" in description.lower():
        filters.append("fade_in")
    if "淡出" in description or "fade" in description.lower():
        filters.append("fade_out")
    
    # 处理转场效果
    if "转场" in description or "过渡" in description or "transition" in description.lower():
        # 随机选择一个转场效果
        # 🔥 注意：rotate不是转场效果，是滤镜效果，所以移除
        transition_effects = [
            "zoom_in",
            "zoom_out", 
            "pan_left",
            "pan_right",
            # "rotate",  # 移除，这是滤镜不是转场
            "shake",
            "glitch"
        ]
        selected_transition = random.choice(transition_effects)
        filters.append(selected_transition)
        print(f"🎬 随机选择转场效果: {selected_transition}")
    
    # 确保video_source是绝对路径
    if not os.path.isabs(video_source):
        video_source = os.path.abspath(video_source)
    
    print(f"🎬 创建时间轴，视频源: {video_source}")
    print(f"📏 时长: {duration}秒")
    
    timeline = {
        "version": "1.0",
        "metadata": {
            "title": "自然语言剪辑",
            "description": description,
            "created_at": datetime.now().isoformat()
        },
        "timeline": {
            "duration": duration,
            "fps": 30,
            "resolution": {"width": 1920, "height": 1080},
            "tracks": [
                {
                    "type": "video",
                    "name": "主视频轨",
                    "clips": [{
                        "start": 0,
                        "end": duration,
                        "source": video_source,
                        "clip_in": 0,
                        "clip_out": duration,
                        "filters": filters,
                        "transform": {
                            "scale": 1.0,
                            "position": ["center", "center"],
                            "rotation": 0
                        }
                    }]
                }
            ]
        }
    }
    
    # 添加字幕轨道
    if "字幕" in description or "文字" in description:
        # 提取文本用于字幕
        subtitle_text = description if len(description) > 10 else "精彩内容分享"
        
        timeline["timeline"]["tracks"].append({
            "type": "text",
            "name": "字幕轨",
            "clips": [{
                "start": 2,
                "end": duration - 2,
                "content": {
                    "text": subtitle_text,
                    "font": "江西拙楷2.0.ttf",  # 🔥 使用江西拙楷字体
                    "size": 40,  # 🔥 与coze系统一致的字体大小
                    "color": "#FFFF00",  # 🔥 使用黄色（与coze系统一致）
                    "stroke_color": "#000000",
                    "stroke_width": 1,  # 🔥 与coze系统一致的描边宽度
                    "position": "bottom",
                    "progressive": True,  # 启用渐进式字幕
                    "max_chars_per_line": 25,
                    "max_lines": 2
                }
            }]
        })
    
    return timeline


def update_timeline_video_source_with_smart_transitions(timeline: Dict, video_source: str, duration: int):
    """更新时间轴并添加智能转场 - 符合AuraRender设计方案"""
    try:
        from video_cut.aura_render.scene_splitter import SceneSplitter
        
        # 使用场景分割器
        splitter = SceneSplitter()
        
        # 🔥 检查metadata中是否有指定的转场效果
        specified_transition = timeline.get("metadata", {}).get("transition_effect")
        
        # 分割场景（默认3个片段）
        segments = splitter.split_by_duration(duration, target_segments=3)
        
        # 如果有指定的转场效果（如叶片翻转），使用它
        if specified_transition == "leaf_flip_transition":
            print(f"   🎬 使用指定的叶片翻转转场效果")
            # 手动设置叶片翻转转场
            for i, segment in enumerate(segments):
                if i > 0:  # 不是第一个片段
                    segment["transition_in"] = {
                        "type": "leaf_flip",
                        "duration": 1.0,
                        "start_time": segment["start"]
                    }
                if i < len(segments) - 1:  # 不是最后一个片段
                    segment["transition_out"] = {
                        "type": "leaf_flip",
                        "duration": 1.0,
                        "start_time": segment["end"] - 1.0
                    }
        else:
            # 使用默认的智能转场
            print(f"   ⚠️ 没有指定转场效果，使用默认转场")
            segments = splitter.add_transitions(segments, transition_duration=1.0)
        
        # 更新时间轴
        for track in timeline.get("timeline", {}).get("tracks", []):
            if track["type"] == "video":
                # 保存原始片段的属性（如果存在）
                original_attrs = {}
                if track.get("clips") and len(track["clips"]) > 0:
                    first_clip = track["clips"][0]
                    # 收集需要保留的属性
                    # 🔥 重要：不要保留filters，因为转场不应该作为滤镜
                    for key in ["artistic_style", "color_grading", "audio_style", "text_style"]:
                        if key in first_clip:
                            original_attrs[key] = first_clip[key]
                    # 如果没有单独的transform，使用第一个片段的
                    if "transform" in first_clip:
                        original_attrs["transform"] = first_clip["transform"]
                    
                    # 🔥 只保留非转场相关的滤镜
                    if "filters" in first_clip and first_clip["filters"]:
                        # 过滤掉可能错误添加的转场效果
                        non_transition_filters = [
                            f for f in first_clip["filters"] 
                            if f not in ["rotate", "zoom_in", "zoom_out", "pan_left", "pan_right", "shake", "glitch"]
                        ]
                        if non_transition_filters:
                            original_attrs["filters"] = non_transition_filters
                        print(f"   🔍 原始滤镜: {first_clip.get('filters', [])}, 保留: {non_transition_filters if non_transition_filters else '无'}")
                
                # 生成新的片段列表，保留原始属性
                new_clips = splitter.generate_timeline_clips(segments, video_source, original_attrs)
                
                track["clips"] = new_clips
                print(f"   🎬 应用智能场景分割: {len(new_clips)}个片段")
                
                # 如果有艺术风格，显示出来
                if original_attrs.get("artistic_style"):
                    print(f"      🎨 保留艺术风格: {original_attrs['artistic_style']}")
                
                for i, clip in enumerate(new_clips):
                    if "transition_in" in clip:
                        print(f"      片段{i+1} 进入转场: {clip['transition_in']['type']}")
                    if "transition_out" in clip:
                        print(f"      片段{i+1} 退出转场: {clip['transition_out']['type']}")
                break
    except ImportError:
        # 如果没有SceneSplitter，使用原来的逻辑
        print("⚠️ SceneSplitter未找到，使用简单模式")
        update_timeline_video_source(timeline, video_source, duration)

def update_timeline_video_source(timeline: Dict, video_source: str, duration: int):
    """更新时间轴中的视频源和时长"""
    import random
    if not timeline:
        return
    
    print(f"🔧 更新时间轴: 视频源={video_source}, 目标时长={duration}秒")
    
    # 可用的转场效果列表
    # 🔥 注意：rotate不是转场效果，是滤镜效果，所以移除
    transition_effects = [
        "zoom_in",
        "zoom_out", 
        "pan_left",
        "pan_right",
        # "rotate",  # 移除，这是滤镜不是转场
        "shake",
        "glitch"
    ]
    
    for track in timeline.get("timeline", {}).get("tracks", []):
        if track["type"] == "video":
            for clip in track.get("clips", []):
                # 更新视频源
                if not clip.get("source"):
                    clip["source"] = video_source
                
                # 处理转场效果
                if "filters" in clip and clip["filters"]:
                    new_filters = []
                    for filter_name in clip["filters"]:
                        if filter_name == "transition_001" or filter_name == "transition":
                            # 随机选择一个转场效果
                            selected_transition = random.choice(transition_effects)
                            new_filters.append(selected_transition)
                            print(f"   🎬 随机选择转场效果: {selected_transition}")
                        else:
                            new_filters.append(filter_name)
                    clip["filters"] = new_filters
                
                # 🔥 修复时长逻辑：如果目标duration更大，则扩展clip时长
                current_end = clip.get("end", 0)
                current_clip_out = clip.get("clip_out", current_end)
                
                print(f"   片段原始时长: end={current_end}, clip_out={current_clip_out}")
                
                # 如果期望时长大于当前时长，则扩展到期望时长
                if duration > current_end:
                    clip["end"] = duration
                    print(f"   扩展end: {current_end} -> {duration}")
                
                if duration > current_clip_out:
                    clip["clip_out"] = duration
                    print(f"   扩展clip_out: {current_clip_out} -> {duration}")
                
                # 确保clipOut不小于end
                clip["clipOut"] = max(clip.get("clipOut", clip["end"]), clip["end"])
    
    # 🔥 更新总时长：使用max确保不会缩短时长
    original_duration = timeline["timeline"].get("duration", 0)
    timeline["timeline"]["duration"] = max(original_duration, duration)
    print(f"   时间轴总时长: {original_duration} -> {timeline['timeline']['duration']}")


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
            video = video.subclipped(0, output_duration)
        
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
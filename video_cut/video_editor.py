"""
视频剪辑执行器
根据生成的时间轴JSON执行实际的视频剪辑操作
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from tqdm import tqdm
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips, ImageClip, ColorClip

# 添加性能优化和验证工具
try:
    from .utils.performance import MemoryManager, ChunkedVideoProcessor, StreamingProcessor
    from .utils.validators import InputValidator, ResourceValidator, ErrorHandler
    from .utils.subtitle_utils import (
        split_text_for_progressive_subtitles,
        calculate_progressive_subtitle_timings,
        create_subtitle_clips
    )
    SUBTITLE_UTILS_AVAILABLE = True
except ImportError:
    # 临时占位
    class MemoryManager:
        def check_memory_usage(self): return {"available": 999}
        def optimize_for_memory(self, d, r, f): return {"chunk_size": None}
    class ChunkedVideoProcessor:
        def __init__(self): pass
    class InputValidator:
        @staticmethod
        def validate_timeline(t): return t
    class ResourceValidator:
        @staticmethod
        def check_resource_availability(r): return {"videos": [], "audios": [], "images": []}
    SUBTITLE_UTILS_AVAILABLE = False

# 导入艺术风格系统
try:
    from video_cut.aura_render.intelligent_layer.artistic_styles import ArtisticStyleSystem
    from video_cut.aura_render.filters.style_filters import StyleFilterEngine
    STYLE_SYSTEM_AVAILABLE = True
except ImportError:
    STYLE_SYSTEM_AVAILABLE = False

# MoviePy 2.x imports
try:
    from moviepy.video.fx.Resize import Resize
    from moviepy.video.fx.FadeIn import FadeIn
    from moviepy.video.fx.FadeOut import FadeOut
    from moviepy.video.fx.Rotate import Rotate
    from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
    from moviepy.audio.fx.AudioFadeOut import AudioFadeOut
    from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
except ImportError:
    # Fallback for older versions
    from moviepy.video.fx import resize as Resize, fadein as FadeIn, fadeout as FadeOut, rotate as Rotate
    from moviepy.audio.fx import audio_fadein as AudioFadeIn, audio_fadeout as AudioFadeOut, volumex as MultiplyVolume
import numpy as np


class VideoEditor:
    """视频剪辑执行器"""
    
    def __init__(self, resource_dir: str = "./resources", enable_memory_optimization: bool = True):
        """
        初始化视频编辑器
        
        Args:
            resource_dir: 资源文件目录（视频、音频、图片等）
            enable_memory_optimization: 是否启用内存优化
        """
        self.resource_dir = Path(resource_dir)
        self.logger = self._setup_logger()
        self.memory_manager = MemoryManager() if enable_memory_optimization else None
        self.chunk_processor = ChunkedVideoProcessor()
        
        # 检查资源可用性
        self.available_resources = ResourceValidator.check_resource_availability(str(self.resource_dir))
        self.logger.info(f"可用资源: {len(self.available_resources['videos'])}个视频, "
                        f"{len(self.available_resources['audios'])}个音频, "
                        f"{len(self.available_resources['images'])}个图片")
        
        # 初始化艺术风格系统
        if STYLE_SYSTEM_AVAILABLE:
            self.style_system = ArtisticStyleSystem()
            self.style_filter_engine = StyleFilterEngine()
        else:
            self.style_system = None
            self.style_filter_engine = None
        
        # 特效映射
        self.effect_mapping = {
            "blur": self._apply_blur,
            "glow": self._apply_glow,
            "particle": self._apply_particle,
            "fade": self._apply_fade,
            "zoom": self._apply_zoom,
            "rotate": self._apply_rotate,
            "shake": self._apply_shake,
            "color_correct": self._apply_color_correct
        }
        
        # 转场映射
        self.transition_mapping = {
            "fade_in": lambda clip, duration: clip.with_effects([FadeIn(duration)]),
            "fade_out": lambda clip, duration: clip.with_effects([FadeOut(duration)]),
            "fade": lambda clip, duration: clip.with_effects([FadeIn(duration)]),
            "cross_fade": self._cross_fade,
            "cut": lambda clip, duration: clip,  # 硬切
            "slide": self._slide_transition,
            "zoom": self._zoom_transition,
            # 添加easy_clip_effects中的转场效果
            "zoom_in": self._apply_zoom_in_transition,
            "zoom_out": self._apply_zoom_out_transition,
            "pan_left": self._apply_pan_left_transition,
            "pan_right": self._apply_pan_right_transition,
            # 添加slide_in系列的映射
            "slide_in_left": self._apply_pan_left_transition,  # 映射到pan_left
            "slide_in_right": self._apply_pan_right_transition,  # 映射到pan_right
            "slide_left": self._apply_pan_left_transition,  # 额外别名
            "slide_right": self._apply_pan_right_transition,  # 额外别名
            "rotate": self._apply_rotate_transition,
            "shake": self._apply_shake_transition,
            "glitch": self._apply_glitch_transition,
            # 🔥 添加叶片翻转转场和其他转场效果
            "leaf_flip": self._apply_leaf_flip_transition,
            "叶片翻转": self._apply_leaf_flip_transition,
            "blinds": self._apply_blinds_transition,
            "百叶窗": self._apply_blinds_transition,
            "wind_blow": self._apply_wind_blow_transition,
            "风吹": self._apply_wind_blow_transition,
            "rotate_zoom": self._apply_rotate_zoom_transition,
            "旋转放大": self._apply_rotate_zoom_transition,
            "hexagon": self._apply_hexagon_transition,
            "六角形": self._apply_hexagon_transition,
            "circle_open": self._apply_circle_open_transition,
            "圆形打开": self._apply_circle_open_transition,
            "heart_open": self._apply_heart_open_transition,
            "心形打开": self._apply_heart_open_transition,
            "dream_zoom": self._apply_dream_zoom_transition,
            "梦幻放大": self._apply_dream_zoom_transition,
            "clock_sweep": self._apply_clock_sweep_transition,
            "时钟扫描": self._apply_clock_sweep_transition
        }

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("VideoEditor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def execute_timeline(self, timeline_json: Dict, output_path: str) -> bool:
        """
        执行时间轴剪辑
        
        Args:
            timeline_json: 时间轴JSON数据
            output_path: 输出视频路径
            
        Returns:
            是否成功
        """
        try:
            self.logger.info("开始处理时间轴...")
            
            # 解析时间轴
            timeline = timeline_json.get("timeline", {})
            duration = timeline.get("duration", 60)
            fps = timeline.get("fps", 30)
            resolution = timeline.get("resolution", {"width": 1920, "height": 1080})
            
            # 检查转场效果
            transition_effect = timeline_json.get("metadata", {}).get("transition_effect")
            
            # 处理各个轨道
            video_clips = []
            audio_clips = []
            text_clips = []
            
            for track in timeline.get("tracks", []):
                track_type = track.get("type")
                
                if track_type == "video":
                    video_clips.extend(self._process_video_track(track, resolution))
                elif track_type == "audio":
                    audio_clips.extend(self._process_audio_track(track))
                elif track_type == "text":
                    text_clips.extend(self._process_text_track(track, resolution))
            
            # 合成最终视频
            final_video = self._composite_video(video_clips, text_clips, audio_clips, duration, resolution, fps, transition_effect)
            
            # 输出视频
            self.logger.info(f"正在输出视频到: {output_path}")
            
            # 保存实际使用的时间轴到output目录
            import os
            output_dir = os.path.dirname(output_path)
            timeline_save_path = os.path.join(output_dir, "actual_timeline_used.json")
            try:
                with open(timeline_save_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(timeline_json, f, ensure_ascii=False, indent=2)
                self.logger.info(f"实际使用的时间轴已保存到: {timeline_save_path}")
            except Exception as e:
                self.logger.warning(f"保存时间轴失败: {e}")
            
            # 输出时间轴调试信息
            self.logger.info("=== 时间轴调试信息 ===")
            self.logger.info(f"视频时长: {duration}秒")
            self.logger.info(f"输出分辨率: {resolution['width']}x{resolution['height']}")
            self.logger.info(f"帧率: {fps}fps")
            self.logger.info(f"视频片段数量: {len(video_clips)}")
            self.logger.info(f"音频片段数量: {len(audio_clips)}")
            self.logger.info(f"文字片段数量: {len(text_clips)}")
            
            # 详细输出完整的时间轴信息
            self.logger.info("=== 完整时间轴内容 ===")
            for i, track in enumerate(timeline.get("tracks", [])):
                self.logger.info(f"轨道 {i}: 类型={track.get('type')}, 名称={track.get('name', 'N/A')}, 片段数={len(track.get('clips', []))}")
                for j, clip in enumerate(track.get("clips", [])):
                    clip_info = f"  片段 {j}: {clip.get('start', 0)}-{clip.get('end', 0)}秒"
                    if clip.get('source'):
                        clip_info += f", 源={clip.get('source')}"
                    if clip.get('content'):
                        content = clip.get('content')
                        if content.get('text'):
                            clip_info += f", 文字='{content.get('text')[:20]}...'"
                        if content.get('source'):
                            clip_info += f", 音频源={content.get('source')}"
                    if clip.get('filters'):
                        clip_info += f", 滤镜={clip.get('filters')}"
                    if clip.get('artistic_style'):
                        clip_info += f", 🎨艺术风格={clip.get('artistic_style')}"
                    self.logger.info(clip_info)
            self.logger.info("====================")
            
            # 使用固定码率来确保质量
            ffmpeg_params = [
                '-b:v', '2000k',      # 视频码率2Mbps
                '-minrate', '1800k',  # 最小码率
                '-maxrate', '2200k',  # 最大码率  
                '-bufsize', '4000k',  # 缓冲区大小
                '-b:a', '128k',       # 音频码率128k
                '-preset:v', 'fast',  # 明确指定视频预设避免截断问题
                '-profile:v', 'high', # 使用高质量profile
                '-level:v', '4.0'     # H.264 level
            ]
            
            self.logger.info(f"使用ffmpeg参数: {' '.join(ffmpeg_params)}")
            
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                ffmpeg_params=ffmpeg_params,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None
            )
            
            # 清理资源
            final_video.close()
            
            self.logger.info("视频剪辑完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"视频剪辑失败: {e}")
            return False

    def _process_video_track(self, track: Dict, resolution: Dict) -> List:
        """处理视频轨道"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                # 获取视频源
                source = clip_data.get("source", "")
                if not source:
                    # 如果没有源文件，创建纯色片段
                    self.logger.warning(f"片段缺少视频源，创建黑屏片段")
                    clip = self._create_color_clip(
                        duration=clip_data["end"] - clip_data["start"],
                        resolution=resolution,
                        color=(0, 0, 0)
                    )
                else:
                    # 处理视频路径
                    # 首先检查是否是绝对路径
                    if os.path.isabs(source):
                        video_path = Path(source)
                    else:
                        # 相对路径，在资源目录中查找
                        video_path = self.resource_dir / source
                    
                    # 如果还不存在，尝试直接使用源路径
                    if not video_path.exists():
                        video_path = Path(source)
                    
                    if video_path.exists():
                        self.logger.info(f"加载视频: {video_path}")
                        clip = VideoFileClip(str(video_path))
                    else:
                        self.logger.error(f"视频文件不存在: {video_path}，尝试的源路径: {source}")
                        # 创建占位片段而不是跳过
                        clip = self._create_color_clip(
                            duration=clip_data["end"] - clip_data["start"],
                            resolution=resolution,
                            color=(50, 50, 50)  # 灰色表示缺失
                        )
                
                # 首先调整视频尺寸以匹配输出分辨率
                # 获取原始视频尺寸
                if hasattr(clip, 'size'):
                    original_w, original_h = clip.size
                    target_w, target_h = resolution["width"], resolution["height"]
                    
                    self.logger.info(f"视频尺寸处理: 原始={original_w}x{original_h}, 目标={target_w}x{target_h}")
                    
                    # 🔥 检查是否需要缩放 - 如果原始尺寸与目标不匹配
                    if original_w != target_w or original_h != target_h:
                        # 计算缩放比例，保持宽高比，使用较大的比例确保填满画面
                        scale_w = target_w / original_w
                        scale_h = target_h / original_h
                        scale = max(scale_w, scale_h)  # 🔥 使用max确保填满整个画面
                        
                        # 应用缩放到目标分辨率
                        try:
                            clip = clip.with_effects([Resize((target_w, target_h))])
                            self.logger.info(f"✅ 视频缩放到目标分辨率: {target_w}x{target_h}")
                        except Exception as e:
                            self.logger.warning(f"直接缩放失败，尝试按比例缩放: {e}")
                            try:
                                # 备用方案：先按比例缩放，然后居中裁剪
                                new_w = int(original_w * scale)
                                new_h = int(original_h * scale)
                                clip = clip.with_effects([Resize((new_w, new_h))])
                                clip = clip.with_position('center')
                                self.logger.info(f"✅ 视频按比例缩放: {new_w}x{new_h} 并居中")
                            except Exception as e2:
                                self.logger.error(f"视频缩放完全失败: {e2}")
                    else:
                        self.logger.info("视频尺寸已匹配，无需缩放")
                
                # 裁剪片段 - 修复时长处理
                # 支持多种字段名称格式
                clip_in = clip_data.get("clip_in", clip_data.get("clipIn", 0))
                clip_out = clip_data.get("clip_out", clip_data.get("clipOut", None))
                
                # 🔥 调试信息
                self.logger.info(f"原始clip_in: {clip_in}, clip_out: {clip_out}, 视频时长: {clip.duration}")
                
                # 如果没有指定clip_out，使用片段的预期时长
                if clip_out is None:
                    expected_duration = clip_data["end"] - clip_data["start"]
                    clip_out = min(clip_in + expected_duration, clip.duration)
                else:
                    # 确保clip_out不超过视频长度
                    clip_out = min(clip_out, clip.duration)
                
                # 确保clip_in < clip_out
                if clip_in >= clip_out:
                    self.logger.warning(f"clip_in ({clip_in}) >= clip_out ({clip_out}), 调整为使用完整片段")
                    clip_in = 0
                    clip_out = min(clip_data["end"] - clip_data["start"], clip.duration)
                
                try:
                    if clip_out > clip_in:
                        clip = clip.subclipped(clip_in, clip_out)
                        self.logger.info(f"视频裁剪: {clip_in}s - {clip_out}s, 裁剪后时长: {clip.duration}s")
                    else:
                        self.logger.warning(f"无效的裁剪时间，使用完整片段")
                except AttributeError:
                    # Fallback for older MoviePy versions
                    try:
                        if clip_out > clip_in:
                            clip = clip.subclip(clip_in, clip_out)
                        self.logger.info(f"视频裁剪 (fallback): {clip_in}s - {clip_out}s")
                    except Exception as e:
                        self.logger.warning(f"裁剪失败，使用完整片段: {e}")
                
                # 🔥 修复时间设置逻辑 - 优先使用clip_out字段
                # 检查是否有多个时长字段，优先使用最大的那个
                end_time = clip_data["end"]
                clip_out_time = clip_data.get("clip_out", clip_data.get("clipOut", end_time))
                
                # 如果clip_out明显大于end，使用clip_out（这是实际想要的时长）
                if clip_out_time > end_time:
                    self.logger.info(f"发现clip_out({clip_out_time})大于end({end_time})，使用clip_out作为实际时长")
                    expected_duration = clip_out_time - clip_data["start"]
                    actual_end_time = clip_data["start"] + expected_duration
                else:
                    expected_duration = end_time - clip_data["start"]
                    actual_end_time = end_time
                
                # 🔥 重要：不要在这里设置start时间，因为拼接时会自动处理
                # 只设置duration
                try:
                    # clip = clip.with_start(clip_data["start"])  # 🔥 注释掉，避免黑屏
                    actual_duration = min(expected_duration, clip.duration)
                    clip = clip.with_duration(actual_duration)
                    self.logger.info(f"片段时间设置: duration={actual_duration}s (期望={expected_duration}s)")
                except AttributeError:
                    # Fallback for older MoviePy versions
                    # clip = clip.set_start(clip_data["start"])  # 🔥 注释掉，避免黑屏
                    actual_duration = min(expected_duration, clip.duration)
                    clip = clip.set_duration(actual_duration)
                
                # 应用变换
                transform = clip_data.get("transform", {})
                clip = self._apply_transform(clip, transform, resolution)
                
                # 应用艺术风格（如果有）
                artistic_style = clip_data.get("artistic_style")
                if artistic_style:
                    if self.style_system and self.style_filter_engine:
                        try:
                            self.logger.info(f"🎨 应用艺术风格: {artistic_style}")
                            # 获取风格的滤镜列表
                            style_filters = self.style_system.get_style_filters(artistic_style)
                            self.logger.info(f"   风格滤镜: {style_filters}")
                            for style_filter in style_filters:
                                self.logger.info(f"   应用滤镜: {style_filter}")
                                clip = self.style_filter_engine.apply_filter(clip, style_filter)
                        except Exception as e:
                            self.logger.warning(f"应用艺术风格失败: {e}")
                    else:
                        self.logger.warning(f"⚠️ 艺术风格系统未初始化，无法应用风格: {artistic_style}")
                
                # 应用滤镜和效果
                filters = clip_data.get("filters", [])
                if filters:
                    try:
                        # 使用本地特效实现（已弃用火山引擎）
                        
                        # 检查是否有艺术风格滤镜可用
                        if self.style_filter_engine:
                            # 优先使用艺术风格滤镜引擎
                            for filter_name in filters:
                                if filter_name in self.style_filter_engine.filter_map:
                                    self.logger.info(f"应用艺术滤镜: {filter_name}")
                                    clip = self.style_filter_engine.apply_filter(clip, filter_name)
                                    continue
                        
                        # 导入easy_clip_effects模块作为后备
                        from core.clipeffects import easy_clip_effects
                        
                        # 分离转场效果和滤镜效果
                        transition_effects = []
                        regular_filters = []
                        
                        for filter_name in filters:
                            if "transition" in filter_name or filter_name in ["leaf_flip", "blinds", "wind_blow"]:
                                transition_effects.append(filter_name)
                            else:
                                regular_filters.append(filter_name)
                        
                        # 只应用常规滤镜，转场效果稍后处理
                        for filter_name in regular_filters:
                            self.logger.info(f"应用滤镜: {filter_name}")
                            
                            # 根据滤镜名称应用对应的效果
                            # 注意：转场效果应用在视频中间部分，模拟片段之间的过渡
                            effect_duration = min(2, clip.duration / 3)  # 效果持续时间，不超过视频的三分之一
                            
                            # 计算转场效果的开始位置（在视频中间）
                            transition_start = (clip.duration - effect_duration) / 2
                            
                            if filter_name == "transition_001" or filter_name == "zoom_in":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.zoom_in(clip, duration=clip.duration, intensity=0.3)
                            elif filter_name == "zoom_out":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.zoom_out(clip, duration=clip.duration, intensity=0.3)
                            elif filter_name == "pan_left":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.pan(clip, duration=clip.duration, intensity=100, direction='left')
                            elif filter_name == "pan_right":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.pan(clip, duration=clip.duration, intensity=100, direction='right')
                            elif filter_name == "rotate":
                                # 直接对整个片段应用旋转效果，不分段
                                clip = easy_clip_effects.rotate(clip, duration=clip.duration, degrees=360)
                            elif filter_name == "blur":
                                clip = easy_clip_effects.blur(clip, sigma=3)
                            elif filter_name == "vignette":
                                clip = easy_clip_effects.vignette(clip, strength=0.5)
                            elif filter_name == "shake":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.shake(clip, intensity=5)
                            elif filter_name == "glitch":
                                # 直接对整个片段应用效果
                                clip = easy_clip_effects.glitch(clip, intensity=3)
                            elif filter_name == "pixelate":
                                clip = easy_clip_effects.pixelate(clip, block_size=10)
                            elif filter_name == "posterize":
                                clip = easy_clip_effects.posterize(clip, levels=4)
                            elif filter_name == "edge_detect":
                                clip = easy_clip_effects.edge_detect(clip)
                            elif filter_name == "black_overlay":
                                clip = easy_clip_effects.apply_black_overlay(clip, opacity=30)
                            else:
                                self.logger.warning(f"未知滤镜: {filter_name}")
                                
                    except Exception as e:
                        self.logger.warning(f"应用滤镜失败: {e}，跳过滤镜应用")
                
                # 应用转场
                if clip_data.get("transition_in"):
                    clip = self._apply_transition(clip, clip_data["transition_in"], "in")
                    self.logger.info(f"  转场in后片段时长: {clip.duration}s")
                if clip_data.get("transition_out"):
                    clip = self._apply_transition(clip, clip_data["transition_out"], "out")
                    self.logger.info(f"  转场out后片段时长: {clip.duration}s")
                
                # 🔥 重要：不要设置start时间，避免黑屏
                # 拼接时会自动处理片段顺序
                # try:
                #     clip = clip.with_start(clip_data["start"])
                # except AttributeError:
                #     clip = clip.set_start(clip_data["start"])
                # self.logger.info(f"  重新设置片段开始时间: {clip_data['start']}s")
                
                # 设置透明度
                if "opacity" in clip_data:
                    try:
                        clip = clip.with_opacity(clip_data["opacity"])
                    except AttributeError:
                        # Fallback for older MoviePy versions
                        clip = clip.set_opacity(clip_data["opacity"])
                
                clips.append(clip)
                
            except Exception as e:
                self.logger.error(f"处理视频片段失败: {e}")
                continue
        
        return clips

    def _process_audio_track(self, track: Dict) -> List:
        """处理音频轨道"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                content = clip_data.get("content", {})
                source = content.get("source", "")
                
                if not source:
                    continue
                
                # 加载音频文件
                audio_path = self.resource_dir / source
                if audio_path.exists():
                    clip = AudioFileClip(str(audio_path))
                else:
                    self.logger.warning(f"音频文件不存在: {audio_path}")
                    continue
                
                # 裁剪片段
                try:
                    clip = clip.subclipped(
                        clip_data.get("clipIn", 0),
                        min(clip_data.get("clipOut", clip.duration), clip.duration)
                    )
                except AttributeError:
                    # Fallback for older MoviePy versions
                    clip = clip.subclip(
                        clip_data.get("clipIn", 0),
                        min(clip_data.get("clipOut", clip.duration), clip.duration)
                    )
                
                # 设置音量
                volume = content.get("volume", 1.0)
                if volume != 1.0:
                    clip = clip.with_effects([MultiplyVolume(volume)])
                
                # 循环处理
                if content.get("loop", False):
                    duration = clip_data["end"] - clip_data["start"]
                    clip = clip.loop(duration=duration)
                
                # 设置时间
                clip = clip.set_start(clip_data["start"])
                
                # 淡入淡出
                fade_in = content.get("fade_in", 0)
                fade_out = content.get("fade_out", 0)
                if fade_in > 0:
                    clip = clip.with_effects([AudioFadeIn(fade_in)])
                if fade_out > 0:
                    clip = clip.with_effects([AudioFadeOut(fade_out)])
                
                clips.append(clip)
                
            except Exception as e:
                self.logger.error(f"处理音频片段失败: {e}")
                continue
        
        return clips

    def _process_text_track(self, track: Dict, resolution: Dict) -> List:
        """处理文字轨道 - 支持渐进式字幕"""
        clips = []
        
        for clip_data in track.get("clips", []):
            try:
                content = clip_data.get("content", {})
                text = content.get("text", "")
                
                # 检查是否使用渐进式字幕
                use_progressive = content.get("progressive", False) or len(text) > 50
                
                if use_progressive and SUBTITLE_UTILS_AVAILABLE:
                    # 使用渐进式字幕系统
                    self.logger.info(f"使用渐进式字幕处理: {text[:30]}...")
                    
                    # 分割文本
                    segments = split_text_for_progressive_subtitles(
                        text,
                        max_chars_per_line=content.get("max_chars_per_line", 25),
                        max_lines=content.get("max_lines", 2)
                    )
                    
                    # 计算时间分配
                    duration = clip_data["end"] - clip_data["start"]
                    timings = calculate_progressive_subtitle_timings(duration, segments)
                    
                    # 获取字体设置
                    font = content.get("font", "Arial")
                    
                    # 字体映射，将中文字体名映射到系统字体
                    font_mapping = {
                        "黑体": "Arial",
                        "宋体": "Times",
                        "思源黑体": "Arial",
                        "微软雅黑": "Arial",
                        "楷体": "Times"
                    }
                    
                    if font in font_mapping:
                        font = font_mapping[font]
                    
                    # 创建字幕剪辑
                    subtitle_clips = create_subtitle_clips(
                        segments=segments,
                        timings=timings,
                        font=font,
                        font_size=content.get("size", 36),
                        color=content.get("color", "white"),
                        stroke_color=content.get("stroke_color", "black"),
                        stroke_width=content.get("stroke_width", 2)
                    )
                    
                    # 调整每个字幕片段的开始时间
                    for subtitle_clip in subtitle_clips:
                        try:
                            # 相对于整个clip_data的开始时间调整
                            current_start = subtitle_clip.start if hasattr(subtitle_clip, 'start') else 0
                            subtitle_clip = subtitle_clip.with_start(clip_data["start"] + current_start)
                        except AttributeError:
                            current_start = getattr(subtitle_clip, 'start', 0)
                            subtitle_clip = subtitle_clip.set_start(clip_data["start"] + current_start)
                        
                        clips.append(subtitle_clip)
                    
                    self.logger.info(f"创建了 {len(subtitle_clips)} 个渐进式字幕片段")
                    
                else:
                    # 🔥 使用江西拙楷字体（与coze系统一致）
                    import os
                    
                    # 获取江西拙楷字体路径
                    # video_cut/video_editor.py -> 项目根目录需要往上1级
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                    font_path = os.path.join(project_root, '江西拙楷2.0.ttf')
                    alt_font_path = os.path.join(project_root, 'core/cliptemplate/coze/transform/江西拙楷2.0.ttf')
                    
                    self.logger.info(f"字体路径计算: project_root={project_root}")
                    self.logger.info(f"主字体路径: {font_path}, 存在: {os.path.exists(font_path)}")
                    self.logger.info(f"备用字体路径: {alt_font_path}, 存在: {os.path.exists(alt_font_path)}")
                    
                    if os.path.exists(font_path):
                        font = font_path
                        self.logger.info(f"使用江西拙楷字体: {font_path}")
                    elif os.path.exists(alt_font_path):
                        font = alt_font_path
                        self.logger.info(f"使用备用江西拙楷字体: {alt_font_path}")
                    else:
                        # macOS 系统中文字体路径
                        system_fonts = [
                            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                            '/System/Library/Fonts/STHeiti Light.ttc',
                            '/System/Library/Fonts/PingFang.ttc',
                            '/Library/Fonts/Arial Unicode.ttf'
                        ]
                        
                        font = None
                        for sys_font in system_fonts:
                            if os.path.exists(sys_font):
                                font = sys_font
                                self.logger.info(f"使用系统字体: {sys_font}")
                                break
                        
                        if not font:
                            # 最后的备选：使用不带路径的字体名称，让moviepy自己查找
                            font = 'Helvetica'
                            self.logger.warning("江西拙楷字体未找到，使用默认字体")
                        else:
                            self.logger.warning("江西拙楷字体未找到，使用系统字体")
                    
                    try:
                        # MoviePy 2.x 中的 TextClip 参数（使用正确的参数名）
                        text_clip = TextClip(
                            text=text,
                            color=content.get("color", "white"),
                            font_size=content.get("size", 50),
                            font=font
                        )
                    except Exception as e:
                        self.logger.warning(f"TextClip创建失败，尝试备用方案: {e}")
                        try:
                            # 备用方案：不指定字体，使用系统默认
                            text_clip = TextClip(
                                text=text,
                                color=content.get("color", "white"),
                                font_size=content.get("size", 50)
                            )
                        except Exception as e2:
                            self.logger.error(f"TextClip创建完全失败，跳过文字: {e2}")
                            continue
                    
                    # 设置位置
                    position = content.get("position", "bottom")
                    try:
                        if position == "center":
                            text_clip = text_clip.with_position("center")
                        elif position == "bottom":
                            text_clip = text_clip.with_position(("center", resolution["height"] - 100))
                        elif position == "top":
                            text_clip = text_clip.with_position(("center", 50))
                        elif isinstance(position, (list, tuple)):
                            text_clip = text_clip.with_position(position)
                    except AttributeError:
                        # Fallback for older MoviePy versions
                        if position == "center":
                            text_clip = text_clip.set_position("center")
                        elif position == "bottom":
                            text_clip = text_clip.set_position(("center", resolution["height"] - 100))
                        elif position == "top":
                            text_clip = text_clip.set_position(("center", 50))
                        elif isinstance(position, (list, tuple)):
                            text_clip = text_clip.set_position(position)
                    
                    # 设置持续时间
                    duration = clip_data["end"] - clip_data["start"]
                    try:
                        text_clip = text_clip.with_duration(duration)
                        text_clip = text_clip.with_start(clip_data["start"])
                    except AttributeError:
                        # Fallback for older MoviePy versions
                        text_clip = text_clip.set_duration(duration)
                        text_clip = text_clip.set_start(clip_data["start"])
                    
                    # 应用动画
                    animation = content.get("animation", "")
                    if animation == "fade_in":
                        text_clip = text_clip.with_effects([FadeIn(0.5)])
                    elif animation == "slide_in":
                        text_clip = self._slide_in_text(text_clip)
                    
                    # 应用滤镜（文字滤镜通常不需要）
                    filters = clip_data.get("filters", [])
                    if filters:
                        self.logger.info(f"跳过文字滤镜应用: {filters}（文字轨道通常不需要滤镜）")
                    
                    clips.append(text_clip)
                
            except Exception as e:
                self.logger.error(f"处理文字片段失败: {e}")
                continue
        
        return clips

    def _composite_video(self, video_clips: List, text_clips: List, audio_clips: List, 
                        duration: float, resolution: Dict, fps: int, transition_effect: str = None):
        """合成最终视频"""
        self.logger.info(f"开始合成视频: {len(video_clips)}个视频片段, {len(text_clips)}个文字片段, {len(audio_clips)}个音频片段")
        
        if not video_clips:
            # 如果没有视频片段，创建黑色背景
            self.logger.warning("没有视频片段，创建纯黑色背景")
            background = self._create_color_clip(duration, resolution, (0, 0, 0))
            all_clips = [background] + text_clips
        else:
            # 有视频片段时，不需要背景
            all_clips = video_clips + text_clips
            
            # 检查视频片段的总时长覆盖
            total_coverage = 0
            for i, clip in enumerate(video_clips):
                try:
                    clip_start = getattr(clip, 'start', 0)
                    clip_duration = getattr(clip, 'duration', 0)
                    clip_end = clip_start + clip_duration
                    self.logger.info(f"  片段{i}: start={clip_start}s, duration={clip_duration}s, end={clip_end}s")
                    total_coverage = max(total_coverage, clip_end)
                except Exception as e:
                    self.logger.warning(f"  片段{i} 时长计算失败: {e}")
                    continue
            
            self.logger.info(f"视频片段总覆盖时长: {total_coverage}s, 目标时长: {duration}s")
            
            # 如果视频片段没有覆盖全部时长，添加黑色填充
            if total_coverage < duration:
                self.logger.info(f"添加黑色填充: {total_coverage}s - {duration}s")
                fill_clip = self._create_color_clip(duration - total_coverage, resolution, (0, 0, 0))
                try:
                    fill_clip = fill_clip.with_start(total_coverage)
                except AttributeError:
                    fill_clip = fill_clip.set_start(total_coverage)
                all_clips.append(fill_clip)
        
        # 创建合成视频
        self.logger.info(f"创建合成视频，总共 {len(all_clips)} 个片段")
        
        # 🔥 使用顺序拼接而不是CompositeVideoClip
        if len(video_clips) > 1:
            # 按顺序拼接视频片段
            from moviepy import concatenate_videoclips
            
            # 🔥 清除start属性，避免黑屏和时间轴冲突
            for clip in video_clips:
                if hasattr(clip, 'start'):
                    delattr(clip, 'start')
                # 同时清除MoviePy的其他时间属性
                if hasattr(clip, '_start'):
                    delattr(clip, '_start')
            
            # 如果有叶片翻转转场效果，应用到片段之间
            if transition_effect:
                self.logger.info(f"检测到转场效果: {transition_effect}")
            if transition_effect in ["leaf_flip_transition", "leaf_flip"]:
                self.logger.info("应用叶片翻转转场效果")
                video_part = self._apply_transitions_between_clips(video_clips, "leaf_flip")
            else:
                # 顺序拼接
                # 🔥 使用chain方法确保片段按顺序播放，而不是叠加
                video_part = concatenate_videoclips(video_clips, method="chain")
            
            self.logger.info(f"视频拼接完成，总时长: {video_part.duration}s")
            
            # 如果有文字片段，合成到视频上
            if text_clips:
                final_video = CompositeVideoClip([video_part] + text_clips, size=(resolution["width"], resolution["height"]))
            else:
                final_video = video_part
        else:
            # 原来的逻辑
            final_video = CompositeVideoClip(all_clips, size=(resolution["width"], resolution["height"]))
        
        # 设置总时长
        try:
            final_video = final_video.with_duration(duration)
        except AttributeError:
            final_video = final_video.set_duration(duration)
        
        # 合并音频
        if audio_clips:
            self.logger.info(f"合并 {len(audio_clips)} 个音频片段")
            final_audio = CompositeAudioClip(audio_clips)
            try:
                final_video = final_video.with_audio(final_audio)
            except AttributeError:
                # Fallback for older MoviePy versions
                final_video = final_video.set_audio(final_audio)
        else:
            # 检查视频片段是否有音频
            has_audio = False
            for clip in video_clips:
                if hasattr(clip, 'audio') and clip.audio is not None:
                    has_audio = True
                    break
            
            if not has_audio:
                self.logger.info("没有音频片段，保持视频原有音频")
        
        return final_video

    def _create_color_clip(self, duration: float, resolution: Dict, color: Tuple[int, int, int]):
        """创建纯色片段"""
        return ColorClip(
            size=(resolution["width"], resolution["height"]),
            color=color,
            duration=duration
        )

    def _apply_transform(self, clip, transform: Dict, resolution: Dict):
        """应用变换"""
        # 缩放
        scale = transform.get("scale", 1.0)
        if scale != 1.0:
            try:
                # 计算目标尺寸
                target_width = int(resolution["width"] * scale)
                target_height = int(resolution["height"] * scale)
                clip = clip.with_effects([Resize((target_width, target_height))])
            except Exception as e:
                self.logger.warning(f"缩放失败: {e}")
        
        # 🔥 修复位置处理
        position = transform.get("position", ["center", "center"])
        
        # 如果position是像素坐标 [960, 540]，转换为居中
        if isinstance(position, list) and len(position) == 2:
            if all(isinstance(p, (int, float)) for p in position):
                # 检查是否是像素坐标（通常960, 540是1920x1080的中心）
                if position[0] > 1 and position[1] > 1:  # 明显是像素坐标
                    self.logger.info(f"检测到像素坐标位置 {position}，转换为居中显示")
                    position = "center"
        
        # 应用位置
        try:
            if position == "center" or position == ["center", "center"]:
                clip = clip.with_position("center")
                self.logger.info("视频设置为居中显示")
            else:
                clip = clip.with_position(position)
                self.logger.info(f"视频位置设置为: {position}")
        except AttributeError:
            # Fallback for older MoviePy versions
            if position == "center" or position == ["center", "center"]:
                clip = clip.set_position("center")
            else:
                clip = clip.set_position(position)
        
        # 旋转
        rotation = transform.get("rotation", 0)
        if rotation != 0:
            try:
                clip = clip.with_effects([Rotate(rotation)])
            except Exception as e:
                self.logger.warning(f"旋转失败: {e}")
        
        return clip

    def _apply_filter(self, clip, filter_name: str):
        """应用滤镜效果"""
        # 解析滤镜名称和强度
        parts = filter_name.split("_")
        if len(parts) >= 2:
            effect_type = parts[0]
            try:
                intensity = int(parts[1]) / 10.0  # 转换为0-1的强度
            except:
                intensity = 1.0
        else:
            effect_type = filter_name
            intensity = 1.0
        
        # 应用对应的效果
        if effect_type in self.effect_mapping:
            return self.effect_mapping[effect_type](clip, intensity)
        else:
            self.logger.warning(f"未知的滤镜效果: {effect_type}")
            return clip

    def _apply_transition(self, clip, transition: Dict, direction: str):
        """应用转场效果 - 只在转场时间内应用"""
        transition_type = transition.get("type", "fade")
        duration = transition.get("duration", 1.0)
        
        self.logger.info(f"✨ 应用{direction}转场: {transition_type}, 时长={duration}s")
        
        # 🔥 重要：只在转场时间内应用效果，不影响整个片段
        if transition_type in self.transition_mapping:
            try:
                if direction == "in":
                    # 进入转场：只影响片段开头的duration秒
                    if clip.duration <= duration:
                        # 如果片段比转场时间短，应用到整个片段
                        result = self.transition_mapping[transition_type](clip, clip.duration)
                    else:
                        # 分割片段：前duration秒应用转场，其余部分保持原样
                        transition_part = clip.subclipped(0, duration)
                        normal_part = clip.subclipped(duration, clip.duration)
                        
                        # 只对转场部分应用效果
                        transition_part = self.transition_mapping[transition_type](transition_part, duration)
                        
                        # 拼接转场部分和正常部分
                        from moviepy import concatenate_videoclips
                        result = concatenate_videoclips([transition_part, normal_part], method="chain")
                        
                elif direction == "out":
                    # 退出转场：只影响片段末尾的duration秒
                    if clip.duration <= duration:
                        # 如果片段比转场时间短，应用到整个片段
                        result = self.transition_mapping[transition_type](clip, clip.duration)
                    else:
                        # 分割片段：最后duration秒应用转场，其余部分保持原样
                        normal_part = clip.subclipped(0, clip.duration - duration)
                        transition_part = clip.subclipped(clip.duration - duration, clip.duration)
                        
                        # 只对转场部分应用效果
                        transition_part = self.transition_mapping[transition_type](transition_part, duration)
                        
                        # 拼接正常部分和转场部分
                        from moviepy import concatenate_videoclips
                        result = concatenate_videoclips([normal_part, transition_part], method="chain")
                else:
                    # 未知方向，应用到整个片段
                    result = self.transition_mapping[transition_type](clip, duration)
                
                self.logger.info(f"✅ {transition_type} 转场应用成功")
                return result
            except Exception as e:
                self.logger.error(f"❌ 应用{transition_type}转场失败: {e}")
                return clip
        else:
            self.logger.warning(f"未知的转场效果: {transition_type}")
            return clip

    # 特效实现
    def _apply_blur(self, clip, intensity: float):
        """应用模糊效果"""
        # MoviePy没有内置模糊，这里用简单的resize实现
        blur_factor = 1 - (intensity * 0.5)  # 最多缩小到50%
        if blur_factor < 1.0:
            small = clip.with_effects([Resize(blur_factor)])
            return small.with_effects([Resize(clip.size)])
        return clip

    def _apply_glow(self, clip, intensity: float):
        """应用光晕效果"""
        # 简单的亮度增强模拟光晕
        return clip.fx(lambda frame: np.clip(frame * (1 + intensity * 0.5), 0, 255).astype('uint8'))

    def _apply_particle(self, clip, intensity: float):
        """应用粒子效果"""
        # 这里需要更复杂的实现，暂时返回原片段
        return clip

    def _apply_fade(self, clip, intensity: float):
        """应用淡入淡出"""
        fade_duration = intensity
        return clip.with_effects([FadeIn(fade_duration), FadeOut(fade_duration)])

    def _apply_zoom(self, clip, intensity: float):
        """应用缩放效果"""
        scale = 1 + intensity * 0.5
        return clip.with_effects([Resize(scale)])

    def _apply_rotate(self, clip, intensity: float):
        """应用旋转效果"""
        try:
            from core.clipeffects import easy_clip_effects
            # 使用easy_clip_effects的rotate函数
            # 旋转整个片段，角度基于intensity
            angle = intensity * 360
            return easy_clip_effects.rotate(clip, duration=clip.duration, degrees=angle)
        except Exception as e:
            self.logger.warning(f"旋转效果失败: {e}")
            return clip

    def _apply_shake(self, clip, intensity: float):
        """应用震动效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.shake(clip, intensity=int(intensity * 5))
        except Exception as e:
            self.logger.warning(f"震动效果失败: {e}")
            return clip

    def _apply_color_correct(self, clip, intensity: float):
        """应用色彩校正"""
        # 简单的对比度和亮度调整
        def color_correct(frame):
            # 增加对比度
            contrast = 1 + intensity * 0.5
            # 调整亮度
            brightness = 1 + intensity * 0.2
            
            frame = frame * contrast
            frame = frame + brightness * 10
            
            return np.clip(frame, 0, 255).astype('uint8')
        
        return clip.fl_image(color_correct)

    # 转场效果实现
    def _cross_fade(self, clip1, clip2, duration: float):
        """交叉淡化转场"""
        # 这个需要两个片段，暂时简化处理
        return clip1.with_effects([FadeIn(duration)])

    def _slide_transition(self, clip, duration: float):
        """滑动转场"""
        # 简化实现
        return clip

    def _zoom_transition(self, clip, duration: float):
        """缩放转场"""
        # 简化实现
        return clip
    
    # 简单转场效果实现 - 使用本地实现
    def _apply_zoom_in_transition(self, clip, duration: float):
        """放大转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.zoom_in(clip, duration=duration)
        except Exception as e:
            self.logger.warning(f"zoom_in效果失败: {e}")
            return clip
    
    def _apply_zoom_out_transition(self, clip, duration: float):
        """缩小转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.zoom_out(clip, duration=duration)
        except Exception as e:
            self.logger.warning(f"zoom_out效果失败: {e}")
            return clip
    
    def _apply_pan_left_transition(self, clip, duration: float):
        """左移转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.pan(clip, duration=duration, direction='left')
        except Exception as e:
            self.logger.warning(f"pan_left效果失败: {e}")
            return clip
    
    def _apply_pan_right_transition(self, clip, duration: float):
        """右移转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.pan(clip, duration=duration, direction='right')
        except Exception as e:
            self.logger.warning(f"pan_right效果失败: {e}")
            return clip
    
    def _apply_rotate_transition(self, clip, duration: float):
        """旋转转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.rotate(clip, duration=min(duration, clip.duration), degrees=360)
        except Exception as e:
            self.logger.warning(f"rotate效果失败: {e}")
            return clip
    
    def _apply_shake_transition(self, clip, duration: float):
        """抖动转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.shake(clip, intensity=5)
        except Exception as e:
            self.logger.warning(f"shake效果失败: {e}")
            return clip
    
    def _apply_glitch_transition(self, clip, duration: float):
        """故障转场效果 - 使用本地实现"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.glitch_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"glitch效果失败: {e}")
            return clip

    # 新增转场效果实现
    def _apply_leaf_flip_transition(self, clip, duration: float):
        """叶片翻转转场效果
        
        注意：叶片翻转是一个需要两个片段的转场效果
        这里我们模拟一个翻转效果作为单片段的滤镜
        """
        try:
            from core.clipeffects import easy_clip_effects
            # 对于单个片段，应用一个翻转动画效果
            # 这不是真正的转场，但可以产生类似的视觉效果
            self.logger.info("应用叶片翻转效果到单个片段")
            # 使用rotate作为替代效果，因为leaf_flip需要两个片段
            return easy_clip_effects.rotate(clip, angle=180, duration=duration)
        except Exception as e:
            self.logger.warning(f"叶片翻转效果失败: {e}")
            return clip
    
    def _apply_transitions_between_clips(self, clips: List, transition_type: str = "leaf_flip", duration: float = 1.0):
        """在视频片段之间应用转场效果"""
        from core.clipeffects import easy_clip_effects
        
        if len(clips) <= 1:
            # 🔥 使用chain方法确保片段按顺序播放
            return concatenate_videoclips(clips, method="chain") if clips else None
        
        result_clips = []
        for i in range(len(clips) - 1):
            # 当前片段和下一个片段
            clip1 = clips[i]
            clip2 = clips[i + 1]
            
            # 如果片段时长过短，不应用转场
            if clip1.duration < duration * 2 or clip2.duration < duration * 2:
                result_clips.append(clip1)
                continue
            
            # 分割片段：保留大部分，只在结尾/开头应用转场
            # 🔥 修复：使用subclipped而不是subclip
            main_part1 = clip1.subclipped(0, clip1.duration - duration)
            transition_part1 = clip1.subclipped(clip1.duration - duration, clip1.duration)
            transition_part2 = clip2.subclipped(0, duration)
            main_part2 = clip2.subclipped(duration, clip2.duration)
            
            # 应用转场效果
            if transition_type == "leaf_flip":
                transition = easy_clip_effects.leaf_flip_transition(transition_part1, transition_part2, duration)
            elif transition_type == "blinds":
                transition = easy_clip_effects.blinds_transition(transition_part1, transition_part2, duration)
            elif transition_type == "wind_blow":
                transition = easy_clip_effects.wind_blow_transition(transition_part1, transition_part2, duration)
            else:
                # 默认使用淡入淡出
                transition = transition_part1.crossfadeout(duration/2).with_end(duration/2)
                transition = concatenate_videoclips([transition, transition_part2.crossfadein(duration/2)])
            
            # 添加到结果
            result_clips.append(main_part1)
            result_clips.append(transition)
            
            # 如果是最后一对片段，添加第二个片段的剩余部分
            if i == len(clips) - 2:
                result_clips.append(main_part2)
        
        # 拼接所有片段
        # 🔥 使用chain方法确保片段按顺序播放
        return concatenate_videoclips(result_clips, method="chain")
    
    def _apply_blinds_transition(self, clip, duration: float):
        """百叶窗转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.blinds_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"百叶窗效果失败: {e}")
            return clip
    
    def _apply_wind_blow_transition(self, clip, duration: float):
        """风吹转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.wind_blow_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"风吹效果失败: {e}")
            return clip
    
    def _apply_rotate_zoom_transition(self, clip, duration: float):
        """旋转放大转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.rotate_zoom_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"旋转放大效果失败: {e}")
            return clip
    
    def _apply_hexagon_transition(self, clip, duration: float):
        """六角形转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.hexagon_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"六角形效果失败: {e}")
            return clip
    
    def _apply_circle_open_transition(self, clip, duration: float):
        """圆形打开转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.circle_open_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"圆形打开效果失败: {e}")
            return clip
    
    def _apply_heart_open_transition(self, clip, duration: float):
        """心形打开转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.heart_open_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"心形打开效果失败: {e}")
            return clip
    
    def _apply_dream_zoom_transition(self, clip, duration: float):
        """梦幻放大转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.dream_zoom_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"梦幻放大效果失败: {e}")
            return clip
    
    def _apply_clock_sweep_transition(self, clip, duration: float):
        """时钟扫描转场效果"""
        try:
            from core.clipeffects import easy_clip_effects
            return easy_clip_effects.clock_sweep_transition(clip, None, duration)
        except Exception as e:
            self.logger.warning(f"时钟扫描效果失败: {e}")
            return clip
    
    def _slide_in_text(self, text_clip):
        """文字滑入动画"""
        # 从右侧滑入
        w, h = text_clip.size
        
        def slide_pos(t):
            if t < 0.5:
                # 滑入阶段
                progress = t / 0.5
                x = w + (1 - progress) * w
                return (x, "center")
            else:
                return ("center", "center")
        
        try:
            return text_clip.with_position(slide_pos)
        except AttributeError:
            # Fallback for older MoviePy versions
            return text_clip.set_position(slide_pos)


def main():
    """测试视频编辑器"""
    # 读取时间轴JSON
    with open("output/final_timeline.json", "r", encoding="utf-8") as f:
        timeline_json = json.load(f)
    
    # 创建编辑器
    editor = VideoEditor(resource_dir="./resources")
    
    # 执行剪辑
    success = editor.execute_timeline(timeline_json, "output/final_video.mp4")
    
    if success:
        print("视频剪辑成功！")
    else:
        print("视频剪辑失败！")


if __name__ == "__main__":
    main()
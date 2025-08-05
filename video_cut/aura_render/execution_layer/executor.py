"""
AuraRender 机械执行器

负责：
1. 解析执行脚本
2. 加载和生成资源
3. 执行时间轴
4. 应用特效
5. 渲染输出
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from moviepy import VideoFileClip, AudioFileClip, ImageClip, TextClip, ColorClip, CompositeVideoClip, concatenate_videoclips, VideoClip
from moviepy.video.fx import CrossFadeIn, CrossFadeOut, MultiplyColor
from moviepy.video.fx.Resize import Resize
import numpy as np
import requests

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.utils.file_utils import download_file_with_retry


class AuraExecutor:
    """机械执行器 - 精确执行脚本，无智能决策"""
    
    def __init__(self, ai_generators: Optional[Dict[str, Any]] = None):
        """
        初始化执行器
        
        Args:
            ai_generators: AI生成器配置，包含万相等AI生成接口
        """
        self.ai_generators = ai_generators or {}
        self.temp_dir = None
        self.resources_cache = {}
        
    def execute(self, script: Dict[str, Any], output_path: str) -> str:
        """
        执行脚本生成视频
        
        Args:
            script: 执行脚本
            output_path: 输出路径
            
        Returns:
            生成的视频文件路径
        """
        try:
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp(prefix='aura_exec_')
            
            # 1. 验证脚本
            self._validate_script(script)
            
            # 2. 加载资源
            resources = self._load_resources(script['resources'])
            
            # 3. 构建时间轴
            timeline = self._build_timeline(script['timeline'], resources, script['project'])
            
            # 4. 应用全局效果
            final_video = self._apply_global_effects(timeline, script.get('global_effects', {}))
            
            # 5. 渲染输出
            output_file = self._render_output(final_video, script['project'], output_path)
            
            return output_file
            
        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _validate_script(self, script: Dict[str, Any]):
        """验证脚本格式"""
        required_fields = ['version', 'project', 'resources', 'timeline']
        for field in required_fields:
            if field not in script:
                raise ValueError(f"脚本缺少必需字段: {field}")
        
        # 验证项目配置
        project = script['project']
        required_project_fields = ['duration', 'resolution', 'fps']
        for field in required_project_fields:
            if field not in project:
                raise ValueError(f"项目配置缺少必需字段: {field}")
    
    def _load_resources(self, resources_config: Dict[str, Any]) -> Dict[str, Any]:
        """加载所有资源"""
        resources = {
            'videos': {},
            'images': {},
            'audio': {},
            'text': {}
        }
        
        print(f"📦 加载资源配置中...")
        
        # 加载视频资源
        for video in resources_config.get('videos', []):
            video_id = video['id']
            video_source = video['source']
            print(f"🎬 加载视频资源: {video_id}")
            
            if video['source'] == 'ai_generated':
                # 使用AI生成视频
                video_path = self._generate_video(video['params'])
            else:
                # 下载或加载本地视频
                video_path = self._load_media_file(video['source'])
            
            if video_path:
                try:
                    clip = VideoFileClip(video_path)
                    # 应用时长限制
                    if 'duration' in video:
                        # MoviePy 2.x 使用 subclipped
                        clip = clip.subclipped(0, min(video['duration'], clip.duration))
                    resources['videos'][video_id] = clip
                    print(f"✅ 视频资源 {video_id} 加载成功，时长: {clip.duration}s")
                except Exception as e:
                    print(f"❌ 加载视频文件失败: {video_path}, 错误: {e}")
            else:
                print(f"❌ 视频资源 {video_id} 加载失败: 无法获取文件路径")
        
        # 加载图片资源
        for image in resources_config.get('images', []):
            image_id = image['id']
            if image['source'].startswith('oss://') or image['source'].startswith('http'):
                image_path = self._load_media_file(image['source'])
                if image_path:
                    resources['images'][image_id] = ImageClip(image_path)
        
        # 加载音频资源
        for audio in resources_config.get('audio', []):
            audio_id = audio['id']
            if audio['source'] == 'ai_generated':
                # 使用AI生成音频
                audio_path = self._generate_audio(audio['params'])
            else:
                audio_path = self._load_media_file(audio['source'])
            
            if audio_path:
                resources['audio'][audio_id] = AudioFileClip(audio_path)
        
        return resources
    
    def _build_timeline(self, timeline_config: List[Dict[str, Any]], 
                       resources: Dict[str, Any], project: Dict[str, Any]) -> VideoClip:
        """构建视频时间轴"""
        print(f"\n🕰️ 构建视频时间轴")
        print(f"📝 时间轴配置：")
        print("-" * 60)
        
        # 输出时间轴详情
        total_duration = 0
        for i, segment in enumerate(timeline_config, 1):
            print(f"\n🎬 片段 {i}:")
            print(f"   ⏱️  时间: {segment.get('start', 0)}s - {segment.get('end', 0)}s")
            print(f"   🎨 类型: {segment.get('type', 'unknown')}")
            
            # 输出图层信息
            layers = segment.get('layers', [])
            for j, layer in enumerate(layers, 1):
                print(f"   🗃️  图层 {j}: {layer.get('type', 'unknown')} - {layer.get('resource_id', 'unknown')}")
                if layer.get('effects'):
                    print(f"      ✨ 特效: {', '.join(layer.get('effects', []))}")
                if layer.get('transform'):
                    print(f"      🔄 变换: {layer.get('transform')}")
            
            total_duration = max(total_duration, segment.get('end', 0))
        
        print(f"\n📊 总时长: {total_duration}s")
        print("-" * 60)
        
        # 解析分辨率
        resolution = project['resolution']
        if isinstance(resolution, str):
            width, height = map(int, resolution.split('x'))
        else:
            width = resolution.get('width', 1920)
            height = resolution.get('height', 1080)
        
        print(f"📺 分辨率: {width}x{height}")
        
        # 创建主合成
        clips = []
        
        for segment in timeline_config:
            start_time = segment['start']
            end_time = segment['end']
            duration = end_time - start_time
            
            # 处理每个图层
            segment_clips = []
            for layer in segment.get('layers', []):
                layer_clip = self._process_layer(layer, resources, duration)
                if layer_clip:
                    # 设置起始时间
                    layer_clip = layer_clip.with_start(start_time)
                    segment_clips.append(layer_clip)
            
            # 合成该片段的所有图层
            if segment_clips:
                # 注意：segment_clips 中的每个clip已经设置了start_time
                # 不需要再次设置时间，直接添加到clips列表
                for clip in segment_clips:
                    # 应用转场效果（如果有）
                    if 'transition_out' in segment:
                        clip = self._apply_transition(clip, segment['transition_out'])
                    clips.append(clip)
        
        # 合成所有片段 - 使用 CompositeVideoClip 而不是 concatenate
        if clips:
            # 创建背景（黑色）
            bg = ColorClip(size=(width, height), color=(0, 0, 0), duration=project['duration'])
            # 将所有片段按时间轴合成
            final_video = CompositeVideoClip([bg] + clips, size=(width, height))
            # MoviePy 2.x 使用 with_duration
            final_video = final_video.with_duration(project['duration'])
            return final_video
        else:
            # 如果没有片段，创建一个空白视频
            return ColorClip(size=(width, height), color=(0, 0, 0), duration=project['duration'])
    
    def _process_layer(self, layer: Dict[str, Any], resources: Dict[str, Any], duration: float) -> Optional[VideoClip]:
        """处理单个图层"""
        layer_type = layer['type']
        
        if layer_type == 'video':
            resource_id = layer['resource_id']
            
            if resource_id in resources['videos']:
                clip = resources['videos'][resource_id].copy()
                # MoviePy 2.x 使用 with_duration
                clip = clip.with_duration(duration)
            else:
                # 如果视频资源不存在，创建一个占位文本
                print(f"⚠️ 视频资源不存在: {resource_id}，创建占位内容")
                clip = TextClip(
                    text=f"视频片段: {resource_id}",
                    font='Arial',
                    font_size=40,
                    color='white',
                    text_align='center'
                ).with_duration(duration)
                # 添加背景色
                bg = ColorClip(size=(1920, 1080), color=(30, 30, 50), duration=duration)
                clip = CompositeVideoClip([bg, clip.with_position('center')])
                
        elif layer_type == 'image':
            resource_id = layer['resource_id']
            if resource_id in resources['images']:
                clip = resources['images'][resource_id].copy()
                # MoviePy 2.x 使用 with_duration
                clip = clip.with_duration(duration)
            else:
                # 如果图片资源不存在，创建一个占位图片
                clip = TextClip(
                    text=f"图片: {resource_id}",
                    font='Arial',
                    font_size=30,
                    color='white',
                    text_align='center'
                ).with_duration(duration)
                # 添加背景色
                bg = ColorClip(size=(1920, 1080), color=(50, 30, 30), duration=duration)
                clip = CompositeVideoClip([bg, clip.with_position('center')])
                
        elif layer_type == 'text':
            # 创建文字图层
            content = layer.get('content', '')
            style = layer.get('style', {})
            
            clip = TextClip(
                text=content,
                font=style.get('font', 'Arial'),
                font_size=style.get('size', 50),
                color=style.get('color', 'white'),
                text_align='center'
            ).with_duration(duration)
            
            # 应用动画
            if style.get('animation') == 'fade_in':
                clip = clip.with_effects([CrossFadeIn(0.5)])
                
        else:
            return None
        
        # 应用变换
        if 'transform' in layer:
            transform = layer['transform']
            if 'scale' in transform:
                # MoviePy 2.x 使用 with_effects
                clip = clip.with_effects([Resize(transform['scale'])])
            if 'position' in transform:
                clip = clip.with_position(transform['position'])
        
        # 应用特效
        for effect in layer.get('effects', []):
            clip = self._apply_effect(clip, effect)
        
        return clip
    
    def _apply_effect(self, clip: VideoClip, effect: Dict[str, Any]) -> VideoClip:
        """应用单个特效"""
        effect_type = effect.get('type', '') if isinstance(effect, dict) else effect
        
        # 这里可以扩展更多特效
        if effect_type == 'glow':
            # 简单的发光效果（通过增加亮度模拟）
            intensity = effect.get('intensity', 0.5) if isinstance(effect, dict) else 0.5
            # 简单的发光效果（通过增加亮度模拟）
            # MoviePy 2.x 使用 MultiplyColor 效果
            clip = clip.with_effects([MultiplyColor(intensity + 1)])
        elif effect_type == 'blur':
            # 模糊效果 - MoviePy 2.x 暂时跳过
            # TODO: 实现模糊效果
            pass
        
        return clip
    
    def _apply_transition(self, clip: VideoClip, transition: Dict[str, Any]) -> VideoClip:
        """应用转场效果"""
        transition_type = transition['type']
        duration = transition.get('duration', 0.5)
        
        if transition_type == 'fade':
            clip = clip.with_effects([CrossFadeOut(duration)])
        elif transition_type == 'glitch':
            # 故障效果转场（简化版）
            pass
        
        return clip
    
    def _apply_global_effects(self, video: VideoClip, effects: Dict[str, Any]) -> VideoClip:
        """应用全局效果"""
        # 颜色分级
        if 'color_grading' in effects:
            grading = effects['color_grading']
            if grading == 'cyberpunk_preset':
                # 赛博朋克色调（偏蓝紫色）
                # 赛博朋克色调（偏蓝紫色）
                # 使用 MultiplyColor 效果模拟
                # RGB顺序，增强红和蓝，减少绿
                video = video.with_effects([MultiplyColor([1.1, 0.9, 1.3])])
            elif grading == 'warm':
                # 暖色调
                # 暖色调
                # 使用 MultiplyColor 效果
                # RGB顺序，增强红，略增绿，减少蓝
                video = video.with_effects([MultiplyColor([1.15, 1.05, 0.9])])
        
        # 滤镜
        for filter_name in effects.get('filters', []):
            if filter_name == 'digital_noise':
                # 数字噪点效果
                pass
            elif filter_name == 'scan_lines':
                # 扫描线效果
                pass
        
        return video
    
    def _render_output(self, video: VideoClip, project: Dict[str, Any], output_path: str) -> str:
        """渲染输出视频"""
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 渲染参数
        fps = project.get('fps', 30)
        codec = 'libx264'
        audio_codec = 'aac'
        
        # 写入视频
        video.write_videofile(
            output_path,
            fps=fps,
            codec=codec,
            audio_codec=audio_codec,
            preset='medium'
        )
        
        return output_path
    
    def _generate_video(self, params: Dict[str, Any]) -> Optional[str]:
        """使用AI生成视频"""
        model = params.get('model', '')
        
        if model == 'animate_diff' and 'animate_diff' in self.ai_generators:
            # 调用AnimateDiff生成视频
            generator = self.ai_generators['animate_diff']
            result = generator.generate(params)
            if result and 'video_path' in result:
                return result['video_path']
        
        # 如果无法生成，返回None
        return None
    
    def _generate_audio(self, params: Dict[str, Any]) -> Optional[str]:
        """使用AI生成音频"""
        model = params.get('model', '')
        
        if model == 'musicgen' and 'musicgen' in self.ai_generators:
            # 调用MusicGen生成音频
            generator = self.ai_generators['musicgen']
            result = generator.generate(params)
            if result and 'audio_path' in result:
                return result['audio_path']
        
        # 如果无法生成，创建静音音频作为fallback
        duration = params.get('duration', 30)
        silence_path = os.path.join(self.temp_dir, 'silence.mp3')
        # 这里可以使用AudioClip创建静音
        
        return None
    
    def _load_media_file(self, source: str) -> Optional[str]:
        """加载媒体文件"""
        if source in self.resources_cache:
            return self.resources_cache[source]
        
        try:
            if source.startswith('oss://'):
                # 处理OSS路径
                # 这里需要实现OSS下载逻辑
                local_path = os.path.join(self.temp_dir, os.path.basename(source))
                # 下载文件...
                self.resources_cache[source] = local_path
                return local_path
                
            elif source.startswith('http'):
                # 检查是否是视频截图接口
                if 'vframe/jpg' in source or 'vframe/png' in source:
                    print(f"⚠️ 检测到视频截图接口，尝试转换为视频URL...")
                    # 尝试移除vframe参数获取原始视频
                    video_url = source.split('?')[0]  # 移除查询参数
                    print(f"🎬 尝试使用原始视频URL: {video_url}")
                    source = video_url  # 更新source为视频URL
                
                # 特殊处理美花资源URL
                if 'resource.meihua.info' in source:
                    print(f"🏇 检测到美花资源URL")
                    # 这个URL可能需要特殊处理或者是一个加密资源
                    # 目前先尝试直接下载
                
                # 下载网络文件
                print(f"📥 下载网络文件: {source}")
                print(f"🔍 URL分析:")
                print(f"   - 协议: {source.split('://')[0]}")
                print(f"   - 域名: {source.split('/')[2]}")
                print(f"   - 路径: {'/'.join(source.split('/')[3:])}")
                filename = os.path.basename(source.split('?')[0])  # 处理URL参数
                if not filename or '.' not in filename:
                    # 如果没有文件名或没有扩展名，默认使用mp4
                    filename = f"downloaded_{int(datetime.now().timestamp())}.mp4"
                elif not any(filename.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']):
                    # 如果不是视频扩展名，添加mp4
                    filename += '.mp4'
                    
                local_path = os.path.join(self.temp_dir, filename)
                
                # 导入下载函数
                try:
                    from core.utils.file_utils import download_file_with_retry
                    success = download_file_with_retry(source, local_path, verbose=True)
                except Exception as download_error:
                    print(f"❌ 下载过程出错: {download_error}")
                    print(f"🔍 错误类型: {type(download_error).__name__}")
                    import traceback
                    traceback.print_exc()
                    success = False
                
                if success and os.path.exists(local_path):
                    # 检查下载的文件大小
                    file_size = os.path.getsize(local_path)
                    print(f"📁 下载成功，文件大小: {file_size} 字节")
                    
                    if file_size < 1024:  # 小于1KB可能是错误文件
                        print(f"⚠️ 下载的文件太小，可能不是有效视频")
                        try:
                            with open(local_path, 'r') as f:
                                content = f.read()
                            print(f"📄 文件内容预览: {content[:200]}...")
                        except:
                            pass
                    
                    self.resources_cache[source] = local_path
                    return local_path
                else:
                    print(f"❌ 网络文件下载失败: {source}")
                    # 尝试使用备用视频
                    print(f"🎆 尝试使用示例视频作为备用...")
                    # 这里可以返回一个默认视频路径或None
                    return None
                
            elif os.path.exists(source):
                # 本地文件
                self.resources_cache[source] = source
                return source
            else:
                print(f"❌ 文件不存在: {source}")
                
        except Exception as e:
            print(f"❌ 加载资源失败: {e}")
            
        return None
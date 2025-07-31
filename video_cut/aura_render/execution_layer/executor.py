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
        
        # 加载视频资源
        for video in resources_config.get('videos', []):
            video_id = video['id']
            if video['source'] == 'ai_generated':
                # 使用AI生成视频
                video_path = self._generate_video(video['params'])
            else:
                # 下载或加载本地视频
                video_path = self._load_media_file(video['source'])
            
            if video_path:
                clip = VideoFileClip(video_path)
                # 应用时长限制
                if 'duration' in video:
                    # MoviePy 2.x 使用 subclipped
                    clip = clip.subclipped(0, min(video['duration'], clip.duration))
                resources['videos'][video_id] = clip
        
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
        # 解析分辨率
        resolution = project['resolution']
        if isinstance(resolution, str):
            width, height = map(int, resolution.split('x'))
        else:
            width = resolution.get('width', 1920)
            height = resolution.get('height', 1080)
        
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
                segment_comp = CompositeVideoClip(segment_clips, size=(width, height))
                
                # 应用转场效果
                if 'transition_out' in segment:
                    segment_comp = self._apply_transition(segment_comp, segment['transition_out'])
                
                clips.append(segment_comp)
        
        # 合成所有片段
        if clips:
            final_video = concatenate_videoclips(clips, method="compose")
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
                # 下载网络文件
                local_path = os.path.join(self.temp_dir, os.path.basename(source))
                download_file_with_retry(source, local_path)
                self.resources_cache[source] = local_path
                return local_path
                
            elif os.path.exists(source):
                # 本地文件
                self.resources_cache[source] = source
                return source
                
        except Exception as e:
            print(f"加载资源失败: {source}, 错误: {e}")
            
        return None
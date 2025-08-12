#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基于标签的视频生成器
根据前端传入的标签顺序，从每个标签的视频列表中随机抽取片段，生成最终视频
"""

import json
import random
import logging
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from moviepy import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip

# 导入文案生成器
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.text_generate.qwen_client import call_qwen
from core.clipgenerate.aliyun_subtitle_api import AliyunSubtitleAPI, SubtitleConfig

# 导入字幕工具
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_cut.utils.subtitle_utils import split_text_for_progressive_subtitles, calculate_progressive_subtitle_timings, create_subtitle_clips


class TagVideoGenerator:
    """基于标签的视频生成器"""
    
    def __init__(self, tag_materials_dir: str = "tag_materials", use_aliyun_subtitle: bool = True):
        """
        初始化生成器
        
        Args:
            tag_materials_dir: 标签素材目录路径
            use_aliyun_subtitle: 是否使用阿里云字幕API
        """
        self.tag_materials_dir = Path(tag_materials_dir)
        self.tag_materials_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        self.use_aliyun_subtitle = use_aliyun_subtitle
        self.aliyun_subtitle_api = AliyunSubtitleAPI() if use_aliyun_subtitle else None
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("TagVideoGenerator")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _download_video(self, url: str, tag_name: str) -> Optional[Path]:
        """
        下载视频到标签素材目录
        
        Args:
            url: 视频URL
            tag_name: 标签名称（用于创建子目录）
            
        Returns:
            下载后的本地文件路径，失败返回None
        """
        try:
            # 创建标签子目录
            tag_dir = self.tag_materials_dir / tag_name
            tag_dir.mkdir(parents=True, exist_ok=True)
            
            # 解析URL，去除查询参数
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            
            # 生成文件名（使用基础URL的hash值避免重复下载）
            url_hash = hashlib.md5(base_url.encode()).hexdigest()[:8]
            
            # 从路径中提取文件扩展名
            path_ext = Path(parsed_url.path).suffix if parsed_url.path else ''
            file_ext = path_ext or '.mp4'
            
            local_filename = f"{url_hash}{file_ext}"
            local_path = tag_dir / local_filename
            
            # 如果文件已存在，直接返回
            if local_path.exists():
                self.logger.info(f"视频已存在，跳过下载: {local_path}")
                return local_path
            
            # 下载视频
            self.logger.info(f"开始下载视频: {url} -> {local_path}")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # 写入文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"视频下载成功: {local_path}")
            return local_path
            
        except Exception as e:
            self.logger.error(f"下载视频失败 {url}: {e}")
            return None
    
    def _prepare_video_path(self, video_path: str, tag_name: str) -> Optional[Path]:
        """
        准备视频路径（支持URL和本地路径）
        
        Args:
            video_path: 视频路径或URL
            tag_name: 标签名称
            
        Returns:
            本地视频文件路径
        """
        # 判断是否是URL
        if video_path.startswith(('http://', 'https://', 'oss://')):
            # 如果是OSS链接，转换为HTTPS
            if video_path.startswith('oss://'):
                video_path = video_path.replace('oss://', 'https://')
            
            # 下载视频
            return self._download_video(video_path, tag_name)
        else:
            # 本地路径
            # 先尝试直接使用路径
            path = Path(video_path)
            if path.exists():
                return path
            
            # 尝试在标签素材目录中查找
            tag_path = self.tag_materials_dir / tag_name / video_path
            if tag_path.exists():
                return tag_path
            
            # 尝试在标签素材根目录查找
            root_path = self.tag_materials_dir / video_path
            if root_path.exists():
                return root_path
            
            self.logger.warning(f"找不到视频文件: {video_path}")
            return None
    
    def generate_video_from_tags(
        self,
        tag_config: Dict[str, Dict[str, List[str]]],
        output_path: str,
        duration_per_tag: Union[float, Dict[str, float]] = 5.0,
        clip_duration_range: tuple = (3.0, 8.0),
        text_content: Optional[str] = None,
        subtitle_config: Optional[Dict] = None,
        dynamic_tags: Optional[List[str]] = None,
        fps: int = 30,
        resolution: tuple = (1920, 1080)
    ) -> str:
        """
        根据标签配置生成视频
        
        Args:
            tag_config: 标签配置，格式如 {"黄山风景": {"video": ["path1.mp4", "path2.mp4"]}}
            output_path: 输出视频路径
            duration_per_tag: 每个标签的目标时长（秒）
                - float: 所有标签使用相同时长
                - Dict[str, float]: 每个标签单独设置时长，如 {"黄山风景": 5.0, "徽州特色餐": 10.0}
            clip_duration_range: 随机片段时长范围 (min, max)
            text_content: 文案内容，如果为None则使用AI生成
            subtitle_config: 字幕配置
            dynamic_tags: 动态标签列表
            fps: 输出视频帧率
            resolution: 输出分辨率
            
        Returns:
            输出视频路径
        """
        self.logger.info(f"开始生成视频，标签数量: {len(tag_config)}")
        
        # 1. 根据标签顺序提取视频片段
        video_clips = self._extract_clips_by_tags(tag_config, duration_per_tag, clip_duration_range)
        
        if not video_clips:
            raise ValueError("无法提取任何视频片段")
        
        # 2. 拼接视频片段
        base_video = concatenate_videoclips(video_clips, method="compose")
        self.logger.info(f"基础视频拼接完成，总时长: {base_video.duration}秒")
        
        # 3. 生成或使用文案
        if text_content is None:
            text_content = self._generate_text_content(list(tag_config.keys()))
            self.logger.info(f"AI生成文案: {text_content[:100]}...")
        
        # 4. 添加字幕
        if subtitle_config is None:
            subtitle_config = self._get_default_subtitle_config()
        
        video_with_subtitles = self._add_subtitles(base_video, text_content, subtitle_config)
        
        # 5. 添加动态标签（可选，通过subtitle_config控制）
        show_dynamic_tags = subtitle_config.get('show_dynamic_tags', False)  # 默认不显示
        if show_dynamic_tags:
            if dynamic_tags:
                final_video = self._add_dynamic_tags(video_with_subtitles, dynamic_tags, tag_config)
            else:
                # 如果没有指定动态标签，使用tag_config的键作为标签
                final_video = self._add_dynamic_tags(video_with_subtitles, list(tag_config.keys()), tag_config)
        else:
            final_video = video_with_subtitles
        
        # 6. 设置输出参数
        final_video = final_video.with_fps(fps)
        # 不需要再调整分辨率，因为在提取片段时已经统一了
        
        # 7. 输出视频
        self.logger.info(f"开始输出视频到: {output_path}")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        self.logger.info(f"视频生成完成: {output_path}")
        return output_path
    
    def _extract_clips_by_tags(
        self,
        tag_config: Dict[str, Dict[str, List[str]]],
        duration_per_tag: Union[float, Dict[str, float]],
        clip_duration_range: tuple
    ) -> List[VideoFileClip]:
        """
        根据标签配置提取视频片段
        
        Args:
            tag_config: 标签配置
            duration_per_tag: 每个标签的目标时长（可以是统一时长或每个标签单独设置）
            clip_duration_range: 片段时长范围
            
        Returns:
            视频片段列表
        """
        clips = []
        
        for tag_name, tag_data in tag_config.items():
            self.logger.info(f"处理标签: {tag_name}")
            
            # 获取当前标签的目标时长
            if isinstance(duration_per_tag, dict):
                # 如果是字典，获取当前标签的时长，如果没有则使用默认值5.0
                target_duration = duration_per_tag.get(tag_name, 5.0)
            else:
                # 如果是float，所有标签使用相同时长
                target_duration = duration_per_tag
            
            self.logger.info(f"标签 {tag_name} 的目标时长: {target_duration}秒")
            
            video_paths = tag_data.get("video", [])
            if not video_paths:
                self.logger.warning(f"标签 {tag_name} 没有视频文件")
                continue
            
            # 累积当前标签的片段时长
            current_tag_duration = 0
            tag_clips = []
            
            # 记录每个视频已使用的时间段，避免重复
            used_segments = {}  # {video_path: [(start1, end1), (start2, end2), ...]}
            
            while current_tag_duration < target_duration:
                # 随机选择一个视频文件
                video_path = random.choice(video_paths)
                
                # 准备视频路径（支持URL下载）
                full_path = self._prepare_video_path(video_path, tag_name)
                if not full_path:
                    self.logger.warning(f"无法获取视频: {video_path}")
                    # 如果所有视频都无法获取，避免死循环
                    video_paths.remove(video_path)
                    if not video_paths:
                        self.logger.error(f"标签 {tag_name} 没有可用的视频文件")
                        break
                    continue
                
                try:
                    # 加载视频
                    video = VideoFileClip(str(full_path))
                    
                    # 随机选择片段时长
                    clip_duration = random.uniform(*clip_duration_range)
                    clip_duration = min(clip_duration, video.duration)
                    clip_duration = min(clip_duration, target_duration - current_tag_duration)
                    
                    if clip_duration <= 0:
                        break
                    
                    # 获取该视频已使用的时间段
                    if video_path not in used_segments:
                        used_segments[video_path] = []
                    
                    # 寻找未使用的时间段
                    available_start = 0
                    found_segment = False
                    attempts = 0
                    max_attempts = 10
                    
                    while attempts < max_attempts:
                        # 随机选择起始时间
                        max_start = max(0, video.duration - clip_duration)
                        start_time = random.uniform(0, max_start) if max_start > 0 else 0
                        end_time = start_time + clip_duration
                        
                        # 检查是否与已使用的时间段重叠
                        overlap = False
                        for used_start, used_end in used_segments[video_path]:
                            # 检查时间段是否重叠
                            if not (end_time <= used_start or start_time >= used_end):
                                overlap = True
                                break
                        
                        if not overlap:
                            found_segment = True
                            break
                        
                        attempts += 1
                    
                    # 如果找不到不重叠的片段，尝试其他视频
                    if not found_segment:
                        # 从视频列表中暂时移除这个视频
                        if len(video_paths) > 1:
                            continue
                        else:
                            # 如果只有一个视频，强制使用可能重叠的片段
                            self.logger.warning(f"无法找到不重叠的片段，使用可能重叠的内容")
                    
                    # 记录使用的时间段
                    used_segments[video_path].append((start_time, end_time))
                    
                    # 提取片段
                    clip = video.subclipped(start_time, end_time)
                    
                    # 统一分辨率为1920x1080 (16:9)
                    target_resolution = (1920, 1080)
                    if clip.size != target_resolution:
                        # 计算缩放比例，保持宽高比
                        clip_aspect = clip.size[0] / clip.size[1]
                        target_aspect = target_resolution[0] / target_resolution[1]
                        
                        if clip_aspect > target_aspect:
                            # 视频更宽，按高度缩放
                            new_height = target_resolution[1]
                            new_width = int(new_height * clip_aspect)
                            clip = clip.resized((new_width, new_height))
                            # 裁剪两边
                            x_center = new_width / 2
                            x1 = x_center - target_resolution[0] / 2
                            clip = clip.cropped(x1=x1, x2=x1 + target_resolution[0], y1=0, y2=target_resolution[1])
                        else:
                            # 视频更高，按宽度缩放
                            new_width = target_resolution[0]
                            new_height = int(new_width / clip_aspect)
                            clip = clip.resized((new_width, new_height))
                            # 裁剪上下
                            y_center = new_height / 2
                            y1 = y_center - target_resolution[1] / 2
                            clip = clip.cropped(x1=0, x2=target_resolution[0], y1=y1, y2=y1 + target_resolution[1])
                    
                    tag_clips.append(clip)
                    current_tag_duration += clip_duration
                    
                    self.logger.info(f"  提取片段: {video_path} [{start_time:.1f}s - {end_time:.1f}s]")
                    
                except Exception as e:
                    self.logger.error(f"处理视频失败 {video_path}: {e}")
                    continue
            
            # 将当前标签的所有片段拼接
            if tag_clips:
                tag_video = concatenate_videoclips(tag_clips, method="compose")
                clips.append(tag_video)
                self.logger.info(f"  标签 {tag_name} 总时长: {tag_video.duration:.1f}秒")
        
        return clips
    
    def _generate_text_content(self, tags: List[str]) -> str:
        """
        使用通义AI生成文案
        
        Args:
            tags: 标签列表
            
        Returns:
            生成的文案
        """
        self.logger.info("使用通义AI生成文案...")
        
        # 构建提示词
        prompt = f"""请根据以下景点/活动标签，生成一段30-50字的旅游宣传文案：
        
标签：{', '.join(tags)}

要求：
1. 文案要生动有吸引力
2. 突出每个景点的特色
3. 语言简洁流畅
4. 适合做视频配音

直接输出文案内容，不要有其他说明。"""
        
        try:
            # 使用 call_qwen 函数
            text = call_qwen(prompt)
            if text and not text.startswith("调用失败"):
                self.logger.info(f"AI生成文案成功: {text}")
                return text
            else:
                # 使用默认文案
                default_text = f"探索{tags[0]}的魅力，体验{tags[-1]}的精彩，这里有最美的风景和难忘的回忆等着你。"
                self.logger.warning(f"AI生成失败: {text}，使用默认文案")
                return default_text
        except Exception as e:
            self.logger.error(f"生成文案失败: {e}")
            # 使用默认文案
            default_text = f"探索{tags[0]}的魅力，体验{tags[-1]}的精彩，这里有最美的风景和难忘的回忆等着你。"
            return default_text
    
    def _get_default_subtitle_config(self) -> Dict:
        """获取默认字幕配置"""
        return {
            'font': 'Arial',
            'font_size': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'grid_position': 8,  # 默认位置：底部中间（九宫格第8格）
            'margin': 50
        }
    
    def _create_aliyun_subtitles(self, video: VideoFileClip, text: str, config: Dict) -> str:
        """
        使用阿里云API创建字幕
        
        Args:
            video: 视频片段
            text: 字幕文本
            config: 字幕配置
            
        Returns:
            字幕时间轴JSON字符串
        """
        if not self.use_aliyun_subtitle or not self.aliyun_subtitle_api:
            self.logger.warning("阿里云字幕API未启用，使用本地字幕")
            return ""
        
        self.logger.info("使用阿里云API创建字幕...")
        
        # 分割文本为字幕片段
        subtitles = self.aliyun_subtitle_api.split_text_for_subtitles(
            text=text,
            video_duration=video.duration,
            max_chars_per_subtitle=config.get('max_chars_per_subtitle', 20),
            min_display_time=config.get('min_display_time', 2.0)
        )
        
        # 应用九宫格位置和样式配置
        grid_position = config.get('grid_position', 8)
        font_size = config.get('font_size', 48)
        font_color = config.get('color', '#FFFFFF')
        outline_color = config.get('stroke_color', '#000000')
        outline_width = config.get('stroke_width', 2)
        
        for subtitle in subtitles:
            subtitle.grid_position = grid_position
            subtitle.font_size = font_size
            subtitle.font_color = font_color
            subtitle.outline_color = outline_color
            subtitle.outline_width = outline_width
        
        # 创建阿里云字幕时间轴
        timeline = self.aliyun_subtitle_api.create_subtitle_timeline(subtitles)
        
        self.logger.info(f"创建了 {len(subtitles)} 个字幕片段，九宫格位置: {grid_position}")
        
        return json.dumps(timeline, ensure_ascii=False, indent=2)
    
    def _add_subtitles(self, video: VideoFileClip, text: str, config: Dict) -> CompositeVideoClip:
        """
        添加字幕到视频 - 使用subtitle_utils的实现
        
        Args:
            video: 视频片段
            text: 字幕文本
            config: 字幕配置
            
        Returns:
            带字幕的视频
        """
        self.logger.info("添加字幕...")
        
        # 如果启用阿里云字幕API，生成配置文件
        if self.use_aliyun_subtitle and self.aliyun_subtitle_api:
            aliyun_subtitle_json = self._create_aliyun_subtitles(video, text, config)
            if aliyun_subtitle_json:
                # 保存阿里云字幕配置到文件
                output_dir = Path("output/aliyun_subtitles")
                output_dir.mkdir(parents=True, exist_ok=True)
                subtitle_file = output_dir / f"subtitle_{hash(text) % 1000000}.json"
                with open(subtitle_file, 'w', encoding='utf-8') as f:
                    f.write(aliyun_subtitle_json)
                self.logger.info(f"阿里云字幕配置已保存到: {subtitle_file}")
        
        # 同时使用本地MoviePy添加字幕到视频中
        self.logger.info("使用本地MoviePy添加字幕...")
        
        # 分割文本为适合显示的片段
        segments = split_text_for_progressive_subtitles(text, max_chars_per_line=25, max_lines=2)
        
        # 计算每个片段的显示时间
        timings = calculate_progressive_subtitle_timings(video.duration, segments)
        
        # 获取项目根目录的字体文件
        project_root = Path(__file__).parent.parent.parent
        font_path = project_root / "江西拙楷2.0.ttf"
        
        # 创建字幕剪辑（支持九宫格位置）
        subtitle_clips = create_subtitle_clips(
            segments=segments,
            timings=timings,
            font=str(font_path) if font_path.exists() else config.get('font', 'Arial'),
            font_size=config.get('font_size', 48),
            color=config.get('color', 'white'),
            stroke_color=config.get('stroke_color', 'black'),
            stroke_width=config.get('stroke_width', 2),
            grid_position=config.get('grid_position', 8)  # 添加九宫格位置参数
        )
        
        # 合成视频和字幕
        if subtitle_clips:
            return CompositeVideoClip([video] + subtitle_clips)
        else:
            return video
    
    def _add_dynamic_tags(
        self,
        video: VideoFileClip,
        tags: List[str],
        tag_config: Dict[str, Dict[str, List[str]]]
    ) -> CompositeVideoClip:
        """
        添加动态标签到视频
        
        Args:
            video: 视频片段
            tags: 标签列表
            tag_config: 标签配置，用于确定每个标签的显示时间
            
        Returns:
            带动态标签的视频
        """
        self.logger.info("添加动态标签...")
        
        # 计算每个标签的显示时间
        duration_per_tag = video.duration / len(tags) if tags else video.duration
        
        # 获取项目根目录的中文字体文件
        project_root = Path(__file__).parent.parent.parent
        font_path = project_root / "江西拙楷2.0.ttf"
        
        # 备用字体路径
        alt_font_path = project_root / "core/cliptemplate/coze/transform/江西拙楷2.0.ttf"
        
        # 选择字体
        if font_path.exists():
            font_to_use = str(font_path)
            self.logger.info(f"动态标签使用字体: {font_path}")
        elif alt_font_path.exists():
            font_to_use = str(alt_font_path)
            self.logger.info(f"动态标签使用备用字体: {alt_font_path}")
        else:
            # macOS 系统中文字体
            system_fonts = [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/PingFang.ttc'
            ]
            font_to_use = None
            for sys_font in system_fonts:
                if Path(sys_font).exists():
                    font_to_use = sys_font
                    self.logger.info(f"动态标签使用系统字体: {sys_font}")
                    break
            
            if not font_to_use:
                font_to_use = 'Helvetica'
                self.logger.warning("未找到中文字体，动态标签可能显示异常")
        
        tag_clips = []
        for i, tag in enumerate(tags):
            # 创建标签文本
            tag_text = f"#{tag}"
            
            try:
                tag_clip = TextClip(
                    text=tag_text,
                    font=font_to_use,
                    font_size=36,
                    color='yellow',
                    stroke_color='black',
                    stroke_width=1
                )
                
                # 设置标签位置（右上角）和显示时间
                tag_clip = tag_clip.with_position(('right', 50))
                tag_clip = tag_clip.with_start(i * duration_per_tag)
                tag_clip = tag_clip.with_duration(duration_per_tag)
                
                tag_clips.append(tag_clip)
                self.logger.info(f"  添加标签: {tag_text} [{i * duration_per_tag:.1f}s - {(i + 1) * duration_per_tag:.1f}s]")
                
            except Exception as e:
                self.logger.error(f"创建动态标签失败 '{tag_text}': {e}")
                # 尝试不使用描边的简单文本
                try:
                    tag_clip = TextClip(
                        text=tag_text,
                        font=font_to_use,
                        font_size=36,
                        color='yellow'
                    )
                    tag_clip = tag_clip.with_position(('right', 50))
                    tag_clip = tag_clip.with_start(i * duration_per_tag)
                    tag_clip = tag_clip.with_duration(duration_per_tag)
                    tag_clips.append(tag_clip)
                    self.logger.info(f"  添加简化标签: {tag_text}")
                except:
                    self.logger.error(f"无法添加动态标签: {tag_text}")
                    continue
        
        # 合成所有元素
        return CompositeVideoClip([video] + tag_clips)
    
    def process_request(
        self,
        request_data: Dict[str, Any],
        output_dir: str = "ikun/output/tag_videos"
    ) -> Dict[str, Any]:
        """
        处理前端请求
        
        Args:
            request_data: 前端请求数据，包含：
                - tag_config: 标签配置
                - text_content: 可选的文案内容
                - subtitle_config: 可选的字幕配置
                - dynamic_tags: 可选的动态标签列表
                - duration_per_tag: 每个标签的时长
            output_dir: 输出目录
            
        Returns:
            处理结果
        """
        try:
            # 解析请求参数
            tag_config = request_data.get('tag_config', {})
            text_content = request_data.get('text_content')
            subtitle_config = request_data.get('subtitle_config')
            dynamic_tags = request_data.get('dynamic_tags')
            duration_per_tag = request_data.get('duration_per_tag', 8.0)
            
            # 验证标签配置
            if not tag_config:
                return {
                    'success': False,
                    'error': '标签配置不能为空'
                }
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"tag_video_{timestamp}.mp4"
            output_path = Path(output_dir) / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 生成视频
            result_path = self.generate_video_from_tags(
                tag_config=tag_config,
                output_path=str(output_path),
                duration_per_tag=duration_per_tag,
                text_content=text_content,
                subtitle_config=subtitle_config,
                dynamic_tags=dynamic_tags
            )
            
            return {
                'success': True,
                'video_path': result_path,
                'message': '视频生成成功'
            }
            
        except Exception as e:
            self.logger.error(f"处理请求失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # 测试代码
    generator = TagVideoGenerator(tag_materials_dir="tag_materials")
    
    # 测试标签配置（支持URL）
    test_config = {
        "黄山风景": {
            "video": ["https://example.com/video1.mp4", "/Users/luming/Downloads/老登.mp4"]
        },
        "徽州特色餐": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        },
        "屯溪老街": {
            "video": ["/Users/luming/Downloads/老登.mp4"]
        }
    }
    
    # 测试生成视频
    output_path = "/tmp/test_tag_video.mp4"
    generator.generate_video_from_tags(
        tag_config=test_config,
        output_path=output_path,
        duration_per_tag=3.0,
        clip_duration_range=(1.0, 2.0)
    )
    
    print(f"测试视频已生成: {output_path}")
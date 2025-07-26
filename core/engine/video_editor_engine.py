# -*- coding: utf-8 -*-
# @Time    : 2025/6/10 09:54
# @Author  : 蔍鸣霸霸
# @FileName: video_editor_engine.py
# @Software: PyCharm
# @Blog    ：只因你太美

# engine/video_editor_engine.py
import os
import json
import subprocess
from typing import Dict, Any, List, Union
from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy import vfx
import tempfile


class VideoEditorEngine:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.original_clip = None
        self.current_clips = []
        self.temp_files = []  # 追踪临时文件

        try:
            self.original_clip = VideoFileClip(video_path)
            self.current_clips = [self.original_clip]
            print(f"✅ 成功加载视频: {video_path}")
        except Exception as e:
            raise ValueError(f"无法加载视频文件: {str(e)}")

    def __del__(self):
        """清理资源"""
        self.cleanup()

    def cleanup(self):
        """清理临时文件和视频资源"""
        try:
            if self.original_clip:
                self.original_clip.close()
            for clip in self.current_clips:
                if clip != self.original_clip:
                    clip.close()
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        except Exception as e:
            print(f"⚠️ 清理资源时出现错误: {e}")

    def execute_actions(self, actions: List[Dict[str, Any]]) -> VideoFileClip:
        """执行一系列剪辑操作"""
        try:
            print(f"🎬 开始执行 {len(actions)} 个剪辑操作...")

            for i, action in enumerate(actions):
                print(f"📝 执行操作 {i + 1}/{len(actions)}: {action.get('function', 'unknown')}")
                self._execute_single_action(action)

            # 合并所有片段
            if len(self.current_clips) == 0:
                print("⚠️ 没有剩余片段，返回原始视频")
                return self.original_clip
            elif len(self.current_clips) == 1:
                final_clip = self.current_clips[0]
            else:
                print("🔗 合并多个片段...")
                final_clip = concatenate_videoclips(self.current_clips, method="compose")

            print("✅ 剪辑操作执行完成")
            return final_clip

        except Exception as e:
            print(f"❌ 剪辑执行失败: {str(e)}")
            return self.original_clip

    def _execute_single_action(self, action: Dict[str, Any]):
        """执行单个剪辑操作"""
        function = action.get("function")

        try:
            if function == "cut":
                self._execute_cut(action)
            elif function == "speedup":
                self._execute_speedup(action)
            elif function == "add_transition":
                self._execute_add_transition(action)
            elif function == "set_resolution":
                self._execute_set_resolution(action)
            elif function == "apply_filter":
                self._execute_apply_filter(action)
            elif function == "merge_clips":
                self._execute_merge_clips(action)
            else:
                print(f"⚠️ 不支持的操作: {function}")

        except Exception as e:
            print(f"❌ 执行操作失败 {function}: {str(e)}")

    def _execute_cut(self, action: Dict[str, Any]):
        """执行裁剪操作"""
        start = action.get("start", 0)
        end = action.get("end")

        if end is None:
            print("⚠️ cut操作缺少end参数")
            return

        # 处理负数时间（从末尾计算）
        duration = self.original_clip.duration
        if start < 0:
            start = duration + start
        if end < 0:
            end = duration + end

        # 确保时间范围有效
        start = max(0, min(start, duration))
        end = max(start, min(end, duration))

        new_clips = []
        for clip in self.current_clips:
            clip_start = getattr(clip, 'start', 0)
            clip_end = getattr(clip, 'end', clip.duration)

            # 如果片段完全在裁剪范围外，保留
            if clip_end <= start or clip_start >= end:
                new_clips.append(clip)
            else:
                # 片段与裁剪范围有重叠，需要分割
                if clip_start < start:
                    # 保留开头部分
                    before_cut = clip.subclip(0, start - clip_start)
                    new_clips.append(before_cut)

                if clip_end > end:
                    # 保留结尾部分
                    after_cut = clip.subclip(end - clip_start, clip_end - clip_start)
                    new_clips.append(after_cut)

        self.current_clips = new_clips
        print(f"✂️ 裁剪完成: 删除 {start:.1f}s - {end:.1f}s")

    def _execute_speedup(self, action: Dict[str, Any]):
        """执行加速操作"""
        start = action.get("start", 0)
        end = action.get("end")
        factor = action.get("factor", 1.0)

        if end is None:
            print("⚠️ speedup操作缺少end参数")
            return

        duration = self.original_clip.duration
        start = max(0, min(start, duration))
        end = max(start, min(end, duration))

        new_clips = []
        for clip in self.current_clips:
            clip_start = getattr(clip, 'start', 0)
            clip_end = getattr(clip, 'end', clip.duration)

            if clip_end <= start or clip_start >= end:
                # 片段不在加速范围内
                new_clips.append(clip)
            else:
                # 需要加速的片段
                if clip_start < start:
                    # 前半部分不加速
                    before_speed = clip.subclip(0, start - clip_start)
                    new_clips.append(before_speed)

                # 中间部分加速
                speed_start = max(0, start - clip_start)
                speed_end = min(clip_end - clip_start, end - clip_start)
                if speed_end > speed_start:
                    speed_part = clip.subclip(speed_start, speed_end).fx(vfx.speedx, factor)
                    new_clips.append(speed_part)

                if clip_end > end:
                    # 后半部分不加速
                    after_speed = clip.subclip(end - clip_start, clip_end - clip_start)
                    new_clips.append(after_speed)

        self.current_clips = new_clips
        print(f"⚡ 加速完成: {start:.1f}s - {end:.1f}s, 倍率: {factor}x")

    def _execute_add_transition(self, action: Dict[str, Any]):
        """执行添加转场操作"""
        transition_type = action.get("type", "crossfade")
        duration = action.get("duration", 0.5)
        start_time = action.get("start", 0)

        if len(self.current_clips) < 2:
            print("⚠️ 需要至少2个片段才能添加转场")
            return

        try:
            # 简单的淡入淡出转场
            if transition_type == "crossfade":
                self._add_crossfade_transition(duration)
            elif transition_type == "fade":
                self._add_fade_transition(duration)
            else:
                print(f"⚠️ 暂不支持转场类型: {transition_type}")

        except Exception as e:
            print(f"❌ 添加转场失败: {str(e)}")

    def _add_crossfade_transition(self, duration: float):
        """添加交叉淡化转场"""
        if len(self.current_clips) < 2:
            return

        # 简化处理：在最后两个片段之间添加转场
        clip1 = self.current_clips[-2]
        clip2 = self.current_clips[-1]

        # 创建转场效果
        if clip1.duration > duration and clip2.duration > duration:
            # 第一个片段的结尾淡出
            fade_out = clip1.fx(vfx.fadeout, duration)
            # 第二个片段的开头淡入
            fade_in = clip2.fx(vfx.fadein, duration)

            # 更新片段列表
            self.current_clips[-2] = fade_out
            self.current_clips[-1] = fade_in

        print(f"🔄 添加交叉淡化转场: {duration}s")

    def _add_fade_transition(self, duration: float):
        """添加淡入淡出转场"""
        for i, clip in enumerate(self.current_clips):
            if clip.duration > duration * 2:
                # 添加淡入淡出效果
                faded_clip = clip.fx(vfx.fadein, duration).fx(vfx.fadeout, duration)
                self.current_clips[i] = faded_clip

        print(f"🌅 添加淡入淡出效果: {duration}s")

    def _execute_set_resolution(self, action: Dict[str, Any]):
        """执行分辨率设置"""
        width = action.get("width", 1920)
        height = action.get("height", 1080)
        orientation = action.get("orientation", "landscape")
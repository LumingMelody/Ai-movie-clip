# -*- coding: utf-8 -*-
# @Time    : 2025/6/14 09:27
# @Author  : 蔍鸣霸霸
# @FileName: video_mcp_server.py
# @Software: PyCharm
# @Blog    ：只因你太美


# !/usr/bin/env python3
"""
Video Processing MCP Server
改造自FastAPI应用，提供视频生成和处理服务
"""

import asyncio
import json
import logging
import os
import threading
import queue
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from threading import Condition

from mcp.server import Server, NotificationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
from pydantic import BaseModel

# 导入原有的核心模块
import config
from core.cliptemplate.coze.video_advertsment import get_video_advertisement
from core.cliptemplate.coze.video_advertsment_enhance import get_video_advertisement_enhance
from core.cliptemplate.coze.video_big_word import get_big_word
from core.cliptemplate.coze.video_catmeme import get_video_catmeme
from core.cliptemplate.coze.video_clicktype import get_video_clicktype
from core.cliptemplate.coze.video_clothes_diffrenent_scene import get_video_clothes_diffrent_scene
from core.cliptemplate.coze.video_dgh_img_insert import get_video_dgh_img_insert
from core.cliptemplate.coze.video_digital_human_clips import get_video_digital_huamn_clips
from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_huamn_easy, \
    get_video_digital_huamn_easy_local
from core.cliptemplate.coze.video_incitment import get_video_incitment
from core.cliptemplate.coze.video_sinology import get_video_sinology
from core.cliptemplate.coze.video_stickman import get_video_stickman
from core.cliptemplate.coze.videos_clothes_fast_change import get_videos_clothes_fast_change
from core.cliptemplate.coze.text_industry import get_text_industry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
task_queue = queue.Queue()
global_lock = threading.Lock()
results = {}
result_condition = Condition()

# 配置路径
MATERIAL_ROOT = os.path.join(config.get_user_data_dir(), "materials")
UPLOAD_DIR = os.path.join(config.get_user_data_dir(), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 创建MCP Server实例
server = Server("video-processing-server")


class VideoProcessingError(Exception):
    """自定义异常类"""
    pass


def extract_warehouse_path(result):
    """提取视频路径，返回相对于warehouse的路径"""
    logger.info(f"提取warehouse路径，输入结果类型: {type(result)}, 内容: {result}")

    video_path = None

    # 提取路径
    if isinstance(result, dict):
        video_path = (result.get("video_path") or
                      result.get("output_path") or
                      result.get("result") or
                      result.get("file_path") or
                      result.get("path") or
                      result.get("output_file") or
                      result.get("video_file"))
    elif isinstance(result, str):
        video_path = result
    else:
        logger.warning(f"无法处理的结果类型: {type(result)}")
        return None

    if not video_path:
        return None

    # 转换为相对于warehouse的路径
    user_data_dir = config.get_user_data_dir()

    # 如果是绝对路径，转换为相对路径
    if os.path.isabs(video_path):
        try:
            relative_path = os.path.relpath(video_path, user_data_dir)
            video_path = relative_path
        except ValueError:
            logger.warning(f"无法转换路径: {video_path}")
            return None

    # 标准化路径分隔符
    warehouse_path = video_path.replace('\\', '/')

    # 移除开头的斜杠
    if warehouse_path.startswith('/'):
        warehouse_path = warehouse_path[1:]

    logger.info(f"warehouse路径: {warehouse_path}")
    return warehouse_path


def process_task(task):
    """处理任务的核心函数"""
    task_id = task["task_id"]
    func_name = task["func_name"]
    args = task["args"]

    start_time = time.time()

    try:
        # 设置初始状态
        with result_condition:
            results[task_id] = {
                "status": "processing",
                "started_at": start_time,
                "current_step": "开始执行",
                "progress": "0%"
            }
            result_condition.notify_all()

        func = globals().get(func_name)
        if not func:
            raise VideoProcessingError(f"Function {func_name} not found")

        logger.info(f"开始执行任务: {task_id}, 函数: {func_name}")
        logger.info(f"参数: {args}")

        # 更新进度
        with result_condition:
            if task_id in results:
                results[task_id].update({
                    "current_step": "正在生成视频",
                    "progress": "50%"
                })
                result_condition.notify_all()

        # 执行实际任务
        result = func(**args)
        logger.info(f"任务 {task_id} 执行成功")

        # 提取warehouse路径
        warehouse_path = extract_warehouse_path(result)
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        with result_condition:
            results[task_id] = {
                "status": "completed",
                "result": result,
                "warehouse_path": warehouse_path,
                "videoPath": warehouse_path,
                "timestamp": end_time,
                "started_at": start_time,
                "processing_time": processing_time,
                "function_name": func_name
            }
            result_condition.notify_all()

    except Exception as e:
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        logger.error(f"任务 {task_id} 执行失败: {str(e)}")
        import traceback
        error_traceback = traceback.format_exc()

        with result_condition:
            results[task_id] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_traceback,
                "timestamp": end_time,
                "started_at": start_time,
                "processing_time": processing_time,
                "function_name": func_name
            }
            result_condition.notify_all()


def worker():
    """后台工作线程"""
    while True:
        task = task_queue.get()
        try:
            process_task(task)
        finally:
            task_queue.task_done()


# 启动工作线程
worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()


async def execute_task_async(func_name: str, args: dict, mode: str = "async"):
    """异步执行任务"""
    task_id = str(uuid.uuid4())
    task_data = {
        "task_id": task_id,
        "func_name": func_name,
        "args": args
    }

    if mode == "sync":
        task_queue.put(task_data)
        timeout_seconds = 1800

        start_time = time.time()
        with result_condition:
            while True:
                elapsed_time = time.time() - start_time
                remaining_time = timeout_seconds - elapsed_time

                if remaining_time <= 0:
                    return {
                        "error": "任务执行超时，但仍在后台处理",
                        "timeout": True,
                        "task_id": task_id
                    }

                if task_id in results:
                    result = results[task_id]
                    if result["status"] in ["completed", "failed"]:
                        break

                result_condition.wait(timeout=min(10, remaining_time))

            final_result = results.pop(task_id)

        if final_result["status"] == "completed":
            return {
                "result": final_result["result"],
                "videoPath": final_result.get("videoPath"),
                "warehouse_path": final_result.get("warehouse_path"),
                "processing_time": final_result.get("processing_time"),
                "function_name": final_result.get("function_name")
            }
        elif final_result["status"] == "failed":
            raise VideoProcessingError(final_result.get("error", "Unknown error occurred"))
    else:
        task_queue.put(task_data)
        return {"task_id": task_id}


# 智能剪辑函数
def get_smart_clip_video(input_source, is_directory=True, company_name="测试公司",
                         text_list=None, audio_durations=None, clip_mode="random",
                         target_resolution=(1920, 1080)):
    """智能剪辑包装器函数"""
    logger.info(f"智能剪辑请求:")
    logger.info(f"   输入源: {input_source}")
    logger.info(f"   剪辑模式: {clip_mode}")
    logger.info(f"   是否目录: {is_directory}")

    # 处理输入路径
    processed_input_source = input_source

    if input_source.startswith("uploads/"):
        processed_input_source = os.path.join(UPLOAD_DIR, input_source.replace("uploads/", ""))
    elif not os.path.isabs(input_source):
        possible_paths = [
            os.path.join(UPLOAD_DIR, input_source),
            os.path.join(MATERIAL_ROOT, input_source),
            input_source
        ]
        for path in possible_paths:
            if os.path.exists(path):
                processed_input_source = path
                break

    logger.info(f"处理后的输入路径: {processed_input_source}")

    if not os.path.exists(processed_input_source):
        raise ValueError(f"输入路径不存在: {processed_input_source}")

    # 生成输出路径
    output_dir = os.path.join(config.get_user_data_dir(), "projects", str(uuid.uuid4()))
    os.makedirs(output_dir, exist_ok=True)

    if clip_mode == "random":
        # 随机剪辑模式的实现
        logger.info("使用随机剪辑模式")

        def create_test_audio_clips_inline(durations):
            import numpy as np
            from moviepy import AudioArrayClip

            audio_clips = []
            for i, duration in enumerate(durations):
                sample_rate = 44100
                samples = int(duration * sample_rate)
                audio_array = np.zeros((samples, 2))
                audio_clip = AudioArrayClip(audio_array, fps=sample_rate)
                audio_clips.append(audio_clip)
                logger.info(f"创建测试音频 {i + 1}: {duration}秒")
            return audio_clips

        def create_complete_advertisement_video_no_text_inline(
                enterprise_source, audio_clips, add_digital_host=False,
                target_resolution=(1920, 1080), output_path="final_advertisement_no_text.mp4"):

            from moviepy import VideoFileClip, concatenate_videoclips, vfx
            import random

            def resolve_materials_inline(source, valid_extensions):
                if not source:
                    return []

                resolved_files = []
                if os.path.isfile(source) and source.lower().endswith(valid_extensions):
                    resolved_files.append(source)
                elif os.path.isdir(source):
                    for f in os.listdir(source):
                        file_path = os.path.join(source, f)
                        if os.path.isfile(file_path) and f.lower().endswith(valid_extensions):
                            resolved_files.append(file_path)
                return resolved_files

            VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')
            enterprise_files = resolve_materials_inline(enterprise_source, VIDEO_EXTENSIONS)

            if not enterprise_files:
                raise ValueError(f"没有找到有效的视频文件: {enterprise_source}")

            logger.info(f"找到 {len(enterprise_files)} 个企业素材文件")

            selected_files = random.sample(enterprise_files, min(len(enterprise_files), len(audio_clips)))
            enterprise_clips = []

            for idx, audio_clip in enumerate(audio_clips):
                if idx >= len(selected_files):
                    break

                video_path = selected_files[idx]

                try:
                    video_clip = VideoFileClip(video_path)

                    if video_clip.size[0] > video_clip.size[1]:
                        video_clip = video_clip.resized(target_resolution)
                    else:
                        vertical_resolution = (target_resolution[1], target_resolution[0])
                        video_clip = video_clip.resized(vertical_resolution)

                    target_duration = audio_clip.duration

                    if video_clip.duration > target_duration:
                        max_start_time = max(0, video_clip.duration - target_duration - 0.1)
                        start_time = random.uniform(0, max_start_time) if max_start_time > 0 else 0
                        video_clip = video_clip.subclipped(start_time, start_time + target_duration)
                    else:
                        loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                        video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                        video_clip = video_clip.subclipped(0, target_duration)

                    video_clip = video_clip.with_audio(audio_clip)
                    enterprise_clips.append(video_clip)
                    logger.info(f"创建企业片段 {len(enterprise_clips)}: {os.path.basename(video_path)}")

                except Exception as e:
                    logger.error(f"创建企业片段失败: {video_path}, 错误: {e}")
                    continue

            if not enterprise_clips:
                raise ValueError("没有成功创建任何视频片段")

            logger.info("开始拼接所有视频片段...")
            final_video = concatenate_videoclips(enterprise_clips, method="compose")

            logger.info(f"开始生成最终视频: {output_path}")
            final_video.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
                audio_codec="aac",
                threads=4
            )

            file_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"最终视频生成完成!")
            logger.info(f"文件路径: {output_path}")
            logger.info(f"文件大小: {file_size:.1f}MB")
            logger.info(f"视频时长: {final_video.duration:.1f}秒")

            try:
                for clip in enterprise_clips:
                    clip.close()
                final_video.close()
            except:
                pass

            return output_path

        if audio_durations:
            audio_duration_list = audio_durations
        else:
            audio_duration_list = [3.0, 4.0, 2.5, 3.5, 5.0]

        audio_clips = create_test_audio_clips_inline(audio_duration_list)
        output_path = os.path.join(output_dir, "random_clip_video.mp4")

        try:
            result_path = create_complete_advertisement_video_no_text_inline(
                enterprise_source=processed_input_source,
                audio_clips=audio_clips,
                add_digital_host=False,
                target_resolution=target_resolution,
                output_path=output_path
            )

            for audio_clip in audio_clips:
                audio_clip.close()

            return result_path

        except Exception as e:
            for audio_clip in audio_clips:
                audio_clip.close()
            raise e

    elif clip_mode == "smart":
        logger.info("使用智能剪辑模式")
        output_path = os.path.join(output_dir, "smart_clip_video.mp4")

        def smart_clips_inline(input_source, output_path, is_directory=True):
            from moviepy import VideoFileClip, concatenate_videoclips

            clips = []

            if is_directory:
                logger.info(f"Processing directory: {input_source}")
                valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']

                for root, _, files in os.walk(input_source):
                    for file in files:
                        file_path = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower()
                        if ext in valid_extensions:
                            logger.info(f"Found video: {file_path}")
                            clip = VideoFileClip(file_path)
                            if clip.size[0] > clip.size[1]:
                                clip = clip.resized(height=1080, width=1920)
                            else:
                                clip = clip.resized(width=1080, height=1920)
                            clips.append(clip)
            else:
                if isinstance(input_source, list):
                    video_paths = input_source
                else:
                    video_paths = [input_source]

                logger.info(f"Processing {len(video_paths)} video(s):")
                for video_path in video_paths:
                    logger.info(f"- {video_path}")
                    clip = VideoFileClip(video_path)
                    if clip.size[0] > clip.size[1]:
                        clip = clip.resized(height=1080, width=1920)
                    else:
                        clip = clip.resized(width=1080, height=1920)
                    clips.append(clip)

            if not clips:
                raise ValueError("No valid video files found!")

            concatenated_clip = concatenate_videoclips(clips, "compose")
            concatenated_clip.write_videofile(
                output_path,
                codec="libx264",
                fps=24,
            )
            logger.info(f"处理完成，结果保存至: {output_path}")

            for clip in clips:
                clip.close()
            concatenated_clip.close()

        smart_clips_inline(
            input_source=processed_input_source,
            output_path=output_path,
            is_directory=is_directory
        )

        return output_path

    else:
        raise ValueError(f"不支持的剪辑模式: {clip_mode}，支持的模式: random, smart")


# 注册资源
@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """列出可用的资源"""
    resources = []

    # 材料库资源
    if os.path.exists(MATERIAL_ROOT):
        resources.append(Resource(
            uri="file:///materials",
            name="Video Materials",
            description="视频素材库",
            mimeType="application/json"
        ))

    # 上传目录资源
    if os.path.exists(UPLOAD_DIR):
        resources.append(Resource(
            uri="file:///uploads",
            name="Uploaded Files",
            description="上传的文件目录",
            mimeType="application/json"
        ))

    return resources


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri == "file:///materials":
        # 返回材料库文件列表
        materials = []
        if os.path.exists(MATERIAL_ROOT):
            for root, dirs, files in os.walk(MATERIAL_ROOT):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), MATERIAL_ROOT)
                    materials.append({
                        "name": file,
                        "path": rel_path,
                        "size": os.path.getsize(os.path.join(root, file))
                    })
        return json.dumps(materials, indent=2)

    elif uri == "file:///uploads":
        # 返回上传文件列表
        uploads = []
        if os.path.exists(UPLOAD_DIR):
            for file in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, file)
                if os.path.isfile(file_path):
                    uploads.append({
                        "name": file,
                        "path": f"uploads/{file}",
                        "size": os.path.getsize(file_path)
                    })
        return json.dumps(uploads, indent=2)

    else:
        raise ValueError(f"Unknown resource: {uri}")


# 注册工具
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="generate_video_advertisement",
            description="生成视频广告",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "公司名称"},
                    "service": {"type": "string", "description": "服务内容"},
                    "topic": {"type": "string", "description": "主题"},
                    "content": {"type": "string", "description": "内容（可选）"},
                    "need_change": {"type": "boolean", "description": "是否需要修改", "default": False},
                    "mode": {"type": "string", "enum": ["sync", "async"], "default": "async"}
                },
                "required": ["company_name", "service", "topic"]
            }
        ),
        Tool(
            name="generate_big_word_video",
            description="生成大字视频",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "公司名称"},
                    "title": {"type": "string", "description": "标题"},
                    "product": {"type": "string", "description": "产品"},
                    "description": {"type": "string", "description": "描述"},
                    "content": {"type": "string", "description": "内容（可选）"},
                    "mode": {"type": "string", "enum": ["sync", "async"], "default": "async"}
                },
                "required": ["company_name", "title", "product", "description"]
            }
        ),
        Tool(
            name="generate_catmeme_video",
            description="生成猫咪表情包视频",
            inputSchema={
                "type": "object",
                "properties": {
                    "author": {"type": "string", "description": "作者"},
                    "title": {"type": "string", "description": "标题"},
                    "content": {"type": "string", "description": "内容（可选）"},
                    "mode": {"type": "string", "enum": ["sync", "async"], "default": "async"}
                },
                "required": ["author", "title"]
            }
        ),
        Tool(
            name="generate_digital_human_video",
            description="生成数字人视频",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "视频文件路径"},
                    "topic": {"type": "string", "description": "主题"},
                    "audio_url": {"type": "string", "description": "音频URL"},
                    "content": {"type": "string", "description": "内容（可选）"},
                    "mode": {"type": "string", "enum": ["sync", "async"], "default": "async"}
                },
                "required": ["file_path", "topic", "audio_url"]
            }
        ),
        Tool(
            name="clip_video",
            description="智能视频剪辑",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_source": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": "输入源：单个文件路径、文件路径列表或目录路径"
                    },
                    "clip_mode": {"type": "string", "enum": ["smart", "random"], "default": "smart"},
                    "company_name": {"type": "string", "default": "测试公司"},
                    "audio_durations": {"type": "string", "default": "3.0,4.0,2.5,3.5,5.0"},
                    "target_width": {"type": "integer", "default": 1920},
                    "target_height": {"type": "integer", "default": 1080},
                    "mode": {"type": "string", "enum": ["sync", "async"], "default": "async"}
                },
                "required": ["input_source"]
            }
        ),
        Tool(
            name="get_task_result",
            description="获取异步任务结果",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务ID"},
                    "remove": {"type": "boolean", "description": "是否移除结果", "default": False}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="list_tasks",
            description="列出所有任务状态",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "generate_video_advertisement":
            mode = arguments.pop("mode", "async")
            res = await execute_task_async("get_video_advertisement", arguments, mode)

            if mode == "sync":
                if "videoPath" in res:
                    return [TextContent(
                        type="text",
                        text=f"视频广告生成成功！\n视频路径: {res['videoPath']}\n处理时间: {res.get('processing_time', 0)}秒"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"视频广告生成失败: {res.get('error', '未知错误')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"视频广告生成任务已提交，任务ID: {res['task_id']}\n请使用 get_task_result 工具查询结果"
                )]

        elif name == "generate_big_word_video":
            mode = arguments.pop("mode", "async")
            res = await execute_task_async("get_big_word", arguments, mode)

            if mode == "sync":
                if "videoPath" in res:
                    return [TextContent(
                        type="text",
                        text=f"大字视频生成成功！\n视频路径: {res['videoPath']}\n处理时间: {res.get('processing_time', 0)}秒"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"大字视频生成失败: {res.get('error', '未知错误')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"大字视频生成任务已提交，任务ID: {res['task_id']}\n请使用 get_task_result 工具查询结果"
                )]

        elif name == "generate_catmeme_video":
            mode = arguments.pop("mode", "async")
            res = await execute_task_async("get_video_catmeme", arguments, mode)

            if mode == "sync":
                if "videoPath" in res:
                    return [TextContent(
                        type="text",
                        text=f"猫咪表情包视频生成成功！\n视频路径: {res['videoPath']}\n处理时间: {res.get('processing_time', 0)}秒"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"猫咪表情包视频生成失败: {res.get('error', '未知错误')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"猫咪表情包视频生成任务已提交，任务ID: {res['task_id']}\n请使用 get_task_result 工具查询结果"
                )]

        elif name == "generate_digital_human_video":
            mode = arguments.pop("mode", "async")
            res = await execute_task_async("get_video_digital_huamn_easy_local", arguments, mode)

            if mode == "sync":
                if "videoPath" in res:
                    return [TextContent(
                        type="text",
                        text=f"数字人视频生成成功！\n视频路径: {res['videoPath']}\n处理时间: {res.get('processing_time', 0)}秒"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"数字人视频生成失败: {res.get('error', '未知错误')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"数字人视频生成任务已提交，任务ID: {res['task_id']}\n请使用 get_task_result 工具查询结果"
                )]

        elif name == "clip_video":
            mode = arguments.pop("mode", "async")

            # 处理输入源参数
            input_source = arguments.get("input_source")
            if not input_source:
                return [TextContent(
                    type="text",
                    text="错误: 必须提供 input_source 参数"
                )]

            # 解析音频时长
            audio_durations_str = arguments.get("audio_durations", "3.0,4.0,2.5,3.5,5.0")
            try:
                audio_durations = [float(d.strip()) for d in audio_durations_str.split(',') if d.strip()]
                if not audio_durations:
                    audio_durations = [3.0, 4.0, 2.5, 3.5, 5.0]
            except ValueError:
                return [TextContent(
                    type="text",
                    text="错误: 音频时长格式错误，应为数字列表如：3.0,4.0,2.5"
                )]

            # 构建剪辑参数
            clip_args = {
                "input_source": input_source,
                "is_directory": isinstance(input_source, str) and os.path.isdir(input_source),
                "company_name": arguments.get("company_name", "测试公司"),
                "audio_durations": audio_durations,
                "clip_mode": arguments.get("clip_mode", "smart"),
                "target_resolution": (
                    arguments.get("target_width", 1920),
                    arguments.get("target_height", 1080)
                )
            }

            res = await execute_task_async("get_smart_clip_video", clip_args, mode)

            if mode == "sync":
                if "videoPath" in res:
                    return [TextContent(
                        type="text",
                        text=f"视频剪辑完成！\n视频路径: {res['videoPath']}\n剪辑模式: {clip_args['clip_mode']}\n处理时间: {res.get('processing_time', 0)}秒"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"视频剪辑失败: {res.get('error', '未知错误')}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"视频剪辑任务已提交，任务ID: {res['task_id']}\n剪辑模式: {clip_args['clip_mode']}\n请使用 get_task_result 工具查询结果"
                )]

        elif name == "get_task_result":
            task_id = arguments.get("task_id")
            remove = arguments.get("remove", False)

            if not task_id:
                return [TextContent(
                    type="text",
                    text="错误: 必须提供 task_id 参数"
                )]

            with result_condition:
                if task_id not in results:
                    return [TextContent(
                        type="text",
                        text=f"任务不存在: {task_id}\n可能已被删除或任务ID错误"
                    )]

                if remove:
                    result = results.pop(task_id)
                else:
                    result = results[task_id]

                task_status = result.get("status", "unknown")

                if task_status == "completed":
                    warehouse_path = result.get("videoPath") or result.get("warehouse_path")
                    return [TextContent(
                        type="text",
                        text=f"任务完成: {task_id}\n状态: 成功\n视频路径: {warehouse_path}\n处理时间: {result.get('processing_time', 0)}秒\n函数: {result.get('function_name', 'unknown')}"
                    )]

                elif task_status == "failed":
                    return [TextContent(
                        type="text",
                        text=f"任务失败: {task_id}\n错误: {result.get('error', '未知错误')}\n错误类型: {result.get('error_type', 'Unknown')}\n处理时间: {result.get('processing_time', 0)}秒"
                    )]

                elif task_status == "processing":
                    return [TextContent(
                        type="text",
                        text=f"任务处理中: {task_id}\n当前步骤: {result.get('current_step', '未知')}\n进度: {result.get('progress', '未知')}"
                    )]

                else:
                    return [TextContent(
                        type="text",
                        text=f"任务状态未知: {task_id}\n状态: {task_status}"
                    )]

        elif name == "list_tasks":
            with result_condition:
                if not results:
                    return [TextContent(
                        type="text",
                        text="当前没有活跃的任务"
                    )]

                task_info = []
                for task_id, result in results.items():
                    status = result.get("status", "unknown")
                    function_name = result.get("function_name", "unknown")

                    if status == "completed":
                        warehouse_path = result.get("videoPath") or result.get("warehouse_path")
                        task_info.append(f"✅ {task_id[:8]}... | {function_name} | 完成 | {warehouse_path}")
                    elif status == "failed":
                        error = result.get("error", "未知错误")
                        task_info.append(f"❌ {task_id[:8]}... | {function_name} | 失败 | {error[:50]}...")
                    elif status == "processing":
                        progress = result.get("progress", "未知")
                        task_info.append(f"🔄 {task_id[:8]}... | {function_name} | 处理中 | {progress}")
                    else:
                        task_info.append(f"❓ {task_id[:8]}... | {function_name} | {status}")

                return [TextContent(
                    type="text",
                    text=f"任务列表 ({len(results)} 个任务):\n" + "\n".join(task_info)
                )]

        else:
            return [TextContent(
                type="text",
                text=f"未知工具: {name}"
            )]

    except Exception as e:
        logger.error(f"工具调用失败: {name}, 错误: {str(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return [TextContent(
            type="text",
            text=f"工具调用失败: {str(e)}"
        )]


async def main():
    """主函数"""
    # 使用标准输入输出运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="video-processing-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    # 添加缺少的导入
    from mcp.server.models import InitializationOptions

    asyncio.run(main())
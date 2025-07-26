# -*- coding: utf-8 -*-
# @Time    : 2025/6/19 10:00
# @Author  : Claude AI
# @FileName: mcp_enhanced_video_generation_server.py
# @Software: PyCharm
# @Blog    : MCP Enhanced Video Generation

"""
MCP增强的视频生成服务器
结合FastAPI和MCP协议，提供强大的视频生成和任务管理功能
"""

import argparse
import threading
import queue
import time
import asyncio
import json
import uuid
import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from threading import Condition

# FastAPI相关导入
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# MCP相关导入
try:
    from mcp.server.fastmcp import FastMCP
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    from mcp.types import TextContent, Tool, Resource

    MCP_AVAILABLE = True
except ImportError:
    print("⚠️ MCP SDK未安装，请运行: pip install mcp")
    MCP_AVAILABLE = False


    # 创建模拟类以避免导入错误
    class FastMCP:
        def __init__(self, name): pass

        def tool(self): pass

        def sse_app(self): pass


    class ClientSession:
        pass


    class StdioServerParameters:
        pass

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置和模块导入
import config

# 视频处理模块导入
try:
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
    from download_material import download_materials_from_api
except ImportError as e:
    print(f"警告: 导入视频处理模块失败 {e}")
    print("请确保所有必要的模块都在正确的路径中")

# ========== 全局配置 ==========
# 目录设置
path = config.get_user_data_dir()
if not os.path.exists(path):
    os.makedirs(path)

MATERIAL_ROOT = os.path.join(config.get_user_data_dir(), "materials")
UPLOAD_DIR = os.path.join(config.get_user_data_dir(), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 全局变量
task_queue = queue.Queue()
results = {}
result_condition = Condition()
temp_dirs = []  # 存储临时目录，用于清理

# ========== FastAPI 初始化 ==========
app = FastAPI(title="MCP Enhanced Video Generation API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost", "http://localhost:5174", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/warehouse", StaticFiles(directory=path, check_dir=True), name='warehouse')
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
urlpath = "http://localhost:8100/warehouse/"
print(f"Mounted folder 'warehouse' at (Path: {path})")

# ========== MCP 服务器初始化 ==========
if MCP_AVAILABLE:
    mcp = FastMCP("MCP Enhanced Video Generation Server")
else:
    mcp = None


# ========== 数据模型定义 ==========
class MaterialQueryParams(BaseModel):
    page: int = 1
    page_size: int = 10
    keyword: Optional[str] = None
    path: Optional[str] = ""


class MaterialItem(BaseModel):
    id: str
    name: str
    type: str
    path: str


class MaterialPageResponse(BaseModel):
    records: List[MaterialItem]
    total: int


class VideoTaskRequest(BaseModel):
    """通用视频任务请求模型"""
    task_type: str
    parameters: Dict[str, Any]
    mode: str = "async"
    use_mcp_enhancement: bool = False


class VideoAdvertisementRequest(BaseModel):
    company_name: str
    service: str
    topic: str
    content: Optional[str] = None
    need_change: bool = False
    categoryId: str


class BigWordRequest(BaseModel):
    company_name: str
    title: str
    product: str
    description: str
    categoryId: str
    content: Optional[str] = None


class CatMemeRequest(BaseModel):
    author: str
    title: str
    content: Optional[str] = None
    categoryId: str


class ClickTypeRequest(BaseModel):
    title: str
    content: Optional[str] = None
    categoryId: str


class ClothesDifferentSceneRequest(BaseModel):
    has_figure: bool
    clothesurl: str
    description: str
    categoryId: str
    is_down: bool = True


class DigitalHumanEasyRequest(BaseModel):
    file_path: str
    topic: str
    audio_url: str
    categoryId: str

class IncitementRequest(BaseModel):
    title: str
    categoryId: str

class SinologyRequest(BaseModel):
    title: str
    content: Optional[str] = None
    categoryId: str

class StickmanRequest(BaseModel):
    author: str
    title: str
    content: Optional[str] = None
    lift_text: str = "科普动画"
    categoryId: str

class ClothesFastChangeRequest(BaseModel):
    has_figure: bool
    clothesurl: str
    description: str
    categoryId: str
    is_down: bool = True

class TextIndustryRequest(BaseModel):
    industry: str
    is_hot: bool = True
    content: Optional[str] = None
    categoryId: str

class VideoRandomRequest(BaseModel):
    enterprise: str
    product: str
    description: str
    categoryId: str

class DGHImgInsertRequest(BaseModel):
    title: str
    video_file_path: str
    content: Optional[str] = None
    need_change: bool = False
    categoryId: str

class DigitalHumanClipsRequest(BaseModel):
    video_file_path: str
    topic: str
    audio_path: str
    content: Optional[str] = None
    categoryId: str

class VideoAdvertisementEnhanceRequest(BaseModel):
    company_name: str
    service: str
    topic: str
    content: Optional[str] = None
    need_change: bool = False
    add_digital_host: bool = True
    use_temp_materials: bool = False
    clip_mode: bool = True
    upload_digital_host: bool = False
    moderator_source: Optional[str] = None
    enterprise_source: Optional[Union[List[str], str]] = None
    categoryId: str

class SmartClipRequest(BaseModel):
    input_source: str
    is_directory: bool = True
    company_name: str = "测试公司"
    text_list: Optional[List[str]] = None
    audio_durations: Optional[List[float]] = None
    clip_mode: str = "random"
    target_resolution: tuple = (1920, 1080)


# ========== 辅助功能函数 ==========
class VideoEditingError(Exception):
    """自定义异常类"""
    pass


def get_video_random(enterprise: str, product: str, description: str, categoryId: str):
    """随机视频生成函数"""
    import random
    kind = int(random.randint(1, 7))

    if kind == 1:
        return get_video_advertisement(enterprise, description, product, categoryId)
    elif kind == 2:
        return get_big_word(enterprise, product, description, categoryId)
    elif kind == 3:
        return get_video_clicktype(product, description, categoryId)
    elif kind == 4:
        return get_video_catmeme(enterprise, product, description, categoryId)
    elif kind == 5:
        return get_video_incitment(product, categoryId)
    elif kind == 6:
        return get_video_stickman(enterprise, product, description, categoryId)
    else:
        return get_video_sinology(product, description, categoryId)


def is_url(string: str) -> bool:
    """检查字符串是否为有效的URL"""
    import urllib.parse
    try:
        result = urllib.parse.urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False


def download_video_from_url(url: str) -> str:
    """从URL下载视频到临时目录"""
    try:
        import requests
        import urllib.parse

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="mcp_video_download_")
        temp_dirs.append(temp_dir)  # 记录用于清理

        # 获取文件名
        parsed_url = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = f"downloaded_video_{int(time.time())}.mp4"

        output_path = os.path.join(temp_dir, filename)

        # 下载文件
        print(f"正在下载视频: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"下载完成: {output_path}")
        return output_path

    except Exception as e:
        raise VideoEditingError(f"下载视频失败: {str(e)}")


def collect_video_files(paths: List[str]) -> List[str]:
    """收集视频文件，支持本地文件和URL"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
    video_files = []

    for path in paths:
        try:
            if is_url(path):
                # 处理URL
                if any(ext in path.lower() for ext in
                       video_extensions) or 'youtube' in path.lower() or 'bilibili' in path.lower():
                    try:
                        downloaded_path = download_video_from_url(path)
                        video_files.append(downloaded_path)
                        print(f"成功下载视频: {path}")
                    except Exception as e:
                        print(f"下载失败: {path}, 错误: {e}")
                        continue
                else:
                    print(f"不支持的URL类型: {path}")

            elif os.path.isfile(path):
                # 处理本地文件
                if path.lower().endswith(video_extensions):
                    video_files.append(path)
                    print(f"找到本地视频: {path}")
                else:
                    print(f"跳过非视频文件: {path}")

            elif os.path.isdir(path):
                # 处理目录
                found_count = 0
                for file in os.listdir(path):
                    if file.lower().endswith(video_extensions):
                        video_files.append(os.path.join(path, file))
                        found_count += 1
                print(f"目录中找到 {found_count} 个视频文件: {path}")

            else:
                print(f"路径不存在: {path}")

        except Exception as e:
            print(f"处理路径 {path} 时出错: {e}")

    return video_files


def cleanup_temp_dirs():
    """清理临时目录"""
    global temp_dirs
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"清理临时目录失败: {e}")
    temp_dirs.clear()


def extract_warehouse_path(result):
    """提取视频路径，返回相对于warehouse的路径"""
    print(f"提取warehouse路径，输入结果类型: {type(result)}, 内容: {result}")

    video_path = None

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
        print(f"无法处理的结果类型: {type(result)}")
        return None

    if not video_path:
        return None

    user_data_dir = config.get_user_data_dir()

    if os.path.isabs(video_path):
        try:
            relative_path = os.path.relpath(video_path, user_data_dir)
            video_path = relative_path
        except ValueError:
            print(f"⚠️ 无法转换路径: {video_path}")
            return None

    warehouse_path = video_path.replace('\\', '/')

    if warehouse_path.startswith('/'):
        warehouse_path = warehouse_path[1:]

    print(f"✅ warehouse路径: {warehouse_path}")
    return warehouse_path


def verify_file_exists(warehouse_path):
    """验证文件是否真实存在"""
    if not warehouse_path:
        return False

    user_data_dir = config.get_user_data_dir()
    full_path = os.path.join(user_data_dir, warehouse_path.replace('/', os.path.sep))
    return os.path.exists(full_path)


def get_full_file_path(warehouse_path):
    """根据warehouse路径获取完整的文件系统路径"""
    if not warehouse_path:
        return None

    user_data_dir = config.get_user_data_dir()
    full_path = os.path.join(user_data_dir, warehouse_path.replace('/', os.path.sep))
    return os.path.normpath(full_path)


# ========== 智能视频剪辑功能 ==========
def get_smart_clip_video(input_source, is_directory=True, company_name="测试公司",
                         text_list=None, audio_durations=None, clip_mode="random",
                         target_resolution=(1920, 1080)):
    """智能剪辑包装器函数"""
    print(f"🎬 智能剪辑请求:")
    print(f"   输入源: {input_source}")
    print(f"   剪辑模式: {clip_mode}")
    print(f"   是否目录: {is_directory}")

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

    print(f"📁 处理后的输入路径: {processed_input_source}")

    if not os.path.exists(processed_input_source):
        raise ValueError(f"输入路径不存在: {processed_input_source}")

    output_dir = os.path.join(config.get_user_data_dir(), "projects", str(uuid.uuid4()))
    os.makedirs(output_dir, exist_ok=True)

    if clip_mode == "random":
        print("🎲 使用随机剪辑模式")
        return _perform_random_clip(processed_input_source, output_dir, audio_durations, target_resolution)
    elif clip_mode == "smart":
        print("🧠 使用智能剪辑模式")
        return _perform_smart_clip(processed_input_source, output_dir, is_directory, target_resolution)
    else:
        raise ValueError(f"不支持的剪辑模式: {clip_mode}，支持的模式: random, smart")


def _perform_random_clip(input_source, output_dir, audio_durations, target_resolution):
    """执行随机剪辑"""

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
            print(f"🎵 创建测试音频 {i + 1}: {duration}秒")
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

        print(f"📁 找到 {len(enterprise_files)} 个企业素材文件")

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
                print(f"✅ 创建企业片段 {len(enterprise_clips)}: {os.path.basename(video_path)}")

            except Exception as e:
                print(f"❌ 创建企业片段失败: {video_path}, 错误: {e}")
                continue

        if not enterprise_clips:
            raise ValueError("没有成功创建任何视频片段")

        print("🔗 开始拼接所有视频片段...")
        final_video = concatenate_videoclips(enterprise_clips, method="compose")

        print(f"🎬 开始生成最终视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4
        )

        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ 最终视频生成完成!")
        print(f"📄 文件路径: {output_path}")
        print(f"📊 文件大小: {file_size:.1f}MB")
        print(f"⏱️  视频时长: {final_video.duration:.1f}秒")

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
            enterprise_source=input_source,
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


def _perform_smart_clip(input_source, output_dir, is_directory, target_resolution):
    """执行智能剪辑"""
    output_path = os.path.join(output_dir, "smart_clip_video.mp4")

    def smart_clips_inline(input_source, output_path, is_directory=True):
        from moviepy import VideoFileClip, concatenate_videoclips

        clips = []

        if is_directory:
            print(f"Processing directory: {input_source}")
            valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']

            for root, _, files in os.walk(input_source):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_extensions:
                        print(f"Found video: {file_path}")
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

            print(f"Processing {len(video_paths)} video(s):")
            for video_path in video_paths:
                print(f"- {video_path}")
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
        print(f"✅ 处理完成，结果保存至: {output_path}")

        for clip in clips:
            clip.close()
        concatenated_clip.close()

    smart_clips_inline(
        input_source=input_source,
        output_path=output_path,
        is_directory=is_directory
    )

    return output_path


# ========== 任务处理系统 ==========
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
                "progress": "0%",
                "function_name": func_name
            }
            result_condition.notify_all()

        func = globals().get(func_name)
        if not func:
            raise VideoEditingError(f"Function {func_name} not found")

        print(f"开始执行任务: {task_id}, 函数: {func_name}")

        # 执行实际任务
        result = func(**args)

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        # 提取warehouse路径
        warehouse_path = extract_warehouse_path(result)
        full_path = get_full_file_path(warehouse_path) if warehouse_path else None
        file_exists = verify_file_exists(warehouse_path) if warehouse_path else False

        with result_condition:
            results[task_id] = {
                "status": "completed",
                "result": result,
                "warehouse_path": warehouse_path,
                "videoPath": warehouse_path,
                "full_file_path": full_path,
                "file_exists": file_exists,
                "timestamp": end_time,
                "started_at": start_time,
                "processing_time": processing_time,
                "function_name": func_name
            }
            result_condition.notify_all()

    except Exception as e:
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        print(f"任务 {task_id} 执行失败: {str(e)}")
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
        timeout_seconds = 1800  # 30分钟超时

        start_time = time.time()
        with result_condition:
            while True:
                elapsed_time = time.time() - start_time
                remaining_time = timeout_seconds - elapsed_time

                if remaining_time <= 0:
                    return {
                        "error": "任务执行超时",
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
            return final_result
        elif final_result["status"] == "failed":
            raise VideoEditingError(final_result.get("error", "Unknown error occurred"))
    else:
        task_queue.put(task_data)
        return {"task_id": task_id}


# ========== MCP工具定义 ==========
if MCP_AVAILABLE:

    from fastapi import Request
    from fastapi.responses import JSONResponse
    import json

    @mcp.tool()
    async def generate_clicktype_video(
            title: str,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成点击类型视频

        Args:
            title: 标题
            content: 内容（可选）
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "title": title,
                "content": content
            }

            res = await execute_task_async("get_video_clicktype", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 点击类型视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 标题: {title}"
                else:
                    return f"❌ 点击类型视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 点击类型视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 点击类型视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_stickman_video(
            author: str,
            title: str,
            content: str = None,
            lift_text: str = "科普动画",
            mode: str = "async"
    ) -> str:
        """
        生成火柴人视频

        Args:
            author: 作者
            title: 标题
            content: 内容（可选）
            lift_text: 提升文本
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "author": author,
                "title": title,
                "content": content,
                "lift_text": lift_text
            }

            res = await execute_task_async("get_video_stickman", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 火柴人视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n👤 作者: {author}\n📝 标题: {title}"
                else:
                    return f"❌ 火柴人视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 火柴人视频任务已提交\n📋 任务ID: {res['task_id']}\n👤 作者: {author}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 火柴人视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_industry_text(
            industry: str,
            is_hot: bool = True,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成行业相关文本

        Args:
            industry: 行业名称
            is_hot: 是否为热门
            content: 内容（可选）
            mode: 执行模式

        Returns:
            文本生成结果的字符串描述
        """
        try:
            args = {
                "industry": industry,
                "is_hot": is_hot,
                "content": content
            }

            res = await execute_task_async("get_text_industry", args, mode)

            if mode == "sync":
                result_text = res.get("result", "")
                return f"✅ 行业文本生成完成！\n🏭 行业: {industry}\n🔥 热门: {'是' if is_hot else '否'}\n📝 生成文本:\n{result_text}"
            else:
                return f"✅ 行业文本任务已提交\n📋 任务ID: {res['task_id']}\n🏭 行业: {industry}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 行业文本生成失败: {str(e)}"


    @mcp.tool()
    async def generate_clothes_change_video(
            has_figure: bool,
            clothesurl: str,
            description: str,
            is_down: bool = True,
            mode: str = "async"
    ) -> str:
        """
        生成服装快速变换视频

        Args:
            has_figure: 是否有人物
            clothesurl: 服装URL
            description: 描述
            is_down: 是否向下
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "has_figure": has_figure,
                "clothesurl": clothesurl,
                "description": description,
                "is_down": is_down
            }

            res = await execute_task_async("get_videos_clothes_fast_change", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 服装变换视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n👥 有人物: {'是' if has_figure else '否'}\n👗 服装URL: {clothesurl}\n📝 描述: {description}"
                else:
                    return f"❌ 服装变换视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 服装变换视频任务已提交\n📋 任务ID: {res['task_id']}\n👗 服装URL: {clothesurl}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 服装变换视频生成失败: {str(e)}"

    @mcp.tool()
    async def generate_video_advertisement(
            company_name: str,
            service: str,
            topic: str,
            content: str = None,
            need_change: bool = False,
            mode: str = "async"
    ) -> str:
        """
        生成视频广告

        Args:
            company_name: 公司名称
            service: 服务类型
            topic: 主题
            content: 内容描述（可选）
            need_change: 是否需要变更
            mode: 执行模式，'sync'同步执行，'async'异步执行

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "company_name": company_name,
                "service": service,
                "topic": topic,
                "content": content,
                "need_change": need_change
            }

            res = await execute_task_async("get_video_advertisement", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 视频广告生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n🎬 公司: {company_name}\n📝 主题: {topic}"
                else:
                    return f"❌ 视频广告生成失败: 无法提取文件路径\n原始结果: {res.get('result', 'Unknown')}"
            else:
                return f"✅ 视频广告任务已提交\n📋 任务ID: {res['task_id']}\n🎬 公司: {company_name}\n📝 主题: {topic}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 视频广告生成失败: {str(e)}"


    @mcp.tool()
    async def generate_big_word_video(
            company_name: str,
            title: str,
            product: str,
            description: str,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成大字视频

        Args:
            company_name: 公司名称
            title: 标题
            product: 产品
            description: 描述
            content: 内容（可选）
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "company_name": company_name,
                "title": title,
                "product": product,
                "description": description,
                "content": content
            }

            res = await execute_task_async("get_big_word", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 大字视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n🎬 公司: {company_name}\n📝 标题: {title}\n🛍️ 产品: {product}"
                else:
                    return f"❌ 大字视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 大字视频任务已提交\n📋 任务ID: {res['task_id']}\n🎬 公司: {company_name}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 大字视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_catmeme_video(
            author: str,
            title: str,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成猫咪表情包视频

        Args:
            author: 作者
            title: 标题
            content: 内容（可选）
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "author": author,
                "title": title,
                "content": content
            }

            res = await execute_task_async("get_video_catmeme", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 猫咪表情包视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n👤 作者: {author}\n📝 标题: {title}"
                else:
                    return f"❌ 猫咪表情包视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 猫咪表情包视频任务已提交\n📋 任务ID: {res['task_id']}\n👤 作者: {author}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 猫咪表情包视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_digital_human_video(
            file_path: str,
            topic: str,
            audio_url: str,
            mode: str = "async"
    ) -> str:
        """
        生成数字人视频

        Args:
            file_path: 视频文件路径
            topic: 主题
            audio_url: 音频URL
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "file_path": file_path,
                "topic": topic,
                "audio_url": audio_url
            }

            res = await execute_task_async("get_video_digital_huamn_easy_local", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 数字人视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 主题: {topic}\n🎵 音频: {audio_url}"
                else:
                    return f"❌ 数字人视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 数字人视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 主题: {topic}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 数字人视频生成失败: {str(e)}"


    @mcp.tool()
    async def smart_video_clip(
            input_source: str,
            clip_mode: str = "smart",
            company_name: str = "测试公司",
            audio_durations: str = "3.0,4.0,2.5,3.5,5.0",
            target_width: int = 1920,
            target_height: int = 1080,
            mode: str = "async"
    ) -> str:
        """
        智能视频剪辑

        Args:
            input_source: 输入视频源（文件路径或目录）
            clip_mode: 剪辑模式（smart/random）
            company_name: 公司名称
            audio_durations: 音频时长列表（逗号分隔）
            target_width: 目标宽度
            target_height: 目标高度
            mode: 执行模式

        Returns:
            视频剪辑结果的字符串描述
        """
        try:
            # 解析音频时长
            try:
                audio_duration_list = [float(d.strip()) for d in audio_durations.split(',') if d.strip()]
                if not audio_duration_list:
                    audio_duration_list = [3.0, 4.0, 2.5, 3.5, 5.0]
            except (ValueError, AttributeError):
                audio_duration_list = [3.0, 4.0, 2.5, 3.5, 5.0]

            # 判断是否为目录
            is_directory = os.path.isdir(input_source) if os.path.exists(input_source) else True

            args = {
                "input_source": input_source,
                "is_directory": is_directory,
                "company_name": company_name,
                "audio_durations": audio_duration_list,
                "clip_mode": clip_mode,
                "target_resolution": (target_width, target_height)
            }

            res = await execute_task_async("get_smart_clip_video", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 视频剪辑完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n🎬 剪辑模式: {clip_mode}\n🏢 公司: {company_name}\n📏 分辨率: {target_width}x{target_height}"
                else:
                    return f"❌ 视频剪辑失败: 无法提取文件路径"
            else:
                return f"✅ 视频剪辑任务已提交\n📋 任务ID: {res['task_id']}\n🎬 剪辑模式: {clip_mode}\n🏢 公司: {company_name}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 视频剪辑失败: {str(e)}"


    @mcp.tool()
    async def generate_video_advertisement_enhance(
            company_name: str,
            service: str,
            topic: str,
            content: str = None,
            need_change: bool = False,
            add_digital_host: bool = True,
            use_temp_materials: bool = False,
            clip_mode: bool = True,
            upload_digital_host: bool = False,
            moderator_source: str = None,
            enterprise_source: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成增强版视频广告

        Args:
            company_name: 公司名称
            service: 服务类型
            topic: 主题
            content: 内容描述（可选）
            need_change: 是否需要变更
            add_digital_host: 是否添加数字主持人
            use_temp_materials: 是否使用临时素材
            clip_mode: 剪辑模式
            upload_digital_host: 是否上传数字主持人
            moderator_source: 主持人素材源
            enterprise_source: 企业素材源
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "company_name": company_name,
                "service": service,
                "topic": topic,
                "content": content,
                "need_change": need_change,
                "add_digital_host": add_digital_host,
                "use_temp_materials": use_temp_materials,
                "clip_mode": clip_mode,
                "upload_digital_host": upload_digital_host,
                "moderator_source": moderator_source,
                "enterprise_source": enterprise_source
            }

            res = await execute_task_async("get_video_advertisement_enhance", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 增强版视频广告生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n🎬 公司: {company_name}\n📝 主题: {topic}\n🤖 数字主持人: {'是' if add_digital_host else '否'}"
                else:
                    return f"❌ 增强版视频广告生成失败: 无法提取文件路径"
            else:
                return f"✅ 增强版视频广告任务已提交\n📋 任务ID: {res['task_id']}\n🎬 公司: {company_name}\n📝 主题: {topic}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 增强版视频广告生成失败: {str(e)}"


    @mcp.tool()
    async def generate_dgh_img_insert_video(
            title: str,
            video_file_path: str,
            content: str = None,
            need_change: bool = False,
            mode: str = "async"
    ) -> str:
        """
        生成数字人图片插入视频

        Args:
            title: 标题
            video_file_path: 视频文件路径
            content: 内容（可选）
            need_change: 是否需要变更
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "title": title,
                "video_file_path": video_file_path,
                "content": content,
                "need_change": need_change
            }

            res = await execute_task_async("get_video_dgh_img_insert", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 数字人图片插入视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 标题: {title}\n🎬 视频路径: {video_file_path}"
                else:
                    return f"❌ 数字人图片插入视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 数字人图片插入视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 数字人图片插入视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_digital_human_clips_video(
            video_file_path: str,
            topic: str,
            audio_path: str,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成数字人剪辑视频

        Args:
            video_file_path: 视频文件路径
            topic: 主题
            audio_path: 音频路径
            content: 内容（可选）
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "video_file_path": video_file_path,
                "topic": topic,
                "audio_path": audio_path,
                "content": content
            }

            res = await execute_task_async("get_video_digital_huamn_clips", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 数字人剪辑视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 主题: {topic}\n🎬 视频路径: {video_file_path}\n🎵 音频路径: {audio_path}"
                else:
                    return f"❌ 数字人剪辑视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 数字人剪辑视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 主题: {topic}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 数字人剪辑视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_incitement_video(
            title: str,
            mode: str = "async"
    ) -> str:
        """
        生成煽动类视频

        Args:
            title: 标题
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "title": title
            }

            res = await execute_task_async("get_video_incitment", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 煽动类视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 标题: {title}"
                else:
                    return f"❌ 煽动类视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 煽动类视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 煽动类视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_sinology_video(
            title: str,
            content: str = None,
            mode: str = "async"
    ) -> str:
        """
        生成国学视频

        Args:
            title: 标题
            content: 内容（可选）
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "title": title,
                "content": content
            }

            res = await execute_task_async("get_video_sinology", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 国学视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n📝 标题: {title}"
                else:
                    return f"❌ 国学视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 国学视频任务已提交\n📋 任务ID: {res['task_id']}\n📝 标题: {title}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 国学视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_clothes_different_scene_video(
            has_figure: bool,
            clothesurl: str,
            description: str,
            is_down: bool = True,
            mode: str = "async"
    ) -> str:
        """
        生成服装不同场景视频

        Args:
            has_figure: 是否有人物
            clothesurl: 服装URL
            description: 描述
            is_down: 是否向下
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "has_figure": has_figure,
                "clothesurl": clothesurl,
                "description": description,
                "is_down": is_down
            }

            res = await execute_task_async("get_video_clothes_diffrent_scene", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 服装不同场景视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n👥 有人物: {'是' if has_figure else '否'}\n👗 服装URL: {clothesurl}\n📝 描述: {description}"
                else:
                    return f"❌ 服装不同场景视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 服装不同场景视频任务已提交\n📋 任务ID: {res['task_id']}\n👗 服装URL: {clothesurl}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 服装不同场景视频生成失败: {str(e)}"


    @mcp.tool()
    async def generate_random_video(
            enterprise: str,
            product: str,
            description: str,
            mode: str = "async"
    ) -> str:
        """
        生成随机视频（从多种类型中随机选择）

        Args:
            enterprise: 企业名称
            product: 产品
            description: 描述
            mode: 执行模式

        Returns:
            视频生成结果的字符串描述
        """
        try:
            args = {
                "enterprise": enterprise,
                "product": product,
                "description": description
            }

            res = await execute_task_async("get_video_random", args, mode)

            if mode == "sync":
                warehouse_path = res.get("warehouse_path") or res.get("videoPath")
                if warehouse_path:
                    return f"✅ 随机视频生成完成！\n📄 文件路径: {warehouse_path}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒\n🏢 企业: {enterprise}\n🛍️ 产品: {product}\n📝 描述: {description}"
                else:
                    return f"❌ 随机视频生成失败: 无法提取文件路径"
            else:
                return f"✅ 随机视频任务已提交\n📋 任务ID: {res['task_id']}\n🏢 企业: {enterprise}\n🛍️ 产品: {product}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 随机视频生成失败: {str(e)}"


    @mcp.tool()
    async def download_materials(
            api_url: str = None,
            download_path: str = None,
            mode: str = "async"
    ) -> str:
        """
        下载素材

        Args:
            api_url: API地址（可选）
            download_path: 下载路径（可选）
            mode: 执行模式

        Returns:
            下载结果的字符串描述
        """
        try:
            args = {
                "api_url": api_url,
                "download_path": download_path
            }

            res = await execute_task_async("download_materials_from_api", args, mode)

            if mode == "sync":
                result = res.get("result", "")
                return f"✅ 素材下载完成！\n📥 下载结果: {result}\n⏱️ 处理时间: {res.get('processing_time', 0)}秒"
            else:
                return f"✅ 素材下载任务已提交\n📋 任务ID: {res['task_id']}\n\n💡 使用以下命令查询结果：\nget_task_result(task_id=\"{res['task_id']}\")"

        except Exception as e:
            return f"❌ 素材下载失败: {str(e)}"

    @mcp.tool()
    async def get_task_result(
            task_id: str,
            remove: bool = False
    ) -> str:
        """
        获取异步任务结果

        Args:
            task_id: 任务ID
            remove: 是否移除结果

        Returns:
            任务结果的字符串描述
        """
        if not task_id:
            return "❌ 错误: 必须提供任务ID"

        with result_condition:
            if task_id not in results:
                return f"❌ 任务不存在: {task_id}\n可能已被删除或任务ID错误\n\n💡 使用 list_active_tasks() 查看所有任务"

            if remove:
                result = results.pop(task_id)
            else:
                result = results[task_id]

            task_status = result.get("status", "unknown")
            function_name = result.get("function_name", "unknown")

            if task_status == "completed":
                warehouse_path = result.get("warehouse_path") or result.get("videoPath")
                processing_time = result.get("processing_time", 0)
                file_exists = result.get("file_exists", False)

                result_text = f"✅ 任务完成: {task_id[:8]}...\n"
                result_text += f"🔧 功能: {function_name}\n"
                result_text += f"⏱️ 处理时间: {processing_time}秒\n"

                if warehouse_path:
                    result_text += f"📄 文件路径: {warehouse_path}\n"
                    result_text += f"📁 文件存在: {'是' if file_exists else '否'}\n"
                else:
                    result_text += f"⚠️ 未找到输出文件路径\n"

                result_text += "=" * 50

                return result_text

            elif task_status == "failed":
                error = result.get("error", "未知错误")
                error_type = result.get("error_type", "Unknown")
                processing_time = result.get("processing_time", 0)

                error_text = f"❌ 任务失败: {task_id[:8]}...\n"
                error_text += f"🔧 功能: {function_name}\n"
                error_text += f"💥 错误: {error}\n"
                error_text += f"🏷️ 错误类型: {error_type}\n"
                error_text += f"⏱️ 处理时间: {processing_time}秒"

                return error_text

            elif task_status == "processing":
                progress = result.get("progress", "未知")
                current_step = result.get("current_step", "未知")
                started_at = result.get("started_at", 0)
                elapsed = time.time() - started_at if started_at else 0

                return f"🔄 任务处理中: {task_id[:8]}...\n🔧 功能: {function_name}\n📊 进度: {progress}\n📍 当前步骤: {current_step}\n⏱️ 已用时间: {elapsed:.1f}秒\n\n💡 请稍后再次查询结果"

            else:
                return f"❓ 任务状态未知: {task_id[:8]}...\n🔧 功能: {function_name}\n📊 状态: {task_status}"


    @mcp.tool()
    async def list_active_tasks() -> str:
        """
        列出所有活跃的任务

        Returns:
            活跃任务列表的字符串描述
        """
        with result_condition:
            if not results:
                return "📋 当前没有活跃的任务"

            task_list = []
            for task_id, result in results.items():
                status = result.get("status", "unknown")
                function_name = result.get("function_name", "unknown")
                started_at = result.get("started_at", 0)
                elapsed = time.time() - started_at if started_at else 0

                # 状态图标
                status_icon = {
                    "completed": "✅",
                    "failed": "❌",
                    "processing": "🔄"
                }.get(status, "❓")

                task_info = f"{status_icon} {task_id[:8]}... | {function_name} | {status}"

                if status == "processing":
                    progress = result.get("progress", "")
                    task_info += f" | {progress} | {elapsed:.1f}s"
                elif status in ["completed", "failed"]:
                    processing_time = result.get("processing_time", 0)
                    task_info += f" | {processing_time:.1f}s"

                task_list.append(task_info)

            task_text = f"📋 活跃任务列表 ({len(results)} 个):\n\n"
            task_text += "\n".join(task_list)

            return task_text


    @mcp.tool()
    async def cleanup_temp_files() -> str:
        """
        清理临时文件和目录

        Returns:
            清理结果的字符串描述
        """
        cleanup_temp_dirs()
        return "🗑️ 临时文件清理完成！\n已清理所有下载的视频文件和临时目录。"


    @mcp.tool()
    async def get_server_info() -> str:
        """
        获取服务器信息

        Returns:
            服务器信息的字符串描述
        """
        return json.dumps({
            "server": "MCP Enhanced Video Generation Server",
            "version": "2.0.0",
            "status": "running",
            "timestamp": time.time(),
            "active_tasks": len(results),
            "temp_dirs": len(temp_dirs),
            "supported_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
            "available_functions": [
                # 原有功能
                "generate_video_advertisement",
                "generate_big_word_video",
                "generate_catmeme_video",
                "generate_digital_human_video",
                "smart_video_clip",
                # 新增功能
                "generate_clicktype_video",
                "generate_stickman_video",
                "generate_industry_text",
                "generate_clothes_change_video",
                "generate_video_advertisement_enhance",
                "generate_dgh_img_insert_video",
                "generate_digital_human_clips_video",
                "generate_incitement_video",
                "generate_sinology_video",
                "generate_clothes_different_scene_video",
                "generate_random_video",
                "download_materials",
                # 系统功能
                "get_task_result",
                "list_active_tasks",
                "cleanup_temp_files",
                "get_server_info"
            ]
        }, indent=2, ensure_ascii=False)


# ========== 素材库功能 ==========
def list_materials_in_dir(base_path: str, keyword: Optional[str] = None) -> List[MaterialItem]:
    """列出指定目录下的素材"""
    full_path = os.path.join(MATERIAL_ROOT, base_path.lstrip("/"))
    if not os.path.exists(full_path):
        return []

    items = []
    for idx, name in enumerate(sorted(os.listdir(full_path))):
        item_path = os.path.join(base_path, name)
        full_item_path = os.path.join(full_path, name)

        if keyword and keyword.lower() not in name.lower():
            continue

        is_dir = os.path.isdir(full_item_path)
        items.append(MaterialItem(
            id=str(idx + 1),
            name=name,
            type="folder" if is_dir else "file",
            path=item_path
        ))
    return items


def format_response(res, mode, urlpath):
    """统一格式化响应，返回warehouse路径和完整路径"""
    if mode == "sync":
        if isinstance(res, dict) and res.get("timeout"):
            return {
                "status": "timeout",
                "error": res["error"],
                "timeout": True,
                "task_id": res["task_id"],
                "message": res["message"]
            }

        if isinstance(res, dict) and "error" in res and not res.get("timeout"):
            return {
                "status": "error",
                "error": res["error"],
                "task_id": res.get("task_id"),
                "message": res.get("message", "任务执行出现错误")
            }

        warehouse_path = res.get("warehouse_path") or res.get("videoPath")
        if warehouse_path:
            user_data_dir = config.get_user_data_dir()
            full_path = os.path.join(user_data_dir, warehouse_path)
            file_exists = os.path.exists(full_path)

            return {
                "status": "completed",
                "videoPath": warehouse_path,
                "fullPath": full_path,
                "warehouse_path": warehouse_path,
                "full_file_path": full_path,
                "file_exists": file_exists,
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name")
            }
        else:
            return {
                "status": "completed",
                "videoPath": None,
                "fullPath": None,
                "raw_result": res.get("result"),
                "error": "无法提取视频路径",
                "processing_time": res.get("processing_time")
            }
    else:
        return {
            "task_id": res["task_id"],
            "status": "submitted",
            "message": "任务已提交，请使用查询接口获取任务结果"
        }


# ========== FastAPI 路由 ==========
@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "MCP Enhanced Video Generation Server",
        "version": "2.0.0",
        "status": "running",
        "description": "MCP增强的视频生成服务器，支持智能分析和剪辑",
        "sse_endpoint": "/sse" if MCP_AVAILABLE else None,
        "mcp_available": MCP_AVAILABLE,
        "mcp_tools": [
            "generate_video_advertisement",
            "generate_big_word_video",
            "generate_catmeme_video",
            "generate_digital_human_video",
            "smart_video_clip",
            "get_task_result",
            "list_active_tasks",
            "cleanup_temp_files",
            "get_server_info"
        ] if MCP_AVAILABLE else []
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_tasks": len(results),
        "temp_dirs": len(temp_dirs),
        "mcp_available": MCP_AVAILABLE
    }


@app.get("/tasks")
async def get_all_tasks():
    """获取所有任务状态"""
    with result_condition:
        return {
            "total_tasks": len(results),
            "tasks": {
                task_id: {
                    "status": result.get("status"),
                    "function_name": result.get("function_name"),
                    "started_at": result.get("started_at"),
                    "processing_time": result.get("processing_time")
                }
                for task_id, result in results.items()
            }
        }


# ========== FastAPI 文件上传 ==========
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """文件上传接口"""
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        return {
            "code": 0,
            "data": {
                "filename": file.filename,
                "url": f"http://localhost:8100/uploads/{file.filename}",
                "warehouse_path": f"uploads/{file.filename}",
                "full_path": file_path,
                "file_size": os.path.getsize(file_path),
                "upload_success": True
            },
            "msg": ""
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 1,
                "data": None,
                "msg": f"文件上传失败: {str(e)}"
            }
        )


# ========== FastAPI 素材库接口 ==========
@app.api_route("/material/all/page", methods=["GET", "POST"], response_model=MaterialPageResponse)
async def get_material_all_page(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        keyword: Optional[str] = None,
        path: Optional[str] = ""
):
    """获取素材库分页数据"""
    all_items = list_materials_in_dir(path, keyword)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = all_items[start:end]

    print(f"Requested page {page} with size {page_size}, total items: {len(all_items)}")
    return {
        "records": [item.dict() for item in paginated_items],
        "total": len(all_items)
    }


# ========== FastAPI 视频生成接口 ==========
@app.post("/video/advertisement")
async def api_get_video_advertisement(
        req: VideoAdvertisementRequest,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """视频广告生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_advertisement", filtered_args, mode)
    return format_response(res, mode, urlpath)


@app.post("/video/big-word")
async def api_get_big_word(
        req: BigWordRequest,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """大字视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_big_word", filtered_args, mode)
    return format_response(res, mode, urlpath)


@app.post("/video/catmeme")
async def api_get_video_catmeme(
        req: CatMemeRequest,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """猫咪表情包视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_catmeme", filtered_args, mode)
    return format_response(res, mode, urlpath)


@app.post("/video/digital-human-easy")
async def api_get_video_digital_human_easy(
        req: DigitalHumanEasyRequest,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """数字人视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_digital_huamn_easy_local", filtered_args, mode)
    return format_response(res, mode, urlpath)


@app.post("/video/clip")
async def clip_video(
        req: SmartClipRequest,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """智能视频剪辑接口"""
    res = await execute_task_async("get_smart_clip_video", req.dict(), mode)
    return format_response(res, mode, urlpath)

@app.post("/video/advertisement-enhance")
async def api_get_video_advertisement_enhance(
    req: VideoAdvertisementEnhanceRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """视频广告增强版接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_advertisement_enhance", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/clicktype")
async def api_get_video_clicktype(
    req: ClickTypeRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """点击类型视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_clicktype", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/dgh-img-insert")
async def api_get_video_dgh_img_insert(
    req: DGHImgInsertRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """数字人图片插入视频接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_dgh_img_insert", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/digital-human-clips")
async def api_get_video_digital_huamn_clips(
    req: DigitalHumanClipsRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """数字人剪辑视频接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_digital_huamn_clips", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/incitement")
async def api_get_video_incitment(
    req: IncitementRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """煽动类视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_incitment", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/sinology")
async def api_get_video_sinology(
    req: SinologyRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """国学视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_sinology", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/stickman")
async def api_get_video_stickman(
    req: StickmanRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """火柴人视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_stickman", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/clothes-fast-change")
async def api_get_videos_clothes_fast_change(
    req: ClothesFastChangeRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """服装快速变换视频接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_videos_clothes_fast_change", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/video/random")
async def api_get_video_random(
    req: VideoRandomRequest,
    mode: str = Query("async", description="执行模式：sync(同步)/async(异步)")
):
    """随机视频生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_video_random", filtered_args, mode)
    return format_response(res, mode, urlpath)

@app.post("/text/industry")
async def api_get_text_industry(req: TextIndustryRequest, mode: str = "sync"):
    """行业文本生成接口"""
    filtered_args = {key: value for key, value in req.dict().items() if key != 'categoryId'}
    res = await execute_task_async("get_text_industry", filtered_args, mode)
    if mode == "sync":
        return {"result": res["result"]}
    else:
        return {"task_id": res["task_id"]}

# ========== FastAPI 任务查询接口 ==========
@app.get("/get-result/{task_id}")
async def get_task_result_api(task_id: str, remove: bool = Query(False, description="是否移除结果")):
    """获取任务结果"""
    with result_condition:
        if task_id not in results:
            return {
                "status": "not_found",
                "task_id": task_id,
                "message": "任务不存在，可能已被删除或任务ID错误",
                "queue_size": task_queue.qsize()
            }

        if remove:
            result = results.pop(task_id)
        else:
            result = results[task_id]

        task_status = result.get("status", "unknown")

        if task_status == "completed":
            warehouse_path = result.get("videoPath") or result.get("warehouse_path")
            full_path = None
            file_exists = result.get("file_exists", False)

            if warehouse_path:
                user_data_dir = config.get_user_data_dir()
                full_path = os.path.join(user_data_dir, warehouse_path)
                file_exists = os.path.exists(full_path)

            return {
                "status": "completed",
                "task_id": task_id,
                "message": "任务处理完成",
                "videoPath": warehouse_path,
                "fullPath": full_path,
                "warehouse_path": warehouse_path,
                "full_file_path": full_path,
                "file_exists": file_exists,
                "result": result.get("result"),
                "removed": remove,
                "timestamp": result.get("timestamp"),
                "processing_time": result.get("processing_time"),
                "function_name": result.get("function_name")
            }

        elif task_status == "failed":
            return {
                "status": "failed",
                "task_id": task_id,
                "message": f"任务处理失败: {result.get('error', '未知错误')}",
                "error": result.get("error", "未知错误"),
                "error_type": result.get("error_type", "Unknown"),
                "removed": remove,
                "timestamp": result.get("timestamp"),
                "processing_time": result.get("processing_time"),
                "function_name": result.get("function_name")
            }

        elif task_status == "processing":
            return {
                "status": "processing",
                "task_id": task_id,
                "message": "任务正在处理中",
                "progress": result.get("progress", "未知"),
                "current_step": result.get("current_step", "未知"),
                "started_at": result.get("started_at")
            }

        else:
            return {
                "status": "unknown",
                "task_id": task_id,
                "message": f"任务状态未知: {task_status}",
                "raw_result": result,
                "removed": remove
            }


# ==================== 挂载MCP SSE应用 ====================

# 将MCP的SSE应用挂载到FastAPI
app.mount("/", mcp.sse_app())


# ========== 启动配置 ==========
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Enhanced Video Generation Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8100, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    # 打印启动信息
    print(f"""
🎬 MCP Enhanced Video Generation Server
======================================
🌐 Host: {args.host}
🔌 Port: {args.port}
🔄 Reload: {args.reload}
📝 Log Level: {args.log_level}
📡 MCP Available: {MCP_AVAILABLE}

📚 Available Endpoints:
  🌐 Web Interface: http://{args.host}:{args.port}
  📖 API Documentation: http://{args.host}:{args.port}/docs
  🔧 Health Check: http://{args.host}:{args.port}/health
  📊 Task Status: http://{args.host}:{args.port}/tasks
  📁 File Upload: http://{args.host}:{args.port}/upload
  📦 Materials: http://{args.host}:{args.port}/material/all/page
  {'📡 MCP SSE Endpoint: http://' + args.host + ':' + str(args.port) + '/sse' if MCP_AVAILABLE else '❌ MCP Not Available'}

🎥 Video Generation APIs:
  📺 Advertisement: POST /video/advertisement
  🎯 Big Word: POST /video/big-word
  🐱 Cat Meme: POST /video/catmeme
  🤖 Digital Human: POST /video/digital-human-easy
  ✂️ Smart Clip: POST /video/clip

🛠️ Available MCP Tools:
  📹 generate_video_advertisement - 生成视频广告
  🎯 generate_big_word_video - 生成大字视频
  🐱 generate_catmeme_video - 生成猫咪表情包视频
  🤖 generate_digital_human_video - 生成数字人视频
  ✂️ smart_video_clip - 智能视频剪辑
  🎬 generate_clicktype_video - 生成点击类型视频
  🤸 generate_stickman_video - 生成火柴人视频
  🏭 generate_industry_text - 生成行业文本
  👗 generate_clothes_change_video - 生成服装变换视频
  🎨 generate_video_advertisement_enhance - 生成增强版视频广告
  🖼️ generate_dgh_img_insert_video - 生成数字人图片插入视频
  🎞️ generate_digital_human_clips_video - 生成数字人剪辑视频
  🔥 generate_incitement_video - 生成煽动类视频
  📚 generate_sinology_video - 生成国学视频
  👔 generate_clothes_different_scene_video - 生成服装不同场景视频
  🎲 generate_random_video - 生成随机视频
  📥 download_materials - 下载素材
  📊 get_task_result - 获取任务结果
  📝 list_active_tasks - 列出活跃任务
  🗑️ cleanup_temp_files - 清理临时文件
  ℹ️ get_server_info - 获取服务器信息

📋 Usage Examples (MCP Tools):
{('  • generate_video_advertisement(company_name="测试公司", service="AI服务", topic="人工智能")' if MCP_AVAILABLE else '')}
{('  • smart_video_clip(input_source="/path/to/videos", clip_mode="smart")' if MCP_AVAILABLE else '')}
{('  • get_task_result(task_id="your-task-id")' if MCP_AVAILABLE else '')}
{('  • list_active_tasks()' if MCP_AVAILABLE else '')}

🚀 Starting server...
    """)

    try:
        uvicorn.run(
            "__main__:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        print("🧹 正在清理临时文件...")
        cleanup_temp_dirs()
        print("✅ 清理完成，再见！")
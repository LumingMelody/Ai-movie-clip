import argparse
import threading
import queue
import time
import asyncio
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core.clipgenerate.interface_function import get_smart_clip_video, download_file_from_url, upload_to_oss, \
    OSS_BUCKET_NAME, OSS_ENDPOINT, get_file_info
from core.clipgenerate.interface_model import VideoRandomRequest, ProductConfigRequest, VoiceConfigRequest, \
    ServerStartRequest, ServerStopRequest, TextIndustryRequest, CopyGenerationRequest, CoverAnalysisRequest, \
    BigWordRequest, CatMemeRequest, ClickTypeRequest, VideoAdvertisementRequest, VideoAdvertisementEnhanceRequest, \
    ClothesDifferentSceneRequest, SmartClipRequest, DGHImgInsertRequest, DigitalHumanClipsRequest, IncitementRequest, \
    SinologyRequest, StickmanRequest, ClothesFastChangeRequest, DigitalHumanRequest, VideoEditMainRequest
from core.clipgenerate.tongyi_wangxiang_model import (
    TextToImageV2Request, TextToImageV1Request,
    AITryonBasicRequest, AITryonPlusRequest,
    VirtualModelV1Request, VirtualModelV2Request,
    BackgroundGenerationRequest, ImageBackgroundEditRequest,
    ImageInpaintingRequest, PersonalPortraitRequest,
    DoodlePaintingRequest, ArtisticTextRequest,
    ImageUpscaleRequest, ImageStyleTransferRequest, VideoStyleTransferRequest, ImageOutpaintingRequest,
    ShoeModelRequest, CreativePosterRequest, AITryonEnhanceRequest, AITryonSegmentRequest,
    ImageToVideoAdvancedRequest, TextToVideoRequest, VideoEditRequest, AnimateAnyoneRequest, EMOVideoRequest,
    LivePortraitRequest
)

from core.clipgenerate.tongyi_wangxiang import (
    # 文生图系列
    get_text_to_image_v2, get_text_to_image_v1,
    # 图像编辑系列
    get_image_background_edit,
    # 虚拟模特系列
    get_virtual_model_v1, get_virtual_model_v2, get_shoe_model,
    get_creative_poster, get_background_generation,
    # AI试衣系列
    get_ai_tryon_basic, get_ai_tryon_plus, get_ai_tryon_enhance,
    get_ai_tryon_segment,
    # 视频生成系列
    get_image_to_video_advanced,
    # 数字人视频系列
    get_animate_anyone, get_emo_video, get_live_portrait,
    # 视频风格重绘
    get_video_style_transform,

)

from core.cliptemplate.coze.video_cover_analyzer import CoverAnalyzer, AnalyzeResponse
import oss2
import requests
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from flask import jsonify, request
from pydantic import BaseModel, Field
import uvicorn
import uuid
from typing import Optional, Union, Dict, List, Any
from threading import Condition
import config
import os
from core.cliptemplate.coze.auto_live_reply import SocketServer, config_manager
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
from core.cliptemplate.coze.video_generate_live import  process_single_video_by_url
from core.cliptemplate.coze.video_incitment import get_video_incitment
from core.cliptemplate.coze.video_sinology import get_video_sinology
from core.cliptemplate.coze.video_stickman import get_video_stickman
from core.cliptemplate.coze.videos_clothes_fast_change import get_videos_clothes_fast_change
from core.cliptemplate.coze.text_industry import get_text_industry
from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator
from core.text_generate.generator import get_copy_generation, CopyGenerator

# ========== FastAPI 初始化 ==========
app = FastAPI()
# 全局变量存储Socket服务器实例
socket_server = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",
                   "http://localhost",
                   "http://localhost:5174",
                   "http://127.0.0.1", ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

path = config.get_user_data_dir()
if not os.path.exists(path):
    os.makedirs(path)
app.mount("/warehouse", StaticFiles(directory=path, check_dir=True), name='warehouse')
urlpath = "http://localhost:8100/warehouse/"
print(f"Mounted folder 'warehouse' at (Path: {path})")
MATERIAL_ROOT = os.path.join(config.get_user_data_dir(), "materials")

# ========== 全局变量 ==========
task_queue = queue.Queue()
global_lock = threading.Lock()
results = {}
result_condition = Condition()
websocket_connections = {}

# ========== 🔥 修复的路径提取函数 ==========
def extract_warehouse_path(result):
    """
    🔥 修复版：提取视频路径，支持列表、字典、字符串等多种格式
    """
    print(f"🔍 提取warehouse路径，输入结果类型: {type(result)}, 内容: {result}")

    video_path = None

    # 🔥 新增：处理AI试衣分割的特殊情况
    if isinstance(result, dict) and any(key in result for key in ['parsing_img_url', 'crop_img_url']):
        print(f"🖼️ 检测到AI试衣分割结果，包含多个图片URL")
        # 这种情况需要特殊处理，返回特殊标识
        return "MULTI_IMAGE_URLS"

    # 🔥 新增：处理列表类型的结果
    if isinstance(result, list):
        print(f"📋 处理列表结果，共 {len(result)} 个项目")
        if len(result) > 0:
            # 取第一个有效的路径
            for item in result:
                if isinstance(item, str) and item.strip():
                    video_path = item.strip()
                    print(f"✅ 从列表中提取到路径: {video_path}")
                    break
                elif isinstance(item, dict):
                    # 如果列表项是字典，递归提取
                    extracted = extract_warehouse_path(item)
                    if extracted:
                        video_path = extracted
                        print(f"✅ 从列表字典项中提取到路径: {video_path}")
                        break

        if not video_path:
            print(f"⚠️ 列表中没有找到有效路径")
            return None

    # 处理字典类型
    elif isinstance(result, dict):
        video_path = (result.get("warehouse_path") or
                      result.get("video_path") or
                      result.get("output_path") or
                      result.get("result") or
                      result.get("file_path") or
                      result.get("path") or
                      result.get("output_file") or
                      result.get("video_file"))

        # 如果字典中的值也是列表，递归处理
        if isinstance(video_path, list):
            video_path = extract_warehouse_path(video_path)

    # 处理字符串类型
    elif isinstance(result, str):
        video_path = result.strip() if result else None

    else:
        print(f"⚠️ 无法处理的结果类型: {type(result)}")
        return None

    if not video_path:
        print(f"⚠️ 未找到有效的视频路径")
        return None

    # 🔥 关键处理：转换为相对于warehouse的路径
    user_data_dir = config.get_user_data_dir()

    # 如果是绝对路径，转换为相对路径
    if os.path.isabs(video_path):
        try:
            # 获取相对于用户数据目录的路径
            relative_path = os.path.relpath(video_path, user_data_dir)
            video_path = relative_path
            print(f"🔄 转换绝对路径为相对路径: {relative_path}")
        except ValueError:
            print(f"⚠️ 无法转换路径: {video_path}")
            return None

    # 标准化路径分隔符（统一使用正斜杠）
    warehouse_path = video_path.replace('\\', '/')

    # 移除开头的斜杠（如果有）
    if warehouse_path.startswith('/'):
        warehouse_path = warehouse_path[1:]

    print(f"✅ 最终warehouse路径: {warehouse_path}")
    return warehouse_path

def verify_file_exists(warehouse_path):
    """
    验证文件是否真实存在
    """
    if not warehouse_path:
        return False

    user_data_dir = config.get_user_data_dir()
    full_path = os.path.join(user_data_dir, warehouse_path.replace('/', os.path.sep))
    return os.path.exists(full_path)

def get_full_file_path(warehouse_path):
    """
    根据warehouse路径获取完整的文件系统路径
    """
    if not warehouse_path:
        return None

    user_data_dir = config.get_user_data_dir()
    full_path = os.path.join(user_data_dir, warehouse_path.replace('/', os.path.sep))
    return os.path.normpath(full_path)

# 🔥 修复后的任务处理函数
def process_task(task):
    """带超时控制的任务处理函数"""
    task_id = task["task_id"]
    func_name = task["func_name"]
    args = task["args"]

    # 设置任务超时时间（30分钟）
    TASK_TIMEOUT = 1800  # 30分钟

    print(f"\n🔥 [DEBUG] 开始处理任务: {task_id}")
    print(f"   函数名: {func_name}")
    print(f"   参数: {args}")
    print(f"   超时时间: {TASK_TIMEOUT}秒")

    start_time = time.time()

    try:
        # 更新状态为处理中
        with result_condition:
            results[task_id] = {
                "task_id": task_id,
                "function_name": func_name,
                "status": "processing",
                "started_at": start_time,
                "progress": "0%",
                "current_step": "开始处理",
                "input_params": args.copy()
            }
            result_condition.notify_all()

        print(f"🔄 [DEBUG] 任务 {task_id} 状态已更新为 processing")

        # 检查函数是否存在
        func = globals().get(func_name)
        if not func:
            raise ValueError(f"函数不存在: {func_name}")

        print(f"✅ [DEBUG] 找到函数: {func_name}")

        # 更新进度
        with result_condition:
            results[task_id].update({
                "current_step": "执行函数",
                "progress": "20%"
            })
            result_condition.notify_all()

        print(f"🚀 [DEBUG] 开始执行函数: {func_name}")

        # 🔥 关键修改：使用线程池执行函数，并设置超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            # 提交任务到线程池
            future = executor.submit(func, **args)

            try:
                # 等待结果，设置超时
                result = future.result(timeout=TASK_TIMEOUT)
                print(f"✅ [DEBUG] 函数执行完成: {func_name}")

            except TimeoutError:
                print(f"⏰ [DEBUG] 函数执行超时: {func_name}")
                # 尝试取消任务
                future.cancel()
                raise TimeoutError(f"函数 {func_name} 执行超时 ({TASK_TIMEOUT}秒)")

        print(f"   结果类型: {type(result)}")
        print(f"   结果内容: {str(result)[:200]}...")

        # 处理结果
        warehouse_path = extract_warehouse_path(result)
        full_path = get_full_file_path(warehouse_path) if warehouse_path else None
        file_exists = verify_file_exists(warehouse_path) if warehouse_path else False

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        print(f"📊 [DEBUG] 处理结果:")
        print(f"   warehouse路径: {warehouse_path}")
        print(f"   完整路径: {full_path}")
        print(f"   文件存在: {file_exists}")
        print(f"   处理时间: {processing_time}秒")

        # 更新最终结果
        final_result = {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "warehouse_path": warehouse_path,
            "videoPath": warehouse_path,
            "full_file_path": full_path,
            "file_exists": file_exists,
            "timestamp": end_time,
            "started_at": start_time,
            "completed_at": end_time,
            "processing_time": processing_time,
            "function_name": func_name,
            "input_params": args
        }

        with result_condition:
            results[task_id] = final_result
            result_condition.notify_all()

        print(f"🎉 [DEBUG] 任务 {task_id} 完成！")

    except Exception as e:
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        import traceback
        error_traceback = traceback.format_exc()

        print(f"❌ [DEBUG] 任务 {task_id} 失败!")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {str(e)}")
        print(f"   错误堆栈: {error_traceback}")

        final_result = {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_traceback,
            "timestamp": end_time,
            "started_at": start_time,
            "failed_at": end_time,
            "processing_time": processing_time,
            "function_name": func_name,
            "input_params": args
        }

        with result_condition:
            results[task_id] = final_result
            result_condition.notify_all()

def worker():
    while True:
        task = task_queue.get()
        try:
            process_task(task)
        finally:
            task_queue.task_done()

worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

class APIConfig:
    def __init__(self):
        self.base_url = "https://agent.cstlanbaai.com/gateway"
        self.admin_api_base = f"{self.base_url}/admin-api"
        self.headers = {
            "Content-Type": "application/json",
        }

    def get_headers(self, tenant_id=None):
        """获取请求头，支持租户ID"""
        headers = self.headers.copy()
        if tenant_id:
            headers["Tenant-Id"] = str(tenant_id)
            headers["X-Tenant-Id"] = str(tenant_id)  # 多种格式支持
        return headers

    def update_task_status(self):
        """通用任务状态更新接口 - 所有任务都使用这个"""
        return f"{self.admin_api_base}/agent/task-video-info/update"

    def update_task_video_edit_update(self):
        return f"{self.admin_api_base}/agent/task-video-edit/update"

    def create_resource_url(self):
        return f"{self.admin_api_base}/agent/resource/create"

class APIService:
    def __init__(self, config: APIConfig):
        self.config = config
        self.base_url = "https://agent.cstlanbaai.com/gateway"
        self.admin_api_base = f"{self.base_url}/admin-api"

    def update_task_status(self, task_id: str, status: str = "1", tenant_id=None, path: str = "",
                           resource_id=None, business_id=None, content=None, api_type="default"):
        """
        更新任务状态
        Args:
            task_id: 任务ID
            status: "0"=运行中, "1"=完成, "2"=失败
            tenant_id: 租户ID
            path: 文件路径
            resource_id: 资源ID
            business_id: 业务ID（请求中的id字段）
            content: 文本内容（文本类接口返回的内容）
            api_type: API类型，"digital_human"时使用特殊接口，否则使用默认接口
        """
        # 🔥 根据 api_type 选择不同的更新接口
        if api_type == "digital_human":
            url = f"{self.admin_api_base}/agent/task-video-edit/update"
            print(f"🤖 [数字人] 使用数字人专用状态更新接口")
        else:
            url = f"{self.admin_api_base}/agent/task-video-info/update"
            print(f"📋 [通用] 使用通用状态更新接口")

        headers = self.config.get_headers(tenant_id)

        # 🔥 注意：根据之前的错误，status字段需要是整数
        data = {
            "code": 200,
            "status": int(status),  # 转换为整数
            "message": "OSS文件上传成功" if status == "1" else ("执行中" if status == "0" else "执行失败"),
            "output_oss_path": path
        }

        # 🔥 新增：如果有文本内容，确保是字符串格式
        if content:
            # 确保 content 是字符串
            if isinstance(content, str):
                final_content = content.strip()
            elif isinstance(content, (tuple, list)):
                # 如果是元组或列表，合并为字符串
                text_parts = []
                for item in content:
                    if isinstance(item, str) and item.strip():
                        text_parts.append(item.strip())
                final_content = '\n'.join(text_parts) if text_parts else str(content)
            else:
                # 其他类型转为字符串
                final_content = str(content)

            if final_content:
                data["content"] = final_content
                print(f"📝 添加文本内容到请求: {final_content[:100]}...")
            else:
                print(f"⚠️ 文本内容为空，跳过添加")

        # 🔥 如果有业务ID，添加到请求体中
        if business_id:
            data["id"] = business_id
            print(f"📋 添加业务ID到请求: {business_id}")

        # 如果有资源ID，添加到请求体中
        if resource_id:
            data["resourceId"] = resource_id

        # 将租户ID添加到请求体中
        if tenant_id:
            data["tenantId"] = tenant_id

        try:
            print(f"📤 更新任务状态请求:")
            print(f"   URL: {url}")
            print(f"   Headers: {headers}")
            print(f"   Data: {data}")

            response = requests.put(url, json=data, headers=headers, timeout=30)

            print(f"📥 任务状态更新响应:")
            print(f"   状态码: {response.status_code}")
            print(f"   响应体: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                # 🔥 检查后端是否返回了错误
                if response_data.get('code') == 0:
                    print(f"✅ 任务状态更新成功: {task_id} -> status={status}")
                    return response_data
                else:
                    print(f"❌ 后端返回错误: {response_data.get('msg', '未知错误')}")
                    return None
            else:
                print(f"❌ 任务状态更新失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 任务状态更新失败: {task_id}, 错误: {str(e)}")
            return None

    def create_resource(self, resource_type: str, name: str, path: str,local_full_path: str, file_type: str, size: int, tenant_id=None):
        """保存资源到素材库"""
        url = self.config.create_resource_url()
        headers = self.config.get_headers(tenant_id)

        data = {
            "type": resource_type,
            "name": name,
            "path": path,
            "fileType": file_type,
            "size": size
        }

        if tenant_id:
            data["tenantId"] = tenant_id
        if local_full_path:
            data["localPath"] = local_full_path
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)

            print(f"✅ 资源保存成功: {name} -> {path}")
            print(f"📤 响应: {response.text}")

            if response.status_code == 200:
                response_data = response.json()

                # 尝试从响应中提取resourceId
                resource_id = None
                possible_id_fields = ['resourceId', 'id', 'data', 'result']
                for field in possible_id_fields:
                    if field in response_data:
                        if field == 'data' and isinstance(response_data[field], dict):
                            resource_id = response_data[field].get('id') or response_data[field].get('resourceId')
                        else:
                            resource_id = response_data[field]
                        if resource_id:
                            break

                return {
                    'response': response_data,
                    'resource_id': resource_id
                }
            else:
                print(f"❌ 资源保存失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 资源保存失败: {name}, 错误: {str(e)}")
            return None

api_config = APIConfig()
api_service = APIService(api_config)


# 修复 AsyncTaskManager 类中的关键问题

class AsyncTaskManager:
    def __init__(self, max_workers=5, max_task_timeout=1800):
        """异步任务管理器"""
        self.max_workers = max_workers
        self.max_task_timeout = max_task_timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TaskWorker")
        self.results = {}
        self.result_condition = threading.Condition()
        self.active_futures = {}
        self.api_service = api_service
        # 🔥 新增：跟踪已更新状态的任务，避免重复更新
        self.status_updated_tasks = set()
        print(f"🚀 异步任务管理器初始化: max_workers={max_workers}, timeout={max_task_timeout}s")

    async def submit_task(self, func_name: str, args: dict, task_id: str = None, tenant_id=None,
                          business_id=None) -> str:
        """支持云端上传的任务提交 - 🔥 避免重复状态更新"""
        if not task_id:
            task_id = str(uuid.uuid4())

        # 检查函数是否存在
        func = globals().get(func_name)
        if not func:
            raise ValueError(f"函数不存在: {func_name}")

        print(f"🎯 [ENHANCED-ASYNC] 提交任务: {task_id} -> {func_name}")
        print(f"   租户ID: {tenant_id}")
        print(f"   业务ID: {business_id}")

        # 检测是否为数字人生成接口
        is_digital_human = func_name == "process_single_video_by_url"
        api_type = "digital_human" if is_digital_human else "default"

        # 🔥 修复：只在这里更新一次状态，标记已更新
        if tenant_id and task_id not in self.status_updated_tasks:
            try:
                self.api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id, api_type=api_type)
                self.status_updated_tasks.add(task_id)  # 标记已更新
                print(f"✅ [SUBMIT-TASK] 首次状态更新成功: {task_id}")
            except Exception as e:
                print(f"⚠️ [SUBMIT-TASK] 状态更新失败: {e}")

        # 初始化任务状态
        with self.result_condition:
            self.results[task_id] = {
                "task_id": task_id,
                "function_name": func_name,
                "status": "submitted",
                "submitted_at": time.time(),
                "progress": "0%",
                "current_step": "已提交，等待执行",
                "input_params": args.copy(),
                "tenant_id": tenant_id,
                "business_id": business_id,
                "enhanced": True
            }
            self.result_condition.notify_all()

        # 异步提交到线程池
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.executor,
            self._execute_task_with_oss_upload,
            task_id, func_name, args, tenant_id, business_id
        )

        self.active_futures[task_id] = future
        asyncio.create_task(self._handle_task_result_with_upload(task_id, future, tenant_id, business_id, api_type))

        return task_id

    def _download_and_upload_aliyun_file(self, aliyun_url: str, task_id: str, file_type: str = "video"):
        """
        简单的下载阿里云文件并上传到自己OSS的函数

        Args:
            aliyun_url: 阿里云临时文件URL
            task_id: 任务ID
            file_type: 文件类型 ("video" 或 "image")

        Returns:
            str: 自己OSS的URL，失败返回原URL
        """
        try:
            import requests
            import os
            import tempfile

            print(f"📥 [DOWNLOAD-UPLOAD] 开始下载并上传阿里云文件: {file_type}")
            print(f"   原始URL: {aliyun_url}")

            # 确定文件扩展名
            if file_type == "video":
                ext = ".mp4"
            elif file_type == "image":
                ext = ".jpg"
            else:
                ext = ".tmp"

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                temp_path = temp_file.name

            print(f"📁 [DOWNLOAD-UPLOAD] 临时文件路径: {temp_path}")

            # 下载文件
            response = requests.get(aliyun_url, timeout=300, stream=True)
            response.raise_for_status()

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(temp_path)
            print(f"✅ [DOWNLOAD-UPLOAD] 下载完成，文件大小: {file_size / 1024 / 1024:.2f} MB")

            if file_size == 0:
                raise Exception("下载的文件大小为0")

            # 生成OSS路径
            filename = f"aliyun_{file_type}_{task_id[:8]}{ext}"
            oss_path = f"agent/resource/downloaded/{filename}"

            print(f"📤 [DOWNLOAD-UPLOAD] 开始上传到OSS: {oss_path}")

            # 上传到OSS
            upload_success = upload_to_oss(temp_path, oss_path)

            if upload_success:
                # 生成自己的OSS URL
                oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}"
                print(f"✅ [DOWNLOAD-UPLOAD] 上传成功: {oss_url}")

                # 清理临时文件
                try:
                    os.remove(temp_path)
                    print(f"🗑️ [DOWNLOAD-UPLOAD] 临时文件已清理")
                except:
                    pass

                return oss_url
            else:
                raise Exception("OSS上传失败")

        except Exception as e:
            print(f"❌ [DOWNLOAD-UPLOAD] 处理失败: {str(e)}")
            # 清理临时文件
            try:
                if 'temp_path' in locals():
                    os.remove(temp_path)
            except:
                pass
            # 失败时返回原URL
            return aliyun_url

    def _handle_multi_image_urls(self, result_data, business_id, task_id, tenant_id):
        """
        🔥 处理包含多个图片URL的结果（如AI试衣分割）

        Args:
            result_data: 包含多个图片URL的结果数据
            business_id: 业务ID
            task_id: 任务ID
            tenant_id: 租户ID

        Returns:
            是否处理成功
        """
        print(f"🖼️ [MULTI-IMAGE] 开始处理多图片URL结果")

        try:
            if not isinstance(result_data, dict):
                print(f"⚠️ [MULTI-IMAGE] 结果不是字典类型: {type(result_data)}")
                return False

            # 收集所有需要下载的图片URL
            all_urls = []
            url_metadata = []

            # 提取parsing_img_url
            parsing_urls = result_data.get('parsing_img_url', [])
            if isinstance(parsing_urls, list):
                for i, url in enumerate(parsing_urls):
                    if url and isinstance(url, str):
                        all_urls.append(url)
                        url_metadata.append({
                            'type': 'parsing',
                            'index': i,
                            'key': f"parsing_{i}"
                        })

            # 提取crop_img_url
            crop_urls = result_data.get('crop_img_url', [])
            if isinstance(crop_urls, list):
                for i, url in enumerate(crop_urls):
                    if url and isinstance(url, str):
                        all_urls.append(url)
                        url_metadata.append({
                            'type': 'crop',
                            'index': i,
                            'key': f"crop_{i}"
                        })

            print(f"📋 [MULTI-IMAGE] 共找到 {len(all_urls)} 个图片URL")

            if not all_urls:
                print(f"⚠️ [MULTI-IMAGE] 没有找到有效的图片URL")
                return False

            # 下载所有图片并上传到OSS
            uploaded_results = {}

            for i, (url, metadata) in enumerate(zip(all_urls, url_metadata)):
                try:
                    print(f"⬇️ [MULTI-IMAGE] 处理图片 {i + 1}/{len(all_urls)}: {metadata['key']}")

                    # 下载图片
                    import requests
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()

                    # 确定文件扩展名
                    content_type = response.headers.get('content-type', '')
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'jpg' in content_type or 'jpeg' in content_type:
                        ext = '.jpg'
                    else:
                        ext = '.png'  # 默认使用png

                    # 生成文件名和OSS路径
                    import time
                    timestamp = int(time.time())
                    filename = f"ai_tryon_segment_{metadata['key']}_{timestamp}{ext}"
                    oss_path = f"agent/resource/ai_tryon_segment/{filename}"

                    # 创建临时文件
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                        temp_file.write(response.content)
                        temp_path = temp_file.name

                    try:
                        # 上传到OSS
                        upload_success = upload_to_oss(temp_path, oss_path)

                        if upload_success:
                            oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}"
                            uploaded_results[metadata['key']] = {
                                'oss_url': oss_url,
                                'oss_path': oss_path,
                                'original_url': url,
                                'type': metadata['type'],
                                'index': metadata['index']
                            }
                            print(f"✅ [MULTI-IMAGE] {metadata['key']} 上传成功: {oss_url}")
                        else:
                            print(f"❌ [MULTI-IMAGE] {metadata['key']} OSS上传失败")

                    finally:
                        # 清理临时文件
                        try:
                            os.remove(temp_path)
                        except:
                            pass

                except Exception as e:
                    print(f"❌ [MULTI-IMAGE] {metadata['key']} 处理失败: {str(e)}")
                    continue

            if not uploaded_results:
                print(f"❌ [MULTI-IMAGE] 所有图片处理都失败了")
                return False

            # 重新构建结果数据，用OSS URL替换原始URL
            updated_parsing_urls = []
            updated_crop_urls = []

            # 重建parsing_img_url数组
            parsing_count = len(parsing_urls) if isinstance(parsing_urls, list) else 0
            for i in range(parsing_count):
                key = f"parsing_{i}"
                if key in uploaded_results:
                    updated_parsing_urls.append(uploaded_results[key]['oss_url'])
                elif i < len(parsing_urls):
                    updated_parsing_urls.append(parsing_urls[i])  # 保留原URL作为备用

            # 重建crop_img_url数组
            crop_count = len(crop_urls) if isinstance(crop_urls, list) else 0
            for i in range(crop_count):
                key = f"crop_{i}"
                if key in uploaded_results:
                    updated_crop_urls.append(uploaded_results[key]['oss_url'])
                elif i < len(crop_urls):
                    updated_crop_urls.append(crop_urls[i])  # 保留原URL作为备用

            # 构建最终结果
            final_result = {
                "parsing_img_url": updated_parsing_urls,
                "crop_img_url": updated_crop_urls,
                "bbox": result_data.get('bbox', []),
                "upload_summary": {
                    "total_images": len(all_urls),
                    "successful_uploads": len(uploaded_results),
                    "uploaded_details": uploaded_results
                }
            }

            # 转换为JSON字符串作为path参数传递
            import json
            result_json = json.dumps(final_result, ensure_ascii=False)

            # 更新任务状态为成功
            task_update_result = self.api_service.update_task_status(
                task_id=task_id,
                status="1",  # 完成
                tenant_id=tenant_id,
                path=result_json,  # 传递JSON字符串
                resource_id=None,
                business_id=business_id,
            )

            print(f"🎉 [MULTI-IMAGE] 多图片处理完成，共上传 {len(uploaded_results)} 个文件")
            print(f"   任务更新: {'成功' if task_update_result else '失败'}")
            return True

        except Exception as e:
            print(f"❌ [MULTI-IMAGE] 多图片处理失败: {str(e)}")
            # 更新任务状态为失败
            try:
                self.api_service.update_task_status(
                    task_id, "2", tenant_id, business_id=business_id
                )
            except Exception as status_error:
                print(f"⚠️ [MULTI-IMAGE] 更新失败状态时出错: {status_error}")
            return False

    def _execute_task_with_oss_upload(self, task_id: str, func_name: str, args: dict, tenant_id=None, business_id=None):
        """🔥 执行任务并上传到OSS - 简化版本（跳过图片和文本上传）"""
        print(f"🎯 [OSS-UPLOAD] 开始执行任务: {task_id}")
        print(f"   业务ID: {business_id}")
        # 🔥 检测是否为数字人生成接口
        is_digital_human = func_name == "process_single_video_by_url"
        api_type = "digital_human" if is_digital_human else "default"

        # 1. 执行原有任务
        result = self._execute_task_with_timeout(task_id, func_name, args)

        # 2. 如果成功且有tenant_id，进行OSS上传
        if result["status"] == "completed" and tenant_id:
            try:
                print(f"☁️ [OSS-UPLOAD] 开始OSS上传流程")

                # 更新状态：开始上传
                with self.result_condition:
                    if task_id in self.results:
                        self.results[task_id].update({
                            "status": "uploading",
                            "current_step": "正在处理结果",
                            "progress": "90%"
                        })
                        self.result_condition.notify_all()

                # 🔥 检查函数类型
                text_functions = [
                    "get_text_industry", "get_copy_generation", "analyze_cover_wrapper"
                ]

                wanxiang_image_functions = [
                    # 原有的
                    "get_text_to_image_v2", "get_text_to_image_v1",
                    "get_ai_tryon_basic", "get_ai_tryon_plus",
                    "get_virtual_model_v1", "get_virtual_model_v2",
                    "get_background_generation", "get_image_background_edit",

                    # 新增的图像类
                    "get_doodle_painting", "get_image_inpainting", "get_personal_portrait",
                    "get_image_outpainting", "get_shoe_model", "get_creative_poster",
                    "get_ai_tryon_enhance", "get_ai_tryon_segment",
                    "get_image_upscale", "get_image_style_transfer", "get_artistic_text"
                ]

                # 🔥 新增：多图片URL类函数
                multi_image_functions = [
                    "get_ai_tryon_segment"  # 返回多个图片URL的函数
                ]

                # 新增的视频类函数
                wanxiang_video_functions = [
                    "get_image_to_video_basic", "get_image_to_video_advanced",
                    "get_text_to_video", "get_video_edit",
                    "get_animate_anyone", "get_emo_video", "get_live_portrait",
                    "get_video_style_transfer"
                ]

                is_text_function = func_name in text_functions
                is_wanxiang_image_function = func_name in wanxiang_image_functions
                is_wanxiang_video_function = func_name in wanxiang_video_functions
                is_multi_image_function = func_name in multi_image_functions

                print(f"🔍 [OSS-UPLOAD] 函数类型检测:")
                print(f"   函数名: {func_name}")
                print(f"   是文本类: {is_text_function}")
                print(f"   是万相图片类: {is_wanxiang_image_function}")

                # 🔥 新增：处理多图片URL函数
                if is_multi_image_function:
                    print(f"🖼️ [OSS-UPLOAD] 检测到多图片URL接口: {func_name} - 特殊处理")

                    success = self._handle_multi_image_urls(result.get("result"), business_id, task_id, tenant_id)

                    if success:
                        result.update({
                            "multi_image_upload_success": True,
                            "task_update_success": True,
                            "cloud_integration": "multi_image",
                            "business_id": business_id,
                            "content_type": "multi_image",
                            "oss_upload_success": True,
                            "upload_skipped": False
                        })
                        print(f"✅ [OSS-UPLOAD] 多图片处理完成!")
                    else:
                        raise Exception("多图片处理失败")

                elif is_text_function:
                    # 🔥 文本类接口处理 - 直接返回结果，不上传
                    print(f"📝 [OSS-UPLOAD] 检测到文本类接口: {func_name} - 跳过上传")

                    # 提取文本内容
                    text_content = self._extract_text_content(result.get("result"))

                    if text_content:
                        print(f"📝 [OSS-UPLOAD] 提取到文本内容: {text_content[:100]}...")

                        # 🔥 直接更新任务状态为完成，传递文本内容
                        task_update_result = self.api_service.update_task_status(
                            task_id=task_id,
                            status="1",  # 完成
                            tenant_id=tenant_id,
                            path="",  # 文本类接口不需要路径
                            resource_id=None,
                            business_id=business_id,
                            content=text_content,  # 🔥 传递文本内容
                            api_type = api_type
                        )

                        # 更新结果
                        result.update({
                            "text_content": text_content,
                            "task_update_success": bool(task_update_result),
                            "content_type": "text",
                            "business_id": business_id,
                            "cloud_integration": "text_direct",
                            "oss_upload_success": False,  # 标记为未上传OSS
                            "upload_skipped": True,
                            "skip_reason": "文本类接口，直接返回内容"
                        })

                        print(f"✅ [OSS-UPLOAD] 文本类接口处理完成!")
                        print(f"   任务更新: {'成功' if task_update_result else '失败'}")
                        print(f"   跳过OSS上传: 文本内容直接返回")
                    else:
                        raise Exception("无法提取文本内容")

                elif is_wanxiang_image_function:
                    print(f"🖼️ [OSS-UPLOAD] 检测到通义万相图片接口: {func_name} - 下载并上传")

                    image_url = self._extract_image_url_from_result(result.get("result"))

                    if image_url:
                        print(f"🔗 [OSS-UPLOAD] 提取到图片URL: {image_url}")

                        # 🔥 检查是否是阿里云URL，如果是则下载上传
                        if "lan8-e-business.oss" not in image_url:
                            final_image_url = self._download_and_upload_aliyun_file(image_url, task_id, "image")
                        else:
                            final_image_url = image_url

                        task_update_result = self.api_service.update_task_status(
                            task_id=task_id,
                            status="1",
                            tenant_id=tenant_id,
                            path=final_image_url,
                            resource_id=None,
                            business_id=business_id,
                            api_type=api_type
                        )

                        result.update({
                            "original_image_url": image_url,
                            "image_url": final_image_url,
                            "task_update_success": bool(task_update_result),
                            "cloud_integration": "image_downloaded" if final_image_url != image_url else "image_direct",
                            "business_id": business_id,
                            "content_type": "image",
                            "oss_upload_success": final_image_url != image_url,
                            "upload_skipped": final_image_url == image_url
                        })

                        print(f"✅ [OSS-UPLOAD] 图片处理完成: {final_image_url}")

                    else:
                        raise Exception("无法提取图片URL")

                elif is_wanxiang_video_function:
                    print(f"🎬 [OSS-UPLOAD] 检测到通义万相视频接口: {func_name} - 下载并上传")

                    video_url = self._extract_video_url_from_result(result.get("result"))

                    if video_url:
                        print(f"🔗 [OSS-UPLOAD] 提取到视频URL: {video_url}")

                        # 🔥 检查是否是阿里云URL，如果是则下载上传
                        if "lan8-e-business.oss" not in video_url:
                            final_video_url = self._download_and_upload_aliyun_file(video_url, task_id, "video")
                        else:
                            final_video_url = video_url

                        task_update_result = self.api_service.update_task_status(
                            task_id=task_id,
                            status="1",
                            tenant_id=tenant_id,
                            path=final_video_url,
                            resource_id=None,
                            business_id=business_id,
                            api_type=api_type
                        )

                        result.update({
                            "original_video_url": video_url,
                            "video_url": final_video_url,
                            "task_update_success": bool(task_update_result),
                            "cloud_integration": "video_downloaded" if final_video_url != video_url else "video_direct",
                            "business_id": business_id,
                            "content_type": "video",
                            "oss_upload_success": final_video_url != video_url,
                            "upload_skipped": final_video_url == video_url
                        })

                        print(f"✅ [OSS-UPLOAD] 视频处理完成: {final_video_url}")

                    else:
                        raise Exception("无法提取视频URL")

                else:
                    # 🔥 普通文件类接口处理（视频、音频等）- 正常上传OSS
                    print(f"📁 [OSS-UPLOAD] 检测到普通文件类接口: {func_name} - 执行OSS上传")

                    # 获取输出文件路径
                    warehouse_path = extract_warehouse_path(result.get("result"))
                    if not warehouse_path:
                        raise Exception("无法提取输出路径")

                    # 🔥 检查路径是否为URL（防止误把URL当作本地路径）
                    if warehouse_path.startswith(('http://', 'https://')):
                        print(f"⚠️ [OSS-UPLOAD] 检测到URL路径，跳过上传: {warehouse_path}")

                        # 🔥 对于URL结果，直接返回，不上传
                        task_update_result = self.api_service.update_task_status(
                            task_id=task_id,
                            status="1",  # 完成
                            tenant_id=tenant_id,
                            path=warehouse_path,  # 直接使用URL
                            resource_id=None,
                            business_id=business_id,
                            api_type=api_type
                        )

                        result.update({
                            "original_url": warehouse_path,
                            "task_update_success": bool(task_update_result),
                            "cloud_integration": "url_direct",
                            "business_id": business_id,
                            "content_type": "url",
                            "oss_upload_success": False,
                            "upload_skipped": True,
                            "skip_reason": "结果为URL，直接返回"
                        })

                        print(f"✅ [OSS-UPLOAD] URL结果处理完成!")

                    else:
                        # 正常的本地文件处理 - 执行OSS上传
                        user_data_dir = config.get_user_data_dir()
                        local_full_path = os.path.join(user_data_dir, warehouse_path)

                        if not os.path.exists(local_full_path):
                            raise Exception(f"输出文件不存在: {local_full_path}")

                        # 生成OSS路径
                        oss_path = f"agent/resource/{warehouse_path}"

                        print(f"📤 [OSS-UPLOAD] 开始上传文件:")
                        print(f"   本地: {local_full_path}")
                        print(f"   OSS: {oss_path}")
                        # 🔥 检测是否为数字人生成接口
                        is_digital_human = func_name == "process_single_video_by_url"
                        api_type = "digital_human" if is_digital_human else "default"

                        # 上传到OSS
                        upload_success = upload_to_oss(local_full_path, oss_path)

                        if upload_success:
                            print(f"✅ [OSS-UPLOAD] 文件OSS上传成功")

                            # 获取文件信息
                            file_info = get_file_info(local_full_path)
                            if file_info:
                                # 调用create_resource API
                                resource_result = self.api_service.create_resource(
                                    resource_type=file_info['resource_type'],
                                    name=file_info['name'],
                                    path=oss_path,
                                    local_full_path=local_full_path,
                                    file_type=file_info['file_type'],
                                    size=file_info['size'],
                                    tenant_id=tenant_id
                                )

                                resource_id = None
                                resource_success = False

                                if resource_result:
                                    resource_id = resource_result.get('resource_id')
                                    if isinstance(resource_result, dict) and resource_result.get('response'):
                                        response_data = resource_result['response']
                                        resource_success = response_data.get('code') == 200
                                    else:
                                        resource_success = bool(resource_id)

                                # 更新任务状态为完成
                                task_update_result = self.api_service.update_task_status(
                                    task_id=task_id,
                                    status="1",  # 完成
                                    tenant_id=tenant_id,
                                    path=oss_path,
                                    resource_id=resource_id,
                                    business_id=business_id,
                                    api_type = api_type
                                )

                                # 生成OSS访问URL
                                oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}"

                                # 更新结果 - 成功情况
                                result.update({
                                    "oss_upload_success": True,
                                    "oss_path": oss_path,
                                    "oss_url": oss_url,
                                    "resource_id": resource_id,
                                    "resource_create_success": resource_success,
                                    "task_update_success": bool(task_update_result),
                                    "cloud_integration": "oss",
                                    "business_id": business_id,
                                    "content_type": "file",
                                    "upload_skipped": False
                                })

                                print(f"✅ [OSS-UPLOAD] 文件完整流程成功!")
                                print(f"   OSS URL: {oss_url}")
                                print(f"   资源ID: {resource_id}")

                            else:
                                raise Exception("获取文件信息失败")
                        else:
                            raise Exception("文件OSS上传失败")

            except Exception as e:
                print(f"❌ [OSS-UPLOAD] 上传流程失败: {str(e)}")

                # 🔥 更新任务状态为失败，传递业务ID
                if tenant_id:
                    try:
                        self.api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id, api_type=api_type)
                        print(f"📤 [OSS-UPLOAD] 已更新任务状态为失败")
                    except Exception as update_error:
                        print(f"⚠️ [OSS-UPLOAD] 更新失败状态时出错: {update_error}")

                # 更新结果 - 失败情况
                result.update({
                    "oss_upload_success": False,
                    "upload_error": str(e),
                    "status": "completed_with_upload_error",
                    "cloud_integration": "oss",
                    "business_id": business_id
                })

        return result

    def _extract_image_url_from_result(self, result):
        """🔥 从通义万相结果中提取图片URL"""
        if not result:
            return None

        print(f"🔍 [EXTRACT-IMAGE-URL] 开始提取图片URL，输入类型: {type(result)}")
        print(f"🔍 [EXTRACT-IMAGE-URL] 输入内容: {str(result)[:200]}...")

        # 如果结果直接是URL字符串
        if isinstance(result, str) and (result.startswith('http://') or result.startswith('https://')):
            print(f"✅ [EXTRACT-IMAGE-URL] 直接URL字符串: {result}")
            return result

        # 如果结果是字典，尝试提取URL
        if isinstance(result, dict):
            # 常见的URL字段名
            url_fields = ['url', 'image_url', 'output_url', 'result_url', 'data', 'output', 'image']

            for field in url_fields:
                if field in result:
                    field_value = result[field]
                    if isinstance(field_value, str) and (
                            field_value.startswith('http://') or field_value.startswith('https://')):
                        print(f"✅ [EXTRACT-IMAGE-URL] 从字典字段 {field} 提取: {field_value}")
                        return field_value

            # 如果有success字段且为True，遍历所有字段查找URL
            if result.get('success') == True:
                for key, value in result.items():
                    if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                        print(f"✅ [EXTRACT-IMAGE-URL] 从成功结果字段 {key} 提取: {value}")
                        return value

        # 如果结果是列表，检查每个元素
        if isinstance(result, list):
            for item in result:
                extracted_url = self._extract_image_url_from_result(item)
                if extracted_url:
                    print(f"✅ [EXTRACT-IMAGE-URL] 从列表项提取: {extracted_url}")
                    return extracted_url

        print(f"⚠️ [EXTRACT-IMAGE-URL] 无法提取有效图片URL")
        return None

    def _extract_video_url_from_result(self, result):
        """🔥 从通义万相结果中提取视频URL"""
        if not result:
            return None

        print(f"🔍 [EXTRACT-VIDEO-URL] 开始提取视频URL，输入类型: {type(result)}")
        print(f"🔍 [EXTRACT-VIDEO-URL] 输入内容: {str(result)[:200]}...")

        # 如果结果直接是URL字符串
        if isinstance(result, str) and (result.startswith('http://') or result.startswith('https://')):
            print(f"✅ [EXTRACT-VIDEO-URL] 直接URL字符串: {result}")
            return result

        # 如果结果是字典，尝试提取URL
        if isinstance(result, dict):
            # 常见的视频URL字段名
            url_fields = ['url', 'video_url', 'output_url', 'result_url', 'data', 'output', 'video', 'video_path']

            for field in url_fields:
                if field in result:
                    field_value = result[field]
                    if isinstance(field_value, str) and (
                            field_value.startswith('http://') or field_value.startswith('https://')):
                        print(f"✅ [EXTRACT-VIDEO-URL] 从字典字段 {field} 提取: {field_value}")
                        return field_value

            # 如果有success字段且为True，遍历所有字段查找URL
            if result.get('success') == True:
                for key, value in result.items():
                    if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
                        print(f"✅ [EXTRACT-VIDEO-URL] 从成功结果字段 {key} 提取: {value}")
                        return value

        # 如果结果是列表，检查每个元素
        if isinstance(result, list):
            for item in result:
                extracted_url = self._extract_video_url_from_result(item)
                if extracted_url:
                    print(f"✅ [EXTRACT-VIDEO-URL] 从列表项提取: {extracted_url}")
                    return extracted_url

        print(f"⚠️ [EXTRACT-VIDEO-URL] 无法提取有效视频URL")
        return None

    def _extract_text_content(self, result):
        """🔥 提取文本内容的辅助函数 - 确保返回字符串"""
        if not result:
            return None

        print(f"🔍 [EXTRACT-TEXT] 开始提取文本内容，输入类型: {type(result)}")
        print(f"🔍 [EXTRACT-TEXT] 输入内容: {str(result)[:200]}...")

        # 🔥 如果结果是元组或列表，合并为字符串
        if isinstance(result, (tuple, list)):
            # 过滤出字符串元素并合并
            text_parts = []
            for item in result:
                if isinstance(item, str) and item.strip():
                    text_parts.append(item.strip())
                elif isinstance(item, dict):
                    # 递归处理字典元素
                    extracted = self._extract_text_content(item)
                    if extracted:
                        text_parts.append(extracted)

            if text_parts:
                # 用换行符或空格连接多个文本部分
                combined_text = '\n'.join(text_parts) if len(text_parts) > 1 else text_parts[0]
                print(f"✅ [EXTRACT-TEXT] 从元组/列表提取: {combined_text[:100]}...")
                return combined_text

        # 🔥 如果结果直接是字符串
        if isinstance(result, str):
            cleaned_text = result.strip()
            print(f"✅ [EXTRACT-TEXT] 直接字符串: {cleaned_text[:100]}...")
            return cleaned_text if cleaned_text else None

        # 🔥 如果结果是字典，尝试提取文本内容
        if isinstance(result, dict):
            print(f"🔍 [EXTRACT-TEXT] 处理字典，键: {list(result.keys())}")

            # 尝试常见的文本字段
            text_fields = ['text', 'content', 'data', 'result', 'message', 'generated_text', 'analysis_result']
            for field in text_fields:
                if field in result:
                    field_value = result[field]
                    print(f"🔍 [EXTRACT-TEXT] 检查字段 {field}: {type(field_value)}")

                    if isinstance(field_value, str) and field_value.strip():
                        print(f"✅ [EXTRACT-TEXT] 从字典字段 {field} 提取: {field_value[:100]}...")
                        return field_value.strip()
                    elif isinstance(field_value, (tuple, list)):
                        # 递归处理
                        extracted = self._extract_text_content(field_value)
                        if extracted:
                            print(f"✅ [EXTRACT-TEXT] 从字典字段 {field} 递归提取: {extracted[:100]}...")
                            return extracted

            # 如果有success字段且为True，尝试提取其他字段
            if result.get('success') == True:
                print(f"🔍 [EXTRACT-TEXT] 成功结果，遍历所有字段")
                for key, value in result.items():
                    if key not in ['success', 'code', 'status'] and isinstance(value, str) and len(value.strip()) > 10:
                        print(f"✅ [EXTRACT-TEXT] 从成功结果字段 {key} 提取: {value[:100]}...")
                        return value.strip()
                    elif isinstance(value, (tuple, list)):
                        extracted = self._extract_text_content(value)
                        if extracted:
                            print(f"✅ [EXTRACT-TEXT] 从成功结果字段 {key} 递归提取: {extracted[:100]}...")
                            return extracted

        print(f"⚠️ [EXTRACT-TEXT] 无法提取有效文本内容")
        return None

    def _execute_task_with_timeout(self, task_id: str, func_name: str, args: dict):
        """🔥 带超时控制的任务执行 - 避免重复状态更新"""
        print(f"\n🔥 [EXECUTE-TIMEOUT] 开始执行任务: {task_id}")
        print(f"   函数名: {func_name}")
        print(f"   参数: {args}")
        print(f"   超时时间: {self.max_task_timeout}秒")

        start_time = time.time()

        # 获取租户ID和业务ID
        tenant_id = None
        business_id = None
        is_digital_human = func_name == "process_single_video_by_url"
        api_type = "digital_human" if is_digital_human else "default"

        with self.result_condition:
            if task_id in self.results:
                tenant_id = self.results[task_id].get("tenant_id")
                business_id = self.results[task_id].get("business_id")

        try:
            # 🔥 修复：检查是否已经更新过状态，避免重复更新
            if tenant_id and task_id not in self.status_updated_tasks:
                try:
                    self.api_service.update_task_status(
                        task_id=task_id,
                        status="0",  # 处理中
                        tenant_id=tenant_id,
                        business_id=business_id,
                        api_type=api_type
                    )
                    self.status_updated_tasks.add(task_id)  # 标记已更新
                    print(f"📤 [EXECUTE-TIMEOUT] 远程状态已更新为处理中")
                except Exception as status_error:
                    print(f"⚠️ [EXECUTE-TIMEOUT] 更新远程状态失败: {status_error}")
            elif task_id in self.status_updated_tasks:
                print(f"🔄 [EXECUTE-TIMEOUT] 任务状态已在submit_task中更新，跳过重复更新")

            # 更新本地状态为处理中
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "status": "processing",
                        "started_at": start_time,
                        "progress": "10%",
                        "current_step": "开始执行函数"
                    })
                    self.result_condition.notify_all()

            print(f"🔄 [EXECUTE-TIMEOUT] 任务 {task_id} 状态已更新为 processing")

            # 检查函数是否存在
            func = globals().get(func_name)
            if not func:
                # 函数不存在时更新远程状态为失败
                if tenant_id:
                    try:
                        self.api_service.update_task_status(
                            task_id=task_id,
                            status="2",  # 失败
                            tenant_id=tenant_id,
                            business_id=business_id,
                            api_type=api_type
                        )
                        print(f"📤 [EXECUTE-TIMEOUT] 函数不存在，远程状态已更新为失败")
                    except Exception as status_error:
                        print(f"⚠️ [EXECUTE-TIMEOUT] 更新远程失败状态时出错: {status_error}")

                raise ValueError(f"函数不存在: {func_name}")

            print(f"✅ [EXECUTE-TIMEOUT] 找到函数: {func_name}")

            # 更新本地进度
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "current_step": "正在执行函数",
                        "progress": "30%"
                    })
                    self.result_condition.notify_all()

            print(f"🚀 [EXECUTE-TIMEOUT] 开始执行函数: {func_name}")

            # 使用线程池执行函数，并设置超时
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, **args)

                try:
                    result = future.result(timeout=self.max_task_timeout)
                    print(f"✅ [EXECUTE-TIMEOUT] 函数执行完成: {func_name}")

                except TimeoutError:
                    print(f"⏰ [EXECUTE-TIMEOUT] 函数执行超时: {func_name}")

                    # 超时时更新远程状态为失败
                    if tenant_id:
                        try:
                            self.api_service.update_task_status(
                                task_id=task_id,
                                status="2",  # 失败
                                tenant_id=tenant_id,
                                business_id=business_id,
                                api_type=api_type
                            )
                            print(f"📤 [EXECUTE-TIMEOUT] 超时，远程状态已更新为失败")
                        except Exception as status_error:
                            print(f"⚠️ [EXECUTE-TIMEOUT] 更新远程超时状态时出错: {status_error}")

                    future.cancel()
                    raise TimeoutError(f"函数 {func_name} 执行超时 ({self.max_task_timeout}秒)")

            print(f"   结果类型: {type(result)}")
            print(f"   结果内容: {str(result)[:200]}...")

            # 处理结果
            warehouse_path = extract_warehouse_path(result)
            full_path = get_full_file_path(warehouse_path) if warehouse_path else None
            file_exists = verify_file_exists(warehouse_path) if warehouse_path else False

            end_time = time.time()
            processing_time = round(end_time - start_time, 2)

            print(f"📊 [EXECUTE-TIMEOUT] 处理结果:")
            print(f"   warehouse路径: {warehouse_path}")
            print(f"   完整路径: {full_path}")
            print(f"   文件存在: {file_exists}")
            print(f"   处理时间: {processing_time}秒")

            # 注意：这里不更新远程状态为完成，因为后续的OSS上传流程会处理
            if not tenant_id:
                print(f"📝 [EXECUTE-TIMEOUT] 本地执行模式，无需远程状态更新")

            # 更新本地最终结果
            final_result = {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "warehouse_path": warehouse_path,
                "videoPath": warehouse_path,
                "full_file_path": full_path,
                "file_exists": file_exists,
                "timestamp": end_time,
                "started_at": start_time,
                "completed_at": end_time,
                "processing_time": processing_time,
                "function_name": func_name,
                "input_params": args,
                "tenant_id": tenant_id,
                "business_id": business_id
            }

            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update(final_result)
                    self.result_condition.notify_all()

            print(f"🎉 [EXECUTE-TIMEOUT] 任务 {task_id} 执行完成！")
            return final_result

        except Exception as e:
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)

            import traceback
            error_traceback = traceback.format_exc()

            print(f"❌ [EXECUTE-TIMEOUT] 任务 {task_id} 失败!")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print(f"   错误堆栈: {error_traceback}")

            # 执行失败时更新远程状态为失败
            if tenant_id:
                try:
                    self.api_service.update_task_status(
                        task_id=task_id,
                        status="2",  # 失败
                        tenant_id=tenant_id,
                        business_id=business_id,
                        api_type=api_type
                    )
                    print(f"📤 [EXECUTE-TIMEOUT] 执行失败，远程状态已更新为失败")
                except Exception as status_error:
                    print(f"⚠️ [EXECUTE-TIMEOUT] 更新远程失败状态时出错: {status_error}")

            # 更新本地失败结果
            final_result = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_traceback,
                "timestamp": end_time,
                "started_at": start_time,
                "failed_at": end_time,
                "processing_time": processing_time,
                "function_name": func_name,
                "input_params": args,
                "tenant_id": tenant_id,
                "business_id": business_id
            }

            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update(final_result)
                    self.result_condition.notify_all()

            return final_result

        finally:
            # 🔥 任务完成后，清理状态更新标记（可选）
            # self.status_updated_tasks.discard(task_id)
            pass

    async def _handle_task_result_with_upload(self, task_id: str, future, tenant_id=None, business_id=None, api_type=None):
        """🔥 修复：异步处理任务结果ん和上传 - 支持业务ID"""
        global results, result_condition

        try:
            # 等待任务完成（包括上传）
            execution_result = await future

            print(f"🎉 [ASYNC-UPLOAD] 处理任务结果: {task_id} -> {execution_result['status']}")
            print(f"   业务ID: {business_id}")

            # 增强的结果处理
            final_result = {
                **execution_result,
                "completed_at": time.time(),
                "current_step": "已完成" if execution_result["status"] == "completed" else "执行失败",
                "progress": "100%" if execution_result["status"] == "completed" else "失败",
                "business_id": business_id,  # 🔥 保存业务ID
                "tenant_id": tenant_id
            }

            # 处理成功结果的路径提取
            if execution_result["status"] in ["completed", "completed_with_upload_error"]:
                result_data = execution_result.get("result")
                print(f"🔍 [ASYNC-UPLOAD] 开始提取路径，结果类型: {type(result_data)}")

                warehouse_path = extract_warehouse_path(result_data)
                full_path = get_full_file_path(warehouse_path) if warehouse_path else None
                file_exists = verify_file_exists(warehouse_path) if warehouse_path else False

                print(f"📁 [ASYNC-UPLOAD] 路径提取结果:")
                print(f"   warehouse_path: {warehouse_path}")
                print(f"   full_path: {full_path}")
                print(f"   file_exists: {file_exists}")

                final_result.update({
                    "warehouse_path": warehouse_path,
                    "videoPath": warehouse_path,
                    "full_file_path": full_path,
                    "file_exists": file_exists
                })

                # 🔥 添加OSS特有信息
                if execution_result.get("oss_upload_success"):
                    final_result.update({
                        "oss_url": execution_result.get("oss_url") or execution_result["video_url"],
                        "oss_path": execution_result.get("oss_path") or execution_result["video_url"].split('https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com')[-1],
                        "cloud_access_url": execution_result.get("oss_url"),
                        "resource_id": execution_result.get("resource_id"),
                        "integration": "oss"
                    })
                    print(f"☁️ [ASYNC-UPLOAD] OSS信息已添加到最终结果")
                else:
                    final_result.update({
                        "integration": "local"
                    })

            # 同时更新两个存储位置
            # 更新异步管理器
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update(final_result)
                    self.result_condition.notify_all()

            # 更新全局results
            with result_condition:
                results[task_id] = final_result
                result_condition.notify_all()

            print(final_result)
            print(f"✅ [ASYNC-UPLOAD] 任务结果处理完成: {task_id}")
            print(f"   最终状态: {final_result.get('status')}")
            print(f"   业务ID: {business_id}")

        except Exception as e:
            print(f"❌ [ASYNC-UPLOAD] 处理任务结果失败: {task_id}, 错误: {str(e)}")

            error_result = {
                "task_id": task_id,
                "status": "failed",
                "error": f"结果处理失败: {str(e)}",
                "error_type": type(e).__name__,
                "completed_at": time.time(),
                "current_step": "结果处理失败",
                "progress": "失败",
                "business_id": business_id,  # 🔥 保存业务ID
                "tenant_id": tenant_id
            }

            # 同时更新两个存储位置
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update(error_result)
                    self.result_condition.notify_all()

            with result_condition:
                results[task_id] = error_result
                result_condition.notify_all()

            # 🔥 如果有租户ID，更新远程状态为失败，传递业务ID
            if tenant_id:
                try:
                    self.api_service.update_task_status(
                        task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                    )
                    print(f"📤 [ASYNC-UPLOAD] 已更新远程任务状态为失败")
                except Exception as status_error:
                    print(f"⚠️ [ASYNC-UPLOAD] 更新远程失败状态时出错: {status_error}")

        finally:
            # 清理Future引用
            self.active_futures.pop(task_id, None)
            print(f"🧹 [ASYNC-UPLOAD] 清理任务引用: {task_id}")

    # 🔥 支持云端上传的任务提交方法
    async def execute_task_with_upload(self, func_name: str, args: dict, mode: str = "async", task_id: str = None,
                                       tenant_id=None, business_id=None):
        """
        🔥 执行任务并支持云端上传 - 完整版本

        Args:
            func_name: 要执行的函数名
            args: 函数参数
            mode: 执行模式 "sync"(同步) 或 "async"(异步)
            task_id: 任务ID
            tenant_id: 租户ID
            business_id: 业务ID (来自请求中的id字段)

        Returns:
            同步模式: 直接返回结果
            异步模式: 返回 {"task_id": "xxx"}
        """
        # 在同步模式部分添加文本内容处理
        # 🔥 检测是否为数字人生成接口
        is_digital_human = func_name == "process_single_video_by_url"
        api_type = "digital_human" if is_digital_human else "default"

        print(f"🎯 [API-TYPE] 函数: {func_name}, API类型: {api_type}")

        if mode == "sync":
            # 🔄 同步模式：直接在当前线程执行（但仍使用超时控制）
            print(f"🔄 [SYNC-UPLOAD] 同步执行任务: {func_name}")
            print(f"   租户ID: {tenant_id}")
            print(f"   业务ID: {business_id}")

            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    func = globals().get(func_name)
                    if not func:
                        raise ValueError(f"函数不存在: {func_name}")

                    future = executor.submit(func, **args)
                    result = future.result(timeout=1800)  # 30分钟超时

                    # 🔥 同步模式下也支持OSS上传和多种类型处理
                    if tenant_id:
                        try:
                            print(f"☁️ [SYNC-UPLOAD] 开始同步OSS上传流程")

                            # 🔥 定义函数分类
                            text_functions = [
                                "get_text_industry", "get_copy_generation", "analyze_cover_wrapper"
                            ]

                            wanxiang_image_functions = [
                                "get_text_to_image_v2", "get_text_to_image_v1",
                                "get_ai_tryon_basic", "get_ai_tryon_plus",
                                "get_virtual_model_v1", "get_virtual_model_v2",
                                "get_background_generation", "get_image_background_edit",
                                "get_doodle_painting", "get_image_inpainting", "get_personal_portrait",
                                "get_image_outpainting", "get_shoe_model", "get_creative_poster",
                                "get_ai_tryon_enhance",
                                "get_image_upscale", "get_image_style_transfer", "get_artistic_text"
                            ]

                            # 🔥 新增：多图片URL类函数
                            multi_image_functions = [
                                "get_ai_tryon_segment"  # 返回多个图片URL的函数
                            ]

                            wanxiang_video_functions = [
                                "get_image_to_video_basic", "get_image_to_video_advanced",
                                "get_text_to_video", "get_video_edit",
                                "get_animate_anyone", "get_emo_video", "get_live_portrait",
                                "get_video_style_transfer"
                            ]

                            is_text_function = func_name in text_functions
                            is_wanxiang_image_function = func_name in wanxiang_image_functions
                            is_multi_image_function = func_name in multi_image_functions
                            is_wanxiang_video_function = func_name in wanxiang_video_functions

                            print(f"🔍 [SYNC-UPLOAD] 函数类型检测:")
                            print(f"   函数名: {func_name}")
                            print(f"   是文本类: {is_text_function}")
                            print(f"   是万相图片类: {is_wanxiang_image_function}")
                            print(f"   是多图片类: {is_multi_image_function}")
                            print(f"   是万相视频类: {is_wanxiang_video_function}")

                            if is_text_function:
                                # 🔥 文本类接口处理
                                print(f"📝 [SYNC-UPLOAD] 检测到文本类接口: {func_name}")

                                # 提取文本内容
                                text_content = self._extract_text_content(result)

                                if text_content:
                                    print(f"📝 [SYNC-UPLOAD] 提取到文本内容: {text_content[:100]}...")

                                    # 🔥 直接更新任务状态为完成，传递文本内容
                                    task_update_result = self.api_service.update_task_status(
                                        task_id=task_id or str(uuid.uuid4()),
                                        status="1",  # 完成
                                        tenant_id=tenant_id,
                                        path="",  # 文本类接口不需要路径
                                        resource_id=None,
                                        business_id=business_id,
                                        content=text_content,  # 🔥 传递文本内容
                                        api_type=api_type  # 🔥 传递API类型
                                    )

                                    print(f"✅ [SYNC-UPLOAD] 文本类接口处理完成!")
                                    print(f"   任务更新: {'成功' if task_update_result else '失败'}")
                                else:
                                    print(f"⚠️ [SYNC-UPLOAD] 无法提取文本内容")
                                    if task_id:
                                        self.api_service.update_task_status(
                                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                        )

                            elif is_multi_image_function:
                                # 🔥 多图片URL接口处理
                                print(f"🖼️ [SYNC-UPLOAD] 检测到多图片URL接口: {func_name}")

                                success = self._handle_multi_image_urls(
                                    result, business_id, task_id or str(uuid.uuid4()), tenant_id
                                )

                                if success:
                                    print(f"✅ [SYNC-UPLOAD] 多图片处理完成!")
                                else:
                                    print(f"❌ [SYNC-UPLOAD] 多图片处理失败")
                                    if tenant_id and task_id:
                                        self.api_service.update_task_status(
                                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                        )

                            elif is_wanxiang_image_function:
                                # 🔥 万相单图片接口处理
                                print(f"🖼️ [SYNC-UPLOAD] 检测到万相图片接口: {func_name}")

                                image_url = self._extract_image_url_from_result(result)

                                if image_url:
                                    print(f"🔗 [SYNC-UPLOAD] 提取到图片URL: {image_url}")

                                    # 🔥 检查是否是阿里云URL，如果是则下载上传
                                    if "lan8-e-business.oss" not in image_url:
                                        final_image_url = self._download_and_upload_aliyun_file(
                                            image_url, task_id or str(uuid.uuid4()), "image"
                                        )
                                    else:
                                        final_image_url = image_url

                                    task_update_result = self.api_service.update_task_status(
                                        task_id=task_id or str(uuid.uuid4()),
                                        status="1",
                                        tenant_id=tenant_id,
                                        path=final_image_url,
                                        resource_id=None,
                                        business_id=business_id,
                                        api_type=api_type
                                    )

                                    print(f"✅ [SYNC-UPLOAD] 万相图片处理完成: {final_image_url}")
                                    print(f"   任务更新: {'成功' if task_update_result else '失败'}")

                                else:
                                    print(f"⚠️ [SYNC-UPLOAD] 无法提取图片URL")
                                    if task_id:
                                        self.api_service.update_task_status(
                                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                        )

                            elif is_wanxiang_video_function:
                                # 🔥 万相视频接口处理
                                print(f"🎬 [SYNC-UPLOAD] 检测到万相视频接口: {func_name}")

                                video_url = self._extract_video_url_from_result(result)

                                if video_url:
                                    print(f"🔗 [SYNC-UPLOAD] 提取到视频URL: {video_url}")

                                    # 🔥 检查是否是阿里云URL，如果是则下载上传
                                    if "lan8-e-business.oss" not in video_url:
                                        final_video_url = self._download_and_upload_aliyun_file(
                                            video_url, task_id or str(uuid.uuid4()), "video"
                                        )
                                    else:
                                        final_video_url = video_url

                                    task_update_result = self.api_service.update_task_status(
                                        task_id=task_id or str(uuid.uuid4()),
                                        status="1",
                                        tenant_id=tenant_id,
                                        path=final_video_url,
                                        resource_id=None,
                                        business_id=business_id,
                                        api_type=api_type
                                    )

                                    print(f"✅ [SYNC-UPLOAD] 万相视频处理完成: {final_video_url}")
                                    print(f"   任务更新: {'成功' if task_update_result else '失败'}")

                                else:
                                    print(f"⚠️ [SYNC-UPLOAD] 无法提取视频URL")
                                    if task_id:
                                        self.api_service.update_task_status(
                                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                        )

                            else:
                                # 🔥 普通文件类接口处理（原有逻辑）
                                print(f"📁 [SYNC-UPLOAD] 检测到普通文件类接口: {func_name}")

                                warehouse_path = extract_warehouse_path(result)

                                if warehouse_path and warehouse_path.startswith(('http://', 'https://')):
                                    # URL结果直接返回
                                    print(f"🔗 [SYNC-UPLOAD] 检测到URL结果，直接使用: {warehouse_path}")

                                    task_update_result = self.api_service.update_task_status(
                                        task_id=task_id or str(uuid.uuid4()),
                                        status="1",
                                        tenant_id=tenant_id,
                                        path=warehouse_path,
                                        resource_id=None,
                                        business_id=business_id,
                                        api_type = api_type
                                    )

                                    print(f"✅ [SYNC-UPLOAD] URL结果处理完成!")
                                    print(f"   任务更新: {'成功' if task_update_result else '失败'}")

                                elif warehouse_path:
                                    # 本地文件上传到OSS
                                    user_data_dir = config.get_user_data_dir()
                                    local_full_path = os.path.join(user_data_dir, warehouse_path)

                                    if os.path.exists(local_full_path):
                                        file_info = get_file_info(local_full_path)
                                        if file_info:
                                            # 生成OSS路径并上传
                                            oss_path = f"agent/resource/{warehouse_path}"
                                            upload_success = upload_to_oss(local_full_path, oss_path)

                                            if upload_success:
                                                print(f"✅ [SYNC-UPLOAD] OSS上传成功: {oss_path}")

                                                # 创建资源记录
                                                resource_result = self.api_service.create_resource(
                                                    resource_type=file_info['resource_type'],
                                                    name=file_info['name'],
                                                    path=oss_path,
                                                    local_full_path=local_full_path,
                                                    file_type=file_info['file_type'],
                                                    size=file_info['size'],
                                                    tenant_id=tenant_id
                                                )

                                                resource_id = resource_result.get(
                                                    'resource_id') if resource_result else None

                                                # 🔥 更新任务状态为完成，传递业务ID
                                                task_update_result = self.api_service.update_task_status(
                                                    task_id=task_id or str(uuid.uuid4()),
                                                    status="1",  # 完成
                                                    tenant_id=tenant_id,
                                                    path=oss_path,
                                                    resource_id=resource_id,
                                                    business_id=business_id,
                                                    api_type = api_type
                                                )

                                                # 生成OSS访问URL
                                                oss_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{oss_path}"

                                                print(f"✅ [SYNC-UPLOAD] 同步模式完整流程成功!")
                                                print(f"   OSS URL: {oss_url}")
                                                print(f"   资源ID: {resource_id}")
                                                print(f"   业务ID: {business_id}")
                                                print(f"   任务更新: {'成功' if task_update_result else '失败'}")

                                            else:
                                                print(f"❌ [SYNC-UPLOAD] OSS上传失败")
                                                if task_id:
                                                    self.api_service.update_task_status(
                                                        task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                                    )
                                        else:
                                            print(f"❌ [SYNC-UPLOAD] 获取文件信息失败")
                                            if task_id:
                                                self.api_service.update_task_status(
                                                    task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                                )
                                    else:
                                        print(f"❌ [SYNC-UPLOAD] 本地文件不存在: {local_full_path}")
                                        if task_id:
                                            self.api_service.update_task_status(
                                                task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                            )
                                else:
                                    print(f"⚠️ [SYNC-UPLOAD] 无法提取有效路径")
                                    if task_id:
                                        self.api_service.update_task_status(
                                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                        )

                        except Exception as upload_error:
                            print(f"⚠️ [SYNC-UPLOAD] 同步模式上传失败: {upload_error}")
                            # 上传流程失败时更新任务状态为失败
                            if tenant_id and task_id:
                                try:
                                    self.api_service.update_task_status(
                                        task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                                    )
                                except Exception as status_error:
                                    print(f"⚠️ [SYNC-UPLOAD] 更新失败状态时出错: {status_error}")

                    return {
                        "result": result,
                        "videoPath": extract_warehouse_path(result),
                        "warehouse_path": extract_warehouse_path(result),
                        "function_name": func_name,
                        "business_id": business_id,
                        "tenant_id": tenant_id,
                        "execution_mode": "sync"
                    }

            except TimeoutError:
                print(f"⏰ [SYNC-UPLOAD] 同步执行超时: {func_name}")
                # 超时时更新任务状态为失败
                if tenant_id and task_id:
                    try:
                        self.api_service.update_task_status(
                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                        )
                    except Exception as status_error:
                        print(f"⚠️ [SYNC-UPLOAD] 更新超时状态时出错: {status_error}")

                return {
                    "error": "同步执行超时",
                    "timeout": True,
                    "task_id": task_id or str(uuid.uuid4()),
                    "business_id": business_id,
                    "tenant_id": tenant_id,
                    "message": "任务执行时间过长，建议使用异步模式",
                    "suggestion": "请使用异步模式避免超时",
                    "execution_mode": "sync_timeout"
                }

            except Exception as e:
                print(f"❌ [SYNC-UPLOAD] 同步执行失败: {func_name}, 错误: {str(e)}")
                # 执行失败时更新任务状态为失败
                if tenant_id and task_id:
                    try:
                        self.api_service.update_task_status(
                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                        )
                    except Exception as status_error:
                        print(f"⚠️ [SYNC-UPLOAD] 更新失败状态时出错: {status_error}")

                import traceback
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                        "function_name": func_name,
                        "business_id": business_id,
                        "tenant_id": tenant_id,
                        "execution_mode": "sync_error"
                    }
                )

        else:
            # 🔥 异步模式：使用支持上传的方法
            print(f"🚀 [ASYNC-UPLOAD] 异步提交任务: {func_name}")
            print(f"   租户ID: {tenant_id}")
            print(f"   业务ID: {business_id}")

            try:
                # 🔥 传递业务ID给异步任务提交方法
                task_id = await self.submit_task(
                    func_name=func_name,
                    args=args,
                    task_id=task_id,
                    tenant_id=tenant_id,
                    business_id=business_id  # 🔥 传递业务ID
                )

                return {
                    "task_id": task_id,
                    "business_id": business_id,  # 🔥 返回业务ID
                    "tenant_id": tenant_id,
                    "execution_mode": "async",
                    "status": "submitted",
                    "message": "任务已提交到异步系统"
                }

            except Exception as e:
                print(f"❌ [ASYNC-UPLOAD] 异步任务提交失败: {str(e)}")
                # 提交失败时也要更新状态
                if tenant_id and task_id:
                    try:
                        self.api_service.update_task_status(
                            task_id, "2", tenant_id, business_id=business_id, api_type=api_type
                        )

                    except Exception as status_error:
                        print(f"⚠️ [ASYNC-UPLOAD] 更新提交失败状态时出错: {status_error}")

                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": f"异步任务提交失败: {str(e)}",
                        "function_name": func_name,
                        "business_id": business_id,
                        "tenant_id": tenant_id,
                        "execution_mode": "async_submit_error"
                    }
                )


    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        global results

        with self.result_condition:
            if task_id not in self.results:
                # 也检查全局results
                if task_id in results:
                    return results[task_id].copy()
                return {"status": "not_found", "message": "任务不存在"}
            return self.results[task_id].copy()


async_task_manager = AsyncTaskManager(max_workers=5, max_task_timeout=1800)

# 🔥 Import the refactored API for proper function access
from core.cliptemplate.coze.refactored_api import video_api

def generate_big_word_endpoint(company_name: str, title: str, product: str, description: str, content: str = None, **kwargs):
    """Wrapper function to properly call the refactored API generate_big_word method"""
    print(f"🔍 [generate_big_word_endpoint] 接收到的参数:")
    print(f"   company_name: {company_name}")
    print(f"   title: {title}")
    print(f"   product: {product}")
    print(f"   description: {description}")
    print(f"   content: {content}")
    print(f"   kwargs: {kwargs}")
    
    # Call the refactored API method
    return video_api.generate_big_word(
        company_name=company_name,
        title=title,
        product=product,
        description=description,
        content=content,
        **kwargs
    )

def get_video_random(req: VideoRandomRequest):
    import random
    kind = int(random.randint(1, 7))
    if kind == 1:
        result = get_video_advertisement(req.enterprise, req.description, req.product)
    elif kind == 2:
        result = get_big_word(req.enterprise, req.product, req.description)
    elif kind == 3:
        result = get_video_clicktype(req.product, req.description)
    elif kind == 4:
        result = get_video_catmeme(req.enterprise, req.product, req.description)
    elif kind == 5:
        result = get_video_incitment(req.product)
    elif kind == 6:
        result = get_video_stickman(req.enterprise, req.product, req.description)
    return result

# 执行任务函数
async def execute_task(func_name: str, args: dict, mode: str = "async", task_id: str = None, tenant_id=None, business_id=None):
    """
    🔥 修复后的异步任务执行函数 - 支持云端上传
    """
    return await async_task_manager.execute_task_with_upload(
        func_name=func_name,
        args=args,
        mode=mode,
        task_id=task_id,
        tenant_id=tenant_id,
        business_id=business_id
    )


def extract_ids_from_request(request: Request):
    """从请求中提取tenant_id和business_id"""
    tenant_id = None
    business_id = None

    try:
        # 从查询参数中获取
        tenant_id = request.query_params.get("tenant_id")

        # 尝试从请求体中获取（如果是JSON）
        if hasattr(request, '_body') and request._body:
            import json
            try:
                body = json.loads(request._body.decode('utf-8'))
                if isinstance(body, dict):
                    tenant_id = tenant_id or body.get("tenant_id")
                    business_id = body.get("id")
            except:
                pass
    except Exception as e:
        print(f"⚠️ 提取ID失败: {e}")

    return tenant_id, business_id


# 🔥 1. Pydantic 验证错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理 Pydantic 验证错误"""
    print(f"🚨 [VALIDATION ERROR] 路径: {request.url.path}")
    print(f"   错误详情: {exc.errors()}")

    # 提取租户ID和业务ID
    tenant_id, business_id = extract_ids_from_request(request)
    task_id = str(uuid.uuid4())

    # 构建详细的错误信息
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    # 生成友好的错误消息
    missing_fields = [detail["field"] for detail in error_details if detail["type"] == "missing"]
    if missing_fields:
        friendly_message = f"缺少必需参数: {', '.join(missing_fields)}"
    else:
        friendly_message = "请求参数格式不正确"

    # 🔥 如果有租户ID，更新任务状态为失败
    if tenant_id:
        try:
            # 这里调用你的 api_service.update_task_status
            # api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            print(f"📤 已更新任务状态为失败: {task_id}")
        except Exception as status_error:
            print(f"⚠️ 更新失败状态时出错: {status_error}")

    # 构建错误响应数据
    error_response_data = {
        "error": friendly_message,
        "details": error_details,
        "message": f"请求 {request.method} {request.url.path} 参数验证失败",
        "task_id": task_id,
        "tenant_id": tenant_id,
        "business_id": business_id,
        "request_path": str(request.url.path),
        "request_method": request.method
    }

    # 🔥 通过 format_response 格式化响应
    formatted_response = format_response(
        error_response_data,
        mode="sync",
        error_type="validation_error"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=formatted_response
    )


# 🔥 2. HTTP 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTP 异常"""
    print(f"🚨 [HTTP ERROR] 路径: {request.url.path}, 状态码: {exc.status_code}")
    print(f"   错误详情: {exc.detail}")

    # 提取租户ID和业务ID
    tenant_id, business_id = extract_ids_from_request(request)
    task_id = str(uuid.uuid4())

    # 🔥 如果有租户ID，更新任务状态为失败
    if tenant_id and exc.status_code >= 400:
        try:
            # api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            print(f"📤 已更新任务状态为失败: {task_id}")
        except Exception as status_error:
            print(f"⚠️ 更新失败状态时出错: {status_error}")

    # 构建错误响应数据
    error_response_data = {
        "error": str(exc.detail),
        "message": f"HTTP {exc.status_code} 错误",
        "task_id": task_id,
        "tenant_id": tenant_id,
        "business_id": business_id,
        "status_code": exc.status_code,
        "request_path": str(request.url.path),
        "request_method": request.method
    }

    # 🔥 通过 format_response 格式化响应
    formatted_response = format_response(
        error_response_data,
        mode="sync",
        error_type="http_exception"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=formatted_response
    )


# 🔥 3. 通用异常处理器
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理所有其他异常"""
    print(f"🚨 [GENERAL ERROR] 路径: {request.url.path}")
    print(f"   错误类型: {type(exc).__name__}")
    print(f"   错误详情: {str(exc)}")

    # 提取租户ID和业务ID
    tenant_id, business_id = extract_ids_from_request(request)
    task_id = str(uuid.uuid4())

    # 🔥 如果有租户ID，更新任务状态为失败
    if tenant_id:
        try:
            # api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            print(f"📤 已更新任务状态为失败: {task_id}")
        except Exception as status_error:
            print(f"⚠️ 更新失败状态时出错: {status_error}")

    # 构建错误响应数据
    error_response_data = {
        "error": "服务器内部错误",
        "message": f"处理请求时发生意外错误: {type(exc).__name__}",
        "task_id": task_id,
        "tenant_id": tenant_id,
        "business_id": business_id,
        "request_path": str(request.url.path),
        "request_method": request.method,
        "traceback": traceback.format_exc(),
        "debug": True  # 可以根据环境变量控制是否显示详细错误
    }

    # 🔥 通过 format_response 格式化响应
    formatted_response = format_response(
        error_response_data,
        mode="sync",
        error_type="general_exception"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=formatted_response
    )

# 🔥 修复的响应格式化函数
def format_response(res, mode="sync", urlpath="", error_type=None):
    """
    完整的响应格式化函数（支持错误处理和跳过上传的情况）
    """
    # 🔥 处理验证错误
    if error_type == "validation_error":
        details = res.get("details", [])
        first_detail = details[0] if details else {}

        return {
            "status": "validation_error",
            "error_code": 422,
            "error": res.get("error", "请求参数验证失败"),
            "details": {
                "field": first_detail.get("field", ""),
                "message": first_detail.get("message", "Field required"),
                "type": first_detail.get("type", "missing"),
                "message": res.get("message", "请检查请求参数格式"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id"),
                "suggestion": "请参考API文档检查请求参数格式",
                "input": first_detail.get("input", {})
            }
        }

    # 🔥 处理HTTP异常 - 改为validation_error格式
    if error_type == "http_exception":
        return {
            "status": "validation_error",
            "error_code": 422,
            "error": res.get("error", "HTTP请求错误"),
            "details": {
                "field": res.get("field", ""),
                "message": "Field required",
                "type": "missing",
                "message": res.get("message", "请求处理失败"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id"),
                "suggestion": "请参考API文档检查请求参数格式",
                "input": res.get("input", {})
            }
        }

    # 🔥 处理一般异常 - 改为validation_error格式
    if error_type == "general_exception":
        return {
            "status": "validation_error",
            "error_code": 422,
            "error": res.get("error", "服务器内部错误"),
            "details": {
                "field": res.get("field", ""),
                "message": "Field required",
                "type": "missing",
                "message": res.get("message", "服务器处理请求时发生错误"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id"),
                "suggestion": "请参考API文档检查请求参数格式",
                "input": res.get("input", {})
            }
        }

    # 原有的同步/异步模式处理逻辑
    if mode == "sync":
        # 🔥 处理超时错误 - 改为validation_error格式
        if isinstance(res, dict) and res.get("timeout"):
            return {
                "status": "validation_error",
                "error_code": 422,
                "error": res.get("error", "请求超时"),
                "details": {
                    "field": "timeout",
                    "message": "Field required",
                    "type": "missing",
                    "message": res.get("message", "请求处理超时"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "business_id": res.get("business_id"),
                    "suggestion": "请参考API文档检查请求参数格式，建议使用异步模式",
                    "input": {
                        "query_urls": {
                            "get_result": f"/get-result/{res['task_id']}",
                            "poll_result": f"/poll-result/{res['task_id']}",
                            "task_status": f"/task-status/{res['task_id']}"
                        }
                    }
                }
            }

        # 🔥 处理一般错误 - 改为validation_error格式
        if isinstance(res, dict) and "error" in res and not res.get("timeout"):
            return {
                "status": "validation_error",
                "error_code": 422,
                "error": res.get("error", "任务执行出现错误"),
                "details": {
                    "field": res.get("field", ""),
                    "message": "Field required",
                    "type": "missing",
                    "message": res.get("message", "任务执行出现错误"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "business_id": res.get("business_id"),
                    "suggestion": "请参考API文档检查请求参数格式",
                    "input": res.get("input", {})
                }
            }

        # 🔥 新增：处理跳过上传的文本结果
        if isinstance(res, dict) and res.get("content_type") == "text" and res.get("upload_skipped"):
            print(f"📝 [FORMAT-RESPONSE] 检测到跳过上传的文本结果")

            return {
                "status": "completed",
                "data": res.get("text_content", res.get("result")),
                "result_type": "text",
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "upload_info": {
                    "upload_skipped": True,
                    "skip_reason": res.get("skip_reason", "文本类接口"),
                    "integration": res.get("cloud_integration", "text_direct")
                },
                "task_update_success": res.get("task_update_success", False),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id")
            }

        # 🔥 新增：处理跳过上传的图片结果
        if isinstance(res, dict) and res.get("content_type") == "image" and res.get("upload_skipped"):
            print(f"🖼️ [FORMAT-RESPONSE] 检测到跳过上传的图片结果")

            image_url = res.get("original_image_url") or res.get("image_url")

            return {
                "status": "completed",
                "image_url": image_url,
                "result_type": "image",
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "upload_info": {
                    "upload_skipped": True,
                    "skip_reason": res.get("skip_reason", "图片类接口"),
                    "integration": res.get("cloud_integration", "image_direct"),
                    "original_url": image_url
                },
                "task_update_success": res.get("task_update_success", False),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id")
            }

        # 🔥 新增：处理跳过上传的URL结果
        if isinstance(res, dict) and res.get("content_type") == "url" and res.get("upload_skipped"):
            print(f"🔗 [FORMAT-RESPONSE] 检测到跳过上传的URL结果")

            return {
                "status": "completed",
                "url": res.get("original_url"),
                "result_type": "url",
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "upload_info": {
                    "upload_skipped": True,
                    "skip_reason": res.get("skip_reason", "URL类型结果"),
                    "integration": res.get("cloud_integration", "url_direct")
                },
                "task_update_success": res.get("task_update_success", False),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id")
            }

        # 处理包含result字段的响应
        if isinstance(res, dict) and res.get("result"):
            result_data = res["result"]

            # 检查是否包含图片URL
            if isinstance(result_data, str) and (
                    result_data.startswith('http://') or result_data.startswith('https://')):
                print(f"🖼️ [FORMAT-RESPONSE] 检测到图片URL结果: {result_data}")

                # 构建图片响应
                response = {
                    "status": "completed",
                    "image_url": result_data,
                    "result_type": "image",
                    "processing_time": res.get("processing_time"),
                    "function_name": res.get("function_name"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "business_id": res.get("business_id")
                }

                # 如果有OSS信息，添加到响应中
                if res.get("oss_upload_success"):
                    response.update({
                        "oss_upload_success": True,
                        "oss_url": res.get("oss_url"),
                        "oss_path": res.get("oss_path"),
                        "resource_id": res.get("resource_id"),
                        "cloud_access_url": res.get("oss_url"),
                        "original_image_url": result_data,
                        "integration": "oss"
                    })
                else:
                    response.update({
                        "integration": "direct_url",
                        "upload_info": {
                            "upload_skipped": res.get("upload_skipped", True),
                            "skip_reason": res.get("skip_reason", "直接返回URL")
                        }
                    })

                return response

            # 检查字典中是否包含图片URL
            elif isinstance(result_data, dict):
                # 尝试提取图片URL
                image_url = None
                url_fields = ['url', 'image_url', 'output_url', 'result_url', 'data', 'output', 'image']

                for field in url_fields:
                    if field in result_data:
                        field_value = result_data[field]
                        if isinstance(field_value, str) and (
                                field_value.startswith('http://') or field_value.startswith('https://')):
                            image_url = field_value
                            break

                if image_url:
                    print(f"🖼️ [FORMAT-RESPONSE] 从字典中检测到图片URL: {image_url}")

                    response = {
                        "status": "completed",
                        "image_url": image_url,
                        "result_type": "image",
                        "raw_result": result_data,
                        "processing_time": res.get("processing_time"),
                        "function_name": res.get("function_name"),
                        "task_id": res.get("task_id"),
                        "tenant_id": res.get("tenant_id"),
                        "business_id": res.get("business_id")
                    }

                    # 如果有OSS信息，添加到响应中
                    if res.get("oss_upload_success"):
                        response.update({
                            "oss_upload_success": True,
                            "oss_url": res.get("oss_url"),
                            "oss_path": res.get("oss_path"),
                            "resource_id": res.get("resource_id"),
                            "cloud_access_url": res.get("oss_url"),
                            "original_image_url": image_url,
                            "integration": "oss"
                        })
                    else:
                        response.update({
                            "integration": "direct_url",
                            "upload_info": {
                                "upload_skipped": res.get("upload_skipped", True),
                                "skip_reason": res.get("skip_reason", "直接返回URL")
                            }
                        })

                    return response

        # 🔥 正常的视频文件处理
        if "videoPath" in res and res["videoPath"]:
            warehouse_path = res["videoPath"]
            full_path = None
            file_exists = False

            if warehouse_path:
                try:
                    import config
                    import os
                    user_data_dir = config.get_user_data_dir()
                    full_path = os.path.join(user_data_dir, warehouse_path)
                    file_exists = os.path.exists(full_path)
                except Exception as e:
                    print(f"⚠️ 构建完整路径失败: {e}")
                    full_path = None
                    file_exists = False

            response = {
                "status": "completed",
                "videoPath": warehouse_path,
                "fullPath": full_path,
                "warehouse_path": warehouse_path,
                "full_file_path": full_path,
                "file_exists": file_exists,
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "business_id": res.get("business_id"),
                "path_info": {
                    "warehouse_path": warehouse_path,
                    "full_path": full_path,
                    "file_exists": file_exists
                }
            }

            # 添加OSS信息（如果有）
            if res.get("oss_upload_success"):
                response.update({
                    "oss_upload_success": True,
                    "oss_url": res.get("oss_url"),
                    "oss_path": res.get("oss_path"),
                    "resource_id": res.get("resource_id"),
                    "integration": "oss"
                })
            else:
                response.update({
                    "integration": "local",
                    "upload_info": {
                        "upload_skipped": res.get("upload_skipped", False),
                        "skip_reason": res.get("skip_reason", "")
                    }
                })

            return response

        elif "result" in res:
            warehouse_path = extract_warehouse_path(res["result"])
            if warehouse_path:
                full_path = None
                file_exists = False

                try:
                    import config
                    import os
                    user_data_dir = config.get_user_data_dir()
                    full_path = os.path.join(user_data_dir, warehouse_path)
                    file_exists = os.path.exists(full_path)
                except Exception as e:
                    print(f"⚠️ 构建完整路径失败: {e}")
                    full_path = None
                    file_exists = False

                response = {
                    "status": "completed",
                    "videoPath": warehouse_path,
                    "fullPath": full_path,
                    "warehouse_path": warehouse_path,
                    "full_file_path": full_path,
                    "file_exists": file_exists,
                    "processing_time": res.get("processing_time"),
                    "function_name": res.get("function_name"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "business_id": res.get("business_id"),
                    "path_info": {
                        "warehouse_path": warehouse_path,
                        "full_path": full_path,
                        "file_exists": file_exists
                    }
                }

                # 添加OSS信息（如果有）
                if res.get("oss_upload_success"):
                    response.update({
                        "oss_upload_success": True,
                        "oss_url": res.get("oss_url"),
                        "oss_path": res.get("oss_path"),
                        "resource_id": res.get("resource_id"),
                        "integration": "oss"
                    })

                return response
            else:
                # 🔥 处理无法提取路径的情况（可能是图片URL等）
                result_data = res["result"]

                # 如果是图片URL，按图片格式返回
                if isinstance(result_data, str) and (
                        result_data.startswith('http://') or result_data.startswith('https://')):
                    return {
                        "status": "completed",
                        "image_url": result_data,
                        "result_type": "image",
                        "processing_time": res.get("processing_time"),
                        "function_name": res.get("function_name"),
                        "task_id": res.get("task_id"),
                        "tenant_id": res.get("tenant_id"),
                        "business_id": res.get("business_id"),
                        "integration": "direct_url",
                        "upload_info": {
                            "upload_skipped": True,
                            "skip_reason": "图片URL直接返回"
                        }
                    }

                # 🔥 其他类型结果的通用处理
                return {
                    "status": "completed",
                    "result": result_data,
                    "result_type": "other",
                    "processing_time": res.get("processing_time"),
                    "function_name": res.get("function_name"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "business_id": res.get("business_id"),
                    "message": "任务完成，但无法识别结果类型"
                }
        else:
            # 如果没有特定的结果字段，直接返回原始响应
            return res
    else:
        # 异步模式：返回任务ID和查询信息
        return {
            "task_id": res["task_id"],
            "status": "submitted",
            "message": "任务已提交到异步系统",
            "tenant_id": res.get("tenant_id"),
            "business_id": res.get("business_id"),
            "query_urls": {
                "get_result": f"/get-result/{res['task_id']}",
                "system_status": "/debug/async-queue-status"
            },
            "system_info": {
                "version": "v2_async",
                "max_workers": getattr(res, 'max_workers', 5),
                "timeout": getattr(res, 'max_task_timeout', 1800)
            }
        }


@app.post("/video/digital-human-easy")
async def api_get_video_digital_huamn_easy_universal(
        req: dict,
        mode: str = Query("async", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """🔥 通用数字人API - 支持您的JSON格式"""
    try:
        print(f"🎯 收到通用数字人请求: {req}")

        # 🔥 修复：从请求体或URL参数获取tenant_id
        tenant_id = req.get("tenant_id") or tenant_id_query
        task_id = req.get("task_id") or task_id_query or str(uuid.uuid4())
        business_id = req.get("id")

        print(f"🎯 [数字人] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 手动参数映射
        video_input = req.get("video_input") or req.get("file_path") or req.get("video_url")
        if not video_input:
            raise HTTPException(status_code=422, detail="必须提供视频输入参数")

        topic = req.get("topic")
        if not topic:
            raise HTTPException(status_code=422, detail="必须提供topic参数")

        content = req.get("content", "")
        if content == "":
            content = None

        audio_input = req.get("audio_input") or req.get("audio_url") or req.get("audio_path", "")
        if audio_input == "":
            audio_input = None

        function_args = {
            "file_path": video_input,
            "topic": topic,
            "content": content,
            "audio_url": audio_input,
        }

        print(f"🔧 转换后的函数参数: {function_args}")

        # 🔥 修复：根据是否有tenant_id选择执行方式
        if tenant_id:
            res = await async_task_manager.execute_task_with_upload(
                func_name="get_video_digital_huamn_easy_local",
                args=function_args,
                mode=mode,
                task_id=task_id,
                tenant_id=tenant_id,
                business_id=business_id
            )
        else:
            res = await execute_task(
                func_name="get_video_digital_huamn_easy_local",
                args=function_args,
                mode=mode,
                task_id=task_id
            )
        print("结果为")
        print(res)
        response = format_response(res, mode, urlpath)
        if isinstance(response, dict):
            response.update({
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "enhanced": True
            })

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 通用API处理失败: {str(e)}")
        # 如果有租户ID，更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.get("/get-result/{task_id}")
async def get_task_result_with_oss_support(task_id: str, remove: bool = Query(False, description="是否移除结果")):
    """增强版任务结果查询接口 - 支持OSS"""
    global results, result_condition

    # 检查任务结果
    async_result = async_task_manager.get_task_status(task_id)
    if async_result.get("status") != "not_found":
        result = async_result
    else:
        with result_condition:
            if task_id not in results:
                return {
                    "status": "not_found",
                    "task_id": task_id,
                    "message": "任务不存在"
                }
            result = results.pop(task_id) if remove else results[task_id]

    task_status = result.get("status", "unknown")
    print(f"📊 [GET-RESULT] 任务状态: {task_status}")

    if task_status == "completed":
        warehouse_path = result.get("videoPath") or result.get("warehouse_path")

        response = {
            "status": "completed",
            "task_id": task_id,
            "message": "任务处理完成",
            "videoPath": warehouse_path,
            "warehouse_path": warehouse_path,
            "result": result.get("result"),
            "timestamp": result.get("timestamp") or result.get("completed_at"),
            "processing_time": result.get("processing_time"),
            "function_name": result.get("function_name")
        }

        # 🔥 如果有OSS信息，添加到响应中
        if result.get("oss_upload_success"):
            response.update({
                "oss_upload_success": True,
                "oss_url": result.get("oss_url"),
                "oss_path": result.get("oss_path"),
                "resource_id": result.get("resource_id"),
                "cloud_access_url": result.get("oss_url"),  # 云端访问URL
                "integration": "oss",
                "cloud_integration": "oss"
            })
            print(f"📊 [GET-RESULT] OSS信息:")
            print(f"   OSS URL: {result.get('oss_url')}")
            print(f"   资源ID: {result.get('resource_id')}")
        else:
            # 本地文件信息
            if warehouse_path:
                user_data_dir = config.get_user_data_dir()
                full_path = os.path.join(user_data_dir, warehouse_path)
                file_exists = os.path.exists(full_path)
                response.update({
                    "fullPath": full_path,
                    "full_file_path": full_path,
                    "file_exists": file_exists,
                    "integration": "local"
                })

        return response

    elif task_status == "failed":
        return {
            "status": "failed",
            "task_id": task_id,
            "message": f"任务处理失败: {result.get('error', '未知错误')}",
            "error": result.get("error"),
            "timestamp": result.get("timestamp") or result.get("failed_at"),
            "processing_time": result.get("processing_time")
        }

    elif task_status in ["processing", "uploading"]:
        return {
            "status": task_status,
            "task_id": task_id,
            "message": f"任务{task_status}中",
            "progress": result.get("progress", "未知"),
            "current_step": result.get("current_step", "未知"),
            "started_at": result.get("started_at")
        }

    else:
        return {
            "status": task_status,
            "task_id": task_id,
            "message": f"任务状态: {task_status}",
            "raw_result": result
        }


@app.put('/api/product')
async def update_product_info(
        request: ProductConfigRequest,
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
):
    """更新产品配置 - 支持任务状态更新"""
    try:
        tenant_id = request.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = request.id

        print(f"🎯 [产品配置] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        # 只更新提供的字段
        updates = {k: v for k, v in request.dict().items()
                   if v is not None and k not in ['tenant_id', 'id']}

        if not updates:
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            raise HTTPException(status_code=400, detail="没有提供要更新的配置项")

        # 更新配置
        success = config_manager.update_product_config(updates)

        if success:
            # 🔥 如果有tenant_id，更新任务状态为完成
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            return {
                "code": 200,
                "message": "产品配置更新成功",
                "data": config_manager.product_info,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id
            }
        else:
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            raise HTTPException(status_code=500, detail="配置保存失败")

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@app.put('/api/voice/live_config')
async def update_voice_config(
        request: VoiceConfigRequest,
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
):
    """更新语音配置 - 支持任务状态更新"""
    try:
        tenant_id = request.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = request.id

        print(f"🎯 [语音配置] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        # 只更新提供的字段
        updates = {k: v for k, v in request.dict().items()
                   if v is not None and k not in ['tenant_id', 'id']}

        if not updates:
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            raise HTTPException(status_code=400, detail="没有提供要更新的配置项")

        # 验证性别参数
        if "gender" in updates:
            if updates["gender"] not in ["female", "male", "default"]:
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise HTTPException(status_code=400, detail="性别参数必须是: female, male, default")

        # 验证速度和音调范围
        if "speed" in updates:
            if not (0.5 <= updates["speed"] <= 2.0):
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise HTTPException(status_code=400, detail="语速必须在0.5-2.0之间")

        if "pitch" in updates:
            if not (0.5 <= updates["pitch"] <= 2.0):
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise HTTPException(status_code=400, detail="音调必须在0.5-2.0之间")

        # 更新配置
        success = config_manager.update_voice_config(updates)

        if success:
            # 🔥 如果有tenant_id，更新任务状态为完成
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            return {
                "code": 200,
                "message": "语音配置更新成功",
                "data": config_manager.voice_config,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id
            }
        else:
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            raise HTTPException(status_code=500, detail="配置保存失败")

    except HTTPException:
        raise
    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@app.post('/api/server/start')
async def start_socket_server(
        req: ServerStartRequest,
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
):
    """启动WebSocket服务器 - 支持任务状态更新"""
    global socket_server, websocket_task

    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [WebSocket服务器启动] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        # 检查是否已有服务器在运行
        if 'websocket_task' in globals() and websocket_task and not websocket_task.done():
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "WebSocket服务器已经在运行中",
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                }
            )

        # 动态导入WebSocket服务器
        try:
            from websocket_server import WebSocketServer
            
            # 创建WebSocket服务器实例
            websocket_server = WebSocketServer(host=req.host, port=req.port)
            
            # 在后台任务中运行WebSocket服务器
            async def run_websocket_server():
                try:
                    await websocket_server.start_server()
                except Exception as e:
                    print(f"❌ WebSocket服务器错误: {e}")
            
            # 创建后台任务
            import asyncio
            websocket_task = asyncio.create_task(run_websocket_server())
            
            # 等待服务器启动
            await asyncio.sleep(1)
            
        except ImportError:
            # 如果没有websocket_server.py，回退到原始的TCP Socket服务器
            print("⚠️ 未找到websocket_server.py，使用TCP Socket服务器")
            socket_server = SocketServer(host=req.host, port=req.port)
            server_thread = threading.Thread(target=socket_server.start)
            server_thread.daemon = True
            server_thread.start()
            time.sleep(1)

        # 🔥 如果有tenant_id，更新任务状态为完成
        if tenant_id:
            api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

        result = {
            "status": "success",
            "message": f"WebSocket服务器已启动，监听 ws://{req.host}:{req.port}",
            "server_info": {
                "host": req.host,
                "port": req.port,
                "running": True,
                "type": "websocket" if 'websocket_server' in locals() else "tcp_socket"
            },
            "task_id": task_id,
            "tenant_id": tenant_id,
            "business_id": business_id
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"启动失败: {str(e)}",
                "task_id": locals().get('task_id'),
                "tenant_id": locals().get('tenant_id'),
                "business_id": locals().get('business_id')
            }
        )


@app.post('/api/server/stop')
async def stop_socket_server(
        req: ServerStopRequest = ServerStopRequest(),  # 🔥 修改：添加请求体参数，默认空对象
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")  # 🔥 新增
):
    """停止Socket服务器 - 支持任务状态更新"""  # 🔥 修改：更新文档
    global socket_server

    try:
        # 🔥 新增：从请求体或URL参数获取相关ID
        tenant_id = req.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [服务器停止] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 新增：如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        if not socket_server or not socket_server.running:
            # 🔥 修改：如果有tenant_id，更新任务状态为失败
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)

            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Socket服务器未运行",
                    # 🔥 新增：返回任务相关信息
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                }
            )

        socket_server.stop()

        # 🔥 新增：如果有tenant_id，更新任务状态为完成
        if tenant_id:
            api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

        return {
            "status": "success",
            "message": "Socket服务器已停止",
            # 🔥 新增：返回任务相关信息
            "task_id": task_id,
            "tenant_id": tenant_id,
            "business_id": business_id
        }

    except HTTPException:
        raise
    except Exception as e:
        # 🔥 新增：异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
                print(f"📤 [服务器停止] 已更新任务状态为失败: {task_id}")
            except Exception as status_error:
                print(f"⚠️ [服务器停止] 更新失败状态时出错: {status_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"停止失败: {str(e)}",
                # 🔥 新增：返回任务相关信息
                "task_id": locals().get('task_id'),
                "tenant_id": locals().get('tenant_id'),
                "business_id": locals().get('business_id')
            }
        )


@app.post("/text/industry")
async def api_get_text_industry(
        req: TextIndustryRequest,
        mode: str = Query("sync", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """🔥 文本行业生成API - 支持任务状态更新"""
    try:
        # 🔥 修复：从请求体或URL参数获取相关ID
        tenant_id = req.tenant_id or tenant_id_query
        task_id = task_id_query or str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [文本行业] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")
        print(f"   Mode: {mode}")

        # 过滤参数（移除不需要的字段）
        filtered_args = {
            key: value for key, value in req.dict().items()
            if key not in ['categoryId', 'tenant_id', 'id']
        }

        # 🔥 支持异步模式和任务状态更新
        if mode == "async" and tenant_id:
            # 异步模式 - 使用任务管理器
            res = await async_task_manager.execute_task_with_upload(
                func_name="get_text_industry",
                args=filtered_args,
                mode=mode,
                task_id=task_id,
                tenant_id=tenant_id,
                business_id=business_id
            )
            response = format_response(res, mode, urlpath)
        else:
            # 同步模式 - 直接执行
            print(f"📝 [文本行业] 同步执行文本生成")

            # 🔥 如果有tenant_id，立即更新任务状态为运行中
            if tenant_id:
                api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

            try:
                result = get_text_industry(**filtered_args)

                # 🔥 如果有tenant_id，更新任务状态为完成
                if tenant_id:
                    api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id, content=result)

                response = {
                    "status": "completed",
                    "data": result,
                    "message": "文本生成完成",
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "execution_mode": "sync"
                }

            except Exception as text_error:
                # 🔥 如果有tenant_id，更新任务状态为失败
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise text_error

        if isinstance(response, dict):
            response.update({
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "enhanced": True
            })

        return response

    except Exception as e:
        print(f"❌ 文本行业生成失败: {str(e)}")
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(
            status_code=500,
            detail=f"文本生成失败: {str(e)}"
        )

generator = CopyGenerator(model="qwen-max", template_dir="templates")
@app.post("/copy/generate")
async def get_copy_generator_sync(
        req: CopyGenerationRequest,
        mode: str = Query("sync", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """🔥 文案生成器API - 支持任务状态更新"""
    try:
        # 🔥 修复：从请求体或URL参数获取相关ID
        tenant_id = req.tenant_id or tenant_id_query
        task_id = task_id_query or str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [文案生成] 处理请求:")
        print(f"   类别: {req.category}")
        print(f"   风格: {req.style}")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")
        print(f"   Mode: {mode}")

        # 🔥 支持异步模式和任务状态更新
        if mode == "async" and tenant_id:
            # 异步模式 - 使用任务管理器
            function_args = {
                "category": req.category,
                "style": req.style,
                "input_data": req.input_data
            }

            res = await async_task_manager.execute_task_with_upload(
                func_name="get_copy_generation",
                args=function_args,
                mode=mode,
                task_id=task_id,
                tenant_id=tenant_id,
                business_id=business_id
            )

            response = format_response(res, mode, urlpath)
        else:
            # 同步模式 - 直接执行
            print(f"📝 [文案生成] 同步执行文案生成")

            # 🔥 如果有tenant_id，立即更新任务状态为运行中
            if tenant_id:
                api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

            try:
                result = get_copy_generation(
                    category=req.category,
                    style=req.style,
                    input_data=req.input_data,
                    use_template=req.use_template,  # 新增
                    ai_enhance=req.ai_enhance,  # 新增
                    custom_params=req.custom_params  # 新增
                )

                print(f"✅ 文案生成成功: {result[:100]}...")

                # 🔥 如果有tenant_id，更新任务状态为完成
                if tenant_id:
                    api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id, content=result)

                response = {
                    "status": "completed",
                    "data": result,
                    "message": "文案生成完成",
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "execution_mode": "sync"
                }

            except Exception as copy_error:
                # 🔥 如果有tenant_id，更新任务状态为失败
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise copy_error

        if isinstance(response, dict):
            response.update({
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "enhanced": True
            })
        print(response)
        return response

    except FileNotFoundError as e:
        error_msg = f"模板文件不存在: {str(e)}"
        print(f"❌ {error_msg}")

        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "template_not_found",
                "message": error_msg,
                "suggestion": f"请确保存在模板文件: templates/{req.category}/{req.style}.j2",
                "tenant_id": locals().get('tenant_id'),
                "task_id": locals().get('task_id')
            }
        )

    except Exception as e:
        error_msg = f"文案生成失败: {str(e)}"
        print(f"❌ {error_msg}")

        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "generation_failed",
                "message": error_msg,
                "category": req.category,
                "style": req.style,
                "tenant_id": locals().get('tenant_id'),
                "task_id": locals().get('task_id')
            }
        )

analyzer = CoverAnalyzer()


@app.post("/cover/analyze")
async def analyze_cover_endpoint(
        req: CoverAnalysisRequest,
        mode: str = Query("sync", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """🔥 分析封面图片 - 支持任务状态更新"""
    try:
        # 🔥 修复：从请求体或URL参数获取相关ID
        tenant_id = req.tenant_id or tenant_id_query
        task_id = task_id_query or str(uuid.uuid4())
        business_id = req.id
        print(req)
        print(f"🎯 [封面分析] 处理请求:")
        print(f"   Platform: {req.platform}")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")
        print(f"   Mode: {mode}")

        # 🔥 支持异步模式和任务状态更新
        if mode == "async" and tenant_id:
            # 异步模式 - 使用任务管理器
            function_args = {
                "image": req.image,
                "is_url": req.is_url,
                "platform": req.platform
            }

            # 创建包装器函数用于异步执行
            def analyze_cover_wrapper(image, is_url, platform):
                if is_url:
                    image_b64 = analyzer.image_processor.download_image_from_url(image)
                else:
                    image_data = image
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    image_b64 = image_data

                result = analyzer.analyze_cover(image_b64, platform)
                if not result["success"]:
                    raise Exception(result["error"])
                return result

            # 将包装器函数注册到全局命名空间
            globals()['analyze_cover_wrapper'] = analyze_cover_wrapper

            res = await async_task_manager.execute_task_with_upload(
                func_name="analyze_cover_wrapper",
                args=function_args,
                mode=mode,
                task_id=task_id,
                tenant_id=tenant_id,
                business_id=business_id
            )
            print("结果为")
            print(res)
            response = format_response(res, mode, urlpath)
        else:
            # 同步模式 - 直接执行
            print(f"🖼️ [封面分析] 同步执行图片分析")

            # 🔥 如果有tenant_id，立即更新任务状态为运行中
            if tenant_id:
                api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

            try:
                # 处理输入图像
                if req.is_url:
                    image_b64 = analyzer.image_processor.download_image_from_url(req.image)
                else:
                    image_data = req.image
                    if image_data.startswith('data:image'):
                        image_data = image_data.split(',')[1]
                    image_b64 = image_data

                # 执行分析
                result = analyzer.analyze_cover(image_b64, req.platform)
                print("分析结果为")
                print(result)
                if not result["success"]:
                    raise Exception(result["error"])

                # 🔥 如果有tenant_id，更新任务状态为完成
                if tenant_id:
                    # 提取分析结果文本
                    analyze_text = result.get("analysis_result", "") or str(result)

                    api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id,
                                                   content=analyze_text)
                # 添加任务信息到响应
                response_data = AnalyzeResponse(**result)
                response_dict = response_data.dict()
                response_dict.update({
                    "status": "completed",
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "execution_mode": "sync"
                })

                response = response_dict

            except Exception as analyze_error:
                # 🔥 如果有tenant_id，更新任务状态为失败
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
                raise analyze_error

        if isinstance(response, dict):
            response.update({
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "enhanced": True
            })
        return response

    except ValueError as e:
        print(f"输入验证错误: {str(e)}")

        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"分析失败: {str(e)}")

        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

# 🔥 通用API接口生成器 - 自动支持云端上传
def create_enhanced_api_endpoint(endpoint_path: str, func_name: str, request_model):
    """创建增强版API接口的通用函数 - 🔥 完全修复tenant_id和id处理"""

    @app.post(endpoint_path)
    async def enhanced_api_endpoint(
            req: request_model,
            mode: str = Query("async", description="执行模式：sync(同步)/async(异步)"),
            tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
            task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
    ):
        try:
            req_dict = req.dict()
            print(f"🔍 [DEBUG] {endpoint_path} 请求数据: {req_dict}")

            # 🔥 修复：从请求体或URL参数获取相关ID
            tenant_id = req_dict.get("tenant_id") or tenant_id_query
            task_id = req_dict.get("task_id") or task_id_query
            business_id = req_dict.get("id")

            # 如果没有task_id，生成一个
            if not task_id:
                task_id = str(uuid.uuid4())

            print(f"🎯 [API] 处理请求: {endpoint_path}")
            print(f"   Task ID: {task_id}")
            print(f"   Tenant ID: {tenant_id}")
            print(f"   Business ID: {business_id}")
            print(f"   Mode: {mode}")

            # 过滤参数（移除不需要的字段）
            # 如果是 /video/digital-human-generation 接口并且函数名是 process_single_video_by_url，则不过滤参数
            if endpoint_path == "/video/digital-human-generation" and func_name == "process_single_video_by_url":
                # 不过滤参数，直接使用原始参数
                filtered_args = req_dict
                print(f"🔧 [API] 数字人生成接口，不过滤参数: {filtered_args}")
            else:
                # 其他情况都过滤参数
                # 🔥 修复：保留必要的业务参数，只过滤系统参数
                filtered_args = {
                    key: value for key, value in req_dict.items()
                    if key not in ['categoryId', 'task_id', 'tenant_id', 'id']
                }
                print(f"🔧 [API] 过滤后参数: {filtered_args}")
                
                # 🔥 特殊处理：对于 BigWordRequest，需要保留所有业务参数
                if func_name == "generate_big_word_endpoint":
                    # 确保保留必要的参数
                    if 'company_name' in req_dict:
                        filtered_args['company_name'] = req_dict['company_name']
                    if 'title' in req_dict:
                        filtered_args['title'] = req_dict['title']
                    if 'product' in req_dict:
                        filtered_args['product'] = req_dict['product']
                    if 'description' in req_dict:
                        filtered_args['description'] = req_dict['description']
                    if 'content' in req_dict:
                        filtered_args['content'] = req_dict['content']
                    print(f"🔥 [API] BigWord参数特殊处理后: {filtered_args}")

            # 🔥 修复：根据是否有tenant_id选择执行方式
            if tenant_id:
                print(f"☁️ [API] 启用云端上传模式")
                res = await async_task_manager.execute_task_with_upload(
                    func_name=func_name,
                    args=filtered_args,
                    mode=mode,
                    task_id=task_id,
                    tenant_id=tenant_id,
                    business_id=business_id
                )
            else:
                print(f"💻 [API] 本地执行模式")
                res = await execute_task(
                    func_name=func_name,
                    args=filtered_args,
                    mode=mode,
                    task_id=task_id,
                    tenant_id=None
                )

            response = format_response(res, mode, urlpath)
            if isinstance(response, dict):
                response.update({
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id,
                    "enhanced": True,
                    "endpoint": endpoint_path,
                    "function": func_name,
                    "upload_enabled": bool(tenant_id)
                })

            return response

        except Exception as e:
            print(f"❌ [{endpoint_path}] API处理失败: {str(e)}")
            # 🔥 如果有租户ID，更新任务状态为失败，传递业务ID
            if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
                try:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
                    print(f"📤 [API] 已更新任务状态为失败: {task_id}")
                except Exception as status_error:
                    print(f"⚠️ [API] 更新失败状态时出错: {status_error}")

            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")

            raise HTTPException(
                status_code=500,
                detail=f"API处理失败: {str(e)}"
            )

    return enhanced_api_endpoint

def setup_enhanced_api_endpoints():
    """批量设置增强版API接口（区分视频和文本类型）"""

    # 🔥 视频类API接口配置（返回视频文件）
    video_api_configs = [
        ("/video/big-word", "generate_big_word_endpoint", BigWordRequest),
        ("/video/catmeme", "get_video_catmeme", CatMemeRequest),
        ("/video/clicktype", "get_video_clicktype", ClickTypeRequest),
        ("/video/advertisement", "get_video_advertisement", VideoAdvertisementRequest),
        ("/video/advertisement-enhance", "get_video_advertisement_enhance", VideoAdvertisementEnhanceRequest),
        ("/video/clothes-different-scene", "get_video_clothes_diffrent_scene", ClothesDifferentSceneRequest),
        ("/video/clip", "get_smart_clip_video", SmartClipRequest),
        ("/video/dgh-img-insert", "get_video_dgh_img_insert", DGHImgInsertRequest),
        ("/video/digital-human-clips", "get_video_digital_huamn_clips", DigitalHumanClipsRequest),
        ("/video/incitement", "get_video_incitment", IncitementRequest),
        ("/video/sinology", "get_video_sinology", SinologyRequest),
        ("/video/stickman", "get_video_stickman", StickmanRequest),
        ("/video/clothes-fast-change", "get_videos_clothes_fast_change", ClothesFastChangeRequest),
        ("/video/random", "get_video_random", VideoRandomRequest),
        # 一生十
        ("/video/digital-human-generation", "process_single_video_by_url", DigitalHumanRequest),
        ("/video/edit", "get_video_edit_simple", VideoEditMainRequest),
        # 🔥 新增：通义万相图像生成API
        ("/wanxiang/text-to-image-v2", "get_text_to_image_v2", TextToImageV2Request),
        ("/wanxiang/text-to-image-v1", "get_text_to_image_v1", TextToImageV1Request),

        # 通用图像编辑
        ("/wanxiang/image-edit", "get_image_background_edit", ImageBackgroundEditRequest),

        # ========== 虚拟模特系列 ==========
        # 虚拟模特
        ("/wanxiang/virtual-model-v1", "get_virtual_model_v1", VirtualModelV1Request),
        ("/wanxiang/virtual-model-v2", "get_virtual_model_v2", VirtualModelV2Request),

        # 鞋靴模特
        ("/wanxiang/shoe-model", "get_shoe_model", ShoeModelRequest),

        # 创意海报生成
        ("/wanxiang/creative-poster", "get_creative_poster", CreativePosterRequest),

        # 图像背景生成
        ("/wanxiang/background-generation", "get_background_generation", BackgroundGenerationRequest),

        # ========== AI试衣系列 ==========
        # AI试衣-基础版
        ("/wanxiang/ai-tryon-basic", "get_ai_tryon_basic", AITryonBasicRequest),

        # AI试衣-Plus版
        ("/wanxiang/ai-tryon-plus", "get_ai_tryon_plus", AITryonPlusRequest),

        # AI试衣-图片精修
        ("/wanxiang/ai-tryon-enhance", "get_ai_tryon_enhance", AITryonEnhanceRequest),

        # AI试衣-图片分割
        ("/wanxiang/ai-tryon-segment", "get_ai_tryon_segment", AITryonSegmentRequest),

        # ========== 视频生成系列 ==========
        # 通义万相-图生视频-基于首尾帧
        ("/wanxiang/image-to-video-advanced", "get_image_to_video_advanced", ImageToVideoAdvancedRequest),

        # ========== 数字人视频系列 ==========
        # 图生舞蹈视频-舞动人像 AnimateAnyone
        ("/wanxiang/animate-anyone", "get_animate_anyone", AnimateAnyoneRequest),

        # 图生唱演视频-悦动人像EMO
        ("/wanxiang/emo-video", "get_emo_video", EMOVideoRequest),

        # 图生播报视频-灵动人像 LivePortrait
        ("/wanxiang/live-portrait", "get_live_portrait", LivePortraitRequest),

        # ========== 视频风格重绘 ==========
        ("/wanxiang/video-style-transfer", "get_video_style_transform", VideoStyleTransferRequest),

        ("/wanxiang/video-style-transfer", "get_video_style_transform", VideoStyleTransferRequest),

        # # 新增：文案生成API配置
        # ("/copy/generate", "get_copy_generation", CopyGenerationRequest),

    ]


    # 为视频类API创建增强版接口（原有逻辑）
    for endpoint_path, func_name, request_model in video_api_configs:
        create_enhanced_api_endpoint(endpoint_path, func_name, request_model)

# 调用设置函数
setup_enhanced_api_endpoints()

# 启动服务
if __name__ == "__main__":
    uvicorn.run(
        "app:app",  # 改为模块路径格式（"文件名:应用实例名"）
        host="0.0.0.0",
        port=8100,
        # reload=True,  # 启用热重载
        reload_dirs=["."],  # 监控当前目录下的文件变化
        reload_excludes=["*.tmp"],  # 可选：排除不需要监控的文件
        reload_delay=1.0  # 可选：文件变化后延迟1秒重载
    )

"""
API 使用示例：

1. 使用本地视频文件（绝对路径）：
POST /video/edit-main
{
    "video_sources": ["/home/user/videos/input.mp4", "/home/user/videos/input2.mp4"],
    "duration": 30,
    "style": "抖音风",
    "purpose": "社交媒体",
    "merge_videos": true,
    "use_local_ai": true
}

2. 使用本地视频文件（相对路径）：
POST /video/edit-main
{
    "video_sources": ["videos/input.mp4", "materials/sample.mp4"],
    "duration": 45,
    "style": "企业风",
    "purpose": "商务演示"
}

3. 混合使用多种路径类型：
POST /video/edit-main
{
    "video_sources": [
        "/absolute/path/video1.mp4",        # 绝对路径
        "relative/video2.mp4",              # 相对路径
        "uploads/uploaded_video.mp4",       # 上传文件
        "https://example.com/online.mp4"    # 在线视频
    ],
    "duration": 60,
    "merge_videos": true
}

4. 使用已上传的视频：
POST /video/edit-main
{
    "video_sources": ["uploads/video1.mp4", "uploads/video2.mp4"],
    "duration": 30,
    "style": "抖音风",
    "tenant_id": "your_tenant_id"
}

5. 编辑在线视频：
POST /video/edit-main
{
    "video_sources": ["https://example.com/video.mp4"],
    "duration": 60,
    "style": "企业风",
    "use_local_ai": false,
    "api_key": "your_api_key"
}

6. 上传并编辑（一体化）：
POST /video/upload-and-edit
Content-Type: multipart/form-data
files: [video files]
duration: 30
style: "抖音风"
tenant_id: "your_tenant_id"

7. 查询任务状态：
GET /get-result/{task_id}

路径解析说明：
- 绝对路径（如 /home/user/video.mp4）：直接使用
- 相对路径（如 videos/video.mp4）：按以下顺序搜索
  1. 当前工作目录
  2. uploads/ 目录
  3. 用户数据目录
  4. materials/ 目录
- uploads/ 前缀：转换为 uploads 目录的完整路径
- http/https 前缀：作为在线视频URL处理

响应格式：
{
    "status": "completed",
    "task_id": "xxx",
    "videoPath": "video_edit_output/xxx/final_edited_video.mp4",
    "oss_url": "https://xxx.oss.com/xxx.mp4", // 如果启用云端上传
    "processing_time": 45.2,
    "edit_info": {
        "target_duration": 30,
        "target_style": "抖音风",
        "ai_mode": "local"
    }
}
"""
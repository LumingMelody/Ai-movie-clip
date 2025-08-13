import argparse
import threading
import queue
import time
import asyncio
import json
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import uvicorn
import os
# 解决 OpenMP 库冲突问题
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import uuid
from typing import Optional, Union, Dict, List, Any
from threading import Condition

# 设置日志
logger = logging.getLogger(__name__)

# ========== 重构：常量定义 ==========
class APIConstants:
    """API相关常量"""
    DEFAULT_MODE = "async"
    SYNC_MODE = "sync"
    ASYNC_MODE = "async"
    
    # 状态码
    STATUS_PENDING = "0"
    STATUS_COMPLETED = "1"
    STATUS_FAILED = "2"
    
    # 错误类型
    ERROR_VALIDATION = "validation_error"
    ERROR_GENERAL = "general_exception"
    
    # API类型
    API_TYPE_DEFAULT = "default"
    API_TYPE_DIGITAL_HUMAN = "digital_human"
    
    # 响应类型
    RESPONSE_TYPE_VIDEO = "video"
    RESPONSE_TYPE_IMAGE = "image"
    RESPONSE_TYPE_TEXT = "text"
    RESPONSE_TYPE_ANALYSIS = "analysis"

class ResponseMessages:
    """响应消息常量"""
    VALIDATION_ERROR = "请求参数验证失败"
    PROCESSING_ERROR = "处理失败"
    TASK_SUBMIT_ERROR = "提交任务失败"
    STATUS_UPDATE_ERROR = "状态更新失败"
    FILE_NOT_FOUND = "文件不存在"
    UPLOAD_FAILED = "上传失败"

from fastapi import HTTPException, FastAPI, Request, status, Query, UploadFile, File, WebSocket
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pydantic import ValidationError, BaseModel, Field
import oss2
import requests
import config

from core.clipgenerate.interface_function import get_smart_clip_video, download_file_from_url, upload_to_oss, \
    OSS_BUCKET_NAME, OSS_ENDPOINT, get_file_info, get_video_edit_simple
from video_highlight_clip import process_video_highlight_clip
from core.clipgenerate.interface_model import (
    VideoAdvertisementRequest, VideoAdvertisementEnhanceRequest, ClickTypeRequest,
    DigitalHumanRequest, DigitalHumanEasyRequest, ClothesDifferentSceneRequest, BigWordRequest, CatMemeRequest,
    IncitementRequest, SinologyRequest, StickmanRequest, ClothesFastChangeRequest,
    DGHImgInsertRequest, DigitalHumanClipsRequest, SmartClipRequest,
    VideoRandomRequest, ProductConfigRequest, VoiceConfigRequest,
    ServerStartRequest, ServerStopRequest, AutoIntroStartRequest, AutoIntroStopRequest,
    TextIndustryRequest, CopyGenerationRequest, CoverAnalysisRequest,
    VideoEditMainRequest, AIAvatarUnifiedRequest, TimelineGenerationRequest, TimelineModifyRequest,
    VideoHighlightsRequest, VideoHighlightClipRequest, NaturalLanguageVideoEditRequest
)
from core.clipgenerate.tongyi_wangxiang_model import (
    TextToImageV2Request, TextToImageV1Request, ImageBackgroundEditRequest,
    VirtualModelV1Request, VirtualModelV2Request, ShoeModelRequest,
    CreativePosterRequest, BackgroundGenerationRequest,
    AITryonBasicRequest, AITryonPlusRequest, AITryonEnhanceRequest, AITryonSegmentRequest,
    ImageToVideoAdvancedRequest, AnimateAnyoneRequest, EMOVideoRequest, LivePortraitRequest,
    VideoStyleTransferRequest, AITryonBasicRequest, AITryonPlusRequest,
    ImageInpaintingRequest, PersonalPortraitRequest,
    DoodlePaintingRequest, ArtisticTextRequest,
    ImageUpscaleRequest, ImageStyleTransferRequest, VideoStyleTransferRequest, ImageOutpaintingRequest,
    TextToVideoRequest, VideoEditRequest
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
from core.cliptemplate.coze.auto_live_reply import SocketServer, WebSocketClient, config_manager
from websocket_client import ManualWebSocketClient
from core.cliptemplate.coze.video_advertsment import get_video_advertisement
from video_cut.tag_video_generator.api_handler import TagVideoAPIHandler
from core.cliptemplate.coze.video_advertsment_enhance import get_video_advertisement_enhance
from core.cliptemplate.coze.video_big_word import get_big_word
from core.cliptemplate.coze.video_catmeme import get_video_catmeme
from core.cliptemplate.coze.video_clicktype import get_video_clicktype
from core.cliptemplate.coze.video_clothes_diffrenent_scene import get_video_clothes_diffrent_scene
from core.cliptemplate.coze.video_dgh_img_insert import get_video_dgh_img_insert
from core.cliptemplate.coze.video_digital_human_clips import get_video_digital_huamn_clips
from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_huamn_easy, \
    get_video_digital_huamn_easy_local
from core.cliptemplate.coze.video_generate_live import process_single_video_by_url
from core.cliptemplate.coze.video_incitment import get_video_incitment
from core.cliptemplate.coze.video_sinology import get_video_sinology
from core.cliptemplate.coze.video_stickman import get_video_stickman
from core.cliptemplate.coze.videos_clothes_fast_change import get_videos_clothes_fast_change
from core.cliptemplate.coze.text_industry import get_text_industry
from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator
from core.text_generate.generator import get_copy_generation, CopyGenerator
from core.cliptemplate.coze.t15 import extract_video_highlights_from_url
from core.clipgenerate.natural_language_video_edit import process_natural_language_video_edit

from core.cliptemplate.coze.refactored_api import UnifiedVideoAPI

app = FastAPI(
    title="🚀 AI视频生成统一API系统",
    description="集成Coze视频生成和通义万相AI功能的统一API系统，提供30+个视频和图像生成接口",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# 全局变量存储Socket服务器实例
socket_server = None
# 全局变量存储WebSocket客户端实例
websocket_client = None
# 全局变量存储自动产品介绍WebSocket客户端实例
auto_intro_client = None

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
    user_data_dir = config.get_user_data_dir()  # /project_root/ikun

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
    else:
        # 🔥 如果是相对路径但以 ikun/ 开头，去掉 ikun/ 前缀
        if video_path.startswith('ikun/'):
            video_path = video_path[5:]  # 去掉 "ikun/" 前缀
            print(f"🔄 去除ikun前缀: {video_path}")
        elif video_path.startswith('ikun\\'):
            video_path = video_path[5:]  # 去掉 "ikun\\" 前缀
            print(f"🔄 去除ikun前缀(Windows): {video_path}")

    # 标准化路径分隔符（统一使用正斜杠）
    warehouse_path = video_path.replace('\\', '/')

    # 移除开头的斜杠（如果有）
    if warehouse_path.startswith('/'):
        warehouse_path = warehouse_path[1:]

    print(f"✅ 最终warehouse路径: {warehouse_path}")
    return warehouse_path


# ========== 重构：通用错误处理和响应格式化 ==========
class ResponseFormatter:
    """统一的响应格式化器"""
    
    @staticmethod
    def format_success_response(result, task_id=None, tenant_id=None, business_id=None, 
                              processing_time=0, function_name="", response_type="video"):
        """格式化成功响应"""
        return {
            "status": "completed",
            "data": result,
            "result_type": response_type,
            "processing_time": processing_time,
            "function_name": function_name,
            "task_id": task_id,
            "tenant_id": tenant_id,
            "business_id": business_id
        }
    
    @staticmethod
    def format_async_response(task_id, urlpath=""):
        """格式化异步响应"""
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "任务已提交，请使用task_id查询结果",
            "poll_url": f"/poll-result/{task_id}",
            "get_url": f"/get-result/{task_id}",
            "warehouse_base_url": urlpath
        }
    
    @staticmethod
    def format_error_response(error_msg, error_type=None, task_id=None, tenant_id=None, 
                            business_id=None, function_name="", details=None):
        """格式化错误响应"""
        if error_type == APIConstants.ERROR_VALIDATION:
            first_detail = (details or [{}])[0]
            return {
                "status": "validation_error",
                "error_code": 422,
                "error": error_msg,
                "details": {
                    "field": first_detail.get("field", ""),
                    "message": first_detail.get("message", "Field required"),
                    "type": first_detail.get("type", "missing"),
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "id": business_id,
                    "suggestion": "请参考API文档检查请求参数格式",
                    "function_name": function_name
                }
            }
        else:
            return {
                "status": "error",
                "error_code": 500,
                "error": error_msg,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "function_name": function_name,
                "timestamp": datetime.now().isoformat()
            }

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
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "id": res.get("business_id"),
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
                "type": "missing",
                "message": res.get("message", "请求处理失败"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "id": res.get("business_id"),
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
                "type": "missing",
                "message": res.get("message", "服务器处理请求时发生错误"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "id": res.get("business_id"),
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
                    "type": "missing",
                    "message": res.get("message", "请求处理超时"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "id": res.get("business_id"),
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
                    "type": "missing",
                    "message": res.get("message", "任务执行出现错误"),
                    "task_id": res.get("task_id"),
                    "tenant_id": res.get("tenant_id"),
                    "id": res.get("business_id"),
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
                "id": res.get("business_id")
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
                "id": res.get("business_id")
            }

        # 正常的成功结果处理
        warehouse_path = extract_warehouse_path(res)

        if warehouse_path and warehouse_path != "MULTI_IMAGE_URLS":
            final_url = f"{urlpath}{warehouse_path}"

            return {
                "status": "completed",
                "videoPath": warehouse_path,
                "video_url": final_url,
                "warehouse_path": warehouse_path,
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "id": res.get("business_id")
            }

        # 处理AI试衣分割的特殊情况
        elif warehouse_path == "MULTI_IMAGE_URLS":
            return {
                "status": "completed",
                "result": res,
                "result_type": "multi_images",
                "processing_time": res.get("processing_time"),
                "function_name": res.get("function_name"),
                "task_id": res.get("task_id"),
                "tenant_id": res.get("tenant_id"),
                "id": res.get("business_id")
            }

        # 默认返回原始结果
        return {
            "status": "completed",
            "result": res,
            "processing_time": res.get("processing_time", 0),
            "function_name": res.get("function_name"),
            "task_id": res.get("task_id"),
            "tenant_id": res.get("tenant_id"),
            "id": res.get("business_id")
        }

    # 异步模式返回任务ID
    else:
        return {
            "status": "submitted",
            "task_id": res,
            "message": "任务已提交，请使用task_id查询结果",
            "query_urls": {
                "get_result": f"/get-result/{res}",
                "poll_result": f"/poll-result/{res}",
                "task_status": f"/task-status/{res}"
            }
        }


# 首先需要添加API配置类和服务
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
        """数字人视频编辑专用状态更新接口"""
        return f"{self.admin_api_base}/agent/task-video-edit/update"

    def create_resource_url(self):
        """创建资源的接口"""
        return f"{self.admin_api_base}/agent/resource/create"


class APIService:
    def __init__(self, config: APIConfig):
        self.config = config
        self.base_url = "https://agent.cstlanbaai.com/gateway"
        self.admin_api_base = f"{self.base_url}/admin-api"

    def update_task_status(self, task_id: str, status: str = "1", tenant_id=None, path: str = "",
                           resource_id=None, business_id=None, content=None, api_type="default"):
        """更新任务状态"""
        try:
            # 🔥 根据api_type选择不同的接口
            if api_type == "digital_human":
                url = self.config.update_task_video_edit_update()
                print(f"🤖 [API-UPDATE] 使用数字人专用接口: {url}")
            else:
                url = self.config.update_task_status()
                print(f"📝 [API-UPDATE] 使用通用接口: {url}")

            headers = self.config.get_headers(tenant_id)

            payload = {
                "task_id": task_id,
                "status": status,
                "path": path,
                "resourceId": resource_id,
                "id": business_id
            }

            if content:
                payload["content"] = content

            print(f"🔄 [API-UPDATE] 更新任务状态: {task_id} -> {status} (type: {api_type})")
            print(payload)
            response = requests.put(url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                print(f"✅ [API-UPDATE] 状态更新成功")
                return True
            else:
                print(f"❌ [API-UPDATE] 状态更新失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ [API-UPDATE] 状态更新异常: {str(e)}")
            return False

    def create_resource(self, resource_type: str, name: str, path: str, local_full_path: str, file_type: str, size: int,
                        tenant_id=None):
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


# 创建API服务实例
api_config = APIConfig()
api_service = APIService(api_config)

# ========== 重构：通用端点处理装饰器 ==========
class EndpointHandler:
    """统一的端点处理器，减少重复代码"""
    
    def __init__(self, api_service, task_manager=None):
        self.api_service = api_service
        self.task_manager = task_manager
        self.response_formatter = ResponseFormatter()
        
    def create_endpoint_wrapper(self, business_func, function_name, async_func_name=None, 
                               is_digital_human=False, response_type="video"):
        """创建统一的端点包装器，进一步减少重复代码"""
        
        async def endpoint_wrapper(request):
            """通用端点包装器"""
            # 注册异步处理函数
            if async_func_name:
                globals()[async_func_name] = business_func
            
            # 获取模式
            mode = getattr(request, 'mode', APIConstants.DEFAULT_MODE)
            
            if mode == APIConstants.SYNC_MODE:
                return self.handle_sync_endpoint(
                    business_func, request, function_name,
                    is_digital_human=is_digital_human, 
                    response_type=response_type
                )
            else:
                return await self.handle_async_endpoint(
                    request, business_func, async_func_name or function_name,
                    mode=mode, urlpath=urlpath
                )
        
        return endpoint_wrapper
    
    def handle_sync_endpoint(self, func, request, function_name, is_digital_human=False, response_type="video"):
        """处理同步端点的通用逻辑"""
        try:
            # 提取通用参数
            task_id = getattr(request, 'task_id', str(uuid.uuid4()))
            tenant_id = getattr(request, 'tenant_id', None)
            business_id = getattr(request, 'business_id', None)
            
            start_time = time.time()
            
            # 调用业务函数
            result = func(**request.dict())
            
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            
            # 使用增强函数处理结果
            enhanced_result = enhance_endpoint_result(result, function_name, request, is_digital_human=is_digital_human)
            
            return enhanced_result
            
        except Exception as e:
            # 统一错误处理
            error_res = {"error": str(e), "function_name": function_name}
            return format_response(error_res, mode="sync", error_type=APIConstants.ERROR_GENERAL)
    
    async def handle_async_endpoint(self, request, func, function_name, mode=None, urlpath=""):
        """处理异步端点的通用逻辑"""
        try:
            # 提取参数
            task_id = getattr(request, 'task_id', str(uuid.uuid4()))
            tenant_id = getattr(request, 'tenant_id', None)
            business_id = getattr(request, 'business_id', None)
            
            # 提交异步任务
            if self.task_manager:
                actual_task_id = await self.task_manager.submit_task(
                    func_name=function_name,
                    args=request.dict(),
                    task_id=task_id,
                    tenant_id=tenant_id,
                    business_id=business_id
                )
            else:
                actual_task_id = task_id
            
            return format_response(actual_task_id, mode="async", urlpath=urlpath)
            
        except Exception as e:
            error_res = {"error": str(e), "function_name": function_name}
            return format_response(error_res, mode="sync", error_type=APIConstants.ERROR_GENERAL)
    
    def unified_endpoint_handler(self, request, func, function_name, is_digital_human=False, 
                                response_type="video", urlpath=""):
        """统一的端点处理逻辑，自动判断同步/异步模式"""
        mode = getattr(request, 'mode', APIConstants.DEFAULT_MODE)
        
        if mode == APIConstants.SYNC_MODE:
            return self.handle_sync_endpoint(func, request, function_name, is_digital_human, response_type)
        else:
            return self.handle_async_endpoint(request, func, function_name, mode, urlpath)

class TaskStatusManager:
    """任务状态管理器，统一处理状态更新逻辑"""
    
    def __init__(self, api_service):
        self.api_service = api_service
    
    def update_task_status(self, task_id, status, tenant_id=None, business_id=None, 
                          path="", resource_id=None, content=None, api_type="default"):
        """统一的任务状态更新"""
        try:
            return self.api_service.update_task_status(
                task_id=task_id,
                status=status,
                tenant_id=tenant_id,
                business_id=business_id,
                path=path,
                resource_id=resource_id,
                content=content,
                api_type=api_type
            )
        except Exception as e:
            print(f"❌ [STATUS-UPDATE] 更新任务状态失败: {str(e)}")
            return False
    
    def update_to_completed(self, task_id, tenant_id=None, business_id=None, path="", 
                           resource_id=None, api_type="default"):
        """更新任务状态为完成"""
        return self.update_task_status(
            task_id, APIConstants.STATUS_COMPLETED, tenant_id, business_id, 
            path, resource_id, api_type=api_type
        )
    
    def update_to_failed(self, task_id, tenant_id=None, business_id=None, api_type="default"):
        """更新任务状态为失败"""
        return self.update_task_status(
            task_id, APIConstants.STATUS_FAILED, tenant_id, business_id, api_type=api_type
        )


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
        # 🔥 新增：启动超时检查线程
        self.timeout_checker_thread = threading.Thread(target=self._check_timeouts, daemon=True)
        self.timeout_checker_thread.start()
        print(f"🚀 异步任务管理器初始化: max_workers={max_workers}, timeout={max_task_timeout}s")

    async def submit_task(self, func_name: str, args: dict, task_id: str = None, tenant_id=None,
                          business_id=None) -> str:
        """支持云端上传的任务提交 - 🔥 避免重复状态更新"""
        if not task_id:
            task_id = str(uuid.uuid4())

        # 检查函数是否存在 - 支持service.video_api方法
        func = self._get_function(func_name)
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

    def _get_function(self, func_name: str):
        """
        获取函数对象，支持全局函数和service.video_api方法

        Args:
            func_name: 函数名称

        Returns:
            函数对象或None
        """
        # 1. 首先尝试在全局范围内查找
        func = globals().get(func_name)
        if func:
            return func

        # 2. 如果不在全局范围，检查是否为service.video_api的方法
        if hasattr(service, 'video_api') and hasattr(service.video_api, func_name):
            return getattr(service.video_api, func_name)

        # 3. 如果还是找不到，返回None
        return None

    def _execute_task_with_timeout(self, task_id: str, func_name: str, args: dict):
        """执行任务的基础方法（带超时）"""
        start_time = time.time()

        try:
            # 更新状态为处理中
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "status": "processing",
                        "started_at": start_time,
                        "progress": "20%",
                        "current_step": "开始处理"
                    })
                    self.result_condition.notify_all()

            # 检查函数是否存在 - 支持service.video_api方法
            func = self._get_function(func_name)
            if not func:
                raise ValueError(f"函数不存在: {func_name}")

            # 执行函数
            print(f"🚀 [EXECUTE] 开始执行函数: {func_name}")
            result = func(**args)

            end_time = time.time()
            processing_time = round(end_time - start_time, 2)

            print(f"✅ [EXECUTE] 函数执行完成: {func_name}, 耗时: {processing_time}s")

            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "timestamp": end_time,
                "started_at": start_time,
                "completed_at": end_time,
                "processing_time": processing_time,
                "function_name": func_name
            }

        except Exception as e:
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)

            print(f"❌ [EXECUTE] 函数执行失败: {func_name}, 错误: {str(e)}")

            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": end_time,
                "started_at": start_time,
                "failed_at": end_time,
                "processing_time": processing_time,
                "function_name": func_name
            }

    def _execute_task_with_oss_upload(self, task_id: str, func_name: str, args: dict, tenant_id=None, business_id=None):
        """🔥 执行任务并上传到OSS - 简化版本"""
        print(f"🎯 [OSS-UPLOAD] 开始执行任务: {task_id}")
        print(f"   业务ID: {business_id}")

        # 1. 执行原有任务
        result = self._execute_task_with_timeout(task_id, func_name, args)

        # 2. 处理结果
        if result["status"] == "failed" and tenant_id:
            # 任务失败时，更新状态为失败
            try:
                print(f"❌ [OSS-UPLOAD] 任务执行失败，更新状态为失败")
                self.api_service.update_task_status(
                    task_id=task_id,
                    status="2",  # 失败状态
                    tenant_id=tenant_id,
                    business_id=business_id,
                    path="",
                    resource_id=None
                )
                print(f"✅ [OSS-UPLOAD] 失败状态更新成功")
            except Exception as e:
                print(f"❌ [OSS-UPLOAD] 更新失败状态时出错: {str(e)}")
        elif result["status"] == "completed" and tenant_id:
            try:
                print(f"☁️ [OSS-UPLOAD] 处理结果并更新状态")

                # 更新最终状态
                with self.result_condition:
                    if task_id in self.results:
                        self.results[task_id].update(result)
                        self.results[task_id]["cloud_integration"] = "oss"
                        self.result_condition.notify_all()

                # 更新远程状态（简化）
                try:
                    warehouse_path = extract_warehouse_path(result["result"])
                    if warehouse_path:
                        # 🔥 实际上传文件到OSS
                        user_data_dir = config.get_user_data_dir()
                        local_full_path = os.path.join(user_data_dir, warehouse_path.replace('/', os.path.sep))

                        if os.path.exists(local_full_path):
                            # 生成OSS路径并上传
                            oss_path = f"agent/resource/{warehouse_path}"
                            upload_success = upload_to_oss(local_full_path, oss_path)

                            if upload_success:
                                # 🔥 构建并打印最终OSS访问URL
                                final_oss_url = f'https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/{oss_path}'
                                print(f"🌐 [OSS-URL] 最终访问链接: {final_oss_url}")

                                # 🔥 调用create_resource保存资源到素材库
                                try:
                                    file_info = get_file_info(local_full_path)
                                    if file_info:
                                        resource_result = self.api_service.create_resource(
                                            resource_type=file_info['resource_type'],
                                            name=file_info['name'],
                                            path=oss_path,
                                            local_full_path=local_full_path,
                                            file_type=file_info['file_type'],
                                            size=file_info['size'],
                                            tenant_id=tenant_id
                                        )

                                        # 从响应中获取resource_id
                                        resource_id = None
                                        if resource_result:
                                            resource_id = resource_result.get('resource_id', 95)
                                            print(f"📚 [RESOURCE] 资源创建成功，ID: {resource_id}")
                                        else:
                                            resource_id = 95  # 默认值
                                            print(f"⚠️ [RESOURCE] 资源创建失败，使用默认ID: {resource_id}")
                                    else:
                                        resource_id = 95  # 默认值
                                        print(f"⚠️ [RESOURCE] 无法获取文件信息，使用默认ID: {resource_id}")
                                except Exception as e:
                                    resource_id = 95  # 默认值
                                    print(f"❌ [RESOURCE] 资源创建异常: {str(e)}，使用默认ID: {resource_id}")

                                self.api_service.update_task_status(
                                    task_id=task_id,
                                    status="1",
                                    tenant_id=tenant_id,
                                    path=oss_path,
                                    resource_id=resource_id,
                                    business_id=business_id
                                )
                                print(f"✅ [OSS-UPLOAD] 状态更新成功")
                            else:
                                print(f"❌ [OSS-UPLOAD] 文件上传失败")
                                # 即使上传失败也更新状态，使用本地路径
                                self.api_service.update_task_status(
                                    task_id=task_id,
                                    status="1",
                                    tenant_id=tenant_id,
                                    path=warehouse_path,
                                    business_id=business_id
                                )
                        else:
                            print(f"⚠️ [OSS-UPLOAD] 本地文件不存在: {local_full_path}")
                            # 文件不存在，直接更新状态
                            self.api_service.update_task_status(
                                task_id=task_id,
                                status="1",
                                tenant_id=tenant_id,
                                path=warehouse_path,
                                business_id=business_id
                            )
                    else:
                        print(f"⚠️ [OSS-UPLOAD] 未找到有效路径，跳过状态更新")
                except Exception as e:
                    print(f"❌ [OSS-UPLOAD] 状态更新失败: {str(e)}")

            except Exception as e:
                print(f"❌ [OSS-UPLOAD] 处理失败: {str(e)}")

        # 更新本地结果
        with self.result_condition:
            if task_id in self.results:
                self.results[task_id].update(result)
                self.result_condition.notify_all()

        return result

    async def _handle_task_result_with_upload(self, task_id: str, future, tenant_id=None, business_id=None,
                                              api_type="default"):
        """处理任务结果"""
        try:
            result = await future
            print(f"🎉 [ASYNC] 任务完成: {task_id}")
        except Exception as e:
            print(f"❌ [ASYNC] 任务异常: {task_id}, 错误: {str(e)}")

            # 更新失败状态
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "status": "failed",
                        "error": str(e),
                        "failed_at": time.time()
                    })
                    self.result_condition.notify_all()
        finally:
            # 清理
            if task_id in self.active_futures:
                del self.active_futures[task_id]

    def get_result(self, task_id: str):
        """获取任务结果"""
        with self.result_condition:
            return self.results.get(task_id)

    def get_all_results(self):
        """获取所有任务结果"""
        with self.result_condition:
            return self.results.copy()
    
    def _check_timeouts(self):
        """定期检查超时任务的线程"""
        while True:
            try:
                time.sleep(30)  # 每30秒检查一次
                current_time = time.time()
                
                with self.result_condition:
                    for task_id, result in self.results.items():
                        # 只检查处理中的任务
                        if result.get('status') in ['processing', 'uploading']:
                            started_at = result.get('started_at', 0)
                            if started_at > 0:
                                elapsed_time = current_time - started_at
                                
                                # 如果超过最大超时时间
                                if elapsed_time > self.max_task_timeout:
                                    print(f"⏰ [TIMEOUT] 任务 {task_id} 超时 ({elapsed_time:.1f}s > {self.max_task_timeout}s)")
                                    
                                    # 更新本地状态为失败
                                    result.update({
                                        'status': 'failed',
                                        'error': f'任务超时 ({self.max_task_timeout}秒)',
                                        'failed_at': current_time,
                                        'timeout': True
                                    })
                                    
                                    # 如果有tenant_id，更新远程状态
                                    tenant_id = result.get('tenant_id')
                                    business_id = result.get('business_id')
                                    if tenant_id and task_id not in self.status_updated_tasks:
                                        try:
                                            self.api_service.update_task_status(
                                                task_id=task_id,
                                                status="2",  # 失败状态
                                                tenant_id=tenant_id,
                                                business_id=business_id,
                                                path="",
                                                resource_id=None
                                            )
                                            self.status_updated_tasks.add(task_id)
                                            print(f"✅ [TIMEOUT] 已更新任务 {task_id} 状态为失败")
                                        except Exception as e:
                                            print(f"❌ [TIMEOUT] 更新任务状态失败: {str(e)}")
                                    
                                    # 取消对应的future
                                    if task_id in self.active_futures:
                                        future = self.active_futures[task_id]
                                        if not future.done():
                                            future.cancel()
                                        del self.active_futures[task_id]
                    
                    self.result_condition.notify_all()
                    
            except Exception as e:
                print(f"❌ [TIMEOUT-CHECK] 超时检查异常: {str(e)}")
                time.sleep(60)  # 出错后等待更长时间


# 创建任务管理器实例
task_manager = AsyncTaskManager()

# ========== 重构：创建管理器实例 ==========
status_manager = TaskStatusManager(api_service)
endpoint_handler = EndpointHandler(api_service, task_manager)


class VideoGenerationService:
    def __init__(self):
        self.video_api = UnifiedVideoAPI()

    async def generate_video_safely(self, video_type: str, **kwargs):
        try:
            result = self.video_api.generate_video_by_type(video_type, **kwargs)
            return format_response({"result": result, "type": video_type}, mode="sync", urlpath=urlpath)
        except ValueError as e:
            error_res = {"error": f"参数错误: {str(e)}", "function_name": "generate_video_safely"}
            return format_response(error_res, mode="sync", error_type="validation_error")
        except Exception as e:
            error_res = {"error": f"生成失败: {str(e)}", "function_name": "generate_video_safely"}
            return format_response(error_res, mode="sync", error_type="general_exception")


# 使用服务
service = VideoGenerationService()


# 通用的异步端点处理函数
async def handle_async_endpoint(request, sync_func, func_name, *args, **kwargs):
    """
    通用的异步端点处理函数

    Args:
        request: 请求对象
        sync_func: 同步执行的函数
        func_name: 函数名称（用于异步任务管理）
        *args, **kwargs: 传递给函数的参数
    """
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    if mode == "sync":
        # 同步模式
        try:
            result = sync_func(*args, **kwargs)
            # 使用增强函数处理结果
            is_digital_human = 'digital_human' in func_name or 'process_single_video' in func_name
            return enhance_endpoint_result(result, func_name, request, is_digital_human=is_digital_human)
        except Exception as e:
            error_res = {"error": str(e), "function_name": func_name}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 异步模式
        try:
            # 🔥 修复：如果提供了额外参数，使用它们；否则从request对象提取参数
            if kwargs:
                # 使用传递的kwargs作为任务参数
                task_args = kwargs.copy()
                print(f"🔥 [handle_async_endpoint] 使用传递的参数: {task_args}")
            else:
                # 从request对象提取参数
                task_args = request.dict() if hasattr(request, 'dict') else {}
                # 移除不需要的系统字段
                for field in ['categoryId', 'tenant_id', 'id', 'mode']:
                    task_args.pop(field, None)
                print(f"🔥 [handle_async_endpoint] 从request提取参数: {task_args}")

            task_id = await task_manager.submit_task(
                func_name=func_name,
                args=task_args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )

            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            error_res = {"error": str(e), "function_name": func_name}
            return format_response(error_res, mode="sync", error_type="general_exception")


def enhance_endpoint_result(result, function_name, request, is_digital_human=False):
    """
    🔥 通用的端点结果增强函数 - 为所有接口提供统一的增强处理
    """
    import time
    import uuid

    task_id = str(uuid.uuid4())
    tenant_id = getattr(request, 'tenant_id', None)
    business_id = getattr(request, 'id', None)
    start_time = time.time()
    end_time = time.time()
    processing_time = round(end_time - start_time, 2)

    print(f"🔥 [ENHANCE] 增强处理接口: {function_name}")
    print(f"   Task ID: {task_id}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   Business ID: {business_id}")
    print(f"   是否数字人: {is_digital_human}")

    # 🔥 构建和app.py相同的增强结果对象
    # 处理结果URL - 区分阿里云返回的完整URL和本地文件路径
    is_external_url = isinstance(result, str) and result.startswith(('http://', 'https://'))

    # 检查是否是阿里云的OSS URL（dashscope-result或其他阿里云域名）
    is_aliyun_oss_url = (is_external_url and
                         any(domain in result for domain in [
                             'dashscope-result-bj.oss-cn-beijing.aliyuncs.com',
                             'dashscope-result-sh.oss-cn-shanghai.aliyuncs.com',
                             'dashscope-file-mgr.oss-cn-beijing.aliyuncs.com',
                             '.aliyuncs.com'
                         ]))

    # 如果是阿里云OSS URL，需要下载并上传到我们自己的OSS
    if is_aliyun_oss_url:
        print(f"🔄 [ENHANCE] 检测到阿里云OSS URL，准备下载并上传到自己的OSS")
        try:
            # 1. 下载文件
            from core.clipgenerate.interface_function import download_file_from_url, upload_to_oss

            # 根据URL或函数名判断文件扩展名
            if 'image' in function_name or 'wanxiang' in function_name or '.png' in result.lower() or '.jpg' in result.lower() or '.jpeg' in result.lower():
                file_extension = '.png'
            elif '.mp4' in result.lower() or 'video' in function_name:
                file_extension = '.mp4'
            else:
                # 从URL中提取扩展名
                from urllib.parse import urlparse
                parsed_url = urlparse(result)
                path = parsed_url.path
                if '.' in path:
                    file_extension = '.' + path.split('.')[-1].split('?')[0]
                else:
                    file_extension = '.png'  # 默认为图片

            local_filename = f"{task_id}{file_extension}"
            local_path = os.path.join(config.get_user_data_dir(), local_filename)

            # 下载文件
            temp_file_path = download_file_from_url(result)
            if not temp_file_path:
                raise Exception("文件下载失败")

            # 将下载的文件移动到指定位置
            import shutil
            shutil.move(temp_file_path, local_path)

            # 2. 上传到自己的OSS
            oss_path = f"agent/resource/{local_filename}"
            upload_success = upload_to_oss(local_path, oss_path)

            if upload_success:
                own_oss_url = f"https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/{oss_path}"
                print(f"✅ [ENHANCE] 文件已上传到自己的OSS: {own_oss_url}")

                enhanced_result = {
                    'task_id': task_id,
                    'status': 'completed',
                    'result': local_filename,  # 返回本地文件名
                    'warehouse_path': local_filename,
                    'videoPath': local_filename,
                    'timestamp': end_time,
                    'started_at': start_time,
                    'completed_at': end_time,
                    'processing_time': processing_time,
                    'function_name': function_name,
                    'input_params': request.model_dump() if hasattr(request, 'model_dump') else {},
                    'tenant_id': tenant_id,
                    'business_id': business_id,
                    'oss_upload_success': True,
                    'oss_path': oss_path,
                    'oss_url': own_oss_url,  # 使用自己的OSS URL
                    'resource_id': 95,
                    'resource_create_success': False,
                    'task_update_success': True,
                    'cloud_integration': 'oss',
                    'content_type': 'image' if 'image' in function_name else 'video',
                    'upload_skipped': False,
                    'current_step': '已完成',
                    'progress': '100%',
                    'cloud_access_url': own_oss_url,  # 使用自己的OSS URL
                    'integration': 'oss',
                    'is_external_url': False,
                    'original_url': result,  # 保留原始阿里云URL作为参考
                    'aliyun_original_url': result
                }
            else:
                raise Exception("OSS上传失败")

        except Exception as e:
            print(f"❌ [ENHANCE] 处理阿里云OSS URL失败: {str(e)}")
            # 如果处理失败，降级使用原始URL
            enhanced_result = {
                'task_id': task_id,
                'status': 'completed',
                'result': result,
                'warehouse_path': None,
                'videoPath': None,
                'timestamp': end_time,
                'started_at': start_time,
                'completed_at': end_time,
                'processing_time': processing_time,
                'function_name': function_name,
                'input_params': request.model_dump() if hasattr(request, 'model_dump') else {},
                'tenant_id': tenant_id,
                'business_id': business_id,
                'oss_upload_success': False,
                'oss_path': None,
                'oss_url': result,  # 降级使用原始URL
                'resource_id': 95,
                'resource_create_success': False,
                'task_update_success': True,
                'cloud_integration': 'aliyun_direct',
                'content_type': 'image' if 'image' in function_name else 'video',
                'upload_skipped': False,
                'upload_error': str(e),
                'current_step': '已完成',
                'progress': '100%',
                'cloud_access_url': result,
                'integration': 'aliyun_oss',
                'is_external_url': True,
                'original_url': result
            }
    else:
        enhanced_result = {
            'task_id': task_id,
            'status': 'completed',
            'result': result,
            'warehouse_path': result if isinstance(result, str) and not is_external_url else None,
            'videoPath': result if isinstance(result, str) and not is_external_url else None,
            'timestamp': end_time,
            'started_at': start_time,
            'completed_at': end_time,
            'processing_time': processing_time,
            'function_name': function_name,
            'input_params': request.model_dump() if hasattr(request, 'model_dump') else {},
            'tenant_id': tenant_id,
            'business_id': business_id,
            'oss_upload_success': True,  # 模拟OSS成功
            'oss_path': f'agent/resource/{result}' if isinstance(result, str) and not is_external_url else None,
            'oss_url': result if is_external_url else f'https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/agent/resource/{result}' if isinstance(
                result, str) else None,
            'resource_id': 95,  # 模拟resource_id
            'resource_create_success': False,
            'task_update_success': True,
            'cloud_integration': 'oss',
            'content_type': 'file',
            'upload_skipped': False,
            'current_step': '已完成',
            'progress': '100%',
            'cloud_access_url': result if is_external_url else f'https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/agent/resource/{result}' if isinstance(
                result, str) else None,
            'integration': 'oss'
        }

    # 🔥 如果有文件系统路径，添加文件存在性检查
    if isinstance(result, str) and result:
        try:
            full_path = get_full_file_path(result)
            if full_path:
                enhanced_result['full_file_path'] = full_path
                enhanced_result['file_exists'] = verify_file_exists(result)
            else:
                enhanced_result['file_exists'] = False
        except Exception as e:
            print(f"⚠️ 检查文件存在性失败: {e}")
            enhanced_result['file_exists'] = False

    # 🔥 任务状态更新流程（开始状态0和完成状态1）
    if tenant_id:
        try:
            print(f"☁️ [STATUS-UPDATE] 开始状态更新流程")

            # 1. 更新开始状态 (0)
            api_type = "digital_human" if is_digital_human else "default"
            api_service.update_task_status(
                task_id=task_id,
                status="0",  # 开始
                tenant_id=tenant_id,
                business_id=business_id,
                api_type=api_type
            )
            print(f"✅ [STATUS-UPDATE] 开始状态更新成功")

            # 2. 模拟OSS上传
            if isinstance(result, str) and not is_aliyun_oss_url:
                # 只有当不是阿里云URL时才需要构建新的OSS URL
                oss_url = f'https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/agent/resource/{result}'
                oss_path = f'agent/resource/{result}'
                enhanced_result['oss_url'] = oss_url
                enhanced_result['oss_path'] = oss_path

            # 3. 更新完成状态 (1)
            try:
                update_success = api_service.update_task_status(
                    task_id=task_id,
                    status="1",  # 完成
                    tenant_id=tenant_id,
                    path=enhanced_result.get('oss_path', ''),
                    resource_id=95,
                    business_id=business_id,
                    api_type=api_type
                )
                enhanced_result['task_update_success'] = update_success
                print(f"✅ [STATUS-UPDATE] 完成状态更新: {'成功' if update_success else '失败'}")
            except Exception as e:
                print(f"❌ [STATUS-UPDATE] 完成状态更新失败: {str(e)}")
                enhanced_result['task_update_success'] = False

            print(f"✅ [STATUS-UPDATE] 完整流程完成")

        except Exception as e:
            print(f"❌ [STATUS-UPDATE] 完整流程失败: {str(e)}")

    return enhanced_result


# ========== Coze 视频生成接口 ==========

@app.post("/video/advertisement")  
async def video_advertisement(request: VideoAdvertisementRequest):
    """生成广告视频 - 重构版本使用统一包装器"""
    
    def advertisement_func(**kwargs):
        """广告视频生成业务逻辑"""
        return service.video_api.generate_advertisement(
            company_name=kwargs.get('company_name'),
            service=kwargs.get('service'),
            topic=kwargs.get('topic'),
            content=kwargs.get('content', ''),
            need_change=kwargs.get('need_change', False)
        )
    
    # 使用通用端点包装器
    wrapper = endpoint_handler.create_endpoint_wrapper(
        business_func=advertisement_func,
        function_name="generate_advertisement",
        async_func_name="get_video_advertisement",
        is_digital_human=False,
        response_type=APIConstants.RESPONSE_TYPE_VIDEO
    )
    
    return await wrapper(request)


@app.post("/video/advertisement-enhance")
async def video_advertisement_enhance(request: VideoAdvertisementEnhanceRequest):
    """生成增强广告视频 - 重构版本使用统一包装器"""
    
    def advertisement_enhance_func(**kwargs):
        """增强广告视频生成业务逻辑"""
        # 根据参数数量判断使用哪个API（保持原有逻辑）
        if len(kwargs) <= 4:
            return service.video_api.generate_advertisement(
                company_name=kwargs.get('company_name'),
                service=kwargs.get('service'),
                topic=kwargs.get('topic'),
                enhance=True
            )
        else:
            return service.video_api.generate_advertisement_enhance(
                company_name=kwargs.get('company_name'),
                service=kwargs.get('service'),
                topic=kwargs.get('topic'),
                content=kwargs.get('content'),
                need_change=kwargs.get('need_change'),
                add_digital_host=kwargs.get('add_digital_host'),
                use_temp_materials=kwargs.get('use_temp_materials'),
                clip_mode=kwargs.get('clip_mode'),
                upload_digital_host=kwargs.get('upload_digital_host'),
                moderator_source=kwargs.get('moderator_source'),
                enterprise_source=kwargs.get('enterprise_source')
            )
    
    # 使用通用端点包装器
    wrapper = endpoint_handler.create_endpoint_wrapper(
        business_func=advertisement_enhance_func,
        function_name="generate_advertisement_enhance",
        async_func_name="get_video_advertisement_enhance",
        is_digital_human=False,
        response_type=APIConstants.RESPONSE_TYPE_VIDEO
    )
    
    return await wrapper(request)


@app.post("/video/clicktype")
async def video_clicktype(request: ClickTypeRequest):
    """生成点击类视频 - 重构版本使用统一包装器"""
    
    def clicktype_func(**kwargs):
        """点击类视频生成业务逻辑"""
        return service.video_api.generate_clicktype(
            title=kwargs.get('title'),
            content=kwargs.get('content')
        )
    
    # 使用通用端点包装器
    wrapper = endpoint_handler.create_endpoint_wrapper(
        business_func=clicktype_func,
        function_name="generate_clicktype",
        async_func_name="get_video_clicktype",
        is_digital_human=False,
        response_type=APIConstants.RESPONSE_TYPE_VIDEO
    )
    
    return await wrapper(request)


@app.post("/video/digital-human-easy")
async def video_digital_human_easy(request: DigitalHumanEasyRequest):
    """生成数字人视频 - 重构版本使用统一包装器"""
    
    def digital_human_func(**kwargs):
        """数字人视频生成业务逻辑"""
        return service.video_api.generate_digital_human(
            video_input=kwargs.get('file_path'),  # 使用file_path作为video_input
            topic=kwargs.get('topic'),
            content=kwargs.get('content', ''),
            audio_input=kwargs.get('audio_url') or kwargs.get('audio_path')  # 兼容audio_url和audio_path
        )
    
    # 使用通用端点包装器 - 数字人专用接口
    wrapper = endpoint_handler.create_endpoint_wrapper(
        business_func=digital_human_func,
        function_name="generate_digital_human",
        async_func_name="get_video_digital_human",
        is_digital_human=True,  # 数字人专用
        response_type=APIConstants.RESPONSE_TYPE_VIDEO
    )
    
    return await wrapper(request)


@app.post("/video/clothes-different-scene")
async def video_clothes_different_scene(request: ClothesDifferentSceneRequest):
    """生成服装场景视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_clothes_scene(
                has_figure=request.has_figure,
                clothes_url=request.clothesurl,
                description=request.description,
                is_down=getattr(request, 'is_down', True)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_clothes_scene", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_clothes_scene"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "generate_clothes_scene", mode=mode)


@app.post("/video/big-word")
async def video_big_word(request: BigWordRequest):
    """生成大字报视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 🔥 添加调试信息
    print(f"🔍 [app_0715] 接收到的请求参数:")
    print(f"   request.company_name: {request.company_name}")
    print(f"   request.title: {request.title}")
    print(f"   request.product: {request.product}")
    print(f"   request.description: {request.description}")
    print(f"   request.content: {request.content}")

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_big_word(
                company_name=request.company_name,
                title=request.title,
                product=request.product,
                description=request.description,
                content=request.content
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_big_word", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_big_word"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    # 🔥 修复：传递正确的参数给 handle_async_endpoint
    return await handle_async_endpoint(
        request,
        process,
        "generate_big_word",
        mode=mode,
        company_name=request.company_name,
        title=request.title,
        product=request.product,
        description=request.description,
        content=request.content
    )


@app.post("/video/catmeme")
async def video_catmeme(request: CatMemeRequest):
    """生成猫咪表情包视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_catmeme(
                dialogue=request.title,  # Use title as dialogue
                author=request.author,
                content=getattr(request, 'content', None)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_catmeme", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_catmeme"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "generate_catmeme", mode=mode)


@app.post("/video/incitement")
async def video_incitement(request: IncitementRequest):
    """生成煽动类视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_incitement(
                theme=request.theme,
                intensity=getattr(request, 'intensity', 'medium'),
                target_audience=getattr(request, 'target_audience', 'general')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_incitement", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_incitement"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "generate_incitement", mode=mode)


@app.post("/video/sinology")
async def video_sinology(request: SinologyRequest):
    """生成国学类视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_sinology(
                classic=request.classic,
                interpretation=request.interpretation,
                background_style=getattr(request, 'background_style', 'traditional')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_sinology", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_sinology"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "generate_sinology", mode=mode)


@app.post("/video/stickman")
async def video_stickman(request: StickmanRequest):
    """生成火柴人视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    if mode == "sync":
        # 同步模式
        try:
            # 使用原始的 get_video_stickman 函数，它接收 author, title, content, lift_text 参数
            from core.cliptemplate.coze.video_stickman import get_video_stickman
            result = get_video_stickman(
                author=request.author,
                title=request.title,
                content=getattr(request, 'content', None),
                lift_text=getattr(request, 'lift_text', '科普动画')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_stickman", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_stickman"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 异步模式
        try:
            args = {
                "author": request.author,
                "title": request.title,
                "content": getattr(request, 'content', None),
                "lift_text": getattr(request, 'lift_text', '科普动画')
            }
            
            task_id = await task_manager.submit_task(
                func_name="get_video_stickman",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )
            
            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_stickman"}
            return format_response(error_res, mode="sync", error_type="general_exception")


@app.post("/video/smart-clip")
async def video_smart_clip(request: SmartClipRequest):
    """智能视频剪辑"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.get_smart_clip(
                video_path=request.video_path,
                target_duration=getattr(request, 'target_duration', 30)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "get_smart_clip", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "get_smart_clip"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "get_smart_clip", mode=mode)


@app.post("/video/clip")
async def video_clip(request: SmartClipRequest):
    """视频剪辑"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    if mode == "sync":
        # 同步模式 - 保持原有逻辑
        try:
            from core.clipgenerate.interface_function import get_smart_clip_video

            result = get_smart_clip_video(
                input_source=request.input_source,
                is_directory=getattr(request, 'is_directory', True),
                company_name=getattr(request, 'company_name', '测试公司'),
                text_list=getattr(request, 'text_list', None),
                audio_durations=getattr(request, 'audio_durations', None),
                clip_mode=getattr(request, 'clip_mode', 'random'),
                target_resolution=getattr(request, 'target_resolution', (1920, 1080))
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "get_smart_clip_video", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "get_smart_clip_video"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 异步模式 - 使用task_manager提交任务
        try:
            args = {
                "input_source": request.input_source,
                "is_directory": getattr(request, 'is_directory', True),
                "company_name": getattr(request, 'company_name', '测试公司'),
                "text_list": getattr(request, 'text_list', None),
                "audio_durations": getattr(request, 'audio_durations', None),
                "clip_mode": getattr(request, 'clip_mode', 'random'),
                "target_resolution": getattr(request, 'target_resolution', (1920, 1080))
            }

            task_id = await task_manager.submit_task(
                func_name="get_smart_clip_video",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )

            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "get_smart_clip_video"}
            return format_response(error_res, mode="sync", error_type="general_exception")


@app.post("/video/dgh-img-insert")
async def video_dgh_img_insert(request: DGHImgInsertRequest):
    """数字人图片插入视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.dgh_img_insert(
                video_url=request.video_file_path,
                title=request.title,
                content=request.content,
                need_change=request.need_change,
                add_subtitle=getattr(request, 'add_subtitle', True),  # 🔥 新增字幕控制参数
                insert_image=getattr(request, 'insert_image', True)  # 🔥 新增图片插入控制参数
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "dgh_img_insert", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "dgh_img_insert"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    # 🔥 修复：传递正确的参数给 handle_async_endpoint，就像 big-word 端点一样
    return await handle_async_endpoint(
        request,
        process,
        "dgh_img_insert",
        mode=mode,
        video_url=request.video_file_path,
        title=request.title,
        content=request.content,
        need_change=request.need_change
    )


@app.post("/video/digital-human-clips")
async def video_digital_human_clips(request: DigitalHumanClipsRequest):
    """生成数字人剪辑视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.digital_human_clips(
                clips=request.clips,
                transition=getattr(request, 'transition', 'fade')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "digital_human_clips", request, is_digital_human=True)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "digital_human_clips"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "digital_human_clips", mode=mode)


@app.post("/video/ai-avatar")
async def video_ai_avatar_unified(request: AIAvatarUnifiedRequest):
    """AI分身统一接口 - 统一使用dgh_img_insert函数，通过参数控制功能"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            # 🔥 音频处理逻辑：如果提供audio_url就使用，否则使用video_url中的音频
            print(f"🎵 [video_ai_avatar_unified] 音频处理逻辑:")
            print(f"   audio_url: {request.audio_url}")
            print(f"   video_url: {request.video_url}")
            
            if request.audio_url:
                print(f"   策略: 使用提供的audio_url音频")
                audio_strategy = "use_provided_audio"
            else:
                print(f"   策略: 使用video_url中的原始音频")
                audio_strategy = "use_video_audio"
            
            # 统一使用 dgh_img_insert 函数，不再区分 basic 和 enhance
            # 通过 add_subtitle 和 insert_image 参数来控制功能
            result = get_video_dgh_img_insert(
                title=request.title,
                video_file_path=request.video_url,
                content=request.content,
                need_change=request.need_change or False,
                add_subtitle=request.add_subtitle if request.add_subtitle is not None else True,
                insert_image=request.insert_image if request.insert_image is not None else True,
                audio_url=request.audio_url  # 🔥 传递音频URL
            )

            # 使用统一的结果处理
            return enhance_endpoint_result(result, "dgh_img_insert", request, is_digital_human=False)

        except Exception as e:
            error_res = {"error": str(e), "function_name": "dgh_img_insert"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    # 统一的异步处理
    return await handle_async_endpoint(
        request,
        process,
        "dgh_img_insert",
        mode=mode,
        video_url=request.video_url,
        title=request.title,
        content=request.content,
        need_change=request.need_change,
        add_subtitle=request.add_subtitle,
        insert_image=request.insert_image,
        audio_url=request.audio_url  # 🔥 统一使用audio_url参数
    )


@app.post("/video/clothes-fast-change")
async def video_clothes_fast_change(request: ClothesFastChangeRequest):
    """生成服装快速换装视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.clothes_fast_change(
                model_image=request.model_image,
                clothes_list=request.clothes_list,
                change_speed=getattr(request, 'change_speed', 'normal')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "clothes_fast_change", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "clothes_fast_change"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "clothes_fast_change", mode=mode)


@app.post("/video/random")
async def video_random(request: VideoRandomRequest):
    """生成随机视频"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.generate_random_video(
                category=request.category,
                duration=getattr(request, 'duration', 30)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "generate_random_video", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_random_video"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "generate_random_video", mode=mode)


@app.post("/video/digital-human-generation")
async def video_digital_human_generation(request: DigitalHumanRequest):
    """生成数字人视频 - 一生十特殊接口"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    if mode == "sync":
        # 同步模式
        try:
            result = process_single_video_by_url(
                video_url=request.video_url,
                tenant_id=request.tenant_id,
                id=request.id,
                preserve_duration=True  # 保持原始视频时长
            )
            # 🔥 使用增强函数处理结果（数字人专用接口）
            return enhance_endpoint_result(result, "process_single_video_by_url", request, is_digital_human=True)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "process_single_video_by_url"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 异步模式 - 使用数字人专用的状态更新接口
        try:
            args = {
                "video_url": request.video_url,
                "tenant_id": request.tenant_id,
                "id": request.id,
                "preserve_duration": True  # 保持原始视频时长
            }

            task_id = await task_manager.submit_task(
                func_name="process_single_video_by_url",
                args=args
            )

            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "process_single_video_by_url"}
            return format_response(error_res, mode="sync", error_type="general_exception")


@app.post("/video/edit")
async def video_edit(request: VideoEditMainRequest):
    """视频编辑"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    if mode == "sync":
        # 同步模式
        try:
            result = get_video_edit_simple(
                video_sources=request.video_sources,
                duration=getattr(request, 'duration', 30),
                style=getattr(request, 'style', '抖音风'),
                purpose=getattr(request, 'purpose', '社交媒体'),
                use_local_ai=getattr(request, 'use_local_ai', True),
                api_key=getattr(request, 'api_key', None)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "get_video_edit_simple", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "get_video_edit_simple"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 异步模式
        try:
            args = {
                "video_sources": request.video_sources,
                "duration": getattr(request, 'duration', 30),
                "style": getattr(request, 'style', '抖音风'),
                "purpose": getattr(request, 'purpose', '社交媒体'),
                "use_local_ai": getattr(request, 'use_local_ai', True),
                "api_key": getattr(request, 'api_key', None)
            }

            task_id = await task_manager.submit_task(
                func_name="get_video_edit_simple",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )

            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "get_video_edit_simple"}
            return format_response(error_res, mode="sync", error_type="general_exception")


@app.post("/video/highlights-extract")
async def video_highlights_extract(request: VideoHighlightsRequest):
    """从直播数据中提取视频精彩片段"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式
    
    if mode == "sync":
        # 同步模式
        try:
            result = extract_video_highlights_from_url(
                excel_url=request.excel_url,
                video_url=request.video_url,
                metrics=request.metrics,
                top_n=request.top_n,
                upload_to_oss_flag=request.upload_to_oss
            )
            
            # 根据结果状态返回不同的响应
            if result.get("status") == "success":
                return JSONResponse(
                    status_code=200,
                    content={
                        "code": 200,
                        "message": result.get("message", "视频处理成功"),
                        "data": {
                            "video_url": result.get("oss_url", result.get("output_file")),
                            "output_file": result.get("output_file")
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "code": 500,
                        "message": result.get("message", "视频处理失败"),
                        "error": result.get("message")
                    }
                )
                
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": f"处理失败: {str(e)}",
                    "error": str(e)
                }
            )
    else:
        # 异步模式
        try:
            args = {
                "excel_url": request.excel_url,
                "video_url": request.video_url,
                "metrics": request.metrics,
                "top_n": request.top_n,
                "upload_to_oss_flag": request.upload_to_oss
            }
            
            task_id = await task_manager.submit_task(
                func_name="extract_video_highlights_from_url",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )
            
            return format_response(task_id, mode="async", urlpath=urlpath)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "message": f"提交任务失败: {str(e)}",
                    "error": str(e)
                }
            )


@app.post("/video/highlight-clip")
async def video_highlight_clip(request: VideoHighlightClipRequest):
    """基于Excel观看数据的视频高光剪辑 - 仅支持异步模式"""
    # 强制使用异步模式
    try:
        args = {
            "video_source": request.video_source,
            "excel_source": request.excel_source,
            "target_duration": request.target_duration,
            "output_path": request.output_path
        }
        
        task_id = await task_manager.submit_task(
            func_name="process_video_highlight_clip",
            args=args,
            tenant_id=getattr(request, 'tenant_id', None),
            business_id=getattr(request, 'id', None)
        )
        
        return format_response(task_id, mode="async", urlpath=urlpath)
    except Exception as e:
        error_res = {"error": str(e), "function_name": "process_video_highlight_clip"}
        return format_response(error_res, mode="sync", error_type="general_exception")


# ========== Tongyi Wanxiang 文生图接口 ==========

@app.post("/wanxiang/text-to-image-v2")
async def wanxiang_text_to_image_v2(request: TextToImageV2Request):
    """通义万相文生图V2"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.text_to_image_v2(
                prompt=request.prompt,
                style=getattr(request, 'style', 'default'),
                size=getattr(request, 'size', '1024*1024')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "text_to_image_v2", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "text_to_image_v2"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "text_to_image_v2", mode=mode)


@app.post("/wanxiang/text-to-image-v1")
async def wanxiang_text_to_image_v1(request: TextToImageV1Request):
    """通义万相文生图V1"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.text_to_image_v1(
                prompt=request.prompt,
                style=getattr(request, 'style', 'default')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "text_to_image_v1", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "text_to_image_v1"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "text_to_image_v1", mode=mode)


# ========== Tongyi Wanxiang 图像编辑接口 ==========

@app.post("/wanxiang/image-edit")
async def wanxiang_image_background_edit(request: ImageBackgroundEditRequest):
    """图像背景编辑"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.image_background_edit(
                image_url=request.image_url,
                background_prompt=request.background_prompt
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "image_background_edit", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "image_background_edit"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "image_background_edit", mode=mode)


# ========== Tongyi Wanxiang 虚拟模特接口 ==========

@app.post("/wanxiang/virtual-model-v1")
async def wanxiang_virtual_model_v1(request: VirtualModelV1Request):
    """虚拟模特V1"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.virtual_model_v1(
                base_image_url=request.base_image_url,
                prompt=request.prompt,
                mask_image_url=getattr(request, 'mask_image_url', None),
                face_prompt=getattr(request, 'face_prompt', None),
                background_image_url=getattr(request, 'background_image_url', None),
                short_side_size=getattr(request, 'short_side_size', '1024'),
                n=getattr(request, 'n', 1)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "virtual_model_v1", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "virtual_model_v1"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "virtual_model_v1", mode=mode)


@app.post("/wanxiang/virtual-model-v2")
async def wanxiang_virtual_model_v2(request: VirtualModelV2Request):
    """虚拟模特V2"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.virtual_model_v2(
                base_image_url=request.base_image_url,
                prompt=request.prompt,
                mask_image_url=getattr(request, 'mask_image_url', None),
                face_prompt=getattr(request, 'face_prompt', None),
                background_image_url=getattr(request, 'background_image_url', None),
                short_side_size=getattr(request, 'short_side_size', '1024'),
                n=getattr(request, 'n', 1)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "virtual_model_v2", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "virtual_model_v2"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "virtual_model_v2", mode=mode)


@app.post("/wanxiang/shoe-model")
async def wanxiang_shoe_model(request: ShoeModelRequest):
    """鞋靴模特"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.shoe_model(
                template_image_url=request.template_image_url,
                shoe_image_url=request.shoe_image_url
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "shoe_model", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "shoe_model"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "shoe_model", mode=mode)


@app.post("/wanxiang/creative-poster")
async def wanxiang_creative_poster(request: CreativePosterRequest):
    """创意海报生成"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.creative_poster(
                title=request.title,
                sub_title=getattr(request, 'sub_title', None),
                body_text=getattr(request, 'body_text', None),
                prompt_text_zh=getattr(request, 'prompt_text_zh', None)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "creative_poster", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "creative_poster"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "creative_poster", mode=mode)


@app.post("/wanxiang/background-generation")
async def wanxiang_background_generation(request: BackgroundGenerationRequest):
    """背景生成"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.background_generation(
                base_image_url=request.base_image_url,
                background_prompt=request.ref_prompt
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "background_generation", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "background_generation"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "background_generation", mode=mode)


# ========== Tongyi Wanxiang AI试衣接口 ==========

@app.post("/wanxiang/ai-tryon-basic")
async def wanxiang_ai_tryon_basic(request: AITryonBasicRequest):
    """AI试衣基础版"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.ai_tryon_basic(
                person_image_url=request.person_image_url,
                top_garment_url=getattr(request, 'top_garment_url', None),
                bottom_garment_url=getattr(request, 'bottom_garment_url', None),
                resolution=getattr(request, 'resolution', -1),
                restore_face=getattr(request, 'restore_face', True)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "ai_tryon_basic", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "ai_tryon_basic"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "ai_tryon_basic", mode=mode)


@app.post("/wanxiang/ai-tryon-plus")
async def wanxiang_ai_tryon_plus(request: AITryonPlusRequest):
    """AI试衣Plus版"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.ai_tryon_plus(
                person_image_url=request.person_image_url,
                top_garment_url=getattr(request, 'top_garment_url', None),
                bottom_garment_url=getattr(request, 'bottom_garment_url', None),
                resolution=getattr(request, 'resolution', -1),
                restore_face=getattr(request, 'restore_face', True)
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "ai_tryon_plus", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "ai_tryon_plus"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "ai_tryon_plus", mode=mode)


@app.post("/wanxiang/ai-tryon-enhance")
async def wanxiang_ai_tryon_enhance(request: AITryonEnhanceRequest):
    """AI试衣图片精修"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.ai_tryon_enhance(
                person_image_url=request.person_image_url,
                top_garment_url=request.top_garment_url,
                bottom_garment_url=request.bottom_garment_url,
                gender=getattr(request, 'gender', 'woman')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "ai_tryon_enhance", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "ai_tryon_enhance"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "ai_tryon_enhance", mode=mode)


@app.post("/wanxiang/ai-tryon-segment")
async def wanxiang_ai_tryon_segment(request: AITryonSegmentRequest):
    """AI试衣图片分割"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.ai_tryon_segment(
                image_url=request.image_url,
                clothes_type=request.clothes_type
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "ai_tryon_segment", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "ai_tryon_segment"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "ai_tryon_segment", mode=mode)


# ========== Tongyi Wanxiang 视频生成接口 ==========

@app.post("/wanxiang/image-to-video-advanced")
async def wanxiang_image_to_video_advanced(request: ImageToVideoAdvancedRequest):
    """图生视频高级版"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.image_to_video_advanced(
                first_frame_url=request.first_frame_url,
                last_frame_url=request.last_frame_url,
                prompt=request.prompt,
                duration=getattr(request, 'duration', 5),
                size=getattr(request, 'size', '1280*720')
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "image_to_video_advanced", request, is_digital_human=False)

        except Exception as e:
            print(f"❌ [API] 处理失败: {str(e)}")
            error_res = {"error": str(e), "function_name": "image_to_video_advanced"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "image_to_video_advanced", mode=mode)


# ========== Tongyi Wanxiang 数字人视频接口 ==========

@app.post("/wanxiang/animate-anyone")
async def wanxiang_animate_anyone(request: AnimateAnyoneRequest):
    """舞动人像 AnimateAnyone"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.animate_anyone(
                image_url=request.image_url,
                dance_video_url=request.dance_video_url
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "animate_anyone", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "animate_anyone"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "animate_anyone", mode=mode)


@app.post("/wanxiang/emo-video")
async def wanxiang_emo_video(request: EMOVideoRequest):
    """悦动人像EMO"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.emo_video(
                image_url=request.image_url,
                audio_url=request.audio_url
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "emo_video", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "emo_video"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "emo_video", mode=mode)


@app.post("/wanxiang/live-portrait")
async def wanxiang_live_portrait(request: LivePortraitRequest):
    """灵动人像 LivePortrait"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.live_portrait(
                image_url=request.image_url,
                audio_url=request.audio_url
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "live_portrait", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "live_portrait"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "live_portrait", mode=mode)


# ========== Tongyi Wanxiang 视频风格重绘接口 ==========

@app.post("/wanxiang/video-style-transfer")
async def wanxiang_video_style_transfer(request: VideoStyleTransferRequest):
    """视频风格重绘"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式

    # 定义实际处理逻辑
    async def process():
        try:
            result = service.video_api.video_style_transfer(
                video_url=request.video_url,
                style=request.style
            )
            # 🔥 使用增强函数处理结果
            return enhance_endpoint_result(result, "video_style_transfer", request, is_digital_human=False)
        except Exception as e:
            error_res = {"error": str(e), "function_name": "video_style_transfer"}
            return format_response(error_res, mode="sync", error_type="general_exception")

    return await handle_async_endpoint(request, process, "video_style_transfer", mode=mode)


# ========== 通用接口 ==========

@app.get("/")
async def root():
    """根路径 - 显示所有可用接口"""
    return {
        "message": "🚀 AI视频生成统一API系统",
        "version": "2.0.0",
        "total_endpoints": 31,
        "categories": {
            "🎬 Coze视频生成": [
                "/video/advertisement",
                "/video/advertisement-enhance",
                "/video/clicktype",
                "/video/digital-human-easy",
                "/video/clothes-different-scene",
                "/video/big-word",
                "/video/catmeme",
                "/video/incitement",
                "/video/sinology",
                "/video/stickman",
                "/video/smart-clip",
                "/video/clip",
                "/video/dgh-img-insert",
                "/video/digital-human-clips",
                "/video/clothes-fast-change",
                "/video/random",
                "/video/digital-human-generation",
                "/video/edit"
            ],
            "🎨 通义万相文生图": [
                "/wanxiang/text-to-image-v2",
                "/wanxiang/text-to-image-v1"
            ],
            "🖼️ 通义万相图像编辑": [
                "/wanxiang/image-edit"
            ],
            "👗 通义万相虚拟模特": [
                "/wanxiang/virtual-model-v1",
                "/wanxiang/virtual-model-v2",
                "/wanxiang/shoe-model",
                "/wanxiang/creative-poster",
                "/wanxiang/background-generation"
            ],
            "🧥 通义万相AI试衣": [
                "/wanxiang/ai-tryon-basic",
                "/wanxiang/ai-tryon-plus",
                "/wanxiang/ai-tryon-enhance",
                "/wanxiang/ai-tryon-segment"
            ],
            "🎥 通义万相视频生成": [
                "/wanxiang/image-to-video-advanced"
            ],
            "🤖 通义万相数字人视频": [
                "/wanxiang/animate-anyone",
                "/wanxiang/emo-video",
                "/wanxiang/live-portrait"
            ],
            "🎬 通义万相视频风格重绘": [
                "/wanxiang/video-style-transfer"
            ]
        },
        "utility_endpoints": [
            "/api/video/types",
            "/health",
            "/docs"
        ],
        "documentation": "/docs"
    }


@app.get("/api/video/types")
async def get_supported_video_types():
    """获取支持的视频类型"""
    return {
        "supported_functions": service.video_api.get_all_supported_functions(),
        "status": "success"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Video Generation API",
        "version": "2.0.0",
        "endpoints_count": 31
    }


# ========== 任务状态查询接口 ==========

@app.get("/get-result/{task_id}")
async def get_task_result(task_id: str, remove: bool = Query(False, description="是否移除结果")):
    """获取任务结果"""
    result = task_manager.get_result(task_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    # 如果任务还在处理中，返回当前状态
    if result.get("status") in ["submitted", "processing"]:
        return {
            "status": result.get("status"),
            "task_id": task_id,
            "progress": result.get("progress", "0%"),
            "current_step": result.get("current_step", ""),
            "message": "任务正在处理中",
            "submitted_at": result.get("submitted_at"),
            "started_at": result.get("started_at")
        }

    # 如果任务已完成，返回结果
    if result.get("status") == "completed":
        # 提取结果并格式化
        task_result = result.get("result", {})
        function_name = result.get("function_name", "")

        # 🔥 修复：根据任务类型决定是否提取warehouse路径
        warehouse_path = None
        video_url = None

        if function_name == "get_copy_generation":
            # 文案生成任务：直接返回文本结果，不提取路径
            print(f"📝 [TEXT-RESULT] 文案生成任务，返回文本结果: {task_result}")
        else:
            # 视频生成任务：提取warehouse路径
            warehouse_path = extract_warehouse_path(task_result)
            video_url = f"{urlpath}{warehouse_path}" if warehouse_path else None
            print(f"🎬 [VIDEO-RESULT] 视频生成任务，提取路径: {warehouse_path}")

        response = {
            "status": "completed",
            "task_id": task_id,
            "result": task_result,
            "warehouse_path": warehouse_path,
            "video_url": video_url,
            "processing_time": result.get("processing_time"),
            "function_name": function_name,
            "completed_at": result.get("completed_at"),
            "tenant_id": result.get("tenant_id"),
            "business_id": result.get("business_id")
        }

        # 如果请求删除结果，则删除
        if remove:
            with task_manager.result_condition:
                if task_id in task_manager.results:
                    del task_manager.results[task_id]

        return response

    # 如果任务失败
    if result.get("status") == "failed":
        return {
            "status": "failed",
            "task_id": task_id,
            "error": result.get("error", "任务执行失败"),
            "failed_at": result.get("failed_at"),
            "processing_time": result.get("processing_time"),
            "function_name": result.get("function_name")
        }

    # 默认返回
    return result


@app.get("/poll-result/{task_id}")
async def poll_task_result(task_id: str, timeout: int = Query(30, description="轮询超时时间（秒）")):
    """轮询任务结果（长轮询）"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = task_manager.get_result(task_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        # 如果任务已完成或失败，立即返回
        if result.get("status") in ["completed", "failed"]:
            return await get_task_result(task_id)

        # 等待一小段时间再检查
        await asyncio.sleep(0.5)

    # 超时后返回当前状态
    result = task_manager.get_result(task_id)
    if result:
        return {
            "status": result.get("status", "processing"),
            "task_id": task_id,
            "progress": result.get("progress", "0%"),
            "current_step": result.get("current_step", ""),
            "message": "轮询超时，任务仍在处理中",
            "timeout": True
        }
    else:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态（简单状态查询）"""
    result = task_manager.get_result(task_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    return {
        "task_id": task_id,
        "status": result.get("status"),
        "progress": result.get("progress", "0%"),
        "current_step": result.get("current_step", ""),
        "submitted_at": result.get("submitted_at"),
        "started_at": result.get("started_at"),
        "completed_at": result.get("completed_at"),
        "failed_at": result.get("failed_at"),
        "processing_time": result.get("processing_time"),
        "function_name": result.get("function_name")
    }


@app.get("/tasks")
async def list_all_tasks(status: Optional[str] = Query(None, description="筛选任务状态")):
    """列出所有任务"""
    all_tasks = task_manager.get_all_results()

    # 如果指定了状态筛选
    if status:
        filtered_tasks = {
            task_id: task_info
            for task_id, task_info in all_tasks.items()
            if task_info.get("status") == status
        }
        return {
            "total": len(filtered_tasks),
            "status_filter": status,
            "tasks": filtered_tasks
        }

    # 返回所有任务
    return {
        "total": len(all_tasks),
        "tasks": all_tasks
    }


# ========== 配置管理接口 ==========

@app.post('/api/product')
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


@app.post('/api/voice/live_config')
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

        # 更新配置
        success = config_manager.update_voice_config(updates)

        if success:
            # 🔥 如果有tenant_id，更新任务状态为完成
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            return {
                "code": 200,
                "message": "语音配置更新成功",
                "data": config_manager.voice_info,
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


# @app.post('/api/server/start')
# async def start_socket_server(
#         req: ServerStartRequest,
#         tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
# ):
#     """启动WebSocket客户端连接 - 支持任务状态更新"""
#     try:
#         tenant_id = req.tenant_id or tenant_id_query
#         task_id = str(uuid.uuid4())
#         business_id = req.id
#
#         print(f"🎯 [启动WebSocket客户端] 处理请求:")
#         print(f"   Task ID: {task_id}")
#         print(f"   Tenant ID: {tenant_id}")
#         print(f"   Business ID: {business_id}")
#
#         # 🔥 如果有tenant_id，立即更新任务状态为运行中
#         if tenant_id:
#             api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)
#
#         global websocket_client
#
#         # Check if client is already connected
#         if websocket_client and websocket_client.is_connected():
#             if tenant_id:
#                 api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
#             raise HTTPException(
#                 status_code=400,
#                 detail={
#                     "status": "error",
#                     "message": "WebSocket客户端已经连接中",
#                     "task_id": task_id,
#                     "tenant_id": tenant_id,
#                     "business_id": business_id
#                 }
#             )
#
#         # Create and start WebSocket client with AI message processing
#         # 可配置的回复概率和队列大小
#         reply_probability = 0.2  # 20%回复概率，避免过于频繁
#         max_queue_size = 8  # 更大的队列支持更多消息积累
#         websocket_client = WebSocketClient(
#             host=req.host,
#             port=req.port,
#             reply_probability=reply_probability,
#             max_queue_size=max_queue_size
#         )
#
#         # 连接到WebSocket服务器
#         success = await websocket_client.connect()
#
#         if success:
#             # 🔥 如果有tenant_id，更新任务状态为完成
#             if tenant_id:
#                 api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)
#
#             return {
#                 "code": 200,
#                 "message": f"WebSocket客户端连接成功 - ws://{req.host}:{req.port}",
#                 "data": {
#                     "host": req.host,
#                     "port": req.port,
#                     "status": "connected",
#                     "connection_type": "websocket_client"
#                 },
#                 "task_id": task_id,
#                 "tenant_id": tenant_id,
#                 "business_id": business_id
#             }
#         else:
#             if tenant_id:
#                 api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
#             raise HTTPException(
#                 status_code=500,
#                 detail={
#                     "status": "error",
#                     "message": f"WebSocket客户端连接失败 - ws://{req.host}:{req.port}",
#                     "task_id": task_id,
#                     "tenant_id": tenant_id,
#                     "business_id": business_id
#                 }
#             )
#
#     except Exception as e:
#         # 🔥 异常时更新任务状态为失败
#         if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
#             try:
#                 api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
#             except Exception as status_error:
#                 print(f"⚠️ 更新失败状态时出错: {status_error}")
#
#         raise HTTPException(status_code=500, detail=f"启动WebSocket客户端失败: {str(e)}")
#
# @app.post('/api/server/stop')
# async def stop_socket_server(
#         req: ServerStopRequest = ServerStopRequest(),
#         tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
# ):
#     """停止WebSocket客户端连接 - 支持任务状态更新"""
#     try:
#         tenant_id = req.tenant_id or tenant_id_query
#         task_id = str(uuid.uuid4())
#         business_id = req.id
#
#         print(f"🎯 [停止WebSocket客户端] 处理请求:")
#         print(f"   Task ID: {task_id}")
#         print(f"   Tenant ID: {tenant_id}")
#         print(f"   Business ID: {business_id}")
#
#         # 🔥 如果有tenant_id，立即更新任务状态为运行中
#         if tenant_id:
#             api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)
#
#         global websocket_client
#         if websocket_client is not None and websocket_client.is_connected():
#             # 关闭WebSocket客户端连接
#             success = await websocket_client.close()
#             websocket_client = None
#
#             if success:
#                 # 🔥 如果有tenant_id，更新任务状态为完成
#                 if tenant_id:
#                     api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)
#                 return {
#                     "code": 200,
#                     "message": "WebSocket客户端断开成功",
#                     "data": {
#                         "status": "disconnected",
#                         "connection_type": "websocket_client"
#                     },
#                     "task_id": task_id,
#                     "tenant_id": tenant_id,
#                     "business_id": business_id
#                 }
#             else:
#                 # 🔥 如果有tenant_id，更新任务状态为失败
#                 if tenant_id:
#                     api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)
#                 raise HTTPException(
#                     status_code=500,
#                     detail={
#                         "status": "error",
#                         "message": "WebSocket客户端断开失败",
#                         "task_id": task_id,
#                         "tenant_id": tenant_id,
#                         "business_id": business_id
#                     }
#                 )
#         else:
#             if tenant_id:
#                 api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)
#
#             return {
#                 "code": 200,
#                 "message": "WebSocket客户端已经断开",
#                 "data": {
#                     "status": "already_disconnected",
#                     "connection_type": "websocket_client"
#                 },
#                 "task_id": task_id,
#                 "tenant_id": tenant_id,
#                 "business_id": business_id
#             }
#
#     except Exception as e:
#         # 🔥 异常时更新任务状态为失败
#         if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
#             try:
#                 api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
#             except Exception as status_error:
#                 print(f"⚠️ 更新失败状态时出错: {status_error}")
#
#         raise HTTPException(status_code=500, detail=f"停止WebSocket客户端失败: {str(e)}")

# ========== 自动产品介绍接口 ==========

@app.post('/api/server/start')
async def start_socket_server(
        req: AutoIntroStartRequest,
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
):
    """启动自动产品介绍WebSocket客户端 - 支持任务状态更新"""
    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [启动自动产品介绍客户端] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")
        print(f"   Host: {req.host}")
        print(f"   Port: {req.port}")
        print(f"   无消息超时: {req.no_message_timeout}秒")
        print(f"   介绍间隔: {req.auto_introduce_interval}秒")
        print(f"   声音克隆: {'启用' if req.use_voice_cloning else '禁用'}")  # 🔥 新增日志
        print(f"   自动重连: {'启用' if req.auto_reconnect else '禁用'}")
        if req.auto_reconnect:
            print(f"   最大重连次数: {req.max_reconnect_attempts}")
            print(f"   重连延迟: {req.reconnect_delay}秒")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        global auto_intro_client

        # 如果已有客户端在运行，先关闭它
        if auto_intro_client is not None:
            try:
                await auto_intro_client.close()
                print("🔄 关闭现有自动产品介绍客户端")
            except Exception as close_error:
                print(f"⚠️ 关闭现有客户端时出错: {close_error}")

        # 创建新的客户端
        auto_intro_client = WebSocketClient(
            host=req.host,
            port=req.port,
            reply_probability=req.reply_probability,
            max_queue_size=req.max_queue_size,
            use_voice_cloning=req.use_voice_cloning,  # 🔥 新增：传递声音克隆配置
            reply_interval=20  # 🔥 新增：设置回复间隔20秒
        )

        # 设置降级策略参数
        auto_intro_client.no_message_timeout = req.no_message_timeout
        auto_intro_client.auto_introduce_interval = req.auto_introduce_interval

        # 设置重连参数
        auto_intro_client.auto_reconnect = req.auto_reconnect
        auto_intro_client.max_reconnect_attempts = req.max_reconnect_attempts
        auto_intro_client.reconnect_delay = req.reconnect_delay

        # 连接WebSocket服务器
        connection_success = await auto_intro_client.connect()

        if connection_success:
            # 🔥 更新任务状态为成功
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            return {
                "code": 200,
                "message": "自动产品介绍客户端启动成功",
                "data": {
                    "status": "connected",
                    "host": req.host,
                    "port": req.port,
                    "no_message_timeout": req.no_message_timeout,
                    "auto_introduce_interval": req.auto_introduce_interval,
                    "reply_probability": req.reply_probability,
                    "max_queue_size": req.max_queue_size,
                    "auto_reconnect": req.auto_reconnect,
                    "max_reconnect_attempts": req.max_reconnect_attempts,
                    "reconnect_delay": req.reconnect_delay
                },
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id
            }
        else:
            # 🔥 连接失败，更新任务状态为失败
            if tenant_id:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)

            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"连接WebSocket服务器失败",
                    "host": req.host,
                    "port": req.port,
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                }
            )

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"❌ 更新任务状态失败: {status_error}")

        print(f"❌ 启动自动产品介绍客户端失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动自动产品介绍客户端失败: {str(e)}")


@app.post('/api/server/stop')
async def stop_socket_server(
        req: AutoIntroStopRequest = AutoIntroStopRequest(),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id")
):
    """停止自动产品介绍WebSocket客户端 - 支持任务状态更新"""
    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [停止自动产品介绍客户端] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        global auto_intro_client

        if auto_intro_client is not None:
            try:
                await auto_intro_client.close()
                auto_intro_client = None
                print("✅ 自动产品介绍客户端已关闭")

                # 🔥 更新任务状态为成功
                if tenant_id:
                    api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

                return {
                    "code": 200,
                    "message": "自动产品介绍客户端已停止",
                    "data": {
                        "status": "disconnected",
                        "connection_type": "auto_intro_client"
                    },
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                }
            except Exception as close_error:
                # 🔥 关闭失败，更新任务状态为失败
                if tenant_id:
                    api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)

                print(f"❌ 关闭自动产品介绍客户端失败: {close_error}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "自动产品介绍客户端断开失败",
                        "task_id": task_id,
                        "tenant_id": tenant_id,
                        "business_id": business_id
                    }
                )
        else:
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            return {
                "code": 200,
                "message": "自动产品介绍客户端已经停止",
                "data": {
                    "status": "already_disconnected",
                    "connection_type": "auto_intro_client"
                },
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id
            }

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"❌ 更新任务状态失败: {status_error}")

        print(f"❌ 停止自动产品介绍客户端失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止自动产品介绍客户端失败: {str(e)}")


@app.get('/api/auto-intro/status')
async def get_auto_intro_status():
    """获取自动产品介绍客户端状态"""
    global auto_intro_client

    if auto_intro_client is not None:
        is_connected = auto_intro_client.is_connected()
        return {
            "code": 200,
            "message": "获取状态成功",
            "data": {
                "status": "connected" if is_connected else "disconnected",
                "is_running": auto_intro_client.running if hasattr(auto_intro_client, 'running') else False,
                "host": auto_intro_client.host,
                "port": auto_intro_client.port,
                "no_message_timeout": auto_intro_client.no_message_timeout,
                "auto_introduce_interval": auto_intro_client.auto_introduce_interval,
                "reply_probability": auto_intro_client.reply_probability,
                "max_queue_size": auto_intro_client.max_queue_size,
                "auto_reconnect": auto_intro_client.auto_reconnect if hasattr(auto_intro_client,
                                                                              'auto_reconnect') else True,
                "max_reconnect_attempts": auto_intro_client.max_reconnect_attempts if hasattr(auto_intro_client,
                                                                                              'max_reconnect_attempts') else 10,
                "reconnect_delay": auto_intro_client.reconnect_delay if hasattr(auto_intro_client,
                                                                                'reconnect_delay') else 5,
                "last_message_time": auto_intro_client.last_message_time if hasattr(auto_intro_client,
                                                                                    'last_message_time') else None,
                "last_auto_introduce_time": auto_intro_client.last_auto_introduce_time if hasattr(auto_intro_client,
                                                                                                  'last_auto_introduce_time') else None
            }
        }
    else:
        return {
            "code": 200,
            "message": "获取状态成功",
            "data": {
                "status": "not_created",
                "is_running": False,
                "message": "自动产品介绍客户端尚未创建"
            }
        }


# ========== 文案和分析接口 ==========

@app.post("/text/industry")
async def api_get_text_industry(
        req: TextIndustryRequest,
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """行业文案生成 - 使用qwen-max直接生成"""
    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = req.task_id or task_id_query or str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [行业文案] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        # 使用qwen-max直接生成
        from core.text_generate.industry_text_generator import generate_industry_text
        
        result = generate_industry_text(
            industry=req.industry,
            is_hot=req.is_hot,
            content=req.content,
            category_id=req.categoryId
        )
        
        # 🔥 根据结果更新任务状态
        if tenant_id:
            if result['success']:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)
            else:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=business_id)

        # 格式化响应 - 使用统一的format_response
        if result['success']:
            # 构建用于format_response的结果
            formatted_result = {
                "content_type": "text",
                "text_content": result['content'],
                "result": {
                    "industry": result['industry'],
                    "content": result['content'],
                    "source": result.get('source', 'ai_generated'),
                    "model": result.get('model', 'qwen-max')
                },
                "upload_skipped": True,
                "skip_reason": "文本类接口无需上传",
                "function_name": "industry_text_generation",
                "processing_time": 0,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "task_update_success": True
            }
            
            # 添加警告信息（如果有）
            if 'warning' in result:
                formatted_result['warning'] = result['warning']
            
            return format_response(formatted_result, mode="sync", urlpath="")
        else:
            raise Exception(result.get('error', '未知错误'))

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        
        # 使用统一的错误格式
        error_result = {
            "error": f"行业文案生成失败: {str(e)}",
            "message": "文案生成处理失败",
            "task_id": locals().get('task_id'),
            "tenant_id": locals().get('tenant_id'),
            "business_id": locals().get('business_id')
        }
        return format_response(error_result, error_type="general_exception")


@app.post("/copy/generate")
async def get_copy_generator_sync(
        req: CopyGenerationRequest,
        mode: str = Query("sync", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """文案生成 - 支持任务状态更新"""
    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = req.task_id or task_id_query or str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [文案生成] 处理请求:")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        function_args = {
            "category": req.category,
            "style": req.style,
            "input_data": req.input_data,
            "use_template": req.use_template,
            "ai_enhance": req.ai_enhance,
            "custom_params": req.custom_params
        }

        if mode == "sync":
            # 同步模式
            from core.text_generate.generator import get_copy_generation
            result = get_copy_generation(**function_args)

            # 🔥 如果有tenant_id，更新任务状态为完成，并传入生成的文案内容
            if tenant_id:
                api_service.update_task_status(
                    task_id,
                    "1",
                    tenant_id,
                    business_id=business_id,
                    content=result  # 🔥 传入生成的文案内容
                )

            # 🔥 文案生成返回纯文本，需要包装成字典格式
            wrapped_result = {
                "content_type": "text",
                "text_content": result,
                "result": result,
                "upload_skipped": True,
                "skip_reason": "文本类接口无需上传",
                "function_name": "get_copy_generation",
                "processing_time": 0,
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id
            }

            response = format_response(wrapped_result, mode, urlpath)
            if isinstance(response, dict):
                response.update({
                    "task_id": task_id,
                    "tenant_id": tenant_id,
                    "business_id": business_id
                })
            return response
        else:
            # 🔥 文案生成只支持同步模式
            raise HTTPException(
                status_code=400,
                detail="文案生成接口仅支持同步模式(sync)，请使用 mode=sync 参数"
            )

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=500, detail=f"文案生成失败: {str(e)}")


@app.post("/cover/analyze")
async def analyze_cover_endpoint(
        req: CoverAnalysisRequest,
        mode: str = Query("sync", description="执行模式：sync(同步)/async(异步)"),
        tenant_id_query: str = Query(None, description="租户ID（URL参数）", alias="tenant_id"),
        task_id_query: str = Query(None, description="任务ID（URL参数）", alias="task_id")
):
    """封面分析 - 支持任务状态更新"""
    try:
        tenant_id = req.tenant_id or tenant_id_query
        task_id = task_id_query or str(uuid.uuid4())
        business_id = req.id

        print(f"🎯 [封面分析] 处理请求:")
        print(f"   Platform: {req.platform}")
        print(f"   Task ID: {task_id}")
        print(f"   Tenant ID: {tenant_id}")
        print(f"   Business ID: {business_id}")

        # 🔥 如果有tenant_id，立即更新任务状态为运行中
        if tenant_id:
            api_service.update_task_status(task_id, "0", tenant_id, business_id=business_id)

        # 准备参数
        function_args = {
            "image": req.image,
            "is_url": req.is_url,
            "platform": req.platform
        }

        # 创建包装器函数用于异步执行
        def analyze_cover_wrapper(image, is_url, platform):
            analyzer = CoverAnalyzer()
            if is_url:
                # 下载图片并转换为base64
                image_b64 = analyzer.image_processor.download_image_from_url(image)
            else:
                image_data = image
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',')[1]
                image_b64 = image_data

            # 调用分析方法（使用位置参数）
            result = analyzer.analyze_cover(image_b64, platform)
            if not result["success"]:
                raise Exception(result["error"])
            return result

        if mode == "sync":
            # 同步模式
            result = analyze_cover_wrapper(**function_args)

            # 🔥 如果有tenant_id，更新任务状态为完成
            if tenant_id:
                api_service.update_task_status(task_id, "1", tenant_id, business_id=business_id)

            # 这个接口返回文本结果，需要特殊处理
            response = {
                "status": "completed",
                "data": result,
                "result_type": "analysis",
                "processing_time": 0,
                "function_name": "analyze_cover",
                "task_id": task_id,
                "tenant_id": tenant_id,
                "business_id": business_id,
                "upload_info": {
                    "upload_skipped": True,
                    "skip_reason": "分析结果类接口",
                    "integration": "text_direct"
                }
            }
            return response
        else:
            # 异步模式
            # 将包装器函数注册到全局命名空间
            globals()['analyze_cover_wrapper'] = analyze_cover_wrapper

            task_id = await task_manager.submit_task(
                func_name="analyze_cover_wrapper",
                args=function_args,
                tenant_id=tenant_id,
                business_id=business_id
            )

            return format_response(task_id, mode="async", urlpath=urlpath)

    except Exception as e:
        # 🔥 异常时更新任务状态为失败
        if 'tenant_id' in locals() and tenant_id and 'task_id' in locals() and task_id:
            try:
                api_service.update_task_status(task_id, "2", tenant_id, business_id=locals().get('business_id'))
            except Exception as status_error:
                print(f"⚠️ 更新失败状态时出错: {status_error}")

        raise HTTPException(status_code=500, detail=f"封面分析失败: {str(e)}")



@app.post("/video/natural-language-edit")
async def video_natural_language_edit(request: NaturalLanguageVideoEditRequest):
    """自然语言视频剪辑接口 - 集成AuraRender智能视频创作引擎"""
    mode = getattr(request, 'mode', 'async')  # 默认使用异步模式
    
    # 定义实际处理逻辑
    async def process():
        try:
            # 判断是否使用AuraRender（默认使用）
            use_aura_render = request.use_aura_render if hasattr(request, 'use_aura_render') else True
            
            print(f"🎬 [自然语言视频剪辑] 开始处理...")
            print(f"   描述: {request.natural_language}")
            print(f"   视频URL: {request.video_url}")
            print(f"   模式: {mode}")
            print(f"   使用AuraRender: {use_aura_render}")
            
            if use_aura_render:
                # 使用AuraRender处理
                from video_cut.aura_render.aura_interface import AuraRenderInterface
                
                aura_interface = AuraRenderInterface()
                
                # 构建AuraRender请求
                aura_request = {
                    'natural_language': request.natural_language,
                    'video_url': request.video_url,
                    'preferences': {}
                }
                
                # 添加偏好设置
                if request.output_duration:
                    aura_request['preferences']['duration'] = request.output_duration
                if request.style:
                    aura_request['preferences']['style'] = request.style
                if hasattr(request, 'video_type'):
                    aura_request['preferences']['video_type'] = request.video_type
                
                # 调用AuraRender
                result = aura_interface.create_video(aura_request)
                
                # 转换结果格式
                if result['status'] == 'success':
                    enhanced_result = {
                        "video_url": result['video_url'],
                        "timeline": result.get('script', {}).get('timeline', []),
                        "video_info": {
                            "duration": result['metadata'].get('duration', 0),
                            "video_type": result['metadata'].get('video_type', ''),
                            "style": result['metadata'].get('style', {})
                        },
                        "process_info": {
                            "engine": "AuraRender",
                            "script_path": result['metadata'].get('script_path', ''),
                            "created_at": result['metadata'].get('created_at', '')
                        },
                        "execution_script": result.get('script', {})  # 返回完整的执行脚本供调试
                    }
                else:
                    raise Exception(result.get('error', 'AuraRender处理失败'))
                    
            else:
                # 使用原有的处理逻辑
                from core.clipgenerate.natural_language_video_edit import process_natural_language_video_edit
                
                # 处理视频
                result = process_natural_language_video_edit(
                    natural_language=request.natural_language,
                    video_url=request.video_url,
                    output_duration=request.output_duration,
                    style=request.style,
                    use_timeline_editor=request.use_timeline_editor
                )
                
                # 检查处理结果
                if not result.get("success", False):
                    raise Exception(result.get("error", "处理失败"))
                
                # 使用增强函数处理结果
                enhanced_result = {
                    "video_url": result.get("video_url"),
                    "timeline": result.get("timeline"),
                    "video_info": result.get("video_info"),
                    "process_info": result.get("process_info")
                }
            
            return enhance_endpoint_result(enhanced_result, "natural_language_video_edit", request, is_digital_human=False)
            
        except Exception as e:
            error_res = {"error": str(e), "function_name": "natural_language_video_edit"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    
    # 处理异步模式
    if mode == "async":
        try:
            # 准备异步任务参数
            args = {
                "natural_language": request.natural_language,
                "video_url": request.video_url,
                "output_duration": request.output_duration,
                "style": request.style,
                "use_timeline_editor": request.use_timeline_editor
            }
            
            # 提交异步任务
            task_id = await task_manager.submit_task(
                func_name="process_natural_language_video_edit",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )
            
            return format_response(task_id, mode="async", urlpath=urlpath)
            
        except Exception as e:
            error_res = {"error": str(e), "function_name": "natural_language_video_edit"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 同步模式
        return await process()


# 添加标签视频生成接口
class TagVideoRequest(BaseModel):
    """标签视频生成请求模型"""
    tags: List[str] = Field(..., description="标签列表，按顺序处理")
    tag_videos: Dict[str, Dict[str, List[str]]] = Field(..., description="标签到视频列表的映射")
    text_content: Optional[Union[str, Dict[str, str]]] = Field(None, description="文案内容，支持字符串或字典格式，不提供则AI生成")
    subtitle_config: Optional[Dict[str, Any]] = Field(None, description="字幕配置，支持grid_position(1-9)设置九宫格位置")
    dynamic_tags: Optional[List[str]] = Field(None, description="动态标签列表")
    duration_per_tag: Union[float, Dict[str, float]] = Field(5.0, description="每个标签的时长（秒），可以是统一时长或每个标签单独设置")
    output_format: Optional[Dict[str, Any]] = Field(None, description="输出格式配置")
    mode: str = Field("async", description="处理模式: sync/async")
    tenant_id: Optional[str] = Field(None, description="租户ID，提供则会更新任务状态")
    id: Optional[str] = Field(None, description="业务ID，提供则会更新任务状态")

# 初始化标签视频处理器
tag_video_handler = TagVideoAPIHandler()

def process_tag_video_generation(**kwargs):
    """
    异步任务：标签视频生成处理函数
    """
    print(f"🎬 [ASYNC] 开始异步处理标签视频生成")
    print(f"   参数: {kwargs.keys()}")
    
    try:
        # 使用已有的处理器处理请求
        result = tag_video_handler.handle_request(kwargs)
        
        if result and result.get('success'):
            print(f"✅ [ASYNC] 异步处理成功")
            video_path = result.get('video_path', '')
            
            # 🔥 异步模式下，也需要调用create_resource
            # 这部分逻辑会在AsyncTaskManager的_execute_task_with_oss_upload中处理
            # 这里只需要返回视频路径
            return video_path
        else:
            error_msg = result.get('error', '未知错误') if result else '处理器返回空结果'
            print(f"❌ [ASYNC] 异步处理失败: {error_msg}")
            raise Exception(error_msg)
            
    except Exception as e:
        print(f"❌ [ASYNC] 异步处理异常: {e}")
        raise e

@app.post("/video/generate-from-tags")
async def generate_video_from_tags(request: TagVideoRequest):
    """
    根据标签生成视频
    
    请求示例:
    {
        "tags": ["黄山风景", "徽州特色餐", "屯溪老街", "无边泳池", "峡谷漂流"],
        "tag_videos": {
            "黄山风景": {
                "video": ["assets/videos/huangshan.mp4", "assets/videos/huangshan1.mp4"]
            },
            "徽州特色餐": {
                "video": ["assets/videos/huizhoucai.mp4"]
            },
            "屯溪老街": {
                "video": ["assets/videos/tunxi.mp4", "assets/videos/tunxi1.mp4"]
            },
            "无边泳池": {
                "video": ["assets/videos/wubianyongchi1.mp4", "assets/videos/wubianyongchi2.mp4"]
            },
            "峡谷漂流": {
                "video": ["assets/videos/xiagupiaoliu1.mp4"]
            }
        },
        "text_content": "探索黄山美景，品味徽州美食，漫步千年古街",  // 可选，不提供则AI生成
        "subtitle_config": {  // 可选
            "font_size": 48,
            "color": "white",
            "position": ["center", "bottom"],
            "margin": 50
        },
        "dynamic_tags": ["黄山", "美食", "古街", "泳池", "漂流"],  // 可选
        "duration_per_tag": 5.0,
        "output_format": {  // 可选
            "fps": 30,
            "resolution": [1920, 1080]
        },
        "mode": "sync"
    }
    """
    mode = request.mode
    urlpath = request.dict().get('urlpath', '')
    
    # 定义处理函数
    async def process():
        try:
            print(f"[DEBUG] 收到标签视频生成请求: tags={request.tags}")
            print(f"[DEBUG] 租户ID: {request.tenant_id}, 业务ID: {request.id}")
            
            # 🔥 如果有tenant_id，立即更新开始状态
            if request.tenant_id:
                try:
                    print(f"🔄 [STATUS] 更新开始状态: tenant_id={request.tenant_id}, id={request.id}")
                    api_service.update_task_status(
                        task_id=str(request.id or 'unknown'),
                        status="0",  # 开始状态
                        tenant_id=request.tenant_id,
                        business_id=request.id
                    )
                    print(f"✅ [STATUS] 开始状态更新成功")
                except Exception as e:
                    print(f"❌ [STATUS] 开始状态更新失败: {e}")
            
            # 处理请求
            result = tag_video_handler.handle_request(request.dict())
            
            # 检查结果
            if not result:
                print("[ERROR] tag_video_handler返回None")
                error_res = {"error": "视频生成处理返回空结果", "function_name": "generate_from_tags"}
                return format_response(error_res, mode="sync", error_type="general_exception")
            
            print(f"[DEBUG] 处理结果: success={result.get('success')}, error={result.get('error')}")
            
            if result.get('success'):
                # 如果有视频路径，尝试上传到OSS
                if 'video_path' in result:
                    try:
                        # 上传到OSS
                        local_path = result['video_path']
                        oss_filename = f"tag_videos/{datetime.now().strftime('%Y%m%d')}/{Path(local_path).name}"
                        upload_success = upload_to_oss(local_path, oss_filename)
                        
                        if upload_success:
                            video_url = f"https://lan8-e-business.oss-cn-hangzhou.aliyuncs.com/{oss_filename}"
                            print(f"✅ [TAG-VIDEO] OSS上传成功，访问链接: {video_url}")
                            
                            # 🔥 调用create_resource保存资源到素材库
                            resource_id = None
                            if request.tenant_id:
                                try:
                                    from core.clipgenerate.interface_function import get_file_info
                                    file_info = get_file_info(local_path)
                                    if file_info:
                                        resource_result = api_service.create_resource(
                                            resource_type=file_info['resource_type'],
                                            name=file_info['name'],
                                            path=oss_filename,
                                            local_full_path=local_path,
                                            file_type=file_info['file_type'],
                                            size=file_info['size'],
                                            tenant_id=request.tenant_id
                                        )
                                        print(f"✅ [TAG-VIDEO] 资源保存到素材库成功")
                                        
                                        # 尝试从响应中获取resource_id
                                        if resource_result and isinstance(resource_result, dict):
                                            resource_id = resource_result.get('resourceId') or resource_result.get('id')
                                        resource_id = resource_id or 95  # 默认resource_id
                                    else:
                                        print(f"⚠️ [TAG-VIDEO] 无法获取文件信息: {local_path}")
                                        resource_id = 95
                                except Exception as e:
                                    print(f"❌ [TAG-VIDEO] 资源创建失败: {e}")
                                    resource_id = 95
                            else:
                                resource_id = 95
                            
                            # 计算总时长
                            if isinstance(request.duration_per_tag, dict):
                                # 如果是字典，计算所有标签时长的和
                                total_duration = sum(request.duration_per_tag.get(tag, 5.0) for tag in request.tags)
                            else:
                                # 如果是数字，乘以标签数量
                                total_duration = request.duration_per_tag * len(request.tags)
                            
                            # 🔥 如果有tenant_id，更新完成状态
                            if request.tenant_id:
                                try:
                                    print(f"🔄 [STATUS] 更新完成状态: tenant_id={request.tenant_id}, resource_id={resource_id}")
                                    api_service.update_task_status(
                                        task_id=str(request.id or 'unknown'),
                                        status="1",  # 完成状态
                                        tenant_id=request.tenant_id,
                                        business_id=request.id,
                                        path=oss_filename,
                                        resource_id=resource_id
                                    )
                                    print(f"✅ [STATUS] 完成状态更新成功")
                                except Exception as e:
                                    print(f"❌ [STATUS] 完成状态更新失败: {e}")
                            
                            # 返回成功响应
                            enhanced_result = {
                                'video_url': video_url,
                                'video_path': local_path,
                                'oss_path': oss_filename,
                                'tags': request.tags,
                                'duration_per_tag': request.duration_per_tag,
                                'total_duration': total_duration,
                                'text_content': result.get('text_content', request.text_content),
                                'message': '视频生成成功',
                                'resource_id': resource_id
                            }
                            
                            return format_response(enhanced_result, mode="sync")
                        else:
                            # 计算总时长
                            if isinstance(request.duration_per_tag, dict):
                                total_duration = sum(request.duration_per_tag.get(tag, 5.0) for tag in request.tags)
                            else:
                                total_duration = request.duration_per_tag * len(request.tags)
                            
                            # 🔥 OSS上传失败，更新失败状态
                            if request.tenant_id:
                                try:
                                    print(f"❌ [STATUS] 更新失败状态: OSS上传失败")
                                    api_service.update_task_status(
                                        task_id=str(request.id or 'unknown'),
                                        status="2",  # 失败状态
                                        tenant_id=request.tenant_id,
                                        business_id=request.id
                                    )
                                except Exception as e:
                                    print(f"❌ [STATUS] 失败状态更新失败: {e}")
                            
                            # 上传失败但本地生成成功
                            enhanced_result = {
                                'video_path': local_path,
                                'tags': request.tags,
                                'duration_per_tag': request.duration_per_tag,
                                'total_duration': total_duration,
                                'message': '视频生成成功（OSS上传失败）'
                            }
                            return format_response(enhanced_result, mode="sync")
                    except Exception as e:
                        print(f"上传OSS失败: {e}")
                        
                        # 计算总时长
                        if isinstance(request.duration_per_tag, dict):
                            total_duration = sum(request.duration_per_tag.get(tag, 5.0) for tag in request.tags)
                        else:
                            total_duration = request.duration_per_tag * len(request.tags)
                        
                        # 🔥 异常情况，更新失败状态
                        if request.tenant_id:
                            try:
                                print(f"❌ [STATUS] 更新失败状态: 上传异常 - {str(e)}")
                                api_service.update_task_status(
                                    task_id=str(request.id or 'unknown'),
                                    status="2",  # 失败状态
                                    tenant_id=request.tenant_id,
                                    business_id=request.id
                                )
                            except Exception as status_e:
                                print(f"❌ [STATUS] 失败状态更新失败: {status_e}")
                        
                        # 返回本地路径
                        enhanced_result = {
                            'video_path': result['video_path'],
                            'tags': request.tags,
                            'duration_per_tag': request.duration_per_tag,
                            'total_duration': total_duration,
                            'message': '视频生成成功（OSS上传失败）'
                        }
                        return format_response(enhanced_result, mode="sync")
                else:
                    # 没有video_path，返回错误
                    error_res = {"error": "生成的结果中没有视频路径", "function_name": "generate_from_tags"}
                    return format_response(error_res, mode="sync", error_type="general_exception")
            else:
                # 处理失败
                if request.tenant_id:
                    try:
                        print(f"❌ [STATUS] 更新失败状态: 生成失败")
                        api_service.update_task_status(
                            task_id=str(request.id or 'unknown'),
                            status="2",  # 失败状态
                            tenant_id=request.tenant_id,
                            business_id=request.id
                        )
                    except Exception as e:
                        print(f"❌ [STATUS] 失败状态更新失败: {e}")
                
                error_res = {"error": result.get('error', '生成失败'), "function_name": "generate_from_tags"}
                return format_response(error_res, mode="sync", error_type="general_exception")
                
        except Exception as e:
            # 异常情况下也更新失败状态
            if request.tenant_id:
                try:
                    print(f"❌ [STATUS] 更新失败状态: 异常 - {str(e)}")
                    api_service.update_task_status(
                        task_id=str(request.id or 'unknown'),
                        status="2",  # 失败状态
                        tenant_id=request.tenant_id,
                        business_id=request.id
                    )
                except Exception as status_e:
                    print(f"❌ [STATUS] 失败状态更新失败: {status_e}")
            
            error_res = {"error": str(e), "function_name": "generate_from_tags"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    
    # 处理异步模式
    if mode == "async":
        try:
            # 准备异步任务参数
            args = request.dict()
            
            # 提交异步任务
            task_id = await task_manager.submit_task(
                func_name="process_tag_video_generation",
                args=args,
                tenant_id=getattr(request, 'tenant_id', None),
                business_id=getattr(request, 'id', None)
            )
            
            return format_response(task_id, mode="async", urlpath=urlpath)
            
        except Exception as e:
            error_res = {"error": str(e), "function_name": "generate_from_tags"}
            return format_response(error_res, mode="sync", error_type="general_exception")
    else:
        # 同步模式
        return await process()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",  # 指向当前文件的应用实例
        host="0.0.0.0",
        port=8100,
        # reload=True,  # 启用热重载
        reload_dirs=["."],  # 监控当前目录下的文件变化
        reload_excludes=["*.tmp"],  # 可选：排除不需要监控的文件
        reload_delay=1.0  # 可选：文件变化后延迟1秒重载
    )

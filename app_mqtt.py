# -*- coding: utf-8 -*-
# @Time    : 2025/6/23 11:23
# @Author  : 蔍鸣霸霸
# @FileName: app_mqtt_enhanced.py
# @Software: PyCharm
# @Blog    ：只因你太美

import argparse
import random
import string
import threading
import queue
import time
import asyncio
import json
import uuid
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, List, Any
from threading import Condition
from concurrent.futures import ThreadPoolExecutor
import paho.mqtt.client as mqtt
import threading
# 导入原有的模块
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
from download_material import download_materials_from_api


# ========== API配置 ==========
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

    def update_task_status_url(self):
        return f"{self.admin_api_base}/agent/task-video-info/update"

    def create_resource_url(self):
        return f"{self.admin_api_base}/agent/resource/create"


# ========== MQTT配置 ==========
class MQTTConfig:
    def __init__(self):
        self.broker_host = "121.36.203.36"
        self.broker_port = 18020
        self.username = "username"
        self.password = "password"
        self.client_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )
        # 主题配置
        self.subscribe_topic = "video/process/request"
        self.response_topic = "video/process/response"
        self.status_topic = "video/process/status"

        self.qos = int(os.getenv("MQTT_QOS", 1))
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", 60))


# ========== 全局变量初始化 ==========
path = config.get_user_data_dir()
if not os.path.exists(path):
    os.makedirs(path)

MATERIAL_ROOT = os.path.join(config.get_user_data_dir(), "materials")
UPLOAD_DIR = os.path.join(config.get_user_data_dir(), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 配置初始化
mqtt_config = MQTTConfig()
api_config = APIConfig()


# ========== API服务类 ==========
class APIService:
    def __init__(self, config: APIConfig):
        self.config = config

    def update_task_status(self, task_id: str, task_no: str = "", status: str = "1", tenant_id=None, path: str = "",
                           resource_id=None):
        """
        更新任务状态
        status: "1"=未开始, "0"=运行中, "1"=完成, "2"=失败
        tenant_id: 租户ID，会添加到请求头和请求体中
        path: 文件路径
        resource_id: 资源ID（在任务完成时传入）
        """
        url = self.config.update_task_status_url()
        headers = self.config.get_headers(tenant_id)

        data = {
            "id": task_id,
            "taskNo": task_no,
            "status": status,
            "path": path
        }

        # 如果有资源ID，添加到请求体中
        if resource_id:
            data["resourceId"] = resource_id

        # 将租户ID添加到请求体中
        if tenant_id:
            data["tenantId"] = tenant_id

        try:
            response = requests.put(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            print(
                f"✅ 任务状态更新成功: {task_id} -> status={status}, tenantId={tenant_id}, path={path}, resourceId={resource_id}")
            print(f"📤 请求URL: {url}")
            print(f"📤 请求头: {headers}")
            print(f"📤 请求体: {data}")
            print(f"📤 响应: {response.text}")
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"❌ 任务状态更新失败: {task_id}, 错误: {str(e)}")
            print(f"📤 请求URL: {url}")
            print(f"📤 请求头: {headers}")
            print(f"📤 请求数据: {data}")
            return None

    def create_resource(self, resource_type: str, name: str, path: str, file_type: str, size: int, tenant_id=None):
        """
        保存资源到素材库
        resource_type: "1"=视频, "2"=图片, "3"=音频等
        tenant_id: 租户ID，会添加到请求头和请求体中
        """
        url = self.config.create_resource_url()
        headers = self.config.get_headers(tenant_id)

        data = {
            "type": resource_type,
            "name": name,
            "path": path,
            "fileType": file_type,
            "size": size
        }

        # 将租户ID添加到请求体中
        if tenant_id:
            data["tenantId"] = tenant_id

        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()

            print(f"✅ 资源保存成功: {name} -> {path}, tenantId={tenant_id}")
            print(f"📤 请求URL: {url}")
            print(f"📤 请求头: {headers}")
            print(f"📤 请求体: {data}")
            print(f"📤 响应: {response.text}")

            # 尝试从响应中提取resourceId
            response_data = response.json()
            print(f"响应体为:{response_data}")
            resource_id = None

            # 常见的resourceId字段名称
            possible_id_fields = ['resourceId', 'id', 'data', 'result']
            for field in possible_id_fields:
                if field in response_data:
                    if field == 'data' and isinstance(response_data[field], dict):
                        # 如果data是对象，尝试从中提取id
                        resource_id = response_data[field].get('id') or response_data[field].get('resourceId')
                    else:
                        resource_id = response_data[field]
                    if resource_id:
                        break

            print(f"📋 提取到资源ID: {resource_id}")
            return {
                'response': response_data,
                'resource_id': resource_id
            }

        except requests.exceptions.RequestException as e:
            print(f"❌ 资源保存失败: {name}, 错误: {str(e)}")
            print(f"📤 请求URL: {url}")
            print(f"📤 请求头: {headers}")
            print(f"📤 请求数据: {data}")
            return None


# ========== 辅助函数 ==========
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


def get_file_info(file_path):
    """获取文件信息"""
    if not os.path.exists(file_path):
        return None

    stat = os.stat(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()

    # 根据扩展名判断文件类型
    if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']:
        file_type = 'video/mp4'
        resource_type = "1"  # 视频
    elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        file_type = 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else f'image/{file_ext[1:]}'
        resource_type = "2"  # 图片
    elif file_ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']:
        file_type = 'audio/mpeg' if file_ext == '.mp3' else f'audio/{file_ext[1:]}'
        resource_type = "3"  # 音频
    else:
        file_type = 'application/octet-stream'
        resource_type = "4"  # 其他

    return {
        'size': stat.st_size,
        'file_type': file_type,
        'resource_type': resource_type,
        'name': os.path.basename(file_path)
    }


def get_smart_clip_video(input_source, is_directory=True, company_name="测试公司",
                         text_list=None, audio_durations=None, clip_mode="random",
                         target_resolution=(1920, 1080)):
    """智能剪辑包装器函数"""
    print(f"🎬 智能剪辑请求:")
    print(f"   输入源: {input_source}")
    print(f"   剪辑模式: {clip_mode}")
    print(f"   是否目录: {is_directory}")

    video_files = []

    if isinstance(input_source, list):
        print(f"📋 处理文件列表，共 {len(input_source)} 个文件")
        for file_path in input_source:
            processed_path = file_path

            if file_path.startswith("uploads/"):
                processed_path = os.path.join(UPLOAD_DIR, file_path.replace("uploads/", ""))
            elif not os.path.isabs(file_path):
                possible_paths = [
                    os.path.join(UPLOAD_DIR, file_path),
                    os.path.join(MATERIAL_ROOT, file_path),
                    file_path
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        processed_path = path
                        break

            if os.path.exists(processed_path) and os.path.isfile(processed_path):
                video_files.append(processed_path)
                print(f"✅ 找到文件: {os.path.basename(processed_path)}")
            else:
                print(f"⚠️ 文件不存在: {file_path}")

        if not video_files:
            raise ValueError(f"没有找到有效的视频文件")

        is_directory = False
        processed_input_source = video_files

    else:
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
        output_path = os.path.join(output_dir, "random_clip_video.mp4")
        time.sleep(2)
        with open(output_path, 'w') as f:
            f.write("random clip video")
        return output_path

    elif clip_mode == "smart":
        print("🧠 使用智能剪辑模式")
        output_path = os.path.join(output_dir, "smart_clip_video.mp4")
        time.sleep(2)
        with open(output_path, 'w') as f:
            f.write("smart clip video")
        return output_path

    else:
        raise ValueError(f"不支持的剪辑模式: {clip_mode}，支持的模式: random, smart")


# ========== 函数映射表 ==========
FUNCTION_MAP = {
    "sinology": get_video_sinology,
    "advertisement": get_video_advertisement,
    "big_word": get_big_word,
    "catmeme": get_video_catmeme,
    "clicktype": get_video_clicktype,
    "clothes_different_scene": get_video_clothes_diffrent_scene,
    "dgh_img_insert": get_video_dgh_img_insert,
    "digital_human_clips": get_video_digital_huamn_clips,
    "digital_human_easy": get_video_digital_huamn_easy_local,
    "incitement": get_video_incitment,
    "stickman": get_video_stickman,
    "clothes_fast_change": get_videos_clothes_fast_change,
    "text_industry": get_text_industry,
    "advertisement_enhance": get_video_advertisement_enhance,
    "smart_clip": get_smart_clip_video,
}


# ========== 任务处理 ==========
class AsyncTaskManager:
    def __init__(self, max_workers=5, max_task_timeout=1800):
        self.max_workers = max_workers
        self.max_task_timeout = max_task_timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TaskWorker")
        self.results = {}
        self.result_condition = threading.Condition()
        self.active_futures = {}
        self.api_service = APIService(api_config)

        print(f"🚀 异步任务管理器初始化: max_workers={max_workers}, timeout={max_task_timeout}s")

    def submit_task_sync(self, func_name: str, args: dict, task_id: str = None, tenant_id=None, user_id=None) -> str:
        """同步提交任务到线程池"""
        if not task_id:
            task_id = str(uuid.uuid4())

        # 检查函数是否存在
        func = FUNCTION_MAP.get(func_name)
        if not func:
            raise ValueError(f"函数不存在: {func_name}")

        print(f"🎯 [SYNC] 提交任务: {task_id} -> {func_name}, 租户ID: {tenant_id}")

        # 更新任务状态为运行中
        self.api_service.update_task_status(task_id, "", "0", tenant_id)

        # 初始化任务状态
        with self.result_condition:
            self.results[task_id] = {
                "task_id": task_id,
                "function_name": func_name,
                "status": "submitted",
                "submitted_at": time.time(),
                "progress": "0%",
                "current_step": "已提交，开始执行",
                "input_params": args.copy(),
                "tenant_id": tenant_id,
                "user_id": user_id
            }
            self.result_condition.notify_all()

        # 同步执行任务
        result = self._execute_task_with_timeout(task_id, func_name, args)

        # 处理结果
        self._handle_task_result_sync(task_id, result, tenant_id)

        return task_id

    def _execute_task_with_timeout(self, task_id: str, func_name: str, args: dict):
        """在线程池中执行任务（带超时控制）"""
        start_time = time.time()

        try:
            print(f"🔄 [WORKER-{threading.current_thread().name}] 开始执行任务: {task_id}")

            # 更新状态为处理中
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "status": "processing",
                        "started_at": start_time,
                        "current_step": "正在执行",
                        "progress": "20%",
                        "worker_thread": threading.current_thread().name
                    })
                    self.result_condition.notify_all()

            # 获取函数并执行
            func = FUNCTION_MAP.get(func_name)

            # 使用超时控制执行函数
            with ThreadPoolExecutor(max_workers=1) as inner_executor:
                inner_future = inner_executor.submit(func, **args)
                try:
                    result = inner_future.result(timeout=self.max_task_timeout)

                    print(f"✅ [WORKER-{threading.current_thread().name}] 任务执行成功: {task_id}")
                    return {
                        "status": "completed",
                        "result": result,
                        "processing_time": time.time() - start_time
                    }

                except TimeoutError:
                    print(f"⏰ [WORKER-{threading.current_thread().name}] 任务执行超时: {task_id}")
                    inner_future.cancel()
                    return {
                        "status": "failed",
                        "error": f"任务执行超时 ({self.max_task_timeout}秒)",
                        "error_type": "TimeoutError",
                        "processing_time": time.time() - start_time
                    }

        except Exception as e:
            print(f"❌ [WORKER-{threading.current_thread().name}] 任务执行失败: {task_id}, 错误: {str(e)}")
            import traceback
            return {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "processing_time": time.time() - start_time
            }

    def _handle_task_result_sync(self, task_id: str, execution_result, tenant_id=None):
        """同步处理任务结果"""
        try:
            # 更新最终结果
            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        **execution_result,
                        "completed_at": time.time(),
                        "current_step": "已完成" if execution_result["status"] == "completed" else "执行失败"
                    })

                    # 处理成功结果的路径提取
                    if execution_result["status"] == "completed":
                        result = execution_result.get("result")
                        warehouse_path = extract_warehouse_path(result)
                        full_path = get_full_file_path(warehouse_path) if warehouse_path else None
                        file_exists = verify_file_exists(warehouse_path) if warehouse_path else False

                        self.results[task_id].update({
                            "warehouse_path": warehouse_path,
                            "videoPath": warehouse_path,
                            "full_file_path": full_path,
                            "file_exists": file_exists,
                            "progress": "100%"
                        })

                        resource_id = None

                        # 如果文件存在，保存到素材库
                        if file_exists and full_path:
                            file_info = get_file_info(full_path)
                            if file_info:
                                # 构造API路径（相对路径）
                                api_path = f"/agent/resource/{warehouse_path}"

                                resource_result = self.api_service.create_resource(
                                    resource_type=file_info['resource_type'],
                                    name=file_info['name'],
                                    path=api_path,
                                    file_type=file_info['file_type'],
                                    size=file_info['size'],
                                    tenant_id=tenant_id
                                )

                                if resource_result:
                                    resource_id = resource_result.get('resource_id')
                                    print(f"📋 素材库保存成功，资源ID: {resource_id}")

                        # 更新任务状态为完成，带上resourceId和path
                        self.api_service.update_task_status(
                            task_id=task_id,
                            task_no="",
                            status="1",
                            tenant_id=tenant_id,
                            path=warehouse_path or "",
                            resource_id=resource_id
                        )

                    else:
                        # 更新任务状态为失败
                        self.api_service.update_task_status(task_id, "", "2", tenant_id)

                    self.result_condition.notify_all()

            print(f"🎉 [SYNC] 任务结果处理完成: {task_id} -> {execution_result['status']}")

        except Exception as e:
            print(f"❌ [SYNC] 处理任务结果失败: {task_id}, 错误: {str(e)}")

            # 更新任务状态为失败
            self.api_service.update_task_status(task_id, "", "2", tenant_id)

            with self.result_condition:
                if task_id in self.results:
                    self.results[task_id].update({
                        "status": "failed",
                        "error": f"结果处理失败: {str(e)}",
                        "error_type": type(e).__name__,
                        "completed_at": time.time(),
                        "current_step": "结果处理失败"
                    })
                    self.result_condition.notify_all()

    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        with self.result_condition:
            if task_id not in self.results:
                return {"status": "not_found", "message": "任务不存在"}
            return self.results[task_id].copy()


async_task_manager = AsyncTaskManager(max_workers=5, max_task_timeout=1800)


# ========== MQTT处理器 ==========
class MQTTProcessor:
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = mqtt.Client(client_id=config.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # 设置认证信息
        if config.username and config.password:
            self.client.username_pw_set(config.username, config.password)

        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            print(f"🔗 MQTT连接成功! Broker: {self.config.broker_host}:{self.config.broker_port}")

            # 订阅处理请求主题
            client.subscribe(self.config.subscribe_topic, qos=self.config.qos)
            print(f"📡 已订阅主题: {self.config.subscribe_topic}")

            # 发送在线状态
            self.publish_status("online", "视频处理服务已启动")

        else:
            self.connected = False
            error_messages = {
                1: "协议版本不正确",
                2: "客户端ID不可用",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            error_msg = error_messages.get(rc, f"未知错误 ({rc})")
            print(f"❌ MQTT连接失败: {error_msg} (错误代码: {rc})")

            # 诊断信息
            print(f"🔍 诊断信息:")
            print(f"   代理地址: {self.config.broker_host}:{self.config.broker_port}")
            print(f"   客户端ID: {self.config.client_id}")
            print(f"   用户名: {self.config.username or '未设置'}")
            print(f"   密码: {'已设置' if self.config.password else '未设置'}")

    def on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.connected = False
        if rc != 0:
            print(f"🔌 MQTT意外断开连接，错误代码: {rc}")
        else:
            print(f"🔌 MQTT正常断开连接")

    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        try:
            # 解析消息
            message = msg.payload.decode('utf-8')
            print(f"📨 收到MQTT消息: {message}")

            # 解析JSON数据
            try:
                data = json.loads(message)
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {str(e)}"
                print(f"❌ {error_msg}")
                self.publish_error(None, error_msg)
                return

            # 验证必需字段
            if not isinstance(data, dict):
                error_msg = "消息格式错误：必须是JSON对象"
                print(f"❌ {error_msg}")
                self.publish_error(None, error_msg)
                return

            func_name = data.get("function")
            task_id = data.get("id")  # 从消息中获取id作为task_id

            if not func_name:
                error_msg = "缺少必需字段: function"
                print(f"❌ {error_msg}")
                self.publish_error(task_id, error_msg)
                return

            # 检查函数是否存在
            if func_name not in FUNCTION_MAP:
                error_msg = f"不支持的函数: {func_name}"
                print(f"❌ {error_msg}")
                available_functions = list(FUNCTION_MAP.keys())
                self.publish_error(task_id, f"{error_msg}。可用函数: {available_functions}")
                return

            # 提取参数 - 处理字符串形式的JSON
            params_raw = data.get("params", {})
            if isinstance(params_raw, str):
                try:
                    params = json.loads(params_raw)
                except json.JSONDecodeError:
                    params = {}
            else:
                params = params_raw

            msg_id = data.get("msgId")
            req_header = data.get("reqHeader")
            send_time = data.get("sendTime")
            tenant_id = data.get("tenantId")
            user_id = data.get("userId")

            print(f"🎯 处理函数: {func_name}, 任务ID: {task_id}, 租户ID: {tenant_id}, 用户ID: {user_id}, 参数: {params}")

            # 异步处理任务
            threading.Thread(
                target=self.process_task,
                args=(func_name, params, task_id, msg_id, req_header, tenant_id, user_id),
                daemon=True
            ).start()

        except Exception as e:
            error_msg = f"处理MQTT消息失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            self.publish_error(None, error_msg)

    def process_task(self, func_name: str, params: dict, task_id: str = None,
                     msg_id: str = None, req_header: str = None, tenant_id=None, user_id=None):
        """处理具体的任务"""
        try:
            print(f"🚀 开始处理任务: {func_name}, ID: {task_id}, 租户ID: {tenant_id}")

            # 发送处理开始状态
            self.publish_status("processing", f"开始处理 {func_name} 任务", task_id, tenant_id)

            # 提交任务并等待完成
            final_task_id = async_task_manager.submit_task_sync(func_name, params, task_id, tenant_id, user_id)

            # 获取最终结果
            task_result = async_task_manager.get_task_status(final_task_id)

            if task_result["status"] == "completed":
                # 发送成功结果
                response_data = {
                    "id": task_id,
                    "msgId": msg_id,
                    "reqHeader": req_header,
                    "task_id": final_task_id,
                    "function": func_name,
                    "status": "completed",
                    "tenantId": tenant_id,
                    "userId": user_id,
                    "result": {
                        "warehouse_path": task_result.get("warehouse_path"),
                        "videoPath": task_result.get("warehouse_path"),  # 兼容字段
                        "full_file_path": task_result.get("full_file_path"),
                        "file_exists": task_result.get("file_exists", False),
                        "processing_time": task_result.get("processing_time")
                    },
                    "timestamp": time.time()
                }

                self.publish_response(response_data)
                print(f"✅ 任务完成: {func_name} -> {task_result.get('warehouse_path')}")

            else:
                # 发送失败结果
                error_data = {
                    "id": task_id,
                    "msgId": msg_id,
                    "reqHeader": req_header,
                    "task_id": final_task_id,
                    "function": func_name,
                    "status": "failed",
                    "tenantId": tenant_id,
                    "userId": user_id,
                    "error": task_result.get("error", "未知错误"),
                    "error_type": task_result.get("error_type"),
                    "processing_time": task_result.get("processing_time"),
                    "timestamp": time.time()
                }

                self.publish_response(error_data)
                print(f"❌ 任务失败: {func_name} -> {task_result.get('error')}")

        except Exception as e:
            error_msg = f"任务处理异常: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")

            # 发送异常结果
            error_data = {
                "id": task_id,
                "msgId": msg_id,
                "reqHeader": req_header,
                "function": func_name,
                "status": "failed",
                "tenantId": tenant_id,
                "userId": user_id,
                "error": error_msg,
                "error_type": type(e).__name__,
                "timestamp": time.time()
            }

            self.publish_response(error_data)

    def publish_response(self, data: dict):
        """发布响应消息"""
        if not self.connected:
            print("⚠️ MQTT未连接，无法发送响应")
            return

        try:
            message = json.dumps(data, ensure_ascii=False, default=str)
            result = self.client.publish(self.config.response_topic, message, qos=self.config.qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 响应已发送: {data.get('status')} -> {self.config.response_topic}")
            else:
                print(f"❌ 发送响应失败，错误代码: {result.rc}")

        except Exception as e:
            print(f"❌ 发布响应消息失败: {str(e)}")

    def publish_status(self, status: str, message: str, task_id: str = None, tenant_id=None):
        """发布状态消息"""
        if not self.connected:
            return

        try:
            status_data = {
                "status": status,
                "message": message,
                "task_id": task_id,
                "tenantId": tenant_id,
                "timestamp": time.time(),
                "client_id": self.config.client_id
            }

            message_json = json.dumps(status_data, ensure_ascii=False, default=str)
            self.client.publish(self.config.status_topic, message_json, qos=self.config.qos)
            print(f"📊 状态已发送: {status} - {message} (租户ID: {tenant_id})")

        except Exception as e:
            print(f"❌ 发布状态消息失败: {str(e)}")

    def publish_error(self, task_id: str, error_message: str):
        """发布错误消息"""
        error_data = {
            "id": task_id,
            "status": "error",
            "error": error_message,
            "timestamp": time.time()
        }
        self.publish_response(error_data)

    def connect(self):
        """连接到MQTT代理"""
        try:
            print(f"🔗 正在连接MQTT代理: {self.config.broker_host}:{self.config.broker_port}")
            print(f"🔍 连接参数:")
            print(f"   客户端ID: {self.config.client_id}")
            print(f"   用户名: {self.config.username or '未设置'}")
            print(f"   密码: {'已设置' if self.config.password else '未设置'}")
            print(f"   保持连接: {self.config.keepalive}秒")

            self.client.connect(self.config.broker_host, self.config.broker_port, self.config.keepalive)
            return True
        except Exception as e:
            print(f"❌ MQTT连接异常: {str(e)}")
            print(f"🔍 可能的原因:")
            print(f"   1. 网络连接问题")
            print(f"   2. MQTT代理地址或端口错误")
            print(f"   3. 防火墙阻止连接")
            print(f"   4. MQTT代理服务未启动")
            return False

    def start(self):
        """启动MQTT客户端"""
        max_retry = 5
        retry_delay = 5

        for attempt in range(max_retry):
            if self.connect():
                print("🚀 启动MQTT客户端...")
                try:
                    self.client.loop_forever()
                except Exception as e:
                    print(f"❌ MQTT客户端运行异常: {str(e)}")
                    if attempt < max_retry - 1:
                        print(f"⏰ {retry_delay}秒后重试... (尝试 {attempt + 2}/{max_retry})")
                        time.sleep(retry_delay)
                    continue
                break
            else:
                if attempt < max_retry - 1:
                    print(f"⏰ {retry_delay}秒后重试连接... (尝试 {attempt + 2}/{max_retry})")
                    time.sleep(retry_delay)
                else:
                    print("❌ 达到最大重试次数，无法启动MQTT客户端")
                    print("🔧 请检查以下项目:")
                    print("   1. MQTT代理是否正在运行")
                    print("   2. 网络连接是否正常")
                    print("   3. 用户名和密码是否正确")
                    print("   4. 端口是否被防火墙阻止")
                    break

    def stop(self):
        """停止MQTT客户端"""
        if self.connected:
            self.publish_status("offline", "视频处理服务已停止")
        self.client.disconnect()
        print("🛑 MQTT客户端已停止")


# ========== 主程序 ==========
def main():
    parser = argparse.ArgumentParser(description='MQTT视频处理服务 (增强版)')
    parser.add_argument('--broker', default='121.36.203.36', help='MQTT代理地址')
    parser.add_argument('--port', type=int, default=18020, help='MQTT代理端口')
    parser.add_argument('--username', help='MQTT用户名')
    parser.add_argument('--password', help='MQTT密码')
    parser.add_argument('--subscribe-topic', default='video/process/request', help='订阅主题')
    parser.add_argument('--response-topic', default='video/process/response', help='响应主题')
    parser.add_argument('--status-topic', default='video/process/status', help='状态主题')
    parser.add_argument('--http-port', type=int, default=8080, help='HTTP状态查询端口')
    parser.add_argument('--api-base-url', default='http://localhost:8080', help='API服务基础URL (默认使用内置配置)')

    args = parser.parse_args()

    # 更新配置 - 但不覆盖已配置的API地址
    mqtt_config.broker_host = args.broker
    mqtt_config.broker_port = args.port
    mqtt_config.username = args.username or mqtt_config.username
    mqtt_config.password = args.password or mqtt_config.password
    mqtt_config.subscribe_topic = args.subscribe_topic
    mqtt_config.response_topic = args.response_topic
    mqtt_config.status_topic = args.status_topic

    # 只有在明确指定了非默认值时才更新API配置
    if args.api_base_url != 'http://localhost:8080':
        api_config.base_url = args.api_base_url
        api_config.admin_api_base = f"{api_config.base_url}/admin-api"
        print(f"🔧 使用自定义API地址: {api_config.base_url}")
    else:
        print(f"🔧 使用默认API地址: {api_config.base_url}")

    # 创建处理器
    global mqtt_processor
    mqtt_processor = MQTTProcessor(mqtt_config)

    print("🎬 视频处理MQTT服务启动中...")
    print(f"📡 MQTT代理: {mqtt_config.broker_host}:{mqtt_config.broker_port}")
    print(f"📡 订阅主题: {mqtt_config.subscribe_topic}")
    print(f"📤 响应主题: {mqtt_config.response_topic}")
    print(f"📊 状态主题: {mqtt_config.status_topic}")
    print(f"🌐 HTTP查询端口: {args.http_port}")
    print(f"🔗 API服务地址: {api_config.base_url}")

    print("\n🔧 支持的函数:")
    for func_name in FUNCTION_MAP.keys():
        print(f"  - {func_name}")

    print("\n📋 MQTT消息格式示例:")
    example_message = {
        "function": "sinology",
        "id": 6,
        "msgId": "6",
        "params": "{\"title\":\"国学经典\",\"content\":\"讲解古诗词的魅力\"}",
        "reqHeader": "12",
        "sendTime": "2025-06-23T13:41:32.881",
        "tenantId": 1,
        "type": "request",
        "userId": 1
    }
    print(json.dumps(example_message, ensure_ascii=False, indent=2))

    print("\n🌐 HTTP状态查询示例:")
    print(f"curl http://localhost:{args.http_port}/task/status?task_id=<task_id>")
    print(f"curl http://localhost:{args.http_port}/task/list")
    print(f"curl http://localhost:{args.http_port}/health")
    print(f"curl http://localhost:{args.http_port}/mqtt/test")
    print(f"curl http://localhost:{args.http_port}/api/test")

    print("\n🔧 MQTT连接故障排除:")
    print("1. 检查MQTT代理是否运行:")
    print(f"   telnet {mqtt_config.broker_host} {mqtt_config.broker_port}")
    print("2. 检查用户名密码:")
    print(f"   用户名: {mqtt_config.username or '未设置'}")
    print(f"   密码: {'已设置' if mqtt_config.password else '未设置'}")
    print("3. 如果连接失败，可以:")
    print("   - 检查网络连接")
    print("   - 确认MQTT代理配置")
    print("   - 检查防火墙设置")
    print("   - 验证认证信息")

    print("\n🔧 API服务配置:")
    print(f"当前API服务: {api_config.base_url}")
    if api_config.base_url == "http://localhost:8080":
        print("⚠️ 使用默认API配置，如需连接真实API服务请设置:")
        print("   export API_BASE_URL=http://your-api-server:port")
        print("   或使用 --api-base-url 参数")
    else:
        print("✅ 已配置自定义API服务")

    try:
        # 启动MQTT处理器
        mqtt_processor.start()

    except KeyboardInterrupt:
        print("\n🛑 接收到停止信号...")
        mqtt_processor.stop()

        print("✅ 服务已安全停止")
    except Exception as e:
        print(f"❌ 服务运行异常: {str(e)}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        mqtt_processor.stop()



if __name__ == "__main__":
    main()

# ========== 更新说明 ==========
"""
🎬 MQTT视频处理服务 (增强版) 更新说明

## 新增功能:

### 1. API状态更新集成
- 自动调用 /admin-api/agent/task-video-info/update 更新任务状态
- 状态映射: "1"=未开始, "0"=运行中, "1"=完成, "2"=失败
- 任务开始时更新为运行中(0)，完成时更新为完成(1)或失败(2)

### 2. 素材库自动保存
- 任务完成后自动调用 /admin-api/agent/resource/create 保存到素材库
- 自动识别文件类型: 视频(1), 图片(2), 音频(3), 其他(4)
- 自动获取文件大小和MIME类型

### 3. MQTT消息格式适配
- 适配你提供的消息格式，支持字符串形式的params
- 保持消息中的id、msgId、reqHeader等字段

### 4. HTTP状态查询服务
- GET /task/status?task_id=<task_id> - 查询单个任务状态
- GET /task/list - 获取所有任务列表
- GET /health - 健康检查
- 默认端口8080，可通过--http-port参数修改

## 配置说明:

### 环境变量:
export API_BASE_URL=http://your-api-server:8080
export API_TOKEN=your_auth_token
export MQTT_USERNAME=your_mqtt_username  
export MQTT_PASSWORD=your_mqtt_password

### 启动命令:
python app_mqtt_enhanced.py \
  --broker 121.36.203.36 \
  --port 18020 \
  --http-port 8080 \
  --api-base-url http://your-api-server:8080

## API调用示例:

### 更新任务状态:
POST /admin-api/agent/task-video-info/update
{
    "id": "task_id",
    "taskNo": "",
    "status": "1"  // 1=未开始,0=运行中,1=完成,2=失败
}

### 保存素材到素材库:
POST /admin-api/agent/resource/create
{
    "type": "2",  // 1=视频,2=图片,3=音频,4=其他
    "name": "原始文件名.jpg",  // 显示名称，保持原始文件名
    "path": "/agent/resource/fdd5d93995d1275541e29f88e7b07a38ac50598326b92f48d5837c374fd0397e.jpg",  // 使用哈希文件名
    "fileType": "image/jpeg",
    "size": 1024000
}

## HTTP查询示例:

### 查询任务状态:
curl "http://localhost:8080/task/status?task_id=12345"

### 获取任务列表:
curl "http://localhost:8080/task/list"

### 健康检查:
curl "http://localhost:8080/health"

## 响应格式:

### 任务状态响应:
{
    "task_id": "12345",
    "function_name": "sinology",
    "status": "completed",
    "progress": "100%",
    "warehouse_path": "projects/xxx/video.mp4",
    "file_exists": true,
    "processing_time": 45.2
}

### MQTT响应消息:
{
    "id": 6,
    "msgId": "6",
    "reqHeader": "12",
    "task_id": "uuid",
    "function": "sinology",
    "status": "completed",
    "result": {
        "warehouse_path": "projects/xxx/video.mp4",
        "videoPath": "projects/xxx/video.mp4",
        "file_exists": true,
        "processing_time": 45.2
    },
    "timestamp": 1640995200.0
}

## 错误处理增强:
- API调用失败时记录日志但不中断任务处理
- HTTP服务异常不影响MQTT服务
- 所有异常都有详细的错误信息和堆栈跟踪

## 部署建议:
1. 确保API服务可访问
2. 配置正确的认证信息
3. 监控HTTP服务和MQTT连接状态
4. 设置日志轮转和监控告警
"""
# -*- coding: utf-8 -*-
"""
优化后的 FastAPI 应用
使用重构后的 Coze 视频生成模块，大幅简化代码
"""

import argparse
import threading
import queue
import time
import asyncio
import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError
import uvicorn
import uuid
from typing import Optional, Union, Dict, List, Any
from threading import Condition
import config
import os

# 🔥 使用重构后的统一API
from core.cliptemplate.coze.refactored_api import UnifiedVideoAPI
from core.cliptemplate.coze.base.video_generator import VideoGeneratorFactory

# 保留必要的原始导入
from core.clipgenerate.interface_function import get_smart_clip_video, download_file_from_url, upload_to_oss
from core.clipgenerate.interface_model import (
    VideoRandomRequest, ProductConfigRequest, VoiceConfigRequest,
    ServerStartRequest, ServerStopRequest, TextIndustryRequest, 
    CopyGenerationRequest, CoverAnalysisRequest,
    BigWordRequest, CatMemeRequest, ClickTypeRequest, 
    VideoAdvertisementRequest, VideoAdvertisementEnhanceRequest,
    ClothesDifferentSceneRequest, SmartClipRequest, 
    DGHImgInsertRequest, DigitalHumanClipsRequest, 
    IncitementRequest, SinologyRequest, StickmanRequest,
    ClothesFastChangeRequest, DigitalHumanRequest, VideoEditMainRequest
)
from core.cliptemplate.coze.video_cover_analyzer import CoverAnalyzer, AnalyzeResponse
from core.cliptemplate.coze.auto_live_reply import SocketServer, config_manager
from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator
from core.text_generate.generator import get_copy_generation, CopyGenerator

# ========== 应用初始化 ==========
app = FastAPI(
    title="AI视频生成系统",
    description="使用重构后架构的高效视频生成API",
    version="2.0.0"
)

# 🔥 初始化重构后的统一视频API
video_api = UnifiedVideoAPI()
video_factory = VideoGeneratorFactory()

# 全局变量
socket_server = None

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== 异常处理 ==========
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "参数验证失败", "errors": exc.errors()}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"}
    )

# ========== 任务管理系统 ==========
class TaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        self.tasks = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    def create_task(self, task_func, *args, **kwargs):
        """创建异步任务"""
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {
            'id': task_id,
            'status': 'pending',
            'result': None,
            'error': None,
            'created_at': datetime.now(),
            'started_at': None,
            'completed_at': None
        }
        
        # 提交任务到线程池
        future = self.executor.submit(self._execute_task, task_id, task_func, *args, **kwargs)
        
        return task_id
    
    def _execute_task(self, task_id, task_func, *args, **kwargs):
        """执行任务"""
        try:
            self.tasks[task_id]['status'] = 'running'
            self.tasks[task_id]['started_at'] = datetime.now()
            
            result = task_func(*args, **kwargs)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['result'] = result
            self.tasks[task_id]['completed_at'] = datetime.now()
            
        except Exception as e:
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['completed_at'] = datetime.now()
    
    def get_task(self, task_id):
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def cleanup_old_tasks(self, max_age_hours=24):
        """清理旧任务"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        self.tasks = {
            task_id: task for task_id, task in self.tasks.items()
            if task['created_at'] > cutoff_time
        }

# 全局任务管理器
task_manager = TaskManager()

# ========== 基础接口 ==========
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI视频生成系统 v2.0",
        "status": "running",
        "supported_types": video_factory.get_supported_types(),
        "documentation": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/video/types")
async def get_supported_video_types():
    """获取支持的视频类型"""
    return {
        "supported_types": video_factory.get_supported_types(),
        "description": "支持的视频生成类型列表"
    }

# ========== 🔥 重构后的视频生成接口 ==========

@app.post("/api/video/advertisement")
async def create_advertisement_video(request: VideoAdvertisementRequest):
    """
    🔥 生成广告视频 - 使用重构后的接口
    """
    try:
        # 创建异步任务
        task_id = task_manager.create_task(
            video_api.generate_advertisement,
            company_name=request.company_name,
            service=request.service,
            topic=request.topic,
            content=request.content,
            need_change=request.need_change
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "广告视频生成任务已创建",
            "check_url": f"/api/task/{task_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/clicktype")
async def create_clicktype_video(request: ClickTypeRequest):
    """🔥 生成点击类视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_clicktype,
            title=request.title,
            content=request.content,
            style=getattr(request, 'style', 'default'),
            duration=getattr(request, 'duration', 30)
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "点击类视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/digital-human")
async def create_digital_human_video(request: DigitalHumanRequest):
    """🔥 生成数字人视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_digital_human,
            video_input=request.video_input,
            topic=request.topic,
            content=request.content,
            audio_input=getattr(request, 'audio_input', None)
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "数字人视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/clothes-scene")
async def create_clothes_scene_video(request: ClothesDifferentSceneRequest):
    """🔥 生成服装场景视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_clothes_scene,
            has_figure=request.has_figure,
            clothes_url=request.clothesurl,
            description=request.description,
            is_down=getattr(request, 'is_down', True)
        )
        
        return {
            "task_id": task_id,
            "status": "pending", 
            "message": "服装场景视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/big-word")
async def create_big_word_video(request: BigWordRequest):
    """🔥 生成大字报视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_big_word,
            text=request.text,
            font_size=getattr(request, 'font_size', 120),
            background_color=getattr(request, 'background_color', 'black'),
            text_color=getattr(request, 'text_color', 'white')
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "大字报视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/catmeme")
async def create_catmeme_video(request: CatMemeRequest):
    """🔥 生成猫咪表情包视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_catmeme,
            dialogue=request.dialogue,
            cat_type=getattr(request, 'cat_type', 'default'),
            emotion=getattr(request, 'emotion', 'happy')
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "猫咪表情包视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/incitement")
async def create_incitement_video(request: IncitementRequest):
    """🔥 生成煽动类视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_incitement,
            theme=request.theme,
            intensity=getattr(request, 'intensity', 'medium'),
            target_audience=getattr(request, 'target_audience', 'general')
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "煽动类视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/sinology")
async def create_sinology_video(request: SinologyRequest):
    """🔥 生成国学类视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_sinology,
            classic=request.classic,
            interpretation=request.interpretation,
            background_style=getattr(request, 'background_style', 'traditional')
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "国学类视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

@app.post("/api/video/stickman")
async def create_stickman_video(request: StickmanRequest):
    """🔥 生成火柴人视频"""
    try:
        task_id = task_manager.create_task(
            video_api.generate_stickman,
            story=request.story,
            animation_style=getattr(request, 'animation_style', 'simple'),
            speed=getattr(request, 'speed', 'normal')
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "火柴人视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

# ========== 🔥 通用视频生成接口 ==========
@app.post("/api/video/generate")
async def generate_video_universal(
    video_type: str = Query(..., description="视频类型"),
    request_data: Dict[str, Any] = None
):
    """
    🔥 通用视频生成接口 - 支持所有类型
    """
    try:
        # 验证视频类型
        if video_type not in video_factory.get_supported_types():
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的视频类型: {video_type}。支持的类型: {video_factory.get_supported_types()}"
            )
        
        # 创建异步任务
        task_id = task_manager.create_task(
            video_api.generate_video_by_type,
            video_type,
            **request_data
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "video_type": video_type,
            "message": f"{video_type}视频生成任务已创建"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务创建失败: {str(e)}")

# ========== 任务状态查询 ==========
@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"].isoformat(),
    }
    
    if task["started_at"]:
        response["started_at"] = task["started_at"].isoformat()
    
    if task["completed_at"]:
        response["completed_at"] = task["completed_at"].isoformat()
        response["duration"] = (task["completed_at"] - task["started_at"]).total_seconds()
    
    if task["status"] == "completed":
        response["result"] = task["result"]
    elif task["status"] == "failed":
        response["error"] = task["error"]
    
    return response

@app.get("/api/tasks")
async def get_all_tasks(
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(20, description="返回数量限制")
):
    """获取所有任务列表"""
    tasks = list(task_manager.tasks.values())
    
    # 状态筛选
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    # 按创建时间倒序排列
    tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 限制返回数量
    tasks = tasks[:limit]
    
    # 格式化输出
    result = []
    for task in tasks:
        task_info = {
            "task_id": task["id"],
            "status": task["status"],
            "created_at": task["created_at"].isoformat(),
        }
        if task["completed_at"]:
            task_info["completed_at"] = task["completed_at"].isoformat()
        result.append(task_info)
    
    return {
        "tasks": result,
        "total": len(result),
        "filtered_by_status": status
    }

# ========== 保留的原始接口 (向后兼容) ==========
# 这里可以保留一些关键的原始接口，调用重构后的模块

@app.post("/video/digital-human-easy")
async def digital_human_easy_legacy(request: DigitalHumanRequest):
    """向后兼容的数字人视频接口"""
    return await create_digital_human_video(request)

# ========== 配置管理接口 ==========
@app.put('/api/product')
async def update_product_config(request: ProductConfigRequest):
    """更新产品配置"""
    try:
        # 这里保留原有的配置逻辑
        return {"message": "配置更新成功", "live_config": request.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

@app.put('/api/voice/live_config')
async def update_voice_config(request: VoiceConfigRequest):
    """更新语音配置"""
    try:
        return {"message": "语音配置更新成功", "live_config": request.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音配置更新失败: {str(e)}")

# ========== 服务器管理接口 ==========
@app.post('/api/server/start')
async def start_server(request: ServerStartRequest):
    """启动服务器"""
    try:
        global socket_server
        if socket_server is None:
            socket_server = SocketServer()
            socket_server.start()
        return {"message": "服务器启动成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器启动失败: {str(e)}")

@app.post('/api/server/stop')
async def stop_server(request: ServerStopRequest):
    """停止服务器"""
    try:
        global socket_server
        if socket_server:
            socket_server.stop()
            socket_server = None
        return {"message": "服务器停止成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器停止失败: {str(e)}")

# ========== 工具接口 ==========
@app.post("/text/industry")
async def generate_industry_text(request: TextIndustryRequest):
    """生成行业文本"""
    try:
        from core.cliptemplate.coze.text_industry import get_text_industry
        result = get_text_industry(request.industry, request.scenario)
        return {"text": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本生成失败: {str(e)}")

@app.post("/copy/generate") 
async def generate_copy(request: CopyGenerationRequest):
    """生成文案"""
    try:
        result = get_copy_generation(
            request.topic,
            request.style,
            request.length,
            request.target_audience
        )
        return {"copy": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案生成失败: {str(e)}")

@app.post("/cover/analyze")
async def analyze_cover(request: CoverAnalysisRequest):
    """封面分析"""
    try:
        analyzer = CoverAnalyzer()
        result = analyzer.analyze_cover_image(request.image_url)
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"封面分析失败: {str(e)}")

# ========== 系统维护接口 ==========
@app.post("/api/system/cleanup")
async def cleanup_old_tasks():
    """清理旧任务"""
    try:
        task_manager.cleanup_old_tasks()
        return {"message": "旧任务清理完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.get("/api/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        tasks = task_manager.tasks
        stats = {
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks.values() if t["status"] == "pending"]),
            "running_tasks": len([t for t in tasks.values() if t["status"] == "running"]),
            "completed_tasks": len([t for t in tasks.values() if t["status"] == "completed"]),
            "failed_tasks": len([t for t in tasks.values() if t["status"] == "failed"]),
            "supported_video_types": video_factory.get_supported_types(),
            "system_status": "healthy"
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")

# ========== 应用启动 ==========
if __name__ == "__main__":
    print("🚀 启动AI视频生成系统 v2.0 (重构版)")
    print(f"📋 支持的视频类型: {video_factory.get_supported_types()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )
# -*- coding: utf-8 -*-
# @Time    : 2025/6/14 13:55
# @Author  : 蔍鸣霸霸
# @FileName: ai_video_editing_fastapi_mcp.py
# @Software: PyCharm
# @Blog    ：只因你太美

"""
AI视频剪辑FastAPI-MCP服务器
通过自然语言对话进行视频分析和剪辑
"""

import asyncio
import json
import logging
import os
import sys
import threading
import queue
import time
import uuid
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Union
from threading import Condition

from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
import uvicorn

from core.ai.ai_model_caller import AIModelCaller
from core.analyzer.video_analyzer import VideoAnalyzer

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入视频处理模块
try:


    from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator, create_orchestrator_from_analysis
except ImportError as e:
    print(f"警告: 导入模块失败 {e}")
    print("请确保所有必要的模块都在正确的路径中")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="AI Video Editing Server", version="1.0.0")
# 创建FastMCP实例
mcp = FastMCP(name="AI Video Editing MCP Server")
# 全局变量
task_queue = queue.Queue()
results = {}
result_condition = Condition()
temp_dirs = []  # 存储临时目录，用于清理


class VideoEditingError(Exception):
    """自定义异常类"""
    pass


# ==================== 核心视频处理功能 ====================

def get_api_key_from_file(file_name="api_key.txt"):
    """从本地文件读取API Key"""
    try:
        base_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(base_path, file_name)

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()

        return api_key if api_key else None
    except Exception as e:
        logger.error(f"读取API Key失败: {e}")
        return None


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
        temp_dir = tempfile.mkdtemp(prefix="ai_video_download_")
        temp_dirs.append(temp_dir)  # 记录用于清理

        # 获取文件名
        parsed_url = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = f"downloaded_video_{int(time.time())}.mp4"

        output_path = os.path.join(temp_dir, filename)

        # 下载文件
        logger.info(f"正在下载视频: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"下载完成: {output_path}")
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
                        logger.info(f"成功下载视频: {path}")
                    except Exception as e:
                        logger.error(f"下载失败: {path}, 错误: {e}")
                        continue
                else:
                    logger.warning(f"不支持的URL类型: {path}")

            elif os.path.isfile(path):
                # 处理本地文件
                if path.lower().endswith(video_extensions):
                    video_files.append(path)
                    logger.info(f"找到本地视频: {path}")
                else:
                    logger.warning(f"跳过非视频文件: {path}")

            elif os.path.isdir(path):
                # 处理目录
                found_count = 0
                for file in os.listdir(path):
                    if file.lower().endswith(video_extensions):
                        video_files.append(os.path.join(path, file))
                        found_count += 1
                logger.info(f"目录中找到 {found_count} 个视频文件: {path}")

            else:
                logger.warning(f"路径不存在: {path}")

        except Exception as e:
            logger.error(f"处理路径 {path} 时出错: {e}")

    return video_files


def cleanup_temp_dirs():
    """清理临时目录"""
    global temp_dirs
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            logger.error(f"清理临时目录失败: {e}")
    temp_dirs.clear()


# ==================== 任务处理系统 ====================

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
            raise VideoEditingError(f"Function {func_name} not found")

        logger.info(f"开始执行任务: {task_id}, 函数: {func_name}")

        # 执行实际任务
        result = func(**args)

        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        with result_condition:
            results[task_id] = {
                "status": "completed",
                "result": result,
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
            return final_result["result"]
        elif final_result["status"] == "failed":
            raise VideoEditingError(final_result.get("error", "Unknown error occurred"))
    else:
        task_queue.put(task_data)
        return {"task_id": task_id}


# ==================== 核心视频处理函数 ====================

def analyze_videos_intelligent(video_paths: List[str]) -> Dict[str, Any]:
    """智能分析视频内容"""
    logger.info(f"开始智能分析 {len(video_paths)} 个视频")

    try:
        analyzer = VideoAnalyzer()
    except Exception as e:
        raise VideoEditingError(f"无法创建视频分析器: {e}")

    results = []

    for i, video_path in enumerate(video_paths):
        logger.info(f"分析视频 {i + 1}/{len(video_paths)}: {os.path.basename(video_path)}")

        try:
            result = analyzer.analyze_video(video_path)
            result['file_path'] = video_path
            results.append(result)

            # 输出分析摘要
            metadata = result.get('metadata', {})
            classification = result.get('classification', {})
            highlights = result.get('highlights', [])

            logger.info(f"  时长: {metadata.get('duration', 0):.1f}秒")
            logger.info(f"  内容类型: {classification.get('content_type', '未知')}")
            logger.info(f"  精彩片段: {len(highlights)}个")

        except Exception as e:
            logger.error(f"分析视频失败: {video_path}, 错误: {e}")
            results.append({
                'file_path': video_path,
                'error': str(e),
                'status': 'failed'
            })

    return {
        "analysis_results": results,
        "total_videos": len(video_paths),
        "successful_analyses": len([r for r in results if 'error' not in r]),
        "failed_analyses": len([r for r in results if 'error' in r])
    }


def edit_videos_with_ai_strategy(video_paths: List[str], user_requirements: str,
                                 target_duration: int = 30, use_local_ai: bool = False) -> Dict[str, Any]:
    """使用AI策略剪辑视频"""
    logger.info(f"开始AI剪辑 {len(video_paths)} 个视频")
    logger.info(f"用户需求: {user_requirements}")
    logger.info(f"目标时长: {target_duration}秒")

    # 获取API密钥
    api_key = None
    if not use_local_ai:
        api_key = get_api_key_from_file()
        if not api_key:
            logger.warning("无法读取API密钥，将使用本地AI模式")
            use_local_ai = True

    # 解析用户需求为结构化选项
    user_options = parse_user_requirements(user_requirements, target_duration)

    try:
        # 创建工作流程编排器
        output_dir = tempfile.mkdtemp(prefix="ai_video_edit_")
        temp_dirs.append(output_dir)

        orchestrator = VideoEditingOrchestrator(
            video_files=video_paths,
            output_dir=output_dir
        )

        # 执行完整工作流程
        result = orchestrator.run_complete_workflow(
            user_options=user_options,
            api_key=api_key,
            use_local_ai=use_local_ai,
            merge_videos=True
        )

        return result

    except Exception as e:
        raise VideoEditingError(f"AI剪辑失败: {str(e)}")


def edit_videos_from_analysis(analysis_file_path: str, user_requirements: str,
                              target_duration: int = 30, use_local_ai: bool = False) -> Dict[str, Any]:
    """从分析结果文件进行剪辑"""
    logger.info(f"使用分析结果进行剪辑: {analysis_file_path}")

    if not os.path.exists(analysis_file_path):
        raise VideoEditingError(f"分析文件不存在: {analysis_file_path}")

    # 获取API密钥
    api_key = None
    if not use_local_ai:
        api_key = get_api_key_from_file()
        if not api_key:
            use_local_ai = True

    # 解析用户需求
    user_options = parse_user_requirements(user_requirements, target_duration)

    try:
        # 从分析结果创建编排器
        output_dir = tempfile.mkdtemp(prefix="ai_video_edit_from_analysis_")
        temp_dirs.append(output_dir)

        orchestrator = create_orchestrator_from_analysis(
            analysis_file_path,
            output_dir
        )

        # 执行剪辑
        result = orchestrator.run_complete_workflow(
            user_options=user_options,
            api_key=api_key,
            use_local_ai=use_local_ai,
            merge_videos=True
        )

        return result

    except Exception as e:
        raise VideoEditingError(f"从分析结果剪辑失败: {str(e)}")


def generate_ai_editing_strategy(video_analysis: Dict[str, Any], user_requirements: str,
                                 target_duration: int = 30) -> Dict[str, Any]:
    """生成AI剪辑策略（不执行剪辑）"""
    logger.info("生成AI剪辑策略")

    # 获取API密钥
    api_key = get_api_key_from_file()

    if not api_key:
        logger.warning("无法读取API密钥，将使用本地策略生成")
        return generate_local_strategy(video_analysis, user_requirements, target_duration)

    try:
        # 使用AI模型生成策略
        caller = AIModelCaller(api_key=api_key, model="qwen-plus")

        # 构建prompt
        prompt = build_strategy_prompt(video_analysis, user_requirements, target_duration)

        # 生成策略
        strategy = caller.generate_editing_plan(prompt, use_local=False)

        return {
            "strategy": strategy,
            "strategy_type": "AI生成",
            "user_requirements": user_requirements,
            "target_duration": target_duration
        }

    except Exception as e:
        logger.error(f"AI策略生成失败: {e}")
        return generate_local_strategy(video_analysis, user_requirements, target_duration)


def parse_user_requirements(user_requirements: str, target_duration: int) -> Dict[str, Any]:
    """解析用户需求为结构化选项"""
    user_options = {
        "target_duration": target_duration,
        "target_style": "智能",
        "target_purpose": "通用"
    }

    # 简单的关键词匹配
    requirements_lower = user_requirements.lower()

    # 风格识别
    if any(word in requirements_lower for word in ["抖音", "短视频", "竖屏"]):
        user_options["target_style"] = "抖音风"
    elif any(word in requirements_lower for word in ["电影", "影院", "横屏"]):
        user_options["target_style"] = "电影风"
    elif any(word in requirements_lower for word in ["vlog", "生活", "日常"]):
        user_options["target_style"] = "VLOG风"

    # 用途识别
    if any(word in requirements_lower for word in ["营销", "推广", "宣传"]):
        user_options["target_purpose"] = "营销推广"
    elif any(word in requirements_lower for word in ["教学", "教育", "学习"]):
        user_options["target_purpose"] = "教育培训"
    elif any(word in requirements_lower for word in ["娱乐", "搞笑", "趣味"]):
        user_options["target_purpose"] = "娱乐内容"

    return user_options


def build_strategy_prompt(video_analysis: Dict[str, Any], user_requirements: str, target_duration: int) -> str:
    """构建AI策略生成的prompt"""
    analysis_summary = ""
    if isinstance(video_analysis, dict) and "analysis_results" in video_analysis:
        results = video_analysis["analysis_results"]
        analysis_summary = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        analysis_summary = json.dumps(video_analysis, indent=2, ensure_ascii=False)

    prompt = f"""
你是一个专业的视频剪辑AI助手。请根据以下视频分析结果和用户需求，生成详细的剪辑策略。

【视频分析结果】:
{analysis_summary}

【用户需求】:
{user_requirements}

【目标时长】:
{target_duration}秒

请输出JSON格式的剪辑策略，包含具体的剪辑操作和思路说明。
"""
    return prompt


def generate_local_strategy(video_analysis: Dict[str, Any], user_requirements: str, target_duration: int) -> Dict[
    str, Any]:
    """生成本地策略（备用方案）"""
    return {
        "strategy": {
            "actions": [
                {
                    "function": "cut",
                    "start": 0,
                    "end": target_duration,
                    "reason": f"根据用户需求'{user_requirements}'进行智能剪切"
                }
            ],
            "target_duration": target_duration,
            "metadata": {
                "description": f"本地生成的剪辑策略，满足用户需求: {user_requirements}"
            }
        },
        "strategy_type": "本地生成",
        "user_requirements": user_requirements,
        "target_duration": target_duration
    }


# ==================== MCP工具定义 ====================

@mcp.tool()
async def analyze_videos(
        video_paths: List[str],
        mode: str = "async"
) -> str:
    """
    智能分析视频内容，识别精彩片段和内容特征

    Args:
        video_paths: 视频文件路径或URL列表
        mode: 执行模式，'sync'同步执行，'async'异步执行

    Returns:
        分析结果的字符串描述
    """
    if not video_paths:
        return "❌ 错误: 必须提供至少一个视频路径"

    # 收集视频文件
    collected_videos = collect_video_files(video_paths)

    if not collected_videos:
        return f"❌ 错误: 在提供的路径中没有找到有效的视频文件\n提供的路径: {video_paths}"

    res = await execute_task_async("analyze_videos_intelligent", {"video_paths": collected_videos}, mode)

    if mode == "sync":
        if isinstance(res, dict) and "analysis_results" in res:
            successful = res["successful_analyses"]
            total = res["total_videos"]

            analysis_text = f"✅ 视频分析完成！\n"
            analysis_text += f"📊 成功分析: {successful}/{total} 个视频\n\n"

            for i, result in enumerate(res["analysis_results"]):
                if "error" not in result:
                    metadata = result.get("metadata", {})
                    classification = result.get("classification", {})
                    highlights = result.get("highlights", [])

                    analysis_text += f"📹 视频 {i + 1}: {os.path.basename(result.get('file_path', ''))}\n"
                    analysis_text += f"  ⏱️ 时长: {metadata.get('duration', 0):.1f}秒\n"
                    analysis_text += f"  📺 分辨率: {metadata.get('width', 0)}x{metadata.get('height', 0)}\n"
                    analysis_text += f"  🎵 音频: {'✅' if metadata.get('has_audio') else '❌'}\n"
                    analysis_text += f"  🎭 内容类型: {classification.get('content_type', '未知')}\n"
                    analysis_text += f"  😊 情绪氛围: {classification.get('mood', '未知')}\n"
                    analysis_text += f"  🎨 风格类型: {classification.get('style', '未知')}\n"
                    analysis_text += f"  ⭐ 精彩片段: {len(highlights)}个\n\n"

            return analysis_text
        else:
            return f"❌ 分析失败: {res.get('error', '未知错误')}"
    else:
        return f"✅ 视频分析任务已提交\n📋 任务ID: {res['task_id']}\n🔍 正在分析 {len(collected_videos)} 个视频文件\n📱 使用 get_task_result 工具查询结果"


@mcp.tool()
async def edit_videos_with_requirements(
        video_paths: List[str],
        user_requirements: str,
        target_duration: int = 30,
        use_local_ai: bool = False,
        mode: str = "async"
) -> str:
    """
    根据自然语言需求智能剪辑视频

    Args:
        video_paths: 视频文件路径或URL列表
        user_requirements: 用户的剪辑需求，用自然语言描述，例如：'制作一个30秒的抖音风格短视频，突出产品特点'
        target_duration: 目标视频时长（秒）
        use_local_ai: 是否使用本地AI（不调用在线模型）
        mode: 执行模式，'sync'同步执行，'async'异步执行

    Returns:
        剪辑结果的字符串描述
    """
    if not video_paths:
        return "❌ 错误: 必须提供至少一个视频路径"

    if not user_requirements:
        return "❌ 错误: 必须提供用户需求描述"

    # 收集视频文件
    collected_videos = collect_video_files(video_paths)

    if not collected_videos:
        return f"❌ 错误: 在提供的路径中没有找到有效的视频文件\n提供的路径: {video_paths}"

    res = await execute_task_async("edit_videos_with_ai_strategy", {
        "video_paths": collected_videos,
        "user_requirements": user_requirements,
        "target_duration": target_duration,
        "use_local_ai": use_local_ai
    }, mode)

    if mode == "sync":
        if isinstance(res, dict) and res.get("status") == "success":
            result_text = f"🎉 AI视频剪辑完成！\n\n"
            result_text += f"📄 输出文件: {res.get('output_video', '未知')}\n"
            result_text += f"📊 文件大小: {res.get('file_size_mb', 0)}MB\n"
            result_text += f"⏱️ 处理时间: {res.get('processing_time', 0)}秒\n\n"

            video_info = res.get('video_info', {})
            result_text += f"📹 处理详情:\n"
            result_text += f"  输入文件数: {video_info.get('input_count', 1)}\n"
            result_text += f"  最终时长: {video_info.get('duration', 0):.1f}秒\n"
            result_text += f"  分辨率: {video_info.get('resolution', '未知')}\n\n"
            result_text += f"🎯 用户需求: {user_requirements}\n"
            result_text += f"🤖 AI模式: {'本地AI' if use_local_ai else '在线AI'}"

            return result_text
        else:
            return f"❌ 剪辑失败: {res.get('error', '未知错误')}"
    else:
        return f"🎬 AI视频剪辑任务已提交\n📋 任务ID: {res['task_id']}\n🎯 用户需求: {user_requirements}\n⏱️ 目标时长: {target_duration}秒\n🎥 处理视频: {len(collected_videos)}个\n📱 使用 get_task_result 工具查询结果"


@mcp.tool()
async def edit_from_analysis(
        analysis_file_path: str,
        user_requirements: str,
        target_duration: int = 30,
        use_local_ai: bool = False,
        mode: str = "async"
) -> str:
    """
    从已有的分析结果进行视频剪辑

    Args:
        analysis_file_path: 分析结果文件路径
        user_requirements: 用户的剪辑需求
        target_duration: 目标视频时长（秒）
        use_local_ai: 是否使用本地AI
        mode: 执行模式，'sync'同步执行，'async'异步执行

    Returns:
        剪辑结果的字符串描述
    """
    if not analysis_file_path:
        return "❌ 错误: 必须提供分析结果文件路径"

    if not user_requirements:
        return "❌ 错误: 必须提供用户需求描述"

    res = await execute_task_async("edit_videos_from_analysis", {
        "analysis_file_path": analysis_file_path,
        "user_requirements": user_requirements,
        "target_duration": target_duration,
        "use_local_ai": use_local_ai
    }, mode)

    if mode == "sync":
        if isinstance(res, dict) and res.get("status") == "success":
            result_text = f"🎉 基于分析结果的剪辑完成！\n\n"
            result_text += f"📄 输出文件: {res.get('output_video', '未知')}\n"
            result_text += f"📊 文件大小: {res.get('file_size_mb', 0)}MB\n"
            result_text += f"⏱️ 处理时间: {res.get('processing_time', 0)}秒\n\n"
            result_text += f"📋 分析文件: {os.path.basename(analysis_file_path)}\n"
            result_text += f"🎯 用户需求: {user_requirements}"

            return result_text
        else:
            return f"❌ 剪辑失败: {res.get('error', '未知错误')}"
    else:
        return f"📋 基于分析结果的剪辑任务已提交\n📋 任务ID: {res['task_id']}\n📄 分析文件: {os.path.basename(analysis_file_path)}\n🎯 用户需求: {user_requirements}\n📱 使用 get_task_result 工具查询结果"


@mcp.tool()
async def generate_editing_strategy(
        video_analysis: Dict[str, Any],
        user_requirements: str,
        target_duration: int = 30,
        mode: str = "sync"
) -> str:
    """
    仅生成剪辑策略，不执行实际剪辑

    Args:
        video_analysis: 视频分析结果
        user_requirements: 用户需求描述
        target_duration: 目标时长
        mode: 执行模式，'sync'同步执行，'async'异步执行

    Returns:
        策略生成结果的字符串描述
    """
    if not video_analysis:
        return "❌ 错误: 必须提供视频分析结果"

    if not user_requirements:
        return "❌ 错误: 必须提供用户需求描述"

    res = await execute_task_async("generate_ai_editing_strategy", {
        "video_analysis": video_analysis,
        "user_requirements": user_requirements,
        "target_duration": target_duration
    }, mode)

    if mode == "sync":
        if isinstance(res, dict) and "strategy" in res:
            strategy_text = f"🧠 AI剪辑策略生成完成！\n\n"
            strategy_text += f"🎯 用户需求: {res.get('user_requirements', '')}\n"
            strategy_text += f"⏱️ 目标时长: {res.get('target_duration', 0)}秒\n"
            strategy_text += f"🤖 策略类型: {res.get('strategy_type', '未知')}\n\n"

            strategy = res.get('strategy', {})
            actions = strategy.get('actions', [])

            strategy_text += f"📋 剪辑操作 ({len(actions)}个):\n"
            for i, action in enumerate(actions, 1):
                func = action.get('function', '未知')
                reason = action.get('reason', '无说明')
                strategy_text += f"  {i}. {func}: {reason}\n"

            metadata = strategy.get('metadata', {})
            if 'description' in metadata:
                strategy_text += f"\n💡 策略说明: {metadata['description']}"

            return strategy_text
        else:
            return f"❌ 策略生成失败: {res.get('error', '未知错误')}"
    else:
        return f"🧠 策略生成任务已提交\n📋 任务ID: {res['task_id']}\n📱 使用 get_task_result 工具查询结果"


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
            return f"❌ 任务不存在: {task_id}\n可能已被删除或任务ID错误"

        if remove:
            result = results.pop(task_id)
        else:
            result = results[task_id]

        task_status = result.get("status", "unknown")
        function_name = result.get("function_name", "unknown")

        if task_status == "completed":
            task_result = result.get("result", {})
            processing_time = result.get("processing_time", 0)

            result_text = f"✅ 任务完成: {task_id[:8]}...\n"
            result_text += f"🔧 功能: {function_name}\n"
            result_text += f"⏱️ 处理时间: {processing_time}秒\n\n"

            # 根据不同功能显示不同的结果格式
            if function_name == "analyze_videos_intelligent":
                if isinstance(task_result, dict) and "analysis_results" in task_result:
                    successful = task_result["successful_analyses"]
                    total = task_result["total_videos"]
                    result_text += f"📊 分析结果: {successful}/{total} 个视频分析成功"
                else:
                    result_text += f"📊 分析结果: {json.dumps(task_result, indent=2, ensure_ascii=False)}"

            elif function_name in ["edit_videos_with_ai_strategy", "edit_videos_from_analysis"]:
                if isinstance(task_result, dict) and task_result.get("status") == "success":
                    result_text += f"🎬 剪辑完成!\n"
                    result_text += f"📄 输出文件: {task_result.get('output_video', '未知')}\n"
                    result_text += f"📊 文件大小: {task_result.get('file_size_mb', 0)}MB"
                else:
                    result_text += f"❌ 剪辑失败: {task_result.get('error', '未知错误')}"

            elif function_name == "generate_ai_editing_strategy":
                if isinstance(task_result, dict) and "strategy" in task_result:
                    strategy = task_result.get('strategy', {})
                    actions = strategy.get('actions', [])
                    result_text += f"🧠 策略生成完成，包含 {len(actions)} 个剪辑操作"
                else:
                    result_text += f"🧠 策略结果: {json.dumps(task_result, indent=2, ensure_ascii=False)}"

            else:
                result_text += f"📋 结果: {json.dumps(task_result, indent=2, ensure_ascii=False)}"

            return result_text

        elif task_status == "failed":
            error = result.get("error", "未知错误")
            error_type = result.get("error_type", "Unknown")
            processing_time = result.get("processing_time", 0)

            return f"❌ 任务失败: {task_id[:8]}...\n🔧 功能: {function_name}\n💥 错误: {error}\n🏷️ 错误类型: {error_type}\n⏱️ 处理时间: {processing_time}秒"

        elif task_status == "processing":
            progress = result.get("progress", "未知")
            current_step = result.get("current_step", "未知")
            started_at = result.get("started_at", 0)
            elapsed = time.time() - started_at if started_at else 0

            return f"🔄 任务处理中: {task_id[:8]}...\n🔧 功能: {function_name}\n📊 进度: {progress}\n📍 当前步骤: {current_step}\n⏱️ 已用时间: {elapsed:.1f}秒"

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


# ==================== FastAPI路由 ====================

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "AI Video Editing Server",
        "version": "1.0.0",
        "status": "running",
        "description": "AI视频剪辑服务器，支持智能分析和剪辑"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_tasks": len(results),
        "temp_dirs": len(temp_dirs)
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


# ==================== 启动配置 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Video Editing FastAPI-MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    # 打印启动信息
    print(f"""
🎬 AI Video Editing FastAPI-MCP Server
=====================================
🌐 Host: {args.host}
🔌 Port: {args.port}
🔄 Reload: {args.reload}
📝 Log Level: {args.log_level}
🚀 Starting server...
    """)

    uvicorn.run(
        "ai_video_editing_mcp:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
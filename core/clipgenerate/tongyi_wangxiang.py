# -*- coding: utf-8 -*-
"""
通义万相官方API处理函数 - 修正版
严格按照官方API文档实现
"""

import os
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests
from typing import Dict, List, Optional, Any, Union
from get_api_key import get_api_key_from_file


class WanXiangAPIHandler:
    """通义万相API处理器"""

    def __init__(self, api_key: str = None):
        self.api_key = get_api_key_from_file()
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, url: str, **kwargs) -> Dict:
        """统一请求处理"""
        try:
            print("请求体")
            print(kwargs)
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")

    def _wait_for_task(self, task_id: str, max_wait_time: int = 300) -> Dict:
        """等待异步任务完成"""
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            url = f"{self.base_url}/tasks/{task_id}"
            result = self._make_request("GET", url, headers=self.headers)

            task_status = result.get("output", {}).get("task_status")

            if task_status == "SUCCEEDED":
                return result
            elif task_status == "FAILED":
                error_msg = result.get("output", {}).get("message", "任务执行失败")
                raise Exception(f"任务失败: {error_msg}")

            time.sleep(5)  # 等待5秒后重试

        raise Exception(f"任务超时，等待时间超过{max_wait_time}秒")


# ============ 创意海报生成 ============

def get_creative_poster(title: str, sub_title: str = None, body_text: str = None,
                        prompt_text_zh: str = None, wh_ratios: str = "竖版",
                        lora_name: str = None, lora_weight: float = 0.8,
                        ctrl_ratio: float = 0.7, ctrl_step: float = 0.7,
                        generate_mode: str = "generate", generate_num: int = 1,
                        auxiliary_parameters: str = None) -> str:
    """
    创意海报生成 - 官方API结构

    Args:
        title: 海报标题
        sub_title: 海报副标题
        body_text: 海报正文
        prompt_text_zh: 中文提示词
        wh_ratios: 宽高比例 (竖版/横版)
        lora_name: 风格名称
        lora_weight: 风格权重
        ctrl_ratio: 控制比例
        ctrl_step: 控制步数
        generate_mode: 生成模式 (generate/sr/hrf)
        generate_num: 生成数量
        auxiliary_parameters: 辅助参数

    Returns:
        创意海报图片URL
    """
    print(f"🎨 [创意海报] 开始生成:")
    print(f"   标题: {title}")
    print(f"   副标题: {sub_title}")
    print(f"   风格: {lora_name}")

    handler = WanXiangAPIHandler()

    # 构建input参数
    input_data = {
        "title": title,
        "wh_ratios": wh_ratios,
        "generate_mode": generate_mode,
        "generate_num": generate_num
    }

    # 添加可选参数
    if sub_title:
        input_data["sub_title"] = sub_title

    if body_text:
        input_data["body_text"] = body_text

    if prompt_text_zh:
        input_data["prompt_text_zh"] = prompt_text_zh

    if lora_name:
        input_data["lora_name"] = lora_name
        input_data["lora_weight"] = lora_weight
        input_data["ctrl_ratio"] = ctrl_ratio
        input_data["ctrl_step"] = ctrl_step

    if auxiliary_parameters:
        input_data["auxiliary_parameters"] = auxiliary_parameters

    task_data = {
        "model": "wanx-poster-generation-v1",
        "input": input_data,
        "parameters": {}
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    # 使用官方端点
    url = f"{handler.base_url}/services/aigc/text2image/image-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    # 等待任务完成
    print("⏳ 等待创意海报生成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)
    print(final_result)
    # 提取结果
    image_url_result = final_result.get("output", {}).get("render_urls", [])

    if not image_url_result:
        raise Exception("未获取到创意海报图片URL")

    print(f"🎉 创意海报生成完成: {image_url_result}")
    return image_url_result


# ============ 文生图系列 ============

def get_text_to_image_v2(prompt: str, model: str = "wanx2.1-t2i-turbo",
                         negative_prompt: str = None, size: str = "1024*1024",
                         n: int = 1, seed: int = None, prompt_extend: bool = True,
                         watermark: bool = False) -> str:
    """
    通义万相文生图V2版 - 官方API结构

    Args:
        prompt: 正向提示词
        model: 模型名称 (wanx2.1-t2i-turbo, wanx2.1-t2i-plus, wanx2.0-t2i-turbo)
        negative_prompt: 反向提示词
        size: 图像尺寸
        n: 生成图片数量
        seed: 随机种子
        prompt_extend: 是否启用智能改写
        watermark: 是否添加水印

    Returns:
        生成的图片URL
    """
    print(f"🎨 [文生图V2] 开始生成图片:")
    print(f"   模型: {model}")
    print(f"   提示词: {prompt}")
    print(f"   尺寸: {size}")

    handler = WanXiangAPIHandler()

    # 构建input参数
    input_data = {
        "prompt": prompt
    }

    if negative_prompt:
        input_data["negative_prompt"] = negative_prompt

    # 构建parameters参数
    parameters_data = {
        "size": size,
        "n": n,
        "prompt_extend": prompt_extend,
        "watermark": watermark
    }

    if seed:
        parameters_data["seed"] = seed

    task_data = {
        "model": model,
        "input": input_data,
        "parameters": parameters_data
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/text2image/image-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    # 等待任务完成
    print("⏳ 等待任务完成...")
    final_result = handler._wait_for_task(task_id)

    # 提取结果
    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url = results[0].get("url")
    if not image_url:
        raise Exception("未获取到图片URL")

    print(f"🎉 文生图完成: {image_url}")
    return image_url


def get_text_to_image_v1(prompt: str, style: str = "<auto>",
                         negative_prompt: str = None, size: str = "1024*1024",
                         n: int = 1, seed: int = None, ref_img: str = None,
                         ref_strength: float = 0.5, ref_mode: str = "repaint") -> str:
    """
    通义万相文生图V1版 - 官方API结构

    Args:
        prompt: 正向提示词
        style: 图片风格
        negative_prompt: 反向提示词
        size: 图像尺寸
        n: 生成图片数量
        seed: 随机种子
        ref_img: 参考图片URL
        ref_strength: 参考强度
        ref_mode: 参考模式 (repaint/refonly)

    Returns:
        生成的图片URL
    """
    print(f"🎨 [文生图V1] 开始生成图片:")
    print(f"   提示词: {prompt}")
    print(f"   风格: {style}")
    print(f"   尺寸: {size}")

    handler = WanXiangAPIHandler()

    # 构建input参数
    input_data = {
        "prompt": prompt
    }

    if negative_prompt:
        input_data["negative_prompt"] = negative_prompt

    if ref_img:
        input_data["ref_img"] = ref_img

    # 构建parameters参数
    parameters_data = {
        "style": style,
        "size": size,
        "n": n,
        "ref_strength": ref_strength,
        "ref_mode": ref_mode
    }

    if seed:
        parameters_data["seed"] = seed

    task_data = {
        "model": "wanx-v1",
        "input": input_data,
        "parameters": parameters_data
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/text2image/image-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    # 等待任务完成
    print("⏳ 等待任务完成...")
    final_result = handler._wait_for_task(task_id)

    # 提取结果
    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url = results[0].get("url")
    if not image_url:
        raise Exception("未获取到图片URL")

    print(f"🎉 文生图完成: {image_url}")
    return image_url


# ============ 视频生成系列 ============

def get_text_to_video(prompt: str, model: str = "wanx2.1-t2v-turbo",
                      size: str = "1280*720") -> str:
    """
    文生视频 - 官方API结构

    Args:
        prompt: 视频描述提示词
        model: 模型名称
        size: 视频尺寸

    Returns:
        生成的视频URL
    """
    print(f"🎬 [文生视频] 开始生成:")
    print(f"   模型: {model}")
    print(f"   提示词: {prompt}")
    print(f"   尺寸: {size}")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": model,
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "size": size
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/text2video/video-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待文生视频完成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=1800)

    video_url = final_result.get("output", {}).get("video_url")
    if not video_url:
        raise Exception("未获取到生成的视频URL")

    print(f"🎉 文生视频完成: {video_url}")
    return video_url


def get_image_to_video(img_url: str, prompt: str, model: str = "wanx2.1-i2v-turbo",
                       resolution: str = "720P", template: str = None) -> str:
    """
    图生视频 - 官方API结构

    Args:
        img_url: 首帧图片URL
        prompt: 运动描述
        model: 模型名称
        resolution: 分辨率档位
        template: 特效模板

    Returns:
        生成的视频URL
    """
    print(f"🎬 [图生视频] 开始生成:")
    print(f"   模型: {model}")
    print(f"   图片: {img_url}")
    print(f"   提示词: {prompt}")

    handler = WanXiangAPIHandler()

    input_data = {
        "img_url": img_url,
        "prompt": prompt
    }

    parameters_data = {
        "resolution": resolution
    }

    if template:
        parameters_data["template"] = template

    task_data = {
        "model": model,
        "input": input_data,
        "parameters": parameters_data
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/video-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待图生视频完成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=1800)

    video_url = final_result.get("output", {}).get("video_url")
    if not video_url:
        raise Exception("未获取到生成的视频URL")

    print(f"🎉 图生视频完成: {video_url}")
    return video_url


def get_image_to_video_advanced(first_frame_url: str, last_frame_url: str,
                                prompt: str, duration: int = 5, size: str = "1280*720") -> str:
    """
    图生视频-基于首尾帧 - 修复后的官方API结构

    Args:
        first_frame_url: 首帧图片URL
        last_frame_url: 尾帧图片URL
        prompt: 视频生成提示词
        duration: 视频时长(秒) - 注意：API可能不支持此参数
        size: 视频尺寸 - 将转换为resolution格式

    Returns:
        生成的视频URL
    """
    print(f"🎬 [图生视频-首尾帧] 开始生成:")
    print(f"   首帧图: {first_frame_url}")
    print(f"   尾帧图: {last_frame_url}")
    print(f"   提示词: {prompt}")
    print(f"   时长: {duration}秒 (可能被忽略)")

    handler = WanXiangAPIHandler()

    # 转换尺寸格式
    resolution_map = {
        "1280*720": "720P",
        "1920*1080": "1080P",
        "1024*1024": "1024x1024",
        "720*1280": "720x1280"  # 竖屏
    }
    resolution = resolution_map.get(size, "720P")  # 默认720P

    print(f"   分辨率: {resolution}")

    # 按照官方API格式构建请求
    task_data = {
        "model": "wanx2.1-kf2v-plus",
        "input": {
            "first_frame_url": first_frame_url,  # 🔥 修正字段名
            "last_frame_url": last_frame_url,  # 🔥 修正字段名
            "prompt": prompt,
        },
        "parameters": {
            "resolution": resolution,  # 🔥 使用正确的参数名
            "prompt_extend": True  # 🔥 添加官方推荐参数
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/video-synthesis"

    print("📤 发送请求...")
    print(f"请求数据: {task_data}")

    try:
        task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            print(f"❌ 创建任务失败，响应: {task_result}")
            raise Exception(f"创建任务失败，未获取到task_id: {task_result}")

        print(f"✅ 任务创建成功: {task_id}")

        # 等待任务完成
        final_result = handler._wait_for_task(task_id, max_wait_time=1800)

        print(f"🔍 [DEBUG] 完整API响应: {final_result}")
        
        # 尝试多个可能的字段路径获取视频URL
        video_url = None
        
        # 尝试路径1: output.video_url
        video_url = final_result.get("output", {}).get("video_url")
        if video_url:
            print(f"✅ 从 output.video_url 获取到视频URL: {video_url}")
        else:
            print("❌ output.video_url 字段为空")
            
        # 尝试路径2: output.video_urls (数组)
        if not video_url:
            video_urls = final_result.get("output", {}).get("video_urls", [])
            if video_urls and len(video_urls) > 0:
                video_url = video_urls[0]
                print(f"✅ 从 output.video_urls[0] 获取到视频URL: {video_url}")
            else:
                print("❌ output.video_urls 字段为空或不存在")
        
        # 尝试路径3: output.results
        if not video_url:
            results = final_result.get("output", {}).get("results", [])
            if results and len(results) > 0:
                video_url = results[0].get("video_url") or results[0].get("url")
                if video_url:
                    print(f"✅ 从 output.results[0] 获取到视频URL: {video_url}")
                else:
                    print("❌ output.results[0] 中未找到视频URL")
            else:
                print("❌ output.results 字段为空或不存在")
        
        # 尝试路径4: 直接在output层级寻找url字段
        if not video_url:
            video_url = final_result.get("output", {}).get("url")
            if video_url:
                print(f"✅ 从 output.url 获取到视频URL: {video_url}")
            else:
                print("❌ output.url 字段为空")
        
        # 如果仍然没有找到，打印详细信息
        if not video_url:
            print(f"❌ 未获取到视频URL，尝试了所有可能的字段路径")
            print(f"完整响应结构: {json.dumps(final_result, indent=2, ensure_ascii=False)}")
            
            # 检查是否有错误信息
            error_msg = final_result.get("output", {}).get("message") or final_result.get("message")
            if error_msg:
                raise Exception(f"API返回错误: {error_msg}")
            else:
                raise Exception(f"未获取到生成的视频URL，响应: {final_result}")

        print(f"🎉 图生视频完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ 等待任务完成时发生错误: {str(e)}")
        # 如果函数执行失败，记录详细错误并重新抛出
        error_msg = f"图生视频失败: {str(e)}"
        print(f"💥 {error_msg}")
        raise Exception(error_msg)

# ============ 虚拟模特系列 ============

def get_virtual_model_v1(base_image_url: str, prompt: str,
                         mask_image_url: str = None,
                         face_prompt: str = None,
                         background_image_url: str = None,
                         short_side_size: str = "1024",
                         n: int = 1) -> str:
    """
    虚拟模特V1版 - 官方API结构

    Args:
        base_image_url: 模特或人台实拍商品展示图URL
        prompt: 虚拟模特和背景描述
        mask_image_url: 遮罩图片URL（可选）
        face_prompt: 面部描述（可选）
        background_image_url: 背景图片URL（可选）
        short_side_size: 输出图片短边尺寸
        n: 生成图片数量

    Returns:
        虚拟模特展示图URL
    """
    print(f"🧑‍🦱 [虚拟模特V1] 开始生成虚拟模特:")
    print(f"   基础图: {base_image_url}")
    print(f"   描述: {prompt}")

    handler = WanXiangAPIHandler()

    input_data = {
        "base_image_url": base_image_url,
        "prompt": prompt
    }

    if mask_image_url:
        input_data["mask_image_url"] = mask_image_url

    if face_prompt:
        input_data["face_prompt"] = face_prompt

    if background_image_url:
        input_data["background_image_url"] = background_image_url

    task_data = {
        "model": "wanx-virtualmodel-v1",
        "input": input_data,
        "parameters": {
            "short_side_size": short_side_size,
            "n": n
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/virtualmodel/generation"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待虚拟模特生成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)

    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url_result = results[0].get("url")
    if not image_url_result:
        raise Exception("未获取到虚拟模特图片URL")

    print(f"🎉 虚拟模特V1生成完成: {image_url_result}")
    return image_url_result


def get_virtual_model_v2(base_image_url: str, prompt: str,
                         mask_image_url: str = None,
                         face_prompt: str = None,
                         background_image_url: str = None,
                         short_side_size: str = "1024",
                         n: int = 1) -> str:
    """
    虚拟模特V2版 - 官方API结构

    Args:
        base_image_url: 模特或人台实拍商品展示图URL
        prompt: 虚拟模特和背景描述（建议使用英文）
        mask_image_url: 遮罩图片URL（可选）
        face_prompt: 面部描述（可选）
        background_image_url: 背景图片URL（可选）
        short_side_size: 输出图片短边尺寸
        n: 生成图片数量

    Returns:
        虚拟模特展示图URL
    """
    print(f"🧑‍🦱 [虚拟模特V2] 开始生成虚拟模特:")
    print(f"   基础图: {base_image_url}")
    print(f"   描述: {prompt}")

    handler = WanXiangAPIHandler()

    input_data = {
        "base_image_url": base_image_url,
        "prompt": prompt
    }

    if mask_image_url:
        input_data["mask_image_url"] = mask_image_url

    if face_prompt:
        input_data["face_prompt"] = face_prompt

    if background_image_url:
        input_data["background_image_url"] = background_image_url

    task_data = {
        "model": "wanx-virtualmodel-v2",
        "input": input_data,
        "parameters": {
            "short_side_size": short_side_size,
            "n": n
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/virtualmodel/generation"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待虚拟模特V2生成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)

    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url_result = results[0].get("url")
    if not image_url_result:
        raise Exception("未获取到虚拟模特图片URL")

    print(f"🎉 虚拟模特V2生成完成: {image_url_result}")
    return image_url_result


# ============ 图像背景生成 ============

def get_background_generation_from_request(request_data: Dict[str, Any]) -> str:
    """
    从请求数据生成背景 - 直接处理原始请求数据

    Args:
        request_data: 包含所有请求参数的字典

    Returns:
        生成的背景图片URL
    """
    print(f"🖼️ [背景生成-从请求] 开始生成背景:")
    print(f"   完整请求数据: {request_data}")

    handler = WanXiangAPIHandler()

    # 提取基本参数
    base_image_url = request_data.get('base_image_url')
    ref_image_url = request_data.get('ref_image_url')
    ref_prompt = request_data.get('ref_prompt')
    n = request_data.get('n', 4)
    ref_prompt_weight = request_data.get('ref_prompt_weight', 0.5)
    model_version = 'v2'

    print(f"   主体图: {base_image_url}")
    print(f"   参考图: {ref_image_url}")
    print(f"   参考提示词: {ref_prompt}")
    print(f"   模型版本: {model_version}")

    # 构建input数据
    input_data = {
        "base_image_url": base_image_url
    }

    # 添加可选的参考图片和提示词
    if ref_image_url:
        input_data["ref_image_url"] = ref_image_url

    if ref_prompt:
        input_data["ref_prompt"] = ref_prompt

    # 🔥 直接使用原始的reference_edge对象
    reference_edge = request_data.get('reference_edge')
    if reference_edge:
        print(f"   找到reference_edge: {reference_edge}")
        input_data["reference_edge"] = reference_edge
    else:
        # 如果没有reference_edge，尝试从扁平参数构建
        reference_edge_built = {}

        foreground_edge_urls = request_data.get('foreground_edge_urls')
        background_edge_urls = request_data.get('background_edge_urls')
        foreground_edge_prompts = request_data.get('foreground_edge_prompts')
        background_edge_prompts = request_data.get('background_edge_prompts')

        if foreground_edge_urls:
            reference_edge_built["foreground_edge"] = foreground_edge_urls
        if background_edge_urls:
            reference_edge_built["background_edge"] = background_edge_urls
        if foreground_edge_prompts:
            reference_edge_built["foreground_edge_prompt"] = foreground_edge_prompts
        if background_edge_prompts:
            reference_edge_built["background_edge_prompt"] = background_edge_prompts

        if reference_edge_built:
            print(f"   从扁平参数构建reference_edge: {reference_edge_built}")
            input_data["reference_edge"] = reference_edge_built

    # 构建完整的任务数据
    task_data = {
        "model": f"wanx-background-generation-{model_version}",
        "input": input_data,
        "parameters": {
            "n": n,
            "ref_prompt_weight": ref_prompt_weight,
            "model_version": model_version
        }
    }

    print(f"📤 最终发送请求数据: {task_data}")

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/background-generation/generation/"

    try:
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 响应状态码: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"❌ 请求失败，响应: {error_text}")
            raise Exception(f"API请求失败: {response.status_code} - {error_text}")

        task_result = response.json()
        print(f"📥 创建任务响应: {task_result}")

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            print(f"❌ 创建任务失败，响应: {task_result}")
            raise Exception(f"创建任务失败，未获取到task_id: {task_result}")

        print(f"✅ 任务创建成功: {task_id}")

        print("⏳ 等待背景生成...")
        final_result = handler._wait_for_task(task_id, max_wait_time=600)

        results = final_result.get("output", {}).get("results", [])
        if not results:
            print(f"❌ 任务完成但未获取到结果，响应: {final_result}")
            raise Exception(f"任务完成但未获取到结果: {final_result}")

        # 返回第一个结果的URL
        image_url = results[0].get("url")
        if not image_url:
            print(f"❌ 结果中没有URL字段，结果: {results[0]}")
            raise Exception(f"未获取到背景生成图片URL: {results[0]}")

        print(f"🎉 背景生成完成: {image_url}")
        print(f"📊 总共生成了 {len(results)} 张图片")

        return image_url

    except Exception as e:
        print(f"❌ 背景生成失败: {str(e)}")
        raise Exception(f"背景生成失败: {str(e)}")


def get_background_generation(**kwargs) -> str:
    """
    图像背景生成 - 兼容新旧参数格式

    支持两种调用方式：
    1. 传统参数: get_background_generation(base_image_url="...", ref_prompt="...")
    2. 嵌套参数: get_background_generation(base_image_url="...", reference_edge={...})
    """
    print(f"🖼️ [背景生成-兼容版] 开始生成背景:")
    print(f"   接收参数: {kwargs}")

    # 直接使用get_background_generation_from_request处理
    return get_background_generation_from_request(kwargs)


# ============ AI试衣系列 ============

def get_ai_tryon_basic(person_image_url: str, top_garment_url: str = None,
                       bottom_garment_url: str = None, resolution: int = -1,
                       restore_face: bool = True) -> str:
    """
    AI试衣-基础版 - 官方API结构

    Args:
        person_image_url: 模特人物图片URL
        top_garment_url: 上装服饰图片URL
        bottom_garment_url: 下装服饰图片URL
        resolution: 输出图片分辨率控制 (-1, 0, 1)
        restore_face: 是否还原脸部

    Returns:
        试衣效果图URL
    """
    print(f"👔 [AI试衣基础版] 开始生成试衣效果:")
    print(f"   模特图: {person_image_url}")
    print(f"   上装: {top_garment_url}")
    print(f"   下装: {bottom_garment_url}")

    if not top_garment_url and not bottom_garment_url:
        raise Exception("至少需要提供上装或下装图片")

    handler = WanXiangAPIHandler()

    input_data = {
        "person_image_url": person_image_url
    }

    if top_garment_url:
        input_data["top_garment_url"] = top_garment_url

    if bottom_garment_url:
        input_data["bottom_garment_url"] = bottom_garment_url

    task_data = {
        "model": "aitryon",
        "input": input_data,
        "parameters": {
            "resolution": resolution,
            "restore_face": restore_face
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2image/image-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)
    print("任务结果")
    print(task_result)
    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待试衣任务完成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)
    print(final_result)
    image_url = final_result.get("output", {}).get("image_url", '')
    print(f"🎉 AI试衣基础版完成: {image_url}")
    return image_url


def get_ai_tryon_plus(person_image_url: str, top_garment_url: str = None,
                      bottom_garment_url: str = None, resolution: int = -1,
                      restore_face: bool = True) -> str:
    """
    AI试衣-Plus版 - 官方API结构

    Args:
        person_image_url: 模特人物图片URL
        top_garment_url: 上装服饰图片URL
        bottom_garment_url: 下装服饰图片URL
        resolution: 输出图片分辨率控制 (-1, 0, 1)
        restore_face: 是否还原脸部

    Returns:
        试衣效果图URL
    """
    print(f"👔 [AI试衣Plus版] 开始生成高质量试衣效果:")
    print(f"   模特图: {person_image_url}")
    print(f"   上装: {top_garment_url}")
    print(f"   下装: {bottom_garment_url}")

    if not top_garment_url and not bottom_garment_url:
        raise Exception("至少需要提供上装或下装图片")

    handler = WanXiangAPIHandler()

    input_data = {
        "person_image_url": person_image_url
    }

    if top_garment_url:
        input_data["top_garment_url"] = top_garment_url

    if bottom_garment_url:
        input_data["bottom_garment_url"] = bottom_garment_url

    task_data = {
        "model": "aitryon-plus",
        "input": input_data,
        "parameters": {
            "resolution": resolution,
            "restore_face": restore_face
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2image/image-synthesis"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待高质量试衣任务完成...")

    final_result = handler._wait_for_task(task_id, max_wait_time=600)
    print(final_result)
    image_url = final_result.get("output", {}).get("image_url", '')

    print(f"🎉 AI试衣Plus版完成: {image_url}")
    return image_url


def get_ai_tryon_enhance(person_image_url: str, top_garment_url: str = None,
                         bottom_garment_url: str = None, gender: str = "woman") -> str:
    """
    AI试衣-图片精修 - 先调用基础版获取粗糙图片，再进行精修

    Args:
        person_image_url: 模特人物图片URL
        top_garment_url: 上装服饰图片URL
        bottom_garment_url: 下装服饰图片URL
        gender: 性别 (woman/man)

    Returns:
        精修后的图片URL
    """
    print(f"✨ [AI试衣精修] 开始两步式试衣:")
    print(f"   模特图: {person_image_url}")
    print(f"   上装: {top_garment_url}")
    print(f"   下装: {bottom_garment_url}")
    print(f"   性别: {gender}")

    try:
        # 第一步：调用基础版获取粗糙试衣图片
        print("🔄 第一步: 生成基础试衣效果...")
        coarse_image_url = get_ai_tryon_basic(
            person_image_url=person_image_url,
            top_garment_url=top_garment_url,
            bottom_garment_url=bottom_garment_url,
            resolution=-1,
            restore_face=True
        )
        print(f"✅ 基础试衣完成: {coarse_image_url}")

        # 第二步：精修图片
        print("🔄 第二步: 开始图片精修...")
        handler = WanXiangAPIHandler()

        task_data = {
            "model": "aitryon-refiner",
            "input": {
                "person_image_url": person_image_url,
                "coarse_image_url": coarse_image_url
            },
            "parameters": {
                "gender": gender
            }
        }

        # 只有在提供了服装URL时才添加到input中
        if top_garment_url:
            task_data["input"]["top_garment_url"] = top_garment_url
        if bottom_garment_url:
            task_data["input"]["bottom_garment_url"] = bottom_garment_url

        create_headers = handler.headers.copy()
        create_headers["X-DashScope-Async"] = "enable"

        url = f"{handler.base_url}/services/aigc/image2image/image-synthesis"
        task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            raise Exception("创建精修任务失败，未获取到task_id")

        print(f"✅ 精修任务创建成功: {task_id}")

        final_result = handler._wait_for_task(task_id, max_wait_time=900)

        # 使用与基础版相同的结果解析逻辑
        output = final_result.get("output", {})

        # 尝试多种可能的结果结构
        image_url = None

        # 方式1: 从results数组获取
        results = output.get("results", [])
        if results and isinstance(results, list) and len(results) > 0:
            image_url = results[0].get("url")

        # 方式2: 直接从output获取
        if not image_url:
            image_url = output.get("url")

        # 方式3: 从其他可能的字段获取
        if not image_url:
            image_url = output.get("image_url")

        if not image_url:
            raise Exception(f"未获取到精修后图片URL，完整响应: {final_result}")

        print(f"🎉 AI试衣精修完成: {image_url}")
        return image_url

    except Exception as e:
        print(f"❌ 试衣精修过程出错: {str(e)}")
        raise


def get_ai_tryon_segment(image_url: str, clothes_type: List[str]) -> Dict:
    """
    AI试衣-图片分割 - 官方API结构

    Args:
        image_url: 待分割的图片URL
        clothes_type: 分割类型列表 ["upper", "lower"]

    Returns:
        分割结果字典，包含parsing_img_url, crop_img_url, bbox
    """
    print(f"✂️ [AI试衣分割] 开始分割:")
    print(f"   原图: {image_url}")
    print(f"   分割类型: {clothes_type}")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": "aitryon-parsing-v1",
        "input": {
            "image_url": image_url
        },
        "parameters": {
            "clothes_type": clothes_type
        }
    }

    # 注意：这个是同步接口，不需要异步处理
    url = f"{handler.base_url}/services/vision/image-process/process"
    result = handler._make_request("POST", url, headers=handler.headers, json=task_data)

    output = result.get("output", {})
    print(output)
    if not output:
        raise Exception("未获取到分割结果")

    print(f"🎉 AI试衣分割完成")
    return {
        "parsing_img_url": output.get("parsing_img_url", []),
        "crop_img_url": output.get("crop_img_url", []),
        "bbox": output.get("bbox", [])
    }

# ============ 数字人视频系列 - 优化精简版 ============

def get_image_detection(image_url: str, detection_type: str, ratio: str = None) -> dict:
    """
    通用图像检测函数 - 支持三种数字人检测，返回适合各自API的数据格式

    Args:
        image_url: 人像图片URL
        detection_type: 检测类型 ("animate-anyone", "emo", "live-portrait")
        ratio: 图片比例，仅EMO需要 (如 "1:1", "16:9")

    Returns:
        dict: 包含检测结果的字典，结构因detection_type而异
        - animate-anyone: {"detection_id": "xxx", "check_pass": True, "bodystyle": "full"}
        - emo: {"image_url": "xxx", "face_bbox": [x,y,w,h], "ext_bbox": [x,y,w,h]}
        - live-portrait: {"detection_id": "xxx", "face_info": {...}}
    """
    # 配置映射
    detection_config = {
        "animate-anyone": {
            "model": "animate-anyone-detect-gen2",
            "url_path": "/services/aigc/image2video/aa-detect",
            "name": "舞动人像AnimateAnyone"
        },
        "emo": {
            "model": "emo-detect-v1",
            "url_path": "/services/aigc/image2video/face-detect",
            "name": "悦动人像EMO"
        },
        "live-portrait": {
            "model": "liveportrait-detect",
            "url_path": "/services/aigc/image2video/face-detect",
            "name": "灵动人像LivePortrait"
        }
    }

    if detection_type not in detection_config:
        raise ValueError(f"不支持的检测类型: {detection_type}")

    config = detection_config[detection_type]

    print(f"🔍 [{config['name']}] 图像检测:")
    print(f"   人像图: {image_url}")
    if ratio:
        print(f"   比例: {ratio}")

    handler = WanXiangAPIHandler()

    # 构建请求数据
    task_data = {
        "model": config["model"],
        "input": {
            "image_url": image_url
        },
        "parameters": {}
    }

    # EMO需要ratio参数
    if detection_type == "emo" and ratio:
        task_data["parameters"]["ratio"] = ratio

    print(f"📤 请求数据: {task_data}")

    # 🔥 修复：使用handler的headers，确保API密钥正确
    create_headers = handler.headers.copy()

    # 🔥 所有检测API都是同步的，都不需要异步header
    # AnimateAnyone、EMO、LivePortrait检测都是同步API

    print(f"📤 请求头: {create_headers}")

    url = f"{handler.base_url}{config['url_path']}"
    print(f"📤 请求URL: {url}")

    try:
        # 使用requests直接调用以获取详细错误信息
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text}")

        if response.status_code == 403:
            print(f"❌ 403错误详情: {response.text}")
            # 检查是否需要同步调用
            if "X-DashScope-Async" in create_headers:
                print("🔄 尝试移除异步header重新请求...")
                create_headers_sync = handler.headers.copy()
                response = requests.post(url, headers=create_headers_sync, json=task_data)
                print(f"📥 同步请求状态码: {response.status_code}")
                print(f"📥 同步请求响应: {response.text}")

        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code} - {response.text}")

        result = response.json()
        print(f"📥 成功响应: {result}")

        # 🔥 处理不同类型的响应结构，返回各自需要的数据格式
        if detection_type == "animate-anyone":
            # AnimateAnyone是同步API，直接返回检测结果
            if "output" in result:
                check_pass = result["output"].get("check_pass")
                bodystyle = result["output"].get("bodystyle")

                if check_pass:
                    # 生成detection_id
                    request_id = result.get("request_id", "")
                    detection_id = f"aa_detect_{request_id}" if request_id else f"aa_detection_{int(time.time())}"

                    detection_result = {
                        "detection_id": detection_id,
                        "check_pass": check_pass,
                        "bodystyle": bodystyle,
                        "image_url": image_url  # 保留原始图片URL
                    }

                    print(f"✅ {config['name']}同步检测完成:")
                    print(f"   检测结果: {detection_result}")
                    return detection_result
                else:
                    raise Exception(f"{config['name']}图像检测未通过：check_pass={check_pass}")
            else:
                raise Exception(f"AnimateAnyone响应格式异常: {result}")

        elif detection_type == "emo":
            # 🔥 EMO也是同步API，直接返回检测结果
            if "output" in result:
                output = result["output"]
                check_pass = output.get("check_pass")
                humanoid = output.get("humanoid")
                face_bbox = output.get("face_bbox")
                ext_bbox = output.get("ext_bbox")

                if check_pass and face_bbox and ext_bbox:
                    detection_result = {
                        "image_url": image_url,
                        "face_bbox": face_bbox,
                        "ext_bbox": ext_bbox,
                        "check_pass": check_pass,
                        "humanoid": humanoid,
                        "detection_id": f"emo_detect_{result.get('request_id', int(time.time()))}"
                    }

                    print(f"✅ {config['name']}同步检测完成:")
                    print(f"   检测结果: {detection_result}")
                    return detection_result
                else:
                    missing_fields = []
                    if not check_pass:
                        missing_fields.append("check_pass为False")
                    if not face_bbox:
                        missing_fields.append("face_bbox")
                    if not ext_bbox:
                        missing_fields.append("ext_bbox")
                    raise Exception(f"EMO检测未通过或缺少必要字段: {', '.join(missing_fields)}")
            else:
                raise Exception(f"EMO响应格式异常: {result}")

        else:  # live-portrait
            # 🔥 LivePortrait也是同步API，直接返回检测结果
            if "output" in result:
                output = result["output"]

                # LivePortrait可能返回不同的字段，需要根据实际API文档调整
                # 这里先用通用的处理方式
                detection_id = output.get("detection_id")
                if not detection_id:
                    # 如果没有detection_id，生成一个
                    request_id = result.get("request_id", "")
                    detection_id = f"lp_detect_{request_id}" if request_id else f"lp_detection_{int(time.time())}"

                detection_result = {
                    "detection_id": detection_id,
                    "image_url": image_url,
                    "face_info": output,  # 保留完整的检测信息
                    "check_pass": output.get("check_pass", True)  # 假设检测通过
                }

                print(f"✅ {config['name']}同步检测完成:")
                print(f"   检测结果: {detection_result}")
                return detection_result
            else:
                raise Exception(f"LivePortrait响应格式异常: {result}")

    except Exception as e:
        print(f"❌ {config['name']}图像检测失败: {str(e)}")
        raise Exception(f"{config['name']}图像检测失败: {str(e)}")


def get_animate_anyone_template(dance_video_url: str) -> str:
    """
    舞动人像 - 动作模板生成
    """
    print(f"🎬 [舞动人像] 创建动作模板:")
    print(f"   舞蹈视频: {dance_video_url}")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": "animate-anyone-template-gen2",
        "input": {
            "dance_video_url": dance_video_url
        }
    }

    print(f"📤 模板生成请求数据: {task_data}")

    # 🔥 修复：使用handler的headers，添加异步header
    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/aa-template-generation"
    print(f"📤 模板生成URL: {url}")

    try:
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 模板生成响应状态码: {response.status_code}")
        print(f"📥 模板生成响应内容: {response.text}")

        if response.status_code != 200:
            raise Exception(f"模板生成API请求失败: {response.status_code} - {response.text}")

        task_result = response.json()

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            raise Exception(f"创建模板任务失败，未获取到task_id: {task_result}")

        print(f"✅ 动作模板任务创建成功: {task_id}")

        final_result = handler._wait_for_task(task_id, max_wait_time=1800)
        print(f"📥 模板生成最终结果: {final_result}")

        template_id = final_result.get("output", {}).get("template_id")
        if not template_id:
            # 尝试其他可能的字段名
            template_id = (
                    final_result.get("output", {}).get("result_id") or
                    final_result.get("output", {}).get("id") or
                    final_result.get("output", {}).get("template_url")
            )

        if not template_id:
            available_fields = list(final_result.get("output", {}).keys())
            raise Exception(f"未获取到生成的动作模板ID，可用字段: {available_fields}")

        print(f"🎉 动作模板创建完成: {template_id}")
        return template_id

    except Exception as e:
        print(f"❌ 动作模板生成失败: {str(e)}")
        raise


def get_animate_anyone_generation(detection_id: str, template_id: str,
                                  duration: int = 10) -> str:
    """
    舞动人像 - 视频生成
    """
    print(f"💃 [舞动人像] 生成视频:")
    print(f"   检测ID: {detection_id}")
    print(f"   动作模板ID: {template_id}")
    print(f"   时长: {duration}秒")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": "animate-anyone-gen2",
        "input": {
            "detection_id": detection_id,
            "template_id": template_id
        },
        "parameters": {
            "duration": duration
        }
    }

    print(f"📤 视频生成请求数据: {task_data}")

    # 🔥 修复：使用handler的headers，添加异步header
    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/aa-generation"
    print(f"📤 视频生成URL: {url}")

    try:
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 视频生成响应状态码: {response.status_code}")
        print(f"📥 视频生成响应内容: {response.text}")

        if response.status_code != 200:
            raise Exception(f"视频生成API请求失败: {response.status_code} - {response.text}")

        task_result = response.json()

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            raise Exception(f"创建视频生成任务失败，未获取到task_id: {task_result}")

        print(f"✅ 视频生成任务创建成功: {task_id}")

        final_result = handler._wait_for_task(task_id, max_wait_time=1800)
        print(f"📥 视频生成最终结果: {final_result}")

        # 🔥 修正字段名：可能是output_video_url
        video_url = final_result.get("output", {}).get("video_url")
        if not video_url:
            video_url = (
                    final_result.get("output", {}).get("output_video_url") or
                    final_result.get("output", {}).get("result_url") or
                    final_result.get("output", {}).get("url")
            )

        if not video_url:
            available_fields = list(final_result.get("output", {}).keys())
            raise Exception(f"未获取到生成的舞蹈视频URL，可用字段: {available_fields}")

        print(f"🎉 舞动人像视频生成完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ 舞动人像视频生成失败: {str(e)}")
        raise

def get_emo_generation(detection_result: dict, audio_url: str,
                       style_level: str = "normal") -> str:
    """
    悦动人像EMO - 视频生成

    Args:
        detection_result: EMO检测结果字典，包含image_url, face_bbox, ext_bbox
        audio_url: 音频文件URL
        style_level: 风格级别 ("normal", "high", "low")

    Returns:
        生成的唱演视频URL
    """
    print(f"🎤 [悦动人像EMO] 生成视频:")
    print(f"   检测结果: {detection_result}")
    print(f"   音频: {audio_url}")
    print(f"   风格级别: {style_level}")

    handler = WanXiangAPIHandler()

    # 按照官方API结构构建请求
    task_data = {
        "model": "emo-v1",
        "input": {
            "image_url": detection_result["image_url"],
            "audio_url": audio_url,
            "face_bbox": detection_result["face_bbox"],
            "ext_bbox": detection_result["ext_bbox"]
        },
        "parameters": {
            "style_level": style_level
        }
    }

    print(f"📤 EMO视频生成请求数据: {task_data}")

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/video-synthesis"

    try:
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 EMO视频生成响应状态码: {response.status_code}")
        print(f"📥 EMO视频生成响应内容: {response.text}")

        if response.status_code != 200:
            raise Exception(f"EMO视频生成API请求失败: {response.status_code} - {response.text}")

        task_result = response.json()

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            raise Exception(f"创建EMO视频生成任务失败，未获取到task_id: {task_result}")

        print(f"✅ EMO视频生成任务创建成功: {task_id}")

        final_result = handler._wait_for_task(task_id, max_wait_time=1800)
        print(f"📥 EMO视频生成最终结果: {final_result}")

        # 🔥 修正字段名：可能是output_video_url
        video_url = final_result.get("output", {}).get("results").get("video_url")
        if not video_url:
            video_url = (
                    final_result.get("output", {}).get("output_video_url") or
                    final_result.get("output", {}).get("result_url") or
                    final_result.get("output", {}).get("url")
            )

        if not video_url:
            available_fields = list(final_result.get("output", {}).keys())
            raise Exception(f"未获取到生成的EMO唱演视频URL，可用字段: {available_fields}")

        print(f"🎉 悦动人像EMO视频生成完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ EMO视频生成失败: {str(e)}")
        raise


def get_live_portrait_generation(image_url: str, audio_url: str,
                                 duration: int = 10) -> str:
    """
    灵动人像LivePortrait - 音频驱动视频生成（异步API）

    Args:
        image_url: 人像图片URL
        audio_url: 音频文件URL
        duration: 视频时长(秒)

    Returns:
        生成的播报视频URL
    """
    print(f"📺 [灵动人像] 生成视频:")
    print(f"   人像图: {image_url}")
    print(f"   音频: {audio_url}")
    print(f"   时长: {duration}秒")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": "liveportrait",
        "input": {
            "image_url": image_url,
            "audio_url": audio_url
        },
        "parameters": {
            "template_id": "normal",
            "eye_move_freq": 0.5,
            "video_fps": 30,
            "mouth_move_strength": 1,
            "paste_back": True,
            "head_move_strength": 0.7
        }
    }

    print(f"📤 LivePortrait请求数据: {task_data}")

    # 🔥 LivePortrait视频生成是异步API，需要异步header
    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image2video/video-synthesis"
    print(f"📤 LivePortrait请求URL: {url}")

    try:
        # 步骤1: 创建异步任务
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 LivePortrait响应状态码: {response.status_code}")
        print(f"📥 LivePortrait响应内容: {response.text}")

        if response.status_code != 200:
            raise Exception(f"LivePortrait API请求失败: {response.status_code} - {response.text}")

        task_result = response.json()
        print(f"📥 LivePortrait任务创建响应: {task_result}")

        # 步骤2: 获取task_id
        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            raise Exception(f"创建LivePortrait视频生成任务失败，未获取到task_id: {task_result}")

        print(f"✅ LivePortrait视频生成任务创建成功: {task_id}")

        # 步骤3: 等待任务完成并获取结果
        # 使用handler的_wait_for_task方法，它会循环调用GET /tasks/{task_id}
        final_result = handler._wait_for_task(task_id, max_wait_time=1800)
        print(f"📥 LivePortrait视频生成最终结果: {final_result}")

        # 步骤4: 提取视频URL
        output = final_result.get("output", {})
        video_url = output.get("results").get("video_url")

        if video_url:
            print(f"🎉 灵动人像视频生成完成: {video_url}")
            return video_url
        else:
            available_fields = list(output.keys())
            raise Exception(f"LivePortrait结果中未找到视频URL，可用字段: {available_fields}")

    except Exception as e:
        print(f"❌ LivePortrait视频生成失败: {str(e)}")
        raise

# ============ 一键完成函数（并行优化版本） ============


def get_animate_anyone(image_url: str, dance_video_url: str, duration: int = 10) -> str:
    """AnimateAnyone完整流程"""
    from concurrent.futures import ThreadPoolExecutor
    import time

    print(f"🚀 [舞动人像] 开始并行流程:")
    print(f"   人像图: {image_url}")
    print(f"   舞蹈视频: {dance_video_url}")
    print(f"   时长: {duration}秒")

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            print("🔄 并行执行图像检测和动作模板生成...")
            detection_future = executor.submit(get_animate_anyone_detection, image_url)
            template_future = executor.submit(get_animate_anyone_template, dance_video_url)

            detection_id = detection_future.result()
            template_id = template_future.result()

        video_url = get_animate_anyone_generation(detection_id, template_id, duration)
        print(f"🎉 舞动人像流程完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ 舞动人像流程失败: {str(e)}")
        raise


def get_emo_video(image_url: str, audio_url: str, ratio: str = "1:1", style_level: str = "normal") -> str:
    """EMO简化完整流程"""
    print(f"🚀 [EMO简化流程] 开始:")
    print(f"   人像图: {image_url}")
    print(f"   音频: {audio_url}")

    try:
        detection_data = get_emo_detection_data(image_url, ratio)
        video_url = get_emo_generation(detection_data, audio_url, style_level)
        print(f"🎉 EMO流程完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ EMO流程失败: {str(e)}")
        raise


def get_live_portrait(image_url: str, audio_url: str, duration: int = 10) -> str:
    """LivePortrait简化完整流程"""
    print(f"🚀 [LivePortrait简化流程] 开始:")
    print(f"   人像图: {image_url}")
    print(f"   音频: {audio_url}")

    try:
        detection_id = get_live_portrait_detection(image_url)
        video_url = get_live_portrait_generation(image_url, audio_url, duration)
        print(f"🎉 LivePortrait流程完成: {video_url}")
        return video_url

    except Exception as e:
        print(f"❌ LivePortrait流程失败: {str(e)}")
        raise
# ============ 便捷函数（向后兼容） ============
# 为了保持向后兼容，提供专门的函数
def get_animate_anyone_detection(image_url: str) -> str:
    """AnimateAnyone检测 - 返回detection_id字符串（向后兼容）"""
    result = get_image_detection(image_url, "animate-anyone")
    return result["detection_id"]


def get_emo_detection_data(image_url: str, ratio: str = "1:1") -> dict:
    """EMO检测 - 返回包含face_bbox和ext_bbox的完整数据"""
    return get_image_detection(image_url, "emo", ratio)


def get_live_portrait_detection(image_url: str) -> str:
    """LivePortrait检测 - 返回detection_id字符串（向后兼容）"""
    result = get_image_detection(image_url, "live-portrait")
    return result["detection_id"]

# ============ 便捷函数 ============

def create_dance_video_with_template(image_url: str, dance_video_url: str,
                                     duration: int = 10) -> str:
    """
    一键生成舞蹈视频 - 自动创建模板并生成视频

    Args:
        image_url: 人像图片URL
        dance_video_url: 舞蹈动作视频URL
        duration: 视频时长(秒)

    Returns:
        生成的舞蹈视频URL
    """
    print(f"🎭 [一键舞蹈] 开始完整流程:")

    # 第一步：创建动作模板
    template_id = get_animate_anyone_template(dance_video_url)

    # 第二步：使用模板生成视频
    video_url = get_animate_anyone(image_url, template_id, duration)

    return video_url




# ============ 视频编辑系列 ============

def get_video_style_transform(video_url: str, style: int = 0, video_fps: int = 15) -> str:
    """
    视频风格转换 - 按照官方API结构

    Args:
        video_url: 原始视频URL
        style: 风格ID (0-10)
        video_fps: 视频帧率

    Returns:
        转换后的视频URL
    """
    print(f"🎨 [视频风格转换] 开始转换:")
    print(f"   原视频: {video_url}")
    print(f"   风格ID: {style}")
    print(f"   帧率: {video_fps}")

    handler = WanXiangAPIHandler()

    # 按照官方API结构构建请求
    task_data = {
        "model": "video-style-transform",
        "input": {
            "video_url": video_url
        },
        "parameters": {
            "style": style,
            "video_fps": video_fps
        }
    }

    print(f"📤 发送请求数据: {task_data}")

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"
    create_headers["X-DashScope-DataInspection"] = "enable"  # 添加官方示例中的header

    # 使用正确的URL路径
    url = f"{handler.base_url}/services/aigc/video-generation/video-synthesis"

    try:
        response = requests.post(url, headers=create_headers, json=task_data)
        print(f"📥 响应状态码: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            print(f"❌ 请求失败，响应: {error_text}")
            raise Exception(f"API请求失败: {response.status_code} - {error_text}")

        task_result = response.json()
        print(f"📥 创建任务响应: {task_result}")

        task_id = task_result.get("output", {}).get("task_id")
        if not task_id:
            print(f"❌ 创建任务失败，响应: {task_result}")
            raise Exception(f"创建任务失败，未获取到task_id: {task_result}")

        print(f"✅ 任务创建成功: {task_id}")

        print("⏳ 等待视频风格转换...")
        final_result = handler._wait_for_task(task_id, max_wait_time=1800)

        video_url_result = final_result.get("output", {}).get("output_video_url")
        if not video_url_result:
            print(f"❌ 未获取到转换后视频URL，响应: {final_result}")
            raise Exception(f"未获取到转换后视频URL: {final_result}")

        print(f"🎉 视频风格转换完成: {video_url_result}")
        return video_url_result

    except Exception as e:
        print(f"❌ 视频风格转换失败: {str(e)}")
        raise Exception(f"视频风格转换失败: {str(e)}")


def get_video_edit(video_url: str = None, image_urls: List[str] = None,
                   prompt: str = None, edit_type: str = "style") -> str:
    """
    通用视频编辑 - 官方API结构

    Args:
        video_url: 原始视频URL
        image_urls: 图片URL列表（多图参考）
        prompt: 编辑指令
        edit_type: 编辑类型：style/object/background

    Returns:
        编辑后的视频URL
    """
    print(f"✂️ [通用视频编辑] 开始编辑:")
    print(f"   原视频: {video_url}")
    print(f"   图片列表: {image_urls}")
    print(f"   编辑类型: {edit_type}")

    handler = WanXiangAPIHandler()

    input_data = {}

    if video_url:
        input_data["video_url"] = video_url

    if image_urls:
        input_data["image_urls"] = image_urls

    if prompt:
        input_data["prompt"] = prompt

    task_data = {
        "model": "wanx-vace",
        "input": input_data,
        "parameters": {
            "edit_type": edit_type
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/video-edit/generation"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    final_result = handler._wait_for_task(task_id, max_wait_time=1800)

    video_url_result = final_result.get("output", {}).get("video_url")
    if not video_url_result:
        raise Exception("未获取到编辑后视频URL")

    print(f"🎉 通用视频编辑完成: {video_url_result}")
    return video_url_result


# ============ 图像编辑系列 ============

def get_image_background_edit(image_url: str, prompt: str,
                              negative_prompt: str = None,
                              guidance_scale: float = 7.5,
                              strength: float = 0.8) -> str:
    """
    通用图像编辑 - 官方API结构

    Args:
        image_url: 原始图片URL
        prompt: 编辑描述
        negative_prompt: 负向提示词
        guidance_scale: 引导系数
        strength: 编辑强度

    Returns:
        编辑后的图片URL
    """
    print(f"✏️ [图像编辑] 开始编辑图像:")
    print(f"   原图: {image_url}")
    print(f"   编辑描述: {prompt}")

    handler = WanXiangAPIHandler()

    input_data = {
        "image_url": image_url,
        "prompt": prompt
    }

    if negative_prompt:
        input_data["negative_prompt"] = negative_prompt

    task_data = {
        "model": "wanx-image-edit-v2",
        "input": input_data,
        "parameters": {
            "guidance_scale": guidance_scale,
            "strength": strength
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/image-edit/generation"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待图像编辑完成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)

    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url_result = results[0].get("url")
    if not image_url_result:
        raise Exception("未获取到编辑后图片URL")

    print(f"🎉 图像编辑完成: {image_url_result}")
    return image_url_result


# ============ 其他特殊模型 ============

def get_shoe_model(template_image_url: str, shoe_image_url: List[str], n: int = 1) -> str:
    """
    鞋靴模特 - 官方API结构

    Args:
        template_image_url: 模特模板图片URL
        shoe_image_url: 鞋靴图片URL列表
        n: 生成图片数量

    Returns:
        鞋靴模特展示图URL
    """
    print(f"👠 [鞋靴模特] 开始生成:")
    print(f"   模特模板图: {template_image_url}")
    print(f"   鞋靴图列表: {shoe_image_url}")

    handler = WanXiangAPIHandler()

    task_data = {
        "model": "shoemodel-v1",
        "input": {
            "template_image_url": template_image_url,
            "shoe_image_url": shoe_image_url
        },
        "parameters": {
            "n": n
        }
    }

    create_headers = handler.headers.copy()
    create_headers["X-DashScope-Async"] = "enable"

    url = f"{handler.base_url}/services/aigc/virtualmodel/generation"
    task_result = handler._make_request("POST", url, headers=create_headers, json=task_data)

    task_id = task_result.get("output", {}).get("task_id")
    if not task_id:
        raise Exception("创建任务失败，未获取到task_id")

    print(f"✅ 任务创建成功: {task_id}")

    print("⏳ 等待鞋靴模特生成...")
    final_result = handler._wait_for_task(task_id, max_wait_time=600)

    results = final_result.get("output", {}).get("results", [])
    if not results:
        raise Exception("任务完成但未获取到结果")

    image_url_result = results[0].get("url")
    if not image_url_result:
        raise Exception("未获取到鞋靴模特图片URL")

    print(f"🎉 鞋靴模特生成完成: {image_url_result}")
    return image_url_result


# ============ 使用示例 ============

def test_creative_poster():
    """测试创意海报生成"""
    try:
        result = get_creative_poster(
            title="春节快乐",
            sub_title="家庭团聚，共享天伦之乐",
            body_text="春节是中国最重要的传统节日之一，它象征着新的开始和希望",
            prompt_text_zh="灯笼，小猫，梅花",
            wh_ratios="竖版",
            lora_name="童话油画",
            lora_weight=0.8,
            ctrl_ratio=0.7,
            ctrl_step=0.7,
            generate_mode="generate",
            generate_num=1
        )
        print(f"测试成功，海报URL: {result}")
        return result
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None


def test_text_to_image_v2():
    """测试文生图V2"""
    try:
        result = get_text_to_image_v2(
            prompt="一间有着精致窗户的花店，漂亮的木质门，摆放着花朵",
            model="wanx2.1-t2i-turbo",
            size="1024*1024",
            n=1
        )
        print(f"测试成功，图片URL: {result}")
        return result
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None


if __name__ == "__main__":
    print("通义万相官方API处理函数模块加载成功!")
    print("可用函数:")
    print("- get_creative_poster() - 创意海报生成")
    print("- get_text_to_image_v2() - 文生图V2版")
    print("- get_text_to_image_v1() - 文生图V1版")
    print("- get_text_to_video() - 文生视频")
    print("- get_image_to_video() - 图生视频")
    print("- get_virtual_model_v1/v2() - 虚拟模特")
    print("- get_background_generation() - 背景生成")
    print("- get_ai_tryon_basic/plus() - AI试衣")
    print("- get_animate_anyone() - 舞动人像")
    print("- get_emo_video() - 悦动人像EMO")
    print("- get_live_portrait() - 灵动人像")
    print("- get_video_style_transfer() - 视频风格重绘")
    print("- get_image_background_edit() - 图像编辑")
    print("等等...")
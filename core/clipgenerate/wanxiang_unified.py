# -*- coding: utf-8 -*-
"""
统一的通义万相API封装
重构原有的tongyi_wangxiang.py，提供统一的API调用接口
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor

import requests
from .base_generator import APIClientBase, handle_api_errors
from get_api_key import get_api_key_from_file


class WanXiangUnifiedClient(APIClientBase):
    """统一的通义万相API客户端"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            
            if response.status_code != 200:
                self._handle_error(response)
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception(f"请求超时 ({self.timeout}秒)")
        except requests.exceptions.ConnectionError:
            raise Exception("网络连接错误")
        except Exception as e:
            if "API请求失败" in str(e):
                raise
            raise Exception(f"请求失败: {str(e)}")
    
    def _wait_for_task(self, task_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """等待异步任务完成"""
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            url = f"{self.base_url}/tasks/{task_id}"
            result = self._make_request("GET", url)
            
            task_status = result.get("output", {}).get("task_status")
            
            if task_status == "SUCCEEDED":
                return result
            elif task_status == "FAILED":
                error_msg = result.get("output", {}).get("message", "任务执行失败")
                raise Exception(f"任务失败: {error_msg}")
            
            time.sleep(5)  # 等待5秒后重试
        
        raise Exception(f"任务超时，等待时间超过{max_wait_time}秒")
    
    def _create_async_task(self, model: str, input_data: Dict[str, Any], 
                          parameters: Dict[str, Any], endpoint: str) -> str:
        """创建异步任务并返回task_id"""
        task_data = {
            "model": model,
            "input": input_data,
            "parameters": parameters
        }
        
        headers = self.session.headers.copy()
        headers["X-DashScope-Async"] = "enable"
        
        url = f"{self.base_url}{endpoint}"
        response = self._make_request("POST", url, headers=headers, json=task_data)
        
        task_id = response.get("output", {}).get("task_id")
        if not task_id:
            raise Exception(f"创建任务失败，未获取到task_id: {response}")
        
        return task_id
    
    def _execute_sync_task(self, model: str, input_data: Dict[str, Any], 
                          parameters: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        """执行同步任务并返回结果"""
        task_data = {
            "model": model,
            "input": input_data,
            "parameters": parameters
        }
        
        url = f"{self.base_url}{endpoint}"
        return self._make_request("POST", url, json=task_data)


class TextToImageGenerator:
    """文生图生成器"""
    
    def __init__(self, client: WanXiangUnifiedClient):
        self.client = client
    
    @handle_api_errors
    def generate_v1(self, prompt: str, style: str = "<auto>", 
                   negative_prompt: str = None, size: str = "1024*1024",
                   n: int = 1, seed: int = None, **kwargs) -> str:
        """文生图V1版"""
        print(f"🎨 [文生图V1] 开始生成:")
        print(f"   提示词: {prompt}")
        print(f"   风格: {style}")
        
        input_data = {"prompt": prompt}
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        if kwargs.get('ref_img'):
            input_data["ref_img"] = kwargs['ref_img']
        
        parameters = {
            "style": style,
            "size": size,
            "n": n,
            "ref_strength": kwargs.get('ref_strength', 0.5),
            "ref_mode": kwargs.get('ref_mode', 'repaint')
        }
        if seed:
            parameters["seed"] = seed
        
        task_id = self.client._create_async_task(
            model="wanx-v1",
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/text2image/image-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id)
        
        results = final_result.get("output", {}).get("results", [])
        if not results:
            raise Exception("任务完成但未获取到结果")
        
        image_url = results[0].get("url")
        if not image_url:
            raise Exception("未获取到图片URL")
        
        print(f"🎉 文生图V1完成: {image_url}")
        return image_url
    
    @handle_api_errors
    def generate_v2(self, prompt: str, model: str = "wanx2.1-t2i-turbo",
                   negative_prompt: str = None, size: str = "1024*1024",
                   n: int = 1, seed: int = None, **kwargs) -> str:
        """文生图V2版"""
        print(f"🎨 [文生图V2] 开始生成:")
        print(f"   模型: {model}")
        print(f"   提示词: {prompt}")
        
        input_data = {"prompt": prompt}
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        
        parameters = {
            "size": size,
            "n": n,
            "prompt_extend": kwargs.get('prompt_extend', True),
            "watermark": kwargs.get('watermark', False)
        }
        if seed:
            parameters["seed"] = seed
        
        task_id = self.client._create_async_task(
            model=model,
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/text2image/image-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id)
        
        results = final_result.get("output", {}).get("results", [])
        if not results:
            raise Exception("任务完成但未获取到结果")
        
        image_url = results[0].get("url")
        if not image_url:
            raise Exception("未获取到图片URL")
        
        print(f"🎉 文生图V2完成: {image_url}")
        return image_url


class TextToVideoGenerator:
    """文生视频生成器"""
    
    def __init__(self, client: WanXiangUnifiedClient):
        self.client = client
    
    @handle_api_errors
    def generate(self, prompt: str, model: str = "wanx2.1-t2v-turbo",
                size: str = "1280*720") -> str:
        """文生视频"""
        print(f"🎬 [文生视频] 开始生成:")
        print(f"   模型: {model}")
        print(f"   提示词: {prompt}")
        
        task_id = self.client._create_async_task(
            model=model,
            input_data={"prompt": prompt},
            parameters={"size": size},
            endpoint="/services/aigc/text2video/video-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=1800)
        
        video_url = final_result.get("output", {}).get("video_url")
        if not video_url:
            raise Exception("未获取到生成的视频URL")
        
        print(f"🎉 文生视频完成: {video_url}")
        return video_url


class ImageToVideoGenerator:
    """图生视频生成器"""
    
    def __init__(self, client: WanXiangUnifiedClient):
        self.client = client
    
    @handle_api_errors
    def generate_basic(self, img_url: str, prompt: str, 
                      model: str = "wanx2.1-i2v-turbo",
                      resolution: str = "720P", template: str = None) -> str:
        """基础图生视频"""
        print(f"🎬 [图生视频] 开始生成:")
        print(f"   图片: {img_url}")
        print(f"   提示词: {prompt}")
        
        input_data = {
            "img_url": img_url,
            "prompt": prompt
        }
        
        parameters = {"resolution": resolution}
        if template:
            parameters["template"] = template
        
        task_id = self.client._create_async_task(
            model=model,
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/image2video/video-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=1800)
        
        video_url = final_result.get("output", {}).get("video_url")
        if not video_url:
            raise Exception("未获取到生成的视频URL")
        
        print(f"🎉 图生视频完成: {video_url}")
        return video_url
    
    @handle_api_errors
    def generate_keyframe(self, first_frame_url: str, last_frame_url: str,
                         prompt: str, duration: int = 5, size: str = "1280*720") -> str:
        """首尾帧图生视频"""
        print(f"🎬 [首尾帧图生视频] 开始生成:")
        print(f"   首帧: {first_frame_url}")
        print(f"   尾帧: {last_frame_url}")
        
        # 转换尺寸格式
        resolution_map = {
            "1280*720": "720P",
            "1920*1080": "1080P",
            "1024*1024": "1024x1024",
            "720*1280": "720x1280"
        }
        resolution = resolution_map.get(size, "720P")
        
        input_data = {
            "first_frame_url": first_frame_url,
            "last_frame_url": last_frame_url,
            "prompt": prompt,
        }
        
        parameters = {
            "resolution": resolution,
            "prompt_extend": True
        }
        
        task_id = self.client._create_async_task(
            model="wanx2.1-kf2v-plus",
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/image2video/video-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=1800)
        
        # 尝试多个可能的字段路径
        output = final_result.get("output", {})
        video_url = (output.get("video_url") or 
                    output.get("video_urls", [None])[0] or
                    (output.get("results", [{}])[0].get("video_url")))
        
        if not video_url:
            available_fields = list(output.keys())
            raise Exception(f"未获取到生成的视频URL，可用字段: {available_fields}")
        
        print(f"🎉 首尾帧图生视频完成: {video_url}")
        return video_url


class CreativePosterGenerator:
    """创意海报生成器"""
    
    def __init__(self, client: WanXiangUnifiedClient):
        self.client = client
    
    @handle_api_errors
    def generate(self, title: str, sub_title: str = None, body_text: str = None,
                prompt_text_zh: str = None, wh_ratios: str = "竖版",
                lora_name: str = None, lora_weight: float = 0.8, **kwargs) -> str:
        """生成创意海报"""
        print(f"🎨 [创意海报] 开始生成:")
        print(f"   标题: {title}")
        print(f"   副标题: {sub_title}")
        
        input_data = {
            "title": title,
            "wh_ratios": wh_ratios,
            "generate_mode": kwargs.get('generate_mode', 'generate'),
            "generate_num": kwargs.get('generate_num', 1)
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
            input_data["ctrl_ratio"] = kwargs.get('ctrl_ratio', 0.7)
            input_data["ctrl_step"] = kwargs.get('ctrl_step', 0.7)
        
        task_id = self.client._create_async_task(
            model="wanx-poster-generation-v1",
            input_data=input_data,
            parameters={},
            endpoint="/services/aigc/text2image/image-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=600)
        
        image_urls = final_result.get("output", {}).get("render_urls", [])
        if not image_urls:
            raise Exception("未获取到创意海报图片URL")
        
        print(f"🎉 创意海报生成完成: {image_urls}")
        return image_urls[0] if isinstance(image_urls, list) else image_urls


class AITryOnGenerator:
    """AI试衣生成器"""
    
    def __init__(self, client: WanXiangUnifiedClient):
        self.client = client
    
    @handle_api_errors
    def generate_basic(self, person_image_url: str, top_garment_url: str = None,
                      bottom_garment_url: str = None, resolution: int = -1,
                      restore_face: bool = True) -> str:
        """基础版AI试衣"""
        print(f"👔 [AI试衣基础版] 开始生成:")
        print(f"   模特图: {person_image_url}")
        
        if not top_garment_url and not bottom_garment_url:
            raise ValueError("至少需要提供上装或下装图片")
        
        input_data = {"person_image_url": person_image_url}
        if top_garment_url:
            input_data["top_garment_url"] = top_garment_url
        if bottom_garment_url:
            input_data["bottom_garment_url"] = bottom_garment_url
        
        parameters = {
            "resolution": resolution,
            "restore_face": restore_face
        }
        
        task_id = self.client._create_async_task(
            model="aitryon",
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/image2image/image-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=600)
        
        image_url = final_result.get("output", {}).get("image_url", '')
        if not image_url:
            raise Exception("未获取到试衣效果图")
        
        print(f"🎉 AI试衣基础版完成: {image_url}")
        return image_url
    
    @handle_api_errors
    def generate_plus(self, person_image_url: str, top_garment_url: str = None,
                     bottom_garment_url: str = None, resolution: int = -1,
                     restore_face: bool = True) -> str:
        """Plus版AI试衣"""
        print(f"👔 [AI试衣Plus版] 开始生成:")
        
        if not top_garment_url and not bottom_garment_url:
            raise ValueError("至少需要提供上装或下装图片")
        
        input_data = {"person_image_url": person_image_url}
        if top_garment_url:
            input_data["top_garment_url"] = top_garment_url
        if bottom_garment_url:
            input_data["bottom_garment_url"] = bottom_garment_url
        
        parameters = {
            "resolution": resolution,
            "restore_face": restore_face
        }
        
        task_id = self.client._create_async_task(
            model="aitryon-plus",
            input_data=input_data,
            parameters=parameters,
            endpoint="/services/aigc/image2image/image-synthesis"
        )
        
        print(f"✅ 任务创建成功: {task_id}")
        final_result = self.client._wait_for_task(task_id, max_wait_time=600)
        
        image_url = final_result.get("output", {}).get("image_url", '')
        if not image_url:
            raise Exception("未获取到试衣效果图")
        
        print(f"🎉 AI试衣Plus版完成: {image_url}")
        return image_url


class WanXiangUnifiedAPI:
    """统一的通义万相API接口"""
    
    def __init__(self, api_key: str = None):
        self.client = WanXiangUnifiedClient(api_key)
        
        # 初始化各个生成器
        self.text_to_image = TextToImageGenerator(self.client)
        self.text_to_video = TextToVideoGenerator(self.client)
        self.image_to_video = ImageToVideoGenerator(self.client)
        self.creative_poster = CreativePosterGenerator(self.client)
        self.ai_tryon = AITryOnGenerator(self.client)
    
    # 快捷方法 - 向后兼容
    def get_text_to_image_v1(self, *args, **kwargs):
        return self.text_to_image.generate_v1(*args, **kwargs)
    
    def get_text_to_image_v2(self, *args, **kwargs):
        return self.text_to_image.generate_v2(*args, **kwargs)
    
    def get_text_to_video(self, *args, **kwargs):
        return self.text_to_video.generate(*args, **kwargs)
    
    def get_image_to_video(self, *args, **kwargs):
        return self.image_to_video.generate_basic(*args, **kwargs)
    
    def get_image_to_video_advanced(self, *args, **kwargs):
        return self.image_to_video.generate_keyframe(*args, **kwargs)
    
    def get_creative_poster(self, *args, **kwargs):
        return self.creative_poster.generate(*args, **kwargs)
    
    def get_ai_tryon_basic(self, *args, **kwargs):
        return self.ai_tryon.generate_basic(*args, **kwargs)
    
    def get_ai_tryon_plus(self, *args, **kwargs):
        return self.ai_tryon.generate_plus(*args, **kwargs)


# 全局实例 - 单例模式
_wanxiang_api = None

def get_wanxiang_api() -> WanXiangUnifiedAPI:
    """获取通义万相API实例（单例）"""
    global _wanxiang_api
    if _wanxiang_api is None:
        _wanxiang_api = WanXiangUnifiedAPI()
    return _wanxiang_api


# 向后兼容的全局函数
def get_text_to_image_v1(*args, **kwargs):
    """V1文生图 - 兼容性函数"""
    return get_wanxiang_api().get_text_to_image_v1(*args, **kwargs)

def get_text_to_image_v2(*args, **kwargs):
    """V2文生图 - 兼容性函数"""
    return get_wanxiang_api().get_text_to_image_v2(*args, **kwargs)

def get_text_to_video(*args, **kwargs):
    """文生视频 - 兼容性函数"""
    return get_wanxiang_api().get_text_to_video(*args, **kwargs)

def get_image_to_video(*args, **kwargs):
    """图生视频 - 兼容性函数"""
    return get_wanxiang_api().get_image_to_video(*args, **kwargs)

def get_image_to_video_advanced(*args, **kwargs):
    """高级图生视频 - 兼容性函数"""
    return get_wanxiang_api().get_image_to_video_advanced(*args, **kwargs)

def get_creative_poster(*args, **kwargs):
    """创意海报 - 兼容性函数"""
    return get_wanxiang_api().get_creative_poster(*args, **kwargs)

def get_ai_tryon_basic(*args, **kwargs):
    """AI试衣基础版 - 兼容性函数"""
    return get_wanxiang_api().get_ai_tryon_basic(*args, **kwargs)

def get_ai_tryon_plus(*args, **kwargs):
    """AI试衣Plus版 - 兼容性函数"""
    return get_wanxiang_api().get_ai_tryon_plus(*args, **kwargs)


if __name__ == "__main__":
    print("🔧 统一通义万相API模块加载完成")
    print("支持的功能:")
    print("  - 文生图 (V1/V2)")
    print("  - 文生视频")
    print("  - 图生视频 (基础/高级)")
    print("  - 创意海报")
    print("  - AI试衣 (基础/Plus)")

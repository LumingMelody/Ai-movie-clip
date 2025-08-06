"""
万相AI生成器集成

集成现有的万相接口，用于：
- 文生图
- 图生视频
- 视频风格化
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
import tempfile

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入tongyi_wangxiang中已经实现的功能
from core.clipgenerate.tongyi_wangxiang import (
    get_text_to_image_v1,
    get_text_to_image_v2,
    get_text_to_video,
    get_image_to_video,
    get_video_style_transform,
    get_background_generation,
    get_virtual_model_v1,
    get_virtual_model_v2,
    get_animate_anyone,
    get_emo_video,
    get_live_portrait
)


class WanxiangGenerator:
    """万相AI生成器 - 使用tongyi_wangxiang.py中的实现"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='wanx_')
    
    def generate_image(self, params: Dict[str, Any]) -> Optional[str]:
        """
        使用万相生成图片
        
        Args:
            params: {
                'prompt': str,        # 文本描述
                'model': str,         # 模型名称
                'resolution': str,    # 分辨率
                'style': str          # 风格
            }
        """
        prompt = params.get('prompt', '')
        model = params.get('model', 'wanx-v1')
        resolution = params.get('resolution', '1024*1024')
        style = params.get('style', '<auto>')
        
        try:
            # 根据模型选择不同的API
            if 'v2' in model or 'turbo' in model or 'plus' in model:
                # 使用V2版本
                result = get_text_to_image_v2(
                    prompt=prompt,
                    model=model,
                    size=resolution,
                    n=1
                )
            else:
                # 使用V1版本
                result = get_text_to_image_v1(
                    prompt=prompt,
                    style=style,
                    size=resolution,
                    n=1
                )
            
            return result
            
        except Exception as e:
            print(f"万相图片生成失败: {e}")
            
        return None
    
    def generate_video_from_image(self, params: Dict[str, Any]) -> Optional[str]:
        """
        使用万相从图片生成视频
        
        Args:
            params: {
                'image_url': str,     # 图片URL
                'prompt': str,        # 运动描述
                'duration': int,      # 视频时长
                'model': str          # 模型名称
            }
        """
        image_url = params.get('image_url', '')
        prompt = params.get('prompt', 'natural motion')
        model = params.get('model', 'wanx2.1-i2v-turbo')
        
        try:
            # 调用图生视频接口
            result = get_image_to_video(
                img_url=image_url,
                prompt=prompt,
                model=model
            )
            
            return result
            
        except Exception as e:
            print(f"万相视频生成失败: {e}")
            
        return None
    
    def generate_video_from_text(self, params: Dict[str, Any]) -> Optional[str]:
        """
        使用万相从文本生成视频
        
        Args:
            params: {
                'prompt': str,        # 视频描述
                'model': str,         # 模型名称
                'size': str           # 视频尺寸
            }
        """
        prompt = params.get('prompt', '')
        model = params.get('model', 'wanx2.1-t2v-turbo')
        size = params.get('size', '1280*720')
        
        try:
            # 调用文生视频接口
            result = get_text_to_video(
                prompt=prompt,
                model=model,
                size=size
            )
            
            return result
            
        except Exception as e:
            print(f"万相文生视频失败: {e}")
            
        return None
    
    def stylize_video(self, params: Dict[str, Any]) -> Optional[str]:
        """
        使用万相进行视频风格化
        
        Args:
            params: {
                'video_url': str,     # 视频URL
                'style': int,         # 风格ID (0-10)
                'video_fps': int      # 帧率
            }
        """
        video_url = params.get('video_url', '')
        style = params.get('style', 0)
        video_fps = params.get('video_fps', 15)
        
        # 如果传入的是风格名称，转换为ID
        if isinstance(style, str):
            style = self._get_style_id(style)
        
        try:
            # 调用视频风格化接口
            result = get_video_style_transform(
                video_url=video_url,
                style=style,
                video_fps=video_fps
            )
            
            return result
            
        except Exception as e:
            print(f"万相视频风格化失败: {e}")
            
        return None
    
    def _get_style_id(self, style_name: str) -> int:
        """获取风格ID"""
        style_map = {
            '3D卡通': 0,
            '手绘': 1,
            '二次元': 2,
            '黑白': 3,
            '复古': 4,
            '水彩': 5,
            '油画': 6,
            '梵高': 7,
            '赛博朋克': 8,
            '极简': 9,
            '写实': 10
        }
        return style_map.get(style_name, 0)


class UnifiedAIGenerator:
    """统一的AI生成器接口"""
    
    def __init__(self):
        self.wanxiang = WanxiangGenerator()
        # 这里可以添加其他AI生成器
        
    def generate(self, resource_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        统一的生成接口
        
        Args:
            resource_type: 资源类型 (image, video, audio)
            params: 生成参数
            
        Returns:
            生成结果
        """
        model = params.get('model', '')
        
        if resource_type == 'image':
            if 'wanx' in model or 'tongyi' in model:
                task_id = self.wanxiang.generate_image(params)
                if task_id:
                    return {
                        'task_id': task_id,
                        'status': 'processing',
                        'type': 'image'
                    }
                    
        elif resource_type == 'video':
            if params.get('source') == 'image':
                # 图生视频
                task_id = self.wanxiang.generate_video_from_image(params)
                if task_id:
                    return {
                        'task_id': task_id,
                        'status': 'processing',
                        'type': 'video'
                    }
            elif params.get('source') == 'style':
                # 视频风格化
                task_id = self.wanxiang.stylize_video(params)
                if task_id:
                    return {
                        'task_id': task_id,
                        'status': 'processing',
                        'type': 'video'
                    }
                    
        elif resource_type == 'audio':
            # 音频生成（待实现）
            pass
            
        return None
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取生成结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            结果信息
        """
        # 这里需要实现查询任务状态和获取结果的逻辑
        # 可以调用现有的查询接口
        return {
            'status': 'completed',
            'url': f'oss://generated/{task_id}.mp4'
        }
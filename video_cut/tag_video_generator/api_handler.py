#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
标签视频生成器的API处理器
用于处理前端请求并调用TagVideoGenerator
"""

import json
from typing import Dict, Any, Optional
from .tag_video_generator import TagVideoGenerator


class TagVideoAPIHandler:
    """标签视频API处理器"""
    
    def __init__(self, tag_materials_dir: str = "tag_materials"):
        self.generator = TagVideoGenerator(tag_materials_dir=tag_materials_dir)
    
    def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理前端请求
        
        请求格式示例:
        {
            "tags": ["黄山风景", "徽州特色餐", "屯溪老街", "无边泳池", "峡谷漂流"],
            "tag_videos": {
                "黄山风景": {
                    "video": ["assets/videos/huangshan.mp4", "assets/videos/huangshan1.mp4"]
                },
                "徽州特色餐": {
                    "video": ["assets/videos/huizhoucai.mp4"]
                }
            },
            "text_content": "可选的文案内容",  # 可选
            "subtitle_config": {  # 可选
                "font": "Arial",
                "font_size": 48,
                "color": "white"
            },
            "dynamic_tags": ["黄山", "美食", "古街"],  # 可选
            "duration_per_tag": 5.0,  # 每个标签的时长（秒）
            "output_format": {
                "fps": 30,
                "resolution": [1920, 1080]
            }
        }
        
        返回格式:
        {
            "success": true/false,
            "video_url": "生成的视频URL",
            "video_path": "视频文件路径",
            "message": "处理消息",
            "error": "错误信息（如果有）"
        }
        """
        
        try:
            print(f"[DEBUG-API] 收到请求数据类型: {type(request_data)}")
            print(f"[DEBUG-API] 请求数据键: {request_data.keys() if request_data else 'None'}")
            
            # 验证请求数据
            if not request_data:
                return {
                    'success': False,
                    'error': '请求数据为空'
                }
            
            # 解析请求参数
            tags = request_data.get('tags', [])
            tag_videos = request_data.get('tag_videos', {})
            
            print(f"[DEBUG-API] tags: {tags}")
            print(f"[DEBUG-API] tag_videos类型: {type(tag_videos)}")
            
            # 构建标签配置（保持标签顺序）
            tag_config = {}
            for tag in tags:
                if tag in tag_videos:
                    tag_config[tag] = tag_videos[tag]
                else:
                    # 如果某个标签没有视频，跳过
                    print(f"警告: 标签 '{tag}' 没有对应的视频配置")
            
            if not tag_config:
                return {
                    'success': False,
                    'error': '没有有效的标签视频配置'
                }
            
            # 获取其他参数
            text_content = request_data.get('text_content')
            subtitle_config = request_data.get('subtitle_config')
            dynamic_tags = request_data.get('dynamic_tags')
            duration_per_tag = request_data.get('duration_per_tag', 8.0)
            
            # 如果duration_per_tag是字典，确保键与标签匹配
            if isinstance(duration_per_tag, dict):
                print(f"[DEBUG-API] 使用每个标签单独的时长设置: {duration_per_tag}")
            
            # 输出格式参数 - 修复可能的None问题
            output_format = request_data.get('output_format')
            if output_format is None:
                output_format = {}
            fps = output_format.get('fps', 30) if output_format else 30
            resolution = tuple(output_format.get('resolution', [1920, 1080]) if output_format else [1920, 1080])
            
            # 打印调试信息
            print(f"[DEBUG] 调用生成器，标签配置: {list(tag_config.keys())}")
            
            # 调用生成器
            try:
                result = self.generator.process_request({
                    'tag_config': tag_config,
                    'text_content': text_content,
                    'subtitle_config': subtitle_config,
                    'dynamic_tags': dynamic_tags,
                    'duration_per_tag': duration_per_tag
                })
            except Exception as gen_error:
                print(f"[ERROR] 生成器处理失败: {gen_error}")
                import traceback
                traceback.print_exc()
                return {
                    'success': False,
                    'error': f'生成器处理失败: {str(gen_error)}'
                }
            
            print(f"[DEBUG] 生成器返回结果: {result}")
            
            if result and result.get('success'):
                # 上传到OSS或返回本地路径
                video_path = result.get('video_path')
                video_url = self._upload_to_oss(video_path) if hasattr(self, '_upload_to_oss') else video_path
                
                return {
                    'success': True,
                    'video_url': video_url,
                    'video_path': video_path,
                    'message': '视频生成成功'
                }
            else:
                error_msg = result.get('error', '生成失败') if result else '生成器返回空结果'
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            import traceback
            print(f"[ERROR-API] 处理请求异常: {e}")
            print(f"[ERROR-API] 异常类型: {type(e)}")
            print(f"[ERROR-API] 堆栈跟踪:")
            traceback.print_exc()
            return {
                'success': False,
                'error': f'处理请求失败: {str(e)}'
            }
    
    def create_tag_config_from_frontend(
        self,
        tags: list,
        video_mapping: Dict[str, list]
    ) -> Dict[str, Dict[str, list]]:
        """
        根据前端传入的标签顺序和视频映射创建标签配置
        
        Args:
            tags: 标签列表（保持顺序）
            video_mapping: 标签到视频列表的映射
            
        Returns:
            标签配置字典
        """
        tag_config = {}
        for tag in tags:
            if tag in video_mapping:
                tag_config[tag] = {"video": video_mapping[tag]}
        
        return tag_config


# 示例：如何在FastAPI中使用
def create_fastapi_endpoint():
    """
    创建FastAPI端点的示例代码
    
    在app.py中添加:
    
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict, List, Optional, Any
    from video_cut.tag_video_generator.api_handler import TagVideoAPIHandler
    
    app = FastAPI()
    tag_video_handler = TagVideoAPIHandler()
    
    class TagVideoRequest(BaseModel):
        tags: List[str]
        tag_videos: Dict[str, Dict[str, List[str]]]
        text_content: Optional[str] = None
        subtitle_config: Optional[Dict[str, Any]] = None
        dynamic_tags: Optional[List[str]] = None
        duration_per_tag: float = 5.0
        output_format: Optional[Dict[str, Any]] = None
    
    @app.post("/video/generate-from-tags")
    async def generate_video_from_tags(request: TagVideoRequest):
        try:
            result = tag_video_handler.handle_request(request.dict())
            if result['success']:
                return result
            else:
                raise HTTPException(status_code=400, detail=result.get('error', '生成失败'))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    """
    pass


if __name__ == "__main__":
    # 测试API处理器
    handler = TagVideoAPIHandler()
    
    # 模拟前端请求
    test_request = {
        "tags": ["黄山风景", "徽州特色餐", "屯溪老街"],
        "tag_videos": {
            "黄山风景": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "徽州特色餐": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            },
            "屯溪老街": {
                "video": ["/Users/luming/Downloads/老登.mp4"]
            }
        },
        "duration_per_tag": 3.0,
        "dynamic_tags": ["黄山", "美食", "古街"]
    }
    
    result = handler.handle_request(test_request)
    print(json.dumps(result, ensure_ascii=False, indent=2))
"""
AuraRender 主接口

提供统一的API接口，集成到现有系统
"""

import json
import os
import sys
from typing import Dict, Any, Optional
import tempfile
from datetime import datetime

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .intelligent_layer.orchestrator import AuraOrchestrator
from .execution_layer.executor import AuraExecutor
from .ai_generators.wanxiang_integration import UnifiedAIGenerator


class AuraRenderInterface:
    """AuraRender 主接口类"""
    
    def __init__(self):
        self.orchestrator = AuraOrchestrator()
        self.ai_generator = UnifiedAIGenerator()
        self.executor = AuraExecutor(ai_generators={
            'wanxiang': self.ai_generator
        })
        
    def create_video(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建视频的主入口
        
        Args:
            request: {
                'natural_language': str,      # 自然语言描述
                'video_url': Optional[str],   # 原始视频URL
                'mode': str,                  # sync/async
                'output_path': Optional[str], # 输出路径
                'preferences': Optional[Dict] # 用户偏好设置
            }
        
        Returns:
            {
                'status': str,
                'video_url': str,
                'script': Dict,  # 生成的执行脚本
                'metadata': Dict
            }
        """
        try:
            # 处理输入视频资源
            if request.get('video_url'):
                request['resources'] = request.get('resources', {})
                request['resources']['videos'] = request['resources'].get('videos', [])
                request['resources']['videos'].append({
                    'id': 'input_video',
                    'source': request['video_url']
                })
            
            # 1. 智能编排 - 生成执行脚本
            print("开始智能编排...")
            script = self.orchestrator.orchestrate(request)
            
            # 保存脚本供调试
            script_path = self._save_script(script)
            print(f"执行脚本已保存: {script_path}")
            
            # 2. 处理AI生成资源
            print("处理AI生成资源...")
            script = self._process_ai_resources(script)
            
            # 3. 机械执行 - 根据脚本生成视频
            print("开始执行视频渲染...")
            output_path = request.get('output_path') or self._generate_output_path()
            video_path = self.executor.execute(script, output_path)
            
            # 4. 上传到OSS（如果需要）
            video_url = self._upload_to_oss(video_path) if request.get('upload_oss', True) else video_path
            
            return {
                'status': 'success',
                'video_url': video_url,
                'script': script,
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'script_path': script_path,
                    'video_type': script['project']['type'],
                    'style': script['project']['style'],
                    'duration': script['project']['duration']
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'metadata': {
                    'created_at': datetime.now().isoformat()
                }
            }
    
    def create_video_from_script(self, script: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        直接从脚本创建视频（跳过智能编排）
        
        Args:
            script: 执行脚本
            output_path: 输出路径
            
        Returns:
            执行结果
        """
        try:
            # 处理AI生成资源
            script = self._process_ai_resources(script)
            
            # 执行渲染
            output_path = output_path or self._generate_output_path()
            video_path = self.executor.execute(script, output_path)
            
            return {
                'status': 'success',
                'video_path': video_path,
                'metadata': {
                    'created_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _process_ai_resources(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """处理脚本中的AI生成资源"""
        resources = script.get('resources', {})
        
        # 处理需要AI生成的资源
        for resource_type in ['videos', 'images', 'audio']:
            for resource in resources.get(resource_type, []):
                if resource.get('source') == 'ai_generated':
                    # 生成资源
                    result = self.ai_generator.generate(
                        resource_type[:-1],  # 去掉复数s
                        resource['params']
                    )
                    
                    if result and result.get('status') == 'processing':
                        # 等待生成完成（简化处理）
                        # 实际应该异步处理或轮询
                        task_result = self.ai_generator.get_result(result['task_id'])
                        if task_result and task_result.get('url'):
                            resource['source'] = task_result['url']
        
        return script
    
    def _save_script(self, script: Dict[str, Any]) -> str:
        """保存执行脚本"""
        script_dir = os.path.join(project_root, 'output', 'aura_scripts')
        os.makedirs(script_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        script_path = os.path.join(script_dir, f'script_{timestamp}.json')
        
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
            
        return script_path
    
    def _generate_output_path(self) -> str:
        """生成输出路径"""
        output_dir = os.path.join(project_root, 'output', 'aura_videos')
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(output_dir, f'aura_video_{timestamp}.mp4')
    
    def _upload_to_oss(self, video_path: str) -> str:
        """上传视频到OSS"""
        # 这里调用现有的OSS上传功能
        # 简化处理，返回本地路径
        return video_path


# 便捷函数
def create_aura_video(natural_language: str, video_url: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    便捷函数：创建AuraRender视频
    
    Args:
        natural_language: 自然语言描述
        video_url: 原始视频URL（可选）
        **kwargs: 其他参数
        
    Returns:
        创建结果
    """
    interface = AuraRenderInterface()
    request = {
        'natural_language': natural_language,
        'video_url': video_url,
        **kwargs
    }
    return interface.create_video(request)
# -*- coding: utf-8 -*-
"""
Coze API客户端封装模块
统一处理Coze API调用、工作流创建和响应处理
"""

import json
from typing import Dict, Any, Optional, Union
from cozepy import COZE_CN_BASE_URL, Coze, TokenAuth
from doubaoconfigs import coze_api_token
from .config import CozeConfig, get_workflow_id


class CozeClient:
    """Coze API客户端封装类"""
    
    def __init__(self, api_token: str = None, base_url: str = COZE_CN_BASE_URL):
        """
        初始化Coze客户端
        
        Args:
            api_token: API token，默认使用配置文件中的token
            base_url: API基础URL
        """
        self.api_token = api_token or coze_api_token
        self.base_url = base_url
        self.client = Coze(auth=TokenAuth(token=self.api_token), base_url=self.base_url)
    
    def run_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行Coze工作流
        
        Args:
            workflow_id: 工作流ID
            parameters: 工作流参数
            
        Returns:
            解析后的响应数据
            
        Raises:
            Exception: 工作流执行失败时抛出异常
        """
        try:
            print(f"🚀 开始调用Coze工作流: {workflow_id}")
            print(f"📋 参数: {parameters}")
            
            # 调用工作流
            workflow = self.client.workflows.runs.create(
                workflow_id=workflow_id,
                parameters=parameters
            )
            
            print(f"✅ 工作流执行成功")
            print(f"📄 原始响应: {workflow.data}")
            
            # 解析响应
            response = json.loads(workflow.data)
            return response
            
        except Exception as e:
            print(f"❌ Coze工作流执行失败: {str(e)}")
            raise
    
    def upload_file(self, file_path: str) -> str:
        """
        上传文件到Coze
        
        Args:
            file_path: 本地文件路径
            
        Returns:
            文件ID
            
        Raises:
            Exception: 上传失败时抛出异常
        """
        try:
            print(f"📤 上传文件到Coze: {file_path}")
            
            # 这里需要实现具体的文件上传逻辑
            # 根据实际的Coze API文档实现
            pass
            
        except Exception as e:
            print(f"❌ 文件上传失败: {str(e)}")
            raise


# 工作流ID常量
class WorkflowIDs:
    """Coze工作流ID常量"""
    
    ADVERTISEMENT = '7499113029830049819'
    DIGITAL_HUMAN = '7494924152006295571'
    CLOTHES_SCENE = '7494924152006295571'
    # 添加更多工作流ID...


# 便捷函数
def create_coze_client() -> CozeClient:
    """创建默认的Coze客户端"""
    return CozeClient()


def run_advertisement_workflow(
    company_name: str, 
    service: str, 
    topic: str, 
    content: Optional[str] = None,
    need_change: bool = False
) -> Dict[str, Any]:
    """
    运行广告生成工作流的便捷函数
    
    Args:
        company_name: 公司名称
        service: 服务类型
        topic: 主题
        content: 内容（可选）
        need_change: 是否需要更改
        
    Returns:
        工作流响应数据
    """
    client = create_coze_client()
    parameters = {
        "company_name": company_name,
        "service": service,
        "topic": topic,
        "content": content,
        "need_change": need_change
    }
    
    return client.run_workflow(WorkflowIDs.ADVERTISEMENT, parameters)


def run_clothes_scene_workflow(
    has_figure: bool,
    clothes_file_id: str,
    description: str,
    is_down: bool = True
) -> Dict[str, Any]:
    """
    运行服装场景生成工作流的便捷函数
    
    Args:
        has_figure: 是否有人物
        clothes_file_id: 服装图片文件ID
        description: 描述
        is_down: 是否下载
        
    Returns:
        工作流响应数据
    """
    client = create_coze_client()
    parameters = {
        "has_figure": has_figure,
        "clothes": json.dumps({"file_id": clothes_file_id}),
        "description": description,
        "is_down": is_down,
    }
    
    return client.run_workflow(WorkflowIDs.CLOTHES_SCENE, parameters)
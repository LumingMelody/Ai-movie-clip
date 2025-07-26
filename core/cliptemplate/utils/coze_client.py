"""
Coze API客户端 - 统一处理Coze工作流调用
"""
import json
import requests
from typing import Dict, Any, Optional
from cozepy import COZE_CN_BASE_URL, Coze, TokenAuth
from doubaoconfigs import coze_api_token

class CozeWorkflowClient:
    """Coze工作流客户端"""
    
    def __init__(self, base_url: str = COZE_CN_BASE_URL):
        self.coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=base_url)
        
    def call_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用Coze工作流
        
        Args:
            workflow_id: 工作流ID
            parameters: 工作流参数
            
        Returns:
            工作流响应数据
        """
        try:
            workflow = self.coze.workflows.runs.create(
                workflow_id=workflow_id, 
                parameters=parameters
            )
            return json.loads(workflow.data)
        except Exception as e:
            print(f"❌ Coze工作流调用失败: {e}")
            raise
            
    def upload_file(self, file_path: str, purpose: str = "assistant") -> Optional[str]:
        """
        上传文件到Coze
        
        Args:
            file_path: 文件路径
            purpose: 文件用途
            
        Returns:
            文件ID或None
        """
        try:
            with open(file_path, 'rb') as f:
                file_obj = self.coze.files.upload(file=f, purpose=purpose)
                return file_obj.id
        except Exception as e:
            print(f"❌ 文件上传失败: {e}")
            return None

# 全局客户端实例
coze_client = CozeWorkflowClient()
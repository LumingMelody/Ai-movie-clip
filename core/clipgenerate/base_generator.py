# -*- coding: utf-8 -*-
"""
统一的生成器基础架构
为所有AI生成模块提供统一的基础功能和错误处理
"""

import os
import json
import time
import uuid
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError

import requests
import dashscope
from core.utils.env_config import get_dashscope_api_key


class APIClientBase(ABC):
    """API客户端基础类"""
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key or get_dashscope_api_key()
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """设置会话"""
        self.session.headers.update({
            'User-Agent': 'AI-Movie-Clip/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    @abstractmethod
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        pass
    
    def _handle_error(self, response: requests.Response) -> None:
        """统一错误处理"""
        if response.status_code == 401:
            raise Exception("API密钥无效或已过期")
        elif response.status_code == 403:
            raise Exception("API访问被拒绝，请检查权限")
        elif response.status_code == 429:
            raise Exception("API请求频率超限，请稍后重试")
        elif response.status_code >= 500:
            raise Exception(f"服务器内部错误: {response.status_code}")
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
            except:
                error_msg = f'HTTP {response.status_code}: {response.text}'
            raise Exception(f"API请求失败: {error_msg}")


class TongyiClient(APIClientBase):
    """通义千问API客户端"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """使用DashScope SDK发送请求"""
        # 通义千问使用DashScope SDK，不直接使用HTTP请求
        pass
    
    def generate_response(self, template: str, content: str, 
                         model: str = "qwen-plus", **kwargs) -> str:
        """生成文本响应"""
        try:
            messages = [
                {'role': 'system', 'content': template},
                {'role': 'user', 'content': content}
            ]
            
            response = dashscope.Generation.call(
                api_key=self.api_key,
                model=model,
                messages=messages,
                result_format='message',
                enable_search=kwargs.get('enable_search', True),
                temperature=kwargs.get('temperature', 0.8),
                max_tokens=kwargs.get('max_tokens', 2000)
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"通义千问API调用失败: {response.message}")
                
        except Exception as e:
            raise Exception(f"文本生成失败: {str(e)}")


class WanXiangClient(APIClientBase):
    """通义万相API客户端"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}"
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


class CozeClient(APIClientBase):
    """Coze工作流API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        super().__init__(api_key)
        # Coze使用专门的SDK，这里保持兼容性
        from cozepy import COZE_CN_BASE_URL
        from doubaoconfigs import coze_api_token
        
        self.coze_api_token = coze_api_token
        self.base_url = base_url or COZE_CN_BASE_URL
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Coze使用专门的SDK"""
        pass
    
    def run_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """运行Coze工作流"""
        try:
            from cozepy import Coze, TokenAuth
            
            coze = Coze(auth=TokenAuth(token=self.coze_api_token), base_url=self.base_url)
            
            workflow = coze.workflows.runs.create(
                workflow_id=workflow_id,
                parameters=parameters
            )
            
            return json.loads(workflow.data)
            
        except Exception as e:
            raise Exception(f"Coze工作流执行失败: {str(e)}")


class BaseGenerator(ABC):
    """生成器基础类"""
    
    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key or get_dashscope_api_key()
        self.tongyi_client = TongyiClient(self.api_key)
        self.wanxiang_client = WanXiangClient(self.api_key)
        self.coze_client = CozeClient()
        
        # 配置参数
        self.default_timeout = kwargs.get('timeout', 300)
        self.retry_count = kwargs.get('retry_count', 3)
        self.retry_delay = kwargs.get('retry_delay', 1)
        
        # 初始化子类特定配置
        self._setup_generator()
    
    def _setup_generator(self):
        """子类可重写此方法进行特定初始化"""
        pass
    
    @abstractmethod
    def generate(self, **kwargs) -> Union[str, Dict[str, Any]]:
        """执行生成任务"""
        pass
    
    def _validate_inputs(self, **kwargs) -> None:
        """验证输入参数"""
        pass
    
    def _process_result(self, result: Any) -> Union[str, Dict[str, Any]]:
        """处理生成结果"""
        return result
    
    def _retry_on_failure(self, func, *args, **kwargs):
        """失败重试机制"""
        last_exception = None
        
        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.retry_count - 1:
                    print(f"第{attempt + 1}次尝试失败: {str(e)}，{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"所有重试尝试都失败了")
        
        raise last_exception
    
    def generate_with_retry(self, **kwargs) -> Union[str, Dict[str, Any]]:
        """带重试的生成方法"""
        try:
            # 验证输入
            self._validate_inputs(**kwargs)
            
            # 执行生成（带重试）
            result = self._retry_on_failure(self.generate, **kwargs)
            
            # 处理结果
            return self._process_result(result)
            
        except Exception as e:
            print(f"生成失败: {str(e)}")
            print(f"错误详情: {traceback.format_exc()}")
            raise


class TextGenerator(BaseGenerator):
    """文本生成器"""
    
    def generate(self, template: str, content: str, **kwargs) -> str:
        """生成文本内容"""
        return self.tongyi_client.generate_response(
            template=template,
            content=content,
            **kwargs
        )


class ImageGenerator(BaseGenerator):
    """图像生成器"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成图像"""
        from .tongyi_wangxiang import get_text_to_image_v2
        
        return get_text_to_image_v2(
            prompt=prompt,
            model=kwargs.get('model', 'wanx2.1-t2i-turbo'),
            size=kwargs.get('size', '1024*1024'),
            n=kwargs.get('n', 1)
        )


class VideoGenerator(BaseGenerator):
    """视频生成器"""
    
    def generate(self, **kwargs) -> str:
        """生成视频 - 由子类实现具体逻辑"""
        raise NotImplementedError("子类必须实现generate方法")


class WorkflowGenerator(BaseGenerator):
    """工作流生成器"""
    
    def __init__(self, workflow_id: str, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
    
    def generate(self, **kwargs) -> Dict[str, Any]:
        """执行工作流"""
        return self.coze_client.run_workflow(
            workflow_id=self.workflow_id,
            parameters=kwargs
        )


class GeneratorFactory:
    """生成器工厂"""
    
    _generators = {
        'text': TextGenerator,
        'image': ImageGenerator,
        'video': VideoGenerator,
        'workflow': WorkflowGenerator,
    }
    
    @classmethod
    def create_generator(cls, generator_type: str, **kwargs) -> BaseGenerator:
        """创建生成器实例"""
        if generator_type not in cls._generators:
            raise ValueError(f"不支持的生成器类型: {generator_type}")
        
        generator_class = cls._generators[generator_type]
        return generator_class(**kwargs)
    
    @classmethod
    def register_generator(cls, name: str, generator_class: type):
        """注册新的生成器类型"""
        cls._generators[name] = generator_class


# 错误处理装饰器
def handle_api_errors(func):
    """API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"API调用失败 [{func.__name__}]: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"调用参数: args={args}, kwargs={kwargs}")
            print(f"错误堆栈: {traceback.format_exc()}")
            raise Exception(error_msg)
    return wrapper


# 异步任务执行器
class AsyncTaskExecutor:
    """异步任务执行器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def execute_parallel(self, tasks: List[tuple], timeout: int = 300) -> List[Any]:
        """并行执行多个任务"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = []
            for func, args, kwargs in tasks:
                future = executor.submit(func, *args, **kwargs)
                futures.append(future)
            
            # 收集结果
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                except TimeoutError:
                    results.append(Exception(f"任务{i}超时"))
                except Exception as e:
                    results.append(e)
        
        return results


# 配置管理
class GeneratorConfig:
    """生成器配置管理"""
    
    DEFAULT_CONFIG = {
        'timeout': 300,
        'retry_count': 3,
        'retry_delay': 1,
        'max_workers': 4,
        'enable_cache': True,
        'cache_ttl': 3600,
    }
    
    @classmethod
    def get_config(cls, key: str, default=None):
        """获取配置值"""
        return os.environ.get(f"GENERATOR_{key.upper()}", 
                            cls.DEFAULT_CONFIG.get(key, default))
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        config = cls.DEFAULT_CONFIG.copy()
        
        # 从环境变量覆盖
        for key in config.keys():
            env_value = os.environ.get(f"GENERATOR_{key.upper()}")
            if env_value:
                # 尝试转换类型
                if isinstance(config[key], int):
                    config[key] = int(env_value)
                elif isinstance(config[key], float):
                    config[key] = float(env_value)
                elif isinstance(config[key], bool):
                    config[key] = env_value.lower() in ('true', '1', 'yes')
                else:
                    config[key] = env_value
        
        return config

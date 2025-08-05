# -*- coding: utf-8 -*-
"""
统一的视频生成器模块
重构所有视频生成功能，消除代码重复
"""

import os
import json
from typing import Dict, Any, Optional, Union, List
from .base_generator import (
    BaseGenerator, WorkflowGenerator, GeneratorFactory, 
    handle_api_errors, AsyncTaskExecutor
)


# 工作流ID配置
WORKFLOW_IDS = {
    'advertisement': '7499113029830049819',
    'big_word': '7502316696242929674', 
    'catmeme': '7499113029830049822',
    'clicktype': '7499113029830049820',
    'incitement': '7499113029830049823',
    'introduction': '7499113029830049824',
    'sinology': '7499113029830049825',
    'stickman': '7499113029830049826',
    'clothes_scene': '7494924152006295571',
    'cover_analysis': '7499113029830049828',
}


class CozeVideoGenerator(WorkflowGenerator):
    """基于Coze工作流的视频生成器基类"""
    
    def __init__(self, workflow_type: str, **kwargs):
        if workflow_type not in WORKFLOW_IDS:
            raise ValueError(f"不支持的工作流类型: {workflow_type}")
        
        workflow_id = WORKFLOW_IDS[workflow_type]
        super().__init__(workflow_id=workflow_id, **kwargs)
        self.workflow_type = workflow_type
    
    def _validate_inputs(self, **kwargs) -> None:
        """验证输入参数 - 子类可重写"""
        pass
    
    def _process_result(self, result: Dict[str, Any]) -> str:
        """处理工作流结果 - 子类可重写"""
        # 默认处理逻辑
        if isinstance(result, dict):
            # 尝试从结果中提取视频路径
            return self._extract_video_path(result)
        return str(result)
    
    def _extract_video_path(self, result: Dict[str, Any]) -> str:
        """从结果中提取视频路径"""
        # 这里需要根据实际的转换逻辑来实现
        # 暂时返回原始结果的字符串表示
        return str(result)


class AdvertisementGenerator(CozeVideoGenerator):
    """广告视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('advertisement', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        required_fields = ['company_name', 'service', 'topic']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"缺少必需参数: {field}")
    
    @handle_api_errors
    def generate(self, company_name: str, service: str, topic: str, 
                content: str = None, need_change: bool = False, **kwargs) -> str:
        """生成广告视频"""
        print(f"🎬 [广告视频] 开始生成:")
        print(f"   公司名称: {company_name}")
        print(f"   服务类型: {service}")
        print(f"   主题: {topic}")
        
        parameters = {
            "company_name": company_name,
            "service": service,
            "topic": topic,
            "content": content,
            "need_change": need_change
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [广告视频] 生成完成")
        return self._process_result(result)


class BigWordGenerator(CozeVideoGenerator):
    """大字视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('big_word', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        required_fields = ['company_name', 'title', 'product', 'description']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"缺少必需参数: {field}")
    
    @handle_api_errors
    def generate(self, company_name: str, title: str, product: str, 
                description: str, content: str = None, **kwargs) -> str:
        """生成大字视频"""
        print(f"📝 [大字视频] 开始生成:")
        print(f"   公司名称: {company_name}")
        print(f"   标题: {title}")
        print(f"   产品: {product}")
        
        parameters = {
            "author": company_name,
            "title": title,
            "product": product,
            "description": description,
            "content": content,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [大字视频] 生成完成")
        return self._process_result(result)


class CatMemeGenerator(CozeVideoGenerator):
    """猫咪对话视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('catmeme', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        required_fields = ['author', 'title']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"缺少必需参数: {field}")
    
    @handle_api_errors
    def generate(self, author: str, title: str, content: str = None, **kwargs) -> str:
        """生成猫咪对话视频"""
        print(f"🐱 [猫咪对话] 开始生成:")
        print(f"   作者: {author}")
        print(f"   标题: {title}")
        
        parameters = {
            "author": author,
            "title": title,
            "content": content,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [猫咪对话] 生成完成")
        return self._process_result(result)


class ClickTypeGenerator(CozeVideoGenerator):
    """点击类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('clicktype', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        if not kwargs.get('title'):
            raise ValueError("缺少必需参数: title")
    
    @handle_api_errors
    def generate(self, title: str, content: str = None, **kwargs) -> str:
        """生成点击类视频"""
        print(f"👆 [点击类视频] 开始生成:")
        print(f"   标题: {title}")
        
        parameters = {
            "title": title,
            "content": content,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [点击类视频] 生成完成")
        return self._process_result(result)


class IncitementGenerator(CozeVideoGenerator):
    """煽动类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('incitement', **kwargs)
    
    @handle_api_errors
    def generate(self, title: str, **kwargs) -> str:
        """生成煽动类视频"""
        print(f"🔥 [煽动类视频] 开始生成:")
        print(f"   标题: {title}")
        
        parameters = {"title": title}
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [煽动类视频] 生成完成")
        return self._process_result(result)


class IntroductionGenerator(CozeVideoGenerator):
    """介绍类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('introduction', **kwargs)
    
    @handle_api_errors
    def generate(self, title: str, content: str = None, **kwargs) -> str:
        """生成介绍类视频"""
        print(f"📖 [介绍类视频] 开始生成:")
        print(f"   标题: {title}")
        
        parameters = {
            "title": title,
            "content": content,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [介绍类视频] 生成完成")
        return self._process_result(result)


class SinologyGenerator(CozeVideoGenerator):
    """国学类视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('sinology', **kwargs)
    
    @handle_api_errors
    def generate(self, title: str, content: str = None, **kwargs) -> str:
        """生成国学类视频"""
        print(f"📚 [国学类视频] 开始生成:")
        print(f"   标题: {title}")
        
        parameters = {
            "title": title,
            "content": content,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [国学类视频] 生成完成")
        return self._process_result(result)


class StickmanGenerator(CozeVideoGenerator):
    """火柴人视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('stickman', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        required_fields = ['author', 'title']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"缺少必需参数: {field}")
    
    @handle_api_errors
    def generate(self, author: str, title: str, content: str = None, 
                lift_text: str = "科普动画", **kwargs) -> str:
        """生成火柴人视频"""
        print(f"🚶 [火柴人视频] 开始生成:")
        print(f"   作者: {author}")
        print(f"   标题: {title}")
        
        parameters = {
            "author": author,
            "title": title,
            "content": content,
            "lift_text": lift_text,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [火柴人视频] 生成完成")
        return self._process_result(result)


class ClothesSceneGenerator(CozeVideoGenerator):
    """服装场景视频生成器"""
    
    def __init__(self, **kwargs):
        super().__init__('clothes_scene', **kwargs)
    
    def _validate_inputs(self, **kwargs) -> None:
        required_fields = ['clothesurl', 'description']
        for field in required_fields:
            if not kwargs.get(field):
                raise ValueError(f"缺少必需参数: {field}")
    
    @handle_api_errors
    def generate(self, has_figure: bool, clothesurl: str, description: str,
                is_down: bool = True, **kwargs) -> str:
        """生成服装场景视频"""
        print(f"👗 [服装场景] 开始生成:")
        print(f"   服装URL: {clothesurl}")
        print(f"   描述: {description}")
        
        parameters = {
            "has_figure": has_figure,
            "clothes": clothesurl,
            "description": description,
            "is_down": is_down,
        }
        
        result = self.coze_client.run_workflow(self.workflow_id, parameters)
        print(f"✅ [服装场景] 生成完成")
        return self._process_result(result)


# 注册所有生成器
GeneratorFactory.register_generator('advertisement', AdvertisementGenerator)
GeneratorFactory.register_generator('big_word', BigWordGenerator)
GeneratorFactory.register_generator('catmeme', CatMemeGenerator)
GeneratorFactory.register_generator('clicktype', ClickTypeGenerator)
GeneratorFactory.register_generator('incitement', IncitementGenerator)
GeneratorFactory.register_generator('introduction', IntroductionGenerator)
GeneratorFactory.register_generator('sinology', SinologyGenerator)
GeneratorFactory.register_generator('stickman', StickmanGenerator)
GeneratorFactory.register_generator('clothes_scene', ClothesSceneGenerator)


# 统一的生成函数
@handle_api_errors
def generate_video_unified(generator_type: str, **kwargs) -> str:
    """
    统一的视频生成入口函数
    
    Args:
        generator_type: 生成器类型 (advertisement, big_word, catmeme等)
        **kwargs: 生成参数
        
    Returns:
        生成的视频路径
    """
    print(f"🚀 [统一生成器] 开始生成 {generator_type} 视频")
    
    generator = GeneratorFactory.create_generator(generator_type)
    result = generator.generate_with_retry(**kwargs)
    
    print(f"🎉 [统一生成器] {generator_type} 视频生成完成: {result}")
    return result


# 批量生成函数
@handle_api_errors
def generate_videos_batch(requests: List[Dict[str, Any]], 
                         max_workers: int = 4) -> List[Union[str, Exception]]:
    """
    批量生成视频
    
    Args:
        requests: 请求列表，每个请求包含 {'type': 'xxx', 'params': {...}}
        max_workers: 最大并发数
        
    Returns:
        生成结果列表
    """
    print(f"🚀 [批量生成] 开始处理 {len(requests)} 个视频生成请求")
    
    executor = AsyncTaskExecutor(max_workers=max_workers)
    
    # 构建任务列表
    tasks = []
    for i, request in enumerate(requests):
        generator_type = request['type']
        params = request.get('params', {})
        
        task = (generate_video_unified, (generator_type,), params)
        tasks.append(task)
    
    # 并行执行
    results = executor.execute_parallel(tasks, timeout=600)
    
    # 统计结果
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    print(f"🎉 [批量生成] 完成: {success_count}/{len(requests)} 成功")
    
    return results


# 向后兼容的函数 - 保持原有接口不变
def get_video_advertisement(company_name: str, service: str, topic: str, 
                          content: str = None, need_change: bool = False) -> str:
    """广告视频生成 - 兼容性函数"""
    return generate_video_unified('advertisement', 
                                company_name=company_name,
                                service=service,
                                topic=topic,
                                content=content,
                                need_change=need_change)


def get_big_word(company_name: str, title: str, product: str, 
                description: str, content: str = None) -> str:
    """大字视频生成 - 兼容性函数"""
    return generate_video_unified('big_word',
                                company_name=company_name,
                                title=title,
                                product=product,
                                description=description,
                                content=content)


def get_catmeme(author: str, title: str, content: str = None) -> str:
    """猫咪对话视频生成 - 兼容性函数"""
    return generate_video_unified('catmeme',
                                author=author,
                                title=title,
                                content=content)


def get_clicktype(title: str, content: str = None) -> str:
    """点击类视频生成 - 兼容性函数"""
    return generate_video_unified('clicktype',
                                title=title,
                                content=content)


def get_incitement(title: str) -> str:
    """煽动类视频生成 - 兼容性函数"""
    return generate_video_unified('incitement', title=title)


def get_introduction(title: str, content: str = None) -> str:
    """介绍类视频生成 - 兼容性函数"""
    return generate_video_unified('introduction',
                                title=title,
                                content=content)


def get_sinology(title: str, content: str = None) -> str:
    """国学类视频生成 - 兼容性函数"""
    return generate_video_unified('sinology',
                                title=title,
                                content=content)


def get_stickman(author: str, title: str, content: str = None, 
                lift_text: str = "科普动画") -> str:
    """火柴人视频生成 - 兼容性函数"""
    return generate_video_unified('stickman',
                                author=author,
                                title=title,
                                content=content,
                                lift_text=lift_text)


def get_clothes_scene(has_figure: bool, clothesurl: str, description: str,
                     is_down: bool = True) -> str:
    """服装场景视频生成 - 兼容性函数"""
    return generate_video_unified('clothes_scene',
                                has_figure=has_figure,
                                clothesurl=clothesurl,
                                description=description,
                                is_down=is_down)


if __name__ == "__main__":
    # 测试统一生成器
    print("🔧 统一视频生成器模块加载完成")
    print("支持的生成器类型:")
    for gen_type in WORKFLOW_IDS.keys():
        print(f"  - {gen_type}")

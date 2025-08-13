#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业文案生成器
使用阿里云 qwen-max 模型直接生成行业相关文案
"""

import logging
from typing import Dict, Any, Optional, List
from core.text_generate.qwen_client import call_qwen


class IndustryTextGenerator:
    """行业文案生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_industry_text(
        self, 
        industry: str, 
        is_hot: bool = True, 
        content: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成行业文案
        
        Args:
            industry: 行业名称（如：财税、医疗、教育等）
            is_hot: 是否要求热点内容
            content: 指定内容（可选）
            category_id: 分类ID（可选）
            
        Returns:
            Dict包含生成的文案和相关信息
        """
        try:
            self.logger.info(f"开始生成行业文案: {industry}")
            
            # 如果指定了内容，直接返回
            if content and content.strip():
                return {
                    'success': True,
                    'industry': industry,
                    'content': content,
                    'source': 'user_provided'
                }
            
            # 构建提示词
            prompt = self._build_prompt(industry, is_hot, category_id)
            
            # 调用qwen生成文案
            generated_text = call_qwen(prompt)
            
            if generated_text and not generated_text.startswith("调用失败"):
                self.logger.info(f"文案生成成功: {generated_text[:50]}...")
                return {
                    'success': True,
                    'industry': industry,
                    'content': generated_text,
                    'source': 'ai_generated',
                    'model': 'qwen-max'
                }
            else:
                # 使用默认文案
                fallback_text = self._get_fallback_text(industry)
                self.logger.warning(f"AI生成失败，使用默认文案: {fallback_text}")
                return {
                    'success': True,
                    'industry': industry,
                    'content': fallback_text,
                    'source': 'fallback',
                    'warning': '使用默认文案'
                }
                
        except Exception as e:
            self.logger.error(f"文案生成失败: {e}")
            return {
                'success': False,
                'industry': industry,
                'error': str(e)
            }
    
    def _build_prompt(self, industry: str, is_hot: bool, category_id: Optional[str]) -> str:
        """构建AI提示词"""
        
        # 基础提示词模板
        prompt_template = """请为{industry}行业生成一段专业的宣传文案。

要求：
1. 文案长度控制在150-300字
2. 语言专业且吸引人
3. 突出{industry}行业的核心价值和优势
4. 适合在营销推广中使用
5. 语言简洁有力，易于理解"""

        # 如果需要热点内容
        if is_hot:
            prompt_template += """
6. 结合当前行业热点和趋势
7. 体现时代性和前瞻性"""

        # 根据分类ID添加特定要求
        if category_id:
            category_requirements = self._get_category_requirements(category_id)
            if category_requirements:
                prompt_template += f"\n8. {category_requirements}"

        prompt_template += "\n\n直接输出文案内容，不要有其他说明。"
        
        return prompt_template.format(industry=industry)
    
    def _get_category_requirements(self, category_id: str) -> str:
        """根据分类ID获取特定要求"""
        category_map = {
            "0": "重点强调专业性和权威性",
            "1": "突出创新性和技术优势", 
            "2": "emphasize服务质量和客户满意度",
            "3": "focus on成本效益和性价比",
            "4": "highlight安全性和可靠性"
        }
        return category_map.get(category_id, "")
    
    def _get_fallback_text(self, industry: str) -> str:
        """获取默认文案"""
        fallback_templates = {
            "财税": "专业财税服务，助力企业合规发展。我们提供全方位的财务咨询、税务筹划和风险管控服务，让您的企业在复杂的财税环境中游刃有余，实现稳健增长。",
            "医疗": "专业医疗服务，守护您的健康。我们致力于提供高质量的医疗服务，用专业的技术和贴心的关怀，为每一位患者带来健康和希望。",
            "教育": "优质教育资源，成就美好未来。我们专注于提供个性化的教育解决方案，让每个学习者都能发挥潜能，实现自己的梦想。",
            "科技": "创新科技驱动，引领数字未来。我们运用前沿技术为企业提供智能化解决方案，助力业务转型升级，在数字化浪潮中抢占先机。",
            "金融": "专业金融服务，智慧理财之选。我们提供全面的金融产品和服务，用专业的投资策略和风险管控，为您的财富保值增值。"
        }
        
        return fallback_templates.get(
            industry, 
            f"专业{industry}服务，值得您信赖的合作伙伴。我们致力于为客户提供高质量的解决方案，用专业和服务创造价值，助力业务发展。"
        )
    
    def generate_multiple_texts(
        self, 
        industry: str, 
        count: int = 3, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        生成多个不同的行业文案
        
        Args:
            industry: 行业名称
            count: 生成数量
            **kwargs: 其他参数
            
        Returns:
            文案列表
        """
        texts = []
        for i in range(count):
            # 为每次生成使用相同参数，qwen会自然产生不同结果
            result = self.generate_industry_text(industry, **kwargs)
            if result['success']:
                texts.append(result)
        
        return texts


# 便捷函数
def generate_industry_text(industry: str, **kwargs) -> Dict[str, Any]:
    """便捷的行业文案生成函数"""
    generator = IndustryTextGenerator()
    return generator.generate_industry_text(industry, **kwargs)


if __name__ == "__main__":
    # 测试代码
    generator = IndustryTextGenerator()
    
    # 测试财税行业
    result = generator.generate_industry_text("财税", is_hot=True)
    print("=== 财税行业文案测试 ===")
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"内容: {result['content']}")
        print(f"来源: {result['source']}")
    else:
        print(f"错误: {result['error']}")
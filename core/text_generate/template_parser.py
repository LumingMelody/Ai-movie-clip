# core/text_generate/template_parser.py
# -*- coding: utf-8 -*-
"""
Jinja2模板解析器 - 自动提取模板中使用的变量
"""

import os
import re
from typing import Set, Dict, Any, List
from jinja2 import Environment, meta, FileSystemLoader


class TemplateVariableExtractor:
    """模板变量提取器"""

    def __init__(self, template_dir: str = "templates"):
        """
        初始化模板变量提取器

        Args:
            template_dir: 模板根目录
        """
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def extract_variables_from_template_file(self, category: str, style: str) -> Set[str]:
        """
        从模板文件中提取所有使用的变量

        Args:
            category: 模板类别
            style: 模板风格

        Returns:
            模板中使用的变量集合
        """
        try:
            template_path = f"{category}/{style}.j2"

            # 读取模板源码
            template_source = self.env.loader.get_source(self.env, template_path)[0]

            # 解析模板，提取变量
            parsed_content = self.env.parse(template_source)
            variables = meta.find_undeclared_variables(parsed_content)

            return variables

        except Exception as e:
            print(f"❌ [TEMPLATE-PARSER] 提取变量失败: {e}")
            return set()

    def identify_extra_params(self, category: str, style: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别额外的参数（不在模板中使用的参数）

        Args:
            category: 模板类别
            style: 模板风格
            input_data: 输入数据

        Returns:
            额外参数字典
        """
        try:
            # 提取模板变量
            template_vars = self.extract_variables_from_template_file(category, style)

            # 找出不在模板中使用的参数
            extra_params = {}
            for key, value in input_data.items():
                if key not in template_vars:
                    extra_params[key] = value

            return extra_params

        except Exception as e:
            print(f"❌ [TEMPLATE-PARSER] 识别额外参数失败: {e}")
            return {}

    def format_extra_requirements(self, extra_params: Dict[str, Any]) -> str:
        """
        将额外参数格式化为自然语言文本

        Args:
            extra_params: 额外参数字典

        Returns:
            格式化后的文本
        """
        if not extra_params:
            return ""

        lines = []
        lines.append("## 额外定制需求：")

        for key, value in extra_params.items():
            # 格式化每个参数
            formatted_line = self._format_single_param(key, value)
            lines.append(formatted_line)

        return "\n".join(lines)

    def _format_single_param(self, key: str, value: Any) -> str:
        """
        格式化单个参数

        Args:
            key: 参数名
            value: 参数值

        Returns:
            格式化后的文本
        """
        # 处理不同类型的值
        if isinstance(value, bool):
            formatted_value = "是" if value else "否"
        elif isinstance(value, (list, tuple)):
            formatted_value = "、".join(str(v) for v in value)
        elif isinstance(value, dict):
            # 字典类型转换为键值对描述
            formatted_value = "，".join(f"{k}: {v}" for k, v in value.items())
        else:
            formatted_value = str(value)

        return f"- {key}：{formatted_value}"


class AdditionalRequirementsProcessor:
    """额外需求处理器"""

    def __init__(self, template_dir: str = "templates"):
        """
        初始化额外需求处理器

        Args:
            template_dir: 模板根目录
        """
        self.extractor = TemplateVariableExtractor(template_dir)

    def process_input_data(self, category: str, style: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据，分离模板参数和额外需求

        Args:
            category: 模板类别
            style: 模板风格
            input_data: 输入数据

        Returns:
            处理后的数据，包含template_params和additional_requirements
        """
        try:
            # 提取模板变量
            template_vars = self.extractor.extract_variables_from_template_file(category, style)

            # 分离参数
            template_params = {}
            extra_params = {}

            for key, value in input_data.items():
                if key in template_vars:
                    template_params[key] = value
                else:
                    extra_params[key] = value

            # 格式化额外需求
            additional_requirements = self.extractor.format_extra_requirements(extra_params)

            print(f"📊 [PARAMS-PROCESSOR] 参数分类完成:")
            print(f"   模板参数: {len(template_params)}个")
            print(f"   额外参数: {len(extra_params)}个")

            return {
                "template_params": template_params,
                "extra_params": extra_params,
                "additional_requirements": additional_requirements
            }

        except Exception as e:
            print(f"❌ [PARAMS-PROCESSOR] 处理失败: {e}")
            # 失败时返回原始数据
            return {
                "template_params": input_data,
                "extra_params": {},
                "additional_requirements": ""
            }


# 创建全局实例
template_parser = AdditionalRequirementsProcessor()


def extract_template_variables(category: str, style: str, template_dir: str = "templates") -> Set[str]:
    """
    提取模板中使用的变量（便捷函数）

    Args:
        category: 模板类别
        style: 模板风格
        template_dir: 模板根目录

    Returns:
        变量集合
    """
    extractor = TemplateVariableExtractor(template_dir)
    return extractor.extract_variables_from_template_file(category, style)


def identify_extra_parameters(category: str, style: str, input_data: Dict[str, Any],
                              template_dir: str = "templates") -> Dict[str, Any]:
    """
    识别额外参数（便捷函数）

    Args:
        category: 模板类别
        style: 模板风格
        input_data: 输入数据
        template_dir: 模板根目录

    Returns:
        额外参数字典
    """
    extractor = TemplateVariableExtractor(template_dir)
    return extractor.identify_extra_params(category, style, input_data)


# 使用示例
if __name__ == "__main__":
    # 测试模板变量提取
    extractor = TemplateVariableExtractor(template_dir="templates")

    # 提取ecom/knowledge模板的变量
    variables = extractor.extract_variables_from_template_file("ecom", "knowledge")
    print(f"📋 ecom/knowledge模板使用的变量: {variables}")

    # 测试额外参数识别
    test_input = {
        "商品名称": "重庆火锅",
        "商品亮点": "新鲜毛肚",
        "适用人群": "美食爱好者",
        "店位置": "天灵路25号",  # 额外参数
        "活动主题": "199元单人畅享",  # 额外参数
        "配送方式": "外卖+堂食",  # 额外参数
        "营业时间": "10:00-22:00"  # 额外参数
    }

    extra_params = extractor.identify_extra_params("ecom", "knowledge", test_input)
    print(f"\n🎯 识别到的额外参数: {extra_params}")

    # 测试格式化
    formatted_text = extractor.format_extra_requirements(extra_params)
    print(f"\n📝 格式化后的额外需求:\n{formatted_text}")

    # 测试完整处理流程
    processor = AdditionalRequirementsProcessor(template_dir="templates")
    result = processor.process_input_data("ecom", "knowledge", test_input)
    print(f"\n🔍 完整处理结果:")
    print(f"   模板参数: {result['template_params']}")
    print(f"   额外参数: {result['extra_params']}")
    print(f"   额外需求文本:\n{result['additional_requirements']}")

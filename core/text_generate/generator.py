# core/text_generate/generator.py
# -*- coding: utf-8 -*-
"""
增强的文案生成器 - 集成阿里云百炼API和Jinja2模板
"""

import json
import requests
import time
import os
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, Template

from core.text_generate.prompt_manager import validate_scene_and_type, build_prompt
from core.utils.env_config import get_dashscope_api_key



class CopyGenerator:
    """文案生成器 - 集成阿里云百炼API和Jinja2模板"""

    def __init__(self, base_url: str = None, model: str = "qwen-max", template_dir: str = "templates"):
        """
        初始化文案生成器

        Args:
            base_url: API基础URL，默认为阿里云百炼官方地址
            model: 使用的模型名称，默认qwen-max
            template_dir: 模板根目录
        """
        self.api_key = get_dashscope_api_key()
        self.base_url = base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = model
        self.template_dir = template_dir

        # 默认参数配置
        self.default_params = {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 2000,
            "repetition_penalty": 1.0
        }

        # 初始化模板环境
        self._init_template_environment()

    def _init_template_environment(self):
        """初始化Jinja2模板环境"""
        try:
            if os.path.exists(self.template_dir):
                self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
                # print(f"✅ 模板环境初始化成功: {self.template_dir}")
                # 扫描可用的模板类型
                self._scan_available_templates()
            else:
                self.jinja_env = Environment()
                print(f"❌ 模板目录不存在: {self.template_dir}")
                self.available_categories = {}
        except Exception as e:
            print(f"❌ 模板环境初始化失败: {e}")
            self.jinja_env = Environment()
            self.available_categories = {}

    def _scan_available_templates(self):
        """扫描可用的模板文件"""
        self.available_categories = {}

        try:
            # 扫描所有category目录
            for category in os.listdir(self.template_dir):
                category_path = os.path.join(self.template_dir, category)
                if os.path.isdir(category_path):
                    # 扫描该category下的所有模板文件
                    templates = []
                    for file in os.listdir(category_path):
                        if file.endswith('.j2'):
                            style_name = file.replace('.j2', '')
                            templates.append(style_name)

                    if templates:
                        self.available_categories[category] = templates

            # print(f"📁 扫描到的模板类型:")
            for category, styles in self.available_categories.items():
                # print(f"   {category}: {styles}")
                pass
        except Exception as e:
            print(f"❌ 模板扫描失败: {e}")
            self.available_categories = {}

    def generate(self, category: str, style: str, input_data: Dict[str, Any],
                 custom_params: Dict[str, Any] = None, use_template: bool = True,
                 ai_enhance: bool = False) -> str:
        """
        生成文案 - 完整流程

        Args:
            category: 文案类别
            style: 文案风格
            input_data: 输入数据
            custom_params: 自定义生成参数
            use_template: 是否使用模板，False则使用原有的prompt_manager
            ai_enhance: 是否使用AI增强（仅在use_template=True时有效）

        Returns:
            生成的文案内容
        """
        try:
            print(f"📝 [COPY-GENERATOR] 开始生成:")
            print(f"   类别: {category}")
            print(f"   风格: {style}")
            print(f"   模型: {self.model}")
            print(f"   使用模板: {use_template}")
            print(f"   AI增强: {ai_enhance}")

            if use_template:
                # 使用模板生成
                return self._generate_with_template(category, style, input_data, ai_enhance, custom_params)
            else:
                # 使用原有方式生成
                return self._generate_with_prompt_manager(category, style, input_data, custom_params)

        except Exception as e:
            print(f"❌ [COPY-GENERATOR] 生成失败: {str(e)}")
            raise e

    def _generate_with_template(self, category: str, style: str, input_data: Dict[str, Any],
                                ai_enhance: bool = False, custom_params: Dict[str, Any] = None) -> str:
        """使用模板生成文案"""
        try:
            # 第一步：验证模板是否存在
            if not self._template_exists(category, style):
                raise ValueError(f"模板不存在: {category}/{style}")

            # 第二步：渲染模板
            template_content = self._render_template(category, style, input_data)

            if not ai_enhance:
                # 直接返回模板渲染结果
                print(f"✅ [TEMPLATE] 模板渲染完成")
                return template_content
            else:
                # AI增强模板内容
                if not self.api_key:
                    print(f"⚠️ 未配置API密钥，返回基础模板内容")
                    return template_content

                enhanced_content = self._enhance_with_ai(template_content, category, style, input_data, custom_params)
                print(f"✅ [AI-ENHANCED] AI增强完成")
                return enhanced_content

        except Exception as e:
            print(f"❌ [TEMPLATE-GENERATOR] 模板生成失败: {e}")
            raise e

    def _generate_with_prompt_manager(self, category: str, style: str, input_data: Dict[str, Any],
                                      custom_params: Dict[str, Any] = None) -> str:
        """使用原有prompt_manager生成文案"""
        try:
            # 🔥 第一步：预先验证配置
            is_valid, message = validate_scene_and_type(category, style)
            if not is_valid:
                raise ValueError(f"配置验证失败: {message}")

            # 🔥 第二步：构建提示词
            prompt = build_prompt(category, style, input_data)
            print(f"📋 [PROMPT-MANAGER] 提示词构建完成: {prompt[:200]}...")

            # 🔥 第三步：调用大模型生成
            if not self.api_key:
                raise ValueError("❌ 未提供API密钥，无法调用大模型")

            generated_text = self._call_qwen_api(prompt, custom_params)
            print(f"✅ [PROMPT-MANAGER] 生成成功，长度: {len(generated_text)}字符")
            return generated_text

        except Exception as e:
            print(f"❌ [PROMPT-MANAGER] 生成失败: {e}")
            raise e

    def _template_exists(self, category: str, style: str) -> bool:
        """检查模板是否存在"""
        return category in self.available_categories and style in self.available_categories[category]

    def _render_template(self, category: str, style: str, params: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            template_path = f"{category}/{style}.j2"
            template = self.jinja_env.get_template(template_path)
            rendered_content = template.render(**params)
            return rendered_content.strip()
        except Exception as e:
            raise Exception(f"模板渲染失败: {e}")

    def _enhance_with_ai(self, base_content: str, category: str, style: str,
                         input_data: Dict[str, Any], custom_params: Dict[str, Any] = None) -> str:
        """使用AI增强模板内容"""
        try:
            # 获取视频时长
            video_duration = input_data.get('视频时长', '10')
            
            # 根据时长确定文案长度要求
            if isinstance(video_duration, str) and video_duration.isdigit():
                duration_num = int(video_duration)
            elif isinstance(video_duration, (int, float)):
                duration_num = int(video_duration)
            else:
                duration_num = 10  # 默认10秒
            
            # 🔥 如果输入的时长小于10秒或为0，自动调整为10秒
            if duration_num <= 0 or duration_num < 10:
                print(f"⚠️ [DURATION-ADJUST] 输入时长{duration_num}秒过短，自动调整为10秒")
                duration_num = 10
            
            # 根据时长确定字数要求（最小10秒）
            if duration_num <= 10:
                length_requirement = "适中长度，至少35字，控制在35-50字内"
                target_words = "40字左右"
                reading_speed = "正常节奏"
            elif duration_num <= 20:
                length_requirement = "详细表达，至少60字，控制在60-80字内"
                target_words = "70字左右"
                reading_speed = "稍慢节奏"
            elif duration_num <= 30:
                length_requirement = "丰富表达，至少90字，控制在90-120字内"
                target_words = "100字左右"
                reading_speed = "舒缓节奏"
            else:
                length_requirement = "充分展开，至少130字，控制在130-180字内"
                target_words = "150字左右"
                reading_speed = "从容节奏"
            
            # 构建增强提示词
            enhancement_prompt = f"""
请优化以下{category}类别的{style}风格文案，提升其吸引力和表达效果：

原始文案：
{base_content}

优化要求：
- 保持核心信息和结构不变
- 提升语言表达的生动性和感染力
- 增加适当的修辞手法，丰富表达层次
- 确保符合{style}风格特点
- 🎬 关键约束：这是一个{video_duration}秒的视频文案，需要{length_requirement}
- 📏 字数目标：请生成{target_words}的文案，确保内容充实饱满
- 语言节奏要适合{reading_speed}的播放效果
- 充分展开描述，增加细节和感染力，避免过于简短
- 确保内容能在{video_duration}秒内自然流畅地播放完成

请直接返回优化后的文案，字数达到{target_words}，不要包含任何解释：
"""

            return self._call_qwen_api(enhancement_prompt, custom_params)

        except Exception as e:
            print(f"❌ AI增强失败，返回原始内容: {e}")
            return base_content

    def generate_template_copy(self, category: str, style: str, params: Dict[str, Any]) -> str:
        """
        基于模板生成文案（向后兼容接口）

        Args:
            category: 模板类别
            style: 模板风格
            params: 模板参数

        Returns:
            渲染后的文案
        """
        return self.generate(category, style, params, use_template=True, ai_enhance=False)

    def generate_ai_enhanced_copy(self, category: str, style: str, params: Dict[str, Any],
                                  custom_params: Dict[str, Any] = None) -> str:
        """
        生成AI增强版文案（向后兼容接口）

        Args:
            category: 模板类别
            style: 模板风格
            params: 模板参数
            custom_params: 自定义参数

        Returns:
            AI增强后的文案
        """
        return self.generate(category, style, params, custom_params, use_template=True, ai_enhance=True)

    def batch_generate_by_styles(self, category: str, params: Dict[str, Any],
                                 styles: List[str] = None, use_template: bool = True) -> Dict[str, str]:
        """
        批量生成同类别不同风格的文案

        Args:
            category: 模板类别
            params: 统一的模板参数
            styles: 要生成的风格列表，如果为None则生成该类别下所有可用风格
            use_template: 是否使用模板

        Returns:
            各风格对应的文案
        """
        if use_template:
            if styles is None:
                styles = self.available_categories.get(category, [])

            if not styles:
                raise ValueError(f"类别 {category} 下没有可用的模板风格")
        else:
            # 如果不使用模板，需要提供styles列表
            if not styles:
                raise ValueError("不使用模板时必须提供styles列表")

        try:
            print(f"🏭 [BATCH-STYLES] 开始批量风格生成:")
            print(f"   类别: {category}")
            print(f"   风格: {styles}")
            print(f"   使用模板: {use_template}")

            results = {}

            for style in styles:
                try:
                    content = self.generate(category, style, params, use_template=use_template)
                    results[style] = content
                    print(f"✅ {style}: 生成成功")
                except Exception as e:
                    print(f"❌ {style}: {e}")
                    results[style] = f"生成失败: {e}"

            success_count = len([r for r in results.values() if not r.startswith('生成失败')])
            print(f"🏁 [BATCH-STYLES] 批量生成完成，成功{success_count}/{len(styles)}个")
            return results

        except Exception as e:
            print(f"❌ [BATCH-STYLES] 批量生成失败: {e}")
            raise e

    def get_available_categories(self) -> Dict[str, List[str]]:
        """获取所有可用的类别和对应的风格"""
        return self.available_categories.copy()

    def get_available_styles_for_category(self, category: str) -> List[str]:
        """获取指定类别下的所有可用风格"""
        return self.available_categories.get(category, [])

    def _call_qwen_api(self, prompt: str, custom_params: Dict[str, Any] = None) -> str:
        """
        调用阿里云百炼通义千问API

        Args:
            prompt: 输入提示词
            custom_params: 自定义参数

        Returns:
            生成的文本内容
        """
        try:
            print(f"🚀 [QWEN-API] 开始调用API...")

            # 合并参数
            params = {**self.default_params, **(custom_params or {})}

            # 构建请求体
            request_body = {
                "model": self.model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                },
                "parameters": params
            }

            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            print(f"📤 [QWEN-API] 发送请求:")
            print(f"   URL: {self.base_url}")
            print(f"   Model: {self.model}")

            # 发送请求
            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=headers,
                json=request_body,
                timeout=60
            )

            response_time = time.time() - start_time
            print(f"⏱️ [QWEN-API] 请求耗时: {response_time:.2f}秒")

            # 检查响应状态
            if response.status_code != 200:
                error_detail = response.text
                print(f"❌ [QWEN-API] HTTP错误: {response.status_code}")
                print(f"   错误详情: {error_detail}")
                raise Exception(f"API请求失败: HTTP {response.status_code}, {error_detail}")

            # 解析响应
            response_data = response.json()

            # 检查API响应状态
            if "output" not in response_data:
                print(f"❌ [QWEN-API] 响应格式错误: {response_data}")
                raise Exception(f"API响应格式错误: {response_data}")

            # 提取生成的文本
            output = response_data["output"]
            if "text" in output:
                generated_text = output["text"]
            elif "choices" in output and len(output["choices"]) > 0:
                generated_text = output["choices"][0].get("message", {}).get("content", "")
            else:
                print(f"❌ [QWEN-API] 无法提取生成文本: {output}")
                raise Exception("无法从API响应中提取生成的文本")

            # 使用统计信息（如果有）
            if "usage" in response_data:
                usage = response_data["usage"]
                print(f"📊 [QWEN-API] Token使用统计:")
                print(f"   输入Token: {usage.get('input_tokens', 'N/A')}")
                print(f"   输出Token: {usage.get('output_tokens', 'N/A')}")
                print(f"   总Token: {usage.get('total_tokens', 'N/A')}")

            print(f"✅ [QWEN-API] API调用成功")
            return generated_text.strip()

        except requests.exceptions.Timeout:
            print(f"❌ [QWEN-API] 请求超时")
            raise Exception("API请求超时，请稍后重试")

        except requests.exceptions.RequestException as e:
            print(f"❌ [QWEN-API] 网络请求错误: {e}")
            raise Exception(f"网络请求失败: {e}")

        except json.JSONDecodeError as e:
            print(f"❌ [QWEN-API] JSON解析错误: {e}")
            print(f"   原始响应: {response.text}")
            raise Exception("API响应格式错误，无法解析JSON")

        except Exception as e:
            print(f"❌ [QWEN-API] 调用失败: {e}")
            raise e

    def generate_with_retry(self, category: str, style: str, input_data: Dict[str, Any],
                            max_retries: int = 3, custom_params: Dict[str, Any] = None,
                            use_template: bool = True, ai_enhance: bool = False) -> str:
        """
        带重试机制的文案生成

        Args:
            category: 文案类别
            style: 文案风格
            input_data: 输入数据
            max_retries: 最大重试次数
            custom_params: 自定义参数
            use_template: 是否使用模板
            ai_enhance: 是否使用AI增强

        Returns:
            生成的文案内容
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"🔄 [COPY-GENERATOR] 第{attempt}次重试...")
                    time.sleep(2 ** attempt)  # 指数退避

                return self.generate(category, style, input_data, custom_params, use_template, ai_enhance)

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"⚠️ [COPY-GENERATOR] 第{attempt + 1}次尝试失败: {e}")
                else:
                    print(f"❌ [COPY-GENERATOR] 所有重试均失败")

        raise last_error

    def batch_generate(self, tasks: list, max_retries: int = 2) -> list:
        """
        批量生成文案

        Args:
            tasks: 任务列表，每个任务包含 {category, style, input_data, custom_params, use_template, ai_enhance}
            max_retries: 每个任务的最大重试次数

        Returns:
            生成结果列表
        """
        results = []

        print(f"📦 [COPY-GENERATOR] 开始批量生成，共{len(tasks)}个任务")

        for i, task in enumerate(tasks):
            try:
                print(f"\n🔄 [COPY-GENERATOR] 处理任务 {i + 1}/{len(tasks)}")

                result = self.generate_with_retry(
                    category=task.get('category'),
                    style=task.get('style'),
                    input_data=task.get('input_data', {}),
                    max_retries=max_retries,
                    custom_params=task.get('custom_params'),
                    use_template=task.get('use_template', True),
                    ai_enhance=task.get('ai_enhance', False)
                )

                results.append({
                    "task_id": i,
                    "status": "success",
                    "content": result,
                    "error": None
                })

            except Exception as e:
                print(f"❌ [COPY-GENERATOR] 任务{i + 1}失败: {e}")
                results.append({
                    "task_id": i,
                    "status": "failed",
                    "content": None,
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n📊 [COPY-GENERATOR] 批量生成完成: {success_count}/{len(tasks)} 成功")

        return results

    def set_model(self, model: str):
        """设置使用的模型"""
        self.model = model
        print(f"🔄 [COPY-GENERATOR] 模型已切换为: {model}")

    def set_default_params(self, **params):
        """设置默认参数"""
        self.default_params.update(params)
        print(f"⚙️ [COPY-GENERATOR] 默认参数已更新: {self.default_params}")


copy_generator = CopyGenerator(model="qwen-max", template_dir="templates")


def get_copy_generation(category: str, style: str, input_data: Dict[str, Any],
                        use_template: bool = True, ai_enhance: bool = False,
                        custom_params: Dict[str, Any] = None) -> str:
    """
    文案生成核心函数

    Args:
        category: 文案类别
        style: 文案风格
        params: 模板参数
        use_template: 是否使用模板
        ai_enhance: 是否AI增强
        custom_params: 自定义参数

    Returns:
        生成的文案内容
    """
    try:
        print(f"📝 [COPY-GENERATION] 开始生成文案:")
        print(f"   类别: {category}")
        print(f"   风格: {style}")
        print(f"   使用模板: {use_template}")
        print(f"   AI增强: {ai_enhance}")
        print(f"   参数数量: {len(input_data)}")

        # 调用生成器
        result = copy_generator.generate(
            category=category,
            style=style,
            input_data=input_data,
            custom_params=custom_params,
            use_template=use_template,
            ai_enhance=ai_enhance
        )

        print(f"✅ [COPY-GENERATION] 生成成功，字符数: {len(result)}")
        return result

    except Exception as e:
        print(f"❌ [COPY-GENERATION] 生成失败: {e}")
        raise e


# 使用示例
if __name__ == "__main__":
    # 创建生成器
    generator = CopyGenerator(model="qwen-max", template_dir="templates")

    # 测试模板生成
    form_params = {
        "店名称": "重庆火锅",
        "所在城市": "苏州",
        "店位置": "天灵路25号",
        "主营产品": "毛肚",
        "活动主题": "199元单人畅享",
        "活动内容": "火锅自助，畅大胃囊",
        "视频时长": "10"
    }

    try:
        # 基础模板生成
        print("=== 基础模板生成 ===")
        result1 = get_copy_generation(
            category="activity",
            style="knowledge",
            input_data=form_params,
            use_template=True,
            ai_enhance=False
        )
        print(f"基础模板结果: {result1}")

        # AI增强生成
        print("\n=== AI增强生成 ===")
        result2 = generator.generate(
            category="activity",
            style="knowledge",
            input_data=form_params,
            use_template=True,
            ai_enhance=True
        )
        print(f"AI增强结果: {result2}")

        # 批量生成
        print("\n=== 批量生成 ===")
        batch_results = generator.batch_generate_by_styles(
            category="activity",
            params=form_params,
            use_template=True
        )
        for style, content in batch_results.items():
            print(f"{style}: {content[:100]}...")

    except Exception as e:
        print(f"测试失败: {e}")
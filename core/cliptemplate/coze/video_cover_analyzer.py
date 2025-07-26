#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
封面图智能分析系统 - 阿里云百炼版本
支持抖音、小红书、视频号封面图分析，输出建议与评分
使用阿里云百炼多模态API (qwen-vl-max-latest)
"""

import os
import base64
import requests
import logging
from io import BytesIO
from PIL import Image
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


# ========== 配置模块 ==========
class Config:
    """配置类"""
    DASHSCOPE_API_KEY = 'sk-a48a1d84e015410292d07021f60b9acb'
    # 阿里云百炼 OpenAI兼容接口地址
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 使用最新的视觉理解模型
    VL_MODEL_NAME = "qwen-vl-max-latest"

    # 图像处理配置
    MAX_IMAGE_SIZE = (1024, 1024)
    IMAGE_QUALITY = 85

    # 日志配置
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# ========== 日志模块 ==========
def setup_logger(name: str) -> logging.Logger:
    """设置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(Config.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger("CoverAnalysis")


# ========== 数据模型 ==========
class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    image: str = Field(..., description="图片数据（base64编码）或URL")
    is_url: bool = Field(default=False, description="是否为URL")
    platform: str = Field(default="douyin", description="平台类型: douyin/xiaohongshu/shipinhao")


class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    success: bool
    platform: str
    analysis: Optional[str] = None
    score: Optional[float] = None
    suggestions: Optional[list] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ========== 阿里云百炼API客户端 ==========
class BailianVisionClient:
    """阿里云百炼视觉API客户端"""

    def __init__(self):
        self.api_key = Config.DASHSCOPE_API_KEY
        self.base_url = Config.BASE_URL
        self.model_name = Config.VL_MODEL_NAME
        self.logger = setup_logger("BailianClient")

    def call_vision_api(self, image_data_b64: str, prompt: str) -> str:
        """调用阿里云百炼视觉API"""
        # if self.api_key == "sk-a48a1d84e015410292d07021f60b9acb":
        #     self.logger.warning("使用默认API密钥，请配置正确的DASHSCOPE_API_KEY")
        #     return "API密钥未配置，返回模拟分析结果：图片清晰度良好，构图合理，建议优化色彩搭配。"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 构建符合OpenAI格式的请求体
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "你是一个专业的封面设计分析师，具备丰富的平台运营经验。"}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        try:
            self.logger.info("调用阿里云百炼视觉API")
            # 使用OpenAI兼容接口
            api_url = f"{self.base_url}/chat/completions"
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    self.logger.info(f"API调用成功，返回内容长度: {len(content)}")
                    return content
                else:
                    self.logger.error(f"API响应格式异常: {result}")
                    return "API响应格式异常"
            else:
                self.logger.error(f"百炼API错误：{response.status_code} - {response.text}")
                return f"API调用失败: {response.status_code} - {response.text}"

        except Exception as e:
            self.logger.exception("调用百炼API出错")
            return f"API调用异常: {str(e)}"


# ========== 图像处理器 ==========
class ImageProcessor:
    """图像处理器"""

    def __init__(self):
        self.logger = setup_logger("ImageProcessor")

    def validate_and_resize_image(self, image_data_b64: str) -> str:
        """验证并调整图像大小"""
        try:
            # 解码base64图像
            image_data = base64.b64decode(image_data_b64)
            image = Image.open(BytesIO(image_data))

            self.logger.info(f"原始图像尺寸: {image.size}, 模式: {image.mode}")

            # 转换颜色模式
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # 调整大小 - 百炼支持更大的图像
            if image.size[0] > Config.MAX_IMAGE_SIZE[0] or image.size[1] > Config.MAX_IMAGE_SIZE[1]:
                image.thumbnail(Config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

            # 重新编码
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=Config.IMAGE_QUALITY, optimize=True)
            processed_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            self.logger.info(f"处理后图像尺寸: {image.size}")
            return processed_b64

        except Exception as e:
            self.logger.error(f"图像处理失败: {str(e)}")
            raise ValueError(f"图像处理失败：{str(e)}")

    def download_image_from_url(self, url: str) -> str:
        """从URL下载图像并转换为base64"""
        try:
            self.logger.info(f"下载图像: {url}")
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")

                # 调整大小
                if image.size[0] > Config.MAX_IMAGE_SIZE[0] or image.size[1] > Config.MAX_IMAGE_SIZE[1]:
                    image.thumbnail(Config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)

                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=Config.IMAGE_QUALITY, optimize=True)
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
            else:
                raise ValueError(f"HTTP {response.status_code}: 无法下载图片")

        except Exception as e:
            self.logger.error(f"图片下载失败: {str(e)}")
            raise ValueError(f"图片下载失败：{str(e)}")


# ========== 评分器 ==========
class CoverScorer:
    """封面评分器"""

    def __init__(self):
        self.logger = setup_logger("Scorer")

    def score_cover_analysis(self, analysis_text: str) -> float:
        """根据分析文本计算评分"""
        keywords = {
            # 正面关键词
            "优秀": 2.5, "出色": 2.5, "卓越": 2.5,
            "吸引": 2.0, "突出": 2.0, "醒目": 2.0, "生动": 2.0,
            "精致": 1.8, "专业": 1.8, "清晰": 1.8,
            "创意": 1.5, "新颖": 1.5, "独特": 1.5,
            "合适": 1.2, "适合": 1.2, "推荐": 1.5,
            "良好": 1.0, "不错": 1.0, "可以": 0.8,

            # 负面关键词
            "糟糕": -3.0, "很差": -2.5, "失败": -2.5,
            "模糊": -2.0, "混乱": -2.0, "杂乱": -2.0,
            "不建议": -2.0, "避免": -2.0,
            "单调": -1.5, "普通": -1.0, "一般": -0.8,
            "问题": -1.2, "缺乏": -1.0, "不足": -1.0,
        }

        score = 6.0  # 基础分数提高
        analysis_lower = analysis_text.lower()

        for keyword, value in keywords.items():
            count = analysis_lower.count(keyword)
            if count > 0:
                # 限制单个关键词的影响，避免过度偏向
                impact = value * min(count, 2)
                score += impact
                self.logger.debug(f"关键词 '{keyword}' 出现 {count} 次，影响分数: {impact}")

        # 基于文本长度的调整 - 更详细的分析通常质量更高
        text_length = len(analysis_text)
        if text_length > 500:
            score += 0.5
        elif text_length < 200:
            score -= 0.3

        # 确保分数在合理范围内
        score = max(1.0, min(10.0, round(score, 1)))
        self.logger.info(f"计算得分: {score}")
        return score

    def extract_suggestions(self, analysis_text: str) -> list:
        """从分析文本中提取建议"""
        suggestions = []
        lines = analysis_text.split('\n')

        suggestion_keywords = ['建议', '推荐', '优化', '改进', '提升', '调整', '可以', '应该', '需要']

        for line in lines:
            line = line.strip()
            # 去除序号等前缀
            line = line.lstrip('0123456789.、- ')

            if any(keyword in line for keyword in suggestion_keywords):
                if line and len(line) > 8:  # 过滤太短的行
                    # 清理建议文本
                    if line.endswith('。'):
                        line = line[:-1]
                    suggestions.append(line)

        # 如果没有找到明确的建议，尝试提取包含关键动词的句子
        if len(suggestions) < 3:
            sentences = analysis_text.replace('。', '。\n').split('\n')
            for sentence in sentences:
                sentence = sentence.strip()
                if any(keyword in sentence for keyword in ['增加', '减少', '使用', '采用', '选择', '避免']):
                    if sentence and len(sentence) > 10 and sentence not in suggestions:
                        suggestions.append(sentence.replace('。', ''))

        return suggestions[:6]  # 最多返回6条建议


# ========== 分析器 ==========
class CoverAnalyzer:
    """封面分析器"""

    # 平台专用提示词（针对阿里云百炼优化）
    PLATFORM_PROMPTS = {
        "douyin": """
请作为抖音运营专家，分析这张封面图的表现效果：

**分析维度：**
1. **视觉冲击力**：能否在0.5秒内抓住用户注意力？色彩、构图是否醒目？
2. **热门元素**：是否包含抖音热门元素（美女、美食、宠物、搞笑、情感等）？
3. **文字设计**：文字是否清晰可读？是否有引导点击的文案？
4. **色彩搭配**：是否使用高饱和度、对比强烈的颜色？
5. **移动适配**：是否符合手机竖屏浏览和快速滑动的习惯？

**请提供：**
- 每个维度的详细分析
- 具体的改进建议（每条建议要具体可操作）
- 整体评价和推荐程度

请用专业但易懂的语言进行分析。
""",

        "xiaohongshu": """
请作为小红书内容策划专家，分析这张封面图：

**分析维度：**
1. **生活美学**：是否体现精致生活感？色调是否符合小红书用户审美？
2. **种草能力**：是否具有激发购买欲或体验欲的视觉元素？
3. **社交价值**：是否适合用户分享到朋友圈或收藏？
4. **文字排版**：标题和重点信息是否突出？字体设计是否美观？
5. **情感共鸣**：是否能引起目标用户的情感共鸣？

**请提供：**
- 每个维度的详细分析
- 针对小红书用户特点的优化建议
- 预估的传播效果和互动潜力

请结合小红书平台特色进行分析。
""",

        "shipinhao": """
请作为微信视频号运营专家，分析这张封面图：

**分析维度：**
1. **微信生态适配**：是否符合微信用户的浏览习惯和审美偏好？
2. **专业可信度**：是否体现内容的专业性和可信度？
3. **传播潜力**：是否适合在朋友圈传播？是否容易引起转发？
4. **年龄包容性**：是否适合微信主要用户群体（25-45岁）？
5. **内容暗示**：封面是否准确传达视频内容，避免标题党？

**请提供：**
- 每个维度的详细分析
- 提升传播效果的具体建议
- 在微信生态中的竞争力评估

请考虑微信平台的社交属性和用户特征。
"""
    }

    def __init__(self):
        self.bailian_client = BailianVisionClient()
        self.image_processor = ImageProcessor()
        self.scorer = CoverScorer()
        self.logger = setup_logger("Analyzer")

    def analyze_cover(self, image_data_b64: str, platform: str = "douyin") -> Dict[str, Any]:
        """分析封面图片"""
        self.logger.info(f"开始分析 {platform} 封面")

        try:
            # 验证平台
            if platform not in self.PLATFORM_PROMPTS:
                raise ValueError(f"不支持的平台: {platform}，支持的平台: {list(self.PLATFORM_PROMPTS.keys())}")

            # 处理图像
            processed_image = self.image_processor.validate_and_resize_image(image_data_b64)

            # 获取分析提示词
            prompt = self.PLATFORM_PROMPTS[platform]

            # 调用AI分析
            analysis_result = self.bailian_client.call_vision_api(processed_image, prompt)

            # 检查分析结果是否有效
            if not analysis_result or "API" in analysis_result and "失败" in analysis_result:
                raise Exception(f"API调用失败: {analysis_result}")

            # 计算评分
            score = self.scorer.score_cover_analysis(analysis_result)

            # 提取建议
            suggestions = self.scorer.extract_suggestions(analysis_result)

            self.logger.info(f"{platform} 封面分析完成，得分: {score}, 建议数: {len(suggestions)}")

            return {
                "success": True,
                "platform": platform,
                "analysis": analysis_result,
                "score": score,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"{platform} 封面分析失败：{str(e)}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# ========== FastAPI 应用 ==========
app = FastAPI(
    title="封面图智能分析系统 - 阿里云百炼版",
    description="基于阿里云百炼qwen-vl-max模型，支持抖音、小红书、视频号封面图分析",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化分析器
analyzer = CoverAnalyzer()


# ========== API 路由 ==========
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "封面图智能分析系统",
        "version": "3.0.0",
        "description": "基于阿里云百炼AI技术的封面图分析服务",
        "ai_model": "qwen-vl-max-latest",
        "supported_platforms": list(analyzer.PLATFORM_PROMPTS.keys()),
        "endpoints": {
            "analyze": "/analyze - 分析图片（Base64或URL）",
            "analyze_file": "/analyze-file - 上传文件分析",
            "health": "/health - 健康检查",
            "platforms": "/platforms - 支持的平台列表",
            "demo": "/analyze/demo - 演示分析结果"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    api_configured = Config.DASHSCOPE_API_KEY != "sk-a48a1d84e015410292d07021f60b9acb"

    return {
        "status": "healthy" if api_configured else "warning",
        "timestamp": datetime.now().isoformat(),
        "api_key_configured": api_configured,
        "model": Config.VL_MODEL_NAME,
        "base_url": Config.BASE_URL,
        "message": "系统正常运行" if api_configured else "请配置DASHSCOPE_API_KEY环境变量"
    }


@app.get("/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": list(analyzer.PLATFORM_PROMPTS.keys()),
        "platform_info": {
            "douyin": {
                "name": "抖音",
                "description": "短视频平台，注重视觉冲击力和热门元素",
                "focus": ["视觉冲击", "热门元素", "移动适配", "快速吸引"]
            },
            "xiaohongshu": {
                "name": "小红书",
                "description": "生活方式分享平台，注重精致感和种草能力",
                "focus": ["生活美学", "种草能力", "社交价值", "情感共鸣"]
            },
            "shipinhao": {
                "name": "微信视频号",
                "description": "微信生态视频平台，注重专业性和传播性",
                "focus": ["专业可信", "传播潜力", "年龄包容", "内容匹配"]
            }
        }
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_cover_endpoint(request: AnalyzeRequest):
    """分析封面图片（base64或URL）"""
    logger.info(f"收到封面分析请求，平台: {request.platform}, 类型: {'URL' if request.is_url else 'Base64'}")

    try:
        # 处理输入图像
        if request.is_url:
            image_b64 = analyzer.image_processor.download_image_from_url(request.image)
        else:
            # 移除可能的data URL前缀
            image_data = request.image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_b64 = image_data

        # 执行分析
        result = analyzer.analyze_cover(image_b64, request.platform)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return AnalyzeResponse(**result)

    except ValueError as e:
        logger.error(f"输入验证错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_cover_file(
        file: UploadFile = File(...),
        platform: str = "douyin"
):
    """分析上传的封面图片文件"""
    logger.info(f"收到文件上传分析请求，文件: {file.filename}, 平台: {platform}")

    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="请上传图片文件（支持JPEG、PNG、GIF等格式）")

        # 文件大小限制（10MB）
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

        # 读取文件内容
        content = await file.read()

        # 转换为base64
        image_b64 = base64.b64encode(content).decode('utf-8')

        # 执行分析
        result = analyzer.analyze_cover(image_b64, platform)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return AnalyzeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")


@app.get("/analyze/demo")
async def demo_analysis():
    """演示分析结果"""
    demo_result = {
        "success": True,
        "platform": "douyin",
        "analysis": """
**视觉冲击力分析：**
封面色彩鲜艳，主要使用红色和黄色的高对比搭配，能够在短时间内抓住用户注意力。构图采用中心对称设计，主体突出明显。

**热门元素评估：**
封面包含了人物表情、文字标题等抖音用户喜爱的元素，具有较强的点击吸引力。

**文字设计：**
标题文字使用粗体字体，颜色对比明显，可读性良好。建议增加一些装饰性元素提升视觉层次。

**色彩搭配：**
整体色彩饱和度适中，符合抖音平台的视觉风格。建议可以尝试更鲜艳的配色方案。

**移动适配：**
布局合理，适合手机竖屏显示，关键信息在安全区域内。

**整体评价：**
这是一个质量较高的抖音封面，各项指标表现良好，预计能获得不错的点击率。
        """,
        "score": 8.2,
        "suggestions": [
            "增加更多视觉装饰元素，如边框、阴影等，提升设计感",
            "尝试使用更鲜艳的色彩搭配，增强视觉冲击力",
            "添加一些时下流行的元素或表情，提高话题性",
            "优化文字排版，可以尝试不同的字体大小组合",
            "考虑添加简单的动效元素暗示（静态设计中体现动感）",
            "调整主体大小比例，让核心内容更加突出"
        ],
        "timestamp": datetime.now().isoformat()
    }

    return AnalyzeResponse(**demo_result)


# ========== 异常处理 ==========
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """处理值错误"""
    logger.error(f"值错误: {str(exc)}")
    return {"error": str(exc), "status_code": 400}


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """处理一般异常"""
    logger.error(f"未处理的异常: {str(exc)}")
    return {"error": "内部服务器错误", "status_code": 500}


# ========== 启动配置 ==========
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="封面图智能分析系统 - 阿里云百炼版")
    parser.add_argument("--host", default="0.0.0.0", help="绑定主机")
    parser.add_argument("--port", type=int, default=8000, help="绑定端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    parser.add_argument("--log-level", default="info", help="日志级别")

    args = parser.parse_args()

    # # 检查API密钥配置
    # if Config.DASHSCOPE_API_KEY == "sk-a48a1d84e015410292d07021f60b9acb":
    #     logger.warning("⚠️  阿里云百炼API密钥未配置，将使用模拟结果")
    #     logger.warning("💡 请设置环境变量: export DASHSCOPE_API_KEY=your_actual_api_key")
    #     logger.warning("📖 获取API Key: https://bailian.console.aliyun.com/")
    # else:
    #     logger.info("✅ 阿里云百炼API密钥已配置")

    # 打印启动信息
    print(f"""
🎨 封面图智能分析系统 v3.0.0 (阿里云百炼版)
==========================================
🤖 AI模型: {Config.VL_MODEL_NAME}
🌐 API地址: {Config.BASE_URL}
🌐 服务地址: http://{args.host}:{args.port}
📖 API文档: http://{args.host}:{args.port}/docs
🔧 健康检查: http://{args.host}:{args.port}/health
📱 支持平台: 抖音、小红书、微信视频号

✨ 主要特性:
   - 基于阿里云百炼qwen-vl-max模型
   - 支持图片URL和文件上传
   - 智能评分和建议生成
   - 平台专属分析策略

🚀 启动中...
    """)

    try:
        uvicorn.run(
            "__main__:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        print(f"❌ 启动失败: {e}")

# ========== 环境变量设置说明 ==========
"""
环境变量配置说明：

1. 获取阿里云百炼API Key：
   - 访问：https://bailian.console.aliyun.com/
   - 注册/登录阿里云账号
   - 开通百炼服务
   - 创建API Key

2. 设置环境变量：

   Linux/macOS:
   export DASHSCOPE_API_KEY="sk-your-actual-api-key"

   Windows:
   set DASHSCOPE_API_KEY=sk-your-actual-api-key

   或者在.env文件中：
   DASHSCOPE_API_KEY=sk-your-actual-api-key

3. 验证配置：
   echo $DASHSCOPE_API_KEY

4. 运行服务：
   python cover_analysis.py

   或者指定参数：
   python cover_analysis.py --host 0.0.0.0 --port 8080 --reload

使用示例：

1. 分析Base64图片：
   POST /analyze
   {
     "image": "base64_image_data",
     "platform": "douyin"
   }

2. 分析URL图片：
   POST /analyze
   {
     "image": "https://example.com/image.jpg",
     "is_url": true,
     "platform": "xiaohongshu"
   }

3. 上传文件分析：
   POST /analyze-file
   multipart/form-data:
   - file: 图片文件
   - platform: 平台类型

API响应格式：
{
  "success": true,
  "platform": "douyin",
  "analysis": "详细分析内容...",
  "score": 8.5,
  "suggestions": ["建议1", "建议2", ...],
  "timestamp": "2025-06-23T10:30:00"
}

支持的平台：
- douyin: 抖音
- xiaohongshu: 小红书  
- shipinhao: 微信视频号

注意事项：
1. 图片大小限制：10MB以内
2. 支持格式：JPEG、PNG、GIF等常见格式
3. API调用超时：60秒
4. 建议图片尺寸：不超过1024x1024像素
"""
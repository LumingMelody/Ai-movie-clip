# -*- coding: utf-8 -*-
# @Time    : 2025/7/14 09:53
# @Author  : 蔍鸣霸霸
# @FileName: interface_model.py
# @Software: PyCharm
# @Blog    ：只因你太美
from typing import Optional, Union, List, Dict, Any

from pydantic import BaseModel, Field


# ========== 请求模型定义 ==========
class VideoAdvertisementRequest(BaseModel):
    company_name: str
    service: str
    topic: str
    content: Optional[str] = None
    need_change: bool = False
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增

class VideoAdvertisementEnhanceRequest(BaseModel):
    company_name: str
    service: str
    topic: str
    content: Optional[str] = None
    need_change: bool = False
    add_digital_host: bool = True
    use_temp_materials: bool = False
    clip_mode: bool = True
    upload_digital_host: bool = False
    moderator_source: Optional[Union[str, List[str]]] = None  # 修改为接受字符串或字符串列表
    enterprise_source: Optional[Union[List[str], str]] = None
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class BigWordRequest(BaseModel):
    company_name: str
    title: str
    product: str
    description: str
    categoryId: Optional[str] = Field(None, description="分类ID")
    content: Optional[str] = None
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class CatMemeRequest(BaseModel):
    author: str
    title: str
    content: Optional[str] = None
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class ClickTypeRequest(BaseModel):
    title: str
    content: Optional[str] = None
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class ClothesDifferentSceneRequest(BaseModel):
    has_figure: bool
    clothesurl: str
    description: str
    categoryId: Optional[str] = Field(None, description="分类ID")
    is_down: bool = True
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class DGHImgInsertRequest(BaseModel):
    title: str
    video_file_path: str
    content: Optional[str] = None
    need_change: bool = False
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增
    add_subtitle: Optional[bool] = Field(True, description="是否添加字幕")  # 🔥 新增字幕控制参数
    insert_image: Optional[bool] = Field(True, description="是否插入图片")  # 🔥 新增图片插入控制参数


class DigitalHumanClipsRequest(BaseModel):
    video_file_path: str
    topic: str
    audio_path: str
    content: Optional[str] = None
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class DigitalHumanEasyRequest(BaseModel):
    file_path: str
    topic: str
    audio_path: str
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增

# 🔥 新增：AI分身统一请求模型
class AIAvatarUnifiedRequest(BaseModel):
    """AI分身统一接口请求模型 - 合并AI分身和AI分身增强"""
    # 公共参数
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")
    
    # 统一的视频和内容参数
    video_url: str = Field(..., description="视频文件路径")
    title: str = Field(..., description="标题/主题")
    content: Optional[str] = Field(None, description="内容描述")
    audio_url: Optional[str] = Field(None, description="音频URL路径，如果提供则使用此音频；如果不提供则使用video_url中的音频")
    
    # 控制参数
    add_subtitle: Optional[bool] = Field(True, description="是否添加字幕")
    insert_image: Optional[bool] = Field(False, description="是否插入图片（增强版功能）")
    need_change: Optional[bool] = Field(False, description="是否需要变换（增强版使用）")


class IncitementRequest(BaseModel):
    title: str
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class SinologyRequest(BaseModel):
    title: str
    content: Optional[str] = None
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class StickmanRequest(BaseModel):
    author: str
    title: str
    content: Optional[str] = None
    lift_text: str = "科普动画"
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增



class ClothesFastChangeRequest(BaseModel):
    has_figure: bool
    clothesurl: str
    description: str
    categoryId: Optional[str] = Field(None, description="分类ID")
    is_down: bool = True
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class TextIndustryRequest(BaseModel):
    industry: str
    is_hot: bool = True
    content: Optional[str] = None
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class VideoRandomRequest(BaseModel):
    enterprise: str
    product: str
    description: str
    categoryId: Optional[str] = Field(None, description="分类ID")  # 🔥 新增
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增



class ProductConfigRequest(BaseModel):
    product_name: str = None
    price: float = None
    features: Union[str, List[str]] = None
    discount: str = None
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class ServerStartRequest(BaseModel):
    host: Optional[str] = "0.0.0.0"
    port: Optional[int] = 8888
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增

class AutoIntroStartRequest(BaseModel):
    """自动产品介绍启动请求"""
    host: Optional[str] = Field("127.0.0.1", description="WebSocket服务器IP")
    port: Optional[int] = Field(8888, description="WebSocket服务器端口")
    reply_probability: Optional[float] = Field(0.3, description="随机回复概率")
    max_queue_size: Optional[int] = Field(5, description="最大消息队列长度")
    no_message_timeout: Optional[int] = Field(90, description="无消息超时时间（秒）")
    auto_introduce_interval: Optional[int] = Field(120, description="自动介绍间隔（秒）")
    auto_reconnect: Optional[bool] = Field(True, description="是否启用自动重连")
    max_reconnect_attempts: Optional[int] = Field(10, description="最大重连次数")
    reconnect_delay: Optional[int] = Field(5, description="重连延迟（秒）")
    use_voice_cloning: Optional[bool] = Field(False, description="是否使用声音克隆（需要本地xiao_zong.m4a文件）")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

class AutoIntroStopRequest(BaseModel):
    """自动产品介绍停止请求"""
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

class TimelineGenerationRequest(BaseModel):
    """时间轴生成请求模型"""
    # 基础参数
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")
    mode: Optional[str] = Field("async", description="执行模式：sync/async")
    
    # 视频参数
    title: str = Field(..., description="视频标题")
    content: str = Field(..., description="视频大纲内容")
    duration: int = Field(60, description="视频时长（秒）")
    platform: str = Field("B站", description="目标平台：B站/抖音/YouTube等")
    audience: str = Field("general", description="目标受众")
    style: str = Field("科技感", description="视频风格")
    
    # 高级参数
    include_subtitles: bool = Field(True, description="是否包含字幕")
    include_logo: bool = Field(True, description="是否包含LOGO")
    include_bgm: bool = Field(True, description="是否包含背景音乐")
    brand_colors: Optional[List[str]] = Field(None, description="品牌色彩")
    special_requirements: Optional[str] = Field(None, description="特殊要求")

class TimelineModifyRequest(BaseModel):
    """时间轴修改请求模型"""
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")
    mode: Optional[str] = Field("async", description="执行模式：sync/async")
    
    node_id: str = Field(..., description="要修改的节点ID")
    changes: Dict[str, Any] = Field(..., description="修改内容")
    timeline_id: Optional[str] = Field(None, description="时间轴ID（用于关联）")


class VoiceConfigRequest(BaseModel):
    gender: str = None
    speed: float = None
    pitch: float = None
    voice: str = None
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class DigitalHumanRequest(BaseModel):
    """数字人视频生成请求体"""

    # 基本参数
    video_url: str = None
    topic: Optional[str] = None
    content: Optional[str] = None
    audio_input: Optional[str] = None
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


# ========== 2. 请求模型定义（添加到请求模型部分） ==========
class VideoEditMainRequest(BaseModel):
    """简化的视频编辑请求模型 - 支持最少参数"""
    video_sources: Union[str, List[str]] = Field(..., description="视频文件路径（支持单个文件或文件列表）")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    id: Optional[str] = Field(None, description="业务ID - 用于状态更新")  # 🔥 新增

    # 可选参数，都有默认值
    duration: Optional[int] = Field(30, description="目标时长(秒)")
    style: Optional[str] = Field("抖音风", description="目标风格")
    purpose: Optional[str] = Field("社交媒体", description="使用目的")
    use_local_ai: Optional[bool] = Field(True, description="是否使用本地AI")
    api_key: Optional[str] = Field(None, description="AI模型API密钥")

    class Config:
        schema_extra = {
            "example": {
                "video_sources": ["/Users/luming/Downloads/2025-06-24-11-40-27.mkv"],
                "tenant_id": "1",
                "id": "1"
            }
        }


class CopyGenerationRequest(BaseModel):
    """文案生成请求模型"""

    # 基础参数
    category: str = Field(..., description="文案类别，如：activity, brand, business等")
    style: str = Field(..., description="文案风格，如：knowledge, suspense, scenario等")

    # 模板参数（根据具体模板变量动态传入）
    input_data: Dict[str, Any] = Field(..., description="模板参数，如店名称、活动主题等")

    # 🔥 修改默认值：默认使用基础模板，不启用AI增强
    use_template: bool = Field(True, description="是否使用模板生成")
    ai_enhance: bool = Field(True, description="是否使用AI增强")  # 默认True

    # 自定义生成参数
    custom_params: Optional[Dict[str, Any]] = Field(None, description="自定义AI参数，如temperature、max_tokens等")

    # 系统参数（可选）
    tenant_id: Optional[str] = Field(None, description="租户ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "category": "activity",
                "style": "knowledge",
                "input_data": {
                    "店名称": "重庆火锅",
                    "所在城市": "苏州",
                    "店位置": "天灵路25号",
                    "主营产品": "毛肚",
                    "活动主题": "199元单人畅享",
                    "活动内容": "火锅自助，畅大胃囊",
                    "视频时长": "10"
                },
                "use_template": True,
                "ai_enhance": False,  # 示例中也设为false
                "custom_params": {
                    "temperature": 0.8,
                    "max_tokens": 1500
                }
            }
        }


class CoverAnalysisRequest(BaseModel):
    """分析请求模型"""
    image: str = Field(..., description="图片数据（base64编码）或URL")
    is_url: bool = Field(default=False, description="是否为URL")
    platform: str = Field(default="douyin", description="平台类型: douyin/xiaohongshu/shipinhao")
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class ServerStopRequest(BaseModel):
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class MaterialItem(BaseModel):
    id: str
    name: str
    type: str
    path: str


class SmartClipRequest(BaseModel):
    """智能剪辑请求模型"""
    input_source: Union[str, List[str]]  # 输入源路径（可以是上传目录或文件路径）
    is_directory: bool = True  # 是否为目录
    company_name: str = "测试公司"  # 公司名称
    text_list: Optional[List[str]] = None  # 文字内容列表（随机剪辑时使用）
    audio_durations: Optional[List[float]] = None  # 音频时长列表（随机剪辑时使用）
    clip_mode: str = "random"  # 剪辑模式：random(随机) 或 smart(智能)
    target_resolution: tuple = (1920, 1080)  # 目标分辨率
    tenant_id: Optional[str] = Field(None, description="租户ID")  # 🔥 新增
    task_id: Optional[str] = Field(None, description="任务ID")  # 🔥 新增
    id: Optional[str] = Field(None, description="业务ID")  # 🔥 新增


class VideoHighlightClipRequest(BaseModel):
    """基于观看数据的视频高光剪辑请求"""
    video_source: str = Field(..., description="视频文件路径或URL")
    excel_source: str = Field(..., description="Excel文件路径或URL，包含观看数据")
    target_duration: int = Field(30, description="目标视频时长（秒）")
    output_path: Optional[str] = Field(None, description="输出文件路径")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    id: Optional[str] = Field(None, description="业务ID")
    mode: Optional[str] = Field("sync", description="执行模式：sync(同步) 或 async(异步)")


class VideoHighlightsRequest(BaseModel):
    """直播视频精彩片段提取请求"""
    excel_url: str = Field(..., description="Excel文件URL")
    video_url: str = Field(..., description="视频文件URL")
    metrics: Optional[List[str]] = Field(
        default=['实时在线人数', '互动率', '关注率', '商品点击率'],
        description="要分析的指标列表"
    )
    top_n: Optional[int] = Field(default=3, description="每个指标提取Top N的时间点")
    upload_to_oss: Optional[bool] = Field(default=True, description="是否上传到OSS")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")


class NaturalLanguageVideoEditRequest(BaseModel):
    """自然语言视频剪辑请求"""
    natural_language: str = Field(..., description="自然语言描述，如：制作一个1分钟的产品介绍视频")
    video_url: str = Field(..., description="视频URL地址")
    mode: Optional[str] = Field('async', description="处理模式：sync/async")
    output_duration: Optional[int] = Field(None, description="输出视频时长（秒），如不指定则从描述中解析")
    style: Optional[str] = Field(None, description="视频风格，如不指定则从描述中解析")
    use_timeline_editor: Optional[bool] = Field(True, description="是否使用时间轴编辑器")
    categoryId: Optional[str] = Field(None, description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")
    use_aura_render: Optional[bool] = Field(True, description="是否使用AuraRender引擎")
    video_type: Optional[str] = Field(None, description="视频类型：product_ad/brand_promo/knowledge_explain等")

# -*- coding: utf-8 -*-
"""
通义万相API请求模型 - 扁平化结构版本
去掉input嵌套，使用更简洁的扁平化参数结构
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 文生图相关请求模型 ============
class TextToImageV2Request(BaseModel):
    """文生图V2版请求模型 - 扁平化结构"""
    model: str = Field("wanx2.1-t2i-turbo", description="模型名称")
    prompt: str = Field(..., description="正向提示词，描述要生成的图像")
    negative_prompt: Optional[str] = Field(None, description="反向提示词，描述不希望出现的内容")
    size: str = Field("1024*1024", description="图像尺寸")
    n: int = Field(1, description="生成图片数量", ge=1, le=4)
    seed: Optional[int] = Field(None, description="随机种子")
    prompt_extend: bool = Field(True, description="是否启用智能改写")
    watermark: bool = Field(False, description="是否添加水印")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx2.1-t2i-turbo",
                "prompt": "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵",
                "negative_prompt": "低质量，模糊",
                "size": "1024*1024",
                "n": 1,
                "prompt_extend": True,
                "watermark": False,
                "categoryId": "image_generation",
                "tenant_id": "1"
            }
        }


class TextToImageV1Request(BaseModel):
    """文生图V1版请求模型 - 扁平化结构"""
    model: str = Field("wanx-v1", description="模型名称")
    prompt: str = Field(..., description="正向提示词，描述要生成的图像")
    negative_prompt: Optional[str] = Field(None, description="反向提示词")
    ref_img: Optional[str] = Field(None, description="参考图片URL")
    style: str = Field("<auto>", description="图片风格")
    size: str = Field("1024*1024", description="图像尺寸")
    n: int = Field(1, description="生成图片数量", ge=1, le=4)
    seed: Optional[int] = Field(None, description="随机种子")
    ref_strength: float = Field(0.5, description="参考强度", ge=0, le=1)
    ref_mode: str = Field("repaint", description="参考模式 (repaint/refonly)")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-v1",
                "prompt": "一只可爱的小猫咪，坐在花园里",
                "style": "<auto>",
                "ref_img": "https://example.com/ref.jpg",
                "size": "1024*1024",
                "n": 1,
                "ref_strength": 0.5,
                "ref_mode": "repaint",
                "categoryId": "image_generation",
                "tenant_id": "1"
            }
        }


# ============ 创意海报生成请求模型 ============
class CreativePosterRequest(BaseModel):
    """创意海报生成请求模型 - 扁平化结构"""
    title: str = Field(..., description="海报标题")
    sub_title: Optional[str] = Field(None, description="海报副标题")
    body_text: Optional[str] = Field(None, description="海报正文")
    prompt_text_zh: Optional[str] = Field(None, description="中文提示词")
    wh_ratios: str = Field("竖版", description="宽高比例")
    lora_name: Optional[str] = Field(None, description="风格名称")
    lora_weight: float = Field(0.8, description="风格权重", ge=0, le=1)
    ctrl_ratio: float = Field(0.7, description="控制比例", ge=0, le=1)
    ctrl_step: float = Field(0.7, description="控制步数", ge=0, le=1)
    generate_mode: str = Field("hrf", description="生成模式")
    generate_num: int = Field(1, description="生成数量", ge=1, le=4)
    auxiliary_parameters: Optional[str] = Field(None, description="辅助参数")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-poster-generation-v1",
                "title": "春节快乐",
                "sub_title": "家庭团聚，共享天伦之乐",
                "body_text": "春节是中国最重要的传统节日之一",
                "prompt_text_zh": "灯笼，小猫，梅花",
                "wh_ratios": "竖版",
                "lora_name": "童话油画",
                "generate_num": 1,
                "categoryId": "creative_poster",
                "tenant_id": "1"
            }
        }


# ============ 视频生成相关请求模型 ============
class TextToVideoRequest(BaseModel):
    """文生视频请求模型 - 扁平化结构"""
    model: str = Field("wanx2.1-t2v-turbo", description="模型名称")
    prompt: str = Field(..., description="视频描述提示词")
    size: str = Field("1280*720", description="视频尺寸")
    duration: Optional[int] = Field(5, description="视频时长(秒)")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx2.1-t2v-turbo",
                "prompt": "一只小猫在月光下奔跑",
                "size": "1280*720",
                "categoryId": "text_to_video",
                "tenant_id": "1"
            }
        }


class ImageToVideoRequest(BaseModel):
    """图生视频请求模型 - 扁平化结构"""
    model: str = Field("wanx2.1-i2v-turbo", description="模型名称")
    img_url: str = Field(..., description="首帧图片URL")
    prompt: str = Field(..., description="运动描述")
    resolution: str = Field("720P", description="分辨率档位")
    template: Optional[str] = Field(None, description="特效模板")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx2.1-i2v-turbo",
                "img_url": "https://example.com/image.jpg",
                "prompt": "一只猫在草地上奔跑",
                "resolution": "720P",
                "categoryId": "image_to_video",
                "tenant_id": "1"
            }
        }


class ImageToVideoAdvancedRequest(BaseModel):
    """图生视频-基于首尾帧请求模型 - 扁平化结构"""
    first_frame_url: str = Field(..., description="首帧图片URL")
    last_frame_url: str = Field(..., description="尾帧图片URL")
    prompt: str = Field(..., description="生成视频描述")
    duration: int = Field(5, description="视频时长(秒)", ge=1, le=10)
    size: str = Field("1280*720", description="视频尺寸")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-i2v-frames",
                "first_frame_image_url": "https://example.com/first.jpg",
                "last_frame_image_url": "https://example.com/last.jpg",
                "duration": 5,
                "size": "1280*720",
                "categoryId": "image_to_video_advanced",
                "tenant_id": "1"
            }
        }


# ============ 虚拟模特相关请求模型 ============
class VirtualModelV1Request(BaseModel):
    """虚拟模特V1版请求模型 - 扁平化结构"""
    model: str = Field("wanx-virtualmodel-v1", description="模型名称")
    base_image_url: str = Field(..., description="模特或人台实拍商品展示图URL")
    prompt: str = Field(..., description="虚拟模特和背景描述")
    mask_image_url: Optional[str] = Field(None, description="遮罩图片URL")
    face_prompt: Optional[str] = Field(None, description="面部描述")
    background_image_url: Optional[str] = Field(None, description="背景图片URL")
    short_side_size: str = Field("1024", description="输出图片短边尺寸")
    n: int = Field(1, description="生成图片数量", ge=1, le=4)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-virtualmodel-v1",
                "base_image_url": "https://example.com/model_photo.jpg",
                "prompt": "一名年轻女子，身穿白色短裤，极简风格调色板，长镜头",
                "face_prompt": "年轻女子，面容姣好，最高品质",
                "short_side_size": "1024",
                "n": 1,
                "categoryId": "virtual_model_v1",
                "tenant_id": "1"
            }
        }


class VirtualModelV2Request(BaseModel):
    """虚拟模特V2版请求模型 - 扁平化结构"""
    model: str = Field("wanx-virtualmodel-v2", description="模型名称")
    base_image_url: str = Field(..., description="模特或人台实拍商品展示图URL")
    prompt: str = Field(..., description="虚拟模特和背景描述（建议使用英文）")
    mask_image_url: Optional[str] = Field(None, description="遮罩图片URL")
    face_prompt: Optional[str] = Field(None, description="面部描述")
    background_image_url: Optional[str] = Field(None, description="背景图片URL")
    short_side_size: str = Field("1024", description="输出图片短边尺寸")
    n: int = Field(1, description="生成图片数量", ge=1, le=4)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-virtualmodel-v2",
                "base_image_url": "https://example.com/model_photo.jpg",
                "prompt": "A woman stands on a rural road",
                "face_prompt": "good face, beautiful face, best quality.",
                "background_image_url": "https://example.com/background.png",
                "short_side_size": "1024",
                "n": 1,
                "categoryId": "virtual_model_v2",
                "tenant_id": "1"
            }
        }


# ============ 图像背景生成相关请求模型 ============

class ReferenceEdge(BaseModel):
    """边缘引导对象"""
    foreground_edge: Optional[List[str]] = Field(None, description="前景边缘图片URL列表")
    background_edge: Optional[List[str]] = Field(None, description="背景边缘图片URL列表")
    foreground_edge_prompt: Optional[List[str]] = Field(None, description="前景边缘提示词列表")
    background_edge_prompt: Optional[List[str]] = Field(None, description="背景边缘提示词列表")


class BackgroundGenerationRequest(BaseModel):
    """图像背景生成请求模型 - 支持嵌套reference_edge对象"""
    base_image_url: str = Field(..., description="主体图片URL (RGBA格式)")
    ref_image_url: Optional[str] = Field(None, description="参考图片URL")
    ref_prompt: Optional[str] = Field(None, description="参考提示词")

    # 支持嵌套的reference_edge对象
    reference_edge: Optional[ReferenceEdge] = Field(None, description="边缘引导对象")

    # 同时保留原有的扁平参数作为备选
    foreground_edge_urls: Optional[List[str]] = Field(None, description="前景边缘引导图片URL列表(备选)")
    background_edge_urls: Optional[List[str]] = Field(None, description="背景边缘引导图片URL列表(备选)")
    foreground_edge_prompts: Optional[List[str]] = Field(None, description="前景边缘提示词列表(备选)")
    background_edge_prompts: Optional[List[str]] = Field(None, description="背景边缘提示词列表(备选)")

    # 参数设置
    n: int = Field(4, description="生成图片数量")
    ref_prompt_weight: float = Field(0.5, description="参考提示词权重")
    model_version: str = Field("v3", description="模型版本 (v2/v3)")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        json_schema_extra = {
            "example": {
                "base_image_url": "https://example.com/product_rgba.png",
                "ref_image_url": "https://example.com/reference.jpg",
                "ref_prompt": "山脉和晚霞",
                "reference_edge": {
                    "foreground_edge": ["https://example.com/edge1.png"],
                    "background_edge": ["https://example.com/edge2.png"],
                    "foreground_edge_prompt": ["粉色桃花"],
                    "background_edge_prompt": ["树叶"]
                },
                "n": 4,
                "ref_prompt_weight": 0.5,
                "model_version": "v3",
                "categoryId": "1",
                "tenant_id": "1"
            }
        }

# ============ AI试衣相关请求模型 ============
class AITryonBasicRequest(BaseModel):
    """AI试衣-基础版请求模型 - 扁平化结构"""
    person_image_url: str = Field(..., description="模特人物图片URL")
    top_garment_url: Optional[str] = Field(None, description="上装服饰图片URL")
    bottom_garment_url: Optional[str] = Field(None, description="下装服饰图片URL")
    resolution: int = Field(-1, description="输出图片分辨率控制 (-1, 0, 1)")
    restore_face: bool = Field(True, description="是否还原脸部")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "aitryon",
                "person_image_url": "https://example.com/person.jpg",
                "top_garment_url": "https://example.com/top.jpg",
                "bottom_garment_url": "https://example.com/bottom.jpg",
                "resolution": -1,
                "restore_face": True,
                "categoryId": "ai_tryon",
                "tenant_id": "1"
            }
        }


class AITryonPlusRequest(BaseModel):
    """AI试衣-Plus版请求模型 - 扁平化结构"""
    person_image_url: str = Field(..., description="模特人物图片URL")
    top_garment_url: Optional[str] = Field(None, description="上装服饰图片URL")
    bottom_garment_url: Optional[str] = Field(None, description="下装服饰图片URL")
    resolution: int = Field(-1, description="输出图片分辨率控制 (-1, 0, 1)")
    restore_face: bool = Field(True, description="是否还原脸部")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "aitryon-plus",
                "person_image_url": "https://example.com/person.jpg",
                "top_garment_url": "https://example.com/top.jpg",
                "resolution": -1,
                "restore_face": True,
                "categoryId": "ai_tryon_plus",
                "tenant_id": "1"
            }
        }


class AITryonEnhanceRequest(BaseModel):
    """AI试衣-图片精修请求模型 - 扁平化结构"""
    person_image_url: str = Field(..., description="模特人物图片URL")
    top_garment_url: str = Field(..., description="上装服饰图片URL")
    bottom_garment_url: str = Field(..., description="下装服饰图片URL")
    gender: str = Field("woman", description="性别 (woman/man)")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "aitryon-refiner",
                "person_image_url": "https://example.com/person.jpg",
                "top_garment_url": "https://example.com/top.jpg",
                "bottom_garment_url": "https://example.com/bottom.jpg",
                "coarse_image_url": "https://example.com/coarse_result.png",
                "gender": "woman",
                "categoryId": "ai_tryon_enhance",
                "tenant_id": "1"
            }
        }


class AITryonSegmentRequest(BaseModel):
    """AI试衣-图片分割请求模型 - 扁平化结构"""
    image_url: str = Field(..., description="待分割的图片URL")
    clothes_type: List[str] = Field(..., description="分割类型列表 ['upper', 'lower']")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "aitryon-parsing-v1",
                "image_url": "https://example.com/person_with_clothes.jpg",
                "clothes_type": ["upper", "lower"],
                "categoryId": "ai_tryon_segment",
                "tenant_id": "1"
            }
        }


# ============ 数字人视频相关请求模型 ============
class AnimateAnyoneRequest(BaseModel):
    """舞动人像请求模型 - 扁平化结构"""
    image_url: str = Field(..., description="人像图片URL")
    dance_video_url: str = Field(..., description="舞蹈动作视频URL")
    duration: int = Field(10, description="视频时长(秒)", ge=1, le=30)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-animate-anyone",
                "image_url": "https://example.com/person.jpg",
                "dance_video_url": "https://example.com/dance.mp4",
                "duration": 10,
                "categoryId": "animate_anyone",
                "tenant_id": "1"
            }
        }


class EMOVideoRequest(BaseModel):
    """悦动人像EMO请求模型 - 扁平化结构"""
    image_url: str = Field(..., description="人像图片URL")
    audio_url: str = Field(..., description="音频文件URL")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-emo-video",
                "image_url": "https://example.com/person.jpg",
                "audio_url": "https://example.com/audio.mp3",
                "duration": 10,
                "categoryId": "emo_video",
                "tenant_id": "1"
            }
        }


class LivePortraitRequest(BaseModel):
    """灵动人像播报请求模型 - 扁平化结构"""
    image_url: str = Field(..., description="人像图片URL")
    audio_url: str = Field(..., description="音频URL")
    duration: int = Field(10, description="视频时长(秒)", ge=1, le=30)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-live-portrait",
                "image_url": "https://example.com/person.jpg",
                "driving_video_url": "https://example.com/driving.mp4",
                "duration": 10,
                "categoryId": "live_portrait",
                "tenant_id": "1"
            }
        }


# ============ 视频编辑相关请求模型 ============
class VideoStyleTransferRequest(BaseModel):
    """视频风格重绘请求模型 - 按照官方API结构"""
    video_url: str = Field(..., description="原始视频URL")
    style: int = Field(0, description="风格ID", ge=0, le=10)  # 根据官方API使用数字风格ID
    video_fps: int = Field(15, description="视频帧率", ge=10, le=30)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://example.com/original_video.mp4",
                "style": 0,
                "video_fps": 15,
                "categoryId": "video_style_transfer",
                "tenant_id": "1"
            }
        }


class VideoEditRequest(BaseModel):
    """通用视频编辑请求模型 - 扁平化结构"""
    model: str = Field("wanx-vace", description="模型名称")
    video_url: Optional[str] = Field(None, description="原始视频URL")
    image_urls: Optional[List[str]] = Field(None, description="图片URL列表（多图参考）")
    prompt: Optional[str] = Field(None, description="编辑指令")
    edit_type: str = Field(..., description="编辑类型：style/object/background")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-vace",
                "video_url": "https://example.com/original_video.mp4",
                "prompt": "将视频风格改为卡通风格",
                "edit_type": "style",
                "categoryId": "video_edit",
                "tenant_id": "1"
            }
        }


# ============ 图像编辑相关请求模型 ============
class ImageBackgroundEditRequest(BaseModel):
    """通用图像编辑请求模型 - 扁平化结构"""
    model: str = Field("wanx-image-edit-v2", description="模型名称")
    image_url: str = Field(..., description="原始图片URL")
    prompt: str = Field(..., description="编辑描述")
    negative_prompt: Optional[str] = Field(None, description="负向提示词")
    guidance_scale: float = Field(7.5, description="引导系数", ge=1.0, le=20.0)
    strength: float = Field(0.8, description="编辑强度", ge=0.1, le=1.0)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-image-edit-v2",
                "image_url": "https://example.com/original.jpg",
                "prompt": "将背景替换为海滩场景",
                "guidance_scale": 7.5,
                "strength": 0.8,
                "categoryId": "image_edit",
                "tenant_id": "1"
            }
        }


# ============ 其他特殊模型请求 ============
class ShoeModelRequest(BaseModel):
    """鞋靴模特请求模型 - 扁平化结构"""
    template_image_url: str = Field(..., description="模特模板图片URL")
    shoe_image_url: List[str] = Field(..., description="鞋靴图片URL列表")
    n: int = Field(1, description="生成图片数量", ge=1, le=4)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "shoemodel-v1",
                "template_image_url": "https://example.com/model_template.jpg",
                "shoe_image_url": ["https://example.com/shoe1.jpg", "https://example.com/shoe2.jpg"],
                "n": 1,
                "categoryId": "shoe_model",
                "tenant_id": "1"
            }
        }


# ============ 图像处理扩展模型 ============
class ImageUpscaleRequest(BaseModel):
    """图像超分辨率请求模型 - 扁平化结构"""
    model: str = Field("wanx-image-upscale", description="模型名称")
    image_url: str = Field(..., description="原始图片URL")
    scale_factor: int = Field(2, description="放大倍数 (2/4)")
    enhance_quality: bool = Field(True, description="是否增强质量")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-image-upscale",
                "image_url": "https://example.com/original.jpg",
                "scale_factor": 2,
                "enhance_quality": True,
                "categoryId": "image_upscale",
                "tenant_id": "1"
            }
        }


class ImageStyleTransferRequest(BaseModel):
    """图像风格迁移请求模型 - 扁平化结构"""
    model: str = Field("wanx-image-style-transfer", description="模型名称")
    content_image_url: str = Field(..., description="内容图片URL")
    style_image_url: str = Field(..., description="风格参考图片URL")
    strength: float = Field(0.8, description="风格强度", ge=0.1, le=1.0)
    preserve_content: bool = Field(True, description="是否保持内容结构")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-image-style-transfer",
                "content_image_url": "https://example.com/content.jpg",
                "style_image_url": "https://example.com/style.jpg",
                "strength": 0.8,
                "preserve_content": True,
                "categoryId": "image_style_transfer",
                "tenant_id": "1"
            }
        }


class ImageInpaintingRequest(BaseModel):
    """图像擦除补全请求模型 - 扁平化结构"""
    model: str = Field("wanx-image-inpainting", description="模型名称")
    image_url: str = Field(..., description="原始图片URL")
    mask_url: str = Field(..., description="掩码图片URL")
    prompt: Optional[str] = Field(None, description="补全内容描述")
    negative_prompt: Optional[str] = Field(None, description="负向提示词")
    strength: float = Field(0.8, description="补全强度", ge=0.1, le=1.0)

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-image-inpainting",
                "image_url": "https://example.com/original.jpg",
                "mask_url": "https://example.com/mask.png",
                "prompt": "美丽的花朵",
                "strength": 0.8,
                "categoryId": "image_inpainting",
                "tenant_id": "1"
            }
        }


class ImageOutpaintingRequest(BaseModel):
    """图像画面扩展请求模型 - 扁平化结构"""
    model: str = Field("wanx-image-outpainting", description="模型名称")
    image_url: str = Field(..., description="原始图片URL")
    expand_direction: str = Field(..., description="扩展方向：left/right/up/down/all")
    expand_ratio: float = Field(1.5, description="扩展比例")
    prompt: Optional[str] = Field("", description="扩展内容提示词")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-image-outpainting",
                "image_url": "https://example.com/original.jpg",
                "expand_direction": "all",
                "expand_ratio": 1.5,
                "prompt": "自然风景",
                "categoryId": "image_outpainting",
                "tenant_id": "1"
            }
        }


# ============ 创意生成模型 ============
class PersonalPortraitRequest(BaseModel):
    """个人写真生成请求模型 - 扁平化结构"""
    model: str = Field("wanx-personal-portrait", description="模型名称")
    image_urls: List[str] = Field(..., description="个人照片URL列表 (2-4张)")
    style: str = Field("default", description="写真风格")
    prompt: Optional[str] = Field(None, description="额外描述")
    negative_prompt: Optional[str] = Field(None, description="负向提示词")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-personal-portrait",
                "image_urls": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
                "style": "professional",
                "prompt": "商务风格写真",
                "categoryId": "personal_portrait",
                "tenant_id": "1"
            }
        }


class DoodlePaintingRequest(BaseModel):
    """涂鸦作画请求模型 - 扁平化结构"""
    model: str = Field("wanx-doodle-painting", description="模型名称")
    sketch_url: str = Field(..., description="手绘涂鸦图片URL")
    prompt: str = Field(..., description="画作描述")
    style: str = Field("default", description="绘画风格")
    negative_prompt: Optional[str] = Field(None, description="负向提示词")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-doodle-painting",
                "sketch_url": "https://example.com/sketch.jpg",
                "prompt": "可爱的小猫咪在花园里玩耍",
                "style": "watercolor",
                "categoryId": "doodle_painting",
                "tenant_id": "1"
            }
        }


class ArtisticTextRequest(BaseModel):
    """艺术字生成请求模型 - 扁平化结构"""
    model: str = Field("wanx-artistic-text", description="模型名称")
    text: str = Field(..., description="要生成的文字内容")
    style: str = Field("default", description="艺术字风格")
    font_style: Optional[str] = Field(None, description="字体样式")
    color_scheme: Optional[str] = Field(None, description="颜色方案")
    background: Optional[str] = Field(None, description="背景设置")

    # 🔥 统一字段
    categoryId: str = Field(..., description="分类ID")
    tenant_id: Optional[str] = Field(None, description="租户ID")
    id: Optional[str] = Field(None, description="业务ID")

    class Config:
        schema_extra = {
            "example": {
                "model": "wanx-artistic-text",
                "text": "新年快乐",
                "style": "modern",
                "font_style": "bold",
                "color_scheme": "gradient",
                "background": "transparent",
                "categoryId": "artistic_text",
                "tenant_id": "1"
            }
        }


# ============ 响应模型定义 ============
class APIResponse(BaseModel):
    """通用API响应模型"""
    status_code: int = Field(..., description="HTTP状态码")
    request_id: str = Field(..., description="请求唯一标识")
    code: Optional[str] = Field(None, description="错误码")
    message: str = Field("", description="响应消息")
    output: Optional[Dict[str, Any]] = Field(None, description="输出结果")
    usage: Optional[Dict[str, Any]] = Field(None, description="使用统计")


class TaskOutput(BaseModel):
    """任务输出模型"""
    task_id: str = Field(..., description="任务ID")
    task_status: str = Field(..., description="任务状态")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="结果列表")
    submit_time: Optional[str] = Field(None, description="提交时间")
    scheduled_time: Optional[str] = Field(None, description="调度时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    task_metrics: Optional[Dict[str, int]] = Field(None, description="任务统计")


class ImageResult(BaseModel):
    """图像结果模型"""
    url: str = Field(..., description="图像URL")
    orig_prompt: Optional[str] = Field(None, description="原始提示词")
    actual_prompt: Optional[str] = Field(None, description="实际使用的提示词")


class VideoResult(BaseModel):
    """视频结果模型"""
    video_url: str = Field(..., description="视频URL")
    duration: Optional[int] = Field(None, description="视频时长")
    size: Optional[str] = Field(None, description="视频尺寸")


# ============ 工具函数 ============
def create_request_dict(request_model: BaseModel, exclude_none: bool = True) -> Dict[str, Any]:
    """
    将请求模型转换为字典格式，用于API调用

    Args:
        request_model: Pydantic请求模型实例
        exclude_none: 是否排除None值

    Returns:
        Dict[str, Any]: 请求字典
    """
    return request_model.dict(exclude_none=exclude_none)


def validate_model_params(model_name: str, **kwargs) -> bool:
    """
    验证模型参数是否符合要求

    Args:
        model_name: 模型名称
        **kwargs: 参数字典

    Returns:
        bool: 验证结果
    """
    # 基础验证逻辑
    if not model_name:
        return False

    # 可以根据不同模型添加特定验证
    model_validations = {
        "wanx2.1-t2i-turbo": lambda x: "prompt" in x,
        "wanx-v1": lambda x: "prompt" in x,
        "wanx-poster-generation-v1": lambda x: "title" in x,
        "wanx2.1-t2v-turbo": lambda x: "prompt" in x,
        "wanx2.1-i2v-turbo": lambda x: "img_url" in x and "prompt" in x,
    }

    validation_func = model_validations.get(model_name)
    if validation_func:
        return validation_func(kwargs)

    return True


# ============ 示例用法 ============
def create_text_to_image_v2_example():
    """创建文生图V2版请求示例"""
    request = TextToImageV2Request(
        model="wanx2.1-t2i-turbo",
        prompt="一间有着精致窗户的花店，漂亮的木质门，摆放着花朵",
        negative_prompt="低质量，模糊",
        size="1024*1024",
        n=1,
        prompt_extend=True,
        watermark=False,
        categoryId="image_generation",
        tenant_id="1"
    )
    return create_request_dict(request)


def create_creative_poster_example():
    """创建创意海报请求示例"""
    request = CreativePosterRequest(
        model="wanx-poster-generation-v1",
        title="春节快乐",
        sub_title="家庭团聚，共享天伦之乐",
        body_text="春节是中国最重要的传统节日之一",
        prompt_text_zh="灯笼，小猫，梅花",
        wh_ratios="竖版",
        lora_name="童话油画",
        generate_num=1,
        categoryId="creative_poster",
        tenant_id="1"
    )
    return create_request_dict(request)


def create_video_generation_example():
    """创建视频生成请求示例"""
    request = ImageToVideoRequest(
        model="wanx2.1-i2v-turbo",
        img_url="https://example.com/image.jpg",
        prompt="一只猫在草地上奔跑",
        resolution="720P",
        categoryId="image_to_video",
        tenant_id="1"
    )
    return create_request_dict(request)


if __name__ == "__main__":
    # 示例用法
    print("=== 文生图V2版请求示例 ===")
    t2i_request = create_text_to_image_v2_example()
    print(t2i_request)

    print("\n=== 创意海报请求示例 ===")
    poster_request = create_creative_poster_example()
    print(poster_request)

    print("\n=== 图生视频请求示例 ===")
    video_request = create_video_generation_example()
    print(video_request)
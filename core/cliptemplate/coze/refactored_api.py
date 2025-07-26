# -*- coding: utf-8 -*-
"""
重构后的统一API接口
提供所有视频生成功能的统一访问入口
包含 Coze 视频生成 + Tongyi Wanxiang 图像/视频生成
"""
from typing import List

from core.cliptemplate.coze.base.video_generator import generate_video, VideoGeneratorFactory

# Coze 视频生成模块
from core.cliptemplate.coze.video_advertsment_refactored import get_video_advertisement_refactored
from core.cliptemplate.coze.video_clicktype_refactored import get_video_clicktype_refactored
from core.cliptemplate.coze.video_digital_human_easy_refactored import get_video_digital_human_easy_refactored
from core.cliptemplate.coze.video_clothes_diffrenent_scene_refactored import get_video_clothes_diffrent_scene_refactored
from core.cliptemplate.coze.video_big_word_refactored import get_video_big_word_refactored
from core.cliptemplate.coze.video_catmeme_refactored import get_video_catmeme_refactored
from core.cliptemplate.coze.video_incitment_refactored import get_video_incitment_refactored
from core.cliptemplate.coze.video_introduction_refactored import get_video_introduction_refactored
from core.cliptemplate.coze.video_sinology_refactored import get_video_sinology_refactored
from core.cliptemplate.coze.video_stickman_refactored import get_video_stickman_refactored
from core.cliptemplate.coze.video_generate_live_refactored import get_video_generate_live_refactored

# Tongyi Wanxiang 图像/视频生成模块
from core.clipgenerate.tongyi_wangxiang import (
    # 文生图系列
    get_text_to_image_v2, get_text_to_image_v1,
    # 图像编辑系列
    get_image_background_edit,
    # 虚拟模特系列
    get_virtual_model_v1, get_virtual_model_v2, get_shoe_model,
    get_creative_poster, get_background_generation,
    # AI试衣系列
    get_ai_tryon_basic, get_ai_tryon_plus, get_ai_tryon_enhance,
    get_ai_tryon_segment,
    # 视频生成系列
    get_image_to_video_advanced,
    # 数字人视频系列
    get_animate_anyone, get_emo_video, get_live_portrait,
    # 视频风格重绘
    get_video_style_transform,
)

# 其他视频处理功能
from core.cliptemplate.coze.video_generate_live import process_single_video_by_url
from core.clipgenerate.interface_function import get_smart_clip_video
from core.cliptemplate.coze.video_dgh_img_insert import get_video_dgh_img_insert
from core.cliptemplate.coze.videos_clothes_fast_change import get_videos_clothes_fast_change


class UnifiedVideoAPI:
    """统一的视频生成API类"""
    
    def __init__(self):
        """初始化API"""
        self.factory = VideoGeneratorFactory()
    
    def generate_advertisement(self, company_name: str, service: str, topic: str, **kwargs) -> str:
        """生成广告视频"""
        return get_video_advertisement_refactored(company_name, service, topic, **kwargs)
    
    def generate_clicktype(self, title: str, content: str, **kwargs) -> str:
        """生成点击类视频"""
        return get_video_clicktype_refactored(title, content, **kwargs)
    
    def generate_digital_human(self, video_url: str, title: str, **kwargs) -> str:
        """生成数字人视频"""
        from core.cliptemplate.coze.video_digital_human_easy import get_video_digital_huamn_easy_local
        # Extract parameters to match the original function signature
        content = kwargs.get('content', None)
        audio_input = kwargs.get('audio_input', None)
        add_subtitle = kwargs.get('add_subtitle', True)  # 获取字幕参数，默认为True
        return get_video_digital_huamn_easy_local(video_url, title, content, audio_input, add_subtitle)
    
    def generate_clothes_scene(self, has_figure: bool, clothes_url: str, description: str, **kwargs) -> str:
        """生成服装场景视频"""
        return get_video_clothes_diffrent_scene_refactored(has_figure, clothes_url, description, **kwargs)
    
    def generate_big_word(self, text: str = None, company_name: str = None, title: str = None, 
                         product: str = None, description: str = None, content: str = None, **kwargs) -> str:
        """生成大字报视频"""
        # Map parameters to the original function expectations
        from core.cliptemplate.coze.video_big_word import get_big_word
        
        # Extract parameters - prioritize direct arguments, then kwargs, then defaults
        final_company_name = company_name or kwargs.get('company_name') or text or 'Company'
        final_title = title or kwargs.get('title') or text or 'Title' 
        final_product = product or kwargs.get('product') or 'Product'
        final_description = description or kwargs.get('description') or 'Description'
        final_content = content or kwargs.get('content', None)
        
        # 🔥 添加调试信息
        print(f"🔍 [generate_big_word] 调用前参数:")
        print(f"   final_company_name: {final_company_name}")
        print(f"   final_title: {final_title}")
        print(f"   final_product: {final_product}")
        print(f"   final_description: {final_description}")
        print(f"   final_content: {final_content}")
        
        return get_big_word(final_company_name, final_title, final_product, final_description, final_content)

    def generate_catmeme(self, dialogue: str = None, author: str = None, content: str = None, **kwargs) -> str:
        """生成猫咪表情包视频"""
        # Map parameters to the original function expectations
        from core.cliptemplate.coze.video_catmeme import get_video_catmeme
        
        # Use dialogue as title if provided, otherwise use kwargs
        title = dialogue or kwargs.get('title', '')
        author = author or kwargs.get('author', 'user')
        content = content or kwargs.get('content', None)
        
        return get_video_catmeme(author, title, content)
    
    def generate_incitement(self, theme: str, **kwargs) -> str:
        """生成煽动类视频"""
        return get_video_incitment_refactored(theme, **kwargs)
    
    def generate_introduction(self, subject: str, details: str, **kwargs) -> str:
        """生成介绍类视频"""
        return get_video_introduction_refactored(subject, details, **kwargs)
    
    def generate_sinology(self, classic: str, interpretation: str, **kwargs) -> str:
        """生成国学类视频"""
        return get_video_sinology_refactored(classic, interpretation, **kwargs)
    
    def generate_stickman(self, story: str, **kwargs) -> str:
        """生成火柴人视频"""
        return get_video_stickman_refactored(story, **kwargs)
    
    def generate_live(self, live_content: str, **kwargs) -> str:
        """生成直播视频"""
        return get_video_generate_live_refactored(live_content, **kwargs)
    
    def generate_video_by_type(self, video_type: str, **kwargs) -> str:
        """根据类型生成视频（通用方法）"""
        return generate_video(generator_type=video_type, **kwargs)
    
    def get_supported_types(self) -> list:
        """获取支持的视频类型"""
        return self.factory.get_supported_types()
    
    # ========== 数字人视频生成 ==========
    def process_video_by_url(self, video_url: str, **kwargs) -> str:
        """通过URL处理单个视频"""
        return process_single_video_by_url(video_url, **kwargs)
    
    def get_smart_clip(self, video_path: str, **kwargs) -> str:
        """智能视频剪辑"""
        return get_smart_clip_video(video_path, **kwargs)
    
    # ========== Tongyi Wanxiang 文生图系列 ==========
    def text_to_image_v2(self, prompt: str, **kwargs) -> str:
        """通义万相文生图V2"""
        return get_text_to_image_v2(prompt, **kwargs)
    
    def text_to_image_v1(self, prompt: str, **kwargs) -> str:
        """通义万相文生图V1"""
        return get_text_to_image_v1(prompt, **kwargs)
    
    # ========== 图像编辑系列 ==========
    def image_background_edit(self, image_url: str, background_prompt: str, **kwargs) -> str:
        """图像背景编辑"""
        return get_image_background_edit(image_url, background_prompt, **kwargs)
    
    # ========== 虚拟模特系列 ==========
    def virtual_model_v1(self, base_image_url: str, prompt: str, **kwargs) -> str:
        """虚拟模特V1"""
        return get_virtual_model_v1(base_image_url, prompt, **kwargs)
    
    def virtual_model_v2(self, base_image_url: str, prompt: str, **kwargs) -> str:
        """虚拟模特V2"""
        return get_virtual_model_v2(base_image_url, prompt, **kwargs)
    
    def shoe_model(self, template_image_url: str, shoe_image_url: list, **kwargs) -> str:
        """鞋靴模特"""
        return get_shoe_model(template_image_url=template_image_url, shoe_image_url=shoe_image_url, **kwargs)
    
    def creative_poster(self, title: str, sub_title: str = None, body_text: str = None, prompt_text_zh: str = None, **kwargs) -> str:
        """创意海报生成"""
        return get_creative_poster(title=title, sub_title=sub_title, body_text=body_text, prompt_text_zh=prompt_text_zh, **kwargs)
    
    def background_generation(self, base_image_url: str, background_prompt: str, **kwargs) -> str:
        """背景生成"""
        return get_background_generation(base_image_url=base_image_url, ref_prompt=background_prompt, **kwargs)
    
    # ========== AI试衣系列 ==========
    def ai_tryon_basic(self, person_image_url: str, top_garment_url: str = None, bottom_garment_url: str = None, **kwargs) -> str:
        """AI试衣基础版"""
        return get_ai_tryon_basic(person_image_url, top_garment_url, bottom_garment_url, **kwargs)
    
    def ai_tryon_plus(self, person_image_url: str, top_garment_url: str = None, bottom_garment_url: str = None, **kwargs) -> str:
        """AI试衣Plus版"""
        return get_ai_tryon_plus(person_image_url, top_garment_url, bottom_garment_url, **kwargs)
    
    def ai_tryon_enhance(self, person_image_url: str, top_garment_url: str = None, bottom_garment_url: str = None, **kwargs) -> str:
        """AI试衣图片精修"""
        return get_ai_tryon_enhance(person_image_url=person_image_url, top_garment_url=top_garment_url, bottom_garment_url=bottom_garment_url, **kwargs)
    
    def ai_tryon_segment(self, image_url: str, clothes_type: list, **kwargs) -> dict:
        """AI试衣图片分割"""
        return get_ai_tryon_segment(image_url=image_url, clothes_type=clothes_type, **kwargs)
    
    # ========== 视频生成系列 ==========
    def image_to_video_advanced(self, first_frame_url: str, last_frame_url: str, prompt: str, **kwargs) -> str:
        """图生视频高级版"""
        return get_image_to_video_advanced(first_frame_url, last_frame_url, prompt, **kwargs)
    
    # ========== 数字人视频系列 ==========
    def animate_anyone(self, image_url: str, dance_video_url: str, **kwargs) -> str:
        """舞动人像 AnimateAnyone"""
        return get_animate_anyone(image_url=image_url, dance_video_url=dance_video_url, **kwargs)
    
    def emo_video(self, image_url: str, audio_url: str, **kwargs) -> str:
        """悦动人像EMO"""
        return get_emo_video(image_url=image_url, audio_url=audio_url, **kwargs)
    
    def live_portrait(self, image_url: str, audio_url: str, **kwargs) -> str:
        """灵动人像 LivePortrait"""
        return get_live_portrait(image_url=image_url, audio_url=audio_url, **kwargs)
    
    # ========== 视频风格重绘 ==========
    def video_style_transfer(self, video_url: str, style: int, **kwargs) -> str:
        """视频风格重绘"""
        return get_video_style_transform(video_url=video_url, style=style, **kwargs)
    
    # ========== 数字人图片插入 ==========
    def dgh_img_insert(self, video_url: str, title: str = None, content: str = None, need_change: bool = False, **kwargs) -> str:
        """数字人图片插入视频
        
        Args:
            video_url: 视频文件路径或URL
            title: 视频标题
            content: 视频内容描述
            need_change: 是否需要修改
            **kwargs: 其他参数
        
        Returns:
            str: 处理后的视频文件路径
        """
        # 从参数中提取信息，支持从kwargs中获取
        final_title = title or kwargs.get('title', '数字人图片插入')
        final_content = content or kwargs.get('content', None)
        final_need_change = need_change or kwargs.get('need_change', False)
        
        # 提取新的控制参数
        add_subtitle = kwargs.get('add_subtitle', True)
        insert_image = kwargs.get('insert_image', True)
        audio_url = kwargs.get('audio_url', None)  # 🔥 添加音频URL参数

        # 调用实际的处理函数
        return get_video_dgh_img_insert(
            title=final_title,
            video_file_path=video_url,
            content=final_content,
            need_change=final_need_change,
            add_subtitle=add_subtitle,
            insert_image=insert_image,
            audio_url=audio_url  # 🔥 传递音频URL参数
        )
    
    # ========== 服装快速换装 ==========
    def clothes_fast_change(self, model_image: str, clothes_list: list, change_speed: str = "normal", **kwargs) -> str:
        """服装快速换装视频
        
        Args:
            model_image: 模特图片URL
            clothes_list: 服装列表
            change_speed: 换装速度，默认为 "normal"
            **kwargs: 其他参数
        
        Returns:
            str: 处理后的视频文件路径
        """
        # 从kwargs中提取其他参数
        has_figure = kwargs.get('has_figure', True)
        description = kwargs.get('description', '服装快速换装视频')
        is_down = kwargs.get('is_down', True)
        
        # 调用实际的处理函数
        # 注意：这里简化处理，使用第一个服装作为示例
        clothes_url = clothes_list[0] if clothes_list else model_image
        return get_videos_clothes_fast_change(
            has_figure=has_figure,
            clothesurl=clothes_url,
            description=description,
            is_down=is_down
        )
    
    # ========== 数字人剪辑 ==========
    def digital_human_clips(self, clips: list, transition: str = "fade", **kwargs) -> str:
        """数字人剪辑视频
        
        Args:
            clips: 视频片段列表
            transition: 转场效果，默认为 "fade"
            **kwargs: 其他参数
        
        Returns:
            str: 处理后的视频文件路径
        """
        # 这是一个占位符实现，需要根据实际需求进行具体实现
        # 可以调用智能剪辑功能或其他数字人处理功能
        if clips and len(clips) > 0:
            # 使用第一个clip作为输入
            first_clip = clips[0]
            video_path = first_clip.get('video_path') or first_clip.get('url')
            if video_path:
                return self.get_smart_clip(video_path, **kwargs)
        
        raise ValueError("数字人剪辑功能需要至少一个有效的视频片段")
    
    # ========== 随机视频生成 ==========
    def generate_random_video(self, enterprise: str, product: str, description: str, **kwargs) -> str:
        """生成随机视频（从多种类型中随机选择）
        
        Args:
            enterprise: 企业名称
            product: 产品名称
            description: 描述信息
            **kwargs: 其他参数
        
        Returns:
            str: 处理后的视频文件路径
        """
        import random
        
        # 定义可用的视频类型
        video_types = [
            'advertisement',
            'clicktype', 
            'big_word',
            'catmeme',
            'incitement'
        ]
        
        # 随机选择一个视频类型
        selected_type = random.choice(video_types)
        
        # 根据选择的类型调用相应的方法
        if selected_type == 'advertisement':
            return self.generate_advertisement(
                company_name=enterprise,
                service=product,
                topic=description,
                **kwargs
            )
        elif selected_type == 'clicktype':
            return self.generate_clicktype(
                title=f"{enterprise} - {product}",
                content=description,
                **kwargs
            )
        elif selected_type == 'big_word':
            return self.generate_big_word(
                company_name=enterprise,
                title=product,
                description=description,
                **kwargs
            )
        elif selected_type == 'catmeme':
            return self.generate_catmeme(
                dialogue=f"{enterprise} {product}",
                content=description,
                **kwargs
            )
        elif selected_type == 'incitement':
            return self.generate_incitement(
                theme=f"{enterprise} {product} {description}",
                **kwargs
            )
        else:
            # 默认使用广告视频
            return self.generate_advertisement(
                company_name=enterprise,
                service=product,
                topic=description,
                **kwargs
            )
    
    # ========== 通用方法 ==========
    def get_all_supported_functions(self) -> dict:
        """获取所有支持的功能列表"""
        return {
            "coze_video_generation": [
                "generate_advertisement", "generate_clicktype", "generate_digital_human",
                "generate_clothes_scene", "generate_big_word", "generate_catmeme",
                "generate_incitement", "generate_introduction", "generate_sinology",
                "generate_stickman", "generate_live"
            ],
            "video_processing": [
                "process_video_by_url", "get_smart_clip"
            ],
            "wanxiang_text_to_image": [
                "text_to_image_v1", "text_to_image_v2"
            ],
            "wanxiang_image_edit": [
                "image_background_edit"
            ],
            "wanxiang_virtual_model": [
                "virtual_model_v1", "virtual_model_v2", "shoe_model", 
                "creative_poster", "background_generation"
            ],
            "wanxiang_ai_tryon": [
                "ai_tryon_basic", "ai_tryon_plus", "ai_tryon_enhance", "ai_tryon_segment"
            ],
            "wanxiang_video_generation": [
                "image_to_video_advanced"
            ],
            "wanxiang_digital_human": [
                "animate_anyone", "emo_video", "live_portrait"
            ],
            "wanxiang_video_style": [
                "video_style_transfer"
            ]
        }


# 创建全局API实例
video_api = UnifiedVideoAPI()

# 便捷函数（向后兼容）
def generate_advertisement_video(company_name: str, service: str, topic: str, **kwargs) -> str:
    """生成广告视频的便捷函数"""
    return video_api.generate_advertisement(company_name, service, topic, **kwargs)

def generate_clicktype_video(title: str, content: str, **kwargs) -> str:
    """生成点击类视频的便捷函数"""
    return video_api.generate_clicktype(title, content, **kwargs)

def generate_digital_human_video(video_input: str, topic: str, **kwargs) -> str:
    """生成数字人视频的便捷函数"""
    return video_api.generate_digital_human(video_input, topic, **kwargs)

def generate_clothes_scene_video(has_figure: bool, clothes_url: str, description: str, **kwargs) -> str:
    """生成服装场景视频的便捷函数"""
    return video_api.generate_clothes_scene(has_figure, clothes_url, description, **kwargs)

def generate_any_video(video_type: str, **kwargs) -> str:
    """生成任意类型视频的便捷函数"""
    return video_api.generate_video_by_type(video_type, **kwargs)

# ========== Tongyi Wanxiang 便捷函数 ==========
def wanxiang_text_to_image(prompt: str, version: str = "v2", **kwargs) -> str:
    """通义万相文生图便捷函数"""
    if version == "v2":
        return video_api.text_to_image_v2(prompt, **kwargs)
    else:
        return video_api.text_to_image_v1(prompt, **kwargs)

def wanxiang_ai_tryon(person_image_url: str, top_garment_url: str = None, bottom_garment_url: str = None, version: str = "basic", **kwargs) -> str:
    """通义万相AI试衣便捷函数"""
    if version == "plus":
        return video_api.ai_tryon_plus(person_image_url, top_garment_url, bottom_garment_url, **kwargs)
    else:
        return video_api.ai_tryon_basic(person_image_url, top_garment_url, bottom_garment_url, **kwargs)

def wanxiang_virtual_model(base_image_url: str, prompt: str, version: str = "v2", **kwargs) -> str:
    """通义万相虚拟模特便捷函数"""
    if version == "v1":
        return video_api.virtual_model_v1(base_image_url, prompt, **kwargs)
    else:
        return video_api.virtual_model_v2(base_image_url, prompt, **kwargs)

def wanxiang_digital_human_video(image_url: str, input_type: str, input_data: str, **kwargs) -> str:
    """通义万相数字人视频便捷函数"""
    if input_type == "dance":
        return video_api.animate_anyone(image_url, input_data, **kwargs)
    elif input_type == "audio":
        return video_api.emo_video(image_url, input_data, **kwargs)
    elif input_type == "driving":
        return video_api.live_portrait(image_url, input_data, **kwargs)
    else:
        raise ValueError(f"不支持的输入类型: {input_type}。支持: dance, audio, driving")


# 使用示例和测试
if __name__ == "__main__":
    api = UnifiedVideoAPI()
    
    print("🚀 重构后的统一视频生成API")
    print(f"📋 支持的视频类型: {api.get_supported_types()}")
    
    # 显示所有支持的功能
    print(f"🎯 所有支持的功能: {api.get_all_supported_functions()}")
    
    # 测试示例
    test_cases = [
        {
            'type': 'advertisement',
            'func': lambda: api.generate_advertisement("测试公司", "AI服务", "技术创新"),
            'name': 'Coze广告视频'
        },
        {
            'type': 'clicktype', 
            'func': lambda: api.generate_clicktype("震惊标题", "你绝对想不到的内容"),
            'name': 'Coze点击类视频'
        },
        {
            'type': 'text_to_image',
            'func': lambda: api.text_to_image_v2("美丽的风景画，高质量，4K"),
            'name': '通义万相文生图'
        },
        {
            'type': 'ai_tryon',
            'func': lambda: wanxiang_ai_tryon("person.jpg", "top.jpg", "bottom.jpg", "basic"),
            'name': '通义万相AI试衣'
        }
    ]
    
    for case in test_cases:
        try:
            print(f"\n🧪 测试 {case['name']}...")
            result = case['func']()
            print(f"✅ {case['name']} 测试成功: {result}")
        except Exception as e:
            print(f"❌ {case['name']} 测试失败: {e}")
    
    print("\n🎉 重构完成！现在你可以用统一的API生成所有类型的视频了！")
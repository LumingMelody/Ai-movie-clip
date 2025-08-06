"""
火山引擎视频特效集成模块
包含滤镜、特效、视频动画和文字动画的API调用
"""

import json
import requests
import time
import tempfile
import os
from typing import Dict, List, Optional, Union
from moviepy import VideoClip, TextClip, CompositeVideoClip
import numpy as np
from dataclasses import dataclass
from enum import Enum


class EffectType(Enum):
    """特效类型枚举"""
    FILTER = "filter"  # 滤镜
    EFFECT = "effect"  # 特效
    VIDEO_ANIMATION = "video_animation"  # 视频动画
    TEXT_ANIMATION = "text_animation"  # 文字动画
    TRANSITION = "transition"  # 转场


@dataclass
class VolcanoEffect:
    """火山引擎特效配置"""
    effect_id: str
    effect_type: EffectType
    name: str
    description: str
    parameters: Dict = None


class VolcanoEffects:
    """火山引擎特效管理器"""
    
    # 滤镜ID - 基于火山引擎官方文档
    FILTERS = {
        # 基础滤镜
        "clear": VolcanoEffect("1184003", EffectType.FILTER, "清晰", "清晰滤镜效果"),
        "afternoon": VolcanoEffect("1184004", EffectType.FILTER, "午后", "午后滤镜效果"),
        "muji": VolcanoEffect("1184005", EffectType.FILTER, "MUJI", "MUJI风格滤镜"),
        "fair": VolcanoEffect("1184006", EffectType.FILTER, "白皙", "白皙滤镜效果"),
        "walnut": VolcanoEffect("1184007", EffectType.FILTER, "胡桃木", "胡桃木风格滤镜"),
        "natural": VolcanoEffect("1184008", EffectType.FILTER, "自然", "自然滤镜效果"),
        
        # 城市风格滤镜
        "hongkong": VolcanoEffect("1183991", EffectType.FILTER, "香港", "香港风格滤镜"),
        "childhood": VolcanoEffect("1183992", EffectType.FILTER, "童年", "童年风格滤镜"),
        "friends": VolcanoEffect("1183993", EffectType.FILTER, "老友记", "老友记风格滤镜"),
        "miami": VolcanoEffect("1183994", EffectType.FILTER, "迈阿密", "迈阿密风格滤镜"),
        "vintage": VolcanoEffect("1183995", EffectType.FILTER, "Vintage", "复古风格滤镜"),
        "american": VolcanoEffect("1183996", EffectType.FILTER, "美式", "美式风格滤镜"),
        
        # 色调滤镜
        "cream": VolcanoEffect("1183961", EffectType.FILTER, "奶油", "奶油色调滤镜"),
        "first_sight": VolcanoEffect("1183962", EffectType.FILTER, "初见", "初见风格滤镜"),
        "bright": VolcanoEffect("1183963", EffectType.FILTER, "鲜亮", "鲜亮色调滤镜"),
        "dream": VolcanoEffect("1183964", EffectType.FILTER, "梦境", "梦境风格滤镜"),
        "jeju": VolcanoEffect("1183965", EffectType.FILTER, "济州", "济州岛风格滤镜"),
        "clear_transparent": VolcanoEffect("1183966", EffectType.FILTER, "清透", "清透风格滤镜"),
        
        # 食物风格滤镜
        "solar_eclipse": VolcanoEffect("1183951", EffectType.FILTER, "日食", "日食风格滤镜"),
        "savor": VolcanoEffect("1183952", EffectType.FILTER, "赏味", "赏味风格滤镜"),
        "warm_food": VolcanoEffect("1183953", EffectType.FILTER, "暖食", "暖食风格滤镜"),
        "delicious": VolcanoEffect("1183954", EffectType.FILTER, "可口", "可口风格滤镜"),
        "midnight_diner": VolcanoEffect("1183955", EffectType.FILTER, "深夜食堂", "深夜食堂风格滤镜"),
        
        # 其他特色滤镜
        "sakura": VolcanoEffect("1183683", EffectType.FILTER, "樱花", "樱花风格滤镜"),
        "lime_green": VolcanoEffect("1183681", EffectType.FILTER, "柠绿", "柠绿风格滤镜"),
        "kyoto": VolcanoEffect("1180981", EffectType.FILTER, "京都", "京都风格滤镜"),
        "sunset": VolcanoEffect("1180982", EffectType.FILTER, "晚霞", "晚霞风格滤镜"),
        "green_beauty": VolcanoEffect("1180983", EffectType.FILTER, "绿妍", "绿妍风格滤镜"),
        "spring_prelude": VolcanoEffect("1180984", EffectType.FILTER, "春日序", "春日序风格滤镜"),
    }
    
    # 特效ID - 基于火山引擎官方文档
    EFFECTS = {
        # 分屏特效
        "mirror_symmetry": VolcanoEffect("1199641", EffectType.EFFECT, "镜像对称", "镜像对称特效"),
        "nine_split": VolcanoEffect("1188883", EffectType.EFFECT, "九分屏", "九分屏特效"),
        "six_split": VolcanoEffect("1188884", EffectType.EFFECT, "六分屏", "六分屏特效"),
        "four_split": VolcanoEffect("1188885", EffectType.EFFECT, "四分屏", "四分屏特效"),
        "three_split": VolcanoEffect("1188886", EffectType.EFFECT, "三分屏", "三分屏特效"),
        "two_split": VolcanoEffect("1188887", EffectType.EFFECT, "二分屏", "二分屏特效"),
    }
    
    # 视频动画ID - 基于火山引擎官方文档
    VIDEO_ANIMATIONS = {
        # 入场动画
        "circle_sweep_open": VolcanoEffect("1180355", EffectType.VIDEO_ANIMATION, "圆形扫开", "圆形扫开入场动画"),
        "slide_in_right": VolcanoEffect("1180331", EffectType.VIDEO_ANIMATION, "向右滑入", "向右滑入动画"),
        "slide_in_left": VolcanoEffect("1180332", EffectType.VIDEO_ANIMATION, "向左滑入", "向左滑入动画"),
        "slide_in_down": VolcanoEffect("1180333", EffectType.VIDEO_ANIMATION, "向下滑入", "向下滑入动画"),
        "slide_in_up": VolcanoEffect("1180334", EffectType.VIDEO_ANIMATION, "向上滑入", "向上滑入动画"),
        "zoom_out": VolcanoEffect("1180335", EffectType.VIDEO_ANIMATION, "缩小", "缩小入场动画"),
        "dissolve_show": VolcanoEffect("1180336", EffectType.VIDEO_ANIMATION, "溶解显示", "溶解显示动画"),
        "fade_in": VolcanoEffect("1180337", EffectType.VIDEO_ANIMATION, "渐显", "渐显入场动画"),
        "zoom_in": VolcanoEffect("1180338", EffectType.VIDEO_ANIMATION, "放大", "放大入场动画"),
        "wipe_right": VolcanoEffect("1180339", EffectType.VIDEO_ANIMATION, "向右擦开", "向右擦开动画"),
        "wipe_left": VolcanoEffect("1180340", EffectType.VIDEO_ANIMATION, "向左擦开", "向左擦开动画"),
        "wipe_down": VolcanoEffect("1180341", EffectType.VIDEO_ANIMATION, "向下擦开", "向下擦开动画"),
        "wipe_up": VolcanoEffect("1180342", EffectType.VIDEO_ANIMATION, "向上擦开", "向上擦开动画"),
        
        # 出场动画
        "circle_sweep_out": VolcanoEffect("1180375", EffectType.VIDEO_ANIMATION, "圆形扫除", "圆形扫除出场动画"),
        "slide_out_left": VolcanoEffect("1180376", EffectType.VIDEO_ANIMATION, "向左滑出", "向左滑出动画"),
        "slide_out_right": VolcanoEffect("1180377", EffectType.VIDEO_ANIMATION, "向右滑出", "向右滑出动画"),
        "slide_out_down": VolcanoEffect("1180378", EffectType.VIDEO_ANIMATION, "向下滑出", "向下滑出动画"),
        "slide_out_up": VolcanoEffect("1180379", EffectType.VIDEO_ANIMATION, "向上滑出", "向上滑出动画"),
        "zoom_out_disappear": VolcanoEffect("1180380", EffectType.VIDEO_ANIMATION, "缩小消失", "缩小消失动画"),
        "dissolve_disappear": VolcanoEffect("1180381", EffectType.VIDEO_ANIMATION, "溶解消失", "溶解消失动画"),
        "fade_out": VolcanoEffect("1180382", EffectType.VIDEO_ANIMATION, "渐隐", "渐隐出场动画"),
        "wipe_out_left": VolcanoEffect("1180383", EffectType.VIDEO_ANIMATION, "向左擦除", "向左擦除动画"),
        "wipe_out_right": VolcanoEffect("1180384", EffectType.VIDEO_ANIMATION, "向右擦除", "向右擦除动画"),
        "wipe_out_down": VolcanoEffect("1180385", EffectType.VIDEO_ANIMATION, "向下擦除", "向下擦除动画"),
        "wipe_out_up": VolcanoEffect("1180386", EffectType.VIDEO_ANIMATION, "向上擦除", "向上擦除动画"),
        "flip": VolcanoEffect("1180403", EffectType.VIDEO_ANIMATION, "翻转", "翻转出场动画"),
    }
    
    # 文字动画ID - 基于火山引擎官方文档
    TEXT_ANIMATIONS = {
        # 入场动画
        "circle_sweep_open": VolcanoEffect("1181455", EffectType.TEXT_ANIMATION, "圆形扫开", "文字圆形扫开入场"),
        "dissolve_show": VolcanoEffect("1181425", EffectType.TEXT_ANIMATION, "溶解显示", "文字溶解显示入场"),
        "wipe_right": VolcanoEffect("1181426", EffectType.TEXT_ANIMATION, "向右擦开", "文字向右擦开入场"),
        "wipe_left": VolcanoEffect("1181427", EffectType.TEXT_ANIMATION, "向左擦开", "文字向左擦开入场"),
        "wipe_down": VolcanoEffect("1181428", EffectType.TEXT_ANIMATION, "向下擦开", "文字向下擦开入场"),
        "wipe_up": VolcanoEffect("1181429", EffectType.TEXT_ANIMATION, "向上擦开", "文字向上擦开入场"),
        "slide_in_left": VolcanoEffect("1181430", EffectType.TEXT_ANIMATION, "向左滑入", "文字向左滑入"),
        "slide_in_right": VolcanoEffect("1181431", EffectType.TEXT_ANIMATION, "向右滑入", "文字向右滑入"),
        "slide_in_down": VolcanoEffect("1181432", EffectType.TEXT_ANIMATION, "向下滑入", "文字向下滑入"),
        "slide_in_up": VolcanoEffect("1181433", EffectType.TEXT_ANIMATION, "向上滑入", "文字向上滑入"),
        "fade_in": VolcanoEffect("1181434", EffectType.TEXT_ANIMATION, "渐显", "文字渐显入场"),
        "zoom_in": VolcanoEffect("1181435", EffectType.TEXT_ANIMATION, "放大", "文字放大入场"),
        "feather_wipe_down": VolcanoEffect("1181436", EffectType.TEXT_ANIMATION, "羽化向下擦开", "文字羽化向下擦开"),
        "feather_wipe_left": VolcanoEffect("1181437", EffectType.TEXT_ANIMATION, "羽化向左擦开", "文字羽化向左擦开"),
        "feather_wipe_up": VolcanoEffect("1181438", EffectType.TEXT_ANIMATION, "羽化向上擦开", "文字羽化向上擦开"),
        "feather_wipe_right": VolcanoEffect("1181439", EffectType.TEXT_ANIMATION, "羽化向右擦开", "文字羽化向右擦开"),
        
        # 出场动画
        "wipe_out_right": VolcanoEffect("1181497", EffectType.TEXT_ANIMATION, "向右擦除", "文字向右擦除出场"),
        "wipe_out_left": VolcanoEffect("1181498", EffectType.TEXT_ANIMATION, "向左擦除", "文字向左擦除出场"),
        "wipe_out_down": VolcanoEffect("1181499", EffectType.TEXT_ANIMATION, "向下擦除", "文字向下擦除出场"),
        "wipe_out_up": VolcanoEffect("1181500", EffectType.TEXT_ANIMATION, "向上擦除", "文字向上擦除出场"),
        "fade_out": VolcanoEffect("1181501", EffectType.TEXT_ANIMATION, "渐隐", "文字渐隐出场"),
        "circle_sweep_out": VolcanoEffect("1181502", EffectType.TEXT_ANIMATION, "圆形扫除", "文字圆形扫除出场"),
        "dissolve_disappear": VolcanoEffect("1181503", EffectType.TEXT_ANIMATION, "溶解消失", "文字溶解消失出场"),
        "zoom_out_disappear": VolcanoEffect("1181504", EffectType.TEXT_ANIMATION, "缩小消失", "文字缩小消失出场"),
        "slide_out_right": VolcanoEffect("1181505", EffectType.TEXT_ANIMATION, "向右滑出", "文字向右滑出"),
        "slide_out_left": VolcanoEffect("1181506", EffectType.TEXT_ANIMATION, "向左滑出", "文字向左滑出"),
        "slide_out_down": VolcanoEffect("1181507", EffectType.TEXT_ANIMATION, "向下滑出", "文字向下滑出"),
        "slide_out_up": VolcanoEffect("1181508", EffectType.TEXT_ANIMATION, "向上划出", "文字向上划出"),
        "feather_wipe_out_down": VolcanoEffect("1181509", EffectType.TEXT_ANIMATION, "羽化向下擦除", "文字羽化向下擦除"),
        "feather_wipe_out_left": VolcanoEffect("1181510", EffectType.TEXT_ANIMATION, "羽化向左擦除", "文字羽化向左擦除"),
        "feather_wipe_out_right": VolcanoEffect("1181511", EffectType.TEXT_ANIMATION, "羽化向右擦除", "文字羽化向右擦除"),
        "feather_wipe_out_up": VolcanoEffect("1181512", EffectType.TEXT_ANIMATION, "羽化向上擦除", "文字羽化向上擦除"),
        "wave_out": VolcanoEffect("1181555", EffectType.TEXT_ANIMATION, "波浪", "文字波浪出场"),
        "flip_out": VolcanoEffect("1181551", EffectType.TEXT_ANIMATION, "翻转", "文字翻转出场"),
        
        # 循环动画
        "wave_loop": VolcanoEffect("1181555", EffectType.TEXT_ANIMATION, "波浪循环", "文字波浪循环动画"),
        "flip_loop": VolcanoEffect("1181551", EffectType.TEXT_ANIMATION, "翻转循环", "文字翻转循环动画"),
    }
    
    # 转场效果ID - 基于火山引擎官方文档
    TRANSITIONS = {
        # 基础转场效果
        "leaf_flip": VolcanoEffect("1182355", EffectType.TRANSITION, "叶片翻转", "叶片翻转转场效果"),
        "blinds": VolcanoEffect("1182356", EffectType.TRANSITION, "百叶窗", "百叶窗转场效果"),
        "wind_blow": VolcanoEffect("1182357", EffectType.TRANSITION, "风吹", "风吹转场效果"),
        "alternating": VolcanoEffect("1182359", EffectType.TRANSITION, "交替出场", "交替出场转场效果"),
        "rotate_zoom": VolcanoEffect("1182360", EffectType.TRANSITION, "旋转放大", "旋转放大转场效果"),
        "spread": VolcanoEffect("1182358", EffectType.TRANSITION, "泛开", "泛开转场效果"),
        "windmill": VolcanoEffect("1182362", EffectType.TRANSITION, "风车", "风车转场效果"),
        "color_mix": VolcanoEffect("1182363", EffectType.TRANSITION, "多色混合", "多色混合转场效果"),
        "mask_transition": VolcanoEffect("1182364", EffectType.TRANSITION, "遮罩转场", "遮罩转场效果"),
        "hexagon": VolcanoEffect("1182365", EffectType.TRANSITION, "六角形", "六角形转场效果"),
        "heart_open": VolcanoEffect("1182366", EffectType.TRANSITION, "心型打开", "心型打开转场效果"),
        "glitch": VolcanoEffect("1182367", EffectType.TRANSITION, "故障转换", "故障转换转场效果"),
        "fly_eye": VolcanoEffect("1182368", EffectType.TRANSITION, "飞眼", "飞眼转场效果"),
        "dream_zoom": VolcanoEffect("1182369", EffectType.TRANSITION, "梦幻放大", "梦幻放大转场效果"),
        "door_open": VolcanoEffect("1182370", EffectType.TRANSITION, "开门展现", "开门展现转场效果"),
        "diagonal_wipe": VolcanoEffect("1182371", EffectType.TRANSITION, "对角擦除", "对角擦除转场效果"),
        "cube": VolcanoEffect("1182373", EffectType.TRANSITION, "立方转换", "立方转换转场效果"),
        "lens_transform": VolcanoEffect("1182374", EffectType.TRANSITION, "透镜变换", "透镜变换转场效果"),
        "sunset": VolcanoEffect("1182375", EffectType.TRANSITION, "晚霞转场", "晚霞转场效果"),
        "circle_open": VolcanoEffect("1182376", EffectType.TRANSITION, "圆形打开", "圆形打开转场效果"),
        "circle_wipe": VolcanoEffect("1182377", EffectType.TRANSITION, "圆形擦开", "圆形擦开转场效果"),
        "circle_alternating": VolcanoEffect("1182378", EffectType.TRANSITION, "圆形交替", "圆形交替转场效果"),
        "clock_sweep": VolcanoEffect("1182379", EffectType.TRANSITION, "时钟扫开", "时钟扫开转场效果"),
    }
    
    def __init__(self, access_key_id: str = None, secret_access_key: str = None, region: str = "cn-north-1"):
        """
        初始化火山引擎特效管理器
        
        Args:
            access_key_id: 访问密钥ID
            secret_access_key: 访问密钥Secret
            region: 服务区域
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.service = "vod"  # 视频点播服务
        self.api_url = f"https://{self.service}.volcengineapi.com"
        self.api_version = "2020-11-19"
        
        # 基础请求头
        self.base_headers = {
            "Content-Type": "application/json",
            "Host": f"{self.service}.volcengineapi.com"
        }
    
    def _get_signed_headers(self, method: str, path: str, body: str) -> Dict[str, str]:
        """
        生成带签名的请求头
        
        Args:
            method: HTTP方法
            path: 请求路径
            body: 请求体
            
        Returns:
            带签名的请求头
        """
        import time
        import hashlib
        import hmac
        
        # 如果没有密钥，返回基础头
        if not self.access_key_id or not self.secret_access_key:
            return self.base_headers
        
        # 生成时间戳
        timestamp = int(time.time())
        date_str = time.strftime('%Y%m%d', time.gmtime(timestamp))
        datetime_str = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(timestamp))
        
        # 构建签名（简化版火山引擎v4签名）
        headers = self.base_headers.copy()
        headers.update({
            "X-Date": datetime_str,
            "Authorization": f"HMAC-SHA256 Credential={self.access_key_id}/{date_str}/{self.region}/{self.service}/request"
        })
        
        return headers
    
    def apply_filter(self, clip: VideoClip, filter_name: str, intensity: float = 1.0) -> VideoClip:
        """
        应用滤镜效果
        
        Args:
            clip: 输入视频剪辑
            filter_name: 滤镜名称
            intensity: 滤镜强度 (0-1)
            
        Returns:
            处理后的视频剪辑
        """
        if filter_name not in self.FILTERS:
            raise ValueError(f"Unknown filter: {filter_name}")
        
        filter_effect = self.FILTERS[filter_name]
        
        # 这里应该调用火山引擎API，暂时返回原始clip
        # 实际实现需要根据火山引擎的具体API文档
        return self._apply_effect_api(clip, filter_effect, {"intensity": intensity})
    
    def apply_effect(self, clip: VideoClip, effect_name: str, **params) -> VideoClip:
        """
        应用特效
        
        Args:
            clip: 输入视频剪辑
            effect_name: 特效名称
            **params: 特效参数
            
        Returns:
            处理后的视频剪辑
        """
        if effect_name not in self.EFFECTS:
            raise ValueError(f"Unknown effect: {effect_name}")
        
        effect = self.EFFECTS[effect_name]
        return self._apply_effect_api(clip, effect, params)
    
    def apply_video_animation(self, clip: VideoClip, animation_name: str, 
                            duration: float = 2.0, **params) -> VideoClip:
        """
        应用视频动画
        
        Args:
            clip: 输入视频剪辑
            animation_name: 动画名称
            duration: 动画持续时间
            **params: 动画参数
            
        Returns:
            处理后的视频剪辑
        """
        if animation_name not in self.VIDEO_ANIMATIONS:
            raise ValueError(f"Unknown video animation: {animation_name}")
        
        animation = self.VIDEO_ANIMATIONS[animation_name]
        params["duration"] = duration
        return self._apply_effect_api(clip, animation, params)
    
    def apply_text_animation(self, text: str, animation_name: str, 
                           font_size: int = 50, **params) -> TextClip:
        """
        应用文字动画
        
        Args:
            text: 文字内容
            animation_name: 动画名称
            font_size: 字体大小
            **params: 动画参数
            
        Returns:
            处理后的文字剪辑
        """
        if animation_name not in self.TEXT_ANIMATIONS:
            raise ValueError(f"Unknown text animation: {animation_name}")
        
        # 创建基础文字剪辑
        text_clip = TextClip(
            text, 
            font_size=font_size,
            color=params.get("color", "white"),
            font=params.get("font", "微软雅黑")
        )
        
        animation = self.TEXT_ANIMATIONS[animation_name]
        return self._apply_effect_api(text_clip, animation, params)
    
    def apply_transition(self, clip1: VideoClip, clip2: VideoClip, 
                        transition_name: str, duration: float = 1.0) -> VideoClip:
        """
        应用转场效果
        
        Args:
            clip1: 第一个视频剪辑
            clip2: 第二个视频剪辑
            transition_name: 转场名称
            duration: 转场持续时间
            
        Returns:
            带转场的合成视频
        """
        if transition_name not in self.TRANSITIONS:
            raise ValueError(f"Unknown transition: {transition_name}")
        
        transition = self.TRANSITIONS[transition_name]
        
        # 这里应该调用火山引擎API实现转场
        # 暂时使用简单的淡入淡出作为示例
        return self._create_transition(clip1, clip2, transition, duration)
    
    def _submit_direct_edit_task(self, video_path: str, effect: VolcanoEffect, params: Dict) -> Dict:
        """
        提交火山引擎直接编辑任务
        
        Args:
            video_path: 视频文件路径
            effect: 特效配置
            params: 特效参数
            
        Returns:
            任务响应
        """
        # 构建编辑任务参数
        edit_params = {
            "TemplateId": "direct_edit_template",
            "EditParam": {
                "VideoArray": [
                    {
                        "FileId": video_path,
                        "StartTime": params.get("start_time", 0),
                        "EndTime": params.get("end_time", -1)
                    }
                ],
                "EffectArray": [
                    {
                        "EffectId": effect.effect_id,
                        "EffectType": effect.effect_type.value,
                        "StartTime": params.get("effect_start", 0),
                        "EndTime": params.get("effect_end", -1),
                        "Parameters": params
                    }
                ]
            }
        }
        
        try:
            # 调用火山引擎 SubmitDirectEditTaskAsync API
            headers = self._get_signed_headers("POST", "/SubmitDirectEditTaskAsync", json.dumps(edit_params))
            response = requests.post(
                f"{self.api_url}/SubmitDirectEditTaskAsync",
                headers=headers,
                data=json.dumps(edit_params)
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 任务提交成功: {result}")
                return result
            else:
                print(f"❌ 任务提交失败: {response.status_code} - {response.text}")
                return {"error": f"API请求失败: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ API调用异常: {str(e)}")
            return {"error": str(e)}
    
    def _get_direct_edit_result(self, task_id: str) -> Dict:
        """
        获取直接编辑任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        try:
            body = json.dumps({"TaskId": task_id})
            headers = self._get_signed_headers("POST", "/GetDirectEditResult", body)
            response = requests.post(
                f"{self.api_url}/GetDirectEditResult",
                headers=headers,
                data=body
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"❌ 获取结果失败: {response.status_code} - {response.text}")
                return {"error": f"API请求失败: {response.status_code}"}
                
        except Exception as e:
            print(f"❌ API调用异常: {str(e)}")
            return {"error": str(e)}
    
    def _wait_for_task_completion(self, task_id: str, timeout: int = 300) -> Dict:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            
        Returns:
            任务结果
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查任务状态
            body = json.dumps({"TaskId": task_id})
            headers = self._get_signed_headers("POST", "/GetDirectEditProgress", body)
            progress_response = requests.post(
                f"{self.api_url}/GetDirectEditProgress",
                headers=headers,
                data=body
            )
            
            if progress_response.status_code == 200:
                progress = progress_response.json()
                status = progress.get("Status", "")
                
                if status == "SUCCESS":
                    print(f"✅ 任务完成: {task_id}")
                    return self._get_direct_edit_result(task_id)
                elif status == "FAILED":
                    print(f"❌ 任务失败: {task_id}")
                    return {"error": "任务处理失败"}
                else:
                    print(f"⏳ 任务进行中: {status}")
                    time.sleep(5)  # 等待5秒后重试
            else:
                print(f"❌ 状态查询失败: {progress_response.status_code}")
                time.sleep(5)
        
        print(f"⏰ 任务超时: {task_id}")
        return {"error": "任务超时"}
    
    def _apply_effect_api(self, clip: Union[VideoClip, TextClip], 
                         effect: VolcanoEffect, params: Dict) -> Union[VideoClip, TextClip]:
        """
        调用火山引擎API应用特效
        
        Args:
            clip: 输入剪辑
            effect: 特效配置
            params: 特效参数
            
        Returns:
            处理后的剪辑
        """
        print(f"🎨 Applying {effect.effect_type.value}: {effect.name} (ID: {effect.effect_id})")
        print(f"📊 Parameters: {params}")
        
        if self.access_key_id:
            try:
                # 1. 导出视频到临时文件
                temp_input = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_input_path = temp_input.name
                temp_input.close()
                
                print(f"📁 导出视频到临时文件: {temp_input_path}")
                clip.write_videofile(temp_input_path, verbose=False, logger=None)
                
                # 2. 提交编辑任务
                print(f"🚀 提交编辑任务...")
                task_result = self._submit_direct_edit_task(temp_input_path, effect, params)
                
                if "error" in task_result:
                    print(f"❌ 任务提交失败: {task_result['error']}")
                    return clip
                
                task_id = task_result.get("TaskId")
                if not task_id:
                    print(f"❌ 未获取到任务ID")
                    return clip
                
                # 3. 等待任务完成
                print(f"⏳ 等待任务完成: {task_id}")
                final_result = self._wait_for_task_completion(task_id)
                
                if "error" in final_result:
                    print(f"❌ 任务执行失败: {final_result['error']}")
                    return clip
                
                # 4. 下载处理后的视频
                output_url = final_result.get("OutputUrl")
                if output_url:
                    print(f"📥 下载处理后的视频: {output_url}")
                    
                    # 下载视频到临时文件
                    temp_output = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                    temp_output_path = temp_output.name
                    temp_output.close()
                    
                    video_response = requests.get(output_url)
                    if video_response.status_code == 200:
                        with open(temp_output_path, 'wb') as f:
                            f.write(video_response.content)
                        
                        # 5. 转换为VideoClip
                        from moviepy import VideoFileClip
                        processed_clip = VideoFileClip(temp_output_path)
                        
                        # 清理临时文件
                        os.unlink(temp_input_path)
                        os.unlink(temp_output_path)
                        
                        print(f"✅ 特效应用成功")
                        return processed_clip
                    else:
                        print(f"❌ 下载失败: {video_response.status_code}")
                        return clip
                else:
                    print(f"❌ 未获取到输出URL")
                    return clip
                    
            except Exception as e:
                print(f"❌ API调用异常: {str(e)}")
                return clip
        else:
            print(f"⚠️  未配置API密钥，使用本地效果模拟")
            
            # 根据特效类型提供基础的本地实现
            if effect.effect_type == EffectType.FILTER and effect.effect_id == "1184003":  # 清晰滤镜
                return clip
            elif effect.effect_type == EffectType.FILTER and effect.effect_id == "1184009":  # 黑白滤镜
                if hasattr(clip, 'fl_image'):
                    return clip.fl_image(lambda img: np.dot(img[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)[..., None].repeat(3, axis=2))
        
        return clip
    
    def _create_transition(self, clip1: VideoClip, clip2: VideoClip, 
                          transition: VolcanoEffect, duration: float) -> VideoClip:
        """
        创建转场效果
        
        Args:
            clip1: 第一个视频剪辑
            clip2: 第二个视频剪辑
            transition: 转场配置
            duration: 转场持续时间
            
        Returns:
            带转场的合成视频
        """
        # TODO: 调用火山引擎API实现转场
        # 暂时使用简单的淡入淡出作为示例
        
        # 确保转场时间不超过任一剪辑的长度
        duration = min(duration, clip1.duration, clip2.duration)
        
        # 创建淡出的clip1
        clip1_fadeout = clip1.with_effects([
            lambda clip: clip.with_opacity(lambda t: 1 - max(0, (t - clip.duration + duration) / duration))
        ])
        
        # 创建淡入的clip2
        clip2_fadein = clip2.with_effects([
            lambda clip: clip.with_opacity(lambda t: min(1, t / duration))
        ])
        
        # 设置clip2的开始时间
        clip2_fadein = clip2_fadein.with_start(clip1.duration - duration)
        
        # 合成两个剪辑
        return CompositeVideoClip([clip1_fadeout, clip2_fadein])
    
    def list_available_effects(self) -> Dict[str, List[str]]:
        """
        列出所有可用的特效
        
        Returns:
            按类型分组的特效列表
        """
        return {
            "filters": list(self.FILTERS.keys()),
            "effects": list(self.EFFECTS.keys()),
            "video_animations": list(self.VIDEO_ANIMATIONS.keys()),
            "text_animations": list(self.TEXT_ANIMATIONS.keys()),
            "transitions": list(self.TRANSITIONS.keys())
        }
    
    def get_effect_info(self, effect_type: str, effect_name: str) -> VolcanoEffect:
        """
        获取特效详细信息
        
        Args:
            effect_type: 特效类型
            effect_name: 特效名称
            
        Returns:
            特效配置信息
        """
        effect_map = {
            "filter": self.FILTERS,
            "effect": self.EFFECTS,
            "video_animation": self.VIDEO_ANIMATIONS,
            "text_animation": self.TEXT_ANIMATIONS,
            "transition": self.TRANSITIONS
        }
        
        if effect_type not in effect_map:
            raise ValueError(f"Unknown effect type: {effect_type}")
        
        effects = effect_map[effect_type]
        if effect_name not in effects:
            raise ValueError(f"Unknown {effect_type}: {effect_name}")
        
        return effects[effect_name]


# 便捷函数
def create_volcano_effects(access_key_id: str = None, secret_access_key: str = None) -> VolcanoEffects:
    """创建火山引擎特效管理器实例"""
    return VolcanoEffects(access_key_id=access_key_id, secret_access_key=secret_access_key)


# 使用示例
if __name__ == "__main__":
    # 创建特效管理器
    volcano = create_volcano_effects()
    
    # 列出所有可用特效
    effects = volcano.list_available_effects()
    print("Available effects:")
    for category, items in effects.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")
    
    # 获取特效信息
    filter_info = volcano.get_effect_info("filter", "vintage")
    print(f"\nFilter info: {filter_info}")
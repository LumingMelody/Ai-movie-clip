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
    
    # 常用滤镜ID - 基于火山引擎实际ID
    FILTERS = {
        # 基础滤镜
        "clear": VolcanoEffect("1184003", EffectType.FILTER, "清晰", "清晰滤镜效果"),
        "afternoon": VolcanoEffect("1184004", EffectType.FILTER, "午后", "午后滤镜效果"),
        
        # 色调滤镜
        "warm": VolcanoEffect("1184005", EffectType.FILTER, "暖色调", "暖色调滤镜"),
        "cold": VolcanoEffect("1184006", EffectType.FILTER, "冷色调", "冷色调滤镜"),
        "vintage": VolcanoEffect("1184007", EffectType.FILTER, "复古", "复古滤镜效果"),
        "film": VolcanoEffect("1184008", EffectType.FILTER, "电影", "电影风格滤镜"),
        
        # 风格滤镜
        "black_white": VolcanoEffect("1184009", EffectType.FILTER, "黑白", "黑白滤镜效果"),
        "vivid": VolcanoEffect("1184010", EffectType.FILTER, "鲜艳", "增强色彩饱和度"),
        "soft": VolcanoEffect("1184011", EffectType.FILTER, "柔和", "柔和滤镜效果"),
        "hdr": VolcanoEffect("1184012", EffectType.FILTER, "HDR", "高动态范围滤镜"),
        "natural": VolcanoEffect("1184013", EffectType.FILTER, "自然", "自然色彩滤镜"),
        "fresh": VolcanoEffect("1184014", EffectType.FILTER, "清新", "清新风格滤镜"),
        
        # 艺术滤镜
        "dream": VolcanoEffect("1184015", EffectType.FILTER, "梦幻", "梦幻效果滤镜"),
        "retro": VolcanoEffect("1184016", EffectType.FILTER, "怀旧", "怀旧风格滤镜"),
        "polaroid": VolcanoEffect("1184017", EffectType.FILTER, "拍立得", "拍立得风格滤镜"),
    }
    
    # 常用特效ID - 基于火山引擎ID格式
    EFFECTS = {
        # 基础特效
        "blur": VolcanoEffect("1185001", EffectType.EFFECT, "模糊", "高斯模糊特效"),
        "shake": VolcanoEffect("1185002", EffectType.EFFECT, "抖动", "画面抖动特效"),
        "glitch": VolcanoEffect("1185003", EffectType.EFFECT, "故障", "故障风特效"),
        
        # 粒子特效
        "particle": VolcanoEffect("1185004", EffectType.EFFECT, "粒子", "粒子特效"),
        "sparkle": VolcanoEffect("1185005", EffectType.EFFECT, "闪光", "闪光粒子特效"),
        "star": VolcanoEffect("1185006", EffectType.EFFECT, "星星", "星星特效"),
        
        # 光效
        "light_leak": VolcanoEffect("1185007", EffectType.EFFECT, "漏光", "漏光特效"),
        "lens_flare": VolcanoEffect("1185008", EffectType.EFFECT, "镜头光晕", "镜头光晕特效"),
        "glow": VolcanoEffect("1185009", EffectType.EFFECT, "发光", "发光特效"),
        
        # 天气特效
        "rain": VolcanoEffect("1185010", EffectType.EFFECT, "下雨", "下雨特效"),
        "snow": VolcanoEffect("1185011", EffectType.EFFECT, "下雪", "下雪特效"),
        "fog": VolcanoEffect("1185012", EffectType.EFFECT, "雾气", "雾气特效"),
        
        # 艺术特效
        "paint": VolcanoEffect("1185013", EffectType.EFFECT, "油画", "油画风格特效"),
        "sketch": VolcanoEffect("1185014", EffectType.EFFECT, "素描", "素描风格特效"),
        "cartoon": VolcanoEffect("1185015", EffectType.EFFECT, "卡通", "卡通风格特效"),
    }
    
    # 视频动画ID - 基于火山引擎ID格式
    VIDEO_ANIMATIONS = {
        # 缩放动画
        "zoom_in": VolcanoEffect("1186001", EffectType.VIDEO_ANIMATION, "放大", "画面放大动画"),
        "zoom_out": VolcanoEffect("1186002", EffectType.VIDEO_ANIMATION, "缩小", "画面缩小动画"),
        "zoom_shake": VolcanoEffect("1186003", EffectType.VIDEO_ANIMATION, "震动缩放", "震动缩放动画"),
        
        # 移动动画
        "slide_left": VolcanoEffect("1186004", EffectType.VIDEO_ANIMATION, "左滑", "向左滑动动画"),
        "slide_right": VolcanoEffect("1186005", EffectType.VIDEO_ANIMATION, "右滑", "向右滑动动画"),
        "slide_up": VolcanoEffect("1186006", EffectType.VIDEO_ANIMATION, "上滑", "向上滑动动画"),
        "slide_down": VolcanoEffect("1186007", EffectType.VIDEO_ANIMATION, "下滑", "向下滑动动画"),
        
        # 旋转动画
        "rotate": VolcanoEffect("1186008", EffectType.VIDEO_ANIMATION, "旋转", "旋转动画"),
        "rotate_3d": VolcanoEffect("1186009", EffectType.VIDEO_ANIMATION, "3D旋转", "3D旋转动画"),
        
        # 其他动画
        "bounce": VolcanoEffect("1186010", EffectType.VIDEO_ANIMATION, "弹跳", "弹跳动画"),
        "fade_in": VolcanoEffect("1186011", EffectType.VIDEO_ANIMATION, "淡入", "淡入动画"),
        "fade_out": VolcanoEffect("1186012", EffectType.VIDEO_ANIMATION, "淡出", "淡出动画"),
        "flip": VolcanoEffect("1186013", EffectType.VIDEO_ANIMATION, "翻转", "翻转动画"),
    }
    
    # 文字动画ID - 基于火山引擎ID格式
    TEXT_ANIMATIONS = {
        # 打字效果
        "typewriter": VolcanoEffect("1187001", EffectType.TEXT_ANIMATION, "打字机", "打字机效果"),
        "typewriter_fast": VolcanoEffect("1187002", EffectType.TEXT_ANIMATION, "快速打字", "快速打字效果"),
        
        # 动态效果
        "wave": VolcanoEffect("1187003", EffectType.TEXT_ANIMATION, "波浪", "波浪文字动画"),
        "shake": VolcanoEffect("1187004", EffectType.TEXT_ANIMATION, "抖动", "文字抖动效果"),
        "pulse": VolcanoEffect("1187005", EffectType.TEXT_ANIMATION, "脉冲", "文字脉冲效果"),
        
        # 光影效果
        "glow": VolcanoEffect("1187006", EffectType.TEXT_ANIMATION, "发光", "文字发光效果"),
        "shadow": VolcanoEffect("1187007", EffectType.TEXT_ANIMATION, "阴影", "文字阴影效果"),
        "neon": VolcanoEffect("1187008", EffectType.TEXT_ANIMATION, "霓虹", "霓虹灯文字效果"),
        
        # 进入动画
        "3d_rotate": VolcanoEffect("1187009", EffectType.TEXT_ANIMATION, "3D旋转", "3D文字旋转"),
        "bounce_in": VolcanoEffect("1187010", EffectType.TEXT_ANIMATION, "弹入", "文字弹入动画"),
        "slide_in": VolcanoEffect("1187011", EffectType.TEXT_ANIMATION, "滑入", "文字滑入动画"),
        "fade_in": VolcanoEffect("1187012", EffectType.TEXT_ANIMATION, "淡入", "文字淡入动画"),
        "zoom_in": VolcanoEffect("1187013", EffectType.TEXT_ANIMATION, "放大进入", "文字放大进入动画"),
    }
    
    # 转场效果ID - 基于火山引擎ID格式
    TRANSITIONS = {
        # 基础转场
        "fade": VolcanoEffect("1188001", EffectType.TRANSITION, "淡入淡出", "淡入淡出转场"),
        "dissolve": VolcanoEffect("1188002", EffectType.TRANSITION, "溶解", "溶解转场效果"),
        "cut": VolcanoEffect("1188003", EffectType.TRANSITION, "硬切", "硬切转场效果"),
        
        # 擦除转场
        "wipe_left": VolcanoEffect("1188004", EffectType.TRANSITION, "左擦除", "向左擦除转场"),
        "wipe_right": VolcanoEffect("1188005", EffectType.TRANSITION, "右擦除", "向右擦除转场"),
        "wipe_up": VolcanoEffect("1188006", EffectType.TRANSITION, "上擦除", "向上擦除转场"),
        "wipe_down": VolcanoEffect("1188007", EffectType.TRANSITION, "下擦除", "向下擦除转场"),
        
        # 滑动转场
        "slide_left": VolcanoEffect("1188008", EffectType.TRANSITION, "左滑动", "左滑动转场效果"),
        "slide_right": VolcanoEffect("1188009", EffectType.TRANSITION, "右滑动", "右滑动转场效果"),
        "slide_up": VolcanoEffect("1188010", EffectType.TRANSITION, "上滑动", "上滑动转场效果"),
        "slide_down": VolcanoEffect("1188011", EffectType.TRANSITION, "下滑动", "下滑动转场效果"),
        
        # 特效转场
        "zoom": VolcanoEffect("1188012", EffectType.TRANSITION, "缩放", "缩放转场效果"),
        "rotate": VolcanoEffect("1188013", EffectType.TRANSITION, "旋转", "旋转转场效果"),
        "blur": VolcanoEffect("1188014", EffectType.TRANSITION, "模糊", "模糊转场效果"),
        "glitch": VolcanoEffect("1188015", EffectType.TRANSITION, "故障", "故障风转场"),
        "cube": VolcanoEffect("1188016", EffectType.TRANSITION, "立方体", "立方体转场效果"),
        "flip": VolcanoEffect("1188017", EffectType.TRANSITION, "翻页", "翻页转场效果"),
        "morph": VolcanoEffect("1188018", EffectType.TRANSITION, "变形", "变形转场效果"),
    }
    
    def __init__(self, api_key: str = None, api_url: str = None, region: str = "cn-north-1"):
        """
        初始化火山引擎特效管理器
        
        Args:
            api_key: API密钥
            api_url: API基础URL
            region: 服务区域
        """
        self.api_key = api_key
        self.region = region
        self.api_url = api_url or f"https://vod.volcengineapi.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json"
        }
    
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
            response = requests.post(
                f"{self.api_url}/SubmitDirectEditTaskAsync",
                headers=self.headers,
                json=edit_params
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
            response = requests.post(
                f"{self.api_url}/GetDirectEditResult",
                headers=self.headers,
                json={"TaskId": task_id}
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
            progress_response = requests.post(
                f"{self.api_url}/GetDirectEditProgress",
                headers=self.headers,
                json={"TaskId": task_id}
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
        
        if self.api_key:
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
def create_volcano_effects(api_key: str = None) -> VolcanoEffects:
    """创建火山引擎特效管理器实例"""
    return VolcanoEffects(api_key=api_key)


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
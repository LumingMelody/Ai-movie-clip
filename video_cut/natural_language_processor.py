"""
自然语言视频剪辑处理器
将用户的自然语言描述转换为结构化的视频剪辑时间轴
"""
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import dashscope
from dashscope import Generation
import os


class NaturalLanguageProcessor:
    """自然语言处理器，将用户输入转换为视频剪辑时间轴"""
    
    def __init__(self):
        """初始化处理器"""
        # 设置API密钥
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            try:
                api_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_key.txt')
                if os.path.exists(api_key_path):
                    with open(api_key_path, 'r') as f:
                        api_key = f.read().strip()
            except:
                pass
        
        if api_key:
            dashscope.api_key = api_key
        else:
            raise Exception("未找到 DashScope API Key")
        
        # 特效和转场映射
        self.effects_mapping = {
            "模糊": "blur",
            "光晕": "glow", 
            "粒子": "particle",
            "淡入淡出": "fade",
            "缩放": "zoom",
            "旋转": "rotate",
            "滑动": "slide",
            "闪烁": "flicker",
            "震动": "shake",
            "故障": "glitch"
        }
        
        self.transition_mapping = {
            "淡入": "fade_in",
            "淡出": "fade_out",
            "交叉淡化": "cross_fade",
            "快切": "cut",
            "擦除": "wipe",
            "滑动": "slide",
            "缩放": "zoom",
            "旋转": "rotate",
            "百叶窗": "blinds",
            "溶解": "dissolve"
        }

    def extract_timeline_info(self, text: str) -> Dict:
        """从自然语言中提取时间轴信息"""
        prompt = f"""
        请分析以下视频剪辑描述，提取关键信息并生成JSON格式的输出：

        用户描述：
        {text}

        请提取并输出以下信息的JSON格式：
        {{
            "title": "视频标题",
            "total_duration": "总时长（秒）",
            "resolution": {{
                "width": 1920,
                "height": 1080
            }},
            "fps": 30,
            "segments": [
                {{
                    "segment_name": "片段名称",
                    "start_time": "开始时间（秒）",
                    "end_time": "结束时间（秒）",
                    "content": "内容描述",
                    "effects": ["特效列表"],
                    "transitions": "转场效果",
                    "text_overlay": "字幕文本（如果有）",
                    "audio": "音频描述（如果有）"
                }}
            ],
            "background_music": "背景音乐描述",
            "overall_style": "整体风格"
        }}

        注意事项：
        1. 如果用户没有明确指定时间，请根据内容合理分配
        2. 特效包括：模糊、光晕、粒子、缩放、旋转等
        3. 转场包括：淡入淡出、快切、滑动、缩放等
        4. 请确保JSON格式正确
        """

        try:
            response = Generation.call(
                model="qwen-plus",
                prompt=prompt
            )
            
            result = response.output.text
            # 提取JSON部分
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
                return json.loads(json_str)
            else:
                raise Exception("未找到有效的JSON内容")
                
        except Exception as e:
            print(f"解析错误: {e}")
            return self._create_default_timeline()

    def _create_default_timeline(self) -> Dict:
        """创建默认时间轴结构"""
        return {
            "title": "未命名视频",
            "total_duration": 60,
            "resolution": {"width": 1920, "height": 1080},
            "fps": 30,
            "segments": [],
            "background_music": "",
            "overall_style": "默认"
        }

    def generate_timeline_json(self, timeline_info: Dict) -> Dict:
        """将提取的信息转换为标准时间轴JSON格式"""
        timeline = {
            "version": "1.0",
            "timeline": {
                "duration": timeline_info.get("total_duration", 60),
                "fps": timeline_info.get("fps", 30),
                "resolution": timeline_info.get("resolution", {"width": 1920, "height": 1080}),
                "tracks": []
            }
        }
        
        # 添加视频轨道
        video_tracks = []
        text_tracks = []
        audio_tracks = []
        
        # 处理每个片段
        for i, segment in enumerate(timeline_info.get("segments", [])):
            # 视频片段
            video_clip = {
                "type": "video",
                "name": segment.get("segment_name", f"片段{i+1}"),
                "clips": [{
                    "start": float(segment.get("start_time", 0)),
                    "end": float(segment.get("end_time", 10)),
                    "clipIn": float(segment.get("start_time", 0)),
                    "clipOut": float(segment.get("end_time", 10)),
                    "filters": self._map_effects(segment.get("effects", [])),
                    "transform": {
                        "scale": 1.0,
                        "position": [960, 540]
                    }
                }]
            }
            video_tracks.append(video_clip)
            
            # 文字片段
            if segment.get("text_overlay"):
                text_clip = {
                    "type": "text",
                    "name": f"字幕{i+1}",
                    "clips": [{
                        "start": float(segment.get("start_time", 0)),
                        "end": float(segment.get("end_time", 10)),
                        "clipIn": float(segment.get("start_time", 0)),
                        "clipOut": float(segment.get("end_time", 10)),
                        "filters": [],
                        "content": {
                            "text": segment.get("text_overlay", ""),
                            "font": "思源黑体",
                            "size": 36,
                            "color": "#FFFFFF",
                            "position": "bottom"
                        }
                    }]
                }
                text_tracks.append(text_clip)
        
        # 添加背景音乐
        if timeline_info.get("background_music"):
            audio_tracks.append({
                "type": "audio",
                "name": "背景音乐",
                "clips": [{
                    "start": 0,
                    "end": timeline_info.get("total_duration", 60),
                    "clipIn": 0,
                    "clipOut": timeline_info.get("total_duration", 60),
                    "filters": [],
                    "content": {
                        "source": "bgm_001.mp3",
                        "volume": 0.6,
                        "loop": True
                    }
                }]
            })
        
        # 合并所有轨道
        timeline["timeline"]["tracks"] = video_tracks + text_tracks + audio_tracks
        
        return timeline

    def _map_effects(self, effects: List[str]) -> List[str]:
        """映射特效名称"""
        mapped_effects = []
        for effect in effects:
            for chinese, english in self.effects_mapping.items():
                if chinese in effect:
                    mapped_effects.append(f"{english}_001")
                    break
        return mapped_effects

    def process_natural_language(self, user_input: str) -> Dict:
        """
        处理自然语言输入，返回时间轴JSON
        
        Args:
            user_input: 用户的自然语言描述
            
        Returns:
            时间轴JSON字典
        """
        # 提取时间轴信息
        timeline_info = self.extract_timeline_info(user_input)
        
        # 生成标准时间轴JSON
        timeline_json = self.generate_timeline_json(timeline_info)
        
        return timeline_json

    def add_advanced_prompts(self, user_input: str) -> str:
        """为用户输入添加高级提示词，增强理解能力"""
        enhanced_prompt = f"""
        用户想要创建一个视频，描述如下：
        {user_input}
        
        请帮助理解用户意图，考虑以下方面：
        1. 视频的目标受众和使用场景
        2. 视频的情感基调和节奏
        3. 特效和转场的合理使用
        4. 音频和视觉的配合
        5. 整体的叙事结构
        
        基于这些考虑，生成一个专业的视频剪辑方案。
        """
        return enhanced_prompt


def main():
    """测试函数"""
    processor = NaturalLanguageProcessor()
    
    # 测试用例
    test_input = """
    我想做一个3分钟的产品介绍视频。
    开头5秒展示公司logo，要有光晕特效。
    然后用30秒介绍产品特点，配上动感的背景音乐，画面要有粒子特效。
    中间1分钟展示产品使用场景，每个场景之间用淡入淡出转场。
    最后30秒是用户评价，要加上字幕。
    结尾5秒再次展示logo和联系方式。
    """
    
    result = processor.process_natural_language(test_input)
    
    # 保存结果
    with open("output/test_timeline.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("处理完成，结果已保存到 output/test_timeline.json")


if __name__ == "__main__":
    main()
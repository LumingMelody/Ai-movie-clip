"""
自然语言时间轴接口
集成自然语言处理器到现有的时间轴生成系统
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .natural_language_processor import NaturalLanguageProcessor
from .timeline_generator import TimelineGenerator
from .core.controller import Controller


class NLTimelineInterface:
    """自然语言时间轴接口"""
    
    def __init__(self):
        """初始化接口"""
        self.nl_processor = NaturalLanguageProcessor()
        self.timeline_generator = TimelineGenerator()
        self.controller = Controller()
        
    def process_user_input(self, user_input: str, video_path: Optional[str] = None) -> Dict:
        """
        处理用户的自然语言输入
        
        Args:
            user_input: 用户的自然语言描述
            video_path: 可选的视频文件路径
            
        Returns:
            处理结果，包含时间轴和执行状态
        """
        result = {
            "status": "success",
            "message": "",
            "timeline": None,
            "output_path": None,
            "errors": []
        }
        
        try:
            # 1. 将自然语言转换为时间轴
            timeline = self.nl_processor.process_natural_language(user_input)
            result["timeline"] = timeline
            
            # 2. 如果提供了视频路径，验证视频信息
            if video_path:
                video_info = self._analyze_video(video_path)
                if video_info:
                    # 调整时间轴以匹配视频
                    timeline = self._adjust_timeline_for_video(timeline, video_info)
                    result["timeline"] = timeline
            
            # 3. 优化时间轴
            optimized_timeline = self.timeline_generator.optimize_timeline(timeline)
            result["timeline"] = optimized_timeline
            
            # 4. 保存时间轴
            output_path = self._save_timeline(optimized_timeline)
            result["output_path"] = str(output_path)
            
            # 5. 生成执行计划
            execution_plan = self._generate_execution_plan(optimized_timeline)
            result["execution_plan"] = execution_plan
            
            result["message"] = "时间轴生成成功！"
            
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"处理失败: {str(e)}"
            result["errors"].append(str(e))
        
        return result
    
    def generate_from_template(self, template_name: str, config: Dict) -> Dict:
        """
        基于模板和自然语言配置生成时间轴
        
        Args:
            template_name: 模板名称
            config: 包含自然语言描述的配置
            
        Returns:
            生成结果
        """
        # 如果配置中包含自然语言描述，先处理
        if "description" in config:
            nl_timeline = self.nl_processor.process_natural_language(config["description"])
            # 合并自然语言生成的结果到配置中
            config = self._merge_nl_config(config, nl_timeline)
        
        # 使用模板生成器
        timeline = self.timeline_generator.generate_advanced_timeline({
            "template": template_name,
            **config
        })
        
        return {
            "status": "success",
            "timeline": timeline,
            "template_used": template_name
        }
    
    def _analyze_video(self, video_path: str) -> Optional[Dict]:
        """分析视频信息"""
        if not os.path.exists(video_path):
            return None
        
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return None
            
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "duration": duration,
                "fps": fps,
                "resolution": {"width": width, "height": height},
                "frame_count": frame_count
            }
            
        except Exception:
            return None
    
    def _adjust_timeline_for_video(self, timeline: Dict, video_info: Dict) -> Dict:
        """调整时间轴以匹配视频信息"""
        # 更新时间轴的基本信息
        timeline["timeline"]["fps"] = video_info["fps"]
        timeline["timeline"]["resolution"] = video_info["resolution"]
        
        # 如果时间轴时长超过视频时长，进行调整
        if timeline["timeline"]["duration"] > video_info["duration"]:
            scale_factor = video_info["duration"] / timeline["timeline"]["duration"]
            
            # 缩放所有片段的时间
            for track in timeline["timeline"]["tracks"]:
                for clip in track.get("clips", []):
                    clip["start"] *= scale_factor
                    clip["end"] *= scale_factor
                    clip["clipIn"] *= scale_factor
                    clip["clipOut"] *= scale_factor
            
            timeline["timeline"]["duration"] = video_info["duration"]
        
        return timeline
    
    def _save_timeline(self, timeline: Dict) -> Path:
        """保存时间轴到文件"""
        output_dir = Path("output/nl_timelines")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        import time
        timestamp = int(time.time())
        title = timeline["metadata"].get("title", "untitled").replace(" ", "_")
        filename = f"{title}_{timestamp}.json"
        
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(timeline, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _generate_execution_plan(self, timeline: Dict) -> Dict:
        """生成执行计划"""
        plan = {
            "steps": [],
            "estimated_time": 0,
            "requirements": []
        }
        
        # 分析需要的资源
        has_video = any(t["type"] == "video" for t in timeline["timeline"]["tracks"])
        has_audio = any(t["type"] == "audio" for t in timeline["timeline"]["tracks"])
        has_text = any(t["type"] == "text" for t in timeline["timeline"]["tracks"])
        has_effects = any(t["type"] == "effect" for t in timeline["timeline"]["tracks"])
        
        if has_video:
            plan["steps"].append("加载视频素材")
            plan["requirements"].append("视频文件")
        
        if has_audio:
            plan["steps"].append("处理音频轨道")
            plan["requirements"].append("音频文件或音乐库")
        
        if has_text:
            plan["steps"].append("生成字幕和文字")
            plan["requirements"].append("字体文件")
        
        if has_effects:
            plan["steps"].append("应用视觉特效")
            plan["requirements"].append("特效处理器")
        
        plan["steps"].append("合成最终视频")
        plan["estimated_time"] = len(plan["steps"]) * 10  # 假设每步10秒
        
        return plan
    
    def _merge_nl_config(self, config: Dict, nl_timeline: Dict) -> Dict:
        """合并自然语言生成的配置"""
        # 提取有用的信息
        if "duration" not in config:
            config["duration"] = nl_timeline["timeline"]["duration"]
        
        if "tags" not in config:
            config["tags"] = nl_timeline["metadata"].get("tags", [])
        
        # 合并特效信息
        nl_effects = []
        for track in nl_timeline["timeline"]["tracks"]:
            for clip in track.get("clips", []):
                nl_effects.extend(clip.get("filters", []))
        
        if nl_effects and "effects" not in config:
            config["effects"] = list(set(nl_effects))
        
        return config


def demo_nl_interface():
    """演示自然语言接口的使用"""
    interface = NLTimelineInterface()
    
    # 示例1：简单描述
    print("=== 示例1: 简单描述 ===")
    result1 = interface.process_user_input("给视频加上转场和字幕，配上轻松的背景音乐")
    print(f"状态: {result1['status']}")
    print(f"消息: {result1['message']}")
    if result1['output_path']:
        print(f"输出: {result1['output_path']}")
    
    # 示例2：带视频文件
    print("\n=== 示例2: 指定视频文件 ===")
    result2 = interface.process_user_input(
        "这是一个产品展示视频，前10秒介绍产品，后10秒展示使用效果，加字幕说明",
        video_path="sample_video.mp4"
    )
    print(f"状态: {result2['status']}")
    if result2['execution_plan']:
        print("执行计划:")
        for step in result2['execution_plan']['steps']:
            print(f"  - {step}")
    
    # 示例3：使用模板
    print("\n=== 示例3: 模板+自然语言 ===")
    result3 = interface.generate_from_template("product", {
        "description": "30秒的手机产品宣传，展示外观、性能和价格，快节奏剪辑",
        "product_name": "SuperPhone X",
        "features": ["5G网络", "AI摄影", "全天续航"]
    })
    print(f"使用模板: {result3['template_used']}")
    print(f"生成状态: {result3['status']}")


if __name__ == "__main__":
    demo_nl_interface()
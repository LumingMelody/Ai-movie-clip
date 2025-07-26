# -*- coding: utf-8 -*-
# @Time    : 2025/6/9 17:47
# @Author  : 蔍鸣霸霸
# @FileName: prompt_pipeline.py.py
# @Software: PyCharm
# @Blog    ：只因你太美

# prompts/prompt_pipeline.py
import os
from jinja2 import Template


class PromptPipeline:
    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.template_dir = template_dir
        self.templates = self.load_all_templates()

    def load_all_templates(self):
        """加载所有模板文件"""
        templates = {}

        # 如果模板目录不存在，创建默认模板
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)
            self.create_default_templates()

        # 加载模板文件
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.txt'):
                key = filename.replace('.txt', '')
                try:
                    with open(os.path.join(self.template_dir, filename), 'r', encoding='utf-8') as f:
                        templates[key] = f.read()
                except Exception as e:
                    print(f"❌ 加载模板失败 {filename}: {e}")

        # 如果没有加载到模板，使用内置模板
        if not templates:
            templates = self.get_builtin_templates()

        return templates

    def create_default_templates(self):
        """创建默认模板文件"""
        templates = self.get_builtin_templates()
        for name, content in templates.items():
            filepath = os.path.join(self.template_dir, f"{name}.txt")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"❌ 创建模板文件失败 {name}: {e}")

    def get_builtin_templates(self):
        """内置模板"""
        return {
            "general": """你是视频剪辑助手 VideoEditorAI。你的任务是根据以下视频分析报告，生成一个适合该视频的剪辑策略。

【视频分析报告】：
- 文件名: {{filename}}
- 时长: {{duration}} 秒
- 分辨率: {{width}}x{{height}}
- 帧率: {{fps}}
- 场景切换: {{scene_changes_count}} 个
- 语音内容: "{{sample_speech_text}}"
- 音乐节奏: {{tempo}} BPM，能量值 {{energy}}
- 检测对象: {{detected_objects}}
- 是否有人脸: {{has_face}}
- 内容分类: {{content_type}}
- 情绪: {{mood}}
- 风格: {{style}}
- 用途: {{purpose}}

【用户需求】：
请帮我把这个视频剪辑成一个 {{target_duration}} 秒左右的短视频，风格为 {{target_style}}，用于 {{target_purpose}} 平台发布。

【输出要求】：
请按如下格式输出 JSON 响应，确保是有效的JSON格式：

{
  "thought_process": [
    "第一步：分析视频内容特点",
    "第二步：确定剪辑重点",
    "第三步：选择合适的剪辑手法"
  ],
  "actions": [
    {"function": "cut", "start": 0, "end": 5, "reason": "删除开头冗余部分"},
    {"function": "speedup", "start": 10, "end": 15, "factor": 1.5, "reason": "加速平淡片段"},
    {"function": "add_transition", "type": "crossfade", "start": 5, "duration": 1, "reason": "平滑过渡"}
  ]
}""",

            "human_drama": """这是一个【人声剧情类】视频，情绪为【{{mood}}】，结构为【{{structure}}】，用于【{{purpose}}】平台发布。

【视频特征】:
- 时长: {{duration}} 秒
- 语音内容: "{{sample_speech_text}}"
- 检测对象: {{detected_objects}}
- 场景变化: {{scene_changes_count}} 次

【剪辑要求】:
- 保留完整语义表达，突出重点台词
- 控制总时长在 {{target_duration}} 秒以内
- 若有多个角色，请使用交替剪辑
- 可适当添加字幕强调关键词
- 输出格式建议为 {{target_style}} 风格

请生成JSON格式的剪辑策略，包含thought_process和actions两个字段。""",

            "scenic_landscape": """这是一个【场景风景类】视频，情绪为【{{mood}}】，风格为【{{style}}】，用于【{{purpose}}】平台发布。

【视频特征】:
- 时长: {{duration}} 秒
- 音乐节奏: {{tempo}} BPM
- 检测对象: {{detected_objects}}
- 场景变化: {{scene_changes_count}} 次

【剪辑要求】:
- 突出视觉美感，保留精彩画面
- 使用慢动作特效强化震撼感
- 添加滤镜增强色彩表现力
- 配合音乐节奏进行剪辑
- 总时长控制在 {{target_duration}} 秒内
- 输出格式为 {{target_style}} 风格

请生成JSON格式的剪辑策略，包含thought_process和actions两个字段。""",

            "action_sports": """这是一个【动作运动类】视频，情绪为【{{mood}}】，用于【{{purpose}}】平台发布。

【视频特征】:
- 时长: {{duration}} 秒
- 音乐节奏: {{tempo}} BPM（高节奏）
- 检测对象: {{detected_objects}}
- 场景变化: {{scene_changes_count}} 次

【剪辑要求】:
- 快节奏剪辑，突出动感
- 保留高潮动作瞬间
- 配合强劲音乐节拍
- 使用快切和特效转场
- 控制时长在 {{target_duration}} 秒内

请生成JSON格式的剪辑策略。""",

            "live_streaming": """这是一个【直播录播类】视频，需要提取精彩片段。

【视频特征】:
- 时长: {{duration}} 秒（较长）
- 语音内容: "{{sample_speech_text}}"
- 检测对象: {{detected_objects}}

【剪辑要求】:
- 提取最精彩的片段
- 删除冗余和重复内容
- 保留完整的关键信息
- 控制最终时长在 {{target_duration}} 秒内

请生成JSON格式的剪辑策略。""",

            "advertisement": """这是一个【广告宣传片类】视频，需要突出产品特点。

【视频特征】:
- 时长: {{duration}} 秒
- 语音内容: "{{sample_speech_text}}"
- 检测对象: {{detected_objects}}

【剪辑要求】:
- 突出产品亮点
- 精炼有力的表达
- 强调核心卖点
- 使用吸引人的特效
- 控制时长在 {{target_duration}} 秒内

请生成JSON格式的剪辑策略。""",

            "music_video": """这是一个【音乐视频类】视频，需要与节拍同步剪辑。

【视频特征】:
- 时长: {{duration}} 秒
- 音乐节奏: {{tempo}} BPM
- 检测对象: {{detected_objects}}
- 场景变化: {{scene_changes_count}} 次

【剪辑要求】:
- 严格按音乐节拍剪辑
- 使用节奏感强的转场
- 突出视觉与听觉的配合
- 控制时长在 {{target_duration}} 秒内

请生成JSON格式的剪辑策略。"""
        }

    def select_template(self, classification):
        """根据分类选择模板"""
        content_type = classification.get("content_type", "unknown")

        mapping = {
            "人声剧情类": "human_drama",
            "场景风景类": "scenic_landscape",
            "动作运动类": "action_sports",
            "直播录播类": "live_streaming",
            "广告宣传片类": "advertisement",
            "音乐视频类": "music_video",
            "教育教学类": "human_drama"  # 教学类使用人声剧情类模板
        }

        template_key = mapping.get(content_type, "general")

        if template_key not in self.templates:
            print(f"⚠️ 模板 {template_key} 不存在，使用通用模板")
            template_key = "general"

        return self.templates[template_key]

    def render_template(self, template_str, context):
        """渲染模板变量"""
        try:
            t = Template(template_str)
            return t.render(context)
        except Exception as e:
            print(f"❌ 模板渲染失败: {e}")
            # 返回简化版本
            return f"""请为这个视频生成剪辑策略：
视频时长：{context.get('duration', 0)}秒
内容类型：{context.get('content_type', '未知')}
目标时长：{context.get('target_duration', 30)}秒

请输出JSON格式的剪辑方案。"""

    def build_full_prompt(self, analysis_report, user_options=None):
        """构建完整的Prompt"""
        # 默认用户选项
        default_options = {
            "target_duration": 30,
            "target_style": "抖音风",
            "target_purpose": "社交媒体"
        }

        # 合并用户输入
        options = {**default_options, **(user_options or {})}

        # 提取分析报告中的关键字段
        metadata = analysis_report.get("metadata", {})
        classification = analysis_report.get("classification", {})
        scene_changes = analysis_report.get("scene_changes", [])
        speech_text = analysis_report.get("speech_text", "")
        music_analysis = analysis_report.get("music_analysis", {})

        # 安全获取视频流信息
        video_stream = {}
        streams = metadata.get("streams", [])
        for stream in streams:
            if stream.get("type") == "video":
                video_stream = stream
                break

        # 构建上下文
        context = {
            "filename": metadata.get("filename", "unknown"),
            "duration": round(metadata.get("duration", 0), 2),
            "width": video_stream.get("width", 1920),
            "height": video_stream.get("height", 1080),
            "fps": video_stream.get("fps", 30),
            "scene_changes_count": len(scene_changes),
            "sample_speech_text": speech_text[:100] + "..." if len(speech_text) > 100 else speech_text,
            "tempo": music_analysis.get("tempo", 0),
            "energy": music_analysis.get("energy", 0),
            "detected_objects": ", ".join(analysis_report.get("detected_objects", ["无"])),
            "has_face": "有" if analysis_report.get("has_face") else "无",
            **classification,
            **options
        }

        # 选择模板并渲染
        template = self.select_template(classification)
        rendered_prompt = self.render_template(template, context)

        return rendered_prompt

    def validate_prompt(self, prompt):
        """验证prompt是否合理"""
        if len(prompt) < 100:
            return False, "Prompt过短"
        if "{{" in prompt or "}}" in prompt:
            return False, "存在未渲染的模板变量"
        return True, "验证通过"


# 便捷函数
def build_prompt(analysis_report, user_options=None):
    """快速构建prompt的便捷函数"""
    pipeline = PromptPipeline()
    return pipeline.build_full_prompt(analysis_report, user_options)
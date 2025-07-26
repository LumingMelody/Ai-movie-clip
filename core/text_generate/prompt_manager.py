# core/text_generate/prompt_manager.py

from jinja2 import Environment, FileSystemLoader
import os

try:
    from core.text_generate.config import SCENES
except ImportError:
    SCENES = {}

TEMPLATE_DIR = "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def scan_and_build_scenes():
    """动态扫描模板目录构建 SCENES 配置"""
    dynamic_scenes = {}

    try:
        if os.path.exists(TEMPLATE_DIR):
            for category in os.listdir(TEMPLATE_DIR):
                category_path = os.path.join(TEMPLATE_DIR, category)
                if os.path.isdir(category_path):
                    # 扫描该类别下的所有模板文件
                    types = {}
                    for file in os.listdir(category_path):
                        if file.endswith('.j2'):
                            style = os.path.splitext(file)[0]
                            # 根据文件名推测类型名称
                            type_name_mapping = {
                                "knowledge": "知识分享",
                                "scenario": "场景描述",
                                "suspense": "悬念式推广",
                                "painpoint": "痛点分析",
                                "straightforward": "直白式推广",
                                "testimonial": "见证式推广",
                                "inspiration": "励志式内容"
                            }
                            types[style] = type_name_mapping.get(style, style.title())

                    if types:
                        dynamic_scenes[category] = {
                            "name": category.title(),
                            "description": f"{category} 相关内容文案",
                            "types": types
                        }

        print(f"📁 [PROMPT-MANAGER] 动态扫描配置: {dynamic_scenes}")
        return dynamic_scenes

    except Exception as e:
        print(f"⚠️ [PROMPT-MANAGER] 动态扫描失败: {str(e)}")
        return {}


def get_scenes_config():
    """获取完整的 SCENES 配置（静态 + 动态）"""
    # 合并静态配置和动态扫描的配置
    dynamic_scenes = scan_and_build_scenes()
    merged_scenes = {**SCENES, **dynamic_scenes}
    return merged_scenes


def build_prompt(scene_type, content_type, data):
    """
    构建用于大模型调用的完整 Prompt
    包含：任务描述 + 输入数据 + 写作风格要求
    """
    try:
        print(f"🔍 [BUILD-PROMPT] 开始构建提示词:")
        print(f"   场景类型: {scene_type}")
        print(f"   内容类型: {content_type}")

        # 🔥 使用动态配置
        all_scenes = get_scenes_config()

        if scene_type not in all_scenes:
            raise KeyError(f"不支持的场景类型: {scene_type}，可用类型: {list(all_scenes.keys())}")

        scene_config = all_scenes[scene_type]
        scene_name = scene_config["name"]

        if content_type not in scene_config["types"]:
            raise KeyError(
                f"场景 '{scene_type}' 不支持内容类型 '{content_type}'，可用类型: {list(scene_config['types'].keys())}")

        content_name = scene_config["types"][content_type]

        template_path = f"{scene_type}/{content_type}.j2"
        print(f"📄 [BUILD-PROMPT] 模板路径: {template_path}")

        try:
            template = env.get_template(template_path)
            rendered_data = template.render(**data)
            print(f"✅ [BUILD-PROMPT] 模板渲染成功")

            # 获取视频时长并设置字数要求
            video_duration = data.get('视频时长', '10')
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
                word_limit = "35-50字"
                target_words = "40字左右"
                pace_desc = "节奏适中"
            elif duration_num <= 20:
                word_limit = "60-80字"
                target_words = "70字左右"
                pace_desc = "节奏稍慢"
            elif duration_num <= 30:
                word_limit = "90-120字"
                target_words = "100字左右"
                pace_desc = "节奏舒缓"
            else:
                word_limit = "130-180字"
                target_words = "150字左右"
                pace_desc = "内容丰富"

            full_prompt = (
                f"你现在需要为一个{scene_name}场景生成文案。\n"
                f"文案类型是：{content_name}\n"
                f"🎬 关键约束：这是一个{duration_num}秒的短视频脚本，需要{pace_desc}，字数控制在{word_limit}内。\n"
                f"📏 字数目标：请生成{target_words}的文案，确保内容充实饱满。\n"
                f"请根据以下信息撰写文案：\n\n"
                f"{rendered_data}\n\n"
                f"要求：\n"
                f"- 语言生动自然，适合口播朗读\n"
                f"- 吸引用户注意力，符合{content_name}风格\n"
                f"- 目标字数{target_words}，充分展开描述，增加细节和感染力\n"
                f"- 确保{duration_num}秒内能自然流畅地播放完成\n"
                f"- 语言节奏要适合{pace_desc}的播放效果\n"
                f"- 避免过于简短，内容要充实饱满"
            )

            print(f"✅ [BUILD-PROMPT] 提示词构建成功: {full_prompt[:100]}...")
            return full_prompt

        except Exception as template_error:
            print(f"❌ [BUILD-PROMPT] 模板处理失败: {str(template_error)}")
            return f"无法加载模板: {template_error}"

    except KeyError as e:
        print(f"❌ [BUILD-PROMPT] 配置错误: {str(e)}")
        raise e
    except Exception as e:
        print(f"❌ [BUILD-PROMPT] 构建失败: {str(e)}")
        raise e


def get_available_scenes():
    """获取可用的场景类型"""
    all_scenes = get_scenes_config()
    return list(all_scenes.keys())


def get_available_content_types(scene_type):
    """获取指定场景的可用内容类型"""
    all_scenes = get_scenes_config()
    if scene_type in all_scenes:
        return list(all_scenes[scene_type]["types"].keys())
    return []


def validate_scene_and_type(scene_type, content_type):
    """验证场景类型和内容类型是否有效"""
    all_scenes = get_scenes_config()

    if scene_type not in all_scenes:
        return False, f"不支持的场景类型: {scene_type}"

    if content_type not in all_scenes[scene_type]["types"]:
        return False, f"场景 '{scene_type}' 不支持内容类型 '{content_type}'"

    # 检查模板文件是否存在
    template_path = f"{scene_type}/{content_type}.j2"
    try:
        env.get_template(template_path)
        return True, "验证通过"
    except Exception as e:
        return False, f"模板文件不存在: {template_path}"
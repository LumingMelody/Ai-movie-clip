import os
import random
import uuid
import warnings
import subprocess
import sys
import platform

import requests
from typing import List, Union, Optional

from moviepy import CompositeAudioClip
from moviepy import (
    VideoFileClip, AudioFileClip, ImageClip, TextClip,
    CompositeVideoClip, concatenate_videoclips,
    afx, vfx
)
from moviepy.tools import close_all_clips

from config import get_user_data_dir, create_font_path
from core.clipgenerate.tongyi_get_online_url import get_online_url
from core.clipgenerate.tongyi_get_videotalk import get_videotalk
from core.cliptemplate.smart_clip_with_vocals import smart_clips

# 支持的视频文件扩展名
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv')

# 忽略 MoviePy 的资源清理警告
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")


def get_script_directory():
    """
    🔥 获取脚本所在目录（适配exe打包）
    支持PyInstaller打包后的路径获取
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接运行的python脚本
        return os.path.dirname(os.path.abspath(__file__))


def find_font_file():
    """
    🔥 查找微软雅黑字体文件
    优先级：
    1. 脚本同级目录下的微软雅黑.ttf
    2. 脚本同级目录下的msyh.ttf
    3. 用户数据目录下的字体文件
    4. 系统字体目录
    """
    script_dir = get_script_directory()
    print(f"🔍 脚本目录: {script_dir}")

    # 可能的字体文件名
    font_names = ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"]

    # 1. 优先检查脚本同级目录
    for font_name in font_names:
        font_path = os.path.join(script_dir, font_name)
        if os.path.exists(font_path):
            print(f"✅ 找到同级目录字体: {font_path}")
            return font_path

    # 2. 检查用户数据目录
    try:
        user_data_dir = get_user_data_dir()
        fonts_dir = os.path.join(user_data_dir, "fonts")
        for font_name in font_names:
            font_path = os.path.join(fonts_dir, font_name)
            if os.path.exists(font_path):
                print(f"✅ 找到用户数据目录字体: {font_path}")
                return font_path
    except:
        pass

    # 3. 检查常见系统字体目录
    system_font_paths = []

    if platform.system() == "Windows":
        system_font_paths = [
            "C:/Windows/Fonts/",
            "C:/Windows/System32/Fonts/",
            os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
        ]
    elif platform.system() == "Darwin":  # macOS
        system_font_paths = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/")
        ]
    else:  # Linux
        system_font_paths = [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            os.path.expanduser("~/.fonts/"),
            os.path.expanduser("~/.local/share/fonts/")
        ]

    for sys_path in system_font_paths:
        if os.path.exists(sys_path):
            for font_name in font_names:
                font_path = os.path.join(sys_path, font_name)
                if os.path.exists(font_path):
                    print(f"✅ 找到系统字体: {font_path}")
                    return font_path

    print("⚠️ 未找到微软雅黑字体文件")
    return None


def get_system_font_name():
    """
    🔥 获取系统字体名称
    """
    system = platform.system()

    if system == "Windows":
        return [
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",  # 黑体
            "SimSun",  # 宋体
            "KaiTi",  # 楷体
            "Arial Unicode MS",  # Arial Unicode
        ]
    elif system == "Darwin":  # macOS
        return [
            "PingFang SC",  # 苹方
            "Hiragino Sans GB",  # 冬青黑体
            "STHeiti Light",  # 华文黑体
            "Arial Unicode MS",  # Arial Unicode
        ]
    else:  # Linux
        return [
            "Noto Sans CJK SC",  # 思源黑体
            "WenQuanYi Micro Hei",  # 文泉驿微米黑
            "DejaVu Sans",  # DejaVu Sans
        ]


def create_font_path_enhanced():
    """
    🔥 增强版字体路径获取函数
    优先级：字体文件 > 系统字体名称 > 默认字体
    """
    # 1. 优先尝试找到字体文件
    font_file = find_font_file()
    if font_file:
        return font_file

    # 2. 使用系统字体名称
    system_fonts = get_system_font_name()
    for font_name in system_fonts:
        print(f"🔍 尝试系统字体: {font_name}")
        return font_name

    # 3. 最后降级到None
    print("⚠️ 未找到合适字体，使用默认字体")
    return None


def translate_to_safe_text(text):
    """
    🔄 将中文文本转换为安全的英文文本（降级方案）
    """
    char_map = {
        '企业': 'Enterprise',
        '财税': 'Finance & Tax',
        '服务': 'Service',
        '公司': 'Company',
        '专业': 'Professional',
        '团队': 'Team',
        '管理': 'Management',
        '发展': 'Development',
        '创新': 'Innovation',
        '优质': 'Quality',
        '优帮': 'YouBang',
        '常熟': 'Changshu',
        '园区': 'Park',
        '运营': 'Operation',
        '阳山': 'Yangshan',
        '数谷': 'Digital Valley',
        '领域': 'Field',
        '挑战': 'Challenge',
        '智慧': 'Smart',
        '税务': 'Tax',
        '推进': 'Advance',
        '机关': 'Authority',
        '掌控': 'Control',
        '数据': 'Data',
        '风险': 'Risk',
        '增加': 'Increase',
        '压力': 'Pressure',
        '传导': 'Transmission',
        '监管': 'Supervision',
        '合规': 'Compliance',
        '趋势': 'Trend',
        '脱颖而出': 'Stand Out',
        '经验': 'Experience',
        '精心': 'Carefully',
        '组建': 'Build',
        '全方位': 'Comprehensive',
        '提供': 'Provide',
        '基础': 'Basic',
        '业务': 'Business',
        '架构': 'Architecture',
        '设计': 'Design',
        '流程': 'Process',
        '针对': 'Target',
        '重大': 'Major',
        '交易': 'Transaction',
        '筹划': 'Planning',
        '应对': 'Response',
        '开展': 'Carry Out',
        '审计': 'Audit',
        '如同': 'Like',
        '打造': 'Build',
        '专属': 'Exclusive',
        '科室': 'Department',
        '提升': 'Improve',
        '能力': 'Capability',
        '秉持': 'Adhere',
        '诚信': 'Integrity',
        '原则': 'Principle',
        '坚守': 'Stick to',
        '客户': 'Customer',
        '至上': 'First',
        '维护': 'Maintain',
        '商业': 'Business',
        '秘密': 'Secret',
        '助力': 'Help',
        '经营': 'Operation',
        '达成': 'Achieve',
        '可持续': 'Sustainable',
        '目标': 'Goal',
    }

    # 简单替换
    safe_text = text
    for chinese, english in char_map.items():
        safe_text = safe_text.replace(chinese, english)

    # 如果仍有中文字符，截断到安全长度
    if len(safe_text) > 50:
        safe_text = safe_text[:47] + "..."

    return safe_text


def create_text_clip_robust(text: str, duration: float, is_title: bool = False) -> Optional[TextClip]:
    """
    🔥 鲁棒性增强的文字片段创建函数
    多级降级策略确保文字能正常显示
    """
    print(f"📝 创建文字片段: {text[:30]}{'...' if len(text) > 30 else ''}")

    # 🔥 修复：调整基础参数以解决定位问题
    font_size = 70 if is_title else 42  # 适中的字体大小
    color = 'yellow' if not is_title else 'white'  # 调整颜色
    stroke_color = 'black'
    stroke_width = 2

    # 🔥 修复：优化文本换行处理
    if len(text) > 18:  # 换行阈值
        words = text
        if len(words) > 36:
            text = words[:18] + "\n" + words[18:36]
            if len(words) > 36:
                text += "\n" + words[36:]
        else:
            text = words[:18] + "\n" + words[18:]

    # 策略1: 尝试使用字体文件或系统字体
    try:
        font_name = create_font_path_enhanced()

        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
            'stroke_color': stroke_color,
            'stroke_width': stroke_width,
            'method': "caption",
            'size': (1000, None),  # 🔥 修复：减小宽度避免溢出
        }

        # 只有在有有效字体时才添加font参数
        if font_name:
            text_clip_params['font'] = font_name

        print(f"🎯 尝试策略1 - 字体: {font_name or '默认'}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)

        # 测试渲染（检查是否会出现字体问题）
        try:
            # 尝试获取第一帧来验证字体渲染
            test_frame = text_clip.get_frame(0)
            print("✅ 策略1成功 - 字体渲染正常")
            return text_clip
        except Exception as e:
            print(f"⚠️ 策略1字体渲染测试失败: {e}")
            try:
                text_clip.close()
            except:
                pass
            raise e

    except Exception as e:
        print(f"❌ 策略1失败: {e}")

    # 策略2: 使用简化参数（去掉描边）
    try:
        font_name = create_font_path_enhanced()

        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
            'method': "caption",
            'size': (1000, None),
        }

        if font_name:
            text_clip_params['font'] = font_name

        print(f"🎯 尝试策略2 - 简化参数，字体: {font_name or '默认'}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略2成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略2失败: {e}")

    # 策略3: 使用最基本参数（无字体指定）
    try:
        text_clip_params = {
            'text': text,
            'font_size': font_size,
            'color': color,
            'size': (1000, None),
        }

        print("🎯 尝试策略3 - 最基本参数")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略3成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略3失败: {e}")

    # 策略4: 终极降级 - 使用纯英文字体
    try:
        # 将中文字符替换为拼音或英文描述（这是最后的降级方案）
        fallback_text = translate_to_safe_text(text)

        text_clip_params = {
            'text': fallback_text,
            'font_size': font_size,
            'color': color,
            'font': 'Arial',  # 使用最安全的英文字体
            'size': (1000, None),
        }

        print(f"🎯 尝试策略4 - 降级文本: {fallback_text}")
        text_clip = TextClip(**text_clip_params).with_duration(duration)
        print("✅ 策略4成功")
        return text_clip

    except Exception as e:
        print(f"❌ 策略4失败: {e}")

        # 最终降级：创建空白文本
        try:
            text_clip = TextClip(
                text="Text Display Error",
                font_size=font_size,
                color=color,
                size=(1000, None),
            ).with_duration(duration)
            print("⚠️ 使用错误提示文本")
            return text_clip
        except:
            # 如果连这个都失败，返回None
            print("❌ 完全无法创建文本片段")
            return None


def check_font_environment():
    """
    🔧 检查字体环境
    """
    print("🔍 检查字体环境...")
    script_dir = get_script_directory()
    print(f"📂 脚本目录: {script_dir}")

    # 检查同级目录下的字体文件
    font_files = []
    font_extensions = ['.ttf', '.ttc', '.otf']

    try:
        for file in os.listdir(script_dir):
            if any(file.lower().endswith(ext) for ext in font_extensions):
                font_files.append(file)
    except:
        pass

    if font_files:
        print(f"✅ 找到同级目录字体文件: {font_files}")
    else:
        print("⚠️ 同级目录未找到字体文件")
        print("💡 建议将微软雅黑.ttf放置到以下目录:")
        print(f"   {script_dir}")

    # 检查字体文件
    font_file = find_font_file()
    if font_file:
        print(f"✅ 将使用字体文件: {font_file}")
    else:
        print("⚠️ 未找到字体文件，将使用系统字体")
        system_fonts = get_system_font_name()
        print(f"📋 系统字体候选: {system_fonts}")

    return font_file is not None


def create_text_clip(text: str, duration: float, is_title: bool = False) -> TextClip:
    """
    🔥 修复版文字片段创建函数 - 替换原版函数
    """
    text_clip = create_text_clip_robust(text, duration, is_title)

    if text_clip is None:
        # 如果无法创建文字片段，创建一个空的占位符
        print("⚠️ 创建空白文字占位符")
        try:
            text_clip = TextClip(
                text=" ",  # 空格占位符
                font_size=70 if is_title else 42,
                color="yellow" if not is_title else "white",
                size=(1000, 100),
            ).with_duration(duration)
        except:
            # 如果连空白都无法创建，返回透明图片
            print("⚠️ 使用透明图片作为文字占位符")
            from moviepy import ColorClip
            text_clip = ColorClip(size=(1000, 100), color=(0, 0, 0), opacity=0).with_duration(duration)

    return text_clip


def safe_load_audio(audio_path):
    """
    安全加载音频文件，处理各种格式问题
    """
    if not audio_path or not os.path.exists(audio_path):
        print(f"音频文件不存在: {audio_path}")
        return None

    try:
        # 方法1：直接加载
        print(f"尝试直接加载音频: {audio_path}")
        return AudioFileClip(audio_path)
    except Exception as e1:
        print(f"直接加载音频失败: {e1}")

        try:
            # 方法2：使用ffmpeg重新编码
            temp_path = audio_path.replace('.mp3', '_fixed.mp3')
            print(f"尝试重新编码音频: {temp_path}")

            # 重新编码音频文件，去除章节信息
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-c:a', 'libmp3lame',  # 使用mp3编码
                '-b:a', '128k',  # 设置比特率
                '-ar', '44100',  # 设置采样率
                '-ac', '2',  # 设置声道数
                '-map_chapters', '-1',  # 去除章节信息
                '-y',  # 覆盖输出文件
                temp_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"音频重新编码成功: {temp_path}")
                return AudioFileClip(temp_path)
            else:
                print(f"FFmpeg重新编码失败: {result.stderr}")
        except Exception as e2:
            print(f"重新编码音频失败: {e2}")

        try:
            # 方法3：使用pydub转换
            print("尝试使用pydub转换...")
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            temp_wav = audio_path.replace('.mp3', '_temp.wav')
            audio.export(temp_wav, format="wav")
            return AudioFileClip(temp_wav)
        except Exception as e3:
            print(f"Pydub转换失败: {e3}")

        # 如果所有方法都失败，返回None
        print(f"所有音频加载方法都失败，跳过音频文件: {audio_path}")
        return None


def download_file(url: str, filename: str, save_dir: str) -> str:
    """下载文件到指定目录"""
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        print(f"文件已存在: {save_path}")
        return save_path

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"下载完成: {save_path}")
        return save_path
    except Exception as e:
        print(f"下载失败: {url}, 错误: {e}")
        raise


# 转换函数
def convert_url_to_local_path(url, base_path):
    # 提取文件名
    filename = os.path.basename(url)
    # 拼接本地路径
    local_path = os.path.join(base_path, filename)
    # 使用正斜杠或保持系统默认都可以（FastAPI等一般不敏感）
    # 如果你想要统一用 `/` 斜杠：
    local_path = local_path.replace("\\", "/")

    return local_path


def select_random_videos(files: List[str], count: int) -> List[str]:
    """随机选择指定数量的视频文件"""
    if not files:
        return []
    if len(files) <= count:
        return files
    return random.sample(files, count)


def resolve_materials(source: Union[str, List[str]], valid_extensions: tuple) -> List[str]:
    """解析素材路径（支持文件/文件夹）"""
    if not source:
        return []

    if isinstance(source, str):
        source = [source]

    resolved_files = []
    for item in source:
        item = os.path.abspath(item)

        if os.path.isfile(item) and item.lower().endswith(valid_extensions):
            resolved_files.append(item)

        elif os.path.isdir(item):
            resolved_files.extend([
                os.path.join(item, f) for f in os.listdir(item)
                if os.path.isfile(os.path.join(item, f)) and f.lower().endswith(valid_extensions)
            ])

    return resolved_files


def trans_videos_advertisement_enhance(
        data: dict,
        add_digital_host: bool = False,
        use_temp_materials: bool = False,
        clip_mode: bool = False,
        upload_digital_host: bool = False,  # True=使用materials/upload目录，False=使用materials/digital_host
        moderator_source: Optional[Union[str, List[str]]] = None,  # 可选：指定其他上传目录路径
        enterprise_source: Optional[Union[str, List[str]]] = None,  # 企业素材路径
) -> str:
    """🔥 生成视频广告（含字体修复）"""
    # 🔥 在开始前检查字体环境
    print("🔍 初始化字体环境...")
    check_font_environment()

    # 确保中文显示正常
    os.environ["IMAGEIO_FT_LIB"] = "freeimage"

    user_data_dir = get_user_data_dir()
    project_id = str(uuid.uuid1())
    project_path = os.path.join(user_data_dir, "projects", project_id)
    res_path = os.path.join("projects", project_id)
    os.makedirs(project_path, exist_ok=True)

    print(f"📂 项目路径: {project_path}")

    # ---------------------- 素材目录设置 ----------------------
    materials_root = "materials"
    base_materials_dir = os.path.join(user_data_dir, materials_root)

    # 系统默认素材目录
    system_digital_host_folder = os.path.join(base_materials_dir, "moderator")
    system_enterprise_folder = os.path.join(base_materials_dir, "enterprise")

    # 上传素材目录（固定为materials/upload）
    upload_folder = os.path.join(base_materials_dir, "upload")

    # 创建必要的目录
    os.makedirs(system_digital_host_folder, exist_ok=True)
    os.makedirs(system_enterprise_folder, exist_ok=True)
    os.makedirs(upload_folder, exist_ok=True)

    print(f"📊 素材模式: {'临时' if use_temp_materials else '正式'}")
    print(f"📂 上传素材目录: {upload_folder}")

    # ---------------------- 下载基础资源 ----------------------
    try:
        bg_image_path = download_file(data.get("data", ""), "background.png", project_path)
        bg_image = ImageClip(bg_image_path)

        # 🔥 修复：使用安全音频加载
        audio_clips = []
        for i, url in enumerate(data.get("audio_urls", [])):
            audio_path = download_file(url, f"audio_{i}.mp3", project_path)
            audio_clip = safe_load_audio(audio_path)
            if audio_clip:
                audio_clips.append(audio_clip)
            else:
                print(f"⚠️ 跳过损坏的音频文件: {audio_path}")

        # 🔥 修复：使用安全音频加载背景音乐
        bgm_path = download_file(data.get("bgm", ""), "bgm.mp3", project_path)
        bgm_clip = safe_load_audio(bgm_path)
        if not bgm_clip:
            print("⚠️ 背景音乐加载失败，将跳过背景音乐")

    except Exception as e:
        print(f"❌ 基础资源下载失败: {e}")
        raise

    # ---------------------- 处理数字人素材 ----------------------
    print(f"🔍 数字人参数: add_digital_host={add_digital_host}, upload_digital_host={upload_digital_host}")
    print(f"🔍 moderator_source={moderator_source}")
    
    # 🔥 处理URL类型的moderator_source
    if moderator_source:
        # 如果提供了moderator_source，先检查是否为URL
        processed_moderator_files = []
        
        # 确保moderator_source是列表
        if isinstance(moderator_source, str):
            moderator_source = [moderator_source]
            
        for ms in moderator_source:
            if ms.startswith(("http://", "https://")):
                # URL: 需要下载到本地
                try:
                    # 生成文件名
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(ms)
                    filename = os.path.basename(parsed_url.path.split('?')[0])
                    
                    if not filename or not filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        filename = f"moderator_{len(processed_moderator_files)}.mp4"
                    
                    # 下载文件到项目目录
                    local_path = download_file(ms, filename, project_path)
                    processed_moderator_files.append(local_path)
                    print(f"✅ 数字人素材下载成功: {filename}")
                    
                except Exception as e:
                    print(f"❌ 数字人素材下载失败: {ms}, 错误: {e}")
                    continue
            else:
                # 本地路径
                processed_moderator_files.extend(resolve_materials(
                    source=ms,
                    valid_extensions=VIDEO_EXTENSIONS
                ))
        
        digital_host_files = processed_moderator_files
        print(f"📂 使用指定的数字人素材: {len(digital_host_files)} 个文件")
        
    elif upload_digital_host:
        # 使用materials/upload目录的素材
        print(f"📂 使用上传目录的数字人素材: {upload_folder}")
        digital_host_files = resolve_materials(
            source=upload_folder,
            valid_extensions=VIDEO_EXTENSIONS
        )
    else:
        # 使用系统默认目录的素材
        print(f"📂 使用系统目录的数字人素材: {system_digital_host_folder}")

        digital_host_files = resolve_materials(
            source=system_digital_host_folder,
            valid_extensions=VIDEO_EXTENSIONS
        )
    
    print(f"📊 找到数字人素材文件: {len(digital_host_files)} 个")
    if digital_host_files:
        print(f"📋 数字人素材列表: {[os.path.basename(f) for f in digital_host_files[:5]]}...")  # 只显示前5个

    if add_digital_host and not digital_host_files:
        raise FileNotFoundError(
            f"数字人素材为空: {moderator_source or upload_folder if upload_digital_host else system_digital_host_folder}")

    # ---------------------- 处理企业素材 ----------------------
    if enterprise_source:
        # 使用指定路径的素材
        print(f"📂 使用指定路径的企业素材: {enterprise_source}")

        # 🔥 修复：处理URL下载逻辑
        processed_enterprise_source = []

        for es in enterprise_source:
            if es.startswith(("http://", "https://")):
                # URL: 需要下载到本地
                try:
                    # 从URL中提取文件名
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(es)

                    # 尝试从URL路径中获取文件名
                    filename = os.path.basename(parsed_url.path)

                    # 如果没有扩展名或文件名不合适，生成一个
                    if not filename or '.' not in filename:
                        # 从URL中提取哈希值作为文件名
                        if '/files/' in es:
                            hash_part = es.split('/files/')[1].split('?')[0]
                            filename = f"{hash_part}.mp4"
                        else:
                            # 生成随机文件名
                            filename = f"enterprise_{len(processed_enterprise_source)}.mp4"

                    # 确保有扩展名
                    if not filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        if '.' not in filename:
                            filename += '.mp4'

                    # 下载文件到项目目录
                    local_path = download_file(es, filename, project_path)
                    processed_enterprise_source.append(local_path)
                    print(f"✅ 企业素材下载成功: {filename}")

                except Exception as e:
                    print(f"❌ 企业素材下载失败: {es}, 错误: {e}")
                    continue
            else:
                # 本地路径：检查是否为相对路径，如果是则添加base路径
                if not os.path.isabs(es):
                    # 相对路径，添加到uploads目录
                    baseurl = os.path.join(get_user_data_dir(), "uploads")
                    full_path = os.path.join(baseurl, es)
                else:
                    # 绝对路径
                    full_path = es

                if os.path.exists(full_path):
                    processed_enterprise_source.append(full_path)
                    print(f"✅ 找到本地企业素材: {full_path}")
                else:
                    print(f"❌ 本地企业素材不存在: {full_path}")

        # 更新enterprise_source为处理后的本地路径列表
        enterprise_source = processed_enterprise_source

        # 解析素材文件
        enterprise_files = resolve_materials(
            source=enterprise_source,
            valid_extensions=VIDEO_EXTENSIONS
        )

        # 检查是否有可用的企业素材
        if not enterprise_files:
            print(f"⚠️ 指定的企业素材路径处理后为空")
            print(f"📋 原始路径: {enterprise_source}")
            print(f"📋 处理后路径: {processed_enterprise_source}")

            # 这里可以选择：1) 抛出错误 2) 回退到系统默认素材
            # 选择1: 抛出错误
            # raise FileNotFoundError(f"指定的企业素材路径为空: {enterprise_source}")

            # 选择2: 回退到系统默认素材（推荐）
            print("🔄 回退到系统默认企业素材")
            enterprise_source = None  # 重置为None，让后面的逻辑处理默认素材

    # 如果没有指定enterprise_source或回退到默认
    if not enterprise_source:
        # 使用系统目录的企业素材
        print(f"📂 使用系统目录的企业素材: {system_enterprise_folder}")
        enterprise_files = resolve_materials(
            source=system_enterprise_folder,
            valid_extensions=VIDEO_EXTENSIONS
        )

        # 只有在使用默认路径且为空时才报错
        if not enterprise_files:
            raise FileNotFoundError(f"企业素材为空: {system_enterprise_folder}")

    # ---------------------- 数字人视频生成 ----------------------
    start_clip = end_clip = None

    if add_digital_host:
        import random
        print(f"🎬 开始生成数字人视频...")
        print(f"📊 可用数字人素材: {len(digital_host_files)} 个")
        
        try:
            selected_host = random.choice(digital_host_files)
            print(f"📌 选择的数字人素材: {os.path.basename(selected_host)}")
            
            host_url, _ = get_online_url(selected_host)
            print(f"🌐 获取到在线URL: {host_url}")

            print(f"🎤 生成开场数字人视频，音频: {data['audio_urls'][0]}")
            start_url = get_videotalk(host_url, data["audio_urls"][0])
            print(f"✅ 开场数字人视频URL: {start_url}")
            
            print(f"🎤 生成结尾数字人视频，音频: {data['audio_urls'][-1]}")
            end_url = get_videotalk(host_url, data["audio_urls"][-1])
            print(f"✅ 结尾数字人视频URL: {end_url}")

            start_clip = VideoFileClip(download_file(start_url, "start.mp4", project_path))
            end_clip = VideoFileClip(download_file(end_url, "end.mp4", project_path))
            
            print(f"✅ 数字人视频生成成功！")

        except Exception as e:
            print(f"❌ 数字人视频生成失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            raise

    # ---------------------- 剪辑逻辑 ----------------------
    num_enterprise_clips = len(data["output"]) - (2 if add_digital_host else 0)

    if num_enterprise_clips < 0:
        raise ValueError("音频数量与输出文本数量不匹配")

    enterprise_clips = []

    if not clip_mode:  # 智能剪辑模式
        try:
            enterprise_clips = smart_clips(
                enterprise_files=enterprise_files,
                audio_clips=audio_clips[1:-1] if add_digital_host else audio_clips,
                project_dir=project_path,
                num_clips=num_enterprise_clips
            )
        except Exception as e:
            print(f"❌ 智能剪辑失败: {e}")
            print("回退到随机剪辑模式")
            clip_mode = True  # 智能剪辑失败时回退到随机剪辑

    if clip_mode:  # 随机剪辑模式

        # 🔥 修复：改进素材分配逻辑
        if add_digital_host:
            target_audio_clips = audio_clips[1:-1]  # 跳过首尾数字人
        else:
            target_audio_clips = audio_clips[1:]  # 跳过第一个标题

        num_enterprise_clips = len(target_audio_clips)
        print(f"📊 需要企业片段: {num_enterprise_clips} 个")
        print(f"📊 可用素材: {len(enterprise_files)} 个")

        # 🔥 智能分配素材，确保充分利用
        if len(enterprise_files) >= num_enterprise_clips:
            # 随机选择不重复的素材
            import random
            selected_files = random.sample(enterprise_files, num_enterprise_clips)
        else:
            # 素材不够时，尽量均匀分配
            selected_files = []
            for i in range(num_enterprise_clips):
                file_idx = i % len(enterprise_files)
                selected_files.append(enterprise_files[file_idx])

        print(f"📋 选中素材: {[os.path.basename(f) for f in selected_files]}")

        # 🔥 按顺序处理，避免索引混乱
        for idx, (audio_clip, video_file) in enumerate(zip(target_audio_clips, selected_files)):
            print(f"🎬 处理片段 {idx + 1}: {os.path.basename(video_file)}")

            video_clip = VideoFileClip(video_file)

            # 调整分辨率
            if video_clip.size[0] > video_clip.size[1]:
                video_clip = video_clip.resized((1280, 720))
            else:
                video_clip = video_clip.resized((1280, 720))

            # 时长处理
            target_duration = audio_clip.duration

            if video_clip.duration > target_duration:
                # 🔥 随机起始点，避免总是从头截取
                max_start = video_clip.duration - target_duration - 0.1
                start_time = random.uniform(0, max(0, max_start))
                video_clip = video_clip.subclipped(start_time, start_time + target_duration)
            else:
                # 循环播放
                loop_count = max(1, int(target_duration / video_clip.duration) + 1)
                video_clip = video_clip.with_effects([vfx.Loop(duration=loop_count * video_clip.duration)])
                video_clip = video_clip.subclipped(0, target_duration)

            # 绑定音频
            video_clip = video_clip.with_audio(audio_clip)
            enterprise_clips.append(video_clip)

    # ---------------------- 视频组装 ----------------------
    video_clips = []
    
    print(f"📊 视频组装信息:")
    print(f"   - 音频片段数: {len(audio_clips)}")
    print(f"   - 文本片段数: {len(data['output'])}")
    print(f"   - 企业视频片段数: {len(enterprise_clips)}")
    print(f"   - 是否添加数字人: {add_digital_host}")
    if add_digital_host:
        print(f"   - 数字人开场视频: {'已生成' if start_clip else '未生成'}")
        print(f"   - 数字人结尾视频: {'已生成' if end_clip else '未生成'}")

    for idx, (text, audio_clip) in enumerate(zip(data["output"], audio_clips)):
        current_bg = bg_image.with_duration(audio_clip.duration)
        text_clip = create_text_clip(text, audio_clip.duration)

        if add_digital_host:
            if idx == 0:  # 开场片段
                # 修复：正确获取公司名称字段
                company_name = data.get("company_name") or data.get("conpany_name", "公司名称")
                title_clip = create_text_clip(company_name, audio_clip.duration, is_title=True)

                composite = CompositeVideoClip([
                    current_bg,
                    start_clip.with_position(("center", "center")),
                    title_clip.with_position(("center", 0.15), relative=True),
                    text_clip.with_position(("center", 0.85), relative=True)
                ]).with_audio(audio_clip)

            elif idx == len(data["output"]) - 1:  # 结尾片段
                composite = CompositeVideoClip([
                    current_bg,
                    end_clip.with_position(("center", "center")),
                    text_clip.with_position(("center", 0.85), relative=True)
                ]).with_audio(audio_clip)

            else:  # 中间企业片段
                enterprise_idx = idx - 1  # 跳过第一个数字人片段
                if enterprise_idx < len(enterprise_clips):
                    composite = CompositeVideoClip([
                        current_bg,
                        enterprise_clips[enterprise_idx].with_position(("center", "center")),
                        text_clip.with_position(("center", 0.85), relative=True)
                    ]).with_audio(audio_clip)
                else:
                    # 如果索引超出范围，只显示背景和文字
                    print(f"⚠️ 企业片段索引超出范围: {enterprise_idx} >= {len(enterprise_clips)}")
                    composite = CompositeVideoClip([
                        current_bg,
                        text_clip.with_position(("center", 0.85), relative=True)
                    ]).with_audio(audio_clip)

        else:  # 🔥 修复：无数字人模式的索引计算
            if idx == 0:  # 标题片段（无企业视频背景）
                # 修复：正确获取公司名称字段
                company_name = data.get("company_name") or data.get("conpany_name", "公司名称")
                title_clip = create_text_clip(company_name, audio_clip.duration, is_title=True)

                composite = CompositeVideoClip([
                    current_bg,
                    title_clip.with_position(("center", 0.4), relative=True),
                    text_clip.with_position(("center", 0.85), relative=True)
                ]).with_audio(audio_clip)

            else:  # 普通企业片段
                # 🔥 修复：正确计算enterprise_clips的索引
                enterprise_idx = idx - 1  # 减去标题片段

                if enterprise_idx < len(enterprise_clips):
                    composite = CompositeVideoClip([
                        current_bg,
                        enterprise_clips[enterprise_idx].with_position(("center", "center")),
                        text_clip.with_position(("center", 0.85), relative=True)
                    ]).with_audio(audio_clip)
                else:
                    # 如果索引超出范围，只显示背景和文字
                    print(f"⚠️ 企业片段索引超出范围: {enterprise_idx} >= {len(enterprise_clips)}")
                    composite = CompositeVideoClip([
                        current_bg,
                        text_clip.with_position(("center", 0.85), relative=True)
                    ]).with_audio(audio_clip)

        video_clips.append(composite)

    print(f"✅ 视频片段组装完成: {len(video_clips)} 个片段")

    # ---------------------- 最终视频处理 ----------------------
    final_video = concatenate_videoclips(video_clips, method="compose")

    # 🔥 修复：安全处理背景音乐
    if bgm_clip:
        try:
            # 调整背景音乐长度匹配视频
            if bgm_clip.duration < final_video.duration:
                try:
                    bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=final_video.duration)])
                except:
                    # 手动循环
                    print("⚠️ AudioLoop不可用，使用手动循环")
                    from moviepy import concatenate_audioclips
                    loops_needed = int(final_video.duration / bgm_clip.duration) + 1
                    bgm_clips = [bgm_clip] * loops_needed
                    bgm_clip = concatenate_audioclips(bgm_clips).subclipped(0, final_video.duration)
            else:
                bgm_clip = bgm_clip.subclipped(0, final_video.duration)

            # 混合音频（背景音量设为30%）
            try:
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.with_effects([afx.MultiplyVolume(0.3)])
                ])
            except:
                # 如果MultiplyVolume不可用，使用volumex
                print("⚠️ MultiplyVolume不可用，使用volumex")
                final_audio = CompositeAudioClip([
                    final_video.audio,
                    bgm_clip.volumex(0.3)
                ])

            final_video = final_video.with_audio(final_audio)
            print("✅ 背景音乐混合成功")
        except Exception as e:
            print(f"❌ 音频混合失败: {e}")
            print("使用原始音频...")
    else:
        print("⚠️ 跳过背景音乐混合")

    # 输出视频
    output_path = os.path.join(project_path, "final_video.mp4")
    res_path = os.path.join(res_path, "final_video.mp4")
    try:
        print(f"🎬 开始生成视频: {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            fps=24,
            audio_codec="aac",
            threads=4,
        )
        print(f"✅ 视频生成完成: {output_path}")
        return res_path
    except Exception as e:
        print(f"❌ 视频生成失败: {e}")
        raise
    finally:
        # 手动关闭所有剪辑资源
        close_all_clips()


if __name__ == '__main__':
    # 🔥 在开始前检查字体环境
    print("🔍 初始化字体环境...")
    check_font_environment()

    json_data = {
        "audio_urls": [
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/74f133ee014744b4a50114e534b1ee5f.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/36a5f3c5310f43af8b2720939e63140b.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/66714b354acb438c8f34e9314b9715bb.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/91693b099d814244aa02e29bd1ebe85b.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/22cefdd470f743dfa5181fe832e6b758.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/d0ecb37928c546629cdd754bfbc680e8.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/7dd2c834afdc4aa08d599a76561275e4.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/d7a777ecb3814bd493a4635349fe022f.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/e0dd6eace6ab42ba9cf623c77be4f29a.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/4a5c6624763d42cb9eb0cfca844c6437.mp3",
            "https://lf-bot-studio-plugin-resource.coze.cn/obj/bot-studio-platform-plugin-tos/artist/image/b02f0ace38e14ef892a99f62492019bd.mp3"
        ],
        "bgm": "https://lf6-lv-music-tos.faceu.com/obj/tos-cn-ve-2774/ocM2U8riP8GkR1w5RQQWIQBxrBMmIA6t7CinZ",
        "company_name": "常熟优帮财税",  # 🔥 修复：使用正确的字段名
        "data": "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/9dc6b146a0c94ffc890996d32dea6ecb.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1778204059&x-signature=lnyYwUBJmGPE8xF4bo0J6Febaw4%3D",
        "output": [
            "在企业财税领域，当下正遭遇着重重挑战",
            "伴随智慧税务推进，税务机关掌控企业各类数据",
            "往昔不规范处易被察觉，企业涉税风险增加",
            "财政压力传导，监管更严，企业财税合规成趋势",
            "常熟优帮财税脱颖而出，有20多年专业经验",
            "精心组建专业团队，全方位为企业提供服务",
            "从基础业务到税务架构设计，提供全流程服务",
            "针对重大交易筹划，应对风险，开展审计等",
            "如同打造专属科室，提升企业财税风险能力",
            "秉持诚信原则，坚守客户至上，维护商业秘密",
            "助力企业合规经营，达成可持续发展目标"
        ]
    }

    try:
        output_path = trans_videos_advertisement_enhance(
            data=json_data,
            add_digital_host=True,  # 添加数字人
            use_temp_materials=False,  # 使用正式素材目录 (materials)
            clip_mode=True,  # 使用随机剪辑模式
            upload_digital_host=False,  # ✅ 使用系统默认目录（而非上传目录）
            moderator_source=None,  # 不指定其他路径，使用默认系统目录
            enterprise_source=None  # 使用默认企业素材目录
        )
        print(f"🎉 视频生成成功，保存路径: {output_path}")
    except Exception as e:
        print(f"❌ 视频生成失败: {e}")
        import traceback

        print(f"错误详情: {traceback.format_exc()}")

# 🔥 使用说明：
# 1. 将微软雅黑.ttf放置到脚本同级目录
# 2. 运行脚本即可自动使用同级目录的字体文件
# 3. 字体定位和大小已优化，避免遮挡问题
# 4. 支持exe打包后的字体路径自动识别
# 5. 多级字体降级策略确保兼容性
# -*- coding: utf-8 -*-
"""
字体管理模块
统一处理字体查找、文本创建和字体降级策略
"""

import os
import sys
import platform
from typing import Optional, List
from moviepy import TextClip
from config import get_user_data_dir


class FontManager:
    """字体管理器"""
    
    def __init__(self):
        self._cached_font_path = None
        self._font_search_completed = False
    
    def get_script_directory(self) -> str:
        """
        获取脚本所在目录（适配exe打包）
        支持PyInstaller打包后的路径获取
        """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            return os.path.dirname(sys.executable)
        else:
            # 如果是直接运行的python脚本
            return os.path.dirname(os.path.abspath(__file__))
    
    def find_font_file(self) -> Optional[str]:
        """
        查找微软雅黑字体文件
        优先级：
        1. 脚本同级目录下的字体文件
        2. 用户数据目录下的字体文件
        3. 系统字体目录
        """
        if self._cached_font_path and os.path.exists(self._cached_font_path):
            return self._cached_font_path
        
        if self._font_search_completed:
            return None
        
        script_dir = self.get_script_directory()
        print(f"🔍 脚本目录: {script_dir}")
        
        # 可能的字体文件名
        font_names = ["微软雅黑.ttf", "msyh.ttf", "Microsoft YaHei.ttf", "msyh.ttc"]
        
        # 1. 优先检查脚本同级目录
        for font_name in font_names:
            font_path = os.path.join(script_dir, font_name)
            if os.path.exists(font_path):
                print(f"✅ 找到同级目录字体: {font_path}")
                self._cached_font_path = font_path
                return font_path
        
        # 2. 检查用户数据目录
        try:
            user_data_dir = get_user_data_dir()
            fonts_dir = os.path.join(user_data_dir, "fonts")
            for font_name in font_names:
                font_path = os.path.join(fonts_dir, font_name)
                if os.path.exists(font_path):
                    print(f"✅ 找到用户数据目录字体: {font_path}")
                    self._cached_font_path = font_path
                    return font_path
        except Exception:
            pass
        
        # 3. 检查常见系统字体目录
        system_font_paths = self._get_system_font_paths()
        
        for sys_path in system_font_paths:
            if os.path.exists(sys_path):
                for font_name in font_names:
                    font_path = os.path.join(sys_path, font_name)
                    if os.path.exists(font_path):
                        print(f"✅ 找到系统字体: {font_path}")
                        self._cached_font_path = font_path
                        return font_path
        
        print("⚠️ 未找到微软雅黑字体文件")
        self._font_search_completed = True
        return None
    
    def _get_system_font_paths(self) -> List[str]:
        """获取系统字体目录路径"""
        system = platform.system()
        
        if system == "Windows":
            return [
                "C:/Windows/Fonts/",
                "C:/Windows/System32/Fonts/",
                os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
            ]
        elif system == "Darwin":  # macOS
            return [
                "/System/Library/Fonts/",
                "/Library/Fonts/",
                os.path.expanduser("~/Library/Fonts/")
            ]
        else:  # Linux
            return [
                "/usr/share/fonts/",
                "/usr/local/share/fonts/",
                os.path.expanduser("~/.fonts/"),
                os.path.expanduser("~/.local/share/fonts/")
            ]
    
    def get_system_font_names(self) -> List[str]:
        """获取系统字体名称"""
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
    
    def get_best_font(self) -> Optional[str]:
        """
        获取最佳可用字体
        优先级：字体文件 > 系统字体名称
        """
        # 1. 优先尝试找到字体文件
        font_file = self.find_font_file()
        if font_file:
            return font_file
        
        # 2. 使用系统字体名称
        system_fonts = self.get_system_font_names()
        if system_fonts:
            print(f"🔍 尝试系统字体: {system_fonts[0]}")
            return system_fonts[0]
        
        # 3. 最后降级到None
        print("⚠️ 未找到合适字体，使用默认字体")
        return None
    
    def check_font_environment(self) -> bool:
        """检查字体环境"""
        print("🔍 检查字体环境...")
        script_dir = self.get_script_directory()
        print(f"📂 脚本目录: {script_dir}")
        
        # 检查同级目录下的字体文件
        font_files = []
        font_extensions = ['.ttf', '.ttc', '.otf']
        
        try:
            for file in os.listdir(script_dir):
                if any(file.lower().endswith(ext) for ext in font_extensions):
                    font_files.append(file)
        except Exception:
            pass
        
        if font_files:
            print(f"✅ 找到同级目录字体文件: {font_files}")
        else:
            print("⚠️ 同级目录未找到字体文件")
            print("💡 建议将微软雅黑.ttf放置到以下目录:")
            print(f"   {script_dir}")
        
        # 检查字体文件
        font_file = self.find_font_file()
        if font_file:
            print(f"✅ 将使用字体文件: {font_file}")
        else:
            print("⚠️ 未找到字体文件，将使用系统字体")
            system_fonts = self.get_system_font_names()
            print(f"📋 系统字体候选: {system_fonts}")
        
        return font_file is not None


class TextClipCreator:
    """文本片段创建器"""
    
    def __init__(self, font_manager: FontManager = None):
        self.font_manager = font_manager or FontManager()
        
        # 中英文映射表（用于降级方案）
        self.translation_map = {
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
            # 可以继续添加更多映射...
        }
    
    def translate_to_safe_text(self, text: str) -> str:
        """将中文文本转换为安全的英文文本（降级方案）"""
        safe_text = text
        for chinese, english in self.translation_map.items():
            safe_text = safe_text.replace(chinese, english)
        
        # 如果仍有中文字符，截断到安全长度
        if len(safe_text) > 50:
            safe_text = safe_text[:47] + "..."
        
        return safe_text
    
    def create_text_clip_robust(self, text: str, duration: float, is_title: bool = False) -> Optional[TextClip]:
        """
        鲁棒性增强的文字片段创建函数
        多级降级策略确保文字能正常显示
        """
        print(f"📝 创建文字片段: {text[:30]}{'...' if len(text) > 30 else ''}")
        
        # 基础参数
        font_size = 70 if is_title else 42
        color = 'yellow' if not is_title else 'white'
        stroke_color = 'black'
        stroke_width = 2
        
        # 优化文本换行处理
        if len(text) > 18:
            words = text
            if len(words) > 36:
                text = words[:18] + "\n" + words[18:36]
                if len(words) > 36:
                    text += "\n" + words[36:]
            else:
                text = words[:18] + "\n" + words[18:]
        
        # 策略1: 尝试使用字体文件或系统字体
        font_name = self.font_manager.get_best_font()
        for strategy_num, params in enumerate([
            # 策略1: 完整参数
            {
                'text': text,
                'font_size': font_size,
                'color': color,
                'stroke_color': stroke_color,
                'stroke_width': stroke_width,
                'method': "caption",
                'size': (1000, None),
                'font': font_name
            },
            # 策略2: 简化参数（去掉描边）
            {
                'text': text,
                'font_size': font_size,
                'color': color,
                'method': "caption",
                'size': (1000, None),
                'font': font_name
            },
            # 策略3: 最基本参数（无字体指定）
            {
                'text': text,
                'font_size': font_size,
                'color': color,
                'size': (1000, None),
            },
            # 策略4: 降级文本 + 安全字体
            {
                'text': self.translate_to_safe_text(text),
                'font_size': font_size,
                'color': color,
                'font': 'Arial',
                'size': (1000, None),
            }
        ], 1):
            try:
                # 过滤掉None值的参数
                filtered_params = {k: v for k, v in params.items() if v is not None}
                
                print(f"🎯 尝试策略{strategy_num} - 字体: {filtered_params.get('font', '默认')}")
                text_clip = TextClip(**filtered_params).with_duration(duration)
                
                # 测试渲染
                try:
                    test_frame = text_clip.get_frame(0)
                    print(f"✅ 策略{strategy_num}成功 - 字体渲染正常")
                    return text_clip
                except Exception as e:
                    print(f"⚠️ 策略{strategy_num}字体渲染测试失败: {e}")
                    try:
                        text_clip.close()
                    except:
                        pass
                    raise e
                    
            except Exception as e:
                print(f"❌ 策略{strategy_num}失败: {e}")
                continue
        
        # 最终降级：创建错误提示文本
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
    
    def create_text_clip_safe(self, text: str, duration: float, is_title: bool = False) -> TextClip:
        """
        安全的文本片段创建函数（保证总是返回有效的TextClip）
        """
        text_clip = self.create_text_clip_robust(text, duration, is_title)
        
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


# 全局实例
_font_manager = FontManager()
_text_creator = TextClipCreator(_font_manager)

# 便捷函数
def check_font_environment() -> bool:
    """检查字体环境"""
    return _font_manager.check_font_environment()

def create_text_clip(text: str, duration: float, is_title: bool = False) -> TextClip:
    """创建文本片段（便捷函数）"""
    return _text_creator.create_text_clip_safe(text, duration, is_title)

def get_best_font() -> Optional[str]:
    """获取最佳可用字体（便捷函数）"""
    return _font_manager.get_best_font()
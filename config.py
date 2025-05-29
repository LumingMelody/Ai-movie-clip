import os
import platform

import yaml
from typing import Dict, Optional

CONFIG_PATH = "config.yaml"
KEY_PATH = "key.yaml"

def load_config(config_path: Optional[str] = None,key_path: Optional[str] = None) -> Dict:
    """
    加载配置文件并返回字典。
    - 如果未提供 config_path，则使用默认路径 CONFIG_PATH。
    - 返回的路径已转换为绝对路径。
    """
    if config_path is None:
        config_path = CONFIG_PATH

    if key_path is None:
        key_path = KEY_PATH

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    base_dir = os.path.dirname(os.path.abspath(config_path))
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    with open(key_path, "r", encoding="utf-8") as f:
        keys = yaml.safe_load(f)

    config.update(keys)
    # # 将相对路径转换为绝对路径
    # for key in ["cliplogs", "clipmaterials", "clipoutputs", "clipprojects"]:
    #     if key in config:
    #         config[key] = os.path.abspath(os.path.join(base_dir, config[key]))
    # if key in ["tongyi","coze"]:
    #     if key in config:
    #         config[key] = os.path.abspath(os.path.join(base_dir, config[key]))

    return config

# 用户数据目录函数（保持不变）
def get_user_data_dir():
    app_name = "ikun"
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
    elif platform.system() == "Darwin":
        appdata = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    elif platform.system() == "Linux":
        appdata = os.path.join(os.path.expanduser('~'), '.config')
    else:
        appdata = os.path.expanduser('~')

    user_data_dir = os.path.join(appdata, app_name)
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir


def create_font_path() -> str:
    """获取项目根目录下的微软雅黑字体文件路径"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    font_path = os.path.join(script_dir, "微软雅黑.ttf")

    # print(f"使用字体文件: {font_path}")
    return font_path

if __name__ == "__main__":
    # config = load_config()
    # print(config)
    create_font_path()
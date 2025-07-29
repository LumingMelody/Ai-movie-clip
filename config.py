import os
import yaml
import sys
from typing import Dict, Optional

CONFIG_PATH = "config.yaml"
KEY_PATH = "key.yaml"


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包环境"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_path = sys._MEIPASS
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def load_config(config_path: Optional[str] = None, key_path: Optional[str] = None) -> Dict:
    """
    加载配置文件并返回字典。
    - 如果未提供 config_path，则使用默认路径 CONFIG_PATH。
    - 返回的路径已转换为绝对路径。
    """
    if config_path is None:
        config_path = get_resource_path(CONFIG_PATH)
    else:
        config_path = get_resource_path(config_path)

    if key_path is None:
        key_path = get_resource_path(KEY_PATH)
    else:
        key_path = get_resource_path(key_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")

    if not os.path.exists(key_path):
        raise FileNotFoundError(f"密钥文件未找到: {key_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    with open(key_path, "r", encoding="utf-8") as f:
        keys = yaml.safe_load(f)

    config.update(keys)
    return config


# 用户数据目录函数（保持不变）
def get_user_data_dir():
    app_name = "ikun"

    # 优先使用环境变量指定的目录（适用于容器挂载）
    if "IKUN_DATA_DIR" in os.environ:
        return os.environ["IKUN_DATA_DIR"]

    # 所有环境都使用项目根目录下的ikun目录
    # 获取当前脚本所在目录作为项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    user_data_dir = os.path.join(project_root, app_name)
    os.makedirs(user_data_dir, exist_ok=True)
    return user_data_dir


def create_font_path() -> str:
    """获取项目根目录下的微软雅黑字体文件路径"""
    return get_resource_path("微软雅黑.ttf")

if __name__ == "__main__":
    # live_config = load_config()
    # print(live_config)
    # result = create_font_path()
    # print(result)
    print(get_user_data_dir())
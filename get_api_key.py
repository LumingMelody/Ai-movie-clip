import os
import sys


def get_api_key_from_file(file_name="api_key.txt"):
    """
    从本地文件读取 API Key
    :param file_name: 文件名（默认：api_key.txt）
    :return: API Key 字符串或 None（读取失败时）
    """
    try:
        # 适配开发环境和打包环境的路径
        if hasattr(sys, '_MEIPASS'):
            # 打包后路径（例如：dist/目录下）
            base_path = sys._MEIPASS
        else:
            # 开发环境路径（脚本同级目录）
            base_path = os.path.abspath(os.path.dirname(__file__))

        # 拼接完整文件路径
        file_path = os.path.join(base_path, file_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"API Key 文件未找到：{file_path}")

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()

        # 验证内容非空
        if not api_key:
            raise ValueError("API Key 文件内容为空")

        return api_key

    except FileNotFoundError as e:
        print(f"错误：{e}，请检查文件路径是否正确")
        return None
    except PermissionError:
        print(f"错误：无权限访问文件 {file_name}")
        return None
    except Exception as e:
        print(f"读取 API Key 失败：{e}")
        return None



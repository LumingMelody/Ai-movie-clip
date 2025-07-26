""" This example describes how to use the workflow interface to chat. """
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL
from doubaoconfigs import coze_api_token

# Get an access_token through personal access token or oauth.
coze_api_token = coze_api_token
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa
import json
import requests
import os
import tempfile
from urllib.parse import urlparse
from config import get_user_data_dir
from core.cliptemplate.coze.transform.coze_videos_cloths_fast_change import trans_videos_clothes_fast_change


def is_url(path):
    """
    🔥 判断是否为URL链接
    """
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False


def download_image_from_url(url, local_path=None):
    """
    🔥 从URL下载图片到本地
    """
    try:
        print(f"🌐 正在下载图片: {url}")

        # 如果没有指定本地路径，创建临时文件
        if not local_path:
            # 🔥 修复：生成安全的文件名
            import hashlib
            import time

            # 从URL中尝试提取文件扩展名
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)

            # 提取扩展名
            if '.' in original_filename:
                # 从原始文件名提取扩展名
                ext = original_filename.split('.')[-1].lower()
                # 只保留常见的图片扩展名
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                    ext = 'jpg'  # 默认扩展名
            else:
                ext = 'jpg'  # 默认扩展名

            # 🔥 生成安全的文件名：使用时间戳+哈希
            timestamp = str(int(time.time()))
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_filename = f"clothes_{timestamp}_{url_hash}.{ext}"

            # 创建临时目录
            temp_dir = os.path.join(get_user_data_dir(), "temp_images")
            os.makedirs(temp_dir, exist_ok=True)
            local_path = os.path.join(temp_dir, safe_filename)

        # 下载图片
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # 🔥 验证下载的文件
        if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
            raise Exception("下载的文件为空或不存在")

        # 🔥 验证文件是否为有效图片
        try:
            from PIL import Image
            with Image.open(local_path) as img:
                img.verify()  # 验证图片完整性
            print(f"✅ 图片验证通过: {local_path} (大小: {os.path.getsize(local_path)} bytes)")
        except Exception as e:
            print(f"⚠️ 图片验证警告: {str(e)}")
            # 不抛出异常，继续处理

        print(f"✅ 图片下载完成: {local_path}")
        return local_path

    except Exception as e:
        print(f"❌ 图片下载失败: {str(e)}")
        raise


def validate_and_convert_image(image_path):
    """
    🔥 新增：验证并转换图片格式
    确保图片格式被Coze接受
    """
    try:
        from PIL import Image
        import tempfile

        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise Exception(f"图片文件不存在: {image_path}")

        # 打开并验证图片
        with Image.open(image_path) as img:
            print(f"📸 原始图片信息 - 格式: {img.format}, 尺寸: {img.size}, 模式: {img.mode}")

            # 如果图片格式不是JPEG，转换为JPEG
            if img.format.upper() not in ['JPEG', 'JPG']:
                print(f"🔄 转换图片格式: {img.format} -> JPEG")

                # 如果是RGBA模式，转换为RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # 生成新的文件路径
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                new_path = os.path.join(os.path.dirname(image_path), f"{base_name}_converted.jpg")

                # 保存为JPEG格式
                img.save(new_path, 'JPEG', quality=95)
                print(f"✅ 图片转换完成: {new_path}")

                # 删除原文件（如果是临时文件）
                if "temp_images" in image_path:
                    try:
                        os.remove(image_path)
                        print(f"🗑️ 已删除原始临时文件: {image_path}")
                    except:
                        pass

                return new_path
            else:
                print("✅ 图片格式已是JPEG，无需转换")
                return image_path

    except Exception as e:
        print(f"❌ 图片验证/转换失败: {str(e)}")
        return image_path  # 返回原始路径，让后续流程处理


def get_videos_clothes_fast_change(has_figure: bool, clothesurl: str, description: str, is_down: bool = True):
    """
    🔥 修改版本：支持传入图片链接或本地文件路径

    Args:
        has_figure (bool): 是否有人物
        clothesurl (str): 服装图片路径或URL链接
        description (str): 描述信息
        is_down (bool): 是否下载

    Returns:
        str: warehouse路径
    """
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)
    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7495051166088020020'

    # 🔥 处理输入：支持URL或本地文件
    if is_url(clothesurl):
        print(f"🌐 检测到图片URL: {clothesurl}")
        # 下载图片到本地
        local_clothes_path = download_image_from_url(clothesurl)
        cleanup_temp_file = True  # 标记需要清理临时文件
    else:
        print(f"📁 使用本地图片: {clothesurl}")
        if not os.path.exists(clothesurl):
            raise ValueError(f"❌ 本地图片文件不存在: {clothesurl}")
        local_clothes_path = clothesurl
        cleanup_temp_file = False  # 不需要清理本地文件

    try:
        # 🔥 验证并转换图片格式
        local_clothes_path = validate_and_convert_image(local_clothes_path)

        # 上传文件到Coze
        url = "https://api.coze.cn/v1/files/upload"
        headers = {
            "Authorization": "Bearer " + coze_api_token,
        }

        print(f"📤 正在上传图片到Coze: {local_clothes_path}")

        # 🔥 验证文件在上传前
        if not os.path.exists(local_clothes_path):
            raise Exception(f"文件不存在: {local_clothes_path}")

        file_size = os.path.getsize(local_clothes_path)
        if file_size == 0:
            raise Exception(f"文件大小为0: {local_clothes_path}")

        print(f"📊 文件信息 - 路径: {local_clothes_path}, 大小: {file_size} bytes")

        # 🔥 使用正确的文件名进行上传
        upload_filename = os.path.basename(local_clothes_path)
        print(f"📝 上传文件名: {upload_filename}")

        # 打开文件并发送POST请求
        with open(local_clothes_path, 'rb') as file:
            files = {'file': (upload_filename, file, 'image/jpeg')}  # 🔥 明确指定MIME类型
            response = requests.post(url, headers=headers, files=files)

        # 🔥 详细的响应检查
        print(f"📡 上传响应状态码: {response.status_code}")
        print(f"📡 上传响应内容: {response.text[:500]}...")  # 只显示前500字符

        if response.status_code != 200:
            raise Exception(f"文件上传失败，状态码: {response.status_code}, 响应: {response.text}")

        try:
            res_json = response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"响应JSON解析失败: {str(e)}, 原始响应: {response.text}")

        # 🔥 更详细的响应验证
        if 'code' in res_json and res_json['code'] != 0:
            error_msg = res_json.get('msg', '未知错误')
            error_detail = res_json.get('detail', {})
            raise Exception(f"Coze API错误 (code: {res_json['code']}): {error_msg}, 详情: {error_detail}")

        if 'data' not in res_json or 'id' not in res_json['data']:
            raise Exception(f"文件上传响应格式错误，缺少必要字段: {res_json}")

        fileid = res_json["data"]["id"]
        print(f"✅ 文件上传成功，文件ID: {fileid}")

        # 构建参数
        parameters = {
            "has_figure": has_figure,
            "clothes": "{\"file_id\": \"" + fileid + "\"}",
            "description": description,
            "is_down": is_down,
        }

        print(f"🚀 开始调用Coze工作流，参数: {parameters}")

        # Call the coze.workflows.runs.create method to create a workflow run.
        workflow = coze.workflows.runs.create(
            workflow_id=workflow_id,
            parameters=parameters
        )

        print("workflow.data", workflow.data)
        response = json.loads(workflow.data)

        # 生成视频
        print("🎬 开始生成换装视频...")
        result_path = trans_videos_clothes_fast_change(response)

        # 🔥 返回warehouse路径
        user_data_dir = get_user_data_dir()
        if os.path.isabs(result_path):
            # 如果是绝对路径，转换为相对路径
            relative_path = os.path.relpath(result_path, user_data_dir)
            warehouse_path = relative_path.replace('\\', '/')
        else:
            # 如果已经是相对路径
            warehouse_path = result_path.replace('\\', '/')

        print(f"📁 warehouse路径: {warehouse_path}")
        return warehouse_path

    finally:
        # 🔥 清理临时文件（包括转换后的文件）
        if cleanup_temp_file:
            temp_files = []
            if os.path.exists(local_clothes_path):
                temp_files.append(local_clothes_path)

            # 清理可能的转换文件
            temp_dir = os.path.join(get_user_data_dir(), "temp_images")
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    if file.startswith("clothes_") or "_converted." in file:
                        temp_files.append(os.path.join(temp_dir, file))

            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"🗑️ 已清理临时文件: {temp_file}")
                except Exception as e:
                    print(f"⚠️ 清理临时文件失败: {str(e)}")


def get_videos_clothes_fast_change_batch(clothes_list: list, description: str, has_figure: bool = False,
                                         is_down: bool = True):
    """
    🔥 新增：批量处理多个服装图片

    Args:
        clothes_list (list): 服装图片路径或URL列表
        description (str): 描述信息
        has_figure (bool): 是否有人物
        is_down (bool): 是否下载

    Returns:
        list: warehouse路径列表
    """
    results = []

    for i, clothesurl in enumerate(clothes_list, 1):
        try:
            print(f"\n🔄 处理第 {i}/{len(clothes_list)} 个服装图片...")
            result_path = get_videos_clothes_fast_change(has_figure, clothesurl, f"{description} - 第{i}套", is_down)
            results.append(result_path)
            print(f"✅ 第 {i} 个视频生成成功: {result_path}")
        except Exception as e:
            print(f"❌ 第 {i} 个图片处理失败: {str(e)}")
            results.append(None)

    success_count = len([r for r in results if r is not None])
    print(f"\n🎉 批量处理完成：成功 {success_count}/{len(clothes_list)} 个")

    return results


def clean_temp_images():
    """
    🔥 清理临时图片文件夹
    """
    temp_dir = os.path.join(get_user_data_dir(), "temp_images")
    if os.path.exists(temp_dir):
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print("🗑️ 临时图片目录已清理")
        except Exception as e:
            print(f"⚠️ 清理临时目录失败: {str(e)}")
    else:
        print("📁 临时图片目录不存在")


if __name__ == '__main__':
    # 🔥 示例1：使用本地文件
    print("=== 测试本地文件 ===")
    has_figure = False
    clothesurl = "Y:\\Ai-movie-clip__\\推荐中年妇女毛衣.png"  # 本地文件路径
    description = "适合40-60岁中年妇女的纺织毛衣"
    is_down = False

    try:
        result_path = get_videos_clothes_fast_change(has_figure, clothesurl, description, is_down)
        print(f"✅ 本地文件处理结果: {result_path}")
    except Exception as e:
        print(f"❌ 本地文件处理失败: {str(e)}")

    # 🔥 示例2：使用图片URL
    print("\n=== 测试图片URL ===")
    clothes_url = "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/e52a65c1e97148f1a58ad30414d1077b.jpg~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1776161691&x-signature=RZ9IXKiJu1ySr2wW%2F%2FqaCuLC7Sc%3D&x-wf-file_name=v2-311f156bc93f8eeecbde57914439fd6d_720w.jpg"

    try:
        result_path = get_videos_clothes_fast_change(has_figure, clothes_url, description, is_down)
        print(f"✅ 图片URL处理结果: {result_path}")
    except Exception as e:
        print(f"❌ 图片URL处理失败: {str(e)}")

    # 🔥 示例3：批量处理
    print("\n=== 测试批量处理 ===")
    clothes_list = [
        "Y:\\Ai-movie-clip__\\推荐中年妇女毛衣.png",  # 本地文件
        "https://example.com/dress1.jpg",  # URL
        "https://example.com/dress2.jpg",  # URL
    ]

    try:
        results = get_videos_clothes_fast_change_batch(clothes_list, "时尚女装系列")
        print(f"✅ 批量处理结果: {results}")
    except Exception as e:
        print(f"❌ 批量处理失败: {str(e)}")

    # 🔥 清理临时文件
    clean_temp_images()
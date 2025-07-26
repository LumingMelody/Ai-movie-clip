""" This example describes how to use the workflow interface to chat. """
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL
from doubaoconfigs import coze_api_token
import json
import requests
import os
import tempfile
import hashlib
import time
from urllib.parse import urlparse
from PIL import Image
from config import get_user_data_dir
from core.cliptemplate.coze.transform.coze_videos_clothes_diffrent_scene import get_trans_video_clothes_diffrent_scene

# Get an access_token through personal access token or oauth.
coze_api_token = coze_api_token
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL
from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType


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
    🔥 验证并转换图片格式
    确保图片格式被Coze接受
    """
    try:
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


def upload_image_to_coze(local_path: str) -> str:
    """
    🔥 上传图片到Coze

    Args:
        local_path: 本地图片路径

    Returns:
        str: 文件ID，上传失败返回None
    """
    try:
        url = "https://api.coze.cn/v1/files/upload"
        headers = {
            "Authorization": "Bearer " + coze_api_token,
        }

        print(f"📤 正在上传图片到Coze: {local_path}")

        # 验证文件在上传前
        if not os.path.exists(local_path):
            raise Exception(f"文件不存在: {local_path}")

        file_size = os.path.getsize(local_path)
        if file_size == 0:
            raise Exception(f"文件大小为0: {local_path}")

        print(f"📊 文件信息 - 路径: {local_path}, 大小: {file_size} bytes")

        # 使用正确的文件名进行上传
        upload_filename = os.path.basename(local_path)
        print(f"📝 上传文件名: {upload_filename}")

        # 打开文件并发送POST请求
        with open(local_path, 'rb') as file:
            files = {'file': (upload_filename, file, 'image/jpeg')}
            response = requests.post(url, headers=headers, files=files)

        # 详细的响应检查
        print(f"📡 上传响应状态码: {response.status_code}")

        if response.status_code != 200:
            raise Exception(f"文件上传失败，状态码: {response.status_code}, 响应: {response.text}")

        try:
            res_json = response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"响应JSON解析失败: {str(e)}, 原始响应: {response.text}")

        # 更详细的响应验证
        if 'code' in res_json and res_json['code'] != 0:
            error_msg = res_json.get('msg', '未知错误')
            error_detail = res_json.get('detail', {})
            raise Exception(f"Coze API错误 (code: {res_json['code']}): {error_msg}, 详情: {error_detail}")

        if 'data' not in res_json or 'id' not in res_json['data']:
            raise Exception(f"文件上传响应格式错误，缺少必要字段: {res_json}")

        file_id = res_json["data"]["id"]
        print(f"✅ 图片上传成功，文件ID: {file_id}")
        return file_id

    except Exception as e:
        print(f"❌ 图片上传失败: {str(e)}")
        raise


def get_video_clothes_diffrent_scene(has_figure: bool, clothesurl: str, description: str,
                                     is_down: bool = True):
    """
    🔥 修改版本：支持HTTP链接和本地路径的服装场景视频生成

    Args:
        has_figure (bool): 是否有人物
        clothesurl (str): 服装图片路径或URL
        description (str): 描述信息
        categoryId (str): 分类ID
        is_down (bool): 是否下载

    Returns:
        str: 生成的视频路径
    """
    print(f"🎯 开始处理服装场景视频生成...")
    print(
        f"📊 参数信息: has_figure={has_figure}, description='{description}', is_down={is_down}")
    print(f"📋 输入图片: {clothesurl}")

    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)
    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7494924152006295571'

    temp_files_to_cleanup = []

    try:
        # 🔥 处理输入：支持URL或本地文件
        if is_url(clothesurl):
            print(f"🌐 检测到图片URL: {clothesurl}")
            # 下载图片到本地
            local_clothes_path = download_image_from_url(clothesurl)
            temp_files_to_cleanup.append(local_clothes_path)
        else:
            print(f"📁 使用本地图片: {clothesurl}")
            if not os.path.exists(clothesurl):
                raise ValueError(f"❌ 本地图片文件不存在: {clothesurl}")
            local_clothes_path = clothesurl

        # 🔥 验证并转换图片格式
        local_clothes_path = validate_and_convert_image(local_clothes_path)
        if local_clothes_path not in temp_files_to_cleanup:
            temp_files_to_cleanup.append(local_clothes_path)

        # 🔥 上传文件到Coze
        file_id = upload_image_to_coze(local_clothes_path)

        # 🔥 构建参数
        parameters = {
            "has_figure": has_figure,
            "clothes": json.dumps({"file_id": file_id}),
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

        # 🔥 生成视频
        print("🎬 开始生成场景视频...")
        result_path = get_trans_video_clothes_diffrent_scene(response)

        # 🔥 返回warehouse路径（相对路径）
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

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        raise

    finally:
        # 🔥 清理临时文件
        for temp_file in temp_files_to_cleanup:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🗑️ 已清理临时文件: {temp_file}")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {str(e)}")


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
    # 🔥 测试用例1：本地文件
    print("=== 测试本地文件 ===")
    has_figure = False
    clothesurl = "Y:\\Ai-movie-clip__\\推荐中年妇女毛衣.png"
    description = "适合40-60岁中年妇女的纺织毛衣"
    categoryId = "8"
    is_down = False

    try:
        if os.path.exists(clothesurl):
            result_path = get_video_clothes_diffrent_scene(has_figure, clothesurl, description, categoryId, is_down)
            print(f"✅ 本地文件测试成功: {result_path}")
        else:
            print(f"⚠️ 本地文件不存在，跳过测试: {clothesurl}")
    except Exception as e:
        print(f"❌ 本地文件测试失败: {str(e)}")

    # 🔥 测试用例2：HTTP链接
    print("\n=== 测试HTTP链接 ===")
    has_figure = True
    clothesurl = "https://files.cstlanbaai.com/robot/images/fa4b4d3a2ee383057ac505e70e1e004ca9331d6ba350bec49d2894579a3cb30f.jpeg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=zklb%2F20250606%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250606T075846Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=0660788749c898114152eaf4d3bd5b1756f430f0eb26c0f7b903810f702fd174"
    description = "女性蓝色纺织毛衣"
    categoryId = "8"
    is_down = True

    try:
        result_path = get_video_clothes_diffrent_scene(has_figure, clothesurl, description, categoryId, is_down)
        print(f"✅ HTTP链接测试成功: {result_path}")
    except Exception as e:
        print(f"❌ HTTP链接测试失败: {str(e)}")

    # 清理临时文件
    clean_temp_images()

    print("\n🎉 测试完成！")
import requests
import os
import platform
from urllib.parse import urlparse
from pathlib import Path

from config import get_user_data_dir


def get_existing_files(download_path):
    """
    获取下载目录中已存在的文件信息

    Args:
        download_path (str): 下载目录路径

    Returns:
        dict: 文件路径映射 {path: full_file_path}
    """
    existing_files = {}

    if not os.path.exists(download_path):
        return existing_files

    try:
        for filename in os.listdir(download_path):
            file_path = os.path.join(download_path, filename)
            if os.path.isfile(file_path) and filename.endswith('.mp4'):
                # 从文件名中提取原始路径（如果有的话）
                # 这里假设文件名包含原始路径信息，或者我们可以通过其他方式匹配
                existing_files[filename] = file_path

                # 如果文件名中包含路径信息，也添加路径作为key
                if '+' in filename:
                    # 尝试从文件名中提取path（基于你的命名规则）
                    parts = filename.split('+')
                    if len(parts) > 1:
                        potential_path = parts[0] + '.mp4'
                        existing_files[potential_path] = file_path

        print(f"📁 发现已存在的.mp4文件: {len(existing_files)} 个")

    except Exception as e:
        print(f"⚠️ 读取下载目录时出错: {e}")

    return existing_files


def compare_and_filter_materials(materials, existing_files):
    """
    对比API返回的素材和本地已存在的文件，过滤出需要下载的文件
    🔥 修改：使用原始路径作为文件名进行比较
    """
    to_download = []
    skipped = []

    for material in materials:
        path = material.get('path', '')
        name = material.get('name', '')
        url = material.get('url', '')

        # 🔥 修改：使用原始路径作为文件名
        if path:
            # 从path中提取文件名
            original_filename = os.path.basename(path)
            # 确保是.mp4格式
            if not original_filename.endswith('.mp4'):
                original_filename += '.mp4'
            file_name = original_filename
        else:
            # 如果没有path，使用name或默认名称
            file_name = name if name else f"video_{material.get('id', 'unknown')}.mp4"
            if not file_name.endswith('.mp4'):
                file_name += '.mp4'

        # 清理文件名中的非法字符（保留更多字符，避免冲突）
        safe_filename = "".join(c for c in file_name if c.isalnum() or c in '.-_() ')

        # 检查是否已存在
        is_existing = False
        existing_file_path = None

        # 🔥 修改：主要通过原始路径文件名检查
        if safe_filename in existing_files:
            is_existing = True
            existing_file_path = existing_files[safe_filename]
        elif path and os.path.basename(path) in existing_files:
            is_existing = True
            existing_file_path = existing_files[os.path.basename(path)]
        elif name in existing_files:
            is_existing = True
            existing_file_path = existing_files[name]

        # 调试信息
        print(f"🔍 检查文件: {safe_filename}")
        print(f"   原始路径: {path}")
        print(f"   原始名称: {name}")
        print(f"   是否存在: {is_existing}")

        if is_existing:
            skipped.append({
                'material': material,
                'reason': 'already_exists',
                'existing_path': existing_file_path
            })
        else:
            to_download.append(material)

    return to_download, skipped


def download_file_with_progress(url, filepath, headers=None):
    """
    下载单个文件，带进度显示

    Args:
        url (str): 文件下载URL
        filepath (str): 保存文件的完整路径
        headers (dict): 请求头

    Returns:
        bool: 下载是否成功
    """
    try:
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    # 显示进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"\r📥 下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)", end='')
                    else:
                        print(f"\r📥 已下载: {downloaded_size} bytes", end='')

        print(f"\n✅ 下载完成: {os.path.basename(filepath)}")
        return True

    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        # 如果下载失败，删除不完整的文件
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
        return False


def download_materials_from_api(tag="", custom_headers=None):
    """
    从API获取素材列表并下载所有.mp4文件
    🔥 修改：使用原始路径作为文件名

    Args:
        tag (str): 素材标签，默认为"装修行业"
        custom_headers (dict): 自定义请求头，如果不提供则使用默认的

    Returns:
        list: 下载成功的文件路径列表
    """
    # API地址
    api_url = f"https://agent.cstlanbaai.com/gateway/admin-api/infra/file/material/list?start=&tag={tag}"

    # 设置请求头
    if custom_headers:
        headers = custom_headers
    else:
        headers = {
            'Authorization': 'Bearer test1',
            'tenant-id': '1'
        }

    # 设置下载目录
    user_data_dir = get_user_data_dir()
    materials_dir = os.path.join(user_data_dir, "materials")
    download_path = os.path.join(materials_dir, "download")
    os.makedirs(download_path, exist_ok=True)

    downloaded_files = []

    try:
        print(f"🔍 正在请求API: {api_url}")
        print(f"🔑 请求头: {headers}")

        # 请求API
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()

        # 解析响应
        data = response.json()

        if data.get('code') != 0:
            print(f"❌ API返回错误: {data.get('msg', '未知错误')}")
            return downloaded_files

        materials = data.get('data', [])

        if not materials:
            print("⚠️ 没有找到任何素材文件")
            return downloaded_files

        print(f"📁 找到 {len(materials)} 个素材文件")

        # 过滤出.mp4文件
        mp4_materials = [m for m in materials if m.get('type') == 'video/mp4' or m.get('url', '').endswith('.mp4')]

        if not mp4_materials:
            print("⚠️ 没有找到.mp4格式的视频文件")
            return downloaded_files

        print(f"🎬 找到 {len(mp4_materials)} 个.mp4视频文件")

        # 获取本地已存在的文件
        existing_files = get_existing_files(download_path)

        # 对比并过滤出需要下载的文件
        to_download, skipped = compare_and_filter_materials(mp4_materials, existing_files)

        # 显示跳过的文件
        if skipped:
            print(f"\n⏭️ 跳过已存在的文件 ({len(skipped)} 个):")
            for skip_info in skipped:
                material = skip_info['material']
                existing_path = skip_info['existing_path']
                print(f"   ✅ {material.get('name', 'unknown')} -> {existing_path}")

        if not to_download:
            print("\n🎉 所有文件都已存在，无需下载！")
            # 返回已存在的文件路径
            return list(existing_files.values())

        print(f"\n📥 需要下载 {len(to_download)} 个新文件")

        # 下载每个新的.mp4文件
        for i, material in enumerate(to_download, 1):
            file_url = material.get('url')
            path = material.get('path', '')
            name = material.get('name', '')

            if not file_url:
                print(f"⚠️ 素材 {i} 没有有效的URL")
                continue

            # 🔥 修改：优先使用原始路径作为文件名
            if path:
                # 从path中提取文件名
                original_filename = os.path.basename(path)
                # 确保是.mp4格式
                if not original_filename.endswith('.mp4'):
                    original_filename += '.mp4'
                file_name = original_filename
                print(f"📄 使用原始路径文件名: {original_filename}")
            else:
                # 如果没有path，使用name或默认名称
                file_name = name if name else f"video_{material.get('id', i)}.mp4"
                if not file_name.endswith('.mp4'):
                    file_name += '.mp4'
                print(f"📝 使用名称: {file_name}")

            # 🔥 修改：保留更多字符，减少文件名冲突
            # 只移除真正的非法字符，保留中文、数字、字母、常用符号
            illegal_chars = '<>:"/\\|?*'
            safe_filename = "".join(c for c in file_name if c not in illegal_chars)

            # 如果文件名过长，截断但保留扩展名
            if len(safe_filename) > 200:  # Windows文件名限制
                name_part = safe_filename[:-4]  # 去掉.mp4
                safe_filename = name_part[:196] + '.mp4'  # 保留.mp4

            # 构建完整的文件路径
            file_path = os.path.join(download_path, safe_filename)

            # 🔥 如果文件已存在，添加数字后缀避免覆盖
            if os.path.exists(file_path):
                name_without_ext = safe_filename[:-4]  # 去掉.mp4
                counter = 1
                while os.path.exists(file_path):
                    new_filename = f"{name_without_ext}_{counter}.mp4"
                    file_path = os.path.join(download_path, new_filename)
                    counter += 1
                safe_filename = os.path.basename(file_path)
                print(f"🔄 文件已存在，重命名为: {safe_filename}")

            print(f"\n🎬 [{i}/{len(to_download)}] 下载: {safe_filename}")
            print(f"🔗 URL: {file_url}")
            print(f"📄 原始路径: {path}")
            print(f"📝 原始名称: {name}")

            # 下载文件（使用相同的请求头）
            if download_file_with_progress(file_url, file_path, headers):
                downloaded_files.append(file_path)
                print(f"💾 保存位置: {file_path}")
            else:
                print(f"❌ 下载失败: {safe_filename}")

        # 合并已存在的文件到返回列表
        all_files = downloaded_files + list(existing_files.values())

    except requests.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")

    print(f"\n📊 下载总结:")
    print(f"✅ 新下载文件: {len(downloaded_files)} 个")
    print(f"📁 已存在文件: {len(existing_files)} 个")
    print(f"🎯 总可用文件: {len(all_files)} 个")
    print(f"📂 保存目录: {download_path}")

    return all_files


def download_materials_by_tags(tags_list):
    """
    按多个标签批量下载素材

    Args:
        tags_list (list): 标签列表

    Returns:
        dict: 每个标签对应的下载文件列表
    """
    all_downloads = {}

    for tag in tags_list:
        print(f"\n🏷️ 开始下载标签 '{tag}' 的素材...")
        downloaded = download_materials_from_api(tag)
        all_downloads[tag] = downloaded
        print(f"🏷️ 标签 '{tag}' 下载完成，共 {len(downloaded)} 个文件\n")

    return all_downloads


# 使用示例
if __name__ == "__main__":
    # 方式1: 使用默认请求头下载素材
    downloaded_files = download_materials_from_api("")

    # 方式2: 使用自定义请求头
    custom_headers = {
        'Authorization': 'Bearer your_custom_token',
        'tenant-id': '2',
        'User-Agent': 'MyApp/1.0'
    }
    # downloaded_files = download_materials_from_api("装修行业", custom_headers)

    # 方式3: 下载多个标签的素材
    # tags = ["装修行业", "美食", "旅游"]
    # all_downloads = download_materials_by_tags(tags)

    # 输出下载的文件列表
    print("\n📋 下载的文件列表:")
    for file_path in downloaded_files:
        print(f"  - {file_path}")
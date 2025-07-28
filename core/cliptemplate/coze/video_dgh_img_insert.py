"""
This example describes how to use the workflow interface to chat.
Enhanced version with better error handling, retry mechanism, and URL support.
"""
import os
import json
import time
import logging
import requests
import tempfile
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL
from doubaoconfigs import coze_api_token

# Get an access_token through personal access token or oauth.
coze_api_token = coze_api_token
# The default access is api.coze.com, but if you need to access api.coze.cn,
# please use base_url to configure the api endpoint to access
coze_api_base = COZE_CN_BASE_URL

from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

from core.cliptemplate.coze.transform.coze_video_dgh_img_insert import trans_dgh_img_insert

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置常量
CONFIG = {
    "download_timeout": 60,  # 下载超时时间
    "request_timeout": 180,  # 数字人生成请求超时时间
    "max_retries": 2,  # 最大重试次数
    "backoff_factor": 3.0,  # 重试等待倍数
    "chunk_size": 8192,  # 下载块大小
    "temp_dir": None,  # 临时目录，None表示使用系统默认
    "fallback_enabled": True,  # 启用回退机制
}


def is_url(path: str) -> bool:
    """
    判断是否为URL

    Args:
        path: 文件路径或URL

    Returns:
        bool: 是否为URL
    """
    return path.strip().startswith(('http://', 'https://'))


def download_video_from_url(url: str, temp_dir: Optional[str] = None) -> str:
    """
    从URL下载视频文件到临时目录

    Args:
        url: 视频文件URL
        temp_dir: 临时目录路径，None表示使用系统默认

    Returns:
        str: 下载后的本地文件路径

    Raises:
        Exception: 下载失败时抛出异常
    """
    try:
        logger.info(f"📥 开始下载视频: {url}")
        print(f"📥 开始下载视频: {url}")

        # 发送HTTP请求下载文件
        response = requests.get(
            url.strip(),
            stream=True,
            timeout=CONFIG["download_timeout"]
        )
        response.raise_for_status()

        # 从URL获取文件扩展名
        parsed_url = urlparse(url)
        path = parsed_url.path
        if '.' in path:
            ext = os.path.splitext(path)[1]
            # 如果扩展名包含查询参数，只取扩展名部分
            if '?' in ext:
                ext = ext.split('?')[0]
        else:
            ext = '.mp4'  # 默认扩展名

        # 创建临时文件
        if temp_dir is None:
            temp_dir = CONFIG["temp_dir"] or tempfile.gettempdir()

        temp_file = tempfile.NamedTemporaryFile(
            dir=temp_dir,
            suffix=ext,
            delete=False
        )

        # 写入文件内容
        total_size = 0
        for chunk in response.iter_content(chunk_size=CONFIG["chunk_size"]):
            if chunk:
                temp_file.write(chunk)
                total_size += len(chunk)

        temp_file.close()

        size_mb = total_size / 1024 / 1024
        success_msg = f"✅ 视频下载完成: {temp_file.name} ({size_mb:.2f}MB)"
        logger.info(success_msg)
        print(success_msg)

        return temp_file.name

    except requests.exceptions.Timeout as e:
        error_msg = f"下载超时: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"网络请求失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    except Exception as e:
        error_msg = f"下载处理失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


def make_request_with_retry(url: str, data: Dict[str, Any],
                            max_retries: Optional[int] = None,
                            timeout: Optional[int] = None,
                            backoff_factor: Optional[float] = None) -> Dict[str, Any]:
    """
    带重试机制的HTTP请求

    Args:
        url: 请求URL
        data: 请求数据
        max_retries: 最大重试次数
        timeout: 请求超时时间（秒）
        backoff_factor: 退避因子

    Returns:
        响应数据字典

    Raises:
        Exception: 请求失败时抛出异常
    """

    # 使用配置中的默认值
    max_retries = max_retries or CONFIG["max_retries"]
    timeout = timeout or CONFIG["request_timeout"]
    backoff_factor = backoff_factor or CONFIG["backoff_factor"]

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            attempt_msg = f"🔄 尝试请求 (第{attempt + 1}次/{max_retries + 1}次)..."
            logger.info(attempt_msg)
            print(attempt_msg)

            response = requests.post(
                url,
                json=data,
                timeout=timeout,
                headers={'Content-Type': 'application/json'}
            )

            status_msg = f"📊 状态码: {response.status_code}"
            logger.info(status_msg)
            print(status_msg)

            # 检查状态码
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info("✅ 请求成功")
                    print("✅ 请求成功")
                    return result
                except json.JSONDecodeError as e:
                    error_msg = f"JSON解析失败: {e}, 响应内容: {response.text[:200]}..."
                    logger.error(error_msg)
                    print(f"❌ {error_msg}")
                    raise Exception(f"服务返回无效JSON: {e}")

            elif response.status_code == 504:
                error_msg = f"服务器超时 (504)"
                logger.warning(error_msg)
                print(f"⏰ {error_msg}")
                last_exception = Exception("服务器超时")

            elif response.status_code >= 500:
                error_msg = f"服务器错误 ({response.status_code}): {response.text[:200]}"
                logger.error(error_msg)
                print(f"🔥 {error_msg}")
                last_exception = Exception(f"服务器错误 {response.status_code}")

            else:
                # 其他HTTP错误，不重试
                error_msg = f"HTTP错误 {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except requests.exceptions.Timeout:
            error_msg = "请求超时"
            logger.warning(error_msg)
            print(f"⏰ {error_msg}")
            last_exception = Exception("请求超时")

        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接错误: {e}"
            logger.warning(error_msg)
            print(f"🔌 {error_msg}")
            last_exception = Exception(f"连接失败: {e}")

        except Exception as e:
            logger.error(f"其他错误: {e}")
            print(f"❌ 其他错误: {e}")
            raise

        # 如果不是最后一次尝试，等待后重试
        if attempt < max_retries:
            wait_time = backoff_factor ** attempt
            wait_msg = f"⏳ 等待 {wait_time:.1f} 秒后重试..."
            logger.info(wait_msg)
            print(wait_msg)
            time.sleep(wait_time)

    # 所有重试都失败了
    final_error = last_exception or Exception("所有重试都已失败")
    logger.error(f"所有重试都失败: {final_error}")
    raise final_error


def check_service_health(service_url: str) -> bool:
    """
    检查服务是否正常

    Args:
        service_url: 服务基础URL

    Returns:
        bool: 服务是否正常
    """
    try:
        health_url = f"{service_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"服务健康检查失败: {e}")
        return False


def get_video_dgh_img_insert(title: str, video_file_path: str,
                             content: Optional[str] = None,
                             need_change: bool = False,
                             add_subtitle: bool = True,
                             insert_image: bool = True,
                             audio_url: Optional[str] = None) -> str:
    """
    修正版的视频处理函数

    关键逻辑：
    - audio_url有值: 使用提供的音频文件替换视频音频
    - audio_url无值: 保留原视频音频（使用video_file_path中的音频）
    """

    logger.info(f"🎬 开始处理视频: title='{title}', path='{video_file_path}'")
    print(f"🎬 开始处理视频: title='{title}'")
    print(f"🎵 audio_url={audio_url}")
    print(f"🔄 need_change={need_change}")
    
    # 🔥 处理内容改写逻辑
    final_content = content if content else title
    if need_change and content:
        print(f"🤖 开始AI改写内容...")
        try:
            # 直接调用qwen-max API进行改写
            from get_api_key import get_api_key_from_file
            
            api_key = get_api_key_from_file()
            
            # 构建改写提示
            rewrite_prompt = f"""
请你作为一个专业的内容创作者，对以下内容进行改写优化：

原内容：{content}

改写要求：
1. 保持原意不变，但让语言更加生动有趣
2. 增加一些吸引力和感染力
3. 保持内容的专业性和准确性
4. 长度与原文相当
5. 适合做视频配音文本

请直接返回改写后的内容，不要添加其他说明。
"""
            
            # 调用阿里云百炼API
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": rewrite_prompt
                        }
                    ]
                },
                "parameters": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("output") and result["output"].get("text"):
                    rewritten_content = result["output"]["text"]
                    if rewritten_content.strip():
                        final_content = rewritten_content.strip()
                        print(f"✅ 内容改写完成")
                        print(f"🔤 原内容长度: {len(content)} 字符")
                        print(f"🔤 改写后长度: {len(final_content)} 字符")
                    else:
                        print(f"⚠️ AI改写返回空内容，使用原内容")
                else:
                    print(f"⚠️ AI响应格式异常，使用原内容")
            else:
                print(f"❌ AI API调用失败 (状态码: {response.status_code})，使用原内容")
                
        except Exception as e:
            print(f"❌ AI改写失败，使用原内容: {str(e)}")
            logger.warning(f"AI改写失败: {str(e)}")
    elif need_change:
        print(f"⚠️ need_change=True 但 content 为空，跳过改写")
    
    # 🔥 简化的音频处理策略
    if audio_url:
        print(f"🎵 策略：使用提供的音频文件 {audio_url}")
        audio_strategy = "use_provided_audio"
    else:
        print(f"🎵 策略：保留原视频音频")
        audio_strategy = "keep_original_audio"

    # 🔥 根据音频策略决定处理方式
    if audio_strategy == "use_provided_audio":
        # 使用提供的音频URL作为声音克隆参考
        print(f"🎵 使用提供的音频URL作为声音克隆参考")
        response = {
            'text': [final_content],
            'audio_text': final_content,  # 🔥 关键：语音合成的文本
            'title': title,
            'voice_reference_url': audio_url  # 🔥 标记为声音克隆参考
        }
    elif audio_strategy == "keep_original_audio":
        # 保留原视频音频，不需要调用工作流
        print(f"🎵 保留原视频音频，跳过语音合成")
        response = {
            'text': [final_content],  # 🔥 使用处理后的内容作为字幕文本
            'title': title,
            'keep_original_audio': True  # 标记保留原音频
        }
    # 注：现在支持两种模式：
    # 1. 使用提供的audio_url作为声音克隆参考，生成新语音
    # 2. 保留原视频音频

    temp_file_path = None
    absolute_video_path = None

    try:
        # 处理视频文件路径（保持原有逻辑）
        if is_url(video_file_path):
            logger.info("🌐 检测到网络URL，开始下载...")
            absolute_video_path = download_video_from_url(video_file_path)
            temp_file_path = absolute_video_path
        else:
            if video_file_path.startswith('projects/'):
                try:
                    from live_config import get_user_data_dir
                    absolute_video_path = os.path.join(get_user_data_dir(), video_file_path)
                except ImportError:
                    absolute_video_path = video_file_path
            else:
                absolute_video_path = video_file_path

            if not os.path.exists(absolute_video_path):
                raise FileNotFoundError(f"❌ 视频文件不存在: {absolute_video_path}")

        print(f"✅ 视频文件准备完成: {absolute_video_path}")

        # 🔥 调用修正版的处理函数
        try:
            logger.info("开始调用视频处理函数")
            print(f"🎵 传递给trans_dgh_img_insert的音频策略: {audio_strategy}")
            result_path = trans_dgh_img_insert(
                response,
                absolute_video_path,
                custom_headers=None,
                audio_strategy=audio_strategy,  # 🔥 使用动态确定的音频策略
                add_subtitle=add_subtitle,
                insert_image=insert_image
            )

            logger.info(f"视频处理成功: {result_path}")
            print(f"🎉 视频处理成功: {result_path}")
            return result_path

        except Exception as process_error:
            error_msg = f"视频处理失败: {str(process_error)}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            raise process_error

    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"🗑️ 已清理临时文件: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ 清理临时文件失败: {str(cleanup_error)}")


def get_video_dgh_img_insert_legacy(title: str, video_file_path: str,
                                    content: Optional[str] = None,
                                    need_change: bool = False) -> str:
    """
    兼容性包装函数，保持原有接口
    如果你的其他代码还在使用这个函数名，可以通过这个函数调用

    Args:
        title: 视频标题
        video_file_path: 视频文件路径或URL
        content: 视频内容描述
        need_change: 是否需要修改

    Returns:
        str: 处理后的视频文件路径
    """
    return get_video_dgh_img_insert(title, video_file_path, content, need_change)


def update_config(**kwargs) -> Dict[str, Any]:
    """
    更新配置参数

    Args:
        **kwargs: 要更新的配置项

    Returns:
        Dict[str, Any]: 更新后的配置
    """
    global CONFIG

    for key, value in kwargs.items():
        if key in CONFIG:
            old_value = CONFIG[key]
            CONFIG[key] = value
            logger.info(f"配置更新: {key} = {value} (原值: {old_value})")
            print(f"⚙️ 配置更新: {key} = {value}")
        else:
            logger.warning(f"未知配置项: {key}")
            print(f"⚠️ 未知配置项: {key}")

    return CONFIG.copy()


def get_config() -> Dict[str, Any]:
    """
    获取当前配置

    Returns:
        Dict[str, Any]: 当前配置的副本
    """
    return CONFIG.copy()


if __name__ == "__main__":
    # 配置日志级别
    logging.getLogger().setLevel(logging.INFO)

    print("🎬 视频处理系统启动")
    print(f"📋 当前配置: {json.dumps(CONFIG, indent=2)}")

    # 测试本地文件
    # filepath = "2日.mp4"
    # try:
    #     result = get_video_dgh_img_insert("财税", filepath)
    #     print(f"🎉 本地文件处理成功，结果: {result}")
    # except Exception as e:
    #     print(f"❌ 本地文件测试失败: {str(e)}")

    # 测试网络URL
    test_url = "https://files.cstlanbaai.com/robot/files/2df02dca2ca27e2bc8b319dad3faafc06191fdd416b17b36cfba6546181093fc.mp4"
    try:
        print("\n🌐 开始测试网络URL...")
        result = get_video_dgh_img_insert("财税", test_url)
        print(f"🎉 网络URL处理成功，结果: {result}")
    except Exception as e:
        print(f"❌ 网络URL测试失败: {str(e)}")

    # 性能测试示例
    # print("\n📊 性能测试...")
    # start_time = time.time()
    # try:
    #     # 这里可以添加性能测试代码
    #     pass
    # finally:
    #     end_time = time.time()
    #     print(f"⏱️ 测试耗时: {end_time - start_time:.2f}秒")

    # 批量测试示例（注释掉的原代码保留）
    # for i in range(10):
    #     get_video_advertisement("常熟优帮财税","全过程代理记账 财务合规 企业内控 重大税务筹划","财税",'''...''',True)
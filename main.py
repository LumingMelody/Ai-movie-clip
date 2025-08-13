# -*- coding: utf-8 -*-
# @Time    : 2025/6/10 09:57
# @Author  : 蔍鸣霸霸
# @FileName: main.py
# @Software: PyCharm
# @Blog    ：只因你太美

# main.py - AI视频自动剪辑系统主入口（完整版 + 日志记录）
import os
import sys
import argparse
import json
import re
import tempfile
import urllib.parse
import shutil
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量配置: {env_path}")

from core.orchestrator.workflow_orchestrator import VideoEditingOrchestrator

# 尝试导入可选依赖
try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import yt_dlp

    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


class LoggerSetup:
    """日志记录设置类"""

    @staticmethod
    def setup_logger(log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
        """
        设置日志记录器
        :param log_file: 日志文件路径，如果为None则自动生成
        :param console_level: 控制台日志级别
        :param file_level: 文件日志级别
        :return: logger对象和日志文件路径
        """
        # 创建日志器
        logger = logging.getLogger('ai_video_editor')
        logger.setLevel(logging.DEBUG)

        # 清除已有的处理器
        logger.handlers.clear()

        # 如果没有指定日志文件，自动生成
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/ai_video_edit_{timestamp}.log"

        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # 只创建文件处理器（不创建控制台处理器，避免重复输出）
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)

        # 创建格式器
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 设置格式器
        file_handler.setFormatter(file_formatter)

        # 添加处理器
        logger.addHandler(file_handler)

        return logger, log_file


class LogCapture:
    """日志捕获类 - 用于捕获print输出并记录到日志"""

    def __init__(self, logger):
        self.logger = logger
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, message):
        # 输出到控制台
        self.original_stdout.write(message)

        # 记录到日志文件（只记录非空行）
        if message.strip():
            self.logger.info(message.strip())

    def flush(self):
        self.original_stdout.flush()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout


def get_api_key_from_file(file_name="api_key.txt"):
    """
    从环境变量读取 API Key（向后兼容函数）
    忽略file_name参数，从环境变量获取
    
    :param file_name: 忽略此参数，仅为向后兼容
    :return: API Key 字符串或 None（读取失败时）
    """
    from core.utils.env_config import get_dashscope_api_key
    api_key = get_dashscope_api_key()
    if not api_key:
        print("⚠️ 未找到DASHSCOPE_API_KEY环境变量")
        print("请在.env文件中配置: DASHSCOPE_API_KEY=your_api_key")
    return api_key


def is_url(string: str) -> bool:
    """检查字符串是否为有效的URL"""
    try:
        result = urllib.parse.urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_video_url(url: str) -> bool:
    """检查URL是否指向视频文件"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m3u8')

    # 检查直接视频链接
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in video_extensions):
        return True

    # 检查常见视频平台
    video_platforms = [
        'youtube.com', 'youtu.be',
        'bilibili.com', 'b23.tv',
        'douyin.com', 'tiktok.com',
        'weibo.com', 'xiaohongshu.com'
    ]

    domain = parsed.netloc.lower()
    return any(platform in domain for platform in video_platforms)


def download_direct_video(url: str, output_dir: str) -> str:
    """下载直接视频链接"""
    if not REQUESTS_AVAILABLE:
        raise Exception("需要安装 requests: pip install requests")

    try:
        print(f"🌐 正在下载视频: {url}")

        # 获取文件名
        parsed_url = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = "downloaded_video.mp4"

        output_path = os.path.join(output_dir, filename)

        # 下载文件
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # 显示进度
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r  📥 下载进度: {progress:.1f}%", end='')

        print(f"\n  ✅ 下载完成: {output_path}")
        return output_path

    except Exception as e:
        raise Exception(f"直接下载失败: {str(e)}")


def download_platform_video(url: str, output_dir: str) -> str:
    """使用 yt-dlp 下载平台视频"""
    if not YT_DLP_AVAILABLE:
        raise Exception("需要安装 yt-dlp: pip install yt-dlp")

    try:
        print(f"🌐 正在从平台下载视频: {url}")

        # 配置 yt-dlp
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'format': 'worst[height<=720]/worst',  # 选择较低质量避免权限问题
            'noplaylist': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频信息
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'downloaded_video')
            ext = info.get('ext', 'mp4')

            # 清理文件名中的非法字符
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]

            # 更新配置
            ydl_opts['outtmpl'] = os.path.join(output_dir, f'{safe_title}.%(ext)s')

            # 下载视频
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                ydl_download.download([url])

            # 找到下载的文件
            for file in os.listdir(output_dir):
                if file.endswith(('.mp4', '.webm', '.mkv')):
                    full_path = os.path.join(output_dir, file)
                    print(f"  ✅ 下载完成: {full_path}")
                    return full_path

            raise FileNotFoundError("下载的视频文件未找到")

    except Exception as e:
        raise Exception(f"平台下载失败: {str(e)}")


def download_video_from_url(url: str, output_dir: str = None) -> str:
    """从URL下载视频"""
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ai_video_")

    try:
        # 方法1: 直接下载视频文件
        if url.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')):
            return download_direct_video(url, output_dir)

        # 方法2: 使用 yt-dlp 下载平台视频
        elif any(platform in url.lower() for platform in ['youtube', 'bilibili', 'douyin', 'tiktok']):
            return download_platform_video(url, output_dir)

        else:
            raise ValueError(f"不支持的视频URL类型: {url}")

    except Exception as e:
        raise Exception(f"下载视频失败: {str(e)}")


def collect_video_files(paths: List[str]) -> tuple[List[str], List[str]]:
    """收集所有视频文件 - 支持本地文件和URL"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
    video_files = []
    temp_dirs = []  # 用于清理临时下载目录

    for path in paths:
        try:
            if is_url(path):
                # 处理URL
                if is_video_url(path):
                    print(f"🌐 检测到视频URL: {path}")

                    # 检查必要依赖
                    if not YT_DLP_AVAILABLE and not REQUESTS_AVAILABLE:
                        print("⚠️ 缺少下载依赖，跳过在线视频下载")
                        print("💡 安装命令: pip install requests yt-dlp")
                        continue

                    try:
                        # 创建临时目录
                        temp_dir = tempfile.mkdtemp(prefix="ai_video_download_")
                        temp_dirs.append(temp_dir)

                        # 下载视频
                        downloaded_path = download_video_from_url(path, temp_dir)
                        video_files.append(downloaded_path)

                    except Exception as e:
                        print(f"⚠️ 跳过无法下载的URL: {path}")
                        print(f"   原因: {str(e)}")
                        # 清理失败的临时目录
                        if temp_dirs and os.path.exists(temp_dirs[-1]):
                            shutil.rmtree(temp_dirs[-1])
                            temp_dirs.pop()
                else:
                    print(f"⚠️ 不支持的URL类型: {path}")

            elif os.path.isfile(path):
                # 处理本地文件
                if path.lower().endswith(video_extensions):
                    video_files.append(path)
                    print(f"✅ 本地视频文件: {os.path.basename(path)}")
                else:
                    print(f"⚠️ 跳过非视频文件: {path}")

            elif os.path.isdir(path):
                # 处理本地目录
                found_in_dir = 0
                for file in os.listdir(path):
                    if file.lower().endswith(video_extensions):
                        video_files.append(os.path.join(path, file))
                        found_in_dir += 1
                print(f"✅ 目录中找到 {found_in_dir} 个视频文件: {path}")

            else:
                print(f"⚠️ 路径不存在: {path}")

        except Exception as e:
            print(f"❌ 处理 {path} 时出错: {str(e)}")

    return video_files, temp_dirs


def cleanup_temp_dirs(temp_dirs: List[str]):
    """清理临时下载目录"""
    for temp_dir in temp_dirs:
        try:
            shutil.rmtree(temp_dir)
            print(f"🗑️ 已清理临时目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️ 清理临时目录失败: {str(e)}")


def handle_analyze_command_enhanced(args, logger=None):
    """增强的分析命令 - 自动保存结果"""
    print("🔍 开始视频分析...")

    # 收集视频文件
    video_files, temp_dirs = collect_video_files(args.videos)

    if not video_files:
        print("❌ 没有找到有效的视频文件")
        suggest_alternative_sources()
        return

    try:
        from analyzer.video_analyzer import VideoAnalyzer
        analyzer = VideoAnalyzer()
    except ImportError as e:
        print(f"❌ 无法导入视频分析器: {e}")
        print("💡 请检查 analyzer.video_analyzer 模块是否存在")
        return

    results = []

    try:
        for i, video_path in enumerate(video_files, 1):
            print(f"\n📹 分析视频 {i}/{len(video_files)}: {os.path.basename(video_path)}")

            try:
                result = analyzer.analyze_video(video_path)
                result['file_path'] = video_path
                results.append(result)

                if args.verbose:
                    print_analysis_summary(result)

            except Exception as e:
                print(f"❌ 分析失败: {str(e)}")
                results.append({
                    'file_path': video_path,
                    'error': str(e),
                    'status': 'failed'
                })

        # 输出结果
        if args.output:
            save_analysis_to_file(results, args.output)
        else:
            # 如果没有指定输出文件，自动创建一个
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            auto_filename = f"analysis_results_{timestamp}.json"
            save_analysis_to_file(results, auto_filename)

        print_final_analysis_summary(results)

    finally:
        # 清理临时下载文件
        cleanup_temp_dirs(temp_dirs)


def handle_edit_command_enhanced(args, logger=None):
    """增强的剪辑命令 - 可以使用现有分析结果"""
    print("🎬 开始AI视频剪辑...")

    # 收集视频文件
    video_files, temp_dirs = collect_video_files(args.videos)

    if not video_files:
        print("❌ 没有找到有效的视频文件")
        return

    try:
        # 获取API密钥
        api_key = None
        if not args.local_ai:
            api_key = get_api_key_from_file(args.api_key_file)
            if not api_key:
                print("⚠️ 无法读取API密钥，将使用本地AI模式")
                args.local_ai = True

        # 准备用户选项
        user_options = {
            "target_duration": args.duration,
            "target_style": args.style,
            "target_purpose": args.purpose
        }

        # 检查是否有现有的分析结果文件
        analysis_results = None
        if hasattr(args, 'analysis_file') and args.analysis_file:
            try:
                with open(args.analysis_file, 'r', encoding='utf-8') as f:
                    analysis_results = json.load(f)
                print(f"✅ 使用现有分析结果: {args.analysis_file}")
            except Exception as e:
                print(f"⚠️ 无法读取分析文件: {e}")
                print("将重新分析视频...")

        # 使用增强的工作流程
        orchestrator = VideoEditingOrchestrator(
            video_files,
            args.output,
            analysis_results=analysis_results
        )

        result = orchestrator.run_complete_workflow(
            user_options=user_options,
            api_key=api_key,
            use_local_ai=args.local_ai,
            merge_videos=args.merge
        )

        print_edit_result(result)

    finally:
        # 清理临时下载文件
        cleanup_temp_dirs(temp_dirs)


def save_analysis_to_file(results: List[Dict[str, Any]], output_file: str):
    """保存分析结果到文件（增强版）"""
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📄 分析结果已保存到: {output_file}")
        print(f"💡 可以使用此文件进行剪辑: python main.py edit-from-analysis --analysis-file {output_file}")

    except Exception as e:
        print(f"❌ 保存结果失败: {str(e)}")


def print_analysis_summary(result: Dict[str, Any]):
    """打印分析摘要"""
    metadata = result.get('metadata', {})
    highlights = result.get('highlights', [])

    print(f"  📊 时长: {metadata.get('duration', 0):.1f}秒")
    print(f"  📺 分辨率: {metadata.get('width', 0)}x{metadata.get('height', 0)}")
    print(f"  🎵 音频: {'✅' if metadata.get('has_audio') else '❌'}")
    print(f"  ⭐ 精彩片段: {len(highlights)}个")


def print_final_analysis_summary(results: List[Dict[str, Any]]):
    """打印最终分析摘要"""
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]

    print(f"\n📊 分析完成:")
    print(f"  ✅ 成功: {len(successful)}个")
    print(f"  ❌ 失败: {len(failed)}个")

    if successful:
        total_duration = sum(r.get('metadata', {}).get('duration', 0) for r in successful)
        print(f"  ⏱️ 总时长: {total_duration:.1f}秒")


def print_edit_result(result: Dict[str, Any]):
    """打印剪辑结果"""
    if result['status'] == 'success':
        print(f"\n🎉 剪辑完成!")
        print(f"📄 输出文件: {result['output_video']}")
        print(f"📊 文件大小: {result['file_size_mb']}MB")
        print(f"⏱️ 处理时间: {result['processing_time']}秒")

        video_info = result.get('video_info', {})
        print(f"📹 输入文件数: {video_info.get('input_count', 1)}")
    else:
        print(f"❌ 剪辑失败: {result.get('error', '未知错误')}")


def suggest_alternative_sources():
    """建议替代视频源"""
    print("\n💡 推荐的测试视频源:")
    print("1. 直接视频链接示例:")
    print("   https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4")
    print("\n2. 本地视频文件:")
    print("   - 下载任意 .mp4 文件到本地")
    print("   - 使用手机录制的视频")
    print("\n3. 无版权视频网站:")
    print("   - Pexels Videos")
    print("   - Pixabay Videos")
    print("   - Unsplash Videos")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI视频自动剪辑系统 - 支持分析结果复用和在线视频下载",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 1. 分析视频并保存结果
  python main.py analyze video.mp4 --output analysis.json

  # 2. 使用分析结果进行剪辑（推荐，避免重复分析）
  python main.py edit-from-analysis --analysis-file analysis.json --duration 30

  # 3. 直接剪辑（会自动分析）
  python main.py edit video.mp4 --duration 30

  # 4. 使用已有分析结果剪辑
  python main.py edit video.mp4 --analysis-file analysis.json --duration 30

  # 5. 分析在线视频
  python main.py analyze "https://www.youtube.com/watch?v=xxxxx"

  # 6. 剪辑在线视频
  python main.py edit "https://youtube.com/watch?v=xxx" --duration 60

  # 7. 测试完整工作流程
  python main.py test-workflow --video test.mp4

注意：
  - 在线视频下载需要安装: pip install requests yt-dlp
  - 某些平台可能需要代理或特殊配置
  - 使用分析结果文件可以避免重复分析，大大提高效率
  - 日志文件会自动保存在 logs/ 目录下
        """
    )

    # 添加全局日志参数
    parser.add_argument('--log-file', help='指定日志文件路径')
    parser.add_argument('--verbose-log', action='store_true', help='详细日志模式')
    parser.add_argument('--no-log', action='store_true', help='禁用日志文件记录')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 分析命令（增强版，自动保存结果）
    analyze_parser = subparsers.add_parser('analyze', help='分析视频内容并保存结果')
    analyze_parser.add_argument('videos', nargs='+', help='视频文件路径、目录或URL')
    analyze_parser.add_argument('--output', '-o', help='分析结果输出文件(JSON格式)')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    # 剪辑命令（增强版，支持使用分析结果）
    edit_parser = subparsers.add_parser('edit', help='AI视频剪辑（可使用现有分析结果）')
    edit_parser.add_argument('videos', nargs='+', help='视频文件路径、目录或URL')
    edit_parser.add_argument('--duration', '-d', type=int, default=30, help='目标时长(秒)')
    edit_parser.add_argument('--style', '-s', default='抖音风', help='目标风格')
    edit_parser.add_argument('--purpose', '-p', default='社交媒体', help='使用目的')
    edit_parser.add_argument('--output', '-o', help='输出目录')
    edit_parser.add_argument('--analysis-file', help='使用现有的分析结果文件')
    edit_parser.add_argument('--api-key-file', default='api_key.txt', help='API密钥文件路径')
    edit_parser.add_argument('--local-ai', action='store_true', help='使用本地AI模型')
    edit_parser.add_argument('--batch', action='store_true', help='批量处理模式')
    edit_parser.add_argument('--merge', action='store_true', default=True, help='合并多个视频后剪辑')
    edit_parser.add_argument('--no-merge', dest='merge', action='store_false', help='分别剪辑后合并')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 设置日志记录
    logger = None
    log_file_path = None

    if not args.no_log:
        try:
            log_level = logging.DEBUG if args.verbose_log else logging.INFO
            logger, log_file_path = LoggerSetup.setup_logger(
                log_file=args.log_file,
                console_level=log_level,
                file_level=logging.DEBUG
            )

            # 使用日志捕获器来同时记录到文件和控制台
            with LogCapture(logger):
                print(f"📝 日志记录已启用，文件路径: {log_file_path}")
                print(f"🚀 开始执行命令: {args.command}")
                print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # 记录命令参数
                print(f"📋 命令参数: {' '.join(sys.argv[1:])}")

                execute_command(args, logger)

        except Exception as e:
            print(f"❌ 日志设置失败: {str(e)}")
            print("继续执行命令（不记录日志）...")
            execute_command(args, None)
    else:
        execute_command(args, None)


def execute_command(args, logger):
    """执行具体命令"""
    try:
        if args.command == 'analyze':
            handle_analyze_command_enhanced(args, logger)
        elif args.command == 'edit':
            handle_edit_command_enhanced(args, logger)
        # 可以继续添加其他命令处理...
        else:
            print(f"❌ 未知命令: {args.command}")

        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if logger:
            print(f"📝 详细日志已保存")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
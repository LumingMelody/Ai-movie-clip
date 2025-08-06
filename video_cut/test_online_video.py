#!/usr/bin/env python
"""
在线视频测试脚本
支持使用URL视频进行自然语言剪辑测试
"""
import os
import sys
import json
import tempfile
import urllib.request
from pathlib import Path
import click
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from video_cut.unified_nl_processor import UnifiedNLProcessor
from video_cut.timeline_generator import TimelineGenerator
from video_cut.video_editor import VideoEditor
from video_cut.utils.resource_manager import ResourceManager


def download_video(url: str, output_dir: str = "temp") -> str:
    """
    下载在线视频到本地
    
    Args:
        url: 视频URL
        output_dir: 下载目录
    
    Returns:
        本地文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 从URL中提取文件名
    filename = url.split('/')[-1].split('?')[0]
    if not filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    local_path = os.path.join(output_dir, filename)
    
    # 如果文件已存在，直接使用
    if os.path.exists(local_path):
        print(f"✅ 使用缓存的视频: {local_path}")
        return local_path
    
    print(f"⬇️  下载视频: {url}")
    print(f"   保存到: {local_path}")
    
    try:
        # 使用urllib下载
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            with open(local_path, 'wb') as f:
                downloaded = 0
                block_size = 8192
                
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    # 显示进度
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print(f"\n✅ 下载完成!")
        return local_path
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        # 尝试使用系统命令下载
        try:
            import subprocess
            print("尝试使用wget下载...")
            subprocess.run(['wget', '-O', local_path, url], check=True)
            return local_path
        except:
            try:
                print("尝试使用curl下载...")
                subprocess.run(['curl', '-L', '-o', local_path, url], check=True)
                return local_path
            except:
                raise Exception(f"无法下载视频: {url}")


@click.command()
@click.option('--url', '-u', required=True, help='在线视频URL')
@click.option('--description', '-d', default=None, help='自然语言描述')
@click.option('--output', '-o', default=None, help='输出视频路径')
@click.option('--duration', '-t', type=int, default=30, help='剪辑时长（秒）')
@click.option('--download-only', is_flag=True, help='仅下载视频，不进行剪辑')
def test_online_video(url, description, output, duration, download_only):
    """测试在线视频剪辑"""
    
    click.echo(click.style("""
╔════════════════════════════════════════════╗
║     在线视频自然语言剪辑测试工具            ║
╚════════════════════════════════════════════╝
""", fg='bright_blue'))
    
    # 步骤1: 下载视频
    try:
        local_video = download_video(url)
    except Exception as e:
        click.echo(click.style(f"❌ 视频下载失败: {e}", fg='red'))
        return
    
    if download_only:
        click.echo(f"✅ 视频已下载到: {local_video}")
        return
    
    # 设置输出路径
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"output/online_test_{timestamp}.mp4"
    
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    # 默认描述
    if not description:
        test_descriptions = [
            f"制作一个{duration}秒的精彩片段，包含淡入淡出效果，配上动感音乐",
            f"创建{duration}秒的产品展示视频，要有转场效果和字幕",
            f"做一个{duration}秒的社交媒体短视频，快节奏剪辑",
            f"生成{duration}秒的vlog风格视频，轻松愉快的氛围"
        ]
        
        click.echo(click.style("\n选择一个测试场景:", fg='cyan'))
        for i, desc in enumerate(test_descriptions, 1):
            click.echo(f"  {i}. {desc}")
        
        choice = click.prompt("请选择 (1-4)", type=int, default=1)
        description = test_descriptions[choice - 1]
    
    click.echo(click.style(f"\n📝 处理描述: {description}", fg='cyan'))
    
    # 步骤2: 生成时间轴
    click.echo(click.style("\n🤖 生成时间轴...", fg='blue'))
    
    # 创建简单的时间轴
    timeline = create_simple_timeline_for_online(
        description=description,
        video_source=local_video,
        duration=duration
    )
    
    # 保存时间轴
    timeline_path = output.replace('.mp4', '_timeline.json')
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    click.echo(f"💾 时间轴已保存: {timeline_path}")
    
    # 步骤3: 执行视频剪辑
    click.echo(click.style("\n🎬 执行视频剪辑...", fg='blue'))
    
    editor = VideoEditor(enable_memory_optimization=False)
    
    try:
        success = editor.execute_timeline(timeline, output)
        
        if success:
            click.echo(click.style(f"\n✅ 视频剪辑完成！", fg='green'))
            click.echo(f"   输出文件: {output}")
            
            if os.path.exists(output):
                size_mb = os.path.getsize(output) / (1024*1024)
                click.echo(f"   文件大小: {size_mb:.2f} MB")
        else:
            click.echo(click.style("❌ 视频剪辑失败", fg='red'))
            
    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg='red'))
        import traceback
        traceback.print_exc()


def create_simple_timeline_for_online(description: str, video_source: str, duration: int = 30) -> dict:
    """为在线视频创建简单的测试时间轴"""
    
    # 检测描述中的关键词
    desc_lower = description.lower()
    
    # 根据描述添加不同的效果
    filters = []
    if "淡入" in description or "fade" in desc_lower:
        filters.append("fade_in")
    if "淡出" in description or "fade" in desc_lower:
        filters.append("fade_out")
    if "快节奏" in description or "快速" in description:
        filters.append("speed_up")
    
    # 文字内容
    text_clips = []
    if "字幕" in description or "文字" in description:
        text_clips.append({
            "start": 2,
            "end": 8,
            "content": {
                "text": "精彩片段",
                "font": "黑体",
                "size": 60,
                "color": "#FFFFFF",
                "position": "center"
            }
        })
        text_clips.append({
            "start": duration - 5,
            "end": duration - 1,
            "content": {
                "text": "感谢观看",
                "font": "黑体",
                "size": 48,
                "color": "#FFFFFF",
                "position": "bottom"
            }
        })
    
    timeline = {
        "version": "1.0",
        "metadata": {
            "title": "在线视频剪辑测试",
            "description": description,
            "created_at": datetime.now().isoformat(),
            "source_url": video_source
        },
        "timeline": {
            "duration": duration,
            "fps": 30,
            "resolution": {"width": 1920, "height": 1080},
            "background_color": "#000000",
            "tracks": [
                {
                    "type": "video",
                    "name": "主视频轨",
                    "clips": [
                        {
                            "start": 0,
                            "end": duration,
                            "source": video_source,  # 使用本地下载的路径
                            "clip_in": 0,
                            "clip_out": duration,
                            "filters": filters,
                            "transform": {
                                "scale": 1.0,
                                "position": [960, 540]
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    # 添加文字轨道
    if text_clips:
        timeline["timeline"]["tracks"].append({
            "type": "text",
            "name": "字幕轨",
            "clips": text_clips
        })
    
    # 如果需要背景音乐
    if "音乐" in description or "music" in desc_lower:
        timeline["timeline"]["tracks"].append({
            "type": "audio",
            "name": "背景音乐",
            "clips": [
                {
                    "start": 0,
                    "end": duration,
                    "content": {
                        "type": "generated",
                        "style": "upbeat" if "动感" in description else "calm"
                    },
                    "volume": 0.3
                }
            ]
        })
    
    return timeline


# 快速测试函数
def quick_test_online():
    """快速测试在线视频"""
    # 一些测试用的视频URL
    test_urls = [
        "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4",
        "https://www.w3schools.com/html/mov_bbb.mp4",
        # 添加你自己的视频URL
    ]
    
    print("快速测试模式 - 使用示例URL")
    print("可用的测试URL:")
    for i, url in enumerate(test_urls, 1):
        print(f"  {i}. {url[:50]}...")
    
    choice = input("选择 (1-{}): ".format(len(test_urls)))
    
    try:
        url = test_urls[int(choice) - 1]
        test_online_video(url, None, None, 30, False)
    except:
        print("无效选择")


if __name__ == "__main__":
    test_online_video()
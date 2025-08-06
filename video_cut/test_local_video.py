#!/usr/bin/env python
"""
本地视频测试脚本
用于测试自然语言视频剪辑系统的完整流程
"""
import os
import sys
import json
from pathlib import Path
import click
from datetime import datetime

from utils.resource_manager import ResourceManager

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from video_cut.unified_nl_processor import UnifiedNLProcessor
from video_cut.timeline_generator import TimelineGenerator
from video_cut.video_editor import VideoEditor



@click.command()
@click.option('--video', '-v', required=True, help='本地视频文件路径')
@click.option('--description', '-d', default=None, help='自然语言描述')
@click.option('--output', '-o', default=None, help='输出视频路径')
@click.option('--mode', '-m', type=click.Choice(['quick', 'timeline', 'full']), default='full', 
              help='测试模式: quick(快速测试), timeline(只生成时间轴), full(完整流程)')
def test_video(video, description, output, mode):
    """测试本地视频剪辑"""
    
    # 检查视频文件
    video_path = Path(video)
    if not video_path.exists():
        click.echo(click.style(f"❌ 视频文件不存在: {video}", fg='red'))
        return
    
    click.echo(click.style(f"📹 使用视频: {video_path.name}", fg='green'))
    click.echo(f"   文件大小: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    # 设置输出路径
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"output/test_{timestamp}.mp4"
    
    output_dir = Path(output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 默认描述
    if not description:
        test_descriptions = [
            "制作一个30秒的精彩片段，包含淡入淡出效果，配上动感音乐，添加字幕说明",
            "创建1分钟的产品展示视频，开头5秒展示logo，然后分3个部分介绍产品特点，每部分15秒，要有转场效果",
            "做一个45秒的社交媒体短视频，快节奏剪辑，添加文字动画和背景音乐",
            "生成2分钟的vlog风格视频，分为开场、主体内容和结尾，要有字幕和轻松的背景音乐"
        ]
        
        click.echo(click.style("\n选择一个测试场景:", fg='cyan'))
        for i, desc in enumerate(test_descriptions, 1):
            click.echo(f"  {i}. {desc[:50]}...")
        
        choice = click.prompt("请选择 (1-4)", type=int, default=1)
        description = test_descriptions[choice - 1]
    
    click.echo(click.style(f"\n📝 处理描述: {description}", fg='cyan'))
    
    # 初始化资源管理器
    resource_manager = ResourceManager()
    
    # 将视频添加到资源管理器
    click.echo("\n⚙️  初始化资源管理...")
    video_resource = resource_manager.add_resource(
        str(video_path), 
        resource_type="video",
        copy=True,
        name=f"input_{video_path.name}"
    )
    click.echo(f"   视频已添加到资源库: {video_resource}")
    
    # 获取视频信息
    video_info = resource_manager.get_resource_info(video_resource)
    if video_info:
        click.echo(f"   视频信息: {video_info.get('duration', 'N/A')}秒, "
                  f"{video_info.get('resolution', {}).get('width', 'N/A')}x"
                  f"{video_info.get('resolution', {}).get('height', 'N/A')}")
    
    if mode == 'quick':
        click.echo(click.style("\n🚀 快速测试模式", fg='yellow'))
        # 直接创建简单的时间轴
        timeline = create_simple_timeline(description, str(video_resource))
        
    else:
        # 步骤1: 自然语言处理
        click.echo(click.style("\n🤖 步骤1: 处理自然语言...", fg='blue'))
        nl_processor = UnifiedNLProcessor(use_ai=True, cache_enabled=True)
        
        try:
            timeline = nl_processor.process(description, mode="auto")
            click.echo(click.style("   ✅ 自然语言处理完成", fg='green'))
        except Exception as e:
            click.echo(click.style(f"   ⚠️  AI处理失败，使用本地处理: {e}", fg='yellow'))
            timeline = nl_processor.process(description, mode="local")
        
        # 添加视频源到时间轴
        add_video_source_to_timeline(timeline, str(video_resource))
        
        # 步骤2: 优化时间轴（可选）
        if mode == 'full':
            click.echo(click.style("\n🎨 步骤2: 优化时间轴...", fg='blue'))
            generator = TimelineGenerator()
            
            # 检测视频类型并选择模板
            template = detect_video_template(description)
            click.echo(f"   使用模板: {template}")
            
            config = {
                "title": "测试视频",
                "duration": timeline["timeline"]["duration"],
                "template": template,
                "resolution": timeline["timeline"]["resolution"],
                "fps": timeline["timeline"]["fps"]
            }
            
            timeline = generator.generate_advanced_timeline(config)
            timeline = generator.optimize_timeline(timeline)
            click.echo(click.style("   ✅ 时间轴优化完成", fg='green'))
    
    # 保存时间轴
    timeline_path = output.replace('.mp4', '_timeline.json')
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    click.echo(f"\n💾 时间轴已保存: {timeline_path}")
    
    # 显示时间轴摘要
    display_timeline_summary(timeline)
    
    if mode == 'timeline':
        click.echo(click.style("\n✅ 时间轴生成完成（仅生成时间轴模式）", fg='green'))
        return
    
    # 步骤3: 执行视频剪辑
    click.echo(click.style("\n🎬 步骤3: 执行视频剪辑...", fg='blue'))
    
    editor = VideoEditor(
        resource_dir=str(resource_manager.base_dir),
        enable_memory_optimization=True
    )
    
    try:
        success = editor.execute_timeline(timeline, output)
        
        if success:
            click.echo(click.style(f"\n✅ 视频剪辑完成！", fg='green'))
            click.echo(f"   输出文件: {output}")
            
            # 检查输出文件
            output_path = Path(output)
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024*1024)
                click.echo(f"   文件大小: {size_mb:.2f} MB")
                
                # 获取输出视频信息
                output_info = resource_manager.get_resource_info(output_path)
                if output_info:
                    click.echo(f"   视频时长: {output_info.get('duration', 'N/A')}秒")
                    click.echo(f"   分辨率: {output_info.get('resolution', {}).get('width', 'N/A')}x"
                              f"{output_info.get('resolution', {}).get('height', 'N/A')}")
        else:
            click.echo(click.style("❌ 视频剪辑失败", fg='red'))
            
    except Exception as e:
        click.echo(click.style(f"❌ 剪辑出错: {e}", fg='red'))
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        resource_manager.cleanup_temp_files()
        click.echo("\n🧹 临时文件已清理")


def create_simple_timeline(description: str, video_source: str) -> dict:
    """创建简单的测试时间轴"""
    return {
        "version": "1.0",
        "metadata": {
            "title": "测试视频",
            "description": description,
            "created_at": datetime.now().isoformat()
        },
        "timeline": {
            "duration": 30,
            "fps": 30,
            "resolution": {"width": 1920, "height": 1080},
            "tracks": [
                {
                    "type": "video",
                    "name": "主视频轨",
                    "clips": [
                        {
                            "start": 0,
                            "end": 30,
                            "source": video_source,
                            "clip_in": 0,
                            "clip_out": 30,
                            "filters": ["fade_in", "fade_out"]
                        }
                    ]
                },
                {
                    "type": "text",
                    "name": "字幕轨",
                    "clips": [
                        {
                            "start": 5,
                            "end": 10,
                            "content": {
                                "text": "测试字幕",
                                "font": "黑体",
                                "size": 48,
                                "color": "#FFFFFF",
                                "position": "bottom"
                            }
                        }
                    ]
                }
            ]
        }
    }


def add_video_source_to_timeline(timeline: dict, video_source: str):
    """将视频源添加到时间轴"""
    # 确保有视频轨道
    tracks = timeline["timeline"].get("tracks", [])
    video_track = None
    
    for track in tracks:
        if track["type"] == "video":
            video_track = track
            break
    
    if video_track and video_track.get("clips"):
        # 为每个片段设置视频源
        for clip in video_track["clips"]:
            if not clip.get("source"):
                clip["source"] = video_source


def detect_video_template(description: str) -> str:
    """根据描述检测合适的视频模板"""
    description_lower = description.lower()
    
    if "vlog" in description_lower or "旅行" in description_lower:
        return "vlog"
    elif "产品" in description_lower or "介绍" in description_lower:
        return "product"
    elif "教育" in description_lower or "教学" in description_lower:
        return "education"
    elif "广告" in description_lower or "商业" in description_lower:
        return "commercial"
    elif "社交" in description_lower or "短视频" in description_lower:
        return "social_media"
    else:
        return "custom"


def display_timeline_summary(timeline: dict):
    """显示时间轴摘要"""
    tl = timeline.get("timeline", {})
    
    click.echo(click.style("\n📊 时间轴摘要:", fg='cyan'))
    click.echo(f"   总时长: {tl.get('duration', 0)}秒")
    click.echo(f"   分辨率: {tl.get('resolution', {}).get('width')}x{tl.get('resolution', {}).get('height')}")
    click.echo(f"   帧率: {tl.get('fps', 30)}fps")
    
    tracks = tl.get("tracks", [])
    video_tracks = sum(1 for t in tracks if t["type"] == "video")
    audio_tracks = sum(1 for t in tracks if t["type"] == "audio")
    text_tracks = sum(1 for t in tracks if t["type"] == "text")
    
    click.echo(f"   轨道: {video_tracks}个视频, {audio_tracks}个音频, {text_tracks}个文字")
    
    # 统计特效
    all_effects = []
    for track in tracks:
        for clip in track.get("clips", []):
            all_effects.extend(clip.get("filters", []))
    
    if all_effects:
        unique_effects = list(set(all_effects))
        click.echo(f"   特效: {', '.join(unique_effects[:5])}")


if __name__ == "__main__":
    click.echo(click.style("""
╔════════════════════════════════════════════╗
║     自然语言视频剪辑系统 - 本地测试工具      ║
╚════════════════════════════════════════════╝
""", fg='bright_blue'))
    
    test_video()
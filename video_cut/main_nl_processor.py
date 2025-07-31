"""
自然语言视频剪辑主程序
整合所有组件，提供完整的自然语言到视频剪辑的流程
"""
import click
import json
import os
from pathlib import Path
from natural_language_processor import NaturalLanguageProcessor
from timeline_generator import TimelineGenerator
from video_editor import VideoEditor


@click.group()
def cli():
    """AI视频剪辑命令行工具"""
    pass


@cli.command()
@click.option('--text', '-t', help='自然语言描述')
@click.option('--input-file', '-f', type=click.Path(exists=True), help='包含描述的文本文件')
@click.option('--output-json', '-o', default='output/generated_timeline.json', help='输出时间轴JSON路径')
@click.option('--template', '-p', type=click.Choice(['vlog', 'product', 'education', 'commercial', 'social_media', 'custom']), 
              default='custom', help='视频模板类型')
def generate(text, input_file, output_json, template):
    """从自然语言生成视频时间轴"""
    
    # 获取输入文本
    if text:
        user_input = text
    elif input_file:
        with open(input_file, 'r', encoding='utf-8') as f:
            user_input = f.read()
    else:
        click.echo("请提供文本描述（--text）或输入文件（--input-file）")
        return
    
    click.echo("正在处理自然语言描述...")
    
    # 创建处理器
    nl_processor = NaturalLanguageProcessor()
    
    # 处理自然语言
    timeline_json = nl_processor.process_natural_language(user_input)
    
    # 如果需要使用高级生成器进一步优化
    if template != 'custom':
        click.echo(f"使用{template}模板优化时间轴...")
        generator = TimelineGenerator()
        
        # 构建配置
        config = {
            "title": timeline_json["timeline"].get("title", "未命名视频"),
            "duration": timeline_json["timeline"]["duration"],
            "template": template,
            "resolution": timeline_json["timeline"]["resolution"],
            "fps": timeline_json["timeline"]["fps"]
        }
        
        # 重新生成时间轴
        timeline_json = generator.generate_advanced_timeline(config)
        timeline_json = generator.optimize_timeline(timeline_json)
    
    # 保存时间轴
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(timeline_json, f, ensure_ascii=False, indent=2)
    
    click.echo(f"✅ 时间轴已生成并保存到: {output_json}")
    
    # 显示生成的时间轴摘要
    _display_timeline_summary(timeline_json)


@cli.command()
@click.option('--timeline', '-t', default='output/generated_timeline.json', help='时间轴JSON文件路径')
@click.option('--output-video', '-o', default='output/final_video.mp4', help='输出视频路径')
@click.option('--resource-dir', '-r', default='./resources', help='资源文件目录')
@click.option('--preview', is_flag=True, help='只生成预览（前30秒）')
def edit(timeline, output_video, resource_dir, preview):
    """根据时间轴JSON执行视频剪辑"""
    
    # 检查时间轴文件
    if not os.path.exists(timeline):
        click.echo(f"错误：时间轴文件不存在: {timeline}")
        return
    
    # 读取时间轴
    with open(timeline, 'r', encoding='utf-8') as f:
        timeline_json = json.load(f)
    
    # 如果是预览模式，截取前30秒
    if preview:
        timeline_json["timeline"]["duration"] = min(30, timeline_json["timeline"]["duration"])
        output_video = output_video.replace('.mp4', '_preview.mp4')
        click.echo("预览模式：只生成前30秒")
    
    click.echo("正在执行视频剪辑...")
    
    # 创建编辑器
    editor = VideoEditor(resource_dir=resource_dir)
    
    # 执行剪辑
    success = editor.execute_timeline(timeline_json, output_video)
    
    if success:
        click.echo(f"✅ 视频剪辑完成: {output_video}")
    else:
        click.echo("❌ 视频剪辑失败，请检查日志")


@cli.command()
@click.option('--text', '-t', help='自然语言描述')
@click.option('--output-video', '-o', default='output/final_video.mp4', help='输出视频路径')
@click.option('--template', '-p', type=click.Choice(['vlog', 'product', 'education', 'commercial', 'social_media', 'custom']), 
              default='custom', help='视频模板类型')
@click.option('--resource-dir', '-r', default='./resources', help='资源文件目录')
def quick(text, output_video, template, resource_dir):
    """快速模式：从自然语言直接生成视频"""
    
    if not text:
        click.echo("请提供文本描述（--text）")
        return
    
    click.echo("正在处理...")
    
    # 生成时间轴
    nl_processor = NaturalLanguageProcessor()
    timeline_json = nl_processor.process_natural_language(text)
    
    # 保存时间轴（备份）
    timeline_path = "output/quick_timeline.json"
    os.makedirs("output", exist_ok=True)
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline_json, f, ensure_ascii=False, indent=2)
    
    # 执行剪辑
    editor = VideoEditor(resource_dir=resource_dir)
    success = editor.execute_timeline(timeline_json, output_video)
    
    if success:
        click.echo(f"✅ 视频生成完成: {output_video}")
        click.echo(f"时间轴已保存到: {timeline_path}")
    else:
        click.echo("❌ 视频生成失败")


@cli.command()
def examples():
    """显示使用示例"""
    examples_text = """
AI视频剪辑使用示例：

1. 生成时间轴：
   python main_nl_processor.py generate -t "制作一个1分钟的产品介绍视频，开头5秒展示logo，然后介绍产品特点"
   
2. 从文件生成时间轴：
   python main_nl_processor.py generate -f description.txt -o timeline.json
   
3. 执行视频剪辑：
   python main_nl_processor.py edit -t timeline.json -o output.mp4
   
4. 快速生成视频：
   python main_nl_processor.py quick -t "创建30秒的社交媒体广告，要有动感音乐和炫酷转场"
   
5. 使用模板：
   python main_nl_processor.py generate -t "Vlog风格的旅行记录" -p vlog

示例描述：
- "制作一个3分钟的教育视频，讲解人工智能，要有字幕和背景音乐"
- "创建产品展示视频，展示手机的各个功能，每个功能10秒，配上说明文字"
- "做一个1分钟的预告片，要有快速剪辑、震撼音效和炫酷特效"
    """
    click.echo(examples_text)


def _display_timeline_summary(timeline_json: Dict):
    """显示时间轴摘要"""
    timeline = timeline_json.get("timeline", {})
    
    click.echo("\n时间轴摘要：")
    click.echo(f"- 总时长: {timeline.get('duration', 0)}秒")
    click.echo(f"- 分辨率: {timeline.get('resolution', {}).get('width')}x{timeline.get('resolution', {}).get('height')}")
    click.echo(f"- 帧率: {timeline.get('fps', 30)}fps")
    
    tracks = timeline.get("tracks", [])
    video_tracks = [t for t in tracks if t["type"] == "video"]
    audio_tracks = [t for t in tracks if t["type"] == "audio"]
    text_tracks = [t for t in tracks if t["type"] == "text"]
    
    click.echo(f"- 视频轨道: {len(video_tracks)}个")
    click.echo(f"- 音频轨道: {len(audio_tracks)}个")
    click.echo(f"- 文字轨道: {len(text_tracks)}个")
    
    # 统计特效
    all_effects = []
    for track in tracks:
        for clip in track.get("clips", []):
            all_effects.extend(clip.get("filters", []))
    
    if all_effects:
        click.echo(f"- 使用特效: {len(set(all_effects))}种")


if __name__ == '__main__':
    cli()
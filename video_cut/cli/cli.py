import click
import json
import os

from video_cut.config import DAG, NODES
from video_cut.core.controller import UnifiedController


@click.group()
def cli():
    pass

@cli.command()
@click.option('--input-file', type=click.Path(exists=True), help='输入 JSON 文件')
def generate(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        user_input = json.load(f)

    controller = UnifiedController(DAG, NODES)
    result = controller.handle_input(user_input)

    output_path = "output/final_timeline.json"
    os.makedirs("output", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result['node12'], f, ensure_ascii=False, indent=2)
    click.echo(f"✅ 输出已保存至 {output_path}")

@cli.command()
@click.option('--input-file', type=click.Path(exists=True), help='修改输入 JSON 文件')
def modify(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        user_input = json.load(f)

    controller = UnifiedController(DAG, NODES)
    result = controller.handle_input(user_input)

    output_path = "output/final_timeline_modified.json"
    os.makedirs("output", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result['node12'], f, ensure_ascii=False, indent=2)
    click.echo(f"✅ 修改后输出已保存至 {output_path}")

@cli.command()
@click.option('--text', '-t', help='自然语言描述')
@click.option('--file', '-f', type=click.Path(exists=True), help='包含自然语言描述的文本文件')
@click.option('--output', '-o', default='output/nl_timeline.json', help='输出文件路径')
def nl_generate(text, file, output):
    """从自然语言生成视频时间轴"""
    
    # 获取自然语言输入
    if text:
        natural_language = text
    elif file:
        with open(file, 'r', encoding='utf-8') as f:
            natural_language = f.read().strip()
    else:
        click.echo("错误：请提供文本描述（--text）或文本文件（--file）")
        return
    
    click.echo(f"正在处理自然语言描述...")
    click.echo(f"输入: {natural_language[:100]}..." if len(natural_language) > 100 else f"输入: {natural_language}")
    
    # 创建输入数据
    user_input = {
        "type": "nl_generate",
        "natural_language": natural_language
    }
    
    # 处理输入
    controller = UnifiedController(DAG, NODES)
    result = controller.handle_input(user_input)
    
    # 保存结果
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result['node12'], f, ensure_ascii=False, indent=2)
    
    click.echo(f"✅ 时间轴已生成并保存至 {output}")
    
    # 显示生成的大纲
    if '大纲内容' in result.get('node1', {}):
        click.echo(f"\n生成的视频大纲：")
        click.echo("-" * 50)
        click.echo(result['node1']['大纲内容'][:300] + "..." if len(result['node1']['大纲内容']) > 300 else result['node1']['大纲内容'])
        click.echo("-" * 50)

@cli.command()
def nl_examples():
    """显示自然语言输入示例"""
    examples = """
自然语言输入示例：

1. 产品介绍：
   python -m video_cut.cli.cli nl-generate -t "制作一个1分钟的智能手表产品介绍视频，展示外观和功能"

2. 教育视频：
   python -m video_cut.cli.cli nl-generate -t "创建一个3分钟的Python编程教程，讲解列表的使用"

3. 社交媒体：
   python -m video_cut.cli.cli nl-generate -t "做一个30秒的抖音风格美食探店视频，要有快切和动感音乐"

4. Vlog：
   python -m video_cut.cli.cli nl-generate -t "制作5分钟的日本旅行vlog，包含东京、京都、大阪的风景"

5. 企业宣传：
   python -m video_cut.cli.cli nl-generate -t "创建一个2分钟的科技公司宣传片，展示公司文化和产品"

更多示例描述：
- "做一个温馨的家庭相册视频，配上舒缓的背景音乐，时长3分钟"
- "制作一个炫酷的游戏宣传片，要有震撼的特效和快节奏剪辑"
- "创建一个专业的在线课程介绍视频，清晰展示课程大纲和特色"
    """
    click.echo(examples)

if __name__ == '__main__':
    cli()
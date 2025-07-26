import click
import json

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
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result['node12'], f, ensure_ascii=False, indent=2)
    click.echo(f"✅ 修改后输出已保存至 {output_path}")

if __name__ == '__main__':
    cli()
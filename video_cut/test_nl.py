"""
测试自然语言处理功能
"""
import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video_cut.config import DAG, NODES
from video_cut.core.controller import UnifiedController
from video_cut.core.nl_processor import NLProcessor


def test_nl_processor():
    """测试自然语言处理器"""
    print("=" * 50)
    print("测试自然语言处理器")
    print("=" * 50)
    
    processor = NLProcessor()
    
    test_input = "做一个30秒的抖音风格美食视频，要有快切和动感音乐"
    print(f"\n测试输入: {test_input}")
    
    outline = processor.process_natural_language(test_input)
    print(f"\n生成的大纲:\n{outline}")
    
    elements = processor.extract_key_elements(outline)
    print(f"\n提取的关键元素:\n{json.dumps(elements, ensure_ascii=False, indent=2)}")


def test_nl_generate_flow():
    """测试完整的自然语言生成流程"""
    print("\n" + "=" * 50)
    print("测试完整的自然语言生成流程")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        "制作一个1分钟的产品介绍视频，展示智能手表的外观和功能",
        "创建30秒的社交媒体广告，要有炫酷特效和快节奏",
        "做一个3分钟的教育视频，讲解人工智能的基础知识"
    ]
    
    controller = UnifiedController(DAG, NODES)
    
    for i, test_input in enumerate(test_cases):
        print(f"\n--- 测试用例 {i+1} ---")
        print(f"输入: {test_input}")
        
        user_input = {
            "type": "nl_generate",
            "natural_language": test_input
        }
        
        try:
            result = controller.handle_input(user_input)
            
            # 检查是否生成了所有节点
            print(f"生成的节点数: {len(result)}")
            
            # 显示部分结果
            if 'node1' in result:
                print(f"\nNode1 (需求提取):")
                print(json.dumps(result['node1'], ensure_ascii=False, indent=2)[:200] + "...")
            
            if 'node12' in result:
                print(f"\nNode12 (最终时间轴):")
                timeline = result['node12']
                if 'timeline' in timeline:
                    print(f"- 时长: {timeline['timeline'].get('duration')}秒")
                    print(f"- 轨道数: {len(timeline['timeline'].get('tracks', []))}")
                
                # 保存结果
                output_file = f"output/test_nl_{i+1}.json"
                os.makedirs("output", exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(timeline, f, ensure_ascii=False, indent=2)
                print(f"结果已保存到: {output_file}")
                
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()


def test_cli_integration():
    """测试CLI集成"""
    print("\n" + "=" * 50)
    print("测试CLI集成")
    print("=" * 50)
    
    # 创建测试文件
    test_nl_file = "test_nl_input.txt"
    with open(test_nl_file, 'w', encoding='utf-8') as f:
        f.write("制作一个2分钟的企业宣传片，展示公司的技术实力和团队文化，要专业大气有科技感")
    
    print(f"创建测试文件: {test_nl_file}")
    
    # 模拟CLI命令
    from video_cut.cli.cli import cli
    from click.testing import CliRunner
    
    runner = CliRunner()
    
    # 测试nl-generate命令
    result = runner.invoke(cli, ['nl-generate', '-f', test_nl_file, '-o', 'output/test_cli.json'])
    
    print(f"\nCLI输出:")
    print(result.output)
    
    if result.exit_code == 0:
        print("CLI测试成功!")
    else:
        print(f"CLI测试失败，退出码: {result.exit_code}")
    
    # 清理测试文件
    os.remove(test_nl_file)


if __name__ == "__main__":
    # 运行测试
    test_nl_processor()
    test_nl_generate_flow()
    test_cli_integration()
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)
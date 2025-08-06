#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 测试修复后的路径计算
executor_file_path = "/Users/luming/PycharmProjects/Ai-movie-clip/video_cut/aura_render/execution_layer/executor.py"
executor_dir = os.path.dirname(executor_file_path)
print(f"executor.py 目录: {executor_dir}")

# 模拟修复后的路径计算
project_root_calc = os.path.abspath(os.path.join(executor_dir, '../../..'))
font_path = os.path.join(project_root_calc, '微软雅黑.ttf')

print(f"计算的项目根目录: {project_root_calc}")
print(f"字体文件路径: {font_path}")
print(f"字体文件存在: {os.path.exists(font_path)}")

# 测试 MoviePy TextClip 是否能使用这个字体
try:
    from moviepy import TextClip
    print("\n测试 MoviePy TextClip...")
    
    # 创建一个简单的文字测试
    test_clip = TextClip(
        text="测试中文字体",
        font=font_path,
        font_size=50,
        color='white'
    ).with_duration(1)
    
    print("✅ TextClip 创建成功，字体可用")
    print(f"文字内容: {test_clip}")
    
except Exception as e:
    print(f"❌ TextClip 创建失败: {e}")
    
    # 尝试使用系统字体
    try:
        test_clip = TextClip(
            text="测试中文字体",
            font='Arial-Unicode-MS',  # macOS 系统中文字体
            font_size=50,
            color='white'
        ).with_duration(1)
        print("✅ 使用 Arial-Unicode-MS 成功")
    except Exception as e2:
        print(f"❌ Arial-Unicode-MS 也失败: {e2}")
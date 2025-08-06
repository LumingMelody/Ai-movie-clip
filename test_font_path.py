#!/usr/bin/env python3
import os

# 测试字体路径计算
current_file = "/Users/luming/PycharmProjects/Ai-movie-clip/video_cut/aura_render/execution_layer/executor.py"
current_dir = os.path.dirname(current_file)
print(f"当前文件目录: {current_dir}")

project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
print(f"计算的项目根目录: {project_root}")

font_path1 = os.path.join(project_root, '江西拙楷2.0.ttf')
font_path2 = os.path.join(project_root, '微软雅黑.ttf')

print(f"江西拙楷字体路径: {font_path1}")
print(f"字体文件存在: {os.path.exists(font_path1)}")

print(f"微软雅黑字体路径: {font_path2}")
print(f"字体文件存在: {os.path.exists(font_path2)}")

# 检查实际的项目根目录
actual_root = "/Users/luming/PycharmProjects/Ai-movie-clip"
actual_font1 = os.path.join(actual_root, '江西拙楷2.0.ttf')
actual_font2 = os.path.join(actual_root, '微软雅黑.ttf')

print(f"实际项目根目录: {actual_root}")
print(f"实际江西拙楷路径: {actual_font1}")
print(f"实际字体文件存在: {os.path.exists(actual_font1)}")
print(f"实际微软雅黑路径: {actual_font2}")
print(f"实际字体文件存在: {os.path.exists(actual_font2)}")
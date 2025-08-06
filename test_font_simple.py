#!/usr/bin/env python3
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from video_cut.aura_render.aura_interface import create_aura_video

# 创建一个简单的测试，重点测试字体显示
result = create_aura_video(
    natural_language="制作一个10秒的测试视频，显示中文字幕",
    preferences={'video_type': 'test', 'style': 'simple'}
)

print(f"生成的视频路径: {result['video_url']}")
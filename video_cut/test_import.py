#!/usr/bin/env python3
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from video_cut.aura_render.aura_interface import create_aura_video
    print("✅ Import successful! Module loaded correctly.")
    
    # Test that the function is callable
    if callable(create_aura_video):
        print("✅ create_aura_video function is available and callable.")
    else:
        print("❌ create_aura_video is not callable.")
        
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
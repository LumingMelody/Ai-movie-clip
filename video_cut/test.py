import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from video_cut.aura_render.aura_interface import create_aura_video

# 创建产品广告
result = create_aura_video(
    natural_language="制作一个30秒的智能手表广告，展示健康监测功能",
    video_url="https://file.digitaling.com/eImg/uvideos/2023/0913/1694591406987124.mp4",
    preferences={'video_type': 'product_ad', 'style': 'modern'}
)

print(result['video_url'])  # 输出视频地址
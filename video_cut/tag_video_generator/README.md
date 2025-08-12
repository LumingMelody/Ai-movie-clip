# 标签视频生成器 (Tag Video Generator)

根据标签配置自动生成视频，支持随机片段提取、AI文案生成、字幕和动态标签。

## 功能特性

1. **按标签顺序生成视频** - 根据前端传入的标签顺序，从每个标签的视频池中随机提取片段
2. **随机片段提取** - 从每个视频中随机选择时间段，避免重复
3. **AI文案生成** - 使用通义千问自动生成宣传文案
4. **字幕支持** - 自动添加字幕，支持自定义样式
5. **动态标签** - 在视频中显示动态变化的标签

## 使用方法

### 1. 基础使用

```python
from video_cut.tag_video_generator import TagVideoGenerator

# 创建生成器
generator = TagVideoGenerator()

# 标签配置
tag_config = {
    "黄山风景": {
        "video": ["assets/videos/huangshan.mp4", "assets/videos/huangshan1.mp4"]
    },
    "徽州特色餐": {
        "video": ["assets/videos/huizhoucai.mp4"]
    },
    "屯溪老街": {
        "video": ["assets/videos/tunxi.mp4", "assets/videos/tunxi1.mp4"]
    }
}

# 生成视频
generator.generate_video_from_tags(
    tag_config=tag_config,
    output_path="output/travel_video.mp4",
    duration_per_tag=5.0,  # 每个标签5秒
    text_content="探索黄山美景，品味徽州美食"  # 可选，不提供则AI生成
)
```

### 2. API接口使用

```python
from video_cut.tag_video_generator import TagVideoAPIHandler

handler = TagVideoAPIHandler()

# 前端请求格式
request = {
    "tags": ["黄山风景", "徽州特色餐", "屯溪老街"],
    "tag_videos": {
        "黄山风景": {
            "video": ["path1.mp4", "path2.mp4"]
        },
        "徽州特色餐": {
            "video": ["path3.mp4"]
        },
        "屯溪老街": {
            "video": ["path4.mp4"]
        }
    },
    "text_content": "可选文案",  # 可选
    "subtitle_config": {  # 可选
        "font_size": 48,
        "color": "white",
        "position": ("center", "bottom")
    },
    "dynamic_tags": ["黄山", "美食", "古街"],  # 可选
    "duration_per_tag": 5.0
}

result = handler.handle_request(request)
```

### 3. FastAPI集成

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from video_cut.tag_video_generator.api_handler import TagVideoAPIHandler

app = FastAPI()
tag_video_handler = TagVideoAPIHandler()

class TagVideoRequest(BaseModel):
    tags: List[str]
    tag_videos: Dict[str, Dict[str, List[str]]]
    text_content: Optional[str] = None
    subtitle_config: Optional[Dict[str, Any]] = None
    dynamic_tags: Optional[List[str]] = None
    duration_per_tag: float = 5.0

@app.post("/video/generate-from-tags")
async def generate_video_from_tags(request: TagVideoRequest):
    result = tag_video_handler.handle_request(request.dict())
    return result
```

## 参数说明

### tag_config
- 类型: `Dict[str, Dict[str, List[str]]]`
- 描述: 标签到视频列表的映射
- 示例: `{"黄山风景": {"video": ["video1.mp4", "video2.mp4"]}}`

### duration_per_tag
- 类型: `float`
- 默认: `5.0`
- 描述: 每个标签的目标时长（秒）

### clip_duration_range
- 类型: `tuple`
- 默认: `(2.0, 5.0)`
- 描述: 随机片段的时长范围

### text_content
- 类型: `Optional[str]`
- 默认: `None`（使用AI生成）
- 描述: 视频文案内容

### subtitle_config
- 类型: `Optional[Dict]`
- 描述: 字幕配置
- 字段:
  - `font`: 字体名称
  - `font_size`: 字体大小
  - `color`: 字体颜色
  - `stroke_color`: 描边颜色
  - `stroke_width`: 描边宽度
  - `position`: 位置
  - `margin`: 边距

### dynamic_tags
- 类型: `Optional[List[str]]`
- 默认: 使用tag_config的键
- 描述: 动态显示的标签列表

## 输出格式

API返回格式:
```json
{
    "success": true,
    "video_path": "/path/to/output.mp4",
    "video_url": "https://oss.example.com/video.mp4",
    "message": "视频生成成功"
}
```

## 测试

运行测试脚本:
```bash
python video_cut/tag_video_generator/test_tag_generator.py
```

## 注意事项

1. 确保视频文件路径正确且可访问
2. AI文案生成需要配置通义千问API密钥
3. 视频处理需要足够的内存和CPU资源
4. 输出视频默认使用H.264编码，兼容性好
# 节点数据结构总结

本文档总结了 `video_cut/data` 目录中各个节点的数据结构和用途。

## 节点概览

### node1 - 基础信息节点
包含视频的基本配置信息：
- `title`: 视频标题
- `duration`: 视频时长（秒）
- `target_platform`: 目标平台（如B站、抖音等）
- `target_audience`: 目标受众
- `video_style`: 视频风格
- `brand_guidelines`: 品牌规范（颜色、字体、logo等）
- `special_requirements`: 特殊要求

### node2 - 时间结构节点
定义视频的时间分配：
- `intro_duration`: 开场时长
- `main_content_duration`: 主要内容时长
- `climax_duration`: 高潮部分时长
- `outro_duration`: 结尾时长
- `transition_style`: 转场风格
- `beat_pattern`: 节奏模式

### node3 - 视频片段节点
包含视频的具体片段信息：
- `segments`: 片段数组，每个片段包含：
  - `id`: 片段ID
  - `title`: 片段标题
  - `start_time`: 开始时间
  - `end_time`: 结束时间
  - `content_type`: 内容类型
  - `media_source`: 媒体来源
  - `duration`: 持续时间
  - `transition`: 转场类型
  - `notes`: 备注

### node4 - 图层节点
定义视频的图层结构（具体结构需查看）

### node5 - 文字片段节点
包含所有文字/字幕信息：
- `clips`: 文字片段数组，每个片段包含：
  - `clip_id`: 片段ID
  - `text`: 文字内容
  - `start_time`: 开始时间
  - `end_time`: 结束时间
  - `duration`: 持续时间
  - `style`: 样式配置（字体、颜色、大小、位置等）
  - `animation`: 动画效果

### node6 - 音频轨道节点
定义音频配置：
- `audio_tracks`: 音频轨道数组，每个轨道包含：
  - `track_id`: 轨道ID
  - `type`: 类型（背景音乐、音效等）
  - `source`: 音频来源描述
  - `start_time`: 开始时间
  - `end_time`: 结束时间
  - `volume`: 音量（0-1）
  - `fade`: 是否淡入淡出
  - `loop`: 是否循环

### node7 - 动画效果节点
包含动画效果配置

### node8 - 特效节点
包含视频特效配置

### node9 - 脚本节点
包含视频脚本或旁白信息

### node10 - 品牌元素节点
包含品牌相关的元素配置

### node11 - 输出配置节点
定义视频输出的相关配置

### node12 - 时间轴节点
包含完整的时间轴结构

## 使用示例

### 1. 加载所有节点数据
```python
from pathlib import Path
import json

node_data_dir = Path("video_cut/data")
nodes = {}

for node_dir in sorted(node_data_dir.iterdir()):
    if node_dir.is_dir():
        node_name = node_dir.name
        json_file = node_dir / f"{node_name}_latest.json"
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                nodes[node_name] = json.load(f)
```

### 2. 基于节点生成时间轴
```python
# 获取基础信息
basic_info = nodes.get('node1', {})
segments = nodes.get('node3', {}).get('segments', [])
text_clips = nodes.get('node5', {}).get('clips', [])

# 构建时间轴
timeline = {
    "version": "1.0",
    "metadata": {
        "title": basic_info.get("title"),
        "duration": basic_info.get("duration")
    },
    "timeline": {
        "tracks": []
    }
}
```

### 3. 节点之间的关系
- node1 提供整体配置
- node2 定义时间分配策略
- node3 定义具体的视频片段
- node5 提供文字内容
- node6 提供音频配置
- 其他节点提供额外的效果和配置

## 测试脚本

项目中提供了以下测试脚本：

1. **test_timeline_node_based.py** - 基础的节点时间轴生成测试
2. **test_timeline_advanced_nodes.py** - 高级节点处理和多模板测试
3. **visualize_timeline.py** - 时间轴可视化工具

运行测试：
```bash
python test_timeline_node_based.py
python test_timeline_advanced_nodes.py
python visualize_timeline.py
```
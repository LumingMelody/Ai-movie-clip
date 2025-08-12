# 阿里云字幕API集成文档

## 概述

本项目已集成阿里云智能媒体服务的字幕API，支持九宫格位置设置和丰富的字幕效果。

## 九宫格位置系统

```
1 | 2 | 3    (左上|顶部中间|右上)
---------
4 | 5 | 6    (左侧中间|正中心|右侧中间)
---------
7 | 8 | 9    (左下|底部中间|右下)
```

## API使用方法

### 1. 基础使用

```json
{
  "tags": ["黄山风景", "徽州特色餐"],
  "tag_videos": {
    "黄山风景": {
      "video": ["https://example.com/video1.mp4"]
    },
    "徽州特色餐": {
      "video": ["https://example.com/video2.mp4"]
    }
  },
  "subtitle_config": {
    "grid_position": 8,           // 九宫格位置 (1-9)
    "font_size": 48,              // 字体大小
    "color": "#FFFFFF",           // 字体颜色
    "stroke_color": "#000000",    // 描边颜色
    "stroke_width": 2,            // 描边宽度
    "max_chars_per_subtitle": 20, // 每个字幕最大字符数
    "min_display_time": 2.0       // 最小显示时间(秒)
  }
}
```

### 2. 高级配置

```json
{
  "subtitle_config": {
    "grid_position": 5,           // 正中心位置
    "font_size": 52,
    "color": "#FFFF00",           // 黄色字体
    "stroke_color": "#000000",
    "stroke_width": 3,
    "font_face": "Bold",          // 字体样式: Normal, Bold, Italic, Underline
    "custom_x": 0.3,              // 自定义X坐标 (0-1)
    "custom_y": 0.7,              // 自定义Y坐标 (0-1)
    "max_chars_per_subtitle": 15,
    "min_display_time": 1.5
  }
}
```

## 支持的字体样式

- `Normal`: 普通字体
- `Bold`: 粗体
- `Italic`: 斜体
- `Underline`: 下划线
- `BoldItalic`: 粗斜体
- `BoldUnderline`: 粗体下划线
- `ItalicUnderline`: 斜体下划线
- `BoldItalicUnderline`: 粗斜体下划线

## 位置设置选项

### 九宫格位置 (推荐)

使用 `grid_position` 参数，取值 1-9：

- **1**: 左上角 - 适合logo或标题
- **2**: 顶部中间 - 适合主标题
- **3**: 右上角 - 适合时间或标签
- **4**: 左侧中间 - 适合人物介绍
- **5**: 正中心 - 适合重要提示
- **6**: 右侧中间 - 适合补充信息
- **7**: 左下角 - 适合来源标注
- **8**: 底部中间 - 适合常规字幕 (默认)
- **9**: 右下角 - 适合版权信息

### 自定义位置

使用 `custom_x` 和 `custom_y` 参数，取值 0-1：

```json
{
  "custom_x": 0.2,  // 距离左边20%
  "custom_y": 0.8,  // 距离顶部80%
  "alignment": "BottomLeft"
}
```

## 生成的文件

使用阿里云字幕API时，系统会生成以下文件：

1. **字幕配置JSON**: `output/aliyun_subtitles/subtitle_*.json`
   - 包含完整的阿里云时间轴配置
   - 可直接用于阿里云制作API

2. **制作时间轴**: 包含视频和字幕轨道的完整配置

## 实际制作流程

1. **生成字幕配置**: 使用本API生成字幕时间轴
2. **调用阿里云制作API**: 将配置提交给阿里云进行实际制作
3. **获取结果**: 从阿里云获取带字幕的视频

## 示例代码

### Python调用示例

```python
from video_cut.tag_video_generator.tag_video_generator import TagVideoGenerator

# 创建生成器，启用阿里云字幕
generator = TagVideoGenerator(use_aliyun_subtitle=True)

# 配置字幕
subtitle_config = {
    'grid_position': 3,  # 右上角
    'font_size': 48,
    'color': '#FFFFFF',
    'stroke_color': '#000000',
    'max_chars_per_subtitle': 18
}

# 生成视频
generator.generate_video_from_tags(
    tag_config=tag_config,
    output_path="output/video.mp4",
    subtitle_config=subtitle_config
)
```

### API请求示例

```bash
curl -X POST "http://localhost:8100/video/generate-from-tags" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["黄山风景", "徽州美食"],
    "tag_videos": {
      "黄山风景": {"video": ["video1.mp4"]},
      "徽州美食": {"video": ["video2.mp4"]}
    },
    "subtitle_config": {
      "grid_position": 8,
      "font_size": 48,
      "color": "#FFFFFF"
    }
  }'
```

## 测试和验证

运行测试脚本验证功能：

```bash
# 测试所有功能
python test_aliyun_subtitle.py

# 只测试API基础功能
python test_aliyun_subtitle.py --test api

# 只测试生成器集成
python test_aliyun_subtitle.py --test generator

# 只测试完整工作流程
python test_aliyun_subtitle.py --test workflow
```

## 注意事项

1. **API密钥**: 需要配置阿里云访问密钥才能调用实际的制作API
2. **视频格式**: 支持阿里云智能媒体服务支持的所有视频格式
3. **字幕长度**: 建议每个字幕片段不超过20个字符以确保可读性
4. **显示时间**: 最小显示时间建议不少于1.5秒
5. **位置冲突**: 避免在同一位置同时显示多个字幕

## 错误处理

系统会自动验证字幕配置，常见错误包括：

- 字幕内容为空
- 九宫格位置超出范围 (1-9)
- 时间设置错误 (结束时间 <= 开始时间)
- 字体大小无效 (≤ 0)
- 不支持的字体样式

## 性能优化建议

1. **分段处理**: 长视频建议分段处理字幕
2. **缓存配置**: 相同配置的字幕可以复用时间轴
3. **批量处理**: 多个视频使用相同字幕配置时建议批量生成
4. **预览模式**: 开发时使用较短的视频进行测试
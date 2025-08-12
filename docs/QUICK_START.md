# 自然语言视频剪辑 - 快速开始指南

## 1分钟快速体验

### 第一步：启动服务
```bash
cd /Users/luming/PycharmProjects/Ai-movie-clip
python app.py
```

### 第二步：发送请求
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个30秒的产品介绍视频",
    "video_url": "你的视频URL",
    "mode": "sync"
  }'
```

### 第三步：获取结果
响应中的 `data.video_url` 就是剪辑后的视频地址！

## 常用示例

### 1. 产品介绍
```json
{
  "natural_language": "制作30秒产品介绍，开头展示logo，中间介绍功能，结尾展示联系方式",
  "video_url": "https://your-video.mp4"
}
```

### 2. Vlog剪辑
```json
{
  "natural_language": "剪辑1分钟旅行vlog，要有温馨的音乐和字幕",
  "video_url": "https://your-video.mp4",
  "style": "温馨"
}
```

### 3. 教学视频
```json
{
  "natural_language": "制作2分钟教学视频，分为介绍、演示、总结三个部分",
  "video_url": "https://your-video.mp4",
  "output_duration": 120
}
```

## 关键参数

- `natural_language`: 用中文描述你想要的效果
- `video_url`: 原始视频的网络地址
- `mode`: "sync"（等待结果）或 "async"（返回任务ID）
- `output_duration`: 输出视频时长（秒）
- `style`: 视频风格（科技感/温馨/动感等）

## 描述技巧

✅ **好的描述**：
- "制作30秒产品介绍，开头5秒logo，20秒功能展示，5秒购买信息"
- "剪辑1分钟vlog，包含风景、美食、人文三部分"

❌ **避免**：
- 过于模糊："剪个视频"
- 技术细节："使用H.264编码，码率5Mbps"

## 故障排除

1. **视频下载失败**：确保video_url可公开访问
2. **处理超时**：长视频建议使用async模式
3. **效果不理想**：尝试更详细的描述

## 需要帮助？

查看完整文档：`/docs/natural_language_video_edit_api.md`

---
🎬 开始你的AI视频创作之旅吧！
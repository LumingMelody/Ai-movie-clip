# 自然语言视频剪辑API文档

## 概述

自然语言视频剪辑API允许用户通过自然语言描述来自动剪辑视频。系统会理解用户的需求，生成视频剪辑时间轴，并执行相应的剪辑操作。

## API端点

```
POST /video/natural-language-edit
```

## 请求参数

| 参数名 | 类型 | 必需 | 说明 | 示例 |
|--------|------|------|------|------|
| natural_language | string | 是 | 自然语言描述 | "制作一个1分钟的产品介绍视频" |
| video_url | string | 是 | 视频URL地址 | "https://example.com/video.mp4" |
| mode | string | 否 | 处理模式 | "sync" 或 "async"（默认） |
| output_duration | integer | 否 | 输出视频时长（秒） | 60 |
| style | string | 否 | 视频风格 | "科技感"、"温馨"、"动感" |
| use_timeline_editor | boolean | 否 | 是否使用时间轴编辑器 | true（默认） |
| tenant_id | string | 否 | 租户ID | "tenant_123" |
| id | string | 否 | 业务ID | "business_456" |

## 请求示例

### 同步模式请求

```json
{
    "natural_language": "制作一个30秒的产品介绍视频，开头5秒展示公司logo带光晕特效，然后20秒介绍产品功能配字幕，最后5秒展示联系方式",
    "video_url": "https://your-oss.com/videos/product_demo.mp4",
    "mode": "sync",
    "output_duration": 30,
    "style": "科技感",
    "use_timeline_editor": true,
    "tenant_id": "tenant_001",
    "id": "biz_001"
}
```

### 异步模式请求

```json
{
    "natural_language": "剪辑一个1分钟的旅行vlog，包含城市风光、美食、人文三个部分，配上轻松的背景音乐",
    "video_url": "https://your-oss.com/videos/travel_footage.mp4",
    "mode": "async",
    "output_duration": 60,
    "style": "温馨",
    "tenant_id": "tenant_002"
}
```

## 响应格式

### 同步模式响应

```json
{
    "status": "completed",
    "data": {
        "video_url": "https://your-oss.com/output/edited_video.mp4",
        "timeline": {
            "version": "1.0",
            "timeline": {
                "duration": 30,
                "fps": 30,
                "tracks": [...]
            }
        },
        "video_info": {
            "duration": 30,
            "width": 1920,
            "height": 1080,
            "fps": 30
        },
        "process_info": {
            "natural_language": "制作一个30秒的产品介绍视频...",
            "used_timeline_editor": true,
            "original_duration": 180
        }
    },
    "processing_time": 15.23,
    "task_id": "uuid-xxx",
    "upload_info": {
        "oss_url": "https://your-oss.com/output/edited_video.mp4",
        "file_size": 12345678
    }
}
```

### 异步模式响应

```json
{
    "status": "submitted",
    "task_id": "task_uuid_123456",
    "message": "任务已提交，请通过任务ID查询结果"
}
```

## 自然语言描述指南

### 基本元素

1. **时长指定**
   - "制作一个**30秒**的视频"
   - "剪辑**2分钟**的片段"

2. **内容结构**
   - "开头5秒展示logo"
   - "然后20秒介绍产品"
   - "最后添加结尾动画"

3. **特效描述**
   - "带**光晕特效**"
   - "使用**淡入淡出**转场"
   - "添加**粒子效果**"

4. **风格指定**
   - "**科技感**十足"
   - "**温馨**的家庭氛围"
   - "**动感**的节奏"

### 示例描述

#### 产品介绍视频
```
制作一个1分钟的智能手表产品介绍视频。开头5秒展示公司logo，要有光晕特效。
然后20秒介绍产品外观，画面要360度旋转展示。接下来20秒展示健康监测、运动追踪、
智能提醒三个核心功能，每个功能配说明文字。最后15秒展示购买信息和二维码。
整体要科技感十足，配上动感的背景音乐。
```

#### Vlog视频
```
制作一个3分钟的日本旅行vlog。第一部分1分钟展示东京街头，包括涩谷、
浅草寺的画面，要有日期和地点标注。第二部分1分钟是美食探店，展示寿司、
拉面的特写镜头。第三部分1分钟是京都古城，用慢镜头展示寺庙风景。
全程配上轻松愉快的背景音乐，字幕用手写风格。
```

#### 教育视频
```
创建一个2分钟的Python编程教学视频。前30秒介绍什么是Python，用图形动画展示。
然后1分钟讲解基础语法，展示代码示例和运行结果。最后30秒总结要点，
提供学习资源。需要清晰的解说词和代码高亮显示。
```

## 时间轴结构说明

系统会根据自然语言描述生成标准的时间轴JSON，包含：

- **视频轨道**：主视频内容、特效层等
- **音频轨道**：背景音乐、音效等
- **文字轨道**：字幕、标题等

## 注意事项

1. **视频URL**必须是可访问的公网地址
2. **处理时间**取决于视频长度和复杂度
3. **异步模式**适合长视频或复杂处理
4. **时间轴编辑器**提供更精确的控制，但处理时间较长

## 错误处理

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 400 | 参数错误 | 检查必需参数 |
| 404 | 视频不存在 | 确认视频URL有效 |
| 500 | 服务器错误 | 联系技术支持 |

## 使用限制

- 最大视频时长：10分钟
- 最大文件大小：2GB
- 支持格式：MP4、AVI、MOV、MKV

## 查询异步任务结果

```
GET /get-result/{task_id}
```

响应示例：
```json
{
    "task_id": "task_uuid_123456",
    "status": "completed",
    "result": {
        "video_url": "https://your-oss.com/output/edited_video.mp4",
        "processing_time": 23.45
    }
}
```
# AuraRender 使用指南

## 概述

AuraRender 是一个智能视频创作引擎，通过分离智能决策和机械执行，实现了高度可控和可预测的视频生成。

## 核心特性

### 1. 智能编排层（前端）
- 理解自然语言需求
- 自动选择合适的视频类型
- 智能匹配风格系统
- 规划资源使用
- 生成详细的执行脚本

### 2. 机械执行层（后端）
- 精确执行脚本指令
- 无智能决策，保证可预测性
- 支持多种资源加载方式
- 集成AI生成能力（万相等）
- 高效的视频渲染

## 支持的视频类型

1. **产品广告** (`product_ad`) - 商品展示、产品介绍
2. **品牌宣传** (`brand_promo`) - 企业形象、品牌故事
3. **知识科普** (`knowledge_explain`) - 科学解释、知识分享
4. **在线课程** (`online_course`) - 教学课程、技能培训
5. **短剧** (`short_drama`) - 剧情短片、创意故事
6. **音乐MV** (`music_mv`) - 歌曲MV、音乐视频
7. **Vlog** (`vlog`) - 日常记录、旅行日志
8. **生活分享** (`life_share`) - 生活技巧、经验分享
9. **微电影** (`micro_film`) - 创意短片、艺术短片
10. **概念展示** (`concept_show`) - 创意展示、设计作品
11. **游戏视频** (`game_video`) - 游戏实况、电竞集锦
12. **培训视频** (`training_video`) - 企业培训、操作指导

## 快速开始

### 1. 基础使用

```python
from video_cut.aura_render.aura_interface import create_aura_video

# 创建产品广告
result = create_aura_video(
    natural_language="制作一个30秒的智能手表广告，展示健康监测功能",
    preferences={
        'video_type': 'product_ad',
        'style': 'modern'
    }
)

print(result['video_url'])  # 输出视频地址
```

### 2. 带原始素材

```python
result = create_aura_video(
    natural_language="用这段素材制作一个温馨的家庭相册视频",
    video_url="https://example.com/family_footage.mp4",
    preferences={
        'video_type': 'life_share',
        'style': 'warm'
    }
)
```

### 3. 高级配置

```python
from video_cut.aura_render.aura_interface import AuraRenderInterface

interface = AuraRenderInterface()

request = {
    'natural_language': '创建一个2分钟的企业宣传片，展示公司文化和产品',
    'video_url': 'https://example.com/company_footage.mp4',
    'mode': 'async',
    'output_path': '/custom/path/output.mp4',
    'preferences': {
        'video_type': 'brand_promo',
        'style': 'professional',
        'music_preference': 'inspirational',
        'text_style': 'elegant'
    },
    'resources': {
        'images': [{
            'id': 'logo',
            'source': 'https://example.com/company_logo.png'
        }]
    }
}

result = interface.create_video(request)
```

## 执行脚本格式

AuraRender 生成的执行脚本是一个详细的JSON文档，包含所有视频制作指令：

```json
{
  "version": "1.0",
  "project": {
    "id": "aura_12345",
    "type": "product_ad",
    "style": {
      "category": "futuristic",
      "subtype": "tech"
    },
    "duration": 30,
    "resolution": "1920x1080",
    "fps": 30
  },
  "resources": {
    "videos": [...],
    "images": [...],
    "audio": [...]
  },
  "timeline": [
    {
      "start": 0,
      "end": 5,
      "layers": [...]
    }
  ],
  "global_effects": {...}
}
```

## 风格系统

### 主要风格类别
- **写实系** (`realistic`) - 自然、真实、纪实
- **艺术系** (`artistic`) - 创意、抽象、唯美
- **设计系** (`design`) - 简约、现代、极简
- **卡通系** (`cartoon`) - 动画、可爱、二次元
- **未来系** (`futuristic`) - 科技、赛博朋克、科幻

## AI资源生成

AuraRender 集成了多种AI生成能力：

### 1. 图片生成
```python
resources = {
    'images': [{
        'id': 'hero_image',
        'source': 'ai_generated',
        'params': {
            'model': 'wanx-v1',
            'prompt': '未来科技风格的智能手表',
            'resolution': '1920x1080'
        }
    }]
}
```

### 2. 视频生成
```python
resources = {
    'videos': [{
        'id': 'intro_video',
        'source': 'ai_generated',
        'params': {
            'model': 'animate_diff',
            'prompt': '产品360度旋转展示',
            'duration': 5
        }
    }]
}
```

### 3. 音频生成
```python
resources = {
    'audio': [{
        'id': 'background_music',
        'source': 'ai_generated',
        'params': {
            'model': 'musicgen',
            'style': 'cinematic',
            'duration': 30
        }
    }]
}
```

## 最佳实践

### 1. 自然语言描述技巧
- 明确说明视频时长
- 描述想要的风格和氛围
- 说明主要内容和结构
- 提及目标受众

**好的例子**：
```
"制作一个60秒的产品介绍视频，前10秒展示logo和品牌理念，
中间40秒详细介绍产品的三个核心功能，最后10秒展示购买信息。
整体风格要现代科技感，配上动感的背景音乐。"
```

### 2. 资源准备
- 提供高质量的原始素材
- 图片建议使用PNG格式
- 视频建议使用MP4格式
- 确保资源URL可访问

### 3. 性能优化
- 长视频使用异步模式
- 合理设置输出分辨率
- 避免过多的特效叠加

## 故障排除

### 常见问题

1. **生成失败**
   - 检查natural_language是否清晰
   - 确认资源URL是否有效
   - 查看生成的脚本是否合理

2. **效果不理想**
   - 尝试更详细的描述
   - 指定具体的视频类型
   - 调整风格偏好

3. **资源加载失败**
   - 确认网络连接
   - 检查URL格式
   - 尝试本地文件路径

## 进阶功能

### 1. 自定义执行脚本
```python
# 直接创建和执行脚本
script = {
    'version': '1.0',
    'project': {...},
    'resources': {...},
    'timeline': [...],
    'global_effects': {...}
}

interface = AuraRenderInterface()
result = interface.create_video_from_script(script)
```

### 2. 批量生成
```python
# 批量生成不同风格的视频
styles = ['modern', 'vintage', 'artistic']
for style in styles:
    result = create_aura_video(
        natural_language="产品介绍",
        preferences={'style': style}
    )
```

### 3. 模板定制
可以通过继承BaseVideoTemplate创建自定义视频类型模板。

## 示例项目

查看 `test_aura_render.py` 获取完整的使用示例。

## 总结

AuraRender 通过智能编排和机械执行的分离，实现了：
- 高度的可控性和可预测性
- 灵活的视频类型支持
- 强大的AI生成能力集成
- 专业的视频制作效果

让每个人都能轻松创作专业级的视频内容！
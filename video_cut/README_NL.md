# 自然语言视频剪辑系统

## 概述

本系统支持用户通过自然语言描述来生成专业的视频剪辑时间轴，并自动执行视频剪辑操作。系统集成了AI语言理解、智能时间轴生成和自动化视频编辑功能。

## 核心功能

### 1. 自然语言理解
- 支持中文自然语言输入
- 自动提取视频结构、时长、特效、转场等信息
- 智能理解用户意图并转换为技术参数

### 2. 时间轴生成
- 根据描述自动分配时间片段
- 智能添加特效和转场效果
- 支持多轨道编辑（视频、音频、文字）

### 3. 视频剪辑执行
- 自动应用特效和滤镜
- 支持多种转场效果
- 文字动画和字幕处理
- 音频混合和处理

## 快速开始

### 安装依赖
```bash
pip install dashscope moviepy click
```

### 基本使用

1. **生成时间轴**
```bash
python main_nl_processor.py generate -t "制作一个1分钟的产品介绍视频，开头展示logo"
```

2. **执行剪辑**
```bash
python main_nl_processor.py edit -t output/generated_timeline.json -o output/video.mp4
```

3. **一键生成**
```bash
python main_nl_processor.py quick -t "创建30秒的社交媒体广告"
```

## 使用示例

### 示例1：产品介绍视频
```bash
python main_nl_processor.py generate -t "我想做一个2分钟的智能手表产品介绍视频。开头5秒展示公司logo，要有光晕特效。然后用20秒介绍产品外观，画面要360度旋转展示。接下来展示核心功能，每个功能10秒，配上说明文字。最后展示购买信息。"
```

### 示例2：Vlog视频
```bash
python main_nl_processor.py generate -t "制作一个3分钟的旅行vlog，包含城市风光、美食探店、人文体验三个部分，要有轻松的背景音乐和手写风格字幕" -p vlog
```

### 示例3：教育视频
```bash
python main_nl_processor.py generate -t "创建一个5分钟的Python编程教学视频，分为概念介绍、代码演示、实战练习三个章节，需要清晰的步骤说明和代码高亮" -p education
```

## 支持的特效

### 视频特效
- **模糊** (blur) - 背景虚化、焦点效果
- **光晕** (glow) - 增加高级感、突出重点
- **粒子** (particle) - 动感效果、科技感
- **缩放** (zoom) - 聚焦、强调
- **旋转** (rotate) - 动态展示
- **震动** (shake) - 冲击力、紧张感
- **色彩校正** (color_correct) - 调色、风格化

### 转场效果
- **淡入淡出** - 柔和过渡
- **快切** - 快节奏切换
- **滑动** - 平滑过渡
- **缩放** - 聚焦转场
- **交叉淡化** - 叠化效果

### 文字动画
- **打字机效果** - 逐字显示
- **滑入** - 从侧面进入
- **淡入** - 渐显效果
- **弹跳** - 活泼动画

## 高级功能

### 使用模板
系统提供多种预设模板：
- `vlog` - 适合旅行、生活记录
- `product` - 产品展示、广告
- `education` - 教学、科普视频
- `commercial` - 商业广告
- `social_media` - 短视频平台

```bash
python main_nl_processor.py generate -t "你的描述" -p vlog
```

### 批量处理
从文件读取描述：
```bash
python main_nl_processor.py generate -f descriptions.txt
```

### 预览模式
只生成前30秒预览：
```bash
python main_nl_processor.py edit --preview
```

## 时间轴格式

生成的时间轴遵循标准JSON格式，包含：
- 视频基本信息（时长、分辨率、帧率）
- 多轨道配置（视频、音频、文字）
- 特效和转场设置
- 时间精确控制

示例结构：
```json
{
  "version": "1.0",
  "timeline": {
    "duration": 60,
    "fps": 30,
    "resolution": {"width": 1920, "height": 1080},
    "tracks": [
      {
        "type": "video",
        "name": "主视频",
        "clips": [...]
      }
    ]
  }
}
```

## 最佳实践

### 描述技巧
1. **明确时间分配**：指定每个部分的时长
2. **详细说明效果**：描述想要的视觉效果
3. **指定转场方式**：说明片段之间如何过渡
4. **描述情感基调**：如"温馨"、"动感"、"专业"

### 资源准备
1. 将视频素材放在 `resources/` 目录
2. 音频文件支持 mp3、wav 格式
3. 图片支持 jpg、png 格式

### 性能优化
1. 长视频建议分段处理
2. 使用预览模式快速验证效果
3. 合理使用特效避免过度渲染

## 常见问题

### Q: 如何添加自定义特效？
A: 在 `video_editor.py` 中的 `effect_mapping` 添加新的特效函数。

### Q: 支持哪些视频格式？
A: 支持 mp4、avi、mov 等常见格式。

### Q: 如何调整生成的时间轴？
A: 可以手动编辑生成的 JSON 文件，然后重新执行剪辑。

## 扩展开发

### 添加新模板
在 `timeline_generator.py` 中实现新的模板方法：
```python
def _create_your_template(self, config: Dict) -> List[Dict]:
    # 实现你的模板逻辑
    pass
```

### 自定义处理器
继承 `NaturalLanguageProcessor` 类实现自定义逻辑：
```python
class CustomProcessor(NaturalLanguageProcessor):
    def extract_timeline_info(self, text: str) -> Dict:
        # 自定义提取逻辑
        pass
```

## 注意事项

1. 确保设置了 `DASHSCOPE_API_KEY` 环境变量
2. 大文件视频处理需要足够的内存
3. 复杂特效可能需要较长渲染时间

## 更新日志

### v1.0.0
- 初始版本发布
- 支持自然语言生成时间轴
- 基础特效和转场
- 多轨道编辑支持

---

如有问题或建议，欢迎提交 Issue 或 PR！
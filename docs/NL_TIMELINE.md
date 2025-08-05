# 自然语言时间轴生成系统

## 概述

这个系统允许用户通过自然语言描述来生成视频编辑时间轴，无需手动编写复杂的JSON配置。只需要用中文描述您想要的视频效果，系统就会自动生成对应的时间轴结构。

## 功能特性

### 1. 自然语言理解
- **时间识别**: 支持多种时间表达方式（秒、分钟、时间段等）
- **特效识别**: 自动识别转场、淡入淡出、模糊、发光等特效关键词
- **节奏识别**: 理解快节奏、慢节奏、动感等节奏描述
- **颜色主题**: 支持各种颜色主题设定

### 2. 智能时间轴生成
- 自动分配时间段
- 智能添加字幕轨道
- 背景音乐自动配置
- 特效自动应用

## 快速开始

### 基础用法

```python
from video_cut.natural_language_processor import NaturalLanguageProcessor

# 创建处理器
processor = NaturalLanguageProcessor()

# 简单的描述
timeline = processor.process_natural_language("我要给这个视频加上转场特效和字幕")
```

### 运行演示

```bash
# 运行所有演示
python demo_nl_timeline.py --demo all

# 运行特定演示
python demo_nl_timeline.py --demo 1

# 进入交互模式
python demo_nl_timeline.py --interactive
```

## 使用示例

### 示例1: 简单编辑
```
输入: "我要给这个视频加上转场特效和字幕"
输出: 生成包含转场特效和字幕轨道的时间轴
```

### 示例2: 产品宣传视频
```
输入: "制作30秒的产品宣传视频，前5秒展示logo淡入效果，中间20秒介绍产品功能配字幕，最后5秒显示购买信息"
输出: 生成精确时间控制的多轨道时间轴
```

### 示例3: 教育视频
```
输入: "制作1分钟的Python教程，包含代码演示和讲解字幕，使用绿色主题，平缓节奏"
输出: 生成适合教学的时间轴，包含代码展示和字幕轨道
```

## 支持的关键词

### 时间表达
- `X秒`、`X分钟`、`X分X秒`
- `前X秒`、`最后X秒`、`X-Y秒`
- `第X秒开始`

### 特效关键词
- **转场**: 转场、过渡、切换
- **淡入淡出**: 淡入、淡出、渐入、渐出
- **视觉特效**: 模糊、发光、粒子、震动、缩放、旋转
- **字幕**: 字幕、文字、标题

### 节奏关键词
- **快节奏**: 快切12次/分钟，转场0.3秒
- **慢节奏**: 慢切4次/分钟，转场1秒
- **动感**: 添加震动、缩放效果

### 颜色主题
- 支持：绿色、蓝色、红色、黄色、紫色、橙色、金色等

## 高级用法

### 使用接口类
```python
from video_cut.nl_timeline_interface import NLTimelineInterface

interface = NLTimelineInterface()

# 处理用户输入
result = interface.process_user_input(
    "制作30秒的产品视频，加特效和字幕",
    video_path="product.mp4"  # 可选
)

# 结果包含
# - timeline: 生成的时间轴
# - output_path: 保存路径
# - execution_plan: 执行计划
```

### 结合模板使用
```python
# 使用模板+自然语言
result = interface.generate_from_template("product", {
    "description": "30秒的手机宣传，快节奏，科技感",
    "product_name": "SuperPhone",
    "features": ["5G", "AI摄影"]
})
```

## 输出格式

生成的时间轴遵循标准JSON格式：

```json
{
  "version": "1.0",
  "metadata": {
    "title": "视频标题",
    "description": "描述",
    "tags": ["标签"],
    "generated_from": "natural_language"
  },
  "timeline": {
    "duration": 30,
    "fps": 30,
    "resolution": {"width": 1920, "height": 1080},
    "tracks": [
      {
        "type": "video",
        "name": "主视频",
        "clips": [...]
      },
      {
        "type": "text",
        "name": "字幕",
        "clips": [...]
      }
    ]
  }
}
```

## 最佳实践

1. **明确时间**: 尽量指定具体的时间段，如"0-5秒"、"前10秒"
2. **描述结构**: 按时间顺序描述各个部分
3. **指定特效**: 明确说明需要的特效类型
4. **设定主题**: 可以指定颜色主题和节奏风格

## 注意事项

1. 默认视频时长为60秒，除非明确指定
2. 时间段会自动调整以避免重叠
3. 字幕会自动从描述中提取
4. 背景音乐在提到时会自动添加

## 扩展开发

如需添加新的关键词或效果：

1. 在 `EffectKeyword` 枚举中添加新效果
2. 在相应的关键词字典中添加映射
3. 在滤镜转换函数中添加处理逻辑

## 问题排查

- **时间识别错误**: 检查时间表达是否符合支持的格式
- **特效未生效**: 确认使用了支持的特效关键词
- **字幕缺失**: 明确使用"字幕"、"文字"等关键词

## 相关文件

- `video_cut/natural_language_processor.py` - 核心处理器
- `video_cut/nl_timeline_interface.py` - 集成接口
- `test_nl_video_edit.py` - 测试脚本
- `demo_nl_timeline.py` - 演示程序
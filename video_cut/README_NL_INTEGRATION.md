# 自然语言视频剪辑集成指南

## 概述

本文档说明如何在现有的DAG视频剪辑系统中使用自然语言功能。系统现在支持直接输入中文自然语言描述来生成视频剪辑时间轴。

## 新增功能

### 1. 自然语言处理器 (NLProcessor)
- 位置：`video_cut/core/nl_processor.py`
- 功能：将用户的自然语言描述转换为结构化的视频大纲
- 特点：
  - 智能理解视频需求
  - 自动提取关键元素（时长、风格、特效等）
  - 支持风格增强

### 2. 扩展的Controller
- 新增 `nl_generate` 类型支持
- 新方法 `run_nl_generate()` 处理自然语言输入
- 自动将自然语言转换为DAG系统需要的大纲格式

### 3. CLI命令
新增两个命令：
- `nl-generate`: 从自然语言生成视频时间轴
- `nl-examples`: 显示使用示例

## 使用方法

### 1. 命令行使用

#### 直接输入文本
```bash
python -m video_cut.cli.cli nl-generate -t "制作一个1分钟的产品介绍视频"
```

#### 从文件读取
```bash
python -m video_cut.cli.cli nl-generate -f description.txt
```

#### 指定输出路径
```bash
python -m video_cut.cli.cli nl-generate -t "你的描述" -o output/my_timeline.json
```

### 2. 程序化使用

```python
from video_cut.config import DAG, NODES
from video_cut.core.controller import UnifiedController

# 创建控制器
controller = UnifiedController(DAG, NODES)

# 准备输入
user_input = {
    "type": "nl_generate",
    "natural_language": "制作一个30秒的抖音风格美食视频"
}

# 生成时间轴
result = controller.handle_input(user_input)

# 获取最终时间轴
timeline = result['node12']
```

### 3. JSON格式输入

创建一个JSON文件：
```json
{
  "type": "nl_generate",
  "natural_language": "你的视频描述"
}
```

然后使用：
```bash
python -m video_cut.main
```

## 示例

### 示例1：产品介绍视频
```bash
python -m video_cut.cli.cli nl-generate -t "制作一个2分钟的智能手表产品介绍视频。开头5秒展示公司logo，要有光晕特效。然后30秒介绍产品外观，画面要360度旋转展示。接下来展示健康监测、运动追踪、智能提醒三个核心功能，每个功能20秒，配上演示画面和说明文字。最后25秒展示购买信息和优惠活动。整体要科技感十足，配上动感的背景音乐。"
```

### 示例2：教育视频
```bash
python -m video_cut.cli.cli nl-generate -t "创建一个3分钟的'Python入门'教育视频。第一部分30秒介绍什么是Python，用简单的图形动画。第二部分1分钟讲解基础语法，展示代码示例。第三部分1分钟演示一个简单项目。最后30秒总结和推荐学习资源。需要清晰的解说和字幕。"
```

### 示例3：Vlog
```bash
python -m video_cut.cli.cli nl-generate -t "制作一个5分钟的东京旅行vlog。包括：1分钟的城市风光镜头，配上日文标题；2分钟的美食探店，要有特写镜头；1分30秒的文化体验，如茶道或和服；30秒的购物场景。使用轻松愉快的背景音乐，字幕用手写风格。"
```

## 工作流程

1. **自然语言输入** → NLProcessor处理
2. **生成视频大纲** → 作为node1的输入
3. **DAG流程执行** → 依次执行所有节点
4. **生成时间轴** → node12输出最终的timeline.json

## 生成的大纲格式

NLProcessor会生成类似这样的大纲：

```
这是一个[产品介绍]的[商业]视频，时长60秒，面向[消费者]，风格[科技感、专业]。

内容结构：
- 第1部分（5秒）：展示公司logo，光晕特效淡入
- 第2部分（20秒）：产品外观展示，360度旋转镜头
- 第3部分（20秒）：功能演示，分屏展示三个核心功能
- 第4部分（15秒）：购买信息，二维码和优惠信息

音频：电子音乐，节奏感强
字幕：简洁的说明文字，白色字体
品牌：logo始终显示在右上角
```

## 高级用法

### 1. 批量处理
创建一个包含多个描述的文件，每行一个描述：
```bash
python -m video_cut.cli.cli nl-generate -f batch_descriptions.txt
```

### 2. 结合修改功能
先生成，然后修改特定节点：
```bash
# 生成初始时间轴
python -m video_cut.cli.cli nl-generate -t "你的描述"

# 修改特定节点
python -m video_cut.cli.cli modify --input-file modify.json
```

### 3. 自定义处理
继承NLProcessor类来自定义处理逻辑：
```python
from video_cut.core.nl_processor import NLProcessor

class CustomNLProcessor(NLProcessor):
    def process_natural_language(self, user_input: str) -> str:
        # 自定义处理逻辑
        pass
```

## 注意事项

1. **API密钥**：确保设置了`DASHSCOPE_API_KEY`环境变量或在项目根目录有`api_key.txt`文件
2. **描述质量**：越详细的描述生成的效果越好
3. **时长限制**：建议视频时长在30秒到10分钟之间
4. **中文支持**：系统优化了中文处理，建议使用中文描述

## 常见问题

### Q: 如何查看生成的大纲？
A: 运行命令时会显示生成的大纲摘要，完整大纲保存在输出JSON的node1中。

### Q: 可以指定特定的视频风格吗？
A: 可以，在描述中明确指出风格，如"抖音风格"、"专业商业"、"温馨家庭"等。

### Q: 支持哪些特效？
A: 支持光晕、模糊、粒子、缩放、旋转、淡入淡出等特效，在描述中提及即可。

### Q: 如何控制视频节奏？
A: 在描述中指定每个部分的时长，系统会据此分配时间。

## 测试

运行测试脚本：
```bash
python video_cut/test_nl.py
```

这将测试：
1. 自然语言处理器功能
2. 完整的生成流程
3. CLI集成

## 更新日志

- v1.0.0: 初始版本，支持基础的自然语言转换
- 集成到现有DAG系统
- 支持命令行和程序化使用
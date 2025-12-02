# AI Movie Clip - 智能视频剪辑系统

一个基于人工智能的自动视频剪辑系统，能够自动分析视频内容并根据用户需求生成编辑后的视频。

## 📚 文档

- [API文档](docs/API.md) - 完整的API接口说明
- [前端接口指南](docs/FRONTEND_API.md) - 前端集成指南
- [架构设计](docs/ARCHITECTURE.md) - 系统架构设计文档
- [快速入门](docs/QUICK_START.md) - 快速上手指南
- [自然语言编辑](docs/NL_VIDEO_EDIT.md) - 自然语言视频编辑功能
- [MCP服务](docs/MCP_SERVICE.md) - Model Context Protocol服务说明

## 🔗 相关项目

- [Aura Render](https://github.com/LumingMelody/aura_render) - 相关渲染项目

## 功能特性

- 🎬 **视频自动分析**：使用CV和ML模型分析视频内容
- 🎨 **多样化模板**：支持多种视频风格模板（社交媒体、商业、教育等）
- 🤖 **AI内容生成**：集成文本生成、图像生成和语音合成
- 🎭 **特效和转场**：丰富的视频效果和转场动画
- 🚀 **API服务**：提供FastAPI接口，支持批处理
- 🔌 **MCP集成**：支持Model Context Protocol扩展

## 快速开始

### 环境要求

- Python 3.8+
- FFmpeg（用于视频处理）
- CUDA（可选，用于GPU加速）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/LumingMelody/Ai-movie-clip.git
cd Ai-movie-clip
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

复制环境变量模板并填写您的配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的API密钥：
```env
# AI Model API Keys
DASHSCOPE_API_KEY=your_dashscope_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# OSS Configuration (Alibaba Cloud)
OSS_ACCESS_KEY_ID=your_oss_access_key_id_here
OSS_ACCESS_KEY_SECRET=your_oss_access_key_secret_here
OSS_BUCKET_NAME=your_bucket_name_here
```

### 获取API密钥

- **DashScope API Key**: 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
- **OpenAI API Key**: 访问 [OpenAI平台](https://platform.openai.com/api-keys)
- **OSS配置**: 访问 [阿里云OSS控制台](https://oss.console.aliyun.com/)

## Coze 集成功能

本系统集成了 Coze 数字人和图片插入功能，为视频制作提供更丰富的素材和效果。

### 🎭 数字人功能
- 基于 Coze API 的数字人视频生成
- 支持多种数字人模型和动作
- 文本驱动的数字人表演生成

### 🖼️ 图片插入功能  
- 智能图片素材插入
- 自动场景匹配和位置优化
- 支持多种图片格式和效果

### ⚙️ 配置要求

使用 Coze 相关功能需要：

1. **搭建 Coze Workflow**
   - 在 [Coze 平台](https://www.coze.com/) 创建并配置相应的工作流
   - 获取 Workflow API 密钥并配置到系统中

2. **下载素材包**
   - 素材下载链接：[https://pan.quark.cn/s/5a16054e18eb](https://pan.quark.cn/s/5a16054e18eb)
   - 将素材包解压到项目的 `resources/` 目录下
   - 确保素材路径配置正确

3. **环境配置**
   ```env
   # 添加到 .env 文件
   COZE_API_KEY=your_coze_api_key_here
   COZE_WORKFLOW_ID=your_workflow_id_here
   ```

### 📋 使用示例

```python
# 使用数字人功能
from core.cliptemplate.coze.video_digital_human_easy import VideoDigitalHumanEasy

# 生成数字人视频
digital_human = VideoDigitalHumanEasy()
result = digital_human.generate_video(
    text="你好，欢迎使用AI视频剪辑系统",
    avatar_id="your_avatar_id"
)

# 使用图片插入功能
from core.cliptemplate.coze.video_dgh_img_insert import VideoDghImgInsert

# 插入图片到视频
img_inserter = VideoDghImgInsert()
result = img_inserter.insert_image(
    video_path="path/to/video.mp4",
    image_path="path/to/image.jpg",
    position="center"
)
```

## 使用方法

### 命令行工具

```bash
# 分析视频
python main.py analyze video.mp4 --output analysis.json

# 自动剪辑视频
python main.py edit video.mp4 --duration 30 --style "抖音风"

# 查看更多选项
python main.py --help
```

### Web API服务

```bash
# 启动FastAPI服务器
python app.py
# 或
uvicorn app:app --reload

# 访问API文档
# http://localhost:8000/docs
```

### API示例

```python
import requests

# 分析视频
response = requests.post(
    "http://localhost:8000/analyze",
    files={"file": open("video.mp4", "rb")},
    data={"duration": 30}
)

# 生成编辑视频
response = requests.post(
    "http://localhost:8000/edit",
    json={
        "video_path": "path/to/video.mp4",
        "template": "douyin",
        "duration": 30
    }
)
```

## 项目结构

```
Ai-movie-clip/
├── core/                  # 核心功能模块
│   ├── orchestrator/     # 工作流编排
│   ├── analyzer/         # 视频分析
│   ├── ai/              # AI模型集成
│   ├── clipeffects/     # 视频特效
│   ├── cliptransition/  # 转场效果
│   ├── clipgenerate/    # AI内容生成
│   └── cliptemplate/    # 视频模板
├── templates/           # Jinja2模板文件
├── config/             # 配置文件
├── main.py            # CLI入口
├── app.py             # API服务器
└── requirements.txt   # 依赖列表
```

## 高级功能

### 自定义模板

在 `templates/` 目录下创建新的模板文件：

```jinja2
# templates/custom/my_template.j2
产品名称：{{ product_name }}
特点：{{ features }}
价格：{{ price }}
```

### 扩展AI模型

在 `core/ai/ai_model_caller.py` 中添加新的模型：

```python
def call_custom_model(prompt):
    # 实现您的模型调用逻辑
    pass
```

## 常见问题

### Q: 如何处理大视频文件？
A: 系统会自动进行分片处理，您可以在配置中调整分片大小。

### Q: 支持哪些视频格式？
A: 支持 MP4、AVI、MOV、MKV 等常见格式。

### Q: 如何提高处理速度？
A: 使用GPU加速，或调整 `config.yaml` 中的并发设置。

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 作者：LumingMelody
- 项目链接：[https://github.com/LumingMelody/Ai-movie-clip](https://github.com/LumingMelody/Ai-movie-clip)

## 致谢

- 感谢阿里云DashScope提供的AI能力
- 感谢OpenAI提供的语言模型

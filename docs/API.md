# FastAPI完整接口文档

## 📊 接口概览
本系统包含**27个主要接口**，分为以下6大类别：
- 🎬 **视频生成与编辑接口**（16个）
- 📝 **文本生成接口**（2个）
- 🖼️ **图像分析接口**（1个）
- 🔧 **系统管理接口**（4个）
- 📤 **文件上传接口**（1个）
- 📊 **任务查询接口**（1个）
- 🎯 **通用批量生成接口**（2个）

---

## 🔧 1. 基础服务接口

### 1.1 文件上传
- **路由**: `POST /upload`
- **执行函数**: `upload_file`
- **参数**:
  - `file: UploadFile` - 上传的文件
- **功能**: 上传文件到服务器，返回标准化文件信息
- **返回格式**:
  ```json
  {
    "code": 0,
    "data": {
      "filename": "文件名",
      "url": "访问URL",
      "warehouse_path": "仓库路径",
      "full_path": "完整路径",
      "file_size": "文件大小",
      "upload_success": true
    },
    "msg": ""
  }
  ```

### 1.2 任务结果查询
- **路由**: `GET /get-result/{task_id}`
- **执行函数**: `get_task_result_with_oss_support`
- **参数**:
  - `task_id: str` - 任务ID（路径参数）
  - `remove: bool` - 是否移除结果（默认false）
- **功能**: 查询异步任务执行结果，支持OSS云存储和本地存储

---

## 🎬 2. 视频生成与编辑接口

### 2.1 视频广告生成
- **路由**: `POST /video/advertisement`
- **执行函数**: `get_video_advertisement`
- **参数**:
  - `company_name: str` - 公司名称
  - `service: str` - 服务内容
  - `topic: str` - 主题
  - `tenant_id: str` - 租户ID
  - `content: Optional[str]` - 内容（可选）
  - `need_change: bool` - 是否需要变更（默认false）
  - `categoryId: str` - 分类ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成企业广告视频
- **支持模式**: 同步/异步，云端上传

### 2.2 大字报风格视频
- **路由**: `POST /video/big-word`
- **执行函数**: `get_big_word`
- **参数**:
  - `company_name: str` - 公司名称
  - `title: str` - 标题
  - `product: str` - 产品
  - `description: str` - 描述
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `content: Optional[str]` - 内容（可选）
  - `id: Optional[str]` - 业务ID
- **功能**: 生成大字报风格的宣传视频

### 2.3 猫咪表情包视频
- **路由**: `POST /video/catmeme`
- **执行函数**: `get_video_catmeme`
- **参数**:
  - `author: str` - 作者
  - `title: str` - 标题
  - `content: Optional[str]` - 内容（可选）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成猫咪表情包风格视频

### 2.4 点击式视频
- **路由**: `POST /video/clicktype`
- **执行函数**: `get_video_clicktype`
- **参数**:
  - `title: str` - 标题
  - `content: Optional[str]` - 内容（可选）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成点击式交互视频

### 2.5 服装展示视频（不同场景）
- **路由**: `POST /video/clothes-different-scene`
- **执行函数**: `get_video_clothes_diffrent_scene`
- **参数**:
  - `has_figure: bool` - 是否有人物
  - `clothesurl: str` - 服装图片URL
  - `description: str` - 描述
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `is_down: bool` - 是否下载（默认true）
  - `id: Optional[str]` - 业务ID
- **功能**: 生成不同场景的服装展示视频

### 2.6 数字人图片插入视频
- **路由**: `POST /video/dgh-img-insert`
- **执行函数**: `get_video_dgh_img_insert`
- **参数**:
  - `title: str` - 标题
  - `video_file_path: str` - 视频文件路径
  - `content: Optional[str]` - 内容（可选）
  - `need_change: bool` - 是否需要变更（默认false）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 在视频中插入数字人图片

### 2.7 数字人视频片段
- **路由**: `POST /video/digital-human-clips`
- **执行函数**: `get_video_digital_huamn_clips`
- **参数**:
  - `video_file_path: str` - 视频文件路径
  - `topic: str` - 主题
  - `audio_path: str` - 音频路径
  - `content: Optional[str]` - 内容（可选）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成数字人视频片段

### 2.8 简易数字人视频
- **路由**: `POST /video/digital-human-easy`
- **执行函数**: `get_video_digital_huamn_easy_local`
- **参数**:
  - `video_input/file_path/video_url: str` - 视频输入（支持多种参数名）
  - `topic: str` - 主题
  - `content: Optional[str]` - 内容（可选）
  - `audio_input/audio_url/audio_path: str` - 音频输入（可选）
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成简易数字人视频，支持多种参数格式
- **特色**: 支持灵活的JSON参数格式

### 2.9 数字人视频生成（高级）
- **路由**: `POST /video/digital-human-generation`
- **执行函数**: `process_single_video_by_url`
- **参数**:
  - `video_url: Optional[str]` - 视频URL
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 高级数字人视频生成，包含以下流程：
  1. 从OSS自动选择或使用指定的视频文件
  2. 随机截取视频片段
  3. 提取音频并进行语音识别(ASR)
  4. 生成新的语音(TTS)
  5. 创建数字人视频
  6. 将处理后的片段替换回原视频
  7. 上传到OSS并返回结果

### 2.10 煽动性视频
- **路由**: `POST /video/incitement`
- **执行函数**: `get_video_incitment`
- **参数**:
  - `title: str` - 标题
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成煽动性风格视频

### 2.11 国学风格视频
- **路由**: `POST /video/sinology`
- **执行函数**: `get_video_sinology`
- **参数**:
  - `title: str` - 标题
  - `content: Optional[str]` - 内容（可选）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成国学风格视频

### 2.12 火柴人动画视频
- **路由**: `POST /video/stickman`
- **执行函数**: `get_video_stickman`
- **参数**:
  - `author: str` - 作者
  - `title: str` - 标题
  - `content: Optional[str]` - 内容（可选）
  - `lift_text: str` - 提升文本（默认"科普动画"）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成火柴人风格的科普动画

### 2.13 快速换装视频
- **路由**: `POST /video/clothes-fast-change`
- **执行函数**: `get_videos_clothes_fast_change`
- **参数**:
  - `has_figure: bool` - 是否有人物
  - `clothesurl: str` - 服装图片URL
  - `description: str` - 描述
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `is_down: bool` - 是否下载（默认true）
  - `id: Optional[str]` - 业务ID
- **功能**: 生成快速换装展示视频

### 2.14 随机视频生成
- **路由**: `POST /video/random`
- **执行函数**: `get_video_random`
- **参数**:
  - `enterprise: str` - 企业名称
  - `product: str` - 产品
  - `description: str` - 描述
  - `tenant_id: str` - 租户ID
  - `categoryId: str` - 分类ID
  - `id: Optional[str]` - 业务ID
- **功能**: 随机选择一种视频生成算法（从7种算法中随机选择）

### 2.15 智能视频剪辑
- **路由**: `POST /video/clip`
- **执行函数**: `get_smart_clip_video`
- **参数**:
  - `input_source: Union[str, List[str]]` - 输入源（文件路径或路径列表）
  - `is_directory: bool` - 是否为目录（默认true）
  - `company_name: str` - 公司名称（默认"测试公司"）
  - `text_list: Optional[List[str]]` - 文字内容列表（随机剪辑时使用）
  - `audio_durations: Optional[List[float]]` - 音频时长列表（随机剪辑时使用）
  - `clip_mode: str` - 剪辑模式："random"(随机) 或 "smart"(智能)，默认"random"
  - `target_resolution: tuple` - 目标分辨率（默认1920x1080）
  - `tenant_id: Optional[str]` - 租户ID
  - `task_id: Optional[str]` - 任务ID
  - `id: Optional[str]` - 业务ID
- **功能**: 智能或随机剪辑视频，支持多文件批量处理

### 2.16 视频编辑主接口
- **路由**: `POST /video/edit`
- **执行函数**: `get_video_edit_simple`
- **参数**:
  - `video_sources: Union[str, List[str]]` - 视频源文件路径（支持单个文件或文件列表）
  - `tenant_id: Optional[str]` - 租户ID
  - `task_id: Optional[str]` - 任务ID
  - `id: Optional[str]` - 业务ID
  - `duration: int` - 目标时长秒数（默认30）
  - `style: str` - 目标风格（默认"抖音风"）
  - `purpose: str` - 使用目的（默认"社交媒体"）
  - `use_local_ai: bool` - 是否使用本地AI（默认true）
  - `api_key: Optional[str]` - AI模型API密钥
- **功能**: 支持多文件的智能视频编辑，使用VideoEditingOrchestrator

---

## 📝 3. 文本生成接口

### 3.1 行业文本生成
- **路由**: `POST /text/industry`
- **执行函数**: `get_text_industry`
- **参数**:
  - `industry: str` - 行业类型
  - `is_hot: bool` - 是否热门（默认true）
  - `content: Optional[str]` - 内容（可选）
  - `categoryId: str` - 分类ID
  - `tenant_id: str` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 生成特定行业的文本内容
- **支持模式**: 同步/异步，任务状态更新

### 3.2 文案生成器
- **路由**: `POST /copy/generate`
- **执行函数**: `get_copy_generator`
- **参数**:
  - `category: str` - 文案类型（如ecom、education、entertainment）
  - `style: str` - 文案风格（如suspense、direct、story）
  - `input_data: Dict[str, Any]` - 输入数据（包含商品名称、亮点、适用人群等）
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 根据类型和风格生成营销文案
- **支持模式**: 同步/异步，任务状态更新

---

## 🖼️ 4. 图像分析接口

### 4.1 封面分析
- **路由**: `POST /cover/analyze`
- **执行函数**: `analyze_cover_endpoint`
- **参数**:
  - `image: str` - 图片数据（base64编码）或URL
  - `is_url: bool` - 是否为URL（默认false）
  - `platform: str` - 平台类型（默认"douyin"，可选"xiaohongshu"、"shipinhao"）
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 分析封面图片的质量和特征
- **支持模式**: 同步/异步，任务状态更新

---

## ⚙️ 5. 系统管理接口

### 5.1 更新产品配置
- **路由**: `PUT /api/product`
- **执行函数**: `update_product_info`
- **参数**:
  - `product_name: Optional[str]` - 产品名称
  - `price: Optional[float]` - 价格
  - `features: Optional[str]` - 特性
  - `discount: Optional[str]` - 折扣
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 更新产品相关配置信息
- **支持**: 任务状态更新

### 5.2 更新语音配置
- **路由**: `PUT /api/voice/config`
- **执行函数**: `update_voice_config`
- **参数**:
  - `gender: Optional[str]` - 性别（female/male/default）
  - `speed: Optional[float]` - 语速（0.5-2.0）
  - `pitch: Optional[float]` - 音调（0.5-2.0）
  - `voice: Optional[str]` - 语音类型
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 更新语音合成相关配置
- **支持**: 任务状态更新

### 5.3 启动Socket服务器
- **路由**: `POST /api/server/start`
- **执行函数**: `start_socket_server`
- **参数**:
  - `host: str` - 主机地址（默认"0.0.0.0"）
  - `port: int` - 端口号（默认8888）
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 启动WebSocket服务器
- **支持**: 任务状态更新

### 5.4 停止Socket服务器
- **路由**: `POST /api/server/stop`
- **执行函数**: `stop_socket_server`
- **参数**:
  - `tenant_id: Optional[str]` - 租户ID
  - `id: Optional[str]` - 业务ID
- **功能**: 停止WebSocket服务器
- **支持**: 任务状态更新

---

## 🎯 6. 通用参数说明

### 6.1 执行模式参数
- `mode: str` - 大部分接口支持的执行模式
  - `"sync"`: 同步执行，直接返回结果
  - `"async"`: 异步执行，返回task_id，需要通过查询接口获取结果

### 6.2 云端集成参数
- `tenant_id: str` - 租户ID，提供时自动启用OSS云存储上传
- `task_id: str` - 任务ID，用于追踪任务状态
- `id: str` - 业务ID，用于业务系统状态更新

### 6.3 路径处理支持
系统支持多种路径格式：
- **绝对路径**: `/home/user/video.mp4` - 直接使用
- **相对路径**: `videos/video.mp4` - 在多个目录中搜索
- **上传路径**: `uploads/video.mp4` - 转换为uploads目录路径
- **在线URL**: `https://example.com/video.mp4` - 作为网络资源处理

### 6.4 标准响应格式
```json
{
  "status": "completed/failed/submitted",
  "task_id": "任务ID",
  "tenant_id": "租户ID",
  "business_id": "业务ID",
  "videoPath": "相对路径",
  "oss_url": "云端访问URL（如果启用）",
  "processing_time": "处理时间（秒）",
  "function_name": "执行的函数名",
  "enhanced": true
}
```

---

## 🏗️ 7. 系统架构特点

### 7.1 核心特性
1. **异步任务处理**: 支持大任务的异步执行和状态查询
2. **云端集成**: 自动上传结果到阿里云OSS
3. **多路径支持**: 灵活的文件路径处理机制
4. **错误恢复**: 完善的错误处理和状态更新
5. **资源管理**: 自动清理临时文件和资源
6. **多租户支持**: 完整的租户隔离和业务ID追踪

### 7.2 任务状态管理
- **状态值**:
  - `"0"`: 运行中
  - `"1"`: 完成
  - `"2"`: 失败
- **自动状态更新**: 所有接口都支持任务状态的自动更新
- **业务ID追踪**: 支持业务系统的状态同步

### 7.3 文件处理能力
- **支持格式**: 
  - 视频: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm
  - 图片: .jpg, .jpeg, .png, .gif, .bmp
  - 音频: .mp3, .wav, .aac, .m4a
- **路径解析**: 智能路径解析和文件查找
- **云端存储**: 自动OSS上传和资源管理

### 7.4 集成能力
- **AI模型**: 支持本地AI和在线AI模型
- **视频处理**: 集成MoviePy、FFmpeg等视频处理库
- **云服务**: 阿里云OSS集成
- **任务调度**: 多线程异步任务处理

这是一个功能完整的AI视频处理和内容生成平台，特别适合需要批量视频处理、自动化内容生成和多租户服务的场景。
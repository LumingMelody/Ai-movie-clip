### 1. **MCP_Enh-generate_clicktype_video**
- **功能**: 生成点击类型视频
- **参数**:
  - `title`: 标题
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 2. **MCP_Enh-generate_stickman_video**
- **功能**: 生成火柴人视频
- **参数**:
  - `author`: 作者
  - `title`: 标题
  - `content` (可选): 内容
  - `lift_text` (可选, 默认为 `科普动画`): 提升文本
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 3. **MCP_Enh-generate_industry_text**
- **功能**: 生成行业相关文本
- **参数**:
  - `industry`: 行业名称
  - `is_hot` (可选, 默认为 `true`): 是否为热门
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 文本生成结果的字符串描述

### 4. **MCP_Enh-generate_clothes_change_video**
- **功能**: 生成服装快速变换视频
- **参数**:
  - `has_figure`: 是否有人物
  - `clothesurl`: 服装URL
  - `description`: 描述
  - `is_down` (可选, 默认为 `true`): 是否向下
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 5. **MCP_Enh-generate_video_advertisement**
- **功能**: 生成视频广告
- **参数**:
  - `company_name`: 公司名称
  - `service`: 服务类型
  - `topic`: 主题
  - `content` (可选): 内容描述
  - `need_change` (可选, 默认为 `false`): 是否需要变更
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 6. **MCP_Enh-generate_big_word_video**
- **功能**: 生成大字视频
- **参数**:
  - `company_name`: 公司名称
  - `title`: 标题
  - `product`: 产品
  - `description`: 描述
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 7. **MCP_Enh-generate_catmeme_video**
- **功能**: 生成猫咪表情包视频
- **参数**:
  - `author`: 作者
  - `title`: 标题
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 8. **MCP_Enh-generate_digital_human_video**
- **功能**: 生成数字人视频
- **参数**:
  - `file_path`: 视频文件路径
  - `topic`: 主题
  - `audio_url`: 音频URL
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 9. **MCP_Enh-smart_video_clip**
- **功能**: 智能视频剪辑
- **参数**:
  - `input_source`: 输入视频源（文件路径或目录）
  - `clip_mode` (可选, 默认为 `smart`): 剪辑模式（`smart` 智能，`random` 随机）
  - `company_name` (可选, 默认为 `测试公司`): 公司名称
  - `audio_durations` (可选, 默认为 `3.0,4.0,2.5,3.5,5.0`): 音频时长列表（逗号分隔）
  - `target_width` (可选, 默认为 `1920`): 目标宽度
  - `target_height` (可选, 默认为 `1080`): 目标高度
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频剪辑结果的字符串描述

### 10. **MCP_Enh-generate_video_advertisement_enhance**
- **功能**: 生成增强版视频广告
- **参数**:
  - `company_name`: 公司名称
  - `service`: 服务类型
  - `topic`: 主题
  - `content` (可选): 内容描述
  - `need_change` (可选, 默认为 `false`): 是否需要变更
  - `add_digital_host` (可选, 默认为 `true`): 是否添加数字主持人
  - `use_temp_materials` (可选, 默认为 `false`): 是否使用临时素材
  - `clip_mode` (可选, 默认为 `true`): 剪辑模式
  - `upload_digital_host` (可选, 默认为 `false`): 是否上传数字主持人
  - `moderator_source` (可选): 主持人素材源
  - `enterprise_source` (可选): 企业素材源
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 11. **MCP_Enh-generate_dgh_img_insert_video**
- **功能**: 生成数字人图片插入视频
- **参数**:
  - `title`: 标题
  - `video_file_path`: 视频文件路径
  - `content` (可选): 内容
  - `need_change` (可选, 默认为 `false`): 是否需要变更
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 12. **MCP_Enh-generate_digital_human_clips_video**
- **功能**: 生成数字人剪辑视频
- **参数**:
  - `video_file_path`: 视频文件路径
  - `topic`: 主题
  - `audio_path`: 音频路径
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 13. **MCP_Enh-generate_incitement_video**
- **功能**: 生成煽动类视频
- **参数**:
  - `title`: 标题
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 14. **MCP_Enh-generate_sinology_video**
- **功能**: 生成国学视频
- **参数**:
  - `title`: 标题
  - `content` (可选): 内容
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 15. **MCP_Enh-generate_clothes_different_scene_video**
- **功能**: 生成服装不同场景视频
- **参数**:
  - `has_figure`: 是否有人物
  - `clothesurl`: 服装URL
  - `description`: 描述
  - `is_down` (可选, 默认为 `true`): 是否向下
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 16. **MCP_Enh-generate_random_video**
- **功能**: 生成随机视频（从多种类型中随机选择）
- **参数**:
  - `enterprise`: 企业名称
  - `product`: 产品
  - `description`: 描述
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 视频生成结果的字符串描述

### 17. **MCP_Enh-download_materials**
- **功能**: 下载素材
- **参数**:
  - `api_url` (可选): API地址
  - `download_path` (可选): 下载路径
  - `mode` (可选, 默认为 `async`): 执行模式
- **返回**: 下载结果的字符串描述

### 18. **MCP_Enh-get_task_result**
- **功能**: 获取异步任务结果
- **参数**:
  - `task_id`: 任务ID
  - `remove` (可选, 默认为 `false`): 是否移除结果
- **返回**: 任务结果的字符串描述

### 19. **MCP_Enh-list_active_tasks**
- **功能**: 列出所有活跃的任务
- **参数**: 无
- **返回**: 活跃任务列表的字符串描述

### 20. **MCP_Enh-cleanup_temp_files**
- **功能**: 清理临时文件和目录
- **参数**: 无
- **返回**: 清理结果的字符串描述

### 21. **MCP_Enh-get_server_info**
- **功能**: 获取服务器信息
- **参数**: 无
- **返回**: 服务器信息的字符串描述

如果您有任何具体的需求或想要使用这些工具来生成特定类型的视频，请告诉我详细信息，我会帮您完成。
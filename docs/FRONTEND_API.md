# FastAPI 视频生成接口文档

## 基础信息

### 服务地址
```
http://localhost:8100
```

### 跨域支持
已启用CORS

### 文件访问
- 素材库访问: `http://localhost:8100/warehouse/`
- 上传文件访问: `http://localhost:8100/uploads/`

---

## 1. 文件上传接口

### 接口地址
```
http://localhost:8100/upload
```

### 请求方法
- `POST`

### 请求参数
| 参数名 | 类型 | 是否必填 | 描述 |
|--------|------|----------|------|
| file   | File | 是       | 上传的文件 |

### 请求格式
- `multipart/form-data`

### 示例响应
```json
{
    "filename": "example.mp4",
    "url": "http://localhost:8100/uploads/example.mp4"
}
```

---

## 2. 素材库管理接口

### 接口地址
```
http://localhost:8100/material/all/page
```

### 请求方法
- `GET` / `POST`

### 请求参数
| 参数名    | 类型   | 是否必填 | 描述                     |
|-----------|--------|----------|--------------------------|
| page      | int    | 否       | 页码，默认1              |
| page_size | int    | 否       | 每页大小，默认10，最大100 |
| keyword   | string | 否       | 搜索关键词               |
| path      | string | 否       | 文件路径，默认空         |

### 示例请求
```json
{
    "page": 1,
    "page_size": 20,
    "keyword": "test",
    "path": "videos"
}
```

### 示例响应
```json
{
    "records": [
        {
            "id": "1",
            "name": "example.mp4",
            "type": "file",
            "path": "videos/example.mp4"
        }
    ],
    "total": 50
}
```

---

## 3. 视频生成接口

### 3.1 广告视频生成

#### 接口地址
```
http://localhost:8100/video/advertisement
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名       | 类型    | 是否必填 | 描述     |
|--------------|---------|----------|----------|
| company_name | string  | 是       | 公司名称 |
| service      | string  | 是       | 服务内容 |
| topic        | string  | 是       | 主题     |
| content      | string  | 否       | 内容     |
| need_change  | boolean | 是       | 是否需要变更 |

#### 示例请求
```json
{
    "company_name": "科技公司",
    "service": "AI解决方案",
    "topic": "智能办公",
    "content": "提升工作效率的AI工具",
    "need_change": false
}
```

### 3.2 增强版广告视频生成

#### 接口地址
```
http://localhost:8100/video/advertisement-enhance
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名               | 类型      | 是否必填 | 描述         |
|---------------------|-----------|----------|-------------|
| company_name        | string    | 是       | 公司名称     |
| service             | string    | 是       | 服务内容     |
| topic               | string    | 是       | 主题         |
| content             | string    | 否       | 内容         |
| need_change         | boolean   | 是       | 是否需要变更 |
| add_digital_host    | boolean   | 是       | 添加数字主持人 |
| use_temp_materials  | boolean   | 是       | 使用临时素材 |
| clip_mode           | boolean   | 是       | 剪辑模式     |
| upload_digital_host | boolean   | 是       | 上传数字主持人 |
| moderator_source    | string    | 否       | 主持人来源   |
| enterprise_source   | string[]  | 否       | 企业来源     |

#### 示例请求
```json
{
    "company_name": "科技公司",
    "service": "AI解决方案",
    "topic": "智能办公",
    "content": "提升工作效率的AI工具",
    "need_change": false,
    "add_digital_host": true,
    "use_temp_materials": false,
    "clip_mode": true,
    "upload_digital_host": false,
    "moderator_source": null,
    "enterprise_source": null
}
```

### 3.3 大字视频生成

#### 接口地址
```
http://localhost:8100/video/big-word
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名       | 类型   | 是否必填 | 描述     |
|--------------|--------|----------|----------|
| company_name | string | 是       | 公司名称 |
| title        | string | 是       | 标题     |
| content      | string | 否       | 内容     |

#### 示例请求
```json
{
    "company_name": "科技公司",
    "title": "突破性创新",
    "content": "改变世界的技术"
}
```

### 3.4 猫咪表情包视频生成

#### 接口地址
```
http://localhost:8100/video/catmeme
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名  | 类型   | 是否必填 | 描述 |
|---------|--------|----------|------|
| author  | string | 是       | 作者 |
| title   | string | 是       | 标题 |
| content | string | 否       | 内容 |

#### 示例请求
```json
{
    "author": "创作者",
    "title": "有趣标题",
    "content": "幽默内容"
}
```

### 3.5 点击类型视频生成

#### 接口地址
```
http://localhost:8100/video/clicktype
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名  | 类型   | 是否必填 | 描述 |
|---------|--------|----------|------|
| title   | string | 是       | 标题 |
| content | string | 否       | 内容 |

#### 示例请求
```json
{
    "title": "吸引点击的标题",
    "content": "引人入胜的内容"
}
```

### 3.6 服装不同场景视频生成

#### 接口地址
```
http://localhost:8100/video/clothes-different-scene
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名      | 类型    | 是否必填 | 描述           |
|-------------|---------|----------|---------------|
| has_figure  | boolean | 是       | 是否有人物     |
| clothesurl  | string  | 是       | 服装图片URL    |
| description | string  | 是       | 描述           |
| is_down     | boolean | 否       | 是否向下，默认true |

#### 示例请求
```json
{
    "has_figure": true,
    "clothesurl": "http://example.com/clothes.jpg",
    "description": "时尚服装展示",
    "is_down": true
}
```

### 3.7 服装快速换装视频生成

#### 接口地址
```
http://localhost:8100/video/clothes-fast-change
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名      | 类型    | 是否必填 | 描述           |
|-------------|---------|----------|---------------|
| has_figure  | boolean | 是       | 是否有人物     |
| clothesurl  | string  | 是       | 服装图片URL    |
| description | string  | 是       | 描述           |
| is_down     | boolean | 否       | 是否向下，默认true |

#### 示例请求
```json
{
    "has_figure": true,
    "clothesurl": "http://example.com/clothes.jpg",
    "description": "快速换装展示",
    "is_down": true
}
```

### 3.8 数字人图片插入视频生成

#### 接口地址
```
http://localhost:8100/video/dgh-img-insert
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名          | 类型    | 是否必填 | 描述         |
|-----------------|---------|----------|-------------|
| title           | string  | 是       | 标题         |
| video_file_path | string  | 是       | 视频文件路径 |
| content         | string  | 否       | 内容         |
| need_change     | boolean | 是       | 是否需要变更 |

#### 示例请求
```json
{
    "title": "数字人演示",
    "video_file_path": "uploads/demo.mp4",
    "content": "演示内容",
    "need_change": false
}
```

### 3.9 简易数字人视频生成

#### 接口地址
```
http://localhost:8100/video/digital-human-easy
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名    | 类型   | 是否必填 | 描述      |
|-----------|--------|----------|-----------|
| video_url | string | 是       | 视频URL   |
| topic     | string | 是       | 主题      |
| content   | string | 否       | 内容      |
| audio_url | string | 否       | 音频URL   |

#### 示例请求
```json
{
    "video_url": "http://example.com/video.mp4",
    "topic": "产品介绍",
    "content": "详细介绍内容",
    "audio_url": "http://example.com/audio.mp3"
}
```

### 3.10 煽动类视频生成

#### 接口地址
```
http://localhost:8100/video/incitement
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名 | 类型   | 是否必填 | 描述 |
|--------|--------|----------|------|
| title  | string | 是       | 标题 |

#### 示例请求
```json
{
    "title": "激励标题"
}
```

### 3.11 国学视频生成

#### 接口地址
```
http://localhost:8100/video/sinology
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名  | 类型   | 是否必填 | 描述 |
|---------|--------|----------|------|
| title   | string | 是       | 标题 |
| content | string | 否       | 内容 |

#### 示例请求
```json
{
    "title": "古诗词赏析",
    "content": "诗词内容和解析"
}
```

### 3.12 火柴人视频生成

#### 接口地址
```
http://localhost:8100/video/stickman
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名    | 类型   | 是否必填 | 描述                   |
|-----------|--------|----------|------------------------|
| author    | string | 是       | 作者                   |
| title     | string | 是       | 标题                   |
| content   | string | 否       | 内容                   |
| lift_text | string | 否       | 提升文本，默认"科普动画" |

#### 示例请求
```json
{
    "author": "动画师",
    "title": "科普动画",
    "content": "教育内容",
    "lift_text": "科普动画"
}
```

### 3.13 随机类型视频生成

#### 接口地址
```
http://localhost:8100/video/random
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名      | 类型   | 是否必填 | 描述     |
|-------------|--------|----------|----------|
| enterprise  | string | 是       | 企业名称 |
| product     | string | 是       | 产品名称 |
| description | string | 是       | 描述     |

#### 示例请求
```json
{
    "enterprise": "科技公司",
    "product": "AI助手",
    "description": "智能语音助手产品"
}
```

---

## 4. 文本生成接口

### 4.1 行业文本生成

#### 接口地址
```
http://localhost:8100/text/industry
```

#### 请求方法
- `POST`

#### 请求参数
| 参数名   | 类型    | 是否必填 | 描述             |
|----------|---------|----------|------------------|
| industry | string  | 是       | 行业名称         |
| is_hot   | boolean | 否       | 是否热门，默认true |
| content  | string  | 否       | 内容             |

#### 示例请求
```json
{
    "industry": "人工智能",
    "is_hot": true,
    "content": "AI发展趋势"
}
```

---

## 5. 异步任务管理

### 5.1 异步任务执行
所有视频生成接口都支持异步执行，通过URL参数控制：
- `mode=sync`: 同步执行（等待结果）
- `mode=async` 或不传参数: 异步执行（返回任务ID）

### 5.2 查询异步任务结果

#### 接口地址
```
http://localhost:8100/get-result/{task_id}
```

#### 请求方法
- `GET`

#### 路径参数
| 参数名  | 类型   | 是否必填 | 描述   |
|---------|--------|----------|--------|
| task_id | string | 是       | 任务ID |

#### 响应状态
- `pending`: 任务处理中
- `completed`: 任务完成
- `failed`: 任务失败

#### 示例响应
```json
{
    "status": "completed",
    "result": "videos/output.mp4"
}
```

---

## 6. 通用响应格式

### 成功响应
```json
{
    "videoPath": "http://localhost:8100/warehouse/videos/output.mp4"
}
```

### 异步任务响应
```json
{
    "task_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### 错误响应
```json
{
    "detail": "错误详细信息"
}
```

---

## 7. 注意事项

1. **同步 vs 异步**：
   - 同步模式会等待任务完成后返回结果，有60秒超时限制
   - 异步模式立即返回任务ID，需要轮询查询结果

2. **文件路径**：
   - 上传的文件通过 `/uploads/文件名` 访问
   - 生成的视频通过 `/warehouse/` 路径访问

3. **并发限制**：
   - 任务队列按顺序处理，避免同时提交大量任务

4. **文件格式**：
   - 支持常见的视频、音频、图片格式
   - 建议使用标准格式以确保兼容性

### 注意：localhost:8100 为本地测试环境，具体地址以上线为主
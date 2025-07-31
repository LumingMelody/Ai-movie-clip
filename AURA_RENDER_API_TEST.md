# AuraRender API 测试指南

## 接口地址
`POST http://localhost:8100/video/natural-language-edit`

## 新增参数说明

- `use_aura_render`: 是否使用AuraRender引擎（默认true）
- `video_type`: 指定视频类型（可选，不指定则自动识别）

## 测试示例

### 1. 使用AuraRender创建产品广告
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个30秒的智能手表产品广告，展示健康监测功能和时尚外观，要有科技感",
    "video_url": "https://example.com/watch_demo.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "product_ad"
  }'
```

### 2. 创建知识科普视频
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个90秒的AI技术科普视频，讲解机器学习的基本原理，要通俗易懂",
    "video_url": "https://example.com/ai_footage.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "knowledge_explain"
  }'
```

### 3. 创建Vlog视频
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "用这段素材制作一个75秒的美食探店vlog，要有温馨轻松的感觉",
    "video_url": "https://example.com/restaurant_visit.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "vlog",
    "style": "温馨"
  }'
```

### 4. 自动识别视频类型
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个2分钟的企业宣传片，展示公司文化、团队风采和产品优势",
    "video_url": "https://example.com/company_footage.mp4",
    "mode": "async",
    "use_aura_render": true
  }'
```

### 5. 使用原有引擎（对比测试）
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个30秒的产品介绍视频",
    "video_url": "https://example.com/product.mp4",
    "mode": "sync",
    "use_aura_render": false
  }'
```

## 响应格式

### 成功响应（AuraRender）
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "video_url": "https://oss.example.com/output/aura_video_20250730_143022.mp4",
    "timeline": [...],
    "video_info": {
      "duration": 30,
      "video_type": "product_ad",
      "style": {
        "category": "futuristic",
        "subtype": "tech"
      }
    },
    "process_info": {
      "engine": "AuraRender",
      "script_path": "/output/aura_scripts/script_20250730_143022.json",
      "created_at": "2025-07-30T14:30:22.123456"
    },
    "execution_script": {
      "version": "1.0",
      "project": {...},
      "resources": {...},
      "timeline": [...],
      "global_effects": {...}
    }
  }
}
```

## 支持的视频类型

1. `product_ad` - 产品广告
2. `brand_promo` - 品牌宣传
3. `knowledge_explain` - 知识科普
4. `online_course` - 在线课程
5. `short_drama` - 短剧
6. `music_mv` - 音乐MV
7. `vlog` - Vlog
8. `life_share` - 生活分享
9. `micro_film` - 微电影
10. `concept_show` - 概念展示
11. `game_video` - 游戏视频
12. `training_video` - 培训视频

## 工作流程

1. **智能分析**：AuraRender分析自然语言描述
2. **类型识别**：自动识别或使用指定的视频类型
3. **资源规划**：
   - 优先使用现有素材
   - 需要时通过万相AI生成
   - 支持视频风格化处理
4. **脚本生成**：生成详细的执行脚本
5. **视频剪辑**：按照时间轴精确剪辑
6. **效果应用**：添加特效、转场、音乐等
7. **输出上传**：渲染并上传到OSS

## 调试技巧

1. **查看执行脚本**：响应中的`execution_script`字段包含完整的执行脚本，可用于调试
2. **脚本文件位置**：`process_info.script_path`指向保存的脚本文件
3. **使用同步模式**：调试时建议使用`"mode": "sync"`实时查看结果
4. **指定视频类型**：明确指定`video_type`可获得更精准的效果

## 注意事项

1. 视频URL必须可访问
2. 较长的视频建议使用异步模式
3. 自然语言描述越详细，效果越好
4. 执行脚本会保存供后续分析和优化
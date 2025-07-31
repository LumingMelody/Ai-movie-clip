# AuraRender 测试命令集

## 准备工作

1. 启动服务：
```bash
python app_0715.py
```

2. 确认服务运行在 http://localhost:8100

## 测试用例（使用真实可用的测试视频）

### 1. 产品广告 - 30秒科技产品介绍
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作30秒智能手表广告，开头5秒logo动画，15秒功能展示（心率监测、消息提醒、运动追踪），8秒外观展示，2秒购买引导。科技风格，蓝紫色调。",
    "video_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "product_ad",
    "output_duration": 30
  }'
```

### 2. 知识科普 - 90秒AI讲解
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作90秒AI科普视频：10秒问题引入'AI如何学习'，20秒基础概念动画讲解，30秒神经网络工作原理，20秒实际应用案例，10秒总结。配图表动画，轻松背景音乐。",
    "video_url": "https://test-videos.co.uk/vids/sintel/mp4/h264/720/Sintel_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "knowledge_explain",
    "output_duration": 90
  }'
```

### 3. Vlog - 75秒探店视频
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作75秒咖啡店vlog：8秒开场打招呼，20秒环境展示配温馨滤镜，25秒咖啡制作过程慢镜头，15秒品尝分享，7秒结尾互动。暖色调，轻快音乐。",
    "video_url": "https://test-videos.co.uk/vids/jellyfish/mp4/h264/720/Jellyfish_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "vlog",
    "style": "warm",
    "output_duration": 75
  }'
```

### 4. 品牌宣传 - 60秒企业介绍
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作60秒企业宣传片：8秒logo和愿景，20秒发展历程时间轴，20秒核心产品展示，12秒团队文化。大气专业风格，企业蓝主色调，激励背景音乐。",
    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "brand_promo",
    "output_duration": 60
  }'
```

### 5. 自动识别类型 - 45秒短视频
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "把这个视频剪成45秒吸引人的短视频，抓人开头，紧凑节奏，强力结尾。自动选择合适风格和音乐。",
    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "output_duration": 45
  }'
```

### 6. 概念展示 - 需要AI生成素材
```bash
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作60秒未来科技概念视频：10秒'2050年'标题动画，20秒未来城市(如无素材则AI生成赛博朋克城市)，20秒展示全息投影等未来科技，10秒'未来已来'结语。赛博朋克风格。",
    "video_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true,
    "video_type": "concept_show",
    "style": "futuristic",
    "output_duration": 60
  }'
```

## 测试说明

### 使用的公开测试视频：

以下是真实可用的测试视频URL：

1. **Big Buck Bunny (10秒版本)**
   - URL: `https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4`
   - 描述：经典开源3D动画短片片段
   - 分辨率：720p
   - 时长：10秒

2. **Sintel Trailer**
   - URL: `https://test-videos.co.uk/vids/sintel/mp4/h264/720/Sintel_720_10s_1MB.mp4`
   - 描述：开源电影Sintel的预告片段
   - 分辨率：720p
   - 时长：10秒

3. **Jellyfish**
   - URL: `https://test-videos.co.uk/vids/jellyfish/mp4/h264/720/Jellyfish_720_10s_1MB.mp4`
   - 描述：水母游动的视频
   - 分辨率：720p
   - 时长：10秒

4. **测试模式视频**
   - URL: `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4`
   - 描述：Google提供的测试视频
   - 分辨率：1080p
   - 时长：15秒

5. **ElephantsDream**
   - URL: `https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4`
   - 描述：开源动画电影片段
   - 分辨率：1080p
   - 时长：较长

**备选方案 - 使用本地视频：**
如果在线视频不稳定，建议下载一个测试视频到本地：
```bash
# 下载测试视频
wget https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4 -O test_video.mp4

# 然后使用本地路径
"video_url": "file:///Users/luming/PycharmProjects/Ai-movie-clip/test_video.mp4"
```

### 响应格式示例：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "video_url": "https://oss.example.com/output/aura_video_xxx.mp4",
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
      "script_path": "/output/aura_scripts/script_xxx.json",
      "created_at": "2025-07-30T14:30:22"
    }
  }
}
```

## 预期效果

1. **产品广告**：
   - 自动识别为产品介绍类型
   - 添加科技感特效和转场
   - 生成产品展示的时间轴结构

2. **知识科普**：
   - 识别教育内容
   - 添加图表动画和说明文字
   - 清晰的章节划分

3. **Vlog**：
   - 轻松活泼的剪辑节奏
   - 温馨滤镜和贴纸效果
   - 适合社交媒体的格式

4. **品牌宣传**：
   - 专业大气的风格
   - 企业色彩方案
   - 激励性的音乐选择

5. **自动识别**：
   - 根据描述智能判断类型
   - 自动匹配合适的模板
   - 优化的剪辑方案

6. **AI生成补充**：
   - 识别缺失的素材需求
   - 调用万相AI生成图片/视频
   - 无缝集成到最终视频

## 快速测试

### 最简单的测试命令：
```bash
# 30秒快速测试（使用真实可用的视频URL）
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作30秒产品介绍视频，要有科技感",
    "video_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true
  }'
```

### 使用本地视频测试：
```bash
# 如果网络视频访问有问题，可以先下载到本地
wget https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4

# 然后使用本地文件路径
curl -X POST http://localhost:8100/video/natural-language-edit \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作30秒产品介绍视频，要有科技感",
    "video_url": "file:///Users/luming/PycharmProjects/Ai-movie-clip/Big_Buck_Bunny_720_10s_1MB.mp4",
    "mode": "sync",
    "use_aura_render": true
  }'
```

### 验证视频URL是否可用：
```bash
# 测试视频是否可以访问
curl -I https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4

# 或者直接在浏览器中打开URL查看
```

## 注意事项

1. 确保服务已启动并运行在8100端口
2. 使用sync模式可立即看到结果
3. 视频URL必须是公开可访问的
4. 处理时间取决于视频长度和复杂度
5. 可查看生成的脚本了解处理细节
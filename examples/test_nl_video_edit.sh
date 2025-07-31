#!/bin/bash

# 自然语言视频剪辑API测试脚本

# API基础URL
BASE_URL="http://localhost:8100"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎬 自然语言视频剪辑API测试${NC}"
echo "================================"

# 测试1: 同步模式 - 产品介绍视频
echo -e "\n${YELLOW}测试1: 同步模式 - 产品介绍视频${NC}"
curl -X POST "${BASE_URL}/video/natural-language-edit" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个30秒的产品介绍视频，开头5秒展示logo带光晕特效，然后介绍产品功能",
    "video_url": "https://example.com/test_video.mp4",
    "mode": "sync",
    "output_duration": 30,
    "style": "科技感",
    "use_timeline_editor": true,
    "tenant_id": "test_tenant",
    "id": "test_001"
  }' | python -m json.tool

# 测试2: 异步模式 - Vlog视频
echo -e "\n${YELLOW}测试2: 异步模式 - Vlog视频${NC}"
RESPONSE=$(curl -s -X POST "${BASE_URL}/video/natural-language-edit" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个1分钟的旅行vlog，要有温馨的背景音乐和手写风格字幕",
    "video_url": "https://example.com/test_video2.mp4",
    "mode": "async",
    "output_duration": 60,
    "style": "温馨",
    "tenant_id": "test_tenant",
    "id": "test_002"
  }')

echo $RESPONSE | python -m json.tool

# 提取task_id
TASK_ID=$(echo $RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")

if [ ! -z "$TASK_ID" ]; then
    echo -e "\n${GREEN}获取到任务ID: $TASK_ID${NC}"
    echo "等待5秒后查询任务状态..."
    sleep 5
    
    # 查询任务状态
    echo -e "\n${YELLOW}查询任务状态${NC}"
    curl -X GET "${BASE_URL}/get-result/${TASK_ID}" | python -m json.tool
fi

# 测试3: 复杂描述测试
echo -e "\n${YELLOW}测试3: 复杂描述测试${NC}"
curl -X POST "${BASE_URL}/video/natural-language-edit" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "制作一个2分钟的企业宣传片。开头10秒展示公司大楼航拍，配震撼音乐。然后30秒介绍公司历史，用时间轴方式展示。接下来40秒展示核心产品，每个产品10秒，要有科技感特效。再30秒展示团队风采，展现活力氛围。最后10秒展示公司愿景和联系方式。",
    "video_url": "https://example.com/company_video.mp4",
    "mode": "sync",
    "output_duration": 120,
    "style": "专业大气",
    "use_timeline_editor": true
  }' | python -m json.tool

# 测试4: 简单剪辑模式（不使用时间轴）
echo -e "\n${YELLOW}测试4: 简单剪辑模式${NC}"
curl -X POST "${BASE_URL}/video/natural-language-edit" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "剪辑视频的前30秒",
    "video_url": "https://example.com/long_video.mp4",
    "mode": "sync",
    "output_duration": 30,
    "use_timeline_editor": false
  }' | python -m json.tool

echo -e "\n${GREEN}测试完成！${NC}"
#!/bin/bash

# 快速测试脚本
echo "======================================"
echo "   自然语言视频剪辑 - 快速测试"
echo "======================================"

# 检查Python环境
echo "检查环境..."
python --version

# 创建必要的目录
mkdir -p resources/videos
mkdir -p resources/audios
mkdir -p resources/images
mkdir -p output

# 提示用户输入视频路径
echo ""
echo "请输入你的视频文件路径："
read VIDEO_PATH

# 检查文件是否存在
if [ ! -f "$VIDEO_PATH" ]; then
    echo "错误：视频文件不存在！"
    exit 1
fi

echo ""
echo "选择测试模式："
echo "1. 快速测试（30秒样例）"
echo "2. 自定义描述"
echo "3. 完整测试（包含AI处理）"
read -p "请选择 (1-3): " MODE

case $MODE in
    1)
        echo "运行快速测试..."
        python test_local_video.py -v "$VIDEO_PATH" -m quick
        ;;
    2)
        echo "请输入视频描述："
        read DESCRIPTION
        python test_local_video.py -v "$VIDEO_PATH" -d "$DESCRIPTION" -m full
        ;;
    3)
        echo "运行完整测试..."
        python test_local_video.py -v "$VIDEO_PATH" -m full
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "测试完成！输出文件在 output/ 目录"
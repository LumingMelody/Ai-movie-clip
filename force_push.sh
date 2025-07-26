#!/bin/bash

echo "🚀 正在强制推送到GitHub..."
echo ""

# 设置Git配置以提高推送成功率
git config http.version HTTP/1.1
git config http.postBuffer 157286400
git config core.compression 0

# 尝试推送
echo "正在推送，请稍候..."
git push -f origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    echo "⚠️  重要后续步骤："
    echo "1. 立即移除token信息："
    echo "   git remote set-url origin https://github.com/LumingMelody/Ai-movie-clip.git"
    echo ""
    echo "2. 在阿里云控制台重新生成AccessKey"
    echo "3. 更新.env文件中的新密钥"
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的解决方案："
    echo "1. 检查网络连接"
    echo "2. 尝试使用VPN"
    echo "3. 使用以下命令手动推送："
    echo "   git push -f origin main"
fi
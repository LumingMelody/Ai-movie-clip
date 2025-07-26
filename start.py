#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - 自动加载环境变量
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载环境变量配置: {env_path}")
else:
    print(f"⚠️ 未找到 .env 文件，使用默认配置")

# 验证关键配置
required_vars = ['DASHSCOPE_API_KEY', 'OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"⚠️ 缺少必要的环境变量: {', '.join(missing_vars)}")
    print("请在 .env 文件中配置这些变量")
else:
    print("✅ 所有必要的环境变量已配置")

# 导入并启动主应用
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # 启动 Web 服务
        print("🚀 启动 FastAPI Web 服务...")
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    else:
        # 启动命令行工具
        print("🚀 启动命令行工具...")
        from main import main
        main()
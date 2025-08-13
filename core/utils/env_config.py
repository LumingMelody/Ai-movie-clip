#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一的环境变量配置管理
所有API key和敏感配置都从环境变量或.env文件读取
"""

import os
from typing import Optional
from pathlib import Path

# 尝试加载.env文件（如果存在）
def load_dotenv():
    """加载.env文件中的环境变量"""
    try:
        from dotenv import load_dotenv as _load_dotenv
        # 查找项目根目录的.env文件
        current_dir = Path(__file__).parent.parent.parent
        env_file = current_dir / '.env'
        if env_file.exists():
            _load_dotenv(env_file)
            return True
    except ImportError:
        pass
    return False

# 自动加载.env
load_dotenv()


def get_dashscope_api_key() -> Optional[str]:
    """
    获取DashScope API Key
    优先级：环境变量 > .env文件
    
    Returns:
        API Key字符串，如果未找到返回None
    """
    api_key = os.getenv('DASHSCOPE_API_KEY')
    
    if not api_key:
        print("警告: 未找到DASHSCOPE_API_KEY环境变量")
        print("请设置环境变量或在.env文件中配置: DASHSCOPE_API_KEY=your_api_key")
        return None
    
    return api_key.strip()


def get_api_key() -> Optional[str]:
    """
    向后兼容的API Key获取函数
    
    Returns:
        API Key字符串，如果未找到返回None
    """
    return get_dashscope_api_key()


# 为了兼容旧代码
def get_api_key_from_file(file_name="api_key.txt") -> Optional[str]:
    """
    向后兼容函数，现在从环境变量获取
    忽略file_name参数
    
    Args:
        file_name: 忽略此参数，仅为向后兼容
        
    Returns:
        API Key字符串，如果未找到返回None
    """
    return get_dashscope_api_key()


# 其他可能需要的API keys
def get_openai_api_key() -> Optional[str]:
    """获取OpenAI API Key"""
    return os.getenv('OPENAI_API_KEY')


def get_oss_access_key() -> Optional[str]:
    """获取OSS Access Key"""
    return os.getenv('OSS_ACCESS_KEY')


def get_oss_secret_key() -> Optional[str]:
    """获取OSS Secret Key"""
    return os.getenv('OSS_SECRET_KEY')


def check_required_keys() -> bool:
    """
    检查必需的API keys是否都已配置
    
    Returns:
        True if all required keys are present, False otherwise
    """
    required_keys = {
        'DASHSCOPE_API_KEY': get_dashscope_api_key(),
    }
    
    missing_keys = [key for key, value in required_keys.items() if not value]
    
    if missing_keys:
        print(f"缺少必需的环境变量: {', '.join(missing_keys)}")
        return False
    
    return True


if __name__ == "__main__":
    # 测试
    print("检查环境变量配置...")
    
    api_key = get_dashscope_api_key()
    if api_key:
        # 只显示前后几个字符，隐藏中间部分
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(f"✅ DASHSCOPE_API_KEY已配置: {masked_key}")
    else:
        print("❌ DASHSCOPE_API_KEY未配置")
    
    if check_required_keys():
        print("✅ 所有必需的环境变量都已配置")
    else:
        print("❌ 缺少必需的环境变量")
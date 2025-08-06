#!/usr/bin/env python3
"""
火山引擎API环境配置测试
演示如何正确设置和测试API密钥
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

from core.clipeffects.volcano_effects import create_volcano_effects


def check_environment():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置")
    print("=" * 60)
    
    # 检查是否设置了环境变量
    access_key_id = os.environ.get('VOLCANO_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('VOLCANO_SECRET_ACCESS_KEY')
    
    if not access_key_id or not secret_access_key:
        print("❌ 未检测到API密钥环境变量\n")
        print("请按以下步骤设置：\n")
        print("1. 在终端运行以下命令（替换为您的实际密钥）：")
        print("   export VOLCANO_ACCESS_KEY_ID='您的访问密钥ID'")
        print("   export VOLCANO_SECRET_ACCESS_KEY='您的访问密钥Secret'\n")
        print("2. 或者创建 .env 文件：")
        print("   echo 'VOLCANO_ACCESS_KEY_ID=您的访问密钥ID' > .env")
        print("   echo 'VOLCANO_SECRET_ACCESS_KEY=您的访问密钥Secret' >> .env\n")
        print("3. 然后重新运行此脚本")
        return False
    
    print("✅ 检测到API密钥配置")
    print(f"   Access Key ID: {access_key_id[:10]}...")
    print(f"   Secret Access Key: {'*' * 20}")
    return True


def test_with_api():
    """使用真实API进行测试"""
    print("\n🚀 使用火山引擎API进行测试")
    print("=" * 60)
    
    # 从环境变量获取密钥
    access_key_id = os.environ.get('VOLCANO_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('VOLCANO_SECRET_ACCESS_KEY')
    
    # 创建火山引擎特效管理器
    volcano = create_volcano_effects(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key
    )
    
    print("📋 可用的特效：")
    effects = volcano.list_available_effects()
    
    # 显示部分特效作为示例
    print(f"\n滤镜 ({len(effects['filters'])} 个):")
    for name in list(effects['filters'])[:5]:
        effect = volcano.get_effect_info('filter', name)
        print(f"  - {effect.name} (ID: {effect.effect_id})")
    
    print(f"\n转场 ({len(effects['transitions'])} 个):")
    for name in list(effects['transitions'])[:5]:
        effect = volcano.get_effect_info('transition', name)
        print(f"  - {effect.name} (ID: {effect.effect_id})")
    
    print("\n💡 提示：要使用这些特效，您需要：")
    print("   1. 将视频上传到火山引擎存储")
    print("   2. 使用返回的FileId创建编辑任务")
    print("   3. 等待任务完成并获取结果")


def test_without_api():
    """不使用API的本地测试"""
    print("\n🏠 使用本地实现进行测试")
    print("=" * 60)
    
    # 创建不带API密钥的管理器
    volcano = create_volcano_effects()
    
    print("ℹ️  未配置API密钥，将使用本地模拟")
    print("   本地模式可以：")
    print("   - 查看所有可用的特效ID和名称")
    print("   - 测试基本的视频处理逻辑")
    print("   - 生成示例配置文件")
    print("\n   本地模式不能：")
    print("   - 调用真实的火山引擎API")
    print("   - 应用高级特效和滤镜")
    print("   - 上传视频到云端")


def create_env_template():
    """创建环境变量模板文件"""
    print("\n📄 创建环境变量模板")
    print("=" * 60)
    
    env_template = """# 火山引擎API配置
# 请将此文件重命名为 .env 并填入您的实际密钥

# 访问密钥ID（从火山引擎控制台获取）
VOLCANO_ACCESS_KEY_ID=your_access_key_id_here

# 访问密钥Secret（从火山引擎控制台获取）
VOLCANO_SECRET_ACCESS_KEY=your_secret_access_key_here

# 区域配置（可选，默认为 cn-north-1）
VOLCANO_REGION=cn-north-1

# 存储桶配置（用于上传视频）
VOLCANO_BUCKET_NAME=your_bucket_name_here
"""
    
    template_path = ".env.template"
    with open(template_path, 'w') as f:
        f.write(env_template)
    
    print(f"✅ 模板文件已创建: {template_path}")
    print("   1. 复制模板: cp .env.template .env")
    print("   2. 编辑文件: nano .env")
    print("   3. 填入您的实际密钥")
    print("   4. 加载环境变量: source .env")


def main():
    """主函数"""
    print("🌋 火山引擎API配置和测试工具")
    print("=" * 60)
    
    # 检查环境配置
    has_api_keys = check_environment()
    
    if has_api_keys:
        # 有API密钥，进行真实测试
        test_with_api()
    else:
        # 无API密钥，使用本地模式
        test_without_api()
        
        # 创建环境变量模板
        create_env_template()
        
        print("\n📚 下一步：")
        print("   1. 注册火山引擎账号：https://console.volcengine.com")
        print("   2. 创建访问密钥")
        print("   3. 配置环境变量")
        print("   4. 重新运行此脚本进行测试")
    
    print("\n✨ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
火山引擎视频特效测试脚本
测试volcano_effects.py的功能并验证API调用方式
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

from core.clipeffects.volcano_effects import VolcanoEffects, create_volcano_effects
from moviepy import VideoFileClip
import tempfile

def test_volcano_effects_basic():
    """测试基本功能"""
    print("🧪 测试火山引擎特效管理器基本功能")
    print("=" * 60)
    
    # 创建特效管理器（不使用API密钥，测试本地模拟功能）
    volcano = create_volcano_effects()
    
    # 1. 测试列出所有可用特效
    print("\n📋 测试: 列出所有可用特效")
    effects = volcano.list_available_effects()
    for category, items in effects.items():
        print(f"\n🎨 {category.upper()} ({len(items)} 个特效):")
        for i, item in enumerate(items[:5], 1):  # 只显示前5个
            print(f"   {i}. {item}")
        if len(items) > 5:
            print(f"   ... 还有 {len(items) - 5} 个特效")
    
    # 2. 测试获取特效详细信息
    print(f"\n🔍 测试: 获取特效详细信息")
    try:
        filter_info = volcano.get_effect_info("filter", "vintage")
        print(f"✅ 复古滤镜信息:")
        print(f"   - ID: {filter_info.effect_id}")
        print(f"   - 名称: {filter_info.name}")
        print(f"   - 描述: {filter_info.description}")
        print(f"   - 类型: {filter_info.effect_type.value}")
    except Exception as e:
        print(f"❌ 获取特效信息失败: {e}")
    
    # 3. 测试转场特效信息
    print(f"\n🔄 测试: 转场特效信息")
    try:
        transition_info = volcano.get_effect_info("transition", "fade")
        print(f"✅ 淡入淡出转场信息:")
        print(f"   - ID: {transition_info.effect_id}")
        print(f"   - 名称: {transition_info.name}")
        print(f"   - 描述: {transition_info.description}")
    except Exception as e:
        print(f"❌ 获取转场信息失败: {e}")

def test_volcano_effects_with_video(video_path: str):
    """测试视频特效应用"""
    print(f"\n🎬 测试火山引擎特效应用 - 视频文件: {video_path}")
    print("=" * 60)
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    try:
        # 加载视频文件
        print(f"📁 加载视频文件...")
        clip = VideoFileClip(video_path)
        print(f"✅ 视频加载成功:")
        print(f"   - 时长: {clip.duration:.2f}秒")
        print(f"   - 分辨率: {clip.size}")
        print(f"   - FPS: {clip.fps}")
        
        # 创建特效管理器
        volcano = create_volcano_effects()
        
        # 测试1: 应用滤镜效果
        print(f"\n🎨 测试: 应用滤镜效果")
        try:
            filtered_clip = volcano.apply_filter(clip.subclipped(0, 3), "vintage", intensity=0.8)
            print(f"✅ 复古滤镜应用成功")
            print(f"   - 原始时长: {clip.subclipped(0, 3).duration:.2f}秒")
            print(f"   - 处理后时长: {filtered_clip.duration:.2f}秒")
        except Exception as e:
            print(f"❌ 滤镜应用失败: {e}")
        
        # 测试2: 应用特效
        print(f"\n✨ 测试: 应用特效")
        try:
            effect_clip = volcano.apply_effect(clip.subclipped(0, 3), "blur", intensity=0.5)
            print(f"✅ 模糊特效应用成功")
        except Exception as e:
            print(f"❌ 特效应用失败: {e}")
        
        # 测试3: 应用视频动画
        print(f"\n🎭 测试: 应用视频动画")
        try:
            animated_clip = volcano.apply_video_animation(clip.subclipped(0, 3), "zoom_in", duration=2.0)
            print(f"✅ 放大动画应用成功")
        except Exception as e:
            print(f"❌ 视频动画应用失败: {e}")
        
        # 测试4: 文字动画
        print(f"\n📝 测试: 文字动画")
        try:
            text_clip = volcano.apply_text_animation(
                "测试文字动画", 
                "fade_in", 
                font_size=50, 
                color="white"
            )
            print(f"✅ 文字动画创建成功")
        except Exception as e:
            print(f"❌ 文字动画创建失败: {e}")
        
        # 测试5: 转场效果（需要两个视频片段）
        print(f"\n🔄 测试: 转场效果")
        try:
            clip1 = clip.subclipped(0, 2)
            clip2 = clip.subclipped(2, 4)
            transition_clip = volcano.apply_transition(clip1, clip2, "fade", duration=1.0)
            print(f"✅ 淡入淡出转场创建成功")
            print(f"   - 总时长: {transition_clip.duration:.2f}秒")
        except Exception as e:
            print(f"❌ 转场效果创建失败: {e}")
        
        # 清理资源
        clip.close()
        print(f"\n🗑️ 资源清理完成")
        
    except Exception as e:
        print(f"❌ 视频测试失败: {e}")

def test_api_structure():
    """测试API结构和调用方式"""
    print(f"\n🔧 测试API结构和调用方式")
    print("=" * 60)
    
    # 模拟API密钥测试
    print(f"\n🔑 测试: API密钥配置")
    volcano_with_key = VolcanoEffects(
        api_key="test_api_key_123456", 
        api_url="https://vod.volcengineapi.com",
        region="cn-north-1"
    )
    
    print(f"✅ API配置:")
    print(f"   - API密钥: {'*' * 20}")
    print(f"   - API地址: {volcano_with_key.api_url}")
    print(f"   - 服务区域: {volcano_with_key.region}")
    print(f"   - 请求头: {volcano_with_key.headers}")
    
    # 测试特效ID格式
    print(f"\n🆔 测试: 特效ID格式分析")
    volcano = create_volcano_effects()
    
    # 分析当前使用的ID格式
    print(f"📊 当前特效ID格式分析:")
    print(f"   滤镜ID范围: 1184003-1184017 (共{len(volcano.FILTERS)}个)")
    print(f"   特效ID范围: 1185001-1185015 (共{len(volcano.EFFECTS)}个)")
    print(f"   视频动画ID范围: 1186001-1186013 (共{len(volcano.VIDEO_ANIMATIONS)}个)")
    print(f"   文字动画ID范围: 1187001-1187013 (共{len(volcano.TEXT_ANIMATIONS)}个)")
    print(f"   转场ID范围: 1188001-1188018 (共{len(volcano.TRANSITIONS)}个)")
    
    # 显示部分实际ID
    print(f"\n🔍 部分特效ID示例:")
    for name, effect in list(volcano.TRANSITIONS.items())[:5]:
        print(f"   转场 '{name}': ID={effect.effect_id}, 描述='{effect.description}'")

def recommend_improvements():
    """提供改进建议"""
    print(f"\n💡 火山引擎特效集成改进建议")
    print("=" * 60)
    
    print(f"""
🎯 主要问题分析:
1. 当前使用的特效ID (如1184003, 1185001等) 可能是模拟数据
2. API调用方式需要验证是否符合火山引擎官方规范
3. 缺少真实的API响应处理和错误处理机制

🔧 建议的改进措施:

1. 获取官方特效ID:
   - 联系火山引擎技术支持获取真实的特效ID列表
   - 查阅最新的API文档，确认正确的ID格式
   - 建议格式可能是字符串型ID，而非数字

2. 优化API调用:
   - 验证API端点URL的正确性
   - 确认请求参数格式是否符合官方要求
   - 添加更完善的错误处理和重试机制

3. 增强测试功能:
   - 添加API连通性测试
   - 实现特效预览功能
   - 添加性能监控和日志记录

4. 代码结构优化:
   - 将特效ID配置分离到独立的配置文件
   - 添加特效缓存机制
   - 实现异步API调用支持

5. 兼容性改进:
   - 添加本地特效回退机制
   - 支持多种视频格式和分辨率
   - 优化内存使用和资源清理
""")

def main():
    """主测试函数"""
    print("🚀 火山引擎视频特效测试开始")
    print("=" * 60)
    
    # 基本功能测试
    test_volcano_effects_basic()
    
    # API结构测试
    test_api_structure()
    
    # 查找本地测试视频
    possible_video_paths = [
        "test_video.mp4",
        "demo.mp4",
        "sample.mp4",
        "/System/Library/Compositions/Ripple.mov",  # macOS系统视频
    ]
    
    test_video = None
    for path in possible_video_paths:
        if os.path.exists(path):
            test_video = path
            break
    
    if test_video:
        test_volcano_effects_with_video(test_video)
    else:
        print(f"\n⚠️ 未找到测试视频文件，跳过视频特效测试")
        print(f"   建议将测试视频文件命名为 'test_video.mp4' 并放在项目根目录")
    
    # 改进建议
    recommend_improvements()
    
    print(f"\n✅ 测试完成！")
    print(f"=" * 60)

if __name__ == "__main__":
    main()
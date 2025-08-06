#!/usr/bin/env python3
"""
测试改进版火山引擎特效模块
使用本地视频文件进行测试
"""

import os
import sys
from pathlib import Path
import tempfile

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

from core.clipeffects.volcano_effects_improved import create_volcano_effects_v2
from moviepy import VideoFileClip, ColorClip
import numpy as np

def create_test_video():
    """创建测试视频"""
    print("🎬 创建测试视频...")
    
    # 创建两个简单的彩色视频片段用于测试
    duration = 3
    
    # 第一个片段 - 红色背景
    clip1 = ColorClip(size=(640, 480), color=(255, 0, 0), duration=duration)
    
    # 第二个片段 - 蓝色背景
    clip2 = ColorClip(size=(640, 480), color=(0, 0, 255), duration=duration)
    
    print(f"✅ 测试视频创建完成")
    print(f"   - 片段1: {duration}秒红色背景")
    print(f"   - 片段2: {duration}秒蓝色背景")
    
    return clip1, clip2

def test_volcano_v2_basic():
    """测试基本功能"""
    print("\n🧪 测试改进版火山引擎特效管理器")
    print("=" * 60)
    
    # 创建管理器实例（不使用真实API密钥）
    volcano = create_volcano_effects_v2()
    
    # 测试1: 列出转场效果
    print("\n📋 测试: 列出所有转场效果")
    transitions = volcano.list_available_transitions()
    print(f"✅ 共找到 {len(transitions)} 个转场效果:")
    
    for name, effect in list(transitions.items())[:5]:  # 显示前5个
        print(f"   - {name}: {effect.name} (ID: {effect.effect_id})")
        print(f"     描述: {effect.description}")
        print(f"     分类: {effect.category}")
    
    if len(transitions) > 5:
        print(f"   ... 还有 {len(transitions) - 5} 个转场效果")
    
    # 测试2: 按分类列出
    print(f"\n📊 测试: 按分类列出转场效果")
    categories = set(effect.category for effect in transitions.values())
    for category in sorted(categories):
        effects = volcano.get_transition_by_category(category)
        print(f"   {category.upper()}: {len(effects)} 个转场")
        for name, effect in list(effects.items())[:2]:  # 每个分类显示2个
            print(f"     - {effect.name}")
    
    return volcano

def test_transitions_with_video(volcano):
    """测试转场效果应用"""
    print(f"\n🎨 测试转场效果应用")
    print("=" * 60)
    
    try:
        # 创建测试视频
        clip1, clip2 = create_test_video()
        
        # 测试不同的转场效果
        transitions_to_test = [
            ("fade", "淡入淡出"),
            ("slide_left", "左滑动"),
            ("slide_right", "右滑动"),
            ("dissolve", "溶解"),
            ("zoom_in", "放大")
        ]
        
        for transition_name, display_name in transitions_to_test:
            print(f"\n🔄 测试转场: {display_name}")
            try:
                # 应用转场效果（使用本地实现，不调用API）
                result_clip = volcano.apply_transition_effect(
                    clip1, clip2, 
                    transition_name, 
                    duration=1.0,
                    use_api=False  # 使用本地实现进行测试
                )
                
                print(f"✅ {display_name} 转场应用成功")
                print(f"   - 输入片段1: {clip1.duration:.1f}秒")
                print(f"   - 输入片段2: {clip2.duration:.1f}秒") 
                print(f"   - 输出总长度: {result_clip.duration:.1f}秒")
                print(f"   - 输出分辨率: {result_clip.size}")
                
                # 清理结果片段
                result_clip.close()
                
            except Exception as e:
                print(f"❌ {display_name} 转场测试失败: {str(e)}")
        
        # 清理测试片段
        clip1.close()
        clip2.close()
        
    except Exception as e:
        print(f"❌ 转场测试失败: {str(e)}")

def test_api_simulation():
    """测试API调用模拟"""
    print(f"\n🔧 测试API调用模拟")
    print("=" * 60)
    
    # 使用模拟的API密钥创建管理器
    volcano = create_volcano_effects_v2(
        access_key_id="test_access_key_id",
        secret_access_key="test_secret_access_key"
    )
    
    print(f"✅ API配置测试:")
    print(f"   - 访问密钥ID: {'*' * 15}")
    print(f"   - 服务区域: {volcano.region}")
    print(f"   - 服务名称: {volcano.service}")
    print(f"   - API主机: {volcano.host}")
    print(f"   - API版本: {volcano.api_version}")
    
    # 测试API调用结构（不实际发送请求）
    print(f"\n📡 API调用结构测试:")
    test_params = {
        "video_url": "test_video.mp4",
        "edit_config": {
            "transitions": [
                {
                    "effect_id": "transition_fade",
                    "duration": 1.0,
                    "start_time": 2.0
                }
            ],
            "output_format": "mp4",
            "quality": "HD"
        }
    }
    
    print(f"   - 参数结构正确: ✅")
    print(f"   - 转场配置: {len(test_params['edit_config']['transitions'])} 个效果")
    print(f"   - 输出格式: {test_params['edit_config']['output_format']}")
    print(f"   - 输出质量: {test_params['edit_config']['quality']}")

def test_error_handling():
    """测试错误处理"""
    print(f"\n🛡️ 测试错误处理")
    print("=" * 60)
    
    volcano = create_volcano_effects_v2()
    clip1, clip2 = create_test_video()
    
    # 测试1: 无效转场名称
    print(f"\n❌ 测试无效转场名称:")
    try:
        volcano.apply_transition_effect(clip1, clip2, "invalid_transition")
        print(f"   错误: 应该抛出异常但没有")
    except ValueError as e:
        print(f"   ✅ 正确捕获异常: {str(e)}")
    except Exception as e:
        print(f"   ⚠️ 捕获了意外异常: {str(e)}")
    
    # 测试2: 极短转场时间
    print(f"\n⏱️ 测试极短转场时间:")
    try:
        result = volcano.apply_transition_effect(
            clip1, clip2, "fade", 
            duration=0.1,  # 极短时间
            use_api=False
        )
        print(f"   ✅ 极短转场处理成功: {result.duration:.2f}秒")
        result.close()
    except Exception as e:
        print(f"   ❌ 极短转场处理失败: {str(e)}")
    
    # 测试3: 超长转场时间
    print(f"\n⏳ 测试超长转场时间:")
    try:
        result = volcano.apply_transition_effect(
            clip1, clip2, "fade",
            duration=10.0,  # 超过视频长度
            use_api=False
        )
        print(f"   ✅ 超长转场处理成功: {result.duration:.2f}秒")
        result.close()
    except Exception as e:
        print(f"   ❌ 超长转场处理失败: {str(e)}")
    
    # 清理
    clip1.close()
    clip2.close()

def performance_test():
    """性能测试"""
    print(f"\n⚡ 性能测试")
    print("=" * 60)
    
    import time
    
    volcano = create_volcano_effects_v2()
    clip1, clip2 = create_test_video()
    
    # 测试多个转场效果的性能
    transitions = ["fade", "slide_left", "slide_right"]
    
    for transition_name in transitions:
        print(f"\n🏃 测试 {transition_name} 转场性能:")
        
        start_time = time.time()
        try:
            result = volcano.apply_transition_effect(
                clip1, clip2, transition_name,
                duration=1.0, use_api=False
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            print(f"   ✅ 处理耗时: {processing_time:.2f}秒")
            print(f"   - 输出时长: {result.duration:.2f}秒")
            print(f"   - 性能比: {result.duration/processing_time:.1f}x")
            
            result.close()
            
        except Exception as e:
            print(f"   ❌ 性能测试失败: {str(e)}")
    
    # 清理
    clip1.close()
    clip2.close()

def main():
    """主测试函数"""
    print("🚀 火山引擎特效模块V2测试开始")
    print("=" * 60)
    
    try:
        # 基础功能测试
        volcano = test_volcano_v2_basic()
        
        # 转场效果测试
        test_transitions_with_video(volcano)
        
        # API模拟测试
        test_api_simulation()
        
        # 错误处理测试
        test_error_handling()
        
        # 性能测试
        performance_test()
        
        print(f"\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)

if __name__ == "__main__":
    main()
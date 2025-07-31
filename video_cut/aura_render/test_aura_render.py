"""
AuraRender 测试脚本

展示如何使用AuraRender创建不同类型的视频
"""

import json
import os
import sys

# 添加项目根目录到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from video_cut.aura_render.aura_interface import AuraRenderInterface, create_aura_video


def test_product_ad():
    """测试产品广告视频生成"""
    print("=== 测试产品广告视频 ===")
    
    request = {
        'natural_language': '制作一个30秒的智能手表产品广告，展示其健康监测功能和时尚外观，风格要科技感十足',
        'preferences': {
            'video_type': 'product_ad',
            'style': 'futuristic'
        }
    }
    
    result = create_aura_video(**request)
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


def test_knowledge_explain():
    """测试知识科普视频生成"""
    print("\n=== 测试知识科普视频 ===")
    
    request = {
        'natural_language': '制作一个90秒的科普视频，解释人工智能的基本原理，要通俗易懂，适合初学者',
        'preferences': {
            'video_type': 'knowledge_explain',
            'style': 'educational'
        }
    }
    
    result = create_aura_video(**request)
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


def test_vlog():
    """测试Vlog视频生成"""
    print("\n=== 测试Vlog视频 ===")
    
    request = {
        'natural_language': '制作一个75秒的美食探店vlog，记录在网红餐厅的用餐体验，要有温馨轻松的氛围',
        'video_url': 'https://example.com/restaurant_footage.mp4',  # 假设有原始素材
        'preferences': {
            'video_type': 'vlog',
            'style': 'lifestyle'
        }
    }
    
    result = create_aura_video(**request)
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


def test_direct_script_execution():
    """测试直接执行脚本"""
    print("\n=== 测试直接执行脚本 ===")
    
    # 创建一个简单的执行脚本
    script = {
        'version': '1.0',
        'project': {
            'id': 'test_001',
            'type': 'product_ad',
            'style': {
                'category': 'futuristic',
                'subtype': 'tech'
            },
            'duration': 15,
            'resolution': '1920x1080',
            'fps': 30
        },
        'resources': {
            'videos': [],
            'images': [],
            'audio': [{
                'id': 'bgm_001',
                'source': 'ai_generated',
                'params': {
                    'model': 'musicgen',
                    'style': 'electronic_tech',
                    'duration': 15
                }
            }]
        },
        'timeline': [
            {
                'start': 0,
                'end': 5,
                'layers': [{
                    'type': 'text',
                    'content': 'AuraRender Demo',
                    'style': {
                        'size': 72,
                        'color': '#00FFFF',
                        'animation': 'fade_in'
                    }
                }]
            },
            {
                'start': 5,
                'end': 10,
                'layers': [{
                    'type': 'text',
                    'content': '智能视频创作引擎',
                    'style': {
                        'size': 60,
                        'color': '#FFFFFF',
                        'animation': 'slide_in'
                    }
                }]
            },
            {
                'start': 10,
                'end': 15,
                'layers': [{
                    'type': 'text',
                    'content': '让创意触手可及',
                    'style': {
                        'size': 56,
                        'color': '#FFD700',
                        'animation': 'scale_up'
                    }
                }]
            }
        ],
        'global_effects': {
            'color_grading': 'cyberpunk_preset',
            'filters': ['digital_noise']
        }
    }
    
    interface = AuraRenderInterface()
    result = interface.create_video_from_script(script)
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    return result


def main():
    """运行所有测试"""
    print("开始AuraRender测试...\n")
    
    # 测试不同类型的视频生成
    test_product_ad()
    test_knowledge_explain()
    test_vlog()
    test_direct_script_execution()
    
    print("\n测试完成！")
    print("\n提示：")
    print("1. 生成的执行脚本保存在 output/aura_scripts/ 目录")
    print("2. 生成的视频保存在 output/aura_videos/ 目录")
    print("3. 可以查看脚本了解AuraRender的工作原理")


if __name__ == '__main__':
    main()
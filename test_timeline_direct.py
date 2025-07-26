#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""直接测试时间轴生成逻辑"""

import sys
import os
import json

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
video_cut_path = os.path.join(project_root, 'video_cut')
sys.path.insert(0, project_root)
sys.path.insert(0, video_cut_path)

# 切换到video_cut目录以确保相对导入正常工作
os.chdir(video_cut_path)

try:
    from core.controller import UnifiedController
    from main import load_dag_and_nodes
    
    print("✅ 成功导入 video_cut 模块")
    
    # 测试加载 DAG
    dag, nodes = load_dag_and_nodes()
    print(f"✅ 成功加载 DAG，节点数: {len(nodes)}")
    
    # 创建控制器
    controller = UnifiedController(dag, nodes)
    print("✅ 成功创建控制器")
    
    # 测试生成
    context = {
        "大纲内容": "测试视频: 这是一个测试",
        "时长": 60,
        "平台": "B站",
        "受众": "学生",
        "风格": "科技感",
        "包含字幕": True,
        "包含LOGO": True,
        "包含背景音乐": True,
        "品牌色彩": ["蓝色", "白色"],
        "特殊要求": ""
    }
    
    print("\n开始执行时间轴生成...")
    result = controller.handle_input({
        "type": "generate",
        "context": context
    })
    
    print("✅ 时间轴生成成功!")
    print(f"结果键: {list(result.keys())}")
    
    # 检查 node12 (timeline node)
    if "node12" in result:
        print("✅ 找到 node12 (时间轴节点)")
        print(f"node12 内容类型: {type(result['node12'])}")
        if isinstance(result['node12'], dict):
            print(f"node12 键: {list(result['node12'].keys())[:5]}...")  # 只显示前5个键
    
    if "final_timeline" in result:
        print("✅ 包含 final_timeline")
    else:
        print("❌ 缺少 final_timeline")
        # node12 应该是最终的时间轴
        if "node12" in result:
            print("将 node12 作为 final_timeline")
        
except Exception as e:
    import traceback
    print(f"❌ 错误: {e}")
    print("详细错误:")
    traceback.print_exc()
#!/usr/bin/env python3
import sys
import json
import os

# 添加项目路径
sys.path.append('/Users/luming/PycharmProjects/Ai-movie-clip')

try:
    from core.clipgenerate.interface_function import get_video_edit_simple
    
    if __name__ == "__main__":
        # 读取参数文件
        if len(sys.argv) != 2:
            print(json.dumps({"error": "需要参数文件路径"}))
            sys.exit(1)
        
        param_file = sys.argv[1]
        with open(param_file, 'r', encoding='utf-8') as f:
            params = json.load(f)
        
        # 调用函数
        result = get_video_edit_simple(
            video_sources=params['video_sources'],
            duration=params.get('duration', 30),
            style=params.get('style', '抖音风'),
            purpose=params.get('purpose', '社交媒体'),
            use_local_ai=params.get('use_local_ai', True),
            api_key=params.get('api_key')
        )
        
        # 添加任务信息
        if isinstance(result, dict):
            result.update({
                'task_id': None,
                'tenant_id': params.get('tenant_id'),
                'business_id': params.get('id')
            })
        
        print(json.dumps(result, ensure_ascii=False))
        
except Exception as e:
    error_result = {
        "error": str(e),
        "task_id": None,
        "tenant_id": None,
        "business_id": None
    }
    print(json.dumps(error_result, ensure_ascii=False))
    sys.exit(1)

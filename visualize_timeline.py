"""
时间轴可视化工具
将生成的时间轴JSON以文本形式可视化
"""

import json
from pathlib import Path


def visualize_timeline(timeline_path):
    """可视化时间轴"""
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline = json.load(f)
    
    print(f"\n{'='*80}")
    print(f"时间轴: {timeline['metadata']['title']}")
    print(f"{'='*80}")
    
    duration = timeline['timeline']['duration']
    fps = timeline['timeline']['fps']
    resolution = timeline['timeline']['resolution']
    
    print(f"时长: {duration}秒 | 帧率: {fps}fps | 分辨率: {resolution['width']}x{resolution['height']}")
    print(f"\n时间刻度 (每个字符代表1秒):")
    print("0" + "-"*9 + "10" + "-"*8 + "20" + "-"*8 + "30" + "-"*8 + "40" + "-"*8 + "50" + "-"*8 + "60")
    print("|" + " "*9 + "|" + " "*9 + "|" + " "*9 + "|" + " "*9 + "|" + " "*9 + "|" + " "*9 + "|")
    
    # 可视化每个轨道
    tracks = timeline['timeline']['tracks']
    
    for i, track in enumerate(tracks):
        print(f"\n轨道{i+1}: {track['name']} ({track['type']})")
        
        # 创建时间线
        timeline_str = [' '] * duration
        
        for clip in track.get('clips', []):
            start = int(clip.get('start', 0))
            end = int(clip.get('end', start + 1))
            
            # 根据轨道类型使用不同符号
            if track['type'] == 'video':
                symbol = '█'
            elif track['type'] == 'audio':
                symbol = '♪'
            elif track['type'] == 'text':
                symbol = 'T'
            else:
                symbol = '●'
            
            # 填充时间线
            for t in range(start, min(end, duration)):
                timeline_str[t] = symbol
        
        # 打印时间线
        print(''.join(timeline_str))
        
        # 显示片段详情
        if track['type'] == 'text' and track.get('clips'):
            print("文字内容:")
            for clip in track['clips'][:5]:  # 只显示前5个
                text = clip.get('content', {}).get('text', '')
                if len(text) > 30:
                    text = text[:27] + "..."
                print(f"  [{clip.get('start', 0):.1f}-{clip.get('end', 0):.1f}s] {text}")
        elif track['type'] == 'video' and track.get('clips'):
            print("视频片段:")
            for clip in track['clips']:
                title = clip.get('title', clip.get('source', '未命名'))
                print(f"  [{clip.get('start', 0)}-{clip.get('end', 0)}s] {title}")


def compare_timelines(timeline_paths):
    """比较多个时间轴"""
    print("\n" + "="*80)
    print("时间轴对比")
    print("="*80)
    
    timelines = []
    for path in timeline_paths:
        with open(path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)
            timelines.append({
                'name': Path(path).stem,
                'data': timeline
            })
    
    # 对比表格
    print(f"\n{'名称':<20} {'版本':<6} {'时长':<6} {'轨道数':<8} {'模板':<15}")
    print("-" * 60)
    
    for tl in timelines:
        name = tl['name']
        data = tl['data']
        version = data.get('version', 'N/A')
        duration = data['timeline']['duration']
        track_count = len(data['timeline']['tracks'])
        template = data['metadata'].get('template', 'N/A')
        
        print(f"{name:<20} {version:<6} {duration:<6} {track_count:<8} {template:<15}")
    
    # 轨道类型统计
    print("\n轨道类型分布:")
    for tl in timelines:
        name = tl['name']
        tracks = tl['data']['timeline']['tracks']
        track_types = {}
        
        for track in tracks:
            t_type = track['type']
            track_types[t_type] = track_types.get(t_type, 0) + 1
        
        types_str = ', '.join([f"{t}:{c}" for t, c in track_types.items()])
        print(f"  {name}: {types_str}")


def main():
    """主函数"""
    print("时间轴可视化工具")
    
    # 可视化单个时间轴
    timeline_files = [
        "output/timeline_from_nodes/generated_timeline.json",
        "output/timeline_advanced_tests/timeline_default.json",
        "output/timeline_advanced_tests/timeline_complete.json",
        "output/timeline_advanced_tests/timeline_simple.json",
        "output/timeline_advanced_tests/timeline_text_only.json"
    ]
    
    # 检查存在的文件
    existing_files = [f for f in timeline_files if Path(f).exists()]
    
    if not existing_files:
        print("没有找到时间轴文件！")
        return
    
    # 可视化第一个文件
    print(f"\n可视化: {existing_files[0]}")
    visualize_timeline(existing_files[0])
    
    # 如果有多个文件，进行对比
    if len(existing_files) > 1:
        compare_timelines(existing_files)


if __name__ == "__main__":
    main()
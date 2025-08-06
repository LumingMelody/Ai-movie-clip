# 火山引擎视频编辑API使用指南

## 1. 准备工作

### 1.1 获取API密钥

1. 登录[火山引擎控制台](https://console.volcengine.com)
2. 进入"密钥管理"页面
3. 创建新的访问密钥（Access Key）
4. 保存 `Access Key ID` 和 `Secret Access Key`

### 1.2 设置环境变量

```bash
# 在终端设置环境变量
export VOLCANO_ACCESS_KEY_ID="你的访问密钥ID"
export VOLCANO_SECRET_ACCESS_KEY="你的访问密钥Secret"

# 或者在 ~/.bashrc 或 ~/.zshrc 中永久设置
echo 'export VOLCANO_ACCESS_KEY_ID="你的访问密钥ID"' >> ~/.zshrc
echo 'export VOLCANO_SECRET_ACCESS_KEY="你的访问密钥Secret"' >> ~/.zshrc
source ~/.zshrc
```

### 1.3 安装依赖

```bash
# 安装火山引擎Python SDK
pip install volcengine

# 安装TOS SDK（用于文件上传）
pip install tos
```

## 2. API调用流程

### 2.1 完整的视频编辑流程

```python
import os
import json
import time
from volcengine.vod.VodService import VodService

# 初始化服务
vod_service = VodService()
vod_service.set_ak(os.environ.get('VOLCANO_ACCESS_KEY_ID'))
vod_service.set_sk(os.environ.get('VOLCANO_SECRET_ACCESS_KEY'))

# 1. 上传视频
def upload_video(file_path):
    """上传本地视频到火山引擎"""
    
    # 申请上传
    resp = vod_service.upload_media_by_file(file_path)
    
    if resp['ResponseMetadata']['Error']['Code'] == '':
        vid = resp['Result']['Data']['Vid']
        print(f"视频上传成功，Vid: {vid}")
        return vid
    else:
        print(f"上传失败: {resp['ResponseMetadata']['Error']}")
        return None

# 2. 创建编辑任务
def create_edit_task(vid):
    """创建视频编辑任务"""
    
    edit_param = {
        "Canvas": {
            "Width": 1080,
            "Height": 1920,
            "Color": "#000000"
        },
        "Track": [{
            "Type": "video",
            "Id": "video_track_1",
            "Segments": [{
                "MaterialId": vid,
                "TargetTimeRange": [0, 5000],  # 5秒
                "SourceTimeRange": [0, 5000],
                "Operations": [{
                    "Type": "filter",
                    "Config": {
                        "Name": "1184003"  # 清晰滤镜
                    }
                }]
            }]
        }],
        "GlobalOperations": [{
            "Type": "transition",
            "TargetId": ["video_track_1"],
            "Config": {
                "Name": "1182355",  # 叶片翻转转场
                "Duration": 1000
            }
        }],
        "Output": {
            "Container": {
                "Format": "mp4"
            },
            "Video": {
                "Codec": "h264",
                "Width": 1080,
                "Height": 1920,
                "Fps": 30,
                "Bitrate": 5000
            },
            "Audio": {
                "Codec": "aac",
                "SampleRate": 44100,
                "Bitrate": 128
            }
        }
    }
    
    # 提交编辑任务
    req = {
        "TemplateId": "DirectEdit",  # 使用直接编辑模板
        "Space": "your_space",  # 你的空间名
        "EditParam": json.dumps(edit_param),
        "CallbackArgs": ""
    }
    
    resp = vod_service.submit_direct_edit_task(req)
    
    if resp['ResponseMetadata']['Error']['Code'] == '':
        request_id = resp['Result']['RequestId']
        print(f"编辑任务创建成功，RequestId: {request_id}")
        return request_id
    else:
        print(f"创建任务失败: {resp['ResponseMetadata']['Error']}")
        return None

# 3. 查询任务状态
def get_task_result(request_id):
    """查询编辑任务结果"""
    
    max_attempts = 60  # 最多等待5分钟
    attempt = 0
    
    while attempt < max_attempts:
        req = {"RequestId": request_id}
        resp = vod_service.get_direct_edit_result(req)
        
        if resp['ResponseMetadata']['Error']['Code'] == '':
            status = resp['Result']['Status']
            print(f"任务状态: {status}")
            
            if status == 'Success':
                output_vid = resp['Result']['OutputVid']
                print(f"编辑完成，输出Vid: {output_vid}")
                return output_vid
            elif status == 'Failed':
                print(f"编辑失败: {resp['Result']['Extra']}")
                return None
        
        time.sleep(5)
        attempt += 1
    
    print("任务超时")
    return None

# 主流程
def process_video(file_path):
    """完整的视频处理流程"""
    
    print(f"开始处理视频: {file_path}")
    
    # 1. 上传视频
    vid = upload_video(file_path)
    if not vid:
        return
    
    # 2. 创建编辑任务
    request_id = create_edit_task(vid)
    if not request_id:
        return
    
    # 3. 等待任务完成
    output_vid = get_task_result(request_id)
    if output_vid:
        print(f"视频处理完成！输出Vid: {output_vid}")
        # 可以通过 output_vid 获取播放地址
        play_info = vod_service.get_play_info({"Vid": output_vid})
        if play_info['ResponseMetadata']['Error']['Code'] == '':
            for item in play_info['Result']['PlayInfoList']:
                print(f"播放地址: {item['MainPlayUrl']}")
```

### 2.2 使用特效ID

我们已经整理了完整的特效ID列表：

#### 滤镜效果
```python
filters = {
    "1184003": "清晰",
    "1184004": "午后", 
    "1184005": "MUJI",
    "1184006": "白皙",
    "1183991": "香港",
    "1183952": "赏味",
    # ... 更多滤镜
}
```

#### 转场效果
```python
transitions = {
    "1182355": "叶片翻转",
    "1182356": "百叶窗",
    "1182357": "风吹",
    "1182367": "故障转换",
    "1182376": "圆形打开",
    # ... 更多转场
}
```

#### 视频动画
```python
video_animations = {
    "1180338": "放大入场",
    "1180337": "渐显入场",
    "1180382": "渐隐出场",
    # ... 更多动画
}
```

## 3. 测试脚本

### 3.1 快速测试脚本

```bash
# 运行我们提供的测试脚本
python test_volcano_api.py

# 如果已设置环境变量，会显示API配置信息
# 如果未设置，会提示如何获取和配置密钥
```

### 3.2 本地模拟测试

如果还没有API密钥，可以使用本地实现进行测试：

```bash
# 使用本地实现测试转场效果
python test_volcano_real_video.py

# 使用改进版测试
python test_volcano_v2.py
```

## 4. 常见问题

### Q1: 如何获取火山引擎账号？
A: 访问 [火山引擎官网](https://www.volcengine.com) 注册账号。

### Q2: API调用是否收费？
A: 火山引擎视频编辑服务按使用量收费，具体价格请查看官方定价页面。

### Q3: 支持哪些视频格式？
A: 支持常见视频格式：MP4、MOV、AVI、FLV等。

### Q4: 视频大小有限制吗？
A: 单个视频文件建议不超过4GB，时长不超过2小时。

### Q5: 如何处理大文件？
A: 大文件建议使用分片上传，火山引擎TOS SDK支持自动分片。

## 5. 进阶使用

### 5.1 批量处理

```python
def batch_process_videos(video_list, effect_config):
    """批量处理多个视频"""
    results = []
    
    for video_path in video_list:
        try:
            result = process_video_with_effects(video_path, effect_config)
            results.append({
                'video': video_path,
                'status': 'success',
                'output': result
            })
        except Exception as e:
            results.append({
                'video': video_path,
                'status': 'failed',
                'error': str(e)
            })
    
    return results
```

### 5.2 自定义特效组合

```python
# 抖音风格配置
douyin_style = {
    'filters': ['1183991'],  # 香港滤镜
    'transitions': ['1182367'],  # 故障转换
    'text_animations': ['1181434']  # 文字渐显
}

# 产品展示配置
product_showcase = {
    'filters': ['1184003'],  # 清晰滤镜
    'transitions': ['1182355'],  # 叶片翻转
    'video_animations': ['1180338']  # 放大入场
}
```

## 6. 参考资源

- [火山引擎官方文档](https://www.volcengine.com/docs/4/102412)
- [视频编辑API参考](https://www.volcengine.com/docs/4/65925)
- [SDK使用指南](https://github.com/volcengine/volc-sdk-python)
- [技术支持](https://www.volcengine.com/support)

## 7. 联系支持

如遇到问题，可通过以下方式获取帮助：
- 火山引擎控制台工单系统
- 技术支持邮箱：support@volcengine.com
- 开发者社区：https://forum.volcengine.com
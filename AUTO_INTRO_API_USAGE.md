# 自动产品介绍API使用文档

## API概述

在 `app_0715.py` 中新增了3个API接口来控制自动产品介绍功能：

1. `POST /api/auto-intro/start` - 启动自动产品介绍客户端
2. `POST /api/auto-intro/stop` - 停止自动产品介绍客户端  
3. `GET /api/auto-intro/status` - 获取客户端状态

## 接口详情

### 1. 启动自动产品介绍客户端

**POST** `/api/auto-intro/start`

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| host | string | 否 | "10.211.55.3" | WebSocket服务器IP地址 |
| port | int | 否 | 8888 | WebSocket服务器端口 |
| reply_probability | float | 否 | 0.3 | 随机回复概率(0-1) |
| max_queue_size | int | 否 | 5 | 最大消息队列长度 |
| no_message_timeout | int | 否 | 90 | 无消息超时时间（秒） |
| auto_introduce_interval | int | 否 | 120 | 自动介绍间隔（秒） |
| auto_reconnect | bool | 否 | true | 是否启用自动重连 |
| max_reconnect_attempts | int | 否 | 10 | 最大重连次数 |
| reconnect_delay | int | 否 | 5 | 重连延迟（秒） |
| tenant_id | string | 否 | null | 租户ID |
| id | string | 否 | null | 业务ID |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/auto-intro/start" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "10.211.55.3",
       "port": 8888,
       "no_message_timeout": 90,
       "auto_introduce_interval": 120,
       "reply_probability": 0.3,
       "max_queue_size": 5,
       "auto_reconnect": true,
       "max_reconnect_attempts": 10,
       "reconnect_delay": 5
     }'
```

#### 成功响应

```json
{
  "code": 200,
  "message": "自动产品介绍客户端启动成功",
  "data": {
    "status": "connected",
    "host": "10.211.55.3",
    "port": 8888,
    "no_message_timeout": 90,
    "auto_introduce_interval": 120,
    "reply_probability": 0.3,
    "max_queue_size": 5,
    "auto_reconnect": true,
    "max_reconnect_attempts": 10,
    "reconnect_delay": 5
  },
  "task_id": "uuid-string",
  "tenant_id": null,
  "business_id": null
}
```

### 2. 停止自动产品介绍客户端

**POST** `/api/auto-intro/stop`

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| tenant_id | string | 否 | null | 租户ID |
| id | string | 否 | null | 业务ID |

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/auto-intro/stop" \
     -H "Content-Type: application/json" \
     -d '{}'
```

#### 成功响应

```json
{
  "code": 200,
  "message": "自动产品介绍客户端已停止",
  "data": {
    "status": "disconnected",
    "connection_type": "auto_intro_client"
  },
  "task_id": "uuid-string",
  "tenant_id": null,
  "business_id": null
}
```

### 3. 获取客户端状态

**GET** `/api/auto-intro/status`

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/auto-intro/status"
```

#### 成功响应（已连接）

```json
{
  "code": 200,
  "message": "获取状态成功",
  "data": {
    "status": "connected",
    "is_running": true,
    "host": "10.211.55.3",
    "port": 8888,
    "no_message_timeout": 90,
    "auto_introduce_interval": 120,
    "reply_probability": 0.3,
    "max_queue_size": 5,
    "auto_reconnect": true,
    "max_reconnect_attempts": 10,
    "reconnect_delay": 5,
    "last_message_time": 1753168115.66,
    "last_auto_introduce_time": 1753168200.12
  }
}
```

#### 成功响应（未创建）

```json
{
  "code": 200,
  "message": "获取状态成功",
  "data": {
    "status": "not_created",
    "is_running": false,
    "message": "自动产品介绍客户端尚未创建"
  }
}
```

## 使用流程

### 1. 基本使用流程

1. **启动服务**：调用 `/api/auto-intro/start` 启动自动产品介绍功能
2. **查看状态**：调用 `/api/auto-intro/status` 查看当前运行状态
3. **停止服务**：调用 `/api/auto-intro/stop` 停止功能

### 2. 带参数的启动示例

```bash
# 启动自动产品介绍，连接到特定的WebSocket服务器
curl -X POST "http://localhost:8000/api/auto-intro/start" \
     -H "Content-Type: application/json" \
     -d '{
       "host": "192.168.1.100",
       "port": 9999,
       "no_message_timeout": 120,
       "auto_introduce_interval": 180,
       "reply_probability": 0.5
     }'
```

### 3. Python代码示例

```python
import requests
import json

# 基础配置
base_url = "http://localhost:8000"

def start_auto_intro(host="10.211.55.3", port=8888, timeout=90, interval=120):
    """启动自动产品介绍"""
    url = f"{base_url}/api/auto-intro/start"
    data = {
        "host": host,
        "port": port,
        "no_message_timeout": timeout,
        "auto_introduce_interval": interval,
        "reply_probability": 0.3,
        "max_queue_size": 5
    }
    
    response = requests.post(url, json=data)
    return response.json()

def stop_auto_intro():
    """停止自动产品介绍"""
    url = f"{base_url}/api/auto-intro/stop"
    response = requests.post(url, json={})
    return response.json()

def get_auto_intro_status():
    """获取状态"""
    url = f"{base_url}/api/auto-intro/status"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 启动
    result = start_auto_intro("10.211.55.3", 8888, 90, 120)
    print("启动结果:", json.dumps(result, indent=2, ensure_ascii=False))
    
    # 查看状态
    status = get_auto_intro_status()
    print("当前状态:", json.dumps(status, indent=2, ensure_ascii=False))
    
    # 停止
    # stop_result = stop_auto_intro()
    # print("停止结果:", json.dumps(stop_result, indent=2, ensure_ascii=False))
```

## 错误处理

### 常见错误码

- `500` - 内部服务器错误（连接失败、启动失败等）
- `422` - 请求参数验证失败

### 错误响应示例

```json
{
  "detail": {
    "status": "error",
    "message": "连接WebSocket服务器失败",
    "host": "10.211.55.3",
    "port": 8888,
    "task_id": "uuid-string",
    "tenant_id": null,
    "business_id": null
  }
}
```

## 自动重连功能

系统内置了强大的自动重连机制，确保WebSocket连接的持久性：

### 重连特性

1. **自动检测**：每5秒检查一次连接状态
2. **智能重连**：连接断开时自动尝试重连
3. **参数可配置**：
   - `auto_reconnect`: 是否启用自动重连（默认true）
   - `max_reconnect_attempts`: 最大重连次数（默认10次）
   - `reconnect_delay`: 每次重连的延迟时间（默认5秒）

### 重连流程

1. 检测到连接断开
2. 清理现有连接资源
3. 等待指定延迟时间
4. 尝试重新建立WebSocket连接
5. 重新启动消息监听任务
6. 成功后重置重连计数器

### 重连日志示例

```
🔄 检测到连接断开，开始第1次重连...
🔌 重新连接到WebSocket服务器 ws://10.211.55.3:8888...
✅ 第1次重连成功！
```

## 注意事项

1. **配置要求**：确保已正确配置DashScope API Key
2. **产品配置**：确保 `live_config/product_config.json` 包含完整的产品信息
3. **网络连通性**：确保能连接到指定的WebSocket服务器
4. **资源管理**：启动新客户端时，会自动关闭已有的客户端
5. **状态管理**：支持租户ID和业务ID的任务状态跟踪
6. **重连保障**：启用自动重连后，系统会持续保持WebSocket连接
7. **故障恢复**：连接断开后自动恢复，无需手动干预
8. **存储优化**：音频文件播放完成后自动删除，节省磁盘空间

## 监控和调试

- 查看服务器日志了解详细运行状态
- 使用状态查询接口监控连接状态
- 检查WebSocket服务器是否正常运行
- 确认产品配置和语音配置文件正确
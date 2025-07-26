#!/usr/bin/env python3
"""
WebSocket服务器 - 用于抖音直播消息监听
支持WebSocket协议，可以与前端或其他WebSocket客户端通信
"""

import asyncio
import json
import websockets
from datetime import datetime
from core.cliptemplate.coze.auto_live_reply import config_manager, SocketServer
import random

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8888):
        # 验证IP地址是否可用（复用SocketServer的逻辑）
        if host not in ['0.0.0.0', '127.0.0.1', 'localhost']:
            import socket as sock
            import subprocess
            import re
            
            try:
                # 尝试获取系统所有IP地址
                hostname = sock.gethostname()
                all_ips = sock.gethostbyname_ex(hostname)[2]
                
                # 添加一些常见的本地IP获取方式
                try:
                    result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                    ips_from_ifconfig = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    all_ips.extend(ips_from_ifconfig)
                except:
                    pass
                
                all_ips = list(set(all_ips))  # 去重
                
                if host not in all_ips:
                    print(f"⚠️ 警告: IP地址 {host} 不在系统网络接口中")
                    print(f"📋 可用的IP地址: {all_ips}")
                    print(f"🔄 将使用 0.0.0.0 来监听所有接口")
                    host = '0.0.0.0'
            except Exception as e:
                print(f"❌ 检查IP地址时出错: {e}")
                print(f"🔄 将使用 0.0.0.0 来监听所有接口")
                host = '0.0.0.0'
        
        self.host = host
        self.port = port
        self.clients = set()
        # 使用SocketServer的逻辑来生成回复
        self.socket_server = SocketServer(host, port)
        print(f"🚀 WebSocket服务器初始化 - {self.host}:{self.port}")
    
    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"✅ 新客户端连接: {websocket.remote_address}")
        
        # 发送欢迎消息
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "连接成功！欢迎使用抖音直播助手",
            "timestamp": datetime.now().isoformat(),
            "product_info": config_manager.product_info
        }, ensure_ascii=False))
    
    async def unregister(self, websocket):
        self.clients.remove(websocket)
        print(f"👋 客户端断开连接: {websocket.remote_address}")
    
    async def handle_message(self, websocket, message):
        """处理接收到的消息"""
        try:
            # 尝试解析JSON
            try:
                data = json.loads(message)
                msg_type = data.get('type', 'chat')
                content = data.get('content', message)
            except:
                # 如果不是JSON，当作普通文本处理
                msg_type = 'chat'
                content = message
            
            print(f"📨 收到消息 [{msg_type}]: {content}")
            
            # 根据消息类型处理
            if msg_type == 'live_config':
                # 配置更新
                response = await self.handle_config_update(data)
            elif msg_type == 'status':
                # 状态查询
                response = {
                    "type": "status",
                    "server": "running",
                    "clients": len(self.clients),
                    "product": config_manager.product_info['product_name'],
                    "voice": config_manager.voice_config['voice']
                }
            else:
                # 普通聊天消息，使用SocketServer的方法生成回复
                reply = self.socket_server.process_message(content)
                response = {
                    "type": "reply",
                    "question": content,
                    "answer": reply,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 发送响应
            await websocket.send(json.dumps(response, ensure_ascii=False))
            
            # 广播给其他客户端（可选）
            if msg_type == 'chat' and len(self.clients) > 1:
                broadcast_msg = {
                    "type": "broadcast",
                    "from": str(websocket.remote_address),
                    "content": content,
                    "reply": response['answer']
                }
                await self.broadcast(json.dumps(broadcast_msg, ensure_ascii=False), websocket)
                
        except Exception as e:
            error_response = {
                "type": "error",
                "message": f"处理消息时出错: {str(e)}"
            }
            await websocket.send(json.dumps(error_response, ensure_ascii=False))
    
    async def handle_config_update(self, data):
        """处理配置更新请求"""
        config_type = data.get('config_type')
        updates = data.get('updates', {})
        
        if config_type == 'product':
            success = config_manager.update_product_config(updates)
            return {
                "type": "config_update",
                "config_type": "product",
                "success": success,
                "message": "产品配置更新成功" if success else "产品配置更新失败",
                "data": config_manager.product_info
            }
        elif config_type == 'voice':
            success = config_manager.update_voice_config(updates)
            return {
                "type": "config_update",
                "config_type": "voice",
                "success": success,
                "message": "语音配置更新成功" if success else "语音配置更新失败",
                "data": config_manager.voice_config
            }
        else:
            return {
                "type": "error",
                "message": "未知的配置类型"
            }
    
    async def broadcast(self, message, sender=None):
        """广播消息给所有客户端（除了发送者）"""
        if self.clients:
            tasks = []
            for client in self.clients:
                if client != sender and client.open:
                    tasks.append(asyncio.create_task(client.send(message)))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def handler(self, websocket, path):
        """WebSocket连接处理器"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start_server(self):
        """启动WebSocket服务器"""
        print(f"🌐 正在启动WebSocket服务器...")
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"✅ WebSocket服务器已启动 - ws://{self.host}:{self.port}")
            print(f"📦 当前产品: {config_manager.product_info['product_name']}")
            print(f"🎤 当前语音: {config_manager.voice_config['voice']}")
            print("⌛ 等待客户端连接...")
            await asyncio.Future()  # 永久运行

# 测试客户端示例
async def test_client():
    """测试WebSocket客户端"""
    uri = "ws://localhost:8888"
    async with websockets.connect(uri) as websocket:
        # 接收欢迎消息
        welcome = await websocket.recv()
        print(f"收到: {welcome}")
        
        # 发送测试消息
        test_messages = [
            "你们的产品有什么功能？",
            "价格多少？",
            {"type": "status"},
            {"type": "live_config", "config_type": "product", "updates": {"price": "199元"}}
        ]
        
        for msg in test_messages:
            if isinstance(msg, dict):
                await websocket.send(json.dumps(msg))
            else:
                await websocket.send(msg)
            
            response = await websocket.recv()
            print(f"发送: {msg}")
            print(f"收到: {response}")
            print("-" * 50)
            await asyncio.sleep(1)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 运行测试客户端
        asyncio.run(test_client())
    else:
        # 运行服务器
        server = WebSocketServer(host='0.0.0.0', port=8888)
        asyncio.run(server.start_server())
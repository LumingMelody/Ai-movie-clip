#!/usr/bin/env python3
"""
WebSocket客户端 - 连接到远程WebSocket服务器
"""

import asyncio
import websockets
import json
import logging
from typing import Optional

class ManualWebSocketClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        self.connected = False
        self.running = False
        self.listen_task = None
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            print(f"🔌 正在连接到 {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self.running = True
            print(f"✅ 已连接到 {self.uri}")
            
            # 启动消息监听任务
            self.listen_task = asyncio.create_task(self._listen_loop())
            
            return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            self.connected = False
            self.running = False
            return False
    
    async def close(self):
        """关闭连接"""
        try:
            self.running = False
            self.connected = False
            
            if self.listen_task:
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
            print("🔌 已断开连接")
            return True
            
        except Exception as e:
            print(f"❌ 断开连接失败: {e}")
            return False
    
    async def send_message(self, message: str):
        """发送消息到服务器"""
        if not self.connected or not self.websocket:
            print("⚠️ 未连接到服务器")
            return False
            
        try:
            await self.websocket.send(message)
            print(f"📤 发送消息: {message}")
            return True
            
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")
            return False
    
    async def receive_message(self):
        """接收服务器消息"""
        if not self.connected or not self.websocket:
            return None
            
        try:
            message = await self.websocket.recv()
            print(f"📥 收到消息: {message}")
            return message
            
        except websockets.exceptions.ConnectionClosed:
            print("🔌 连接已关闭")
            self.connected = False
            self.running = False
            return None
            
        except Exception as e:
            print(f"❌ 接收消息失败: {e}")
            return None
    
    async def _listen_loop(self):
        """消息监听循环"""
        try:
            while self.running:
                message = await self.receive_message()
                if message:
                    await self._process_message(message)
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("📴 消息监听任务已取消")
        except Exception as e:
            print(f"❌ 消息监听错误: {e}")
            self.connected = False
            self.running = False
    
    async def _process_message(self, message: str):
        """处理接收到的消息"""
        try:
            # 尝试解析JSON
            try:
                data = json.loads(message)
                print(f"📨 处理JSON消息: {data}")
            except json.JSONDecodeError:
                # 不是JSON，作为普通文本处理
                print(f"💬 文本消息: {message}")
                
        except Exception as e:
            print(f"❌ 处理消息时出错: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected and self.websocket is not None


# 全局客户端实例
websocket_client = None

async def process_message(message: str):
    """处理从服务器接收的消息"""
    try:
        # 尝试解析JSON
        try:
            data = json.loads(message)
            print(f"📨 处理JSON消息: {data}")
            
            # 根据消息类型做不同处理
            if data.get('type') == 'live_message':
                content = data.get('content', '')
                print(f"🎥 直播消息: {content}")
                
            elif data.get('type') == 'reply':
                answer = data.get('answer', '')
                print(f"🤖 AI回复: {answer}")
                
        except json.JSONDecodeError:
            # 不是JSON，作为普通文本处理
            print(f"💬 文本消息: {message}")
            
    except Exception as e:
        print(f"❌ 处理消息时出错: {e}")


# 手动WebSocket连接函数
async def manual_websocket_connect():
    """使用手动WebSocket客户端"""
    client = ManualWebSocketClient("10.211.55.3", 8888)

    try:
        await client.connect()

        while True:
            message = await client.receive_message()
            if message:
                await process_message(message)
            else:
                await asyncio.sleep(0.1)  # 避免忙等待

    except KeyboardInterrupt:
        print("👋 手动断开连接")
    except Exception as e:
        print(f"❌ 手动连接错误: {e}")
    finally:
        await client.close()
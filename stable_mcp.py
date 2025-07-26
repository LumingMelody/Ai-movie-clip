# -*- coding: utf-8 -*-
# @Time    : 2025/6/16 09:28
# @Author  : 蔍鸣霸霸
# @FileName: stable_mcp.py
# @Software: PyCharm
# @Blog    ：只因你太美


# !/usr/bin/env python3
"""
稳定版MCP服务器 - 解决连接关闭问题
"""

import asyncio
import json
import sys
import os
import logging
from typing import List, Dict, Any

# 设置日志到文件和stderr
log_file = '/tmp/mcp_server.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

logger.info("=== MCP服务器启动 ===")
logger.info(f"Python版本: {sys.version}")
logger.info(f"工作目录: {os.getcwd()}")
logger.info(f"日志文件: {log_file}")

# 导入MCP相关模块
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, Resource
    import mcp.server.stdio

    logger.info("✅ MCP模块导入成功")
except ImportError as e:
    logger.error(f"❌ MCP模块导入失败: {e}")
    logger.error("请运行: pip install mcp")
    sys.exit(1)

# 导入其他必要模块
try:
    # 尝试不同的导入方式
    try:
        from mcp.server.models import InitializationOptions

        logger.info("✅ InitializationOptions导入成功 (models)")
    except ImportError:
        try:
            from mcp.types import InitializationOptions

            logger.info("✅ InitializationOptions导入成功 (types)")
        except ImportError:
            # 创建一个简单的类
            class InitializationOptions:
                def __init__(self, server_name: str, server_version: str, capabilities: dict):
                    self.server_name = server_name
                    self.server_version = server_version
                    self.capabilities = capabilities


            logger.info("✅ 使用自定义InitializationOptions")

    try:
        from mcp.server.notifications import NotificationOptions

        logger.info("✅ NotificationOptions导入成功")
    except ImportError:
        # 创建一个简单的类
        class NotificationOptions:
            def __init__(self):
                pass


        logger.info("✅ 使用自定义NotificationOptions")

except Exception as e:
    logger.error(f"❌ 导入辅助类失败: {e}")
    sys.exit(1)

# 创建服务器实例
try:
    server = Server("stable-mcp-server")
    logger.info("✅ MCP服务器实例创建成功")
except Exception as e:
    logger.error(f"❌ 服务器创建失败: {e}")
    sys.exit(1)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """返回可用工具列表"""
    logger.info("📋 收到工具列表请求")

    tools = [
        Tool(
            name="ping",
            description="简单的ping测试，返回pong",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="echo",
            description="回显输入的文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要回显的消息"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="status",
            description="获取服务器状态信息",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

    logger.info(f"📋 返回 {len(tools)} 个工具")
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    logger.info(f"🔧 收到工具调用: {name}")
    logger.info(f"🔧 参数: {arguments}")

    try:
        if name == "ping":
            response = "🏓 pong! MCP服务器正常运行。"
            logger.info(f"📤 ping响应: {response}")
            return [TextContent(type="text", text=response)]

        elif name == "echo":
            message = arguments.get("message", "")
            response = f"🔊 回显: {message}"
            logger.info(f"📤 echo响应: {response}")
            return [TextContent(type="text", text=response)]

        elif name == "status":
            import time
            status_info = {
                "server_name": "stable-mcp-server",
                "status": "running",
                "uptime": time.time(),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }
            response = f"📊 服务器状态:\n{json.dumps(status_info, indent=2, ensure_ascii=False)}"
            logger.info(f"📤 status响应长度: {len(response)}")
            return [TextContent(type="text", text=response)]

        else:
            error_response = f"❌ 未知工具: {name}"
            logger.warning(f"⚠️ {error_response}")
            return [TextContent(type="text", text=error_response)]

    except Exception as e:
        error_response = f"💥 工具执行错误: {str(e)}"
        logger.error(f"💥 工具调用异常: {e}", exc_info=True)
        return [TextContent(type="text", text=error_response)]


@server.list_resources()
async def list_resources() -> List[Resource]:
    """返回可用资源列表"""
    logger.info("📚 收到资源列表请求")
    return []


async def main():
    """主函数"""
    logger.info("🚀 启动MCP服务器主函数")

    try:
        # 创建stdio服务器
        logger.info("🔗 创建stdio连接...")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("✅ stdio服务器创建成功")
            logger.info("🎯 等待Cherry Studio连接...")

            # 准备初始化选项
            try:
                notification_options = NotificationOptions()
                capabilities = server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities={}
                )

                init_options = InitializationOptions(
                    server_name="stable-mcp-server",
                    server_version="1.0.0",
                    capabilities=capabilities
                )

                logger.info(f"⚙️ 服务器配置完成")
                logger.info(
                    f"⚙️ 能力: {list(capabilities.keys()) if isinstance(capabilities, dict) else str(capabilities)}")

            except Exception as e:
                logger.error(f"❌ 初始化配置失败: {e}")
                raise

            # 运行服务器
            logger.info("🏃 开始运行MCP服务器...")
            await server.run(
                read_stream,
                write_stream,
                init_options
            )

    except asyncio.CancelledError:
        logger.info("🛑 服务器被取消")
    except Exception as e:
        logger.error(f"💀 主函数运行错误: {e}")
        logger.error("💀 详细错误信息:", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("🎬 启动稳定版MCP服务器")

    try:
        # 确保事件循环正常运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info("🔄 事件循环创建成功")

        # 运行主函数
        loop.run_until_complete(main())

    except KeyboardInterrupt:
        logger.info("⏹️ 收到键盘中断信号")
    except Exception as e:
        logger.error(f"💀 服务器启动失败: {e}")
        logger.error("💀 完整错误信息:", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("🏁 MCP服务器关闭")
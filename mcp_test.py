# -*- coding: utf-8 -*-
# @Time    : 2025/6/16 09:11
# @Author  : 蔍鸣霸霸
# @FileName: mcp_test.py
# @Software: PyCharm
# @Blog    ：只因你太美


# !/usr/bin/env python3
"""
简化的MCP测试服务器
用于验证基础连接是否正常
"""

import asyncio
import sys
import os

# 添加调试输出
print("=== 简化MCP测试服务器启动 ===", file=sys.stderr)
print(f"Python版本: {sys.version}", file=sys.stderr)
print(f"工作目录: {os.getcwd()}", file=sys.stderr)

try:
    from mcp.server import Server, NotificationOptions
    from mcp.types import Tool, TextContent
    import mcp.server.stdio

    print("✓ MCP模块导入成功", file=sys.stderr)
except ImportError as e:
    print(f"✗ MCP模块导入失败: {e}", file=sys.stderr)
    print("请安装MCP: pip install mcp", file=sys.stderr)
    sys.exit(1)

# 创建服务器
server = Server("simple-test-server")
print("✓ MCP服务器创建成功", file=sys.stderr)


@server.list_tools()
async def handle_list_tools():
    """列出可用工具"""
    return [
        Tool(
            name="test_connection",
            description="测试MCP连接是否正常",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "测试消息",
                        "default": "Hello MCP!"
                    }
                }
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """处理工具调用"""
    if name == "test_connection":
        message = arguments.get("message", "Hello MCP!")
        return [TextContent(
            type="text",
            text=f"✅ MCP连接测试成功！\n收到消息: {message}\n服务器正在正常运行。"
        )]
    else:
        return [TextContent(
            type="text",
            text=f"❌ 未知工具: {name}"
        )]


async def main():
    """主函数"""
    print("启动MCP stdio服务器...", file=sys.stderr)

    # 导入必要的类
    from mcp.server.models import InitializationOptions

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print("✓ stdio服务器创建成功，等待连接...", file=sys.stderr)
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="simple-test-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    print("启动简化MCP测试服务器", file=sys.stderr)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("服务器被用户中断", file=sys.stderr)
    except Exception as e:
        print(f"服务器运行错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
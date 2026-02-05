#!/usr/bin/env python3
"""
启动知识代理MCP服务器 - 完整CORS支持
通过自定义Uvicorn配置解决CORS问题
"""

import sys
import logging
from pathlib import Path
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.routing import Route, Mount

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from knowledge_agent.server import KnowledgeMCPServer
from knowledge_agent.core.logging_config import setup_logging


def create_app_with_cors():
    """创建带CORS支持的应用"""
    
    # Setup logging
    setup_logging(level=logging.INFO, structured=True)
    logger = logging.getLogger("knowledge_agent.main")
    
    logger.info("=" * 60)
    logger.info("创建MCP服务器...")
    logger.info("=" * 60)
    
    # Create MCP server
    mcp_server = KnowledgeMCPServer("personal-knowledge-agent")
    
    # Get the FastMCP app
    fastmcp_app = mcp_server.get_app()
    
    # Get the SSE Starlette app from FastMCP
    # FastMCP.sse_app() is a method that returns the Starlette app
    if hasattr(fastmcp_app, 'sse_app') and callable(fastmcp_app.sse_app):
        starlette_app = fastmcp_app.sse_app()
        logger.info("✓ 获取到SSE Starlette应用")
        logger.info(f"  应用类型: {type(starlette_app)}")
    else:
        logger.error("✗ 无法获取SSE应用")
        raise RuntimeError("Cannot access SSE app from FastMCP")
    
    # Add CORS middleware directly to the Starlette app
    starlette_app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],  # 允许所有来源
        allow_credentials=True,
        allow_methods=['*'],  # 允许所有方法
        allow_headers=['*'],  # 允许所有头
        expose_headers=['*'],
    )
    
    logger.info("✓ CORS中间件已配置")
    logger.info("=" * 60)
    
    return starlette_app, mcp_server


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 启动个人知识管理智能体 MCP服务器")
    print("=" * 60)
    print("📡 传输模式: SSE (Server-Sent Events)")
    print("🌐 Web访问: http://localhost:8000")
    print("📋 SSE端点: http://localhost:8000/sse")
    print("🔓 CORS: 已启用（完整支持）")
    print("⚠️  按Ctrl+C停止服务器")
    print("=" * 60)
    print()
    
    try:
        # Create app with CORS
        app, mcp_server = create_app_with_cors()
        
        # Run with uvicorn
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        server.run()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("✅ 服务器已停止")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

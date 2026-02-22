"""
知识管理代理的主 MCP 服务器实现模块。
"""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from ..core import KnowledgeAgentCore
from .mcp_tools import register_knowledge_tools
from .mcp_resources import register_knowledge_resources
from .mcp_prompts import register_knowledge_prompts


class KnowledgeMCPServer:
    """
    个人知识管理 MCP 服务器。

    提供 MCP 兼容的接口，用于知识收集、组织和搜索功能。
    """

    def __init__(self, server_name: str = "personal-knowledge-agent"):
        """
        初始化知识管理 MCP 服务器。

        Args:
            server_name: 服务器名称
        """
        self.server_name = server_name
        self.logger = logging.getLogger(f"knowledge_agent.{server_name}")

        # 服务器状态
        self._initialized = False
        self._running = False

        try:
            self.logger.info("=" * 60)
            self.logger.info(f"Initializing Knowledge MCP Server: {server_name}")
            self.logger.info("=" * 60)

            # 初始化 FastMCP 应用
            self.app = FastMCP(server_name)
            self.logger.info("✓ FastMCP application created")

            # 初始化知识代理核心
            self.knowledge_core = KnowledgeAgentCore()
            self.logger.info("✓ Knowledge agent core initialized")

            # 注册 MCP 工具和资源
            self._register_components()

            self._initialized = True
            self.logger.info("=" * 60)
            self.logger.info(f"Knowledge MCP server initialized successfully")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP server: {e}")
            # 初始化失败时进行清理
            if hasattr(self, 'knowledge_core'):
                self.knowledge_core.shutdown()
            raise

    def _register_components(self) -> None:
        """注册 MCP 工具和资源到服务器。"""
        try:
            self.logger.info("Registering MCP components...")

            # 注册知识管理工具
            register_knowledge_tools(self.app, self.knowledge_core)
            self.logger.info("✓ Knowledge tools registered")

            # 注册知识资源
            register_knowledge_resources(self.app, self.knowledge_core)
            self.logger.info("✓ Knowledge resources registered")

            # 注册知识提示模板
            register_knowledge_prompts(self.app, self.knowledge_core)
            self.logger.info("✓ Knowledge prompts registered")

            self.logger.info("MCP components registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register MCP components: {e}")
            raise

    def get_server_info(self) -> Dict[str, Any]:
        """
        获取服务器信息及其功能。

        Returns:
            Dict[str, Any]: 服务器信息字典
        """
        return {
            "name": self.server_name,
            "version": "0.1.0",
            "description": "Personal Knowledge Management Agent MCP Server",
            "capabilities": {
                "knowledge_collection": True,
                "knowledge_organization": True,
                "semantic_search": True,
                "knowledge_graph": True,
                "data_export_import": True,
            },
            "supported_sources": [
                "documents",
                "pdf",
                "web_pages",
                "code_files",
                "images",
            ],
        }

    def start_stdio(self) -> None:
        """通过 stdio 传输方式启动服务器。"""
        if not self._initialized:
            raise RuntimeError("Server not initialized")

        self.logger.info("=" * 60)
        self.logger.info(f"Starting {self.server_name} via stdio transport")
        self.logger.info("=" * 60)

        self._running = True

        try:
            self.app.run(transport="stdio")
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self._running = False
            self.shutdown()

    def start_sse(self, host: str = "localhost", port: int = 8000, mount_path: str = "/sse") -> None:
        """
        通过 SSE（服务器推送事件）传输方式启动服务器。

        SSE 允许服务器向 Web 客户端推送实时更新。
        适用于需要实时更新的 Web 界面。

        Args:
            host: 监听主机地址（默认：localhost）
            port: 监听端口号（默认：8000）
            mount_path: SSE 端点路径（默认：/sse）
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized")

        self.logger.info("=" * 60)
        self.logger.info(f"Starting {self.server_name} via SSE transport")
        self.logger.info(f"Listening on: {host}:{port}")
        self.logger.info(f"SSE endpoint: {mount_path}")
        self.logger.info("=" * 60)

        self._running = True

        try:
            self.app.run(transport="sse", host=host, port=port, mount_path=mount_path)
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self._running = False
            self.shutdown()

    def get_app(self) -> FastMCP:
        """
        获取 FastMCP 应用实例。

        Returns:
            FastMCP: MCP 应用实例
        """
        return self.app

    def shutdown(self) -> None:
        """关闭服务器并清理资源。"""
        self.logger.info("=" * 60)
        self.logger.info(f"Shutting down {self.server_name}")
        self.logger.info("=" * 60)

        try:
            # 关闭知识核心
            if hasattr(self, 'knowledge_core') and self.knowledge_core:
                self.knowledge_core.shutdown()

            self._initialized = False
            self._running = False

            self.logger.info("=" * 60)
            self.logger.info("Server shutdown complete")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Error during server shutdown: {e}")
            raise

    def is_running(self) -> bool:
        """检查服务器是否正在运行。"""
        return self._running

    def is_initialized(self) -> bool:
        """检查服务器是否已初始化。"""
        return self._initialized

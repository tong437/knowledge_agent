"""
MCPClient 类封装（使用 OpenAI API 替换 Claude）
- 负责连接 MCP Server
- 使用 OpenAI API 进行初始 LLM 响应
- 支持工具调用
"""

from contextlib import AsyncExitStack
from typing import Any, Dict, List

from mcp import ClientSession
from modules.YA_Common.mcp.base_connector import BaseConnector
from modules.YA_Common.types.mcp import MCPServerMetadata
from modules.YA_Common.utils.logger import get_logger
from mcp.client.sse import sse_client

logger = get_logger("mcp_client")


class MCPClient:
    """基于 OpenAI 通用格式的 MCP Client"""

    def __init__(self, servers: List[MCPServerMetadata]):
        self.servers = servers

        self.connectors: Dict[str, BaseConnector] = {}
        self.exit_stack = AsyncExitStack()

    def get_connector(self, name: str) -> BaseConnector:
        """根据名称获取对应的连接器"""
        connector = self.connectors.get(name)
        if not connector:
            raise ValueError(f"No connector found for server '{name}'")
        return connector

    def get_connectors(self) -> List[BaseConnector]:
        """获取所有连接器列表"""
        return self.connectors.values()

    async def connect(self):
        """连接所有服务器"""
        for server in self.servers:
            await self.connect_sse(server.name, server.url)

    async def connect_sse(self, name, url):
        """
        通过 SSE transport 连接服务器

        Args:
            name: 服务器名称
            url: 服务器地址
        """
        try:
            streams = await self.exit_stack.enter_async_context(sse_client(url=url))

            session: ClientSession = await self.exit_stack.enter_async_context(
                ClientSession(*streams)
            )
            connector = BaseConnector(session)
            await connector.initialize()
            logger.info(f"Connected to MCP server '{name}' at {url} via SSE.")
            self.connectors[name] = connector
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}' at {url}: {e}")

    async def list_servers_capabilities(self) -> Dict[str, Any]:
        """
        列出所有服务器的可用工具、资源、资源模板、Prompts
        """
        if not self.connectors:
            logger.warning(
                "No active connectors found, attempting to connect servers..."
            )
            await self.connect()

        capabilities_map: Dict[str, Any] = {}

        for name, connector in self.connectors.items():
            try:
                tools, resources, resource_templates, prompts = (
                    await connector.list_capabilities()
                )

                capabilities_map[name] = {
                    "tools": [tool.model_dump() for tool in tools],
                    "resources": [res.model_dump() for res in resources],
                    "resource_templates": [
                        tpl.model_dump() for tpl in resource_templates
                    ],
                    "prompts": [prompt.model_dump() for prompt in prompts],
                }
                logger.info(f"Fetched capabilities of server '{name}'.")
            except Exception as e:
                logger.error(f"Error fetching capabilities of '{name}': {e}")
                capabilities_map[name] = {"error": str(e)}

        return capabilities_map

    async def close(self):
        """清理资源"""
        await self.exit_stack.aclose()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

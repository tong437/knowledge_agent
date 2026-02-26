import json
from typing import Any, Dict, List
from mcp import ClientSession
from mcp.types import (
    Tool,
    Resource,
    ResourceTemplate,
    Prompt,
)

from modules.YA_Common.utils.logger import get_logger

logger = get_logger("base_connector")


class BaseConnector:
    """Base class for MCP connectors."""

    def __init__(self, session: ClientSession):
        self.session = session

    async def initialize(self):
        await self.session.initialize()
        self.tools = await self.list_tools()
        self.prompts = await self.list_prompts()
        self.resources = await self.list_resources()

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        result = await self.session.call_tool(name, args)
        content = result.content[0]
        if result.structuredContent:
            return result.structuredContent
        else:
            if content.type == "text":
                try:
                    contentJson = json.loads(content.text)
                    return contentJson
                except Exception as e:
                    logger.warning(f"Failed to parse content: {e}")
            return content.model_dump()

    async def get_prompt(self, name: str, args: Dict[str, Any]) -> Any:
        result = await self.session.get_prompt(name, args)
        return result.description

    async def read_resource(self, uri: str) -> Any:
        result = await self.session.read_resource(uri)
        return result.contents

    async def list_tools(self) -> List[Tool]:
        response = await self.session.list_tools()
        return response.tools

    async def list_resources(self) -> List[Resource]:
        response = await self.session.list_resources()
        return response.resources

    async def list_resource_templates(self) -> List[ResourceTemplate]:
        response = await self.session.list_resource_templates()
        return response.resourceTemplates

    async def list_prompts(self) -> List[Prompt]:
        response = await self.session.list_prompts()
        return response.prompts

    async def close(self):
        await self.session.close()

    async def list_capabilities(self) -> tuple[
        list[Tool],
        list[Resource],
        list[ResourceTemplate],
        list[Prompt],
    ]:
        """列出某个server的可用工具/资源/Prompts，直接返回列表"""
        list_tools_response = await self.session.list_tools()
        list_resources_response = await self.session.list_resources()
        list_resource_templates_response = await self.session.list_resource_templates()
        list_prompts_response = await self.session.list_prompts()

        return (
            list_tools_response.tools,
            list_resources_response.resources,
            list_resource_templates_response.resourceTemplates,
            list_prompts_response.prompts,
        )

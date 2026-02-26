"""
自动注册 tools 下的所有工具
"""

from typing import Callable, List, Optional, Any
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations, Icon
import pkgutil, importlib
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("YA_MCPServer_Tools")

_TOOL_REGISTRY: List[tuple[Callable, dict]] = []


def YA_MCPServer_Tool(
    name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    annotations: Optional[ToolAnnotations] = None,
    icons: Optional[list[Icon]] = None,
    structured_output: Optional[bool] = None,
    enable: Optional[bool] = True,
):
    """
    工具函数装饰器，用于延迟注册到 MCP。

    用法：
        @YA_MCPServer_Tool(name="echo", title="Echo", description="Echo text")
        def echo(text: str) -> str:
            return text
    """

    def decorator(func: Callable):
        if not enable:
            return func
        _TOOL_REGISTRY.append(
            (
                func,
                {
                    "name": name,
                    "title": title,
                    "description": description,
                    "annotations": annotations,
                    "icons": icons,
                    "structured_output": structured_output,
                },
            )
        )
        return func

    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator


def register_tools(app: FastMCP):
    """
    将所有已注册的工具函数挂载到 MCP。

    会自动导入 tools 目录下所有模块，并将标记的函数注册到 app.tool。
    """
    package = __name__

    for _, module_name, is_pkg in pkgutil.walk_packages(__path__, f"{package}."):
        if not is_pkg:
            importlib.import_module(module_name)

    for func, kwargs in _TOOL_REGISTRY:
        app.tool(
            name=kwargs.get("name"),
            title=kwargs.get("title"),
            description=kwargs.get("description"),
            annotations=kwargs.get("annotations"),
            icons=kwargs.get("icons"),
            structured_output=kwargs.get("structured_output"),
        )(func)

    logger.info(f"Registered {len(_TOOL_REGISTRY)} tools to MCP")

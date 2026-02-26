"""
自动注册 resources 下的所有资源定义
"""

from typing import Callable, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Icon, Annotations
import pkgutil, importlib
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("YA_MCPServer_Resources")

# 存储 (func, kwargs) 元组
_RESOURCE_REGISTRY: List[tuple[Callable, dict]] = []


def YA_MCPServer_Resource(
    uri: Optional[str] = None,
    *,
    name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    mime_type: Optional[str] = None,
    icons: Optional[list[Icon]] = None,
    annotations: Optional[Annotations] = None,
    enable: Optional[bool] = True,
):
    """
    资源装饰器，用于延迟注册到 MCP。

    用法：
        @YA_MCPServer_Resource("data://my/resource", title="My Resource")
        def get_my_resource() -> str:
            return "some content"
    """

    def decorator(func: Callable):
        if uri is None:
            raise ValueError("YA_MCPServer_Resource 需要指定 uri 参数。")
        if not enable:
            return func
        _RESOURCE_REGISTRY.append(
            (
                func,
                {
                    "uri": uri,
                    "name": name,
                    "title": title,
                    "description": description,
                    "mime_type": mime_type,
                    "icons": icons,
                    "annotations": annotations,
                },
            )
        )
        return func

    if callable(uri):
        func = uri
        raise TypeError(
            "YA_MCPServer_Resource 必须指定 uri，例如：@YA_MCPServer_Resource('data://example')"
        )

    return decorator


def register_resources(app: FastMCP):
    """
    自动导入并注册所有标记的 Resource。
    """
    package = __name__

    for _, module_name, is_pkg in pkgutil.walk_packages(__path__, f"{package}."):
        if not is_pkg:
            importlib.import_module(module_name)

    for func, kwargs in _RESOURCE_REGISTRY:
        app.resource(
            kwargs["uri"],
            name=kwargs.get("name"),
            title=kwargs.get("title"),
            description=kwargs.get("description"),
            mime_type=kwargs.get("mime_type"),
            icons=kwargs.get("icons"),
            annotations=kwargs.get("annotations"),
        )(func)

    logger.info(f"Registered {len(_RESOURCE_REGISTRY)} resources to MCP")

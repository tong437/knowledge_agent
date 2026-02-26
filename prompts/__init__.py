"""
自动注册 prompts 下的所有 Prompt 定义
"""

from typing import Callable, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Icon
import pkgutil, importlib
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("YA_MCPServer_Prompts")

_PROMPT_REGISTRY: List[tuple[Callable, dict]] = []


def YA_MCPServer_Prompt(
    name: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    icons: Optional[list[Icon]] = None,
    enable: Optional[bool] = True,
):
    """
    Prompt 装饰器，用于延迟注册到 MCP。

    用法：
        @YA_MCPServer_Prompt(name="greet", title="Greeting", description="问候语生成")
        def greet_prompt(name: str):
            return f"你好，{name}！"
    """

    def decorator(func: Callable):
        if not enable:
            return func
        _PROMPT_REGISTRY.append(
            (
                func,
                {
                    "name": name,
                    "title": title,
                    "description": description,
                    "icons": icons,
                },
            )
        )
        return func

    if callable(name):
        func = name
        name = None
        return decorator(func)

    return decorator


def register_prompts(app: FastMCP):
    """
    自动导入并注册所有标记的 Prompt。
    """
    package = __name__

    for _, module_name, is_pkg in pkgutil.walk_packages(__path__, f"{package}."):
        if not is_pkg:
            importlib.import_module(module_name)

    for func, kwargs in _PROMPT_REGISTRY:
        app.prompt(
            name=kwargs.get("name"),
            title=kwargs.get("title"),
            description=kwargs.get("description"),
            icons=kwargs.get("icons"),
        )(func)

    logger.info(f"Registered {len(_PROMPT_REGISTRY)} prompts to MCP")

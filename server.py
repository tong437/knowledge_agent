import logging
import os
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server import Server

from modules.YA_Common.utils.config import (
    get_server_name,
    is_default_server_name,
    get_transport_type,
    get_config,
)
from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.middleware import exception_handler
from modules.YA_Common.utils.helpers import print_server_banner
from setup import setup
import tools
import prompts
import resources
from starlette.middleware.cors import CORSMiddleware


class YA_MCPServer:
    """
    YA_MCPServer

    封装了 MCP 服务的启动逻辑，支持 stdio 与 SSE 两种传输方式。
    同时暴露 FastMCP 实例（app）供外部扩展。
    """

    def __init__(self):
        self.server_name = get_server_name()
        self.logger = get_logger(self.server_name)
        self.transport_type = get_transport_type()

        self.init_logger()

        self.app: FastMCP = FastMCP(self.server_name)

        tools.register_tools(self.app)
        prompts.register_prompts(self.app)
        resources.register_resources(self.app)

    def init_logger(self):
        noisy_loggers = [
            "mcp",
            "fastmcp",
            "mcp.server",
            "mcp.transport",
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
        ]
        for name in noisy_loggers:
            lib_logger = logging.getLogger(name)
            lib_logger.propagate = True
            lib_logger.handlers.clear()

    @exception_handler
    def run_stdio(self):
        """通过标准输入输出运行 MCP Server"""
        self.logger.info(f"Running MCP server via stdio: {self.server_name}")
        self.app.run(transport="stdio", mount_path="")

    @exception_handler
    def run_sse(self):
        """通过 SSE 运行 MCP Server"""
        env_host = os.getenv("HOST")
        env_port = os.getenv("PORT")
        host = env_host if env_host else get_config("transport.host", "0.0.0.0")
        port = int(env_port) if env_port else get_config("transport.port", 12345)

        self.logger.info(
            f"Running MCP server via SSE: {self.server_name} ({host}:{port})"
        )
        sse_app = self.create_starlette_app(self.app._mcp_server, debug=False)

        uvicorn.run(sse_app, host=host, port=port)

    def create_starlette_app(
        self, mcp_server: Server, *, debug: bool = False
    ) -> Starlette:
        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )

        app = Starlette(
            debug=debug,
            routes=[
                Route("/", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

        return app

    def start(self):
        """根据配置启动 MCP Server"""
        if is_default_server_name():
            self.logger.warning(
                "You are using the default server name. Please change it in config.yaml."
            )

        self.logger.info(f"Starting MCP server: {self.server_name}")
        print_server_banner()

        if self.transport_type == "stdio":
            self.run_stdio()
        elif self.transport_type == "sse":
            self.run_sse()
        else:
            raise ValueError(f"Unknown transport type: {self.transport_type}")


setup()
mcp_server = YA_MCPServer()
app = mcp_server.app

if __name__ == "__main__":
    mcp_server.start()

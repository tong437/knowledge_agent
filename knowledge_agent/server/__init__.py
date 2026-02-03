"""
MCP server implementation for the knowledge management agent.
"""

from .knowledge_mcp_server import KnowledgeMCPServer
from .mcp_tools import register_knowledge_tools
from .mcp_resources import register_knowledge_resources

__all__ = [
    "KnowledgeMCPServer",
    "register_knowledge_tools",
    "register_knowledge_resources",
]
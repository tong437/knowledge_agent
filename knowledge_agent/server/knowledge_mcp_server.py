"""
Main MCP server implementation for the knowledge management agent.
"""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from ..core import KnowledgeAgentCore
from .mcp_tools import register_knowledge_tools
from .mcp_resources import register_knowledge_resources


class KnowledgeMCPServer:
    """
    MCP server for the personal knowledge management agent.
    
    Provides MCP-compliant interface for knowledge collection,
    organization, and search functionality.
    """
    
    def __init__(self, server_name: str = "personal-knowledge-agent"):
        """
        Initialize the knowledge MCP server.
        
        Args:
            server_name: Name of the MCP server
        """
        self.server_name = server_name
        self.logger = logging.getLogger(f"knowledge_agent.{server_name}")
        
        # Initialize the FastMCP app
        self.app = FastMCP(server_name)
        
        # Initialize the knowledge agent core
        self.knowledge_core = KnowledgeAgentCore()
        
        # Register MCP tools and resources
        self._register_components()
        
        self.logger.info(f"Knowledge MCP server initialized: {server_name}")
    
    def _register_components(self) -> None:
        """Register MCP tools and resources with the server."""
        # Register knowledge management tools
        register_knowledge_tools(self.app, self.knowledge_core)
        
        # Register knowledge resources
        register_knowledge_resources(self.app, self.knowledge_core)
        
        self.logger.info("MCP components registered successfully")
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the server and its capabilities.
        
        Returns:
            Dict[str, Any]: Server information
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
        """Start the server using stdio transport."""
        self.logger.info(f"Starting {self.server_name} via stdio")
        self.app.run(transport="stdio")
    
    def start_sse(self, host: str = "localhost", port: int = 8000, mount_path: str = "/sse") -> None:
        """
        Start the server using SSE (Server-Sent Events) transport.
        
        SSE allows the server to push real-time updates to web clients.
        This is useful for web-based interfaces that need live updates.
        
        Note: FastMCP handles the host/port configuration internally.
        The server will start on the default host/port configured by FastMCP.
        
        Args:
            host: Host preference (informational only)
            port: Port preference (informational only) 
            mount_path: SSE endpoint path (default: /sse)
        """
        self.logger.info(f"Starting {self.server_name} via SSE")
        self.logger.info(f"SSE endpoint will be available at: {mount_path}")
        self.logger.info(f"Note: Host/port are managed by FastMCP internally")
        self.app.run(transport="sse", mount_path=mount_path)
    
    def get_app(self) -> FastMCP:
        """
        Get the FastMCP application instance.
        
        Returns:
            FastMCP: The MCP application
        """
        return self.app
    
    def shutdown(self) -> None:
        """Shutdown the server and cleanup resources."""
        self.logger.info(f"Shutting down {self.server_name}")
        if hasattr(self.knowledge_core, 'shutdown'):
            self.knowledge_core.shutdown()
        self.logger.info("Server shutdown complete")
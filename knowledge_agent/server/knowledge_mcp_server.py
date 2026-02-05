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
        
        # Server state
        self._initialized = False
        self._running = False
        
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"Initializing Knowledge MCP Server: {server_name}")
            self.logger.info("=" * 60)
            
            # Initialize the FastMCP app
            self.app = FastMCP(server_name)
            self.logger.info("✓ FastMCP application created")
            
            # Initialize the knowledge agent core
            self.knowledge_core = KnowledgeAgentCore()
            self.logger.info("✓ Knowledge agent core initialized")
            
            # Register MCP tools and resources
            self._register_components()
            
            self._initialized = True
            self.logger.info("=" * 60)
            self.logger.info(f"Knowledge MCP server initialized successfully")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP server: {e}")
            # Cleanup on initialization failure
            if hasattr(self, 'knowledge_core'):
                self.knowledge_core.shutdown()
            raise
    
    def _register_components(self) -> None:
        """Register MCP tools and resources with the server."""
        try:
            self.logger.info("Registering MCP components...")
            
            # Register knowledge management tools
            register_knowledge_tools(self.app, self.knowledge_core)
            self.logger.info("✓ Knowledge tools registered")
            
            # Register knowledge resources
            register_knowledge_resources(self.app, self.knowledge_core)
            self.logger.info("✓ Knowledge resources registered")
            
            self.logger.info("MCP components registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP components: {e}")
            raise
    
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
        if not self._initialized:
            raise RuntimeError("Server not initialized")
        
        self.logger.info("=" * 60)
        self.logger.info(f"Starting {self.server_name} via SSE transport")
        self.logger.info(f"SSE endpoint will be available at: {mount_path}")
        self.logger.info(f"Note: Host/port are managed by FastMCP internally")
        self.logger.info("=" * 60)
        
        self._running = True
        
        try:
            self.app.run(transport="sse", mount_path=mount_path)
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
        Get the FastMCP application instance.
        
        Returns:
            FastMCP: The MCP application
        """
        return self.app
    
    def shutdown(self) -> None:
        """Shutdown the server and cleanup resources."""
        self.logger.info("=" * 60)
        self.logger.info(f"Shutting down {self.server_name}")
        self.logger.info("=" * 60)
        
        try:
            # Shutdown knowledge core
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
        """Check if the server is currently running."""
        return self._running
    
    def is_initialized(self) -> bool:
        """Check if the server is initialized."""
        return self._initialized
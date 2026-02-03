#!/usr/bin/env python3
"""
Main entry point for the Personal Knowledge Management Agent MCP Server.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from knowledge_agent.server import KnowledgeMCPServer


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Personal Knowledge Management Agent MCP Server"
    )
    
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport method: stdio (default) or sse"
    )
    
    parser.add_argument(
        "--host",
        default="localhost", 
        help="Host to bind to for SSE transport (default: localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for SSE transport (default: 8000)"
    )
    
    parser.add_argument(
        "--name",
        default="personal-knowledge-agent",
        help="Server name (default: personal-knowledge-agent)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the knowledge agent server."""
    setup_logging()
    args = parse_arguments()
    
    logger = logging.getLogger("knowledge_agent.main")
    logger.info("Starting Personal Knowledge Management Agent MCP Server")
    
    try:
        # Create the MCP server
        server = KnowledgeMCPServer(args.name)
        
        # Print server information
        info = server.get_server_info()
        logger.info(f"Server: {info['name']} v{info['version']}")
        logger.info(f"Description: {info['description']}")
        logger.info(f"Capabilities: {list(info['capabilities'].keys())}")
        logger.info(f"Transport: {args.transport}")
        
        # Start the server with the specified transport
        if args.transport == "stdio":
            logger.info("Using stdio transport (for local MCP clients)")
            server.start_stdio()
        elif args.transport == "sse":
            logger.info(f"Using SSE transport (for web clients)")
            logger.info(f"Note: FastMCP will handle host/port configuration")
            server.start_sse(args.host, args.port)
        
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()
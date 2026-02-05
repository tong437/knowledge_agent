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
from knowledge_agent.core.logging_config import setup_logging, log_system_info


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
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (optional)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the knowledge agent server."""
    args = parse_arguments()
    
    # Setup logging with configured level
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file, structured=True)
    
    logger = logging.getLogger("knowledge_agent.main")
    logger.info("=" * 60)
    logger.info("Starting Personal Knowledge Management Agent MCP Server")
    logger.info("=" * 60)
    
    # Log system information
    log_system_info()
    
    server = None
    
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
        logger.info("\n" + "=" * 60)
        logger.info("Server interrupted by user (Ctrl+C)")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Server error: {e}", exc_info=True)
        logger.error("=" * 60)
        if server:
            server.shutdown()
        sys.exit(1)
    finally:
        # Ensure cleanup happens
        if server and server.is_running():
            logger.info("Performing final cleanup...")
            server.shutdown()
        
        # Log final monitoring report
        if server and hasattr(server, 'knowledge_core'):
            try:
                server.knowledge_core.log_monitoring_report()
            except Exception as e:
                logger.error(f"Failed to log monitoring report: {e}")
        
        logger.info("=" * 60)
        logger.info("Server shutdown complete - Goodbye!")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
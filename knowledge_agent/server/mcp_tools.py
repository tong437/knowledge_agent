"""
MCP tools registration for knowledge management functionality.
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent
from ..models import DataSource, SourceType
from ..core.exceptions import KnowledgeAgentError


def _validate_source_type(source_type: str) -> bool:
    """
    Validate that the source type is supported.
    
    Args:
        source_type: Source type string to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_types = ["auto", "document", "pdf", "web", "code", "image"]
    return source_type.lower() in valid_types


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a successful response with standard structure.
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success",
        "message": message,
        **data
    }


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format an error response with standard structure.
    
    Args:
        error: Exception that occurred
        context: Context information about the operation
        
    Returns:
        Formatted error response dictionary
    """
    return {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context
    }


def register_knowledge_tools(app: FastMCP, knowledge_core) -> None:
    """
    Register all knowledge management tools with the MCP server.
    
    Args:
        app: FastMCP application instance
        knowledge_core: Knowledge agent core instance
    """
    logger = logging.getLogger("knowledge_agent.mcp_tools")
    
    @app.tool()
    def collect_knowledge(source_path: str, source_type: str = "auto") -> Dict[str, Any]:
        """
        Collect knowledge from a data source.
        
        Processes various data sources (documents, PDFs, web pages, code files, images)
        and creates knowledge items in the knowledge base.
        
        Args:
            source_path: Path to the data source (file path or URL)
            source_type: Type of source - one of: auto, document, pdf, web, code, image
            
        Returns:
            Dictionary with status and created knowledge item information
        """
        try:
            # Validate parameters
            if not source_path or not source_path.strip():
                return _format_error_response(
                    ValueError("source_path cannot be empty"),
                    {"source_path": source_path}
                )
            
            if not _validate_source_type(source_type):
                return _format_error_response(
                    ValueError(f"Invalid source_type: {source_type}. Must be one of: auto, document, pdf, web, code, image"),
                    {"source_path": source_path, "source_type": source_type}
                )
            
            logger.info(f"Collecting knowledge from: {source_path} (type: {source_type})")
            
            # Create data source object
            # Map source_type string to SourceType enum
            type_mapping = {
                "auto": SourceType.DOCUMENT,  # Default to document for auto
                "document": SourceType.DOCUMENT,
                "pdf": SourceType.PDF,
                "web": SourceType.WEB_PAGE,
                "code": SourceType.CODE,
                "image": SourceType.IMAGE
            }
            
            source = DataSource(
                path=source_path.strip(),
                source_type=type_mapping.get(source_type.lower(), SourceType.DOCUMENT)
            )
            
            # Process the data source
            item = knowledge_core.collect_knowledge(source)
            
            return _format_success_response(
                f"Successfully collected knowledge from {source_path}",
                {
                    "item_id": item.id,
                    "title": item.title,
                    "source_path": item.source_path,
                    "source_type": item.source_type.value,
                    "created_at": item.created_at.isoformat()
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "source_path": source_path,
                "source_type": source_type
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"source_path": source_path, "source_type": source_type})
        except Exception as e:
            logger.error(f"Unexpected error collecting knowledge: {e}")
            return _format_error_response(e, {"source_path": source_path, "source_type": source_type})
    
    @app.tool()
    def search_knowledge(query: str, max_results: int = 10, 
                        min_relevance: float = 0.1) -> Dict[str, Any]:
        """
        Search for knowledge items using natural language or keywords.
        
        Performs semantic search across the knowledge base to find relevant items.
        Supports both keyword matching and semantic similarity search.
        
        Args:
            query: Search query string (natural language or keywords)
            max_results: Maximum number of results to return (1-100)
            min_relevance: Minimum relevance score threshold (0.0 to 1.0)
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Validate parameters
            if not query or not query.strip():
                return _format_error_response(
                    ValueError("query cannot be empty"),
                    {"query": query}
                )
            
            if max_results < 1 or max_results > 100:
                return _format_error_response(
                    ValueError("max_results must be between 1 and 100"),
                    {"query": query, "max_results": max_results}
                )
            
            if min_relevance < 0.0 or min_relevance > 1.0:
                return _format_error_response(
                    ValueError("min_relevance must be between 0.0 and 1.0"),
                    {"query": query, "min_relevance": min_relevance}
                )
            
            logger.info(f"Searching knowledge: {query}")
            
            # Perform search
            search_results = knowledge_core.search_knowledge(
                query.strip(),
                max_results=max_results,
                min_relevance=min_relevance
            )
            
            return _format_success_response(
                f"Found {len(search_results.get('results', []))} results for query: {query}",
                {
                    "query": query,
                    "results": search_results.get("results", []),
                    "total_found": search_results.get("total_found", 0),
                    "max_results": max_results,
                    "min_relevance": min_relevance
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "query": query,
                "results": [],
                "total_found": 0
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"query": query})
        except Exception as e:
            logger.error(f"Unexpected error searching knowledge: {e}")
            return _format_error_response(e, {"query": query})
    
    @app.tool()
    def organize_knowledge(item_id: str, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Organize a knowledge item by classifying, tagging, and finding relationships.
        
        Applies automatic classification, generates relevant tags, and identifies
        relationships with other knowledge items in the knowledge base.
        
        Args:
            item_id: ID of the knowledge item to organize
            force_reprocess: Whether to force reprocessing even if already organized
            
        Returns:
            Dictionary with organization results (categories, tags, relationships)
        """
        try:
            # Validate parameters
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )
            
            logger.info(f"Organizing knowledge item: {item_id}")
            
            # Get the knowledge item
            item = knowledge_core.get_knowledge_item(item_id.strip())
            
            if not item:
                return _format_error_response(
                    ValueError(f"Knowledge item not found: {item_id}"),
                    {"item_id": item_id}
                )
            
            # Check if already organized and force_reprocess is False
            if not force_reprocess and item.categories and item.tags:
                logger.info(f"Item {item_id} already organized, skipping")
                return _format_success_response(
                    f"Item {item_id} is already organized (use force_reprocess=true to reprocess)",
                    {
                        "item_id": item_id,
                        "categories": [{"id": c.id, "name": c.name, "confidence": c.confidence} for c in item.categories],
                        "tags": [{"id": t.id, "name": t.name} for t in item.tags],
                        "relationships": [],
                        "reprocessed": False
                    }
                )
            
            # Organize the item
            result = knowledge_core.organize_knowledge(item)
            
            return _format_success_response(
                f"Successfully organized knowledge item {item_id}",
                {
                    "item_id": result["item_id"],
                    "categories": result["categories"],
                    "tags": result["tags"],
                    "relationships": result["relationships"],
                    "reprocessed": force_reprocess
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "item_id": item_id,
                "categories": [],
                "tags": [],
                "relationships": []
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"item_id": item_id})
        except Exception as e:
            logger.error(f"Unexpected error organizing knowledge: {e}")
            return _format_error_response(e, {"item_id": item_id})
    
    @app.tool()
    def get_knowledge_item(item_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific knowledge item by ID.
        
        Returns complete information about a knowledge item including its content,
        categories, tags, and metadata.
        
        Args:
            item_id: ID of the knowledge item to retrieve
            
        Returns:
            Dictionary with knowledge item data or error
        """
        try:
            # Validate parameters
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )
            
            logger.info(f"Retrieving knowledge item: {item_id}")
            
            # Get the item
            item = knowledge_core.get_knowledge_item(item_id.strip())
            
            if not item:
                return _format_error_response(
                    ValueError(f"Knowledge item not found: {item_id}"),
                    {"item_id": item_id}
                )
            
            return _format_success_response(
                f"Successfully retrieved knowledge item {item_id}",
                {
                    "item": item.to_dict()
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "item_id": item_id,
                "item": None
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"item_id": item_id})
        except Exception as e:
            logger.error(f"Unexpected error retrieving knowledge item: {e}")
            return _format_error_response(e, {"item_id": item_id})
    
    @app.tool()
    def list_knowledge_items(category: str = "", tag: str = "", 
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List knowledge items with optional filtering.
        
        Returns a paginated list of knowledge items, optionally filtered by
        category or tag.
        
        Args:
            category: Filter by category name (optional, empty string for no filter)
            tag: Filter by tag name (optional, empty string for no filter)
            limit: Maximum number of items to return (1-100)
            offset: Number of items to skip for pagination
            
        Returns:
            Dictionary with list of knowledge items and metadata
        """
        try:
            # Validate parameters
            if limit < 1 or limit > 100:
                return _format_error_response(
                    ValueError("limit must be between 1 and 100"),
                    {"limit": limit}
                )
            
            if offset < 0:
                return _format_error_response(
                    ValueError("offset must be non-negative"),
                    {"offset": offset}
                )
            
            logger.info(f"Listing knowledge items (category: {category}, tag: {tag}, limit: {limit}, offset: {offset})")
            
            # Build filters
            filters = {}
            if category and category.strip():
                filters["category"] = category.strip()
            if tag and tag.strip():
                filters["tag"] = tag.strip()
            filters["limit"] = limit
            filters["offset"] = offset
            
            # Get items
            items = knowledge_core.list_knowledge_items(**filters)
            
            # Convert items to dictionaries
            items_data = [item.to_dict() for item in items]
            
            return _format_success_response(
                f"Retrieved {len(items_data)} knowledge items",
                {
                    "items": items_data,
                    "count": len(items_data),
                    "limit": limit,
                    "offset": offset,
                    "filters": {
                        "category": category if category else None,
                        "tag": tag if tag else None
                    }
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "items": [],
                "count": 0,
                "limit": limit,
                "offset": offset
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"category": category, "tag": tag})
        except Exception as e:
            logger.error(f"Unexpected error listing knowledge items: {e}")
            return _format_error_response(e, {"category": category, "tag": tag})
    
    @app.tool()
    def export_knowledge(format: str = "json", include_content: bool = True) -> Dict[str, Any]:
        """
        Export all knowledge data in the specified format.
        
        Exports the complete knowledge base including items, categories, tags,
        and relationships in a structured format.
        
        Args:
            format: Export format (currently only 'json' is supported)
            include_content: Whether to include full content or just metadata
            
        Returns:
            Dictionary with export results or download information
        """
        try:
            # Validate parameters
            if format.lower() not in ["json"]:
                return _format_error_response(
                    ValueError(f"Unsupported export format: {format}. Currently only 'json' is supported"),
                    {"format": format}
                )
            
            logger.info(f"Exporting knowledge data in {format} format")
            
            # Export data
            export_data = knowledge_core.export_data(format=format.lower())
            
            # Optionally filter out content
            if not include_content and "knowledge_items" in export_data:
                for item in export_data["knowledge_items"]:
                    if "content" in item:
                        item["content"] = "[Content excluded from export]"
            
            return _format_success_response(
                f"Successfully exported knowledge data in {format} format",
                {
                    "format": format,
                    "include_content": include_content,
                    "export_data": export_data,
                    "item_count": len(export_data.get("knowledge_items", [])),
                    "category_count": len(export_data.get("categories", [])),
                    "tag_count": len(export_data.get("tags", [])),
                    "relationship_count": len(export_data.get("relationships", []))
                }
            )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "format": format,
                "include_content": include_content
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"format": format})
        except Exception as e:
            logger.error(f"Unexpected error exporting knowledge: {e}")
            return _format_error_response(e, {"format": format})
    
    @app.tool()
    def import_knowledge(data_path: str, format: str = "json", 
                        merge_strategy: str = "skip_existing") -> Dict[str, Any]:
        """
        Import knowledge data from a file.
        
        Imports knowledge items, categories, tags, and relationships from an
        exported data file.
        
        Args:
            data_path: Path to the data file to import
            format: Format of the data file (currently only 'json' is supported)
            merge_strategy: How to handle existing items - one of: skip_existing, overwrite, merge
            
        Returns:
            Dictionary with import results
        """
        try:
            # Validate parameters
            if not data_path or not data_path.strip():
                return _format_error_response(
                    ValueError("data_path cannot be empty"),
                    {"data_path": data_path}
                )
            
            if format.lower() not in ["json"]:
                return _format_error_response(
                    ValueError(f"Unsupported import format: {format}. Currently only 'json' is supported"),
                    {"format": format, "data_path": data_path}
                )
            
            valid_strategies = ["skip_existing", "overwrite", "merge"]
            if merge_strategy.lower() not in valid_strategies:
                return _format_error_response(
                    ValueError(f"Invalid merge_strategy: {merge_strategy}. Must be one of: {', '.join(valid_strategies)}"),
                    {"merge_strategy": merge_strategy, "data_path": data_path}
                )
            
            logger.info(f"Importing knowledge data from {data_path}")
            
            # Read the data file
            import json
            from pathlib import Path
            
            file_path = Path(data_path.strip())
            if not file_path.exists():
                return _format_error_response(
                    FileNotFoundError(f"Data file not found: {data_path}"),
                    {"data_path": data_path}
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import the data
            success = knowledge_core.import_data(import_data)
            
            if success:
                return _format_success_response(
                    f"Successfully imported knowledge data from {data_path}",
                    {
                        "data_path": data_path,
                        "format": format,
                        "merge_strategy": merge_strategy,
                        "imported_items": len(import_data.get("knowledge_items", [])),
                        "imported_categories": len(import_data.get("categories", [])),
                        "imported_tags": len(import_data.get("tags", [])),
                        "imported_relationships": len(import_data.get("relationships", []))
                    }
                )
            else:
                return _format_error_response(
                    Exception("Import failed"),
                    {"data_path": data_path}
                )
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return {
                "status": "not_implemented",
                "message": str(e),
                "data_path": data_path,
                "format": format,
                "merge_strategy": merge_strategy
            }
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"data_path": data_path})
        except Exception as e:
            logger.error(f"Unexpected error importing knowledge: {e}")
            return _format_error_response(e, {"data_path": data_path})
    
    @app.tool()
    def get_statistics() -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns statistics about the knowledge base including counts of items,
        categories, tags, and relationships.
        
        Returns:
            Dictionary with knowledge base statistics
        """
        try:
            logger.info("Retrieving knowledge base statistics")
            
            stats = knowledge_core.get_statistics()
            
            return _format_success_response(
                "Successfully retrieved knowledge base statistics",
                {
                    "statistics": stats
                }
            )
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {})
        except Exception as e:
            logger.error(f"Unexpected error retrieving statistics: {e}")
            return _format_error_response(e, {})
    
    @app.tool()
    def get_performance_metrics() -> Dict[str, Any]:
        """
        Get performance metrics for all operations.
        
        Returns performance metrics including operation counts, durations,
        success rates, and error rates.
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            logger.info("Retrieving performance metrics")
            
            metrics = knowledge_core.get_performance_metrics()
            
            return _format_success_response(
                "Successfully retrieved performance metrics",
                {
                    "metrics": metrics
                }
            )
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {})
        except Exception as e:
            logger.error(f"Unexpected error retrieving performance metrics: {e}")
            return _format_error_response(e, {})
    
    @app.tool()
    def get_error_summary() -> Dict[str, Any]:
        """
        Get error summary and recent errors.
        
        Returns a summary of errors that have occurred in the system including
        error counts by type and recent error details.
        
        Returns:
            Dictionary with error summary
        """
        try:
            logger.info("Retrieving error summary")
            
            error_summary = knowledge_core.get_error_summary()
            
            return _format_success_response(
                "Successfully retrieved error summary",
                {
                    "error_summary": error_summary
                }
            )
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {})
        except Exception as e:
            logger.error(f"Unexpected error retrieving error summary: {e}")
            return _format_error_response(e, {})
    
    logger.info("Knowledge management tools registered successfully")
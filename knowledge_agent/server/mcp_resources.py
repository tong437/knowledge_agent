"""
MCP resources registration for knowledge management.
"""

import logging
import json
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextContent
from ..core.exceptions import KnowledgeAgentError


def _format_resource_response(data: Any) -> str:
    """
    Format resource data as JSON string.
    
    Args:
        data: Data to format
        
    Returns:
        JSON string representation
    """
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to format response: {str(e)}"})


def _format_error_resource(error: Exception) -> str:
    """
    Format an error as a JSON resource response.
    
    Args:
        error: Exception that occurred
        
    Returns:
        JSON string with error information
    """
    return json.dumps({
        "error": type(error).__name__,
        "message": str(error)
    })


def register_knowledge_resources(app: FastMCP, knowledge_core) -> None:
    """
    Register knowledge management resources with the MCP server.
    
    Resources provide read-only access to knowledge base data through
    URI-based endpoints.
    
    Args:
        app: FastMCP application instance
        knowledge_core: Knowledge agent core instance
    """
    logger = logging.getLogger("knowledge_agent.mcp_resources")
    
    @app.resource("knowledge://items")
    def get_knowledge_items() -> str:
        """
        Get a list of all knowledge items.
        
        Returns a JSON array of all knowledge items in the knowledge base,
        including their metadata, categories, and tags.
        
        Returns:
            JSON string containing all knowledge items
        """
        try:
            logger.info("Retrieving all knowledge items resource")
            
            # Get all items from storage
            items = knowledge_core.list_knowledge_items()
            
            # Convert to dictionaries
            items_data = [item.to_dict() for item in items]
            
            response = {
                "resource": "knowledge://items",
                "count": len(items_data),
                "items": items_data
            }
            
            return _format_resource_response(response)
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return _format_resource_response({
                "resource": "knowledge://items",
                "status": "not_implemented",
                "message": str(e),
                "items": []
            })
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving knowledge items resource: {e}")
            return _format_error_resource(e)
    
    @app.resource("knowledge://items/{item_id}")
    def get_knowledge_item_by_id(item_id: str) -> str:
        """
        Get a specific knowledge item by ID.
        
        Returns complete information about a single knowledge item including
        its content, categories, tags, and metadata.
        
        Args:
            item_id: ID of the knowledge item to retrieve
            
        Returns:
            JSON string containing the knowledge item
        """
        try:
            logger.info(f"Retrieving knowledge item resource: {item_id}")
            
            # Get the item
            item = knowledge_core.get_knowledge_item(item_id)
            
            if not item:
                return _format_resource_response({
                    "resource": f"knowledge://items/{item_id}",
                    "error": "NotFound",
                    "message": f"Knowledge item not found: {item_id}"
                })
            
            response = {
                "resource": f"knowledge://items/{item_id}",
                "item": item.to_dict()
            }
            
            return _format_resource_response(response)
            
        except NotImplementedError as e:
            logger.warning(f"Feature not yet implemented: {e}")
            return _format_resource_response({
                "resource": f"knowledge://items/{item_id}",
                "status": "not_implemented",
                "message": str(e)
            })
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving knowledge item resource: {e}")
            return _format_error_resource(e)
    
    @app.resource("knowledge://categories")
    def get_categories() -> str:
        """
        Get a list of all categories.
        
        Returns all categories in the knowledge base with their hierarchical
        structure and usage statistics.
        
        Returns:
            JSON string containing all categories
        """
        try:
            logger.info("Retrieving categories resource")
            
            # Get categories from storage
            if not knowledge_core._storage_manager:
                return _format_resource_response({
                    "resource": "knowledge://categories",
                    "message": "Storage manager not initialized",
                    "categories": []
                })
            
            categories = knowledge_core._storage_manager.get_all_categories()
            
            # Convert to dictionaries
            categories_data = [cat.to_dict() for cat in categories]
            
            response = {
                "resource": "knowledge://categories",
                "count": len(categories_data),
                "categories": categories_data
            }
            
            return _format_resource_response(response)
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving categories resource: {e}")
            return _format_error_resource(e)
    
    @app.resource("knowledge://tags")
    def get_tags() -> str:
        """
        Get a list of all tags.
        
        Returns all tags in the knowledge base with their usage counts
        and color coding.
        
        Returns:
            JSON string containing all tags
        """
        try:
            logger.info("Retrieving tags resource")
            
            # Get tags from storage
            if not knowledge_core._storage_manager:
                return _format_resource_response({
                    "resource": "knowledge://tags",
                    "message": "Storage manager not initialized",
                    "tags": []
                })
            
            tags = knowledge_core._storage_manager.get_all_tags()
            
            # Convert to dictionaries
            tags_data = [tag.to_dict() for tag in tags]
            
            response = {
                "resource": "knowledge://tags",
                "count": len(tags_data),
                "tags": tags_data
            }
            
            return _format_resource_response(response)
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving tags resource: {e}")
            return _format_error_resource(e)
    
    @app.resource("knowledge://graph")
    def get_knowledge_graph() -> str:
        """
        Get the knowledge graph structure.
        
        Returns the complete knowledge graph showing relationships between
        knowledge items as nodes and edges.
        
        Returns:
            JSON string containing the knowledge graph
        """
        try:
            logger.info("Retrieving knowledge graph resource")
            
            # Get all items and relationships
            if not knowledge_core._storage_manager:
                return _format_resource_response({
                    "resource": "knowledge://graph",
                    "message": "Storage manager not initialized",
                    "nodes": [],
                    "edges": []
                })
            
            items = knowledge_core._storage_manager.get_all_knowledge_items()
            
            # Build nodes
            nodes = []
            for item in items:
                nodes.append({
                    "id": item.id,
                    "title": item.title,
                    "source_type": item.source_type.value,
                    "categories": [cat.name for cat in item.categories],
                    "tags": [tag.name for tag in item.tags]
                })
            
            # Build edges from relationships
            edges = []
            for item in items:
                relationships = knowledge_core._storage_manager.get_relationships_for_item(item.id)
                for rel in relationships:
                    # Only add edge if this item is the source (to avoid duplicates)
                    if rel.source_id == item.id:
                        edges.append({
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "type": rel.relationship_type.value,
                            "strength": rel.strength,
                            "description": rel.description
                        })
            
            response = {
                "resource": "knowledge://graph",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "nodes": nodes,
                "edges": edges
            }
            
            return _format_resource_response(response)
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving knowledge graph resource: {e}")
            return _format_error_resource(e)
    
    @app.resource("knowledge://stats")
    def get_knowledge_stats() -> str:
        """
        Get statistics about the knowledge base.
        
        Returns comprehensive statistics including counts of items, categories,
        tags, relationships, and source type distribution.
        
        Returns:
            JSON string containing knowledge base statistics
        """
        try:
            logger.info("Retrieving knowledge statistics resource")
            
            # Get statistics from core
            stats = knowledge_core.get_statistics()
            
            # Add source type distribution if storage is available
            if knowledge_core._storage_manager:
                items = knowledge_core._storage_manager.get_all_knowledge_items()
                source_distribution = {}
                for item in items:
                    source_type = item.source_type.value
                    source_distribution[source_type] = source_distribution.get(source_type, 0) + 1
                stats["source_type_distribution"] = source_distribution
            
            # Add timestamp
            from datetime import datetime
            stats["last_updated"] = datetime.now().isoformat()
            stats["resource"] = "knowledge://stats"
            
            return _format_resource_response(stats)
            
        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_resource(e)
        except Exception as e:
            logger.error(f"Error retrieving knowledge statistics: {e}")
            return _format_error_resource(e)
    
    logger.info("Knowledge management resources registered successfully")
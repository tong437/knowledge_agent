"""
Core knowledge agent implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from ..models import KnowledgeItem, DataSource, Category, Tag, Relationship
from ..interfaces import DataSourceProcessor, KnowledgeOrganizer, SearchEngine, StorageManager
from ..storage import SQLiteStorageManager
from ..organizers import KnowledgeOrganizerImpl
from .exceptions import KnowledgeAgentError, ConfigurationError


class KnowledgeAgentCore:
    """
    Core implementation of the personal knowledge management agent.
    
    Coordinates between different components to provide unified
    knowledge management functionality.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the knowledge agent core.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.logger = logging.getLogger("knowledge_agent.core")
        self.config = config or {}
        
        # Component instances (will be initialized in later tasks)
        self._storage_manager: Optional[StorageManager] = None
        self._data_processors: Dict[str, DataSourceProcessor] = {}
        self._knowledge_organizer: Optional[KnowledgeOrganizer] = None
        self._search_engine: Optional[SearchEngine] = None
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("Knowledge agent core initialized")
    
    def _initialize_components(self) -> None:
        """Initialize core components based on configuration."""
        # Initialize storage manager
        storage_config = self.config.get("storage", {})
        storage_type = storage_config.get("type", "sqlite")
        
        if storage_type == "sqlite":
            db_path = storage_config.get("path", "knowledge_agent.db")
            self._storage_manager = SQLiteStorageManager(db_path)
            self.logger.info(f"Initialized SQLite storage at {db_path}")
        
        # Initialize knowledge organizer
        if self._storage_manager:
            self._knowledge_organizer = KnowledgeOrganizerImpl(self._storage_manager)
            self.logger.info("Initialized knowledge organizer")
        
        self.logger.info("Component initialization completed")
    
    def collect_knowledge(self, source: DataSource) -> KnowledgeItem:
        """
        Collect knowledge from a data source.
        
        Args:
            source: The data source to process
            
        Returns:
            KnowledgeItem: The created knowledge item
            
        Raises:
            KnowledgeAgentError: If collection fails
        """
        try:
            self.logger.info(f"Collecting knowledge from: {source.path}")
            
            # This will be implemented in task 3
            raise NotImplementedError("Knowledge collection will be implemented in task 3")
            
        except Exception as e:
            self.logger.error(f"Error collecting knowledge: {e}")
            raise KnowledgeAgentError(f"Failed to collect knowledge: {e}")
    
    def organize_knowledge(self, item: KnowledgeItem) -> Dict[str, Any]:
        """
        Organize a knowledge item (classify, tag, find relationships).
        
        Args:
            item: The knowledge item to organize
            
        Returns:
            Dict containing organization results
            
        Raises:
            KnowledgeAgentError: If organization fails
        """
        try:
            self.logger.info(f"Organizing knowledge item: {item.id}")
            
            if not self._knowledge_organizer:
                raise KnowledgeAgentError("Knowledge organizer not initialized")
            
            # Classify the item
            categories = self._knowledge_organizer.classify(item)
            self.logger.info(f"Classified into {len(categories)} categories")
            
            # Generate tags
            tags = self._knowledge_organizer.generate_tags(item)
            self.logger.info(f"Generated {len(tags)} tags")
            
            # Find relationships
            relationships = self._knowledge_organizer.find_relationships(item)
            self.logger.info(f"Found {len(relationships)} relationships")
            
            # Update the item with categories and tags
            for category in categories:
                item.add_category(category)
            for tag in tags:
                item.add_tag(tag)
            
            # Save the organized item
            if self._storage_manager:
                self._storage_manager.save_knowledge_item(item)
            
            # Update knowledge graph with relationships
            if relationships:
                self._knowledge_organizer.update_knowledge_graph(relationships)
            
            return {
                "item_id": item.id,
                "categories": [{"id": c.id, "name": c.name, "confidence": c.confidence} for c in categories],
                "tags": [{"id": t.id, "name": t.name} for t in tags],
                "relationships": [
                    {
                        "target_id": r.target_id,
                        "type": r.relationship_type.value,
                        "strength": r.strength,
                        "description": r.description
                    }
                    for r in relationships
                ],
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error organizing knowledge: {e}")
            raise KnowledgeAgentError(f"Failed to organize knowledge: {e}")
    
    def search_knowledge(self, query: str, **options) -> Dict[str, Any]:
        """
        Search for knowledge items.
        
        Args:
            query: Search query string
            **options: Search options
            
        Returns:
            Dict containing search results
            
        Raises:
            KnowledgeAgentError: If search fails
        """
        try:
            self.logger.info(f"Searching knowledge: {query}")
            
            # This will be implemented in task 6
            raise NotImplementedError("Knowledge search will be implemented in task 6")
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {e}")
            raise KnowledgeAgentError(f"Failed to search knowledge: {e}")
    
    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """
        Retrieve a knowledge item by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            KnowledgeItem if found, None otherwise
            
        Raises:
            KnowledgeAgentError: If retrieval fails
        """
        try:
            self.logger.info(f"Retrieving knowledge item: {item_id}")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            item = self._storage_manager.get_knowledge_item(item_id)
            
            if item:
                self.logger.info(f"Successfully retrieved knowledge item: {item_id}")
            else:
                self.logger.info(f"Knowledge item not found: {item_id}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge item: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve knowledge item: {e}")
    
    def list_knowledge_items(self, **filters) -> List[KnowledgeItem]:
        """
        List knowledge items with optional filtering.
        
        Args:
            **filters: Filter criteria (category, tag, limit, offset)
            
        Returns:
            List of knowledge items
            
        Raises:
            KnowledgeAgentError: If listing fails
        """
        try:
            self.logger.info("Listing knowledge items")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # Get all items
            all_items = self._storage_manager.get_all_knowledge_items()
            
            # Apply filters
            filtered_items = all_items
            
            # Filter by category
            if "category" in filters and filters["category"]:
                category_name = filters["category"]
                filtered_items = [
                    item for item in filtered_items
                    if any(cat.name == category_name for cat in item.categories)
                ]
            
            # Filter by tag
            if "tag" in filters and filters["tag"]:
                tag_name = filters["tag"]
                filtered_items = [
                    item for item in filtered_items
                    if any(tag.name == tag_name for tag in item.tags)
                ]
            
            # Apply pagination
            offset = filters.get("offset", 0)
            limit = filters.get("limit", 50)
            
            paginated_items = filtered_items[offset:offset + limit]
            
            self.logger.info(f"Retrieved {len(paginated_items)} knowledge items (total: {len(filtered_items)})")
            
            return paginated_items
            
        except Exception as e:
            self.logger.error(f"Error listing knowledge items: {e}")
            raise KnowledgeAgentError(f"Failed to list knowledge items: {e}")
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export all knowledge data.
        
        Args:
            format: Export format (currently only 'json' is supported)
            
        Returns:
            Exported data dictionary
            
        Raises:
            KnowledgeAgentError: If export fails
        """
        try:
            self.logger.info(f"Exporting data in {format} format")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            if format.lower() != "json":
                raise KnowledgeAgentError(f"Unsupported export format: {format}")
            
            # Export data from storage
            export_data = self._storage_manager.export_data(format=format)
            
            self.logger.info(f"Successfully exported {len(export_data.get('knowledge_items', []))} items")
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise KnowledgeAgentError(f"Failed to export data: {e}")
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        Import knowledge data.
        
        Args:
            data: Data dictionary to import (must contain knowledge_items, categories, tags, relationships)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            KnowledgeAgentError: If import fails
        """
        try:
            self.logger.info("Importing knowledge data")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # Validate data structure
            if not isinstance(data, dict):
                raise KnowledgeAgentError("Import data must be a dictionary")
            
            # Import data to storage
            success = self._storage_manager.import_data(data)
            
            if success:
                item_count = len(data.get("knowledge_items", []))
                self.logger.info(f"Successfully imported {item_count} items")
            else:
                self.logger.warning("Import completed with warnings or partial success")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            raise KnowledgeAgentError(f"Failed to import data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            self.logger.info("Retrieving knowledge base statistics")
            
            if not self._storage_manager:
                return {
                    "total_items": 0,
                    "total_categories": 0,
                    "total_tags": 0,
                    "total_relationships": 0,
                    "message": "Storage manager not initialized",
                }
            
            # Get actual statistics from storage
            items = self._storage_manager.get_all_knowledge_items()
            categories = self._storage_manager.get_all_categories()
            tags = self._storage_manager.get_all_tags()
            
            # Count relationships
            total_relationships = 0
            for item in items:
                relationships = self._storage_manager.get_relationships_for_item(item.id)
                total_relationships += len(relationships)
            
            return {
                "total_items": len(items),
                "total_categories": len(categories),
                "total_tags": len(tags),
                "total_relationships": total_relationships,
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving statistics: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve statistics: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the knowledge agent and cleanup resources."""
        try:
            self.logger.info("Shutting down knowledge agent core")
            
            # Cleanup will be implemented as components are added
            if self._storage_manager and hasattr(self._storage_manager, 'close'):
                self._storage_manager.close()
            
            self.logger.info("Knowledge agent core shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise KnowledgeAgentError(f"Failed to shutdown cleanly: {e}")
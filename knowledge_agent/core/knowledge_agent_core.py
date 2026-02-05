"""
Core knowledge agent implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from ..models import KnowledgeItem, DataSource, Category, Tag, Relationship
from ..interfaces import DataSourceProcessor, KnowledgeOrganizer, SearchEngine, StorageManager
from ..storage import SQLiteStorageManager
from ..organizers import KnowledgeOrganizerImpl
from ..search import SearchEngineImpl
from ..processors import DocumentProcessor, PDFProcessor, CodeProcessor
from .exceptions import KnowledgeAgentError, ConfigurationError
from .logging_config import (
    monitor_performance,
    track_errors,
    performance_context,
    get_performance_monitor,
    get_error_tracker
)
from .component_registry import get_component_registry, ComponentRegistry
from .config_manager import get_config_manager, ConfigManager
from .data_import_export import DataImportExport


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
        self._data_import_export: Optional[DataImportExport] = None
        
        # Component registry for dependency injection
        self._registry: ComponentRegistry = get_component_registry()
        
        # Configuration manager
        self._config_manager: Optional[ConfigManager] = None
        
        # Initialization state
        self._initialized = False
        self._shutdown_requested = False
        
        # Initialize components
        self._initialize_components()
        
        self._initialized = True
        self.logger.info("Knowledge agent core initialized successfully")
    
    def _initialize_components(self) -> None:
        """Initialize core components based on configuration."""
        try:
            self.logger.info("Starting component initialization...")
            
            # Initialize configuration manager if config path is provided
            config_path = self.config.get("config_path")
            if config_path:
                self._config_manager = get_config_manager(config_path)
                self.logger.info(f"✓ Loaded configuration from {config_path}")
                # Merge loaded config with provided config
                loaded_config = self._config_manager.get_config()
                # Update self.config with loaded values
                if not self.config.get("storage"):
                    self.config["storage"] = {
                        "type": loaded_config.storage.type,
                        "path": loaded_config.storage.path
                    }
            
            # Register components with the registry
            self._register_components()
            
            # Initialize storage manager
            storage_config = self.config.get("storage", {})
            storage_type = storage_config.get("type", "sqlite")
            
            if storage_type == "sqlite":
                db_path = storage_config.get("path", "knowledge_agent.db")
                self._storage_manager = SQLiteStorageManager(db_path)
                self._registry.set_instance("storage_manager", self._storage_manager)
                self.logger.info(f"✓ Initialized SQLite storage at {db_path}")
            else:
                self.logger.warning(f"Unknown storage type: {storage_type}, using default SQLite")
                self._storage_manager = SQLiteStorageManager("knowledge_agent.db")
                self._registry.set_instance("storage_manager", self._storage_manager)
            
            # Initialize knowledge organizer
            if self._storage_manager:
                self._knowledge_organizer = KnowledgeOrganizerImpl(self._storage_manager)
                self._registry.set_instance("knowledge_organizer", self._knowledge_organizer)
                self.logger.info("✓ Initialized knowledge organizer")
            else:
                self.logger.warning("Storage manager not available, knowledge organizer not initialized")
            
            # Initialize search engine
            search_config = self.config.get("search", {})
            index_dir = search_config.get("index_dir", "search_index")
            self._search_engine = SearchEngineImpl(index_dir)
            self._registry.set_instance("search_engine", self._search_engine)
            self.logger.info(f"✓ Initialized search engine with index at {index_dir}")
            
            # Initialize data processors
            self._initialize_data_processors()
            
            # Initialize data import/export
            self._data_import_export = DataImportExport(self._storage_manager)
            self.logger.info("✓ Initialized data import/export")
            
            # Log component registry status
            self._registry.log_status()
            
            self.logger.info("Component initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            # Cleanup any partially initialized components
            self._cleanup_components()
            raise KnowledgeAgentError(f"Component initialization failed: {e}")
    
    def _register_components(self) -> None:
        """Register all components with the component registry."""
        self.logger.info("Registering components with registry...")
        
        # Register storage manager
        self._registry.register(
            name="storage_manager",
            component_type=SQLiteStorageManager,
            dependencies=[]
        )
        
        # Register knowledge organizer
        self._registry.register(
            name="knowledge_organizer",
            component_type=KnowledgeOrganizerImpl,
            dependencies=["storage_manager"]
        )
        
        # Register search engine
        self._registry.register(
            name="search_engine",
            component_type=SearchEngineImpl,
            dependencies=[]
        )
        
        # Register data processors
        self._registry.register(
            name="document_processor",
            component_type=DocumentProcessor,
            dependencies=[]
        )
        
        self._registry.register(
            name="pdf_processor",
            component_type=PDFProcessor,
            dependencies=[]
        )
        
        self._registry.register(
            name="code_processor",
            component_type=CodeProcessor,
            dependencies=[]
        )
        
        self.logger.info("Components registered with registry")
    
    def _initialize_data_processors(self) -> None:
        """Initialize all data source processors."""
        self.logger.info("Initializing data processors...")
        
        # Initialize document processor
        doc_processor = DocumentProcessor()
        self._data_processors["document"] = doc_processor
        self._data_processors["txt"] = doc_processor
        self._data_processors["markdown"] = doc_processor
        self._registry.set_instance("document_processor", doc_processor)
        
        # Initialize PDF processor
        pdf_processor = PDFProcessor()
        self._data_processors["pdf"] = pdf_processor
        self._registry.set_instance("pdf_processor", pdf_processor)
        
        # Initialize code processor
        code_processor = CodeProcessor()
        self._data_processors["code"] = code_processor
        self._data_processors["python"] = code_processor
        self._data_processors["javascript"] = code_processor
        self._data_processors["java"] = code_processor
        self._registry.set_instance("code_processor", code_processor)
        
        self.logger.info(f"✓ Initialized {len(self._data_processors)} data processors")
    
    @monitor_performance("collect_knowledge")
    @track_errors({"component": "knowledge_collection"})
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
            
            # Determine the appropriate processor based on source type
            processor = self._get_processor_for_source(source)
            
            if not processor:
                raise KnowledgeAgentError(
                    f"No processor available for source type: {source.source_type.value}"
                )
            
            # Validate the source
            if not processor.validate(source):
                raise KnowledgeAgentError(f"Invalid data source: {source.path}")
            
            # Process the source to create a knowledge item
            item = processor.process(source)
            
            # Save the item to storage
            if self._storage_manager:
                self._storage_manager.save_knowledge_item(item)
                self.logger.info(f"✓ Saved knowledge item: {item.id}")
            
            # Update search index
            if self._search_engine:
                self._search_engine.update_index(item)
                self.logger.info(f"✓ Updated search index for item: {item.id}")
            
            self.logger.info(f"Successfully collected knowledge from: {source.path}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error collecting knowledge: {e}")
            raise KnowledgeAgentError(f"Failed to collect knowledge: {e}")
    
    def _get_processor_for_source(self, source: DataSource) -> Optional[DataSourceProcessor]:
        """
        Get the appropriate processor for a data source.
        
        Args:
            source: The data source
            
        Returns:
            DataSourceProcessor or None if no processor is available
        """
        source_type = source.source_type.value.lower()
        
        # Check if we have a direct match
        if source_type in self._data_processors:
            return self._data_processors[source_type]
        
        # Check file extension for more specific matching
        if source.path:
            ext = source.path.split('.')[-1].lower()
            if ext in self._data_processors:
                return self._data_processors[ext]
            
            # Map common extensions to processors
            if ext in ['txt', 'md', 'doc', 'docx']:
                return self._data_processors.get('document')
            elif ext in ['py', 'js', 'java', 'cpp', 'c', 'ts']:
                return self._data_processors.get('code')
            elif ext == 'pdf':
                return self._data_processors.get('pdf')
        
        return None
    
    @monitor_performance("organize_knowledge")
    @track_errors({"component": "knowledge_organization"})
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
    
    @monitor_performance("search_knowledge")
    @track_errors({"component": "knowledge_search"})
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
            
            if not self._search_engine:
                raise KnowledgeAgentError("Search engine not initialized")
            
            # Create search options from kwargs
            from ..models import SearchOptions
            
            # Handle category and tag filters
            include_categories = []
            if "category" in options and options["category"]:
                include_categories = [options["category"]]
            elif "include_categories" in options:
                include_categories = options["include_categories"]
            
            include_tags = []
            if "tag" in options and options["tag"]:
                include_tags = [options["tag"]]
            elif "include_tags" in options:
                include_tags = options["include_tags"]
            
            search_options = SearchOptions(
                max_results=options.get("max_results", 10),
                include_categories=include_categories,
                include_tags=include_tags,
                sort_by=options.get("sort_by", "relevance"),
                group_by_category=options.get("group_by_category", False)
            )
            
            # Execute search
            search_results = self._search_engine.search(query, search_options)
            
            # Convert to dictionary format
            results_dict = {
                "query": search_results.query,
                "total_results": search_results.total_found,
                "search_time_ms": search_results.search_time_ms,
                "results": [
                    {
                        "item_id": result.item.id,
                        "title": result.item.title,
                        "content": result.item.content[:200] + "..." if len(result.item.content) > 200 else result.item.content,
                        "source_type": result.item.source_type.value,
                        "source_path": result.item.source_path,
                        "categories": [{"id": c.id, "name": c.name} for c in result.item.categories],
                        "tags": [{"id": t.id, "name": t.name} for t in result.item.tags],
                        "relevance_score": result.relevance_score,
                        "matched_fields": result.matched_fields,
                    }
                    for result in search_results.results
                ],
                "grouped_results": search_results.grouped_results if search_results.grouped_results else {},
                "suggestions": options.get("include_suggestions", False) and self._search_engine.suggest(query) or []
            }
            
            self.logger.info(f"Found {search_results.total_found} results in {search_results.search_time_ms:.2f}ms")
            
            return results_dict
            
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
            
            if not self._data_import_export:
                raise KnowledgeAgentError("Data import/export not initialized")
            
            if format.lower() != "json":
                raise KnowledgeAgentError(f"Unsupported export format: {format}")
            
            # Export data using the data import/export component
            export_data = self._data_import_export.export_to_json()
            
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
            
            if not self._data_import_export:
                raise KnowledgeAgentError("Data import/export not initialized")
            
            # Validate data structure
            if not isinstance(data, dict):
                raise KnowledgeAgentError("Import data must be a dictionary")
            
            # Import data using the data import/export component
            success = self._data_import_export.import_from_json(data)
            
            if success:
                item_count = len(data.get("knowledge_items", []))
                self.logger.info(f"Successfully imported {item_count} items")
                
                # Rebuild search index after import
                if self._search_engine and self._storage_manager:
                    self.logger.info("Rebuilding search index after import...")
                    all_items = self._storage_manager.get_all_knowledge_items()
                    self._search_engine.rebuild_index(all_items)
                    self.logger.info("✓ Search index rebuilt")
            else:
                self.logger.warning("Import completed with warnings or partial success")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            raise KnowledgeAgentError(f"Failed to import data: {e}")
    
    def get_similar_items(self, item_id: str, limit: int = 10) -> List[KnowledgeItem]:
        """
        Find items similar to the given knowledge item.
        
        Args:
            item_id: ID of the reference item
            limit: Maximum number of similar items to return
            
        Returns:
            List of similar knowledge items
            
        Raises:
            KnowledgeAgentError: If retrieval fails
        """
        try:
            self.logger.info(f"Finding similar items to: {item_id}")
            
            if not self._search_engine:
                raise KnowledgeAgentError("Search engine not initialized")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # Get the reference item
            item = self._storage_manager.get_knowledge_item(item_id)
            if not item:
                raise KnowledgeAgentError(f"Knowledge item not found: {item_id}")
            
            # Find similar items using search engine
            similar_items = self._search_engine.get_similar_items(item, limit=limit)
            
            self.logger.info(f"Found {len(similar_items)} similar items")
            
            return similar_items
            
        except Exception as e:
            self.logger.error(f"Error finding similar items: {e}")
            raise KnowledgeAgentError(f"Failed to find similar items: {e}")
    
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
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for all operations.
        
        Returns:
            Performance metrics dictionary
        """
        monitor = get_performance_monitor()
        return monitor.get_metrics()
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error summary.
        
        Returns:
            Error summary dictionary
        """
        tracker = get_error_tracker()
        return tracker.get_error_summary()
    
    def log_monitoring_report(self) -> None:
        """Log a comprehensive monitoring report."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("KNOWLEDGE AGENT MONITORING REPORT")
        self.logger.info("=" * 60)
        
        # Log statistics
        try:
            stats = self.get_statistics()
            self.logger.info("\nKnowledge Base Statistics:")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
        
        # Log performance metrics
        monitor = get_performance_monitor()
        monitor.log_metrics()
        
        # Log error summary
        tracker = get_error_tracker()
        tracker.log_error_summary()
        
        self.logger.info("=" * 60)
    
    def shutdown(self) -> None:
        """Shutdown the knowledge agent and cleanup resources."""
        if self._shutdown_requested:
            self.logger.warning("Shutdown already in progress")
            return
        
        self._shutdown_requested = True
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("Initiating knowledge agent core shutdown...")
            self.logger.info("=" * 60)
            
            # Cleanup components
            self._cleanup_components()
            
            self._initialized = False
            self.logger.info("=" * 60)
            self.logger.info("Knowledge agent core shutdown complete")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise KnowledgeAgentError(f"Failed to shutdown cleanly: {e}")
    
    def _cleanup_components(self) -> None:
        """Cleanup all initialized components."""
        cleanup_errors = []
        
        # Cleanup search engine
        if self._search_engine:
            try:
                self.logger.info("Closing search engine...")
                if hasattr(self._search_engine, 'close'):
                    self._search_engine.close()
                self.logger.info("✓ Search engine closed")
            except Exception as e:
                error_msg = f"Failed to close search engine: {e}"
                self.logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Cleanup storage manager
        if self._storage_manager:
            try:
                self.logger.info("Closing storage manager...")
                if hasattr(self._storage_manager, 'close'):
                    self._storage_manager.close()
                self.logger.info("✓ Storage manager closed")
            except Exception as e:
                error_msg = f"Failed to close storage manager: {e}"
                self.logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Cleanup knowledge organizer
        if self._knowledge_organizer:
            try:
                self.logger.info("Cleaning up knowledge organizer...")
                if hasattr(self._knowledge_organizer, 'cleanup'):
                    self._knowledge_organizer.cleanup()
                self.logger.info("✓ Knowledge organizer cleaned up")
            except Exception as e:
                error_msg = f"Failed to cleanup knowledge organizer: {e}"
                self.logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        # Cleanup data processors
        if self._data_processors:
            try:
                self.logger.info("Cleaning up data processors...")
                for processor_name, processor in self._data_processors.items():
                    if hasattr(processor, 'cleanup'):
                        processor.cleanup()
                self.logger.info(f"✓ Cleaned up {len(self._data_processors)} data processors")
            except Exception as e:
                error_msg = f"Failed to cleanup data processors: {e}"
                self.logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        if cleanup_errors:
            self.logger.warning(f"Cleanup completed with {len(cleanup_errors)} errors")
        else:
            self.logger.info("All components cleaned up successfully")
    
    def is_initialized(self) -> bool:
        """Check if the agent is fully initialized."""
        return self._initialized
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested
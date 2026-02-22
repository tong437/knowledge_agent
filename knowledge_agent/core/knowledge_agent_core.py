"""
知识管理智能体核心实现模块。
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..models import KnowledgeItem, DataSource, Category, Tag, Relationship, SourceType
from ..interfaces import DataSourceProcessor, KnowledgeOrganizer, SearchEngine, StorageManager
from ..storage import SQLiteStorageManager
from ..organizers import KnowledgeOrganizerImpl
from ..search import SearchEngineImpl
from ..processors import DocumentProcessor, PDFProcessor, CodeProcessor, WebProcessor
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
from .source_type_detector import SourceTypeDetector
from .security_validator import SecurityValidator


class KnowledgeAgentCore:
    """
    个人知识管理智能体核心实现。
    
    协调各组件之间的交互，提供统一的知识管理功能。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化知识管理智能体核心。
        
        Args:
            config: 配置字典（可选）
        """
        self.logger = logging.getLogger("knowledge_agent.core")
        self.config = config or {}
        
        # 组件实例（将在后续任务中初始化）
        self._storage_manager: Optional[StorageManager] = None
        self._data_processors: Dict[str, DataSourceProcessor] = {}
        self._knowledge_organizer: Optional[KnowledgeOrganizer] = None
        self._search_engine: Optional[SearchEngine] = None
        self._data_import_export: Optional[DataImportExport] = None
        
        # 组件注册表，用于依赖注入
        self._registry: ComponentRegistry = get_component_registry()
        
        # 配置管理器
        self._config_manager: Optional[ConfigManager] = None
        
        # 初始化状态
        self._initialized = False
        self._shutdown_requested = False
        
        # 初始化组件
        self._initialize_components()
        
        self._initialized = True
        self.logger.info("Knowledge agent core initialized successfully")
    
    def _initialize_components(self) -> None:
        """根据配置初始化核心组件。"""
        try:
            self.logger.info("Starting component initialization...")
            
            # 如果提供了配置文件路径，则初始化配置管理器
            config_path = self.config.get("config_path")
            if config_path:
                self._config_manager = get_config_manager(config_path)
                self.logger.info(f"✓ Loaded configuration from {config_path}")
                # 将加载的配置与提供的配置合并
                loaded_config = self._config_manager.get_config()
                # 用加载的值更新 self.config
                if not self.config.get("storage"):
                    self.config["storage"] = {
                        "type": loaded_config.storage.type,
                        "path": loaded_config.storage.path
                    }
            
            # 向注册表注册组件
            self._register_components()
            
            # 初始化存储管理器
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
            
            # 初始化知识组织器
            if self._storage_manager:
                self._knowledge_organizer = KnowledgeOrganizerImpl(self._storage_manager)
                self._registry.set_instance("knowledge_organizer", self._knowledge_organizer)
                self.logger.info("✓ Initialized knowledge organizer")
            else:
                self.logger.warning("Storage manager not available, knowledge organizer not initialized")
            
            # 初始化搜索引擎
            search_config = self.config.get("search", {})
            index_dir = search_config.get("index_dir", "search_index")
            self._search_engine = SearchEngineImpl(index_dir)
            self._registry.set_instance("search_engine", self._search_engine)
            self.logger.info(f"✓ Initialized search engine with index at {index_dir}")
            
            # 初始化数据处理器
            self._initialize_data_processors()
            
            # 初始化数据导入导出
            self._data_import_export = DataImportExport(self._storage_manager)
            self.logger.info("✓ Initialized data import/export")
            
            # 记录组件注册表状态
            self._registry.log_status()
            
            self.logger.info("Component initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            # 清理已部分初始化的组件
            self._cleanup_components()
            raise KnowledgeAgentError(f"Component initialization failed: {e}")
    
    def _register_components(self) -> None:
        """将所有组件注册到组件注册表。"""
        self.logger.info("Registering components with registry...")
        
        # 注册存储管理器
        self._registry.register(
            name="storage_manager",
            component_type=SQLiteStorageManager,
            dependencies=[]
        )
        
        # 注册知识组织器
        self._registry.register(
            name="knowledge_organizer",
            component_type=KnowledgeOrganizerImpl,
            dependencies=["storage_manager"]
        )
        
        # 注册搜索引擎
        self._registry.register(
            name="search_engine",
            component_type=SearchEngineImpl,
            dependencies=[]
        )
        
        # 注册数据处理器
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
        
        # 注册网页处理器
        self._registry.register(
            name="web_processor",
            component_type=WebProcessor,
            dependencies=[]
        )
        
        self.logger.info("Components registered with registry")
    
    def _initialize_data_processors(self) -> None:
        """初始化所有数据源处理器。"""
        self.logger.info("Initializing data processors...")
        
        # 初始化文档处理器
        doc_processor = DocumentProcessor()
        self._data_processors["document"] = doc_processor
        self._data_processors["txt"] = doc_processor
        self._data_processors["markdown"] = doc_processor
        self._registry.set_instance("document_processor", doc_processor)
        
        # 初始化 PDF 处理器
        pdf_processor = PDFProcessor()
        self._data_processors["pdf"] = pdf_processor
        self._registry.set_instance("pdf_processor", pdf_processor)
        
        # 初始化代码处理器
        code_processor = CodeProcessor()
        self._data_processors["code"] = code_processor
        self._data_processors["python"] = code_processor
        self._data_processors["javascript"] = code_processor
        self._data_processors["java"] = code_processor
        self._registry.set_instance("code_processor", code_processor)
        
        # 初始化网页处理器
        web_processor = WebProcessor()
        self._data_processors["web"] = web_processor
        self._registry.set_instance("web_processor", web_processor)
        
        self.logger.info(f"✓ Initialized {len(self._data_processors)} data processors")
    
    @monitor_performance("collect_knowledge")
    @track_errors({"component": "knowledge_collection"})
    def collect_knowledge(self, source: DataSource) -> KnowledgeItem:
        """
        从数据源收集知识。
        
        Args:
            source: 要处理的数据源
            
        Returns:
            KnowledgeItem: 创建的知识条目
            
        Raises:
            KnowledgeAgentError: 收集失败时抛出
        """
        try:
            self.logger.info(f"Collecting knowledge from: {source.path}")
            
            # 根据数据源类型确定合适的处理器（未注册类型会抛出 NotImplementedError）
            try:
                processor = self._get_processor_for_source(source)
            except NotImplementedError as e:
                raise KnowledgeAgentError(
                    f"No processor available for source type: {source.source_type.value}"
                ) from e
            
            # 验证数据源
            if not processor.validate(source):
                raise KnowledgeAgentError(f"Invalid data source: {source.path}")
            
            # 处理数据源以创建知识条目
            item = processor.process(source)
            
            # 将条目保存到存储
            if self._storage_manager:
                self._storage_manager.save_knowledge_item(item)
                self.logger.info(f"✓ Saved knowledge item: {item.id}")
            
            # 更新搜索索引
            if self._search_engine:
                self._search_engine.update_index(item)
                self.logger.info(f"✓ Updated search index for item: {item.id}")
            
            self.logger.info(f"Successfully collected knowledge from: {source.path}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error collecting knowledge: {e}")
            raise KnowledgeAgentError(f"Failed to collect knowledge: {e}")
    
    def _get_processor_for_source(self, source: DataSource) -> DataSourceProcessor:
        """
        获取适合数据源的处理器。

        Args:
            source: 数据源

        Returns:
            匹配的 DataSourceProcessor 实例

        Raises:
            NotImplementedError: 没有注册对应类型的处理器时抛出
        """
        source_type = source.source_type.value.lower()

        # 检查是否有直接匹配
        if source_type in self._data_processors:
            return self._data_processors[source_type]

        # 通过文件扩展名进行更精确的匹配
        if source.path:
            ext = source.path.split('.')[-1].lower()
            if ext in self._data_processors:
                return self._data_processors[ext]

            # 将常见扩展名映射到处理器
            if ext in ['txt', 'md', 'doc', 'docx']:
                processor = self._data_processors.get('document')
                if processor:
                    return processor
            elif ext in ['py', 'js', 'java', 'cpp', 'c', 'ts']:
                processor = self._data_processors.get('code')
                if processor:
                    return processor
            elif ext == 'pdf':
                processor = self._data_processors.get('pdf')
                if processor:
                    return processor

        raise NotImplementedError(
            f"No processor registered for source type: {source.source_type.value}"
        )

    
    @monitor_performance("organize_knowledge")
    @track_errors({"component": "knowledge_organization"})
    def organize_knowledge(self, item: KnowledgeItem) -> Dict[str, Any]:
        """
        组织知识条目（分类、打标签、查找关联关系）。
        
        Args:
            item: 要组织的知识条目
            
        Returns:
            包含组织结果的字典
            
        Raises:
            KnowledgeAgentError: 组织失败时抛出
        """
        try:
            self.logger.info(f"Organizing knowledge item: {item.id}")
            
            if not self._knowledge_organizer:
                raise KnowledgeAgentError("Knowledge organizer not initialized")
            
            # 对条目进行分类
            categories = self._knowledge_organizer.classify(item)
            self.logger.info(f"Classified into {len(categories)} categories")
            
            # 生成标签
            tags = self._knowledge_organizer.generate_tags(item)
            self.logger.info(f"Generated {len(tags)} tags")
            
            # 查找关联关系
            relationships = self._knowledge_organizer.find_relationships(item)
            self.logger.info(f"Found {len(relationships)} relationships")
            
            # 用分类和标签更新条目
            for category in categories:
                item.add_category(category)
            for tag in tags:
                item.add_tag(tag)
            
            # 保存已组织的条目
            if self._storage_manager:
                self._storage_manager.save_knowledge_item(item)
            
            # 用关联关系更新知识图谱
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
        搜索知识条目。
        
        Args:
            query: 搜索查询字符串
            **options: 搜索选项
            
        Returns:
            包含搜索结果的字典
            
        Raises:
            KnowledgeAgentError: 搜索失败时抛出
        """
        try:
            self.logger.info(f"Searching knowledge: {query}")
            
            if not self._search_engine:
                raise KnowledgeAgentError("Search engine not initialized")
            
            # 从关键字参数创建搜索选项
            from ..models import SearchOptions
            
            # 处理分类和标签过滤器
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
            
            # 执行搜索
            search_results = self._search_engine.search(query, search_options)
            
            # 转换为字典格式
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
        根据 ID 获取知识条目。
        
        Args:
            item_id: 要获取的条目 ID
            
        Returns:
            找到则返回 KnowledgeItem，否则返回 None
            
        Raises:
            KnowledgeAgentError: 获取失败时抛出
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
        列出知识条目，支持可选的过滤条件。
        
        委托给存储层的 query_knowledge_items() 方法，
        在数据库层面完成过滤和分页，避免加载全部数据到内存。
        
        Args:
            **filters: 过滤条件（category、tag、limit、offset）
            
        Returns:
            知识条目列表
            
        Raises:
            KnowledgeAgentError: 列出失败时抛出
        """
        try:
            self.logger.info("Listing knowledge items")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # 委托给存储层的 query_knowledge_items() 方法
            category = filters.get("category")
            tag = filters.get("tag")
            limit = filters.get("limit", 50)
            offset = filters.get("offset", 0)
            items = self._storage_manager.query_knowledge_items(
                category=category, tag=tag, limit=limit, offset=offset
            )
            
            self.logger.info(f"Retrieved {len(items)} knowledge items")
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error listing knowledge items: {e}")
            raise KnowledgeAgentError(f"Failed to list knowledge items: {e}")
    
    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        导出所有知识数据。
        
        Args:
            format: 导出格式（目前仅支持 'json'）
            
        Returns:
            导出的数据字典
            
        Raises:
            KnowledgeAgentError: 导出失败时抛出
        """
        try:
            self.logger.info(f"Exporting data in {format} format")
            
            if not self._data_import_export:
                raise KnowledgeAgentError("Data import/export not initialized")
            
            if format.lower() != "json":
                raise KnowledgeAgentError(f"Unsupported export format: {format}")
            
            # 使用数据导入导出组件导出数据
            export_data = self._data_import_export.export_to_json()
            
            self.logger.info(f"Successfully exported {len(export_data.get('knowledge_items', []))} items")
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise KnowledgeAgentError(f"Failed to export data: {e}")
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """
        导入知识数据。
        
        Args:
            data: 要导入的数据字典（必须包含 knowledge_items、categories、tags、relationships）
            
        Returns:
            成功返回 True，否则返回 False
            
        Raises:
            KnowledgeAgentError: 导入失败时抛出
        """
        try:
            self.logger.info("Importing knowledge data")
            
            if not self._data_import_export:
                raise KnowledgeAgentError("Data import/export not initialized")
            
            # 验证数据结构
            if not isinstance(data, dict):
                raise KnowledgeAgentError("Import data must be a dictionary")
            
            # 使用数据导入导出组件导入数据
            result = self._data_import_export.import_from_json(data)
            
            # import_from_json 返回结果摘要字典，判断是否成功导入
            success = isinstance(result, dict) and result.get("error_count", 0) == 0
            
            if success:
                item_count = len(data.get("knowledge_items", []))
                self.logger.info(f"Successfully imported {item_count} items")
                
                # 导入后重建搜索索引
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
        查找与给定知识条目相似的条目。
        
        Args:
            item_id: 参考条目的 ID
            limit: 返回的最大相似条目数量
            
        Returns:
            相似知识条目列表
            
        Raises:
            KnowledgeAgentError: 获取失败时抛出
        """
        try:
            self.logger.info(f"Finding similar items to: {item_id}")
            
            if not self._search_engine:
                raise KnowledgeAgentError("Search engine not initialized")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # 获取参考条目
            item = self._storage_manager.get_knowledge_item(item_id)
            if not item:
                raise KnowledgeAgentError(f"Knowledge item not found: {item_id}")
            
            # 使用搜索引擎查找相似条目
            similar_items = self._search_engine.get_similar_items(item, limit=limit)
            
            self.logger.info(f"Found {len(similar_items)} similar items")
            
            return similar_items
            
        except Exception as e:
            self.logger.error(f"Error finding similar items: {e}")
            raise KnowledgeAgentError(f"Failed to find similar items: {e}")
    
    def get_all_categories(self) -> List[Category]:
        """
        返回所有分类。
        
        Returns:
            分类列表
            
        Raises:
            KnowledgeAgentError: 获取失败时抛出
        """
        try:
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            return self._storage_manager.get_all_categories()
        except Exception as e:
            self.logger.error(f"Error retrieving categories: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve categories: {e}")
    
    def get_all_tags(self) -> List[Tag]:
        """
        返回所有标签。
        
        Returns:
            标签列表
            
        Raises:
            KnowledgeAgentError: 获取失败时抛出
        """
        try:
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            return self._storage_manager.get_all_tags()
        except Exception as e:
            self.logger.error(f"Error retrieving tags: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve tags: {e}")
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """
        返回知识图谱的节点和边数据。
        
        遍历所有知识条目作为节点，获取所有关系作为边，
        返回 {"nodes": [...], "edges": [...]} 格式的图谱数据。
        
        Returns:
            包含 nodes 和 edges 的字典
            
        Raises:
            KnowledgeAgentError: 获取失败时抛出
        """
        try:
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # 获取所有知识条目作为节点
            all_items = self._storage_manager.get_all_knowledge_items()
            nodes = [
                {
                    "id": item.id,
                    "title": item.title,
                    "source_type": item.source_type.value,
                }
                for item in all_items
            ]
            
            # 获取所有关系作为边
            edges = []
            for item in all_items:
                relationships = self._storage_manager.get_relationships_for_item(item.id)
                for rel in relationships:
                    edges.append({
                        "source_id": rel.source_id,
                        "target_id": rel.target_id,
                        "relationship_type": rel.relationship_type.value,
                        "strength": rel.strength,
                    })
            
            return {"nodes": nodes, "edges": edges}
            
        except Exception as e:
            self.logger.error(f"Error retrieving knowledge graph: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve knowledge graph: {e}")
    
    def update_knowledge_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新知识条目并重新索引。
        
        Args:
            item_id: 知识条目 ID
            updates: 可更新字段字典
            
        Returns:
            更新成功返回 True，条目不存在返回 False
            
        Raises:
            KnowledgeAgentError: 更新失败时抛出
        """
        try:
            self.logger.info(f"Updating knowledge item: {item_id}")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # 委托给存储层执行更新
            success = self._storage_manager.update_knowledge_item(item_id, updates)
            
            # 如果更新成功且搜索引擎可用，重新索引该条目
            if success and self._search_engine:
                updated_item = self._storage_manager.get_knowledge_item(item_id)
                if updated_item:
                    self._search_engine.update_index(updated_item)
                    self.logger.info(f"Re-indexed knowledge item: {item_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating knowledge item: {e}")
            raise KnowledgeAgentError(f"Failed to update knowledge item: {e}")
    
    def delete_knowledge_item(self, item_id: str) -> bool:
        """
        删除知识条目及其关联数据和搜索索引。
        
        Args:
            item_id: 知识条目 ID
            
        Returns:
            删除成功返回 True，条目不存在返回 False
            
        Raises:
            KnowledgeAgentError: 删除失败时抛出
        """
        try:
            self.logger.info(f"Deleting knowledge item: {item_id}")
            
            if not self._storage_manager:
                raise KnowledgeAgentError("Storage manager not initialized")
            
            # 委托给存储层执行删除
            success = self._storage_manager.delete_knowledge_item(item_id)
            
            # 如果删除成功且搜索引擎可用，从索引中移除
            if success and self._search_engine:
                try:
                    self._search_engine.remove_from_index(item_id)
                    self.logger.info(f"Removed from search index: {item_id}")
                except Exception as index_err:
                    # 索引删除失败不影响主流程，仅记录日志
                    self.logger.warning(
                        f"Failed to remove item from search index: {index_err}"
                    )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting knowledge item: {e}")
            raise KnowledgeAgentError(f"Failed to delete knowledge item: {e}")
    
    def batch_collect_knowledge(
        self,
        directory_path: str,
        file_pattern: str = "*",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        遍历目录批量处理文件。
        
        对目录中匹配模式的文件逐一进行类型检测和知识收集，
        单文件失败不会中断整个流程。
        
        Args:
            directory_path: 目录路径
            file_pattern: 文件匹配模式（glob 格式）
            recursive: 是否递归处理子目录
            
        Returns:
            批量处理结果摘要，包含 success_count、failure_count、
            failed_files 和 errors
            
        Raises:
            KnowledgeAgentError: 目录路径无效或安全验证失败时抛出
        """
        self.logger.info(
            f"Batch collecting knowledge from: {directory_path} "
            f"(pattern={file_pattern}, recursive={recursive})"
        )
        
        # 安全验证：从配置中读取安全策略
        security_config = self.config.get("security", {})
        allowed_paths = security_config.get("allowed_paths")
        blocked_extensions = security_config.get("blocked_extensions")
        validator = SecurityValidator(
            allowed_paths=allowed_paths,
            blocked_extensions=blocked_extensions,
        )
        if not validator.validate_path(directory_path):
            raise KnowledgeAgentError(
                f"Directory path failed security validation: {directory_path}"
            )
        
        # 验证目录存在
        dir_path = Path(directory_path)
        if not dir_path.is_dir():
            raise KnowledgeAgentError(
                f"Directory does not exist: {directory_path}"
            )
        
        # 使用 glob 或 rglob 匹配文件
        if recursive:
            matched_files = list(dir_path.rglob(file_pattern))
        else:
            matched_files = list(dir_path.glob(file_pattern))
        
        # 只处理文件，跳过目录
        matched_files = [f for f in matched_files if f.is_file()]
        
        success_count = 0
        failure_count = 0
        failed_files: List[str] = []
        errors: List[str] = []
        
        for file_path in matched_files:
            file_str = str(file_path)
            try:
                # 安全验证单个文件
                if not validator.validate_path(file_str):
                    failure_count += 1
                    failed_files.append(file_str)
                    errors.append(f"Security validation failed: {file_str}")
                    continue
                
                # 自动检测数据源类型
                source_type = SourceTypeDetector.detect(file_str)
                source = DataSource(
                    path=file_str,
                    source_type=source_type,
                    metadata={"batch_source": directory_path},
                )
                
                # 收集知识
                self.collect_knowledge(source)
                success_count += 1
                
            except Exception as e:
                # 单文件失败不中断整个流程
                failure_count += 1
                failed_files.append(file_str)
                errors.append(f"{file_str}: {e}")
                self.logger.warning(f"Failed to process file: {file_str}, error: {e}")
        
        self.logger.info(
            f"Batch collection completed: {success_count} succeeded, "
            f"{failure_count} failed out of {len(matched_files)} files"
        )
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "failed_files": failed_files,
            "errors": errors,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息。
        
        使用 SQL COUNT 聚合查询，避免加载全部数据到内存。
        
        Returns:
            统计信息字典
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
            
            # 使用 SQL COUNT 聚合查询获取统计数据
            stats = self._storage_manager.get_database_stats()
            return {
                "total_items": stats.get("knowledge_items", 0),
                "total_categories": stats.get("categories", 0),
                "total_tags": stats.get("tags", 0),
                "total_relationships": stats.get("relationships", 0),
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving statistics: {e}")
            raise KnowledgeAgentError(f"Failed to retrieve statistics: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取所有操作的性能指标。
        
        Returns:
            性能指标字典
        """
        monitor = get_performance_monitor()
        return monitor.get_metrics()
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要。
        
        Returns:
            错误摘要字典
        """
        tracker = get_error_tracker()
        return tracker.get_error_summary()
    
    def log_monitoring_report(self) -> None:
        """记录综合监控报告。"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("KNOWLEDGE AGENT MONITORING REPORT")
        self.logger.info("=" * 60)
        
        # 记录统计信息
        try:
            stats = self.get_statistics()
            self.logger.info("\nKnowledge Base Statistics:")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
        
        # 记录性能指标
        monitor = get_performance_monitor()
        monitor.log_metrics()
        
        # 记录错误摘要
        tracker = get_error_tracker()
        tracker.log_error_summary()
        
        self.logger.info("=" * 60)
    
    def shutdown(self) -> None:
        """关闭知识管理智能体并清理资源。"""
        if self._shutdown_requested:
            self.logger.warning("Shutdown already in progress")
            return
        
        self._shutdown_requested = True
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("Initiating knowledge agent core shutdown...")
            self.logger.info("=" * 60)
            
            # 清理组件
            self._cleanup_components()
            
            self._initialized = False
            self.logger.info("=" * 60)
            self.logger.info("Knowledge agent core shutdown complete")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise KnowledgeAgentError(f"Failed to shutdown cleanly: {e}")
    
    def _cleanup_components(self) -> None:
        """清理所有已初始化的组件。"""
        cleanup_errors = []
        
        # 清理搜索引擎
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
        
        # 清理存储管理器
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
        
        # 清理知识组织器
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
        
        # 清理数据处理器
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
        """检查智能体是否已完全初始化。"""
        return self._initialized
    
    def is_shutdown_requested(self) -> bool:
        """检查是否已请求关闭。"""
        return self._shutdown_requested
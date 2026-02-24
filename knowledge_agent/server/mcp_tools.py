"""
知识管理功能的 MCP 工具注册模块。
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent
from ..models import DataSource, SourceType
from ..core.exceptions import KnowledgeAgentError
from ..core.source_type_detector import SourceTypeDetector
from ..core.security_validator import SecurityValidator
from ..core.config_manager import get_config_manager


def _validate_source_type(source_type: str) -> bool:
    """
    验证数据源类型是否受支持。

    Args:
        source_type: 待验证的数据源类型字符串

    Returns:
        有效返回 True，否则返回 False
    """
    valid_types = ["auto", "document", "pdf", "web", "code", "image"]
    return source_type.lower() in valid_types


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化标准结构的成功响应。

    Args:
        message: 成功消息
        data: 响应数据

    Returns:
        格式化后的响应字典
    """
    return {
        "status": "success",
        "message": message,
        **data
    }


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化标准结构的错误响应。

    Args:
        error: 发生的异常
        context: 操作的上下文信息

    Returns:
        格式化后的错误响应字典
    """
    return {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context
    }


def register_knowledge_tools(app: FastMCP, knowledge_core) -> None:
    """
    注册所有知识管理工具到 MCP 服务器。

    Args:
        app: FastMCP 应用实例
        knowledge_core: 知识代理核心实例
    """
    logger = logging.getLogger("knowledge_agent.mcp_tools")

    # 已实现处理器的数据源类型集合
    IMPLEMENTED_TYPES = {"document", "pdf", "code", "web"}

    @app.tool()
    def collect_knowledge(source_path: str, source_type: str = "auto") -> Dict[str, Any]:
        """
        从数据源收集知识。

        处理各种数据源（文档、PDF、网页、代码文件、图片），
        并在知识库中创建知识条目。

        Args:
            source_path: 数据源路径（文件路径或 URL）
            source_type: 数据源类型，可选值：auto、document、pdf、web、code、image

        Returns:
            包含状态和已创建知识条目信息的字典
        """
        try:
            # 验证参数
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

            # 检查非 auto 类型是否已实现处理器
            source_type_lower = source_type.lower()
            if source_type_lower != "auto" and source_type_lower not in IMPLEMENTED_TYPES:
                return {
                    "status": "not_implemented",
                    "message": f"Processor for '{source_type}' type is defined but not yet implemented",
                    "source_path": source_path,
                    "source_type": source_type,
                    "available_types": sorted(IMPLEMENTED_TYPES)
                }

            logger.info(f"Collecting knowledge from: {source_path} (type: {source_type})")

            # 确定数据源类型
            if source_type_lower == "auto":
                # 使用 SourceTypeDetector 自动检测类型
                detected_type = SourceTypeDetector.detect(source_path.strip())
                logger.info(f"Auto-detected source type: {detected_type.value}")
            else:
                type_mapping = {
                    "document": SourceType.DOCUMENT,
                    "pdf": SourceType.PDF,
                    "web": SourceType.WEB,
                    "code": SourceType.CODE,
                    "image": SourceType.IMAGE
                }
                detected_type = type_mapping.get(source_type_lower, SourceType.DOCUMENT)

            # 安全路径验证（仅对文件路径进行验证，URL 跳过）
            if detected_type != SourceType.WEB:
                try:
                    config_manager = get_config_manager()
                    config = config_manager.get_config()
                    allowed_paths = config.security.allowed_paths if hasattr(config, 'security') and hasattr(config.security, 'allowed_paths') else []
                    blocked_extensions = config.security.blocked_extensions if hasattr(config, 'security') and hasattr(config.security, 'blocked_extensions') else None
                except Exception:
                    # 配置加载失败时使用默认值
                    allowed_paths = []
                    blocked_extensions = None

                validator = SecurityValidator(
                    allowed_paths=allowed_paths,
                    blocked_extensions=blocked_extensions
                )
                if not validator.validate_path(source_path.strip()):
                    return _format_error_response(
                        ValueError(f"Path failed security validation: {source_path}"),
                        {"source_path": source_path, "source_type": source_type}
                    )

            # 创建数据源对象
            source = DataSource(
                path=source_path.strip(),
                source_type=detected_type,
                metadata={}
            )

            # 处理数据源
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
        使用自然语言或关键词搜索知识条目。

        在知识库中执行语义搜索以查找相关条目。
        支持关键词匹配和语义相似度搜索。

        Args:
            query: 搜索查询字符串（自然语言或关键词）
            max_results: 返回结果的最大数量（1-100）
            min_relevance: 最低相关性分数阈值（0.0 到 1.0）

        Returns:
            包含搜索结果和元数据的字典
        """
        try:
            # 验证参数
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

            # 执行搜索
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
        通过分类、标记和查找关系来组织知识条目。

        自动分类、生成相关标签，并识别与知识库中其他知识条目的关系。

        Args:
            item_id: 待组织的知识条目 ID
            force_reprocess: 是否强制重新处理已组织的条目

        Returns:
            包含组织结果（分类、标签、关系）的字典
        """
        try:
            # 验证参数
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )

            logger.info(f"Organizing knowledge item: {item_id}")

            # 获取知识条目
            item = knowledge_core.get_knowledge_item(item_id.strip())

            if not item:
                return _format_error_response(
                    ValueError(f"Knowledge item not found: {item_id}"),
                    {"item_id": item_id}
                )

            # 检查是否已组织且 force_reprocess 为 False
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

            # 组织知识条目
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
        根据 ID 获取指定的知识条目。

        返回知识条目的完整信息，包括内容、分类、标签和元数据。

        Args:
            item_id: 待获取的知识条目 ID

        Returns:
            包含知识条目数据或错误信息的字典
        """
        try:
            # 验证参数
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )

            logger.info(f"Retrieving knowledge item: {item_id}")

            # 获取知识条目
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
        列出知识条目，支持可选过滤。

        返回分页的知识条目列表，可按分类或标签进行过滤。

        Args:
            category: 按分类名称过滤（可选，空字符串表示不过滤）
            tag: 按标签名称过滤（可选，空字符串表示不过滤）
            limit: 返回条目的最大数量（1-100）
            offset: 分页跳过的条目数量

        Returns:
            包含知识条目列表和元数据的字典
        """
        try:
            # 验证参数
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

            # 构建过滤条件
            filters = {}
            if category and category.strip():
                filters["category"] = category.strip()
            if tag and tag.strip():
                filters["tag"] = tag.strip()
            filters["limit"] = limit
            filters["offset"] = offset

            # 获取知识条目
            items = knowledge_core.list_knowledge_items(**filters)

            # 将条目转换为字典
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
        以指定格式导出所有知识数据。

        导出完整的知识库，包括条目、分类、标签和关系，以结构化格式输出。

        Args:
            format: 导出格式（目前仅支持 'json'）
            include_content: 是否包含完整内容，还是仅导出元数据

        Returns:
            包含导出结果或下载信息的字典
        """
        try:
            # 验证参数
            if format.lower() not in ["json"]:
                return _format_error_response(
                    ValueError(f"Unsupported export format: {format}. Currently only 'json' is supported"),
                    {"format": format}
                )

            logger.info(f"Exporting knowledge data in {format} format")

            # 导出数据
            export_data = knowledge_core.export_data(format=format.lower())

            # 可选地过滤掉内容
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
        从文件导入知识数据。

        从导出的数据文件中导入知识条目、分类、标签和关系。

        Args:
            data_path: 待导入的数据文件路径
            format: 数据文件格式（目前仅支持 'json'）
            merge_strategy: 处理已存在条目的策略，可选值：skip_existing、overwrite、merge

        Returns:
            包含导入结果的字典
        """
        try:
            # 验证参数
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

            # 读取数据文件
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

            # 导入数据
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
        获取知识库统计信息。

        返回知识库的统计数据，包括条目、分类、标签和关系的数量。

        Returns:
            包含知识库统计信息的字典
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
        获取所有操作的性能指标。

        返回性能指标，包括操作次数、持续时间、成功率和错误率。

        Returns:
            包含性能指标的字典
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
        获取错误摘要和最近的错误信息。

        返回系统中发生的错误摘要，包括按类型统计的错误数量和最近的错误详情。

        Returns:
            包含错误摘要的字典
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

    @app.tool()
    def update_knowledge_item(item_id: str, title: str = "", content: str = "",
                              categories: str = "", tags: str = "") -> Dict[str, Any]:
        """
        更新指定的知识条目。

        根据提供的参数部分更新知识条目的标题、内容、分类或标签。
        仅非空参数会被更新。

        Args:
            item_id: 待更新的知识条目 ID（必需）
            title: 新标题（可选，空字符串表示不更新）
            content: 新内容（可选，空字符串表示不更新）
            categories: 新分类，以逗号分隔（可选，空字符串表示不更新）
            tags: 新标签，以逗号分隔（可选，空字符串表示不更新）

        Returns:
            包含更新结果的字典
        """
        try:
            # 验证参数
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )

            logger.info(f"Updating knowledge item: {item_id}")

            # 构建更新字典，只包含非空参数
            updates = {}
            if title and title.strip():
                updates["title"] = title.strip()
            if content and content.strip():
                updates["content"] = content.strip()
            if categories and categories.strip():
                updates["categories"] = [c.strip() for c in categories.split(",") if c.strip()]
            if tags and tags.strip():
                updates["tags"] = [t.strip() for t in tags.split(",") if t.strip()]

            if not updates:
                return _format_error_response(
                    ValueError("At least one field must be provided for update"),
                    {"item_id": item_id}
                )

            # 调用核心层更新
            result = knowledge_core.update_knowledge_item(item_id.strip(), updates)

            if result:
                return _format_success_response(
                    f"Successfully updated knowledge item {item_id}",
                    {
                        "item_id": item_id,
                        "updated_fields": list(updates.keys())
                    }
                )
            else:
                return _format_error_response(
                    ValueError(f"Knowledge item not found: {item_id}"),
                    {"item_id": item_id}
                )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"item_id": item_id})
        except Exception as e:
            logger.error(f"Unexpected error updating knowledge item: {e}")
            return _format_error_response(e, {"item_id": item_id})

    @app.tool()
    def delete_knowledge_item(item_id: str) -> Dict[str, Any]:
        """
        删除指定的知识条目。

        从知识库中永久删除指定 ID 的知识条目及其相关索引。

        Args:
            item_id: 待删除的知识条目 ID

        Returns:
            包含删除结果的字典
        """
        try:
            # 验证参数
            if not item_id or not item_id.strip():
                return _format_error_response(
                    ValueError("item_id cannot be empty"),
                    {"item_id": item_id}
                )

            logger.info(f"Deleting knowledge item: {item_id}")

            # 调用核心层删除
            result = knowledge_core.delete_knowledge_item(item_id.strip())

            if result:
                return _format_success_response(
                    f"Successfully deleted knowledge item {item_id}",
                    {"item_id": item_id}
                )
            else:
                return _format_error_response(
                    ValueError(f"Knowledge item not found: {item_id}"),
                    {"item_id": item_id}
                )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"item_id": item_id})
        except Exception as e:
            logger.error(f"Unexpected error deleting knowledge item: {e}")
            return _format_error_response(e, {"item_id": item_id})

    @app.tool()
    def batch_collect_knowledge(directory_path: str, file_pattern: str = "*",
                                recursive: bool = False) -> Dict[str, Any]:
        """
        批量收集目录中的知识。

        扫描指定目录中匹配模式的文件，批量处理并收集知识条目。

        Args:
            directory_path: 目标目录路径（必需）
            file_pattern: 文件匹配模式，支持逗号分隔的多个模式（默认 "*" 匹配所有文件）
                         例如: "*.pdf" 或 "*.doc,*.docx,*.pdf"
            recursive: 是否递归扫描子目录（默认 False）

        Returns:
            包含批量收集结果摘要的字典
        """
        try:
            # 验证参数
            if not directory_path or not directory_path.strip():
                return _format_error_response(
                    ValueError("directory_path cannot be empty"),
                    {"directory_path": directory_path}
                )

            logger.info(f"Batch collecting knowledge from: {directory_path} "
                        f"(pattern: {file_pattern}, recursive: {recursive})")

            # 调用核心层批量收集
            result = knowledge_core.batch_collect_knowledge(
                directory_path.strip(), file_pattern, recursive
            )

            return _format_success_response(
                f"Batch collection completed for {directory_path}",
                {
                    "directory_path": directory_path,
                    "file_pattern": file_pattern,
                    "recursive": recursive,
                    "success_count": result.get("success_count", 0),
                    "failure_count": result.get("failure_count", 0),
                    "total_count": result.get("total_count", 0),
                    "failed_files": result.get("failed_files", []),
                    "collected_items": result.get("collected_items", [])
                }
            )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"directory_path": directory_path})
        except Exception as e:
            logger.error(f"Unexpected error in batch collection: {e}")
            return _format_error_response(e, {"directory_path": directory_path})

    @app.tool()
    def suggest_search(partial_query: str) -> Dict[str, Any]:
        """
        根据部分输入提供搜索建议。

        基于知识库索引和语义模型，为用户的部分查询提供自动补全建议。

        Args:
            partial_query: 部分查询字符串

        Returns:
            包含搜索建议列表的字典
        """
        try:
            # 验证参数
            if not partial_query or not partial_query.strip():
                return _format_error_response(
                    ValueError("partial_query cannot be empty"),
                    {"partial_query": partial_query}
                )

            logger.info(f"Getting search suggestions for: {partial_query}")

            # TODO: 应通过 knowledge_core 的公开接口调用，待核心层添加 suggest() 方法后修复
            suggestions = knowledge_core._search_engine.suggest(partial_query.strip())

            return _format_success_response(
                f"Found {len(suggestions)} suggestions for '{partial_query}'",
                {
                    "partial_query": partial_query,
                    "suggestions": suggestions,
                    "count": len(suggestions)
                }
            )

        except KnowledgeAgentError as e:
            logger.error(f"Knowledge agent error: {e}")
            return _format_error_response(e, {"partial_query": partial_query})
        except Exception as e:
            logger.error(f"Unexpected error getting search suggestions: {e}")
            return _format_error_response(e, {"partial_query": partial_query})

    logger.info("Knowledge management tools registered successfully")

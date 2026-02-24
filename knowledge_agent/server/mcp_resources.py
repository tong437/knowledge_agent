"""
知识管理的 MCP 资源注册模块。
"""

import logging
import json
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextContent
from ..core.exceptions import KnowledgeAgentError


def _format_resource_response(data: Any) -> str:
    """
    将资源数据格式化为 JSON 字符串。

    Args:
        data: 待格式化的数据

    Returns:
        JSON 字符串表示
    """
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to format response: {str(e)}"})


def _format_error_resource(error: Exception) -> str:
    """
    将错误格式化为 JSON 资源响应。

    Args:
        error: 发生的异常

    Returns:
        包含错误信息的 JSON 字符串
    """
    return json.dumps({
        "error": type(error).__name__,
        "message": str(error)
    })


def register_knowledge_resources(app: FastMCP, knowledge_core) -> None:
    """
    注册知识管理资源到 MCP 服务器。

    资源通过基于 URI 的端点提供对知识库数据的只读访问。

    Args:
        app: FastMCP 应用实例
        knowledge_core: 知识代理核心实例
    """
    logger = logging.getLogger("knowledge_agent.mcp_resources")

    @app.resource("knowledge://items")
    def get_knowledge_items() -> str:
        """
        获取所有知识条目列表。

        返回知识库中所有知识条目的 JSON 数组，
        包括其元数据、分类和标签。

        Returns:
            包含所有知识条目的 JSON 字符串
        """
        try:
            logger.info("Retrieving all knowledge items resource")

            # 从存储中获取所有条目
            items = knowledge_core.list_knowledge_items()

            # 转换为字典
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
        根据 ID 获取指定的知识条目。

        返回单个知识条目的完整信息，包括其内容、分类、标签和元数据。

        Args:
            item_id: 待获取的知识条目 ID

        Returns:
            包含知识条目的 JSON 字符串
        """
        try:
            logger.info(f"Retrieving knowledge item resource: {item_id}")

            # 获取知识条目
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
        获取所有分类列表。

        返回知识库中所有分类及其层级结构和使用统计。

        Returns:
            包含所有分类的 JSON 字符串
        """
        try:
            logger.info("Retrieving categories resource")

            # 通过公开接口获取分类
            categories = knowledge_core.get_all_categories()

            # 转换为字典
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
        获取所有标签列表。

        返回知识库中所有标签及其使用次数和颜色编码。

        Returns:
            包含所有标签的 JSON 字符串
        """
        try:
            logger.info("Retrieving tags resource")

            # 通过公开接口获取标签
            tags = knowledge_core.get_all_tags()

            # 转换为字典
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
        获取知识图谱结构。

        返回完整的知识图谱，以节点和边的形式展示知识条目之间的关系。

        Returns:
            包含知识图谱的 JSON 字符串
        """
        try:
            logger.info("Retrieving knowledge graph resource")

            # 通过公开接口获取知识图谱
            graph_data = knowledge_core.get_knowledge_graph()

            response = {
                "resource": "knowledge://graph",
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", [])),
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", [])
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
        获取知识库统计信息。

        返回全面的统计数据，包括条目、分类、标签、关系的数量以及数据源类型分布。

        Returns:
            包含知识库统计信息的 JSON 字符串
        """
        try:
            logger.info("Retrieving knowledge statistics resource")

            # 通过公开接口获取统计信息
            stats = knowledge_core.get_statistics()

            # 通过公开接口获取数据源类型分布
            items = knowledge_core.list_knowledge_items()
            source_distribution = {}
            for item in items:
                source_type = item.source_type.value
                source_distribution[source_type] = source_distribution.get(source_type, 0) + 1
            stats["source_type_distribution"] = source_distribution

            # 添加时间戳
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


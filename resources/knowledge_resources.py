"""知识管理 MCP 资源端点"""
import json
from typing import Any
from resources import YA_MCPServer_Resource
from modules.YA_Common.utils.logger import get_logger
from core.exceptions import KnowledgeAgentError

logger = get_logger("resources.knowledge_resources")


def _format_resource_response(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to format response: {str(e)}"})


def _format_error_resource(error: Exception) -> str:
    return json.dumps({"error": type(error).__name__, "message": str(error)})


@YA_MCPServer_Resource(
    "knowledge://items",
    name="knowledge_items",
    title="Knowledge Items",
    description="获取所有知识条目列表",
)
def get_knowledge_items() -> str:
    try:
        logger.info("Retrieving all knowledge items resource")
        from setup import get_core

        core = get_core()
        items = core.list_knowledge_items()
        items_data = [item.to_dict() for item in items]
        response = {
            "resource": "knowledge://items",
            "count": len(items_data),
            "items": items_data,
        }
        return _format_resource_response(response)
    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return _format_resource_response(
            {
                "resource": "knowledge://items",
                "status": "not_implemented",
                "message": str(e),
                "items": [],
            }
        )
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_resource(e)
    except Exception as e:
        logger.error(f"Error retrieving knowledge items resource: {e}")
        return _format_error_resource(e)


@YA_MCPServer_Resource(
    "knowledge://items/{item_id}",
    name="knowledge_item_by_id",
    title="Knowledge Item By ID",
    description="根据 ID 获取指定的知识条目",
)
def get_knowledge_item_by_id(item_id: str) -> str:
    try:
        logger.info(f"Retrieving knowledge item resource: {item_id}")
        from setup import get_core

        core = get_core()
        item = core.get_knowledge_item(item_id)

        if not item:
            return _format_resource_response(
                {
                    "resource": f"knowledge://items/{item_id}",
                    "error": "NotFound",
                    "message": f"Knowledge item not found: {item_id}",
                }
            )

        response = {
            "resource": f"knowledge://items/{item_id}",
            "item": item.to_dict(),
        }
        return _format_resource_response(response)
    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return _format_resource_response(
            {
                "resource": f"knowledge://items/{item_id}",
                "status": "not_implemented",
                "message": str(e),
            }
        )
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_resource(e)
    except Exception as e:
        logger.error(f"Error retrieving knowledge item resource: {e}")
        return _format_error_resource(e)


@YA_MCPServer_Resource(
    "knowledge://categories",
    name="knowledge_categories",
    title="Knowledge Categories",
    description="获取所有分类列表",
)
def get_categories() -> str:
    try:
        logger.info("Retrieving categories resource")
        from setup import get_core

        core = get_core()
        categories = core.get_all_categories()
        categories_data = [cat.to_dict() for cat in categories]
        response = {
            "resource": "knowledge://categories",
            "count": len(categories_data),
            "categories": categories_data,
        }
        return _format_resource_response(response)
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_resource(e)
    except Exception as e:
        logger.error(f"Error retrieving categories resource: {e}")
        return _format_error_resource(e)


@YA_MCPServer_Resource(
    "knowledge://tags",
    name="knowledge_tags",
    title="Knowledge Tags",
    description="获取所有标签列表",
)
def get_tags() -> str:
    try:
        logger.info("Retrieving tags resource")
        from setup import get_core

        core = get_core()
        tags = core.get_all_tags()
        tags_data = [tag.to_dict() for tag in tags]
        response = {
            "resource": "knowledge://tags",
            "count": len(tags_data),
            "tags": tags_data,
        }
        return _format_resource_response(response)
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_resource(e)
    except Exception as e:
        logger.error(f"Error retrieving tags resource: {e}")
        return _format_error_resource(e)


@YA_MCPServer_Resource(
    "knowledge://graph",
    name="knowledge_graph",
    title="Knowledge Graph",
    description="获取知识图谱结构",
)
def get_knowledge_graph() -> str:
    try:
        logger.info("Retrieving knowledge graph resource")
        from setup import get_core

        core = get_core()
        graph_data = core.get_knowledge_graph()
        response = {
            "resource": "knowledge://graph",
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", []),
        }
        return _format_resource_response(response)
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_resource(e)
    except Exception as e:
        logger.error(f"Error retrieving knowledge graph resource: {e}")
        return _format_error_resource(e)


@YA_MCPServer_Resource(
    "knowledge://stats",
    name="knowledge_stats",
    title="Knowledge Statistics",
    description="获取知识库统计信息",
)
def get_knowledge_stats() -> str:
    try:
        logger.info("Retrieving knowledge statistics resource")
        from setup import get_core

        core = get_core()
        stats = core.get_statistics()

        items = core.list_knowledge_items()
        source_distribution = {}
        for item in items:
            source_type = item.source_type.value
            source_distribution[source_type] = (
                source_distribution.get(source_type, 0) + 1
            )
        stats["source_type_distribution"] = source_distribution

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

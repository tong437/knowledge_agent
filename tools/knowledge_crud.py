"""
知识条目 CRUD 操作工具模块。

提供知识条目的获取、列表、更新和删除功能。
"""

from typing import Dict, Any
from tools import YA_MCPServer_Tool
from modules.YA_Common.utils.logger import get_logger
from core.exceptions import KnowledgeAgentError

logger = get_logger("tools.knowledge_crud")


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "success", "message": message, **data}


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "error", "error_type": type(error).__name__, "message": str(error), "context": context}


@YA_MCPServer_Tool(
    name="get_knowledge_item",
    title="Get Knowledge Item",
    description="根据 ID 获取指定的知识条目",
)
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
        if not item_id or not item_id.strip():
            return _format_error_response(
                ValueError("item_id cannot be empty"),
                {"item_id": item_id},
            )

        logger.info(f"Retrieving knowledge item: {item_id}")

        from setup import get_core
        core = get_core()
        item = core.get_knowledge_item(item_id.strip())

        if not item:
            return _format_error_response(
                ValueError(f"Knowledge item not found: {item_id}"),
                {"item_id": item_id},
            )

        return _format_success_response(
            f"Successfully retrieved knowledge item {item_id}",
            {"item": item.to_dict()},
        )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {"status": "not_implemented", "message": str(e), "item_id": item_id, "item": None}
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"item_id": item_id})
    except Exception as e:
        logger.error(f"Unexpected error retrieving knowledge item: {e}")
        return _format_error_response(e, {"item_id": item_id})


@YA_MCPServer_Tool(
    name="list_knowledge_items",
    title="List Knowledge Items",
    description="列出知识条目，支持可选过滤",
)
def list_knowledge_items(
    category: str = "",
    tag: str = "",
    limit: int = 50,
    offset: int = 0,
    include_content: bool = False,
) -> Dict[str, Any]:
    """
    列出知识条目，支持可选过滤。

    返回分页的知识条目列表，可按分类或标签进行过滤。
    默认返回精简信息（不含完整内容），以避免响应过大。

    Args:
        category: 按分类名称过滤（可选，空字符串表示不过滤）
        tag: 按标签名称过滤（可选，空字符串表示不过滤）
        limit: 返回条目的最大数量（1-100）
        offset: 分页跳过的条目数量
        include_content: 是否包含完整内容（默认 False，仅返回摘要信息）

    Returns:
        包含知识条目列表和元数据的字典
    """
    try:
        if limit < 1 or limit > 100:
            return _format_error_response(
                ValueError("limit must be between 1 and 100"),
                {"limit": limit},
            )

        if offset < 0:
            return _format_error_response(
                ValueError("offset must be non-negative"),
                {"offset": offset},
            )

        logger.info(
            f"Listing knowledge items (category: {category}, tag: {tag}, "
            f"limit: {limit}, offset: {offset}, include_content: {include_content})"
        )

        filters = {}
        if category and category.strip():
            filters["category"] = category.strip()
        if tag and tag.strip():
            filters["tag"] = tag.strip()
        filters["limit"] = limit
        filters["offset"] = offset

        from setup import get_core
        core = get_core()
        items = core.list_knowledge_items(**filters)

        if include_content:
            items_data = [item.to_dict() for item in items]
        else:
            items_data = []
            for item in items:
                summary = {
                    "id": item.id,
                    "title": item.title,
                    "source_path": item.source_path,
                    "source_type": item.source_type.value if hasattr(item.source_type, 'value') else str(item.source_type),
                    "created_at": item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at),
                    "updated_at": item.updated_at.isoformat() if hasattr(item.updated_at, 'isoformat') else str(item.updated_at),
                    "categories": [{"id": c.id, "name": c.name} for c in item.categories] if item.categories else [],
                    "tags": [{"id": t.id, "name": t.name} for t in item.tags] if item.tags else [],
                }
                if hasattr(item, 'content') and item.content:
                    content_preview = item.content[:200]
                    if len(item.content) > 200:
                        content_preview += "..."
                    summary["content_preview"] = content_preview
                items_data.append(summary)

        return _format_success_response(
            f"Retrieved {len(items_data)} knowledge items",
            {
                "items": items_data,
                "count": len(items_data),
                "limit": limit,
                "offset": offset,
                "include_content": include_content,
                "filters": {
                    "category": category if category else None,
                    "tag": tag if tag else None,
                },
            },
        )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {
            "status": "not_implemented",
            "message": str(e),
            "items": [],
            "count": 0,
            "limit": limit,
            "offset": offset,
        }
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"category": category, "tag": tag})
    except Exception as e:
        logger.error(f"Unexpected error listing knowledge items: {e}")
        return _format_error_response(e, {"category": category, "tag": tag})


@YA_MCPServer_Tool(
    name="update_knowledge_item",
    title="Update Knowledge Item",
    description="更新指定的知识条目",
)
def update_knowledge_item(
    item_id: str,
    title: str = "",
    content: str = "",
    categories: str = "",
    tags: str = "",
) -> Dict[str, Any]:
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
        if not item_id or not item_id.strip():
            return _format_error_response(
                ValueError("item_id cannot be empty"),
                {"item_id": item_id},
            )

        logger.info(f"Updating knowledge item: {item_id}")

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
                {"item_id": item_id},
            )

        from setup import get_core
        core = get_core()
        result = core.update_knowledge_item(item_id.strip(), updates)

        if result:
            return _format_success_response(
                f"Successfully updated knowledge item {item_id}",
                {"item_id": item_id, "updated_fields": list(updates.keys())},
            )
        else:
            return _format_error_response(
                ValueError(f"Knowledge item not found: {item_id}"),
                {"item_id": item_id},
            )

    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"item_id": item_id})
    except Exception as e:
        logger.error(f"Unexpected error updating knowledge item: {e}")
        return _format_error_response(e, {"item_id": item_id})


@YA_MCPServer_Tool(
    name="delete_knowledge_item",
    title="Delete Knowledge Item",
    description="删除指定的知识条目",
)
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
        if not item_id or not item_id.strip():
            return _format_error_response(
                ValueError("item_id cannot be empty"),
                {"item_id": item_id},
            )

        logger.info(f"Deleting knowledge item: {item_id}")

        from setup import get_core
        core = get_core()
        result = core.delete_knowledge_item(item_id.strip())

        if result:
            return _format_success_response(
                f"Successfully deleted knowledge item {item_id}",
                {"item_id": item_id},
            )
        else:
            return _format_error_response(
                ValueError(f"Knowledge item not found: {item_id}"),
                {"item_id": item_id},
            )

    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"item_id": item_id})
    except Exception as e:
        logger.error(f"Unexpected error deleting knowledge item: {e}")
        return _format_error_response(e, {"item_id": item_id})

"""知识组织工具 - 通过分类、标记和关系分析来组织知识条目"""

from typing import Dict, Any
from tools import YA_MCPServer_Tool
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("tools.knowledge_organize")


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "success", "message": message, **data}


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "error", "error_type": type(error).__name__, "message": str(error), "context": context}


@YA_MCPServer_Tool(
    name="organize_knowledge",
    title="Organize Knowledge",
    description="通过分类、标记和查找关系来组织知识条目",
)
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
    from setup import get_core
    from core.exceptions import KnowledgeAgentError

    try:
        if not item_id or not item_id.strip():
            return _format_error_response(
                ValueError("item_id cannot be empty"),
                {"item_id": item_id},
            )

        logger.info(f"Organizing knowledge item: {item_id}")

        core = get_core()
        item = core.get_knowledge_item(item_id.strip())

        if not item:
            return _format_error_response(
                ValueError(f"Knowledge item not found: {item_id}"),
                {"item_id": item_id},
            )

        # 已组织且未要求强制重新处理时直接返回
        if not force_reprocess and item.categories and item.tags:
            logger.info(f"Item {item_id} already organized, skipping")
            return _format_success_response(
                f"Item {item_id} is already organized (use force_reprocess=true to reprocess)",
                {
                    "item_id": item_id,
                    "categories": [
                        {"id": c.id, "name": c.name, "confidence": c.confidence}
                        for c in item.categories
                    ],
                    "tags": [{"id": t.id, "name": t.name} for t in item.tags],
                    "relationships": [],
                    "reprocessed": False,
                },
            )

        result = core.organize_knowledge(item)

        return _format_success_response(
            f"Successfully organized knowledge item {item_id}",
            {
                "item_id": result["item_id"],
                "categories": result["categories"],
                "tags": result["tags"],
                "relationships": result["relationships"],
                "reprocessed": force_reprocess,
            },
        )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {
            "status": "not_implemented",
            "message": str(e),
            "item_id": item_id,
            "categories": [],
            "tags": [],
            "relationships": [],
        }
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"item_id": item_id})
    except Exception as e:
        logger.error(f"Unexpected error organizing knowledge: {e}")
        return _format_error_response(e, {"item_id": item_id})

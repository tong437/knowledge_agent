"""
知识搜索工具模块。

提供知识库搜索和搜索建议功能的 MCP 工具。
"""

from typing import Dict, Any

from tools import YA_MCPServer_Tool
from modules.YA_Common.utils.logger import get_logger
from core.exceptions import KnowledgeAgentError

logger = get_logger("tools.knowledge_search")


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "success", "message": message, **data}


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context,
    }


@YA_MCPServer_Tool(
    name="search_knowledge",
    title="Search Knowledge",
    description="使用自然语言或关键词搜索知识条目",
)
def search_knowledge(
    query: str, max_results: int = 10, min_relevance: float = 0.1
) -> Dict[str, Any]:
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
        if not query or not query.strip():
            return _format_error_response(
                ValueError("query cannot be empty"), {"query": query}
            )

        if max_results < 1 or max_results > 100:
            return _format_error_response(
                ValueError("max_results must be between 1 and 100"),
                {"query": query, "max_results": max_results},
            )

        if min_relevance < 0.0 or min_relevance > 1.0:
            return _format_error_response(
                ValueError("min_relevance must be between 0.0 and 1.0"),
                {"query": query, "min_relevance": min_relevance},
            )

        logger.info(f"Searching knowledge: {query}")

        from setup import get_core

        core = get_core()
        search_results = core.search_knowledge(
            query.strip(), max_results=max_results, min_relevance=min_relevance
        )

        return _format_success_response(
            f"Found {len(search_results.get('results', []))} results for query: {query}",
            {
                "query": query,
                "results": search_results.get("results", []),
                "total_found": search_results.get("total_found", 0),
                "max_results": max_results,
                "min_relevance": min_relevance,
            },
        )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {
            "status": "not_implemented",
            "message": str(e),
            "query": query,
            "results": [],
            "total_found": 0,
        }
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"query": query})
    except Exception as e:
        logger.error(f"Unexpected error searching knowledge: {e}")
        return _format_error_response(e, {"query": query})


@YA_MCPServer_Tool(
    name="suggest_search",
    title="Suggest Search",
    description="根据部分输入提供搜索建议",
)
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
        if not partial_query or not partial_query.strip():
            return _format_error_response(
                ValueError("partial_query cannot be empty"),
                {"partial_query": partial_query},
            )

        logger.info(f"Getting search suggestions for: {partial_query}")

        from setup import get_core

        core = get_core()
        # TODO: 应通过 knowledge_core 的公开接口调用，待核心层添加 suggest() 方法后修复
        suggestions = core._search_engine.suggest(partial_query.strip())

        return _format_success_response(
            f"Found {len(suggestions)} suggestions for '{partial_query}'",
            {
                "partial_query": partial_query,
                "suggestions": suggestions,
                "count": len(suggestions),
            },
        )

    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"partial_query": partial_query})
    except Exception as e:
        logger.error(f"Unexpected error getting search suggestions: {e}")
        return _format_error_response(e, {"partial_query": partial_query})

"""知识库系统管理工具 - 导入导出、统计、性能指标、错误摘要"""
import json
from typing import Dict, Any
from pathlib import Path
from tools import YA_MCPServer_Tool
from modules.YA_Common.utils.logger import get_logger
from core.exceptions import KnowledgeAgentError

logger = get_logger("tools.knowledge_system")


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
    name="export_knowledge",
    title="Export Knowledge",
    description="以指定格式导出所有知识数据",
)
def export_knowledge(
    format: str = "json", include_content: bool = True
) -> Dict[str, Any]:
    try:
        if format.lower() not in ["json"]:
            return _format_error_response(
                ValueError(
                    f"Unsupported export format: {format}. Currently only 'json' is supported"
                ),
                {"format": format},
            )

        logger.info(f"Exporting knowledge data in {format} format")

        from setup import get_core

        core = get_core()
        export_data = core.export_data(format=format.lower())

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
                "relationship_count": len(export_data.get("relationships", [])),
            },
        )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {
            "status": "not_implemented",
            "message": str(e),
            "format": format,
            "include_content": include_content,
        }
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"format": format})
    except Exception as e:
        logger.error(f"Unexpected error exporting knowledge: {e}")
        return _format_error_response(e, {"format": format})


@YA_MCPServer_Tool(
    name="import_knowledge",
    title="Import Knowledge",
    description="从文件导入知识数据",
)
def import_knowledge(
    data_path: str, format: str = "json", merge_strategy: str = "skip_existing"
) -> Dict[str, Any]:
    try:
        if not data_path or not data_path.strip():
            return _format_error_response(
                ValueError("data_path cannot be empty"),
                {"data_path": data_path},
            )

        if format.lower() not in ["json"]:
            return _format_error_response(
                ValueError(
                    f"Unsupported import format: {format}. Currently only 'json' is supported"
                ),
                {"format": format, "data_path": data_path},
            )

        valid_strategies = ["skip_existing", "overwrite", "merge"]
        if merge_strategy.lower() not in valid_strategies:
            return _format_error_response(
                ValueError(
                    f"Invalid merge_strategy: {merge_strategy}. Must be one of: {', '.join(valid_strategies)}"
                ),
                {"merge_strategy": merge_strategy, "data_path": data_path},
            )

        logger.info(f"Importing knowledge data from {data_path}")

        file_path = Path(data_path.strip())
        if not file_path.exists():
            return _format_error_response(
                FileNotFoundError(f"Data file not found: {data_path}"),
                {"data_path": data_path},
            )

        with open(file_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)

        from setup import get_core

        core = get_core()
        success = core.import_data(import_data)

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
                    "imported_relationships": len(
                        import_data.get("relationships", [])
                    ),
                },
            )
        else:
            return _format_error_response(
                Exception("Import failed"), {"data_path": data_path}
            )

    except NotImplementedError as e:
        logger.warning(f"Feature not yet implemented: {e}")
        return {
            "status": "not_implemented",
            "message": str(e),
            "data_path": data_path,
            "format": format,
            "merge_strategy": merge_strategy,
        }
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {"data_path": data_path})
    except Exception as e:
        logger.error(f"Unexpected error importing knowledge: {e}")
        return _format_error_response(e, {"data_path": data_path})


@YA_MCPServer_Tool(
    name="get_statistics",
    title="Get Statistics",
    description="获取知识库统计信息",
)
def get_statistics() -> Dict[str, Any]:
    try:
        logger.info("Retrieving knowledge base statistics")
        from setup import get_core

        core = get_core()
        stats = core.get_statistics()
        return _format_success_response(
            "Successfully retrieved knowledge base statistics",
            {"statistics": stats},
        )
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {})
    except Exception as e:
        logger.error(f"Unexpected error retrieving statistics: {e}")
        return _format_error_response(e, {})


@YA_MCPServer_Tool(
    name="get_performance_metrics",
    title="Get Performance Metrics",
    description="获取所有操作的性能指标",
)
def get_performance_metrics() -> Dict[str, Any]:
    try:
        logger.info("Retrieving performance metrics")
        from setup import get_core

        core = get_core()
        metrics = core.get_performance_metrics()
        return _format_success_response(
            "Successfully retrieved performance metrics",
            {"metrics": metrics},
        )
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {})
    except Exception as e:
        logger.error(f"Unexpected error retrieving performance metrics: {e}")
        return _format_error_response(e, {})


@YA_MCPServer_Tool(
    name="get_error_summary",
    title="Get Error Summary",
    description="获取错误摘要和最近的错误信息",
)
def get_error_summary() -> Dict[str, Any]:
    try:
        logger.info("Retrieving error summary")
        from setup import get_core

        core = get_core()
        error_summary = core.get_error_summary()
        return _format_success_response(
            "Successfully retrieved error summary",
            {"error_summary": error_summary},
        )
    except KnowledgeAgentError as e:
        logger.error(f"Knowledge agent error: {e}")
        return _format_error_response(e, {})
    except Exception as e:
        logger.error(f"Unexpected error retrieving error summary: {e}")
        return _format_error_response(e, {})

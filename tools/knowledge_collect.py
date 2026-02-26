"""知识收集相关的 MCP 工具"""

from typing import Dict, Any
from tools import YA_MCPServer_Tool
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("tools.knowledge_collect")

# 已实现处理器的数据源类型集合
IMPLEMENTED_TYPES = {"document", "pdf", "code", "web"}


def _validate_source_type(source_type: str) -> bool:
    """验证数据源类型是否受支持"""
    valid_types = ["auto", "document", "pdf", "web", "code", "image"]
    return source_type.lower() in valid_types


def _format_success_response(message: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """格式化标准结构的成功响应"""
    return {
        "status": "success",
        "message": message,
        **data
    }


def _format_error_response(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """格式化标准结构的错误响应"""
    return {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context
    }


@YA_MCPServer_Tool(
    name="collect_knowledge",
    title="Collect Knowledge",
    description="从数据源收集知识。支持文档、PDF、网页、代码文件等多种数据源类型。",
)
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
    from setup import get_core
    from core.models import DataSource, SourceType
    from core.exceptions import KnowledgeAgentError
    from core.source_type_detector import SourceTypeDetector
    from core.security_validator import SecurityValidator
    from core.config_manager import get_config_manager

    try:
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

        if source_type_lower == "auto":
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

        source = DataSource(
            path=source_path.strip(),
            source_type=detected_type,
            metadata={}
        )

        core = get_core()
        item = core.collect_knowledge(source)

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


@YA_MCPServer_Tool(
    name="batch_collect_knowledge",
    title="Batch Collect Knowledge",
    description="批量收集目录中的知识。扫描指定目录中匹配模式的文件，批量处理并收集知识条目。",
)
def batch_collect_knowledge(
    directory_path: str, file_pattern: str = "*", recursive: bool = False
) -> Dict[str, Any]:
    """
    批量收集目录中的知识。

    扫描指定目录中匹配模式的文件，批量处理并收集知识条目。

    Args:
        directory_path: 目标目录路径
        file_pattern: 文件匹配模式，支持逗号分隔的多个模式（默认 "*"）
        recursive: 是否递归扫描子目录

    Returns:
        包含批量收集结果摘要的字典
    """
    from setup import get_core
    from core.exceptions import KnowledgeAgentError

    try:
        if not directory_path or not directory_path.strip():
            return _format_error_response(
                ValueError("directory_path cannot be empty"),
                {"directory_path": directory_path}
            )

        logger.info(
            f"Batch collecting knowledge from: {directory_path} "
            f"(pattern: {file_pattern}, recursive: {recursive})"
        )

        core = get_core()
        result = core.batch_collect_knowledge(
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

"""应用初始化模块 - 创建和管理 KnowledgeAgentCore 单例"""
import atexit
from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config

logger = get_logger("setup")

_core = None


def get_core():
    """获取 KnowledgeAgentCore 单例"""
    if _core is None:
        raise RuntimeError("KnowledgeAgentCore 未初始化，请确保 setup() 已被调用")
    return _core


def setup():
    """初始化 KnowledgeAgentCore 并注册关闭回调"""
    global _core
    try:
        knowledge_config = {
            "storage": {
                "type": get_config("knowledge.storage.type", "sqlite"),
                "path": get_config("knowledge.storage.path", "knowledge_agent.db"),
            },
            "search": {
                "index_dir": get_config("knowledge.search.index_dir", "search_index"),
                "min_relevance": get_config("knowledge.search.min_relevance", 0.1),
                "max_results": get_config("knowledge.search.max_results", 50),
            },
            "security": {
                "allowed_paths": get_config("knowledge.security.allowed_paths", []),
                "blocked_extensions": get_config(
                    "knowledge.security.blocked_extensions",
                    [".exe", ".dll", ".so"],
                ),
            },
        }

        from core.knowledge_agent_core import KnowledgeAgentCore
        _core = KnowledgeAgentCore(config=knowledge_config)

        atexit.register(_shutdown)
        logger.info("KnowledgeAgentCore 初始化完成")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise


def _shutdown():
    """应用退出时清理资源"""
    global _core
    if _core is not None:
        try:
            if hasattr(_core, "shutdown"):
                _core.shutdown()
            logger.info("KnowledgeAgentCore 已关闭")
        except Exception as e:
            logger.warning(f"关闭时发生错误: {e}")
        finally:
            _core = None

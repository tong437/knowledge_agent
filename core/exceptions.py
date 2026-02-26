"""
知识管理智能体自定义异常模块。

定义异常类层级，用于在各业务模块中抛出和捕获特定类型的错误。
"""


class KnowledgeAgentError(Exception):
    """知识管理智能体基础异常类。"""
    pass


class ProcessingError(KnowledgeAgentError):
    """数据源处理过程中的异常。"""
    pass


class StorageError(KnowledgeAgentError):
    """存储操作过程中的异常。"""
    pass


class SearchError(KnowledgeAgentError):
    """搜索操作过程中的异常。"""
    pass


class ValidationError(KnowledgeAgentError):
    """数据验证过程中的异常。"""
    pass


class ConfigurationError(KnowledgeAgentError):
    """配置相关的异常。"""
    pass

"""
数据源处理器接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.models import DataSource, KnowledgeItem


class DataSourceProcessor(ABC):
    """
    数据源处理器的抽象基类。

    定义所有数据源处理器必须实现的接口，
    用于从各种来源收集知识。
    """

    @abstractmethod
    def process(self, source: DataSource) -> KnowledgeItem:
        """
        处理数据源并生成知识条目。

        Args:
            source: 待处理的数据源

        Returns:
            KnowledgeItem: 生成的知识条目

        Raises:
            ProcessingError: 数据源无法处理时抛出
        """
        pass

    @abstractmethod
    def validate(self, source: DataSource) -> bool:
        """
        验证数据源是否可以被处理。

        Args:
            source: 待验证的数据源

        Returns:
            bool: 可处理返回 True，否则返回 False
        """
        pass

    @abstractmethod
    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        从数据源中提取元数据。

        Args:
            source: 待提取元数据的数据源

        Returns:
            Dict[str, Any]: 元数据字典
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> list:
        """
        获取此处理器支持的数据源类型列表。

        Returns:
            list: 支持的 SourceType 值列表
        """
        pass

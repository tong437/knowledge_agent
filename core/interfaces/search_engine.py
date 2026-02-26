"""
搜索引擎接口。
"""

from abc import ABC, abstractmethod
from typing import List
from core.models import SearchResults, SearchOptions, KnowledgeItem


class SearchEngine(ABC):
    """
    知识搜索引擎的抽象基类。

    定义语义搜索、自然语言查询和搜索结果处理的接口。
    """

    @abstractmethod
    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        执行搜索查询并返回结果。

        Args:
            query: 搜索查询字符串
            options: 搜索配置选项

        Returns:
            SearchResults: 带元数据的结构化搜索结果
        """
        pass

    @abstractmethod
    def suggest(self, partial_query: str) -> List[str]:
        """
        根据部分输入提供查询建议。

        Args:
            partial_query: 部分查询字符串

        Returns:
            List[str]: 建议的完整查询列表
        """
        pass

    @abstractmethod
    def update_index(self, item: KnowledgeItem) -> None:
        """
        使用新的或修改的知识条目更新搜索索引。

        Args:
            item: 待索引的知识条目
        """
        pass

    @abstractmethod
    def remove_from_index(self, item_id: str) -> None:
        """
        从搜索索引中移除知识条目。

        Args:
            item_id: 待移除条目的 ID
        """
        pass

    @abstractmethod
    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        从头重建整个搜索索引。

        Args:
            items: 所有待索引的知识条目列表
        """
        pass

    @abstractmethod
    def get_similar_items(self, item: KnowledgeItem, limit: int = 10) -> List[KnowledgeItem]:
        """
        查找与给定知识条目相似的条目。

        Args:
            item: 参考知识条目
            limit: 返回的最大相似条目数

        Returns:
            List[KnowledgeItem]: 相似条目列表
        """
        pass

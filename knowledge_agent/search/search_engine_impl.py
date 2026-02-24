"""
搜索引擎核心实现模块。
"""

import time
from typing import List, Optional
from ..interfaces import SearchEngine
from ..models import (
    KnowledgeItem,
    SearchResult,
    SearchResults,
    SearchOptions
)
from .search_index_manager import SearchIndexManager
from .semantic_searcher import SemanticSearcher
from .result_processor import ResultProcessor


class SearchEngineImpl(SearchEngine):
    """
    完整的搜索引擎实现，结合关键词搜索和语义搜索。

    集成 Whoosh 全文索引和 TF-IDF 语义搜索，
    提供全面的搜索能力。
    """

    def __init__(self, index_dir: str):
        """
        初始化搜索引擎。

        Args:
            index_dir: 搜索索引的存储目录路径
        """
        self.index_manager = SearchIndexManager(index_dir)
        self.semantic_searcher = SemanticSearcher()
        self.result_processor = ResultProcessor()

    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        执行搜索查询并返回结果。

        结合关键词搜索（通过 Whoosh）和语义搜索（通过 TF-IDF）
        以获得全面的搜索结果。

        Args:
            query: 搜索查询字符串
            options: 搜索配置选项

        Returns:
            SearchResults: 包含元数据的结构化搜索结果
        """
        start_time = time.time()

        # 执行关键词搜索
        keyword_results = self._keyword_search(query, options.max_results * 2)

        # 如果模型已拟合，则执行语义搜索
        semantic_results = []
        if self.semantic_searcher.is_fitted:
            semantic_results = self._semantic_search(query, options.max_results * 2)

        # 合并搜索结果
        if keyword_results and semantic_results:
            merged_results = self.result_processor.merge_results(
                keyword_results,
                semantic_results,
                keyword_weight=0.6,
                semantic_weight=0.4
            )
        elif keyword_results:
            merged_results = keyword_results
        elif semantic_results:
            merged_results = semantic_results
        else:
            merged_results = []

        # 应用搜索选项（过滤、排序、分组）
        search_results = self.result_processor.apply_options(merged_results, options)

        # 设置查询字符串和耗时
        search_results.query = query
        search_results.search_time_ms = (time.time() - start_time) * 1000

        return search_results

    def _keyword_search(
        self,
        query: str,
        limit: int
    ) -> List[SearchResult]:
        """
        使用 Whoosh 执行基于关键词的搜索。

        Args:
            query: 搜索查询字符串
            limit: 最大结果数量

        Returns:
            搜索结果列表
        """
        try:
            # 搜索索引
            whoosh_results = self.index_manager.search(query, limit=limit)

            # 转换为 SearchResult 对象
            results = []
            for hit in whoosh_results:
                # 从存储字段重建知识条目
                item = self._reconstruct_item_from_hit(hit)
                if item:
                    # 从 Whoosh 获取评分（已包含在 hit 字典中）
                    # 将评分归一化到 0-1 范围（Whoosh 评分范围不固定）
                    raw_score = hit.get('score', 0.0)
                    relevance_score = min(raw_score / 10.0, 1.0) if raw_score > 0 else 0.5

                    result = SearchResult(
                        item=item,
                        relevance_score=relevance_score,
                        matched_fields=['title', 'content'],
                        highlights=[]
                    )
                    results.append(result)

            return results
        except Exception:
            return []

    def _semantic_search(
        self,
        query: str,
        limit: int
    ) -> List[SearchResult]:
        """
        使用 TF-IDF 执行语义搜索。

        Args:
            query: 搜索查询字符串
            limit: 最大结果数量

        Returns:
            搜索结果列表
        """
        try:
            # 使用语义搜索器进行搜索
            semantic_results = self.semantic_searcher.search(
                query,
                top_k=limit,
                min_similarity=0.05  # 降低阈值以获得更多结果
            )

            # 转换为 SearchResult 对象
            results = []
            for item, similarity in semantic_results:
                result = SearchResult(
                    item=item,
                    relevance_score=similarity,
                    matched_fields=['semantic'],
                    highlights=[]
                )
                results.append(result)

            return results
        except Exception:
            return []

    def _reconstruct_item_from_hit(self, hit: dict) -> Optional[KnowledgeItem]:
        """
        从 Whoosh 搜索命中结果重建 KnowledgeItem。

        注意：这是一个简化的重建过程。在实际系统中，
        应该从存储层获取完整的条目。

        Args:
            hit: 包含 Whoosh 存储字段的字典

        Returns:
            KnowledgeItem 或重建失败时返回 None
        """
        try:
            from ..models import SourceType, Category, Tag
            from datetime import datetime

            # 解析分类
            categories = []
            if hit.get('categories'):
                cat_names = hit['categories'].split(',')
                categories = [
                    Category(id=name, name=name, description="", parent_id=None, confidence=1.0)
                    for name in cat_names if name
                ]

            # 解析标签
            tags = []
            if hit.get('tags'):
                tag_names = hit['tags'].split(',')
                tags = [
                    Tag(id=name, name=name, color="#000000", usage_count=1)
                    for name in tag_names if name
                ]

            # 创建知识条目
            item = KnowledgeItem(
                id=hit['id'],
                title=hit['title'],
                content=hit['content'],
                source_type=SourceType(hit['source_type']),
                source_path=hit['source_path'],
                categories=categories,
                tags=tags,
                metadata={},
                created_at=hit.get('created_at', datetime.now()),
                updated_at=hit.get('updated_at', datetime.now()),
                embedding=None
            )

            return item
        except Exception:
            return None

    def suggest(self, partial_query: str, max_suggestions: int = 10) -> List[str]:
        """
        根据部分输入提供查询建议。

        结合 Whoosh 索引的前缀匹配和语义搜索器的词项分析，
        返回去重后的建议列表。

        Args:
            partial_query: 部分查询字符串
            max_suggestions: 最大建议数量，默认 10

        Returns:
            List[str]: 建议的完整查询列表
        """
        if not partial_query or not partial_query.strip():
            return []

        partial_query = partial_query.strip().lower()
        suggestions = []

        # 从 Whoosh 索引中获取前缀匹配的词项
        try:
            with self.index_manager.ix.searcher() as searcher:
                reader = searcher.reader()
                # 在 title 和 content 字段中查找前缀匹配的词项
                for field_name in ["title", "content"]:
                    try:
                        for term in reader.field_terms(field_name):
                            if isinstance(term, bytes):
                                term = term.decode("utf-8", errors="ignore")
                            if term.lower().startswith(partial_query) and len(term) > 1:
                                suggestions.append(term)
                    except Exception:
                        continue
        except Exception:
            pass

        # 从语义搜索器中获取相关词项
        if self.semantic_searcher.is_fitted:
            try:
                semantic_terms = self.semantic_searcher.get_query_terms(
                    partial_query, top_n=max_suggestions
                )
                suggestions.extend(semantic_terms)
            except Exception:
                pass

        # 去重并保持顺序
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            s_lower = s.lower()
            if s_lower not in seen:
                seen.add(s_lower)
                unique_suggestions.append(s)

        return unique_suggestions[:max_suggestions]


    def update_index(self, item: KnowledgeItem) -> None:
        """
        使用新的或修改后的知识条目更新搜索索引。

        Args:
            item: 需要索引的知识条目
        """
        # 更新关键词索引
        self.index_manager.update_item(item)

        # 更新语义模型
        self.semantic_searcher.update_item(item)

    def remove_from_index(self, item_id: str) -> None:
        """
        从搜索索引中移除知识条目。

        Args:
            item_id: 要移除的条目 ID
        """
        # 从关键词索引中移除
        self.index_manager.remove_item(item_id)

        # 从语义模型中移除
        self.semantic_searcher.remove_item(item_id)

    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        从头重建整个搜索索引。

        Args:
            items: 需要索引的所有知识条目列表
        """
        # 重建关键词索引
        self.index_manager.rebuild_index(items)

        # 重建语义模型
        self.semantic_searcher.fit(items)

    def get_similar_items(
        self,
        item: KnowledgeItem,
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """
        查找与给定知识条目相似的条目。

        Args:
            item: 参考知识条目
            limit: 返回的最大相似条目数量

        Returns:
            List[KnowledgeItem]: 相似条目列表
        """
        if not self.semantic_searcher.is_fitted:
            return []

        # 使用语义搜索查找相似条目
        similar_results = self.semantic_searcher.find_similar_items(
            item,
            top_k=limit,
            min_similarity=0.05  # 降低阈值以获得更多相似结果
        )

        return [item for item, _ in similar_results]

    def close(self) -> None:
        """关闭搜索引擎并释放资源。"""
        self.index_manager.close()

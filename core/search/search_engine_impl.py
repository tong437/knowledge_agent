"""
搜索引擎核心实现模块。
"""

import time
from typing import List, Optional

from modules.YA_Common.utils.logger import get_logger
from core.interfaces import SearchEngine
from core.models import (
    KnowledgeItem,
    SearchResult,
    SearchResults,
    SearchOptions,
    SourceType,
    Category,
    Tag,
)
from core.models.search_result import MatchedChunk
from core.models.knowledge_chunk import KnowledgeChunk
from .search_index_manager import SearchIndexManager
from .semantic_searcher import SemanticSearcher
from .result_processor import ResultProcessor

logger = get_logger(__name__)

# 单个知识项在分块搜索中返回的最大匹配分块数
MAX_MATCHED_CHUNKS_PER_ITEM = 10
# 单个知识项在分块搜索中返回的最大上下文分块数
MAX_CONTEXT_CHUNKS_PER_ITEM = 6


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
        self.storage_manager = None

    def set_storage_manager(self, storage_manager) -> None:
        """注入存储管理器，用于分块搜索时获取完整条目和上下文分块。"""
        self.storage_manager = storage_manager

    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        执行搜索查询并返回结果。

        优先使用分块搜索（两阶段），分块索引不可用时降级为文档级搜索。

        Args:
            query: 搜索查询字符串
            options: 搜索配置选项

        Returns:
            SearchResults: 包含元数据的结构化搜索结果
        """
        start_time = time.time()

        # 优先尝试分块搜索
        if self.index_manager.has_chunk_index() and self.storage_manager is not None:
            try:
                search_results = self._chunk_search(query, options)
                search_results.search_time_ms = (time.time() - start_time) * 1000
                return search_results
            except Exception:
                logger.warning("分块搜索失败，降级为文档级搜索")

        # 降级为文档级搜索
        search_results = self._item_search(query, options)
        search_results.search_time_ms = (time.time() - start_time) * 1000
        return search_results

    def _item_search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        文档级搜索，结合关键词搜索和语义搜索。

        Args:
            query: 搜索查询字符串
            options: 搜索配置选项

        Returns:
            SearchResults: 包含元数据的结构化搜索结果
        """
        keyword_results = self._keyword_search(query, options.max_results * 2)

        semantic_results = []
        if self.semantic_searcher.is_fitted:
            semantic_results = self._semantic_search(query, options.max_results * 2)

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

        search_results = self.result_processor.apply_options(merged_results, options)
        search_results.query = query
        return search_results

    def _chunk_search(self, query: str, options: SearchOptions) -> SearchResults:
        """
        两阶段分块搜索。

        阶段1：在分块索引上执行关键词搜索和语义搜索，合并分块结果。
        阶段2：按 item_id 聚合，获取完整条目和上下文分块，构建搜索结果。

        Args:
            query: 搜索查询字符串
            options: 搜索配置选项

        Returns:
            SearchResults: 包含 matched_chunks 和 context_chunks 的搜索结果
        """
        # 阶段1：分块级搜索
        keyword_chunk_hits = self.index_manager.search_chunks(
            query, limit=options.max_results * 3
        )

        semantic_chunk_hits = []
        if self.semantic_searcher.is_chunk_fitted:
            semantic_chunk_hits = self.semantic_searcher.search_chunks(
                query, top_k=options.max_results * 3
            )

        # 合并分块结果（按 chunk_id 去重，取最高分）
        chunk_scores = {}
        for hit in keyword_chunk_hits:
            cid = hit['chunk_id']
            score = min(hit.get('score', 0) / 10.0, 1.0)
            if cid not in chunk_scores or score > chunk_scores[cid][0]:
                chunk_scores[cid] = (score, hit)

        for chunk, sim in semantic_chunk_hits:
            cid = chunk.id
            if cid not in chunk_scores or sim > chunk_scores[cid][0]:
                chunk_scores[cid] = (sim, {
                    'chunk_id': chunk.id,
                    'item_id': chunk.item_id,
                    'chunk_index': chunk.chunk_index,
                    'heading': chunk.heading,
                    'content': chunk.content,
                    'start_position': chunk.start_position,
                    'end_position': chunk.end_position,
                })

        # 阶段2：按 item_id 聚合
        item_chunks = {}
        for cid, (score, info) in chunk_scores.items():
            iid = info['item_id'] if isinstance(info, dict) else info.item_id
            if iid not in item_chunks:
                item_chunks[iid] = []
            item_chunks[iid].append((score, info))

        results = []
        for item_id, scored_chunks in item_chunks.items():
            item = self.storage_manager.get_knowledge_item(item_id)
            if not item:
                continue

            best_score = max(s for s, _ in scored_chunks)

            # 构建 matched_chunks，按分数排序后只取前 N 个
            matched_chunks = []
            for score, info in sorted(scored_chunks, key=lambda x: -x[0]):
                if len(matched_chunks) >= MAX_MATCHED_CHUNKS_PER_ITEM:
                    break
                mc = MatchedChunk(
                    chunk_id=info['chunk_id'] if isinstance(info, dict) else info.id,
                    content=info['content'] if isinstance(info, dict) else info.content,
                    heading=info.get('heading', '') if isinstance(info, dict) else getattr(info, 'heading', ''),
                    chunk_index=int(info.get('chunk_index', 0)) if isinstance(info, dict) else info.chunk_index,
                    start_position=int(info.get('start_position', 0)) if isinstance(info, dict) else info.start_position,
                    end_position=int(info.get('end_position', 0)) if isinstance(info, dict) else info.end_position,
                    score=score
                )
                matched_chunks.append(mc)

            # 加载上下文分块（匹配分块的相邻分块），限制总数
            context_chunks = []
            matched_chunk_ids = {m.chunk_id for m in matched_chunks}
            context_chunk_ids = set()
            for mc in matched_chunks:
                if len(context_chunks) >= MAX_CONTEXT_CHUNKS_PER_ITEM:
                    break
                adjacent = self.storage_manager.get_adjacent_chunks(item_id, mc.chunk_index)
                for adj in adjacent:
                    if len(context_chunks) >= MAX_CONTEXT_CHUNKS_PER_ITEM:
                        break
                    if adj.id not in matched_chunk_ids and adj.id not in context_chunk_ids:
                        context_chunk_ids.add(adj.id)
                        context_chunks.append(MatchedChunk(
                            chunk_id=adj.id,
                            content=adj.content,
                            heading=adj.heading,
                            chunk_index=adj.chunk_index,
                            start_position=adj.start_position,
                            end_position=adj.end_position,
                            score=0.0
                        ))

            result = SearchResult(
                item=item,
                relevance_score=best_score,
                matched_fields=['chunk_content'],
                highlights=[],
                matched_chunks=matched_chunks,
                context_chunks=context_chunks
            )
            results.append(result)

        search_results = self.result_processor.apply_options(results, options)
        search_results.query = query
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
            whoosh_results = self.index_manager.search(query, limit=limit)

            results = []
            for hit in whoosh_results:
                item = self._reconstruct_item_from_hit(hit)
                if item:
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
            semantic_results = self.semantic_searcher.search(
                query,
                top_k=limit,
                min_similarity=0.05
            )

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

        Args:
            hit: 包含 Whoosh 存储字段的字典

        Returns:
            KnowledgeItem 或重建失败时返回 None
        """
        try:
            from datetime import datetime

            categories = []
            if hit.get('categories'):
                cat_names = hit['categories'].split(',')
                categories = [
                    Category(id=name, name=name, description="", parent_id=None, confidence=1.0)
                    for name in cat_names if name
                ]

            tags = []
            if hit.get('tags'):
                tag_names = hit['tags'].split(',')
                tags = [
                    Tag(id=name, name=name, color="#000000", usage_count=1)
                    for name in tag_names if name
                ]

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
            建议的完整查询列表
        """
        if not partial_query or not partial_query.strip():
            return []

        partial_query = partial_query.strip().lower()
        suggestions = []

        # 从 Whoosh 索引中获取前缀匹配的词项
        try:
            with self.index_manager.ix.searcher() as searcher:
                reader = searcher.reader()
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
        self.index_manager.update_item(item)
        self.semantic_searcher.update_item(item)

    def remove_from_index(self, item_id: str) -> None:
        """
        从搜索索引中移除知识条目。

        Args:
            item_id: 要移除的条目 ID
        """
        self.index_manager.remove_item(item_id)
        self.semantic_searcher.remove_item(item_id)

    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        从头重建整个搜索索引。

        Args:
            items: 需要索引的所有知识条目列表
        """
        self.index_manager.rebuild_index(items)
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
            相似条目列表
        """
        if not self.semantic_searcher.is_fitted:
            return []

        similar_results = self.semantic_searcher.find_similar_items(
            item,
            top_k=limit,
            min_similarity=0.05
        )

        return [item for item, _ in similar_results]

    def update_chunk_index(self, item_id: str, chunks: List[KnowledgeChunk]) -> None:
        """
        更新指定条目的分块索引。

        先移除旧分块，再添加新分块，同时更新语义搜索器。

        Args:
            item_id: 知识条目 ID
            chunks: 新的分块列表
        """
        self.index_manager.remove_chunks_for_item(item_id)
        self.index_manager.add_chunks(chunks)
        self.semantic_searcher.update_chunks_for_item(item_id, chunks)

    def remove_chunks_from_index(self, item_id: str) -> None:
        """
        从分块索引中移除指定条目的所有分块。

        Args:
            item_id: 知识条目 ID
        """
        self.index_manager.remove_chunks_for_item(item_id)
        self.semantic_searcher.remove_chunks_for_item(item_id)

    def rebuild_chunk_index(self, chunks: List[KnowledgeChunk]) -> None:
        """
        从头重建整个分块索引。

        Args:
            chunks: 所有分块列表
        """
        self.index_manager.rebuild_chunk_index(chunks)
        self.semantic_searcher.fit_chunks(chunks)

    def close(self) -> None:
        """关闭搜索引擎并释放资源。"""
        self.index_manager.close()

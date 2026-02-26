"""
基于 Whoosh 的全文搜索索引管理模块。
"""

import os
from typing import List, Optional
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD, NUMERIC
from whoosh.qparser import MultifieldParser, QueryParser, OrGroup
from whoosh.analysis import RegexTokenizer, LowercaseFilter, CharsetFilter
from whoosh.support.charset import accent_map

from core.models import KnowledgeItem
from core.models.knowledge_chunk import KnowledgeChunk




# 尝试导入 jieba 分词库
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

class SearchIndexManager:
    """
    使用 Whoosh 管理全文搜索索引。.

    提供创建、更新和查询知识条目搜索索引的功能。
    """

    def __init__(self, index_dir: str):
        """
        初始化搜索索引管理器。

        Args:
            index_dir: 搜索索引的存储目录路径
        """
        self.index_dir = index_dir
        self.schema = self._create_schema()
        self.ix = self._get_or_create_index()
        self.chunk_index_dir = os.path.join(index_dir, "chunks")
        self.chunk_schema = self._create_chunk_schema()
        self.chunk_ix = None

    def _extract_query_terms(self, query_str: str) -> List[str]:
        """
        从查询字符串中提取搜索词项。

        策略：
        1. 保留原始查询（整体匹配）
        2. 按空格分词（支持多词查询）
        3. 使用 jieba 进行中文分词（智能识别词语边界）
        4. 对长词进行 N-gram 分词（兜底策略）

        Args:
            query_str: 原始查询字符串

        Returns:
            提取的词项列表
        """
        terms = []

        # 添加原始查询（整体匹配）
        if query_str.strip():
            terms.append(query_str.strip())

        # 按空格分词
        space_terms = query_str.split()
        terms.extend(space_terms)

        if JIEBA_AVAILABLE:
            for term in space_terms:
                if any('\u4e00' <= char <= '\u9fff' for char in term):
                    seg_list = jieba.cut(term, cut_all=False)
                    for seg in seg_list:
                        if seg.strip() and len(seg) > 0:
                            terms.append(seg)
        else:
            # jieba 不可用时降级为 N-gram 分词
            for term in space_terms:
                if any('\u4e00' <= char <= '\u9fff' for char in term):
                    term_len = len(term)
                    if term_len >= 2:
                        for i in range(term_len - 1):
                            terms.append(term[i:i+2])
                    if term_len >= 3:
                        for i in range(term_len - 2):
                            terms.append(term[i:i+3])

        # 去重并保持顺序
        seen = set()
        unique_terms = []
        for term in terms:
            if term and term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms


    def _create_schema(self) -> Schema:
        """
        创建知识条目的 Whoosh Schema。

        Returns:
            Whoosh Schema 定义
        """
        analyzer = RegexTokenizer(r"\w+") | LowercaseFilter() | CharsetFilter(accent_map)

        return Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True, field_boost=2.0, analyzer=analyzer),
            content=TEXT(stored=True, analyzer=analyzer),
            source_type=ID(stored=True),
            source_path=TEXT(stored=True),
            categories=KEYWORD(stored=True, commas=True, scorable=True, lowercase=True),
            tags=KEYWORD(stored=True, commas=True, scorable=True, lowercase=True),
            created_at=DATETIME(stored=True),
            updated_at=DATETIME(stored=True),
        )

    def _get_or_create_index(self) -> index.Index:
        """获取已有索引或创建新索引。"""
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)

        if index.exists_in(self.index_dir):
            return index.open_dir(self.index_dir)
        else:
            return index.create_in(self.index_dir, self.schema)

    def _create_chunk_schema(self) -> Schema:
        """创建分块索引的 Schema。"""
        analyzer = RegexTokenizer(r"\w+") | LowercaseFilter() | CharsetFilter(accent_map)
        return Schema(
            chunk_id=ID(stored=True, unique=True),
            item_id=ID(stored=True),
            chunk_index=NUMERIC(stored=True),
            heading=TEXT(stored=True, analyzer=analyzer),
            content=TEXT(stored=True, analyzer=analyzer),
        )

    def _get_or_create_chunk_index(self) -> index.Index:
        """获取或创建分块索引，延迟初始化。"""
        if self.chunk_ix is not None:
            return self.chunk_ix

        if not os.path.exists(self.chunk_index_dir):
            os.makedirs(self.chunk_index_dir)

        if index.exists_in(self.chunk_index_dir):
            self.chunk_ix = index.open_dir(self.chunk_index_dir)
        else:
            self.chunk_ix = index.create_in(self.chunk_index_dir, self.chunk_schema)

        return self.chunk_ix

    def add_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        """
        批量添加分块到索引。

        Args:
            chunks: 待添加的知识分块列表
        """
        ix = self._get_or_create_chunk_index()
        writer = ix.writer()
        try:
            for chunk in chunks:
                writer.add_document(
                    chunk_id=chunk.id,
                    item_id=chunk.item_id,
                    chunk_index=chunk.chunk_index,
                    heading=chunk.heading,
                    content=chunk.content,
                )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to add chunks to index: {e}")

    def remove_chunks_for_item(self, item_id: str) -> None:
        """
        删除指定条目的所有分块索引。

        Args:
            item_id: 知识条目 ID
        """
        ix = self._get_or_create_chunk_index()
        writer = ix.writer()
        try:
            writer.delete_by_term("item_id", item_id)
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to remove chunks from index: {e}")

    def search_chunks(self, query_str: str, limit: int = 50) -> List[dict]:
        """
        在分块索引上搜索。

        Args:
            query_str: 搜索查询字符串
            limit: 最大返回结果数

        Returns:
            匹配结果列表，每项包含 score 和存储字段
        """
        ix = self._get_or_create_chunk_index()
        with ix.searcher() as searcher:
            parser = MultifieldParser(
                ["heading", "content"], schema=self.chunk_schema, group=OrGroup
            )

            terms = self._extract_query_terms(query_str)
            wildcard_query = " OR ".join([f"*{term}*" for term in terms])

            try:
                query = parser.parse(wildcard_query)
            except Exception:
                query = parser.parse(query_str)

            results = searcher.search(query, limit=limit)
            return [{'score': hit.score, **dict(hit)} for hit in results]

    def rebuild_chunk_index(self, chunks: List[KnowledgeChunk]) -> None:
        """
        重建整个分块索引。

        Args:
            chunks: 所有分块列表
        """
        if self.chunk_ix is not None:
            self.chunk_ix.close()
            self.chunk_ix = None

        if not os.path.exists(self.chunk_index_dir):
            os.makedirs(self.chunk_index_dir)

        self.chunk_ix = index.create_in(self.chunk_index_dir, self.chunk_schema)

        writer = self.chunk_ix.writer()
        try:
            for chunk in chunks:
                writer.add_document(
                    chunk_id=chunk.id,
                    item_id=chunk.item_id,
                    chunk_index=chunk.chunk_index,
                    heading=chunk.heading,
                    content=chunk.content,
                )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to rebuild chunk index: {e}")

    def has_chunk_index(self) -> bool:
        """检查分块索引是否存在且有效。"""
        if not os.path.exists(self.chunk_index_dir):
            return False
        try:
            ix = index.open_dir(self.chunk_index_dir)
            ix.close()
            return True
        except Exception:
            return False

    def add_item(self, item: KnowledgeItem) -> None:
        """
        添加知识条目到搜索索引。

        Args:
            item: 待索引的知识条目
        """
        writer = self.ix.writer()
        try:
            writer.add_document(
                id=item.id,
                title=item.title,
                content=item.content,
                source_type=item.source_type.value,
                source_path=item.source_path,
                categories=",".join([cat.name for cat in item.categories]),
                tags=",".join([tag.name for tag in item.tags]),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to add item to index: {e}")

    def update_item(self, item: KnowledgeItem) -> None:
        """
        更新搜索索引中的知识条目。

        Args:
            item: 待更新的知识条目
        """
        writer = self.ix.writer()
        try:
            writer.update_document(
                id=item.id,
                title=item.title,
                content=item.content,
                source_type=item.source_type.value,
                source_path=item.source_path,
                categories=",".join([cat.name for cat in item.categories]),
                tags=",".join([tag.name for tag in item.tags]),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to update item in index: {e}")

    def remove_item(self, item_id: str) -> None:
        """
        从搜索索引中移除知识条目。

        Args:
            item_id: 待移除条目的 ID
        """
        writer = self.ix.writer()
        try:
            writer.delete_by_term("id", item_id)
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to remove item from index: {e}")

    def rebuild_index(self, items: List[KnowledgeItem]) -> None:
        """
        从头重建整个搜索索引。

        Args:
            items: 所有待索引的知识条目列表
        """
        self.ix.close()
        self.ix = index.create_in(self.index_dir, self.schema)

        writer = self.ix.writer()
        try:
            for item in items:
                writer.add_document(
                    id=item.id,
                    title=item.title,
                    content=item.content,
                    source_type=item.source_type.value,
                    source_path=item.source_path,
                    categories=",".join([cat.name for cat in item.categories]),
                    tags=",".join([tag.name for tag in item.tags]),
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            writer.commit()
        except Exception as e:
            writer.cancel()
            raise RuntimeError(f"Failed to rebuild index: {e}")

    def search(
        self,
        query_str: str,
        fields: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[dict]:
        """
        使用查询字符串搜索索引。

        Args:
            query_str: 搜索查询字符串
            fields: 要搜索的字段列表（默认：title 和 content）
            limit: 最大返回结果数

        Returns:
            包含存储字段和评分的结果字典列表
        """
        if fields is None:
            fields = ["title", "content"]

        with self.ix.searcher() as searcher:
            parser = MultifieldParser(fields, schema=self.schema, group=OrGroup)

            terms = self._extract_query_terms(query_str)
            wildcard_query = " OR ".join([f"*{term}*" for term in terms])

            try:
                query = parser.parse(wildcard_query)
            except Exception:
                query = parser.parse(query_str)

            results = searcher.search(query, limit=limit)
            return [{'score': hit.score, **dict(hit)} for hit in results]

    def search_by_field(
        self,
        field: str,
        query_str: str,
        limit: int = 50
    ) -> List[dict]:
        """
        在索引的指定字段中搜索。

        Args:
            field: 要搜索的字段名
            query_str: 搜索查询字符串
            limit: 最大返回结果数

        Returns:
            包含存储字段和评分的结果字典列表
        """
        with self.ix.searcher() as searcher:
            parser = QueryParser(field, schema=self.schema)

            terms = self._extract_query_terms(query_str)
            wildcard_query = " OR ".join([f"*{term}*" for term in terms])

            try:
                query = parser.parse(wildcard_query)
            except Exception:
                query = parser.parse(query_str)

            results = searcher.search(query, limit=limit)
            return [{'score': hit.score, **dict(hit)} for hit in results]

    def get_all_ids(self) -> List[str]:
        """
        获取索引中所有文档的 ID。

        Returns:
            所有文档 ID 列表
        """
        with self.ix.searcher() as searcher:
            return [doc["id"] for doc in searcher.all_stored_fields()]

    def close(self) -> None:
        """关闭索引并释放资源。"""
        if hasattr(self, 'ix') and self.ix is not None:
            self.ix.close()
        if hasattr(self, 'chunk_ix') and self.chunk_ix is not None:
            self.chunk_ix.close()
            self.chunk_ix = None

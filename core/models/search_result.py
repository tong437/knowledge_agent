"""
搜索结果数据模型。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .knowledge_item import KnowledgeItem


@dataclass
class MatchedChunk:
    """匹配到的知识块，包含块内容和匹配位置信息。"""

    chunk_id: str
    content: str
    heading: str
    chunk_index: int
    start_position: int
    end_position: int
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "score": self.score,
        }


@dataclass
class SearchResult:
    """
    单个搜索结果，包含匹配的知识条目和相关性信息。
    """

    item: KnowledgeItem
    relevance_score: float
    matched_fields: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)
    matched_chunks: List[MatchedChunk] = field(default_factory=list)
    context_chunks: List[MatchedChunk] = field(default_factory=list)

    def __post_init__(self):
        if not (0.0 <= self.relevance_score <= 1.0):
            raise ValueError("Relevance score must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "item": self.item.to_dict(),
            "relevance_score": self.relevance_score,
            "matched_fields": self.matched_fields,
            "highlights": self.highlights,
        }
        if self.matched_chunks:
            result["matched_chunks"] = [c.to_dict() for c in self.matched_chunks]
        if self.context_chunks:
            result["context_chunks"] = [c.to_dict() for c in self.context_chunks]
        return result


@dataclass
class SearchOptions:
    """
    搜索选项，用于配置搜索行为、过滤和结果格式。
    """

    max_results: int = 50
    min_relevance: float = 0.05
    include_categories: List[str] = field(default_factory=list)
    exclude_categories: List[str] = field(default_factory=list)
    include_tags: List[str] = field(default_factory=list)
    exclude_tags: List[str] = field(default_factory=list)
    source_types: List[str] = field(default_factory=list)
    sort_by: str = "relevance"
    group_by_category: bool = False

    def __post_init__(self):
        if self.max_results <= 0:
            raise ValueError("Max results must be positive")
        if not (0.0 <= self.min_relevance <= 1.0):
            raise ValueError("Min relevance must be between 0.0 and 1.0")
        if self.sort_by not in ["relevance", "date", "title"]:
            raise ValueError("Sort by must be 'relevance', 'date', or 'title'")


@dataclass
class SearchResults:
    """
    搜索结果容器，包含查询信息和结果统计。
    """

    query: str
    results: List[SearchResult] = field(default_factory=list)
    total_found: int = 0
    search_time_ms: float = 0.0
    grouped_results: Optional[Dict[str, List[SearchResult]]] = None

    def __post_init__(self):
        if self.total_found == 0:
            self.total_found = len(self.results)

    def add_result(self, result: SearchResult) -> None:
        self.results.append(result)
        self.total_found = len(self.results)

    def sort_by_relevance(self) -> None:
        self.results.sort(key=lambda r: r.relevance_score, reverse=True)

    def filter_by_min_relevance(self, min_relevance: float) -> None:
        self.results = [r for r in self.results if r.relevance_score >= min_relevance]
        self.total_found = len(self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_found": self.total_found,
            "search_time_ms": self.search_time_ms,
            "grouped_results": (
                {k: [r.to_dict() for r in v] for k, v in self.grouped_results.items()}
                if self.grouped_results else None
            ),
        }

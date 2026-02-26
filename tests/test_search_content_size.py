"""
缺陷条件探索测试：搜索结果内容大小失控。

**Validates: Requirements 1.1, 1.2, 1.3**

此测试在未修复代码上应当失败，失败即确认缺陷存在。
测试编码了期望行为，修复后测试通过即验证修复正确性。
"""

import uuid
import tempfile
import shutil
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from core.knowledge_agent_core import KnowledgeAgentCore
from core.models.data_source import DataSource, SourceType
from core.models.knowledge_chunk import KnowledgeChunk

# 设计文档中定义的常量
MAX_CHUNK_CONTENT_SIZE = 1500
MAX_MATCHED_CHUNKS = 5
MAX_CONTEXT_CHUNKS = 3
MAX_RESULT_CONTENT_SIZE = 30_000
MAX_TOTAL_CONTENT_SIZE = 100_000
SAFE_CONTENT_THRESHOLD = 5000


@pytest.fixture(scope="module")
def test_workspace():
    """创建测试工作空间，模块级别共享以减少初始化开销。"""
    workspace = Path(tempfile.mkdtemp())
    yield workspace
    shutil.rmtree(workspace, ignore_errors=True)


def _create_core(workspace: Path, test_id: str) -> KnowledgeAgentCore:
    """创建独立的 KnowledgeAgentCore 实例。"""
    test_dir = workspace / test_id
    test_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "storage": {"type": "sqlite", "path": str(test_dir / "test.db")},
        "search": {"index_dir": str(test_dir / "search_index")},
        "security": {"allowed_paths": [str(workspace)]},
    }
    return KnowledgeAgentCore(config=config)


def _generate_large_content(size: int, keyword: str = "machine learning") -> str:
    """生成包含搜索关键词的大型文本内容。"""
    # 在内容中均匀分布关键词，确保搜索能命中
    base_paragraph = (
        f"This document discusses {keyword} techniques and applications. "
        "The field has seen tremendous growth in recent years with advances "
        "in neural networks, deep learning, and natural language processing. "
    )
    # 重复填充到目标大小
    repeat_count = (size // len(base_paragraph)) + 1
    content = (base_paragraph * repeat_count)[:size]
    return content


def _create_document_file(workspace: Path, content: str, filename: str) -> Path:
    """在工作空间中创建文档文件。"""
    file_path = workspace / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


class TestScenarioA_NoChunkFallback:
    """
    场景 A：无分块降级。

    创建大型知识项但不生成分块数据，执行搜索。
    断言 matched_chunks 不为空。

    故障条件：hasNoChunks AND item.content > SAFE_CONTENT_THRESHOLD
    """

    @given(
        content_size=st.integers(min_value=50_000, max_value=200_000),
    )
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_large_item_without_chunks_should_have_matched_chunks(
        self, content_size, test_workspace
    ):
        """
        **Validates: Requirements 1.1**

        大型知识项缺少分块数据时，搜索结果的 matched_chunks 不应为空。
        未修复代码中 _item_search 降级路径返回空 matched_chunks。
        """
        test_id = f"scenario_a_{uuid.uuid4().hex[:8]}"
        core = _create_core(test_workspace, test_id)
        try:
            keyword = "machine learning"
            content = _generate_large_content(content_size, keyword)

            # 创建文档文件并收集知识
            doc_path = _create_document_file(
                test_workspace / test_id, content, "large_doc.txt"
            )
            source = DataSource(
                path=str(doc_path),
                source_type=SourceType.DOCUMENT,
                metadata={"title": "Large Document Without Chunks"},
            )
            item = core.collect_knowledge(source)

            # 手动删除分块数据，模拟分块失败场景
            if core._storage_manager:
                with core._storage_manager._use_connection() as conn:
                    conn.execute(
                        "DELETE FROM knowledge_chunks WHERE item_id = ?", (item.id,)
                    )
                    conn.commit()
            # 从搜索引擎中移除分块索引，迫使搜索降级到 _item_search 路径
            if core._search_engine:
                core._search_engine.remove_chunks_from_index(item.id)
                # 清除分块索引目录，确保 has_chunk_index() 返回 False
                import shutil as _shutil
                chunk_idx_dir = core._search_engine.index_manager.chunk_index_dir
                if Path(chunk_idx_dir).exists():
                    _shutil.rmtree(chunk_idx_dir)

            # 执行搜索
            results = core.search_knowledge(keyword)

            # 断言：搜索应返回结果
            assert results["total_results"] >= 1, (
                f"搜索应命中大型文档，但返回 {results['total_results']} 个结果"
            )

            # 断言：matched_chunks 不应为空
            for result in results["results"]:
                if result["item_id"] == item.id:
                    assert len(result["matched_chunks"]) > 0, (
                        f"大型知识项（{content_size} 字符）缺少分块数据时，"
                        f"matched_chunks 不应为空，但实际为空列表。"
                        f"content 字段仅截断为 {len(result['content'])} 字符，"
                        f"调用方无法获取有效内容片段。"
                    )
        finally:
            core.shutdown()



class TestScenarioB_ChunkContentOverflow:
    """
    场景 B：分块内容溢出。

    创建大型知识项并生成 50+ 个分块（每个约 1500 字符），
    执行搜索命中多个分块。
    断言单结果内容总大小 <= MAX_RESULT_CONTENT_SIZE
    且所有结果总大小 <= MAX_TOTAL_CONTENT_SIZE。

    故障条件：totalContentSize > MAX_RESULT_CONTENT_SIZE
    """

    @given(
        content_size=st.integers(min_value=80_000, max_value=300_000),
    )
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_chunk_search_result_content_within_budget(
        self, content_size, test_workspace
    ):
        """
        **Validates: Requirements 1.2, 1.3**

        分块搜索返回的单结果内容总大小应 <= MAX_RESULT_CONTENT_SIZE，
        所有结果总大小应 <= MAX_TOTAL_CONTENT_SIZE。
        未修复代码中 matched_chunks 和 context_chunks 数量无上限，
        内容未截断，总大小可轻易超出安全阈值。
        """
        test_id = f"scenario_b_{uuid.uuid4().hex[:8]}"
        core = _create_core(test_workspace, test_id)
        try:
            keyword = "machine learning"
            # 生成包含 Markdown 标题的大型内容，确保产生多个分块
            sections = []
            section_count = content_size // 1500
            for i in range(section_count):
                sections.append(
                    f"## Section {i}: {keyword} Topic {i}\n\n"
                    f"This section covers {keyword} concepts in detail. "
                    f"The {keyword} algorithms discussed here include "
                    f"supervised and unsupervised approaches. "
                    + "x" * 1200
                    + "\n\n"
                )
            content = "".join(sections)[:content_size]

            doc_path = _create_document_file(
                test_workspace / test_id, content, "chunked_doc.txt"
            )
            source = DataSource(
                path=str(doc_path),
                source_type=SourceType.DOCUMENT,
                metadata={"title": "Large Chunked Document"},
            )
            core.collect_knowledge(source)

            results = core.search_knowledge(keyword)

            if results["total_results"] == 0:
                return  # 搜索未命中则跳过

            # 计算所有结果的内容总大小
            total_content_size = 0
            for result in results["results"]:
                item_content_size = len(result.get("content", ""))
                for mc in result.get("matched_chunks", []):
                    item_content_size += len(mc.get("content", ""))
                for cc in result.get("context_chunks", []):
                    item_content_size += len(cc.get("content", ""))

                # 断言：单结果内容总大小 <= MAX_RESULT_CONTENT_SIZE
                assert item_content_size <= MAX_RESULT_CONTENT_SIZE, (
                    f"单结果内容总大小 {item_content_size} 字符 "
                    f"超出安全阈值 {MAX_RESULT_CONTENT_SIZE} 字符。"
                    f"matched_chunks 数量: {len(result.get('matched_chunks', []))}，"
                    f"context_chunks 数量: {len(result.get('context_chunks', []))}。"
                )

                total_content_size += item_content_size

            # 断言：所有结果总大小 <= MAX_TOTAL_CONTENT_SIZE
            assert total_content_size <= MAX_TOTAL_CONTENT_SIZE, (
                f"所有结果内容总大小 {total_content_size} 字符 "
                f"超出安全阈值 {MAX_TOTAL_CONTENT_SIZE} 字符。"
                f"结果数量: {results['total_results']}。"
            )
        finally:
            core.shutdown()


class TestScenarioC_OversizedChunk:
    """
    场景 C：单分块超大。

    创建分块内容为 10,000+ 字符的异常大分块，执行搜索。
    断言返回的分块内容已被截断至 MAX_CHUNK_CONTENT_SIZE。
    """

    @given(
        chunk_content_size=st.integers(min_value=10_000, max_value=50_000),
    )
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_oversized_chunk_content_should_be_truncated(
        self, chunk_content_size, test_workspace
    ):
        """
        **Validates: Requirements 1.3**

        搜索返回的单个分块内容应 <= MAX_CHUNK_CONTENT_SIZE。
        未修复代码中分块的 content 字段完全未截断。
        """
        test_id = f"scenario_c_{uuid.uuid4().hex[:8]}"
        core = _create_core(test_workspace, test_id)
        try:
            keyword = "machine learning"
            # 创建一个普通大小的文档先收集
            small_content = f"A brief introduction to {keyword} techniques."
            doc_path = _create_document_file(
                test_workspace / test_id, small_content, "base_doc.txt"
            )
            source = DataSource(
                path=str(doc_path),
                source_type=SourceType.DOCUMENT,
                metadata={"title": "Document With Oversized Chunks"},
            )
            item = core.collect_knowledge(source)

            # 手动插入异常大的分块数据
            oversized_content = (
                f"This chunk discusses {keyword} in great detail. " * 100
                + "y" * chunk_content_size
            )
            oversized_chunks = []
            for i in range(3):
                chunk = KnowledgeChunk(
                    item_id=item.id,
                    chunk_index=i,
                    content=oversized_content,
                    heading=f"Oversized Section {i}",
                    start_position=i * chunk_content_size,
                    end_position=(i + 1) * chunk_content_size,
                )
                oversized_chunks.append(chunk)

            # 保存分块并更新索引
            if core._storage_manager:
                core._storage_manager.save_chunks(item.id, oversized_chunks)
            if core._search_engine:
                core._search_engine.update_chunk_index(item.id, oversized_chunks)

            results = core.search_knowledge(keyword)

            if results["total_results"] == 0:
                return

            # 检查所有返回的分块内容大小
            for result in results["results"]:
                for mc in result.get("matched_chunks", []):
                    assert len(mc.get("content", "")) <= MAX_CHUNK_CONTENT_SIZE, (
                        f"分块内容大小 {len(mc['content'])} 字符 "
                        f"超出最大限制 {MAX_CHUNK_CONTENT_SIZE} 字符。"
                        f"分块 ID: {mc.get('chunk_id', 'unknown')}。"
                    )
                for cc in result.get("context_chunks", []):
                    assert len(cc.get("content", "")) <= MAX_CHUNK_CONTENT_SIZE, (
                        f"上下文分块内容大小 {len(cc['content'])} 字符 "
                        f"超出最大限制 {MAX_CHUNK_CONTENT_SIZE} 字符。"
                        f"分块 ID: {cc.get('chunk_id', 'unknown')}。"
                    )
        finally:
            core.shutdown()

"""
功能完整性集成验证测试。

验证核心业务逻辑在模版框架迁移后仍然正常工作，覆盖：
- 知识收集（单条 + 批量）
- 全文搜索
- 知识组织（分类/标签）
- 内容分块
"""

import pytest

from core.knowledge_agent_core import KnowledgeAgentCore
from core.models.data_source import DataSource, SourceType
from core.chunking.content_chunker import ContentChunker, ChunkConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def core_instance(tmp_path):
    """创建 KnowledgeAgentCore 实例，测试结束后自动关闭。"""
    config = {
        "storage": {"type": "sqlite", "path": str(tmp_path / "test.db")},
        "search": {
            "index_dir": str(tmp_path / "search_index"),
            "min_relevance": 0.1,
            "max_results": 50,
        },
        "security": {
            "allowed_paths": [str(tmp_path)],
            "blocked_extensions": [".exe"],
        },
    }
    core = KnowledgeAgentCore(config=config)
    yield core
    core.shutdown()


@pytest.fixture
def sample_txt(tmp_path):
    """在临时目录创建一个用于测试的 .txt 文件。"""
    file_path = tmp_path / "sample.txt"
    file_path.write_text(
        "Python is a versatile programming language widely used in "
        "data science, web development, and automation. It provides "
        "clear syntax and a rich ecosystem of libraries.",
        encoding="utf-8",
    )
    return file_path


# ---------------------------------------------------------------------------
# 9.1 验证知识收集功能
# ---------------------------------------------------------------------------

class TestKnowledgeCollection:
    """验证从文档数据源收集知识的功能。"""

    def test_collect_knowledge_from_document(self, core_instance, sample_txt):
        """收集单个文档，返回有效的 KnowledgeItem。"""
        source = DataSource(
            path=str(sample_txt),
            source_type=SourceType.DOCUMENT,
            metadata={"title": "Python Introduction"},
        )
        item = core_instance.collect_knowledge(source)

        assert item is not None
        assert item.id
        assert item.content
        assert item.source_type == SourceType.DOCUMENT

    def test_batch_collect_knowledge(self, core_instance, tmp_path):
        """批量收集目录下的多个文件。"""
        for i in range(3):
            (tmp_path / f"doc_{i}.txt").write_text(
                f"Document number {i} with enough content for processing.",
                encoding="utf-8",
            )

        result = core_instance.batch_collect_knowledge(
            directory_path=str(tmp_path),
            file_pattern="*.txt",
        )

        assert result["success_count"] >= 1
        assert result["total_count"] >= 3
        assert isinstance(result["collected_items"], list)


# ---------------------------------------------------------------------------
# 9.4 验证搜索功能
# ---------------------------------------------------------------------------

class TestSearchKnowledge:
    """验证全文搜索功能。"""

    def test_search_returns_results(self, core_instance, tmp_path):
        """先收集知识，再搜索已有内容，应返回结果。"""
        # 创建内容更丰富的文档以确保搜索引擎能索引到
        doc = tmp_path / "searchable.txt"
        doc.write_text(
            "Machine learning is a subset of artificial intelligence. "
            "Machine learning algorithms build models based on sample data. "
            "Deep learning is a branch of machine learning.",
            encoding="utf-8",
        )
        source = DataSource(
            path=str(doc),
            source_type=SourceType.DOCUMENT,
            metadata={"title": "Machine Learning Guide"},
        )
        core_instance.collect_knowledge(source)

        results = core_instance.search_knowledge("machine learning")

        assert results["total_results"] >= 1
        assert len(results["results"]) >= 1

    def test_search_nonexistent_returns_empty(self, core_instance, sample_txt):
        """搜索不存在的内容，应返回空结果。"""
        source = DataSource(
            path=str(sample_txt),
            source_type=SourceType.DOCUMENT,
            metadata={"title": "Python Introduction"},
        )
        core_instance.collect_knowledge(source)

        results = core_instance.search_knowledge("xyznonexistentkeyword12345")

        assert results["total_results"] == 0
        assert len(results["results"]) == 0


# ---------------------------------------------------------------------------
# 9.5 验证知识组织功能
# ---------------------------------------------------------------------------

class TestOrganizeKnowledge:
    """验证知识组织（分类/标签）功能。"""

    def test_organize_returns_categories_and_tags(self, core_instance, sample_txt):
        """收集知识后调用 organize_knowledge，返回分类/标签信息。"""
        source = DataSource(
            path=str(sample_txt),
            source_type=SourceType.DOCUMENT,
            metadata={"title": "Python Introduction"},
        )
        item = core_instance.collect_knowledge(source)

        org_result = core_instance.organize_knowledge(item)

        assert org_result["success"] is True
        assert org_result["item_id"] == item.id
        assert "categories" in org_result
        assert "tags" in org_result
        assert isinstance(org_result["categories"], list)
        assert isinstance(org_result["tags"], list)


# ---------------------------------------------------------------------------
# 9.6 验证内容分块功能
# ---------------------------------------------------------------------------

class TestContentChunker:
    """直接测试 ContentChunker 类的分块逻辑。"""

    def test_empty_content_returns_empty(self):
        """空内容返回空列表。"""
        chunker = ContentChunker()
        assert chunker.chunk("", "Title") == []
        assert chunker.chunk("   ", "Title") == []

    def test_short_document_returns_single_chunk(self):
        """短文档返回单个分块。"""
        chunker = ContentChunker()
        chunks = chunker.chunk("Short text.", "Title")

        assert len(chunks) == 1
        assert "Short text." in chunks[0].content

    def test_markdown_headings_produce_multiple_chunks(self):
        """含 Markdown 标题的长文档按标题分块。"""
        content = (
            "# Introduction\n\n"
            + "A" * 300
            + "\n\n# Methods\n\n"
            + "B" * 300
            + "\n\n# Results\n\n"
            + "C" * 300
        )
        chunker = ContentChunker()
        chunks = chunker.chunk(content, "Research Paper")

        assert len(chunks) > 1

    def test_plain_text_splits_by_paragraph(self):
        """纯文本长文档按段落分块。"""
        paragraphs = [f"Paragraph {i}. " + "x" * 200 for i in range(10)]
        content = "\n\n".join(paragraphs)

        chunker = ContentChunker()
        chunks = chunker.chunk(content, "Plain Text")

        assert len(chunks) > 1

"""
内容分块引擎，将长文档拆分为语义完整的 KnowledgeChunk。

三级分块策略：
1. 按 Markdown 标题结构分块
2. 按段落（双换行符）分块
3. 对超长文本使用滑动窗口二次切分
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from modules.YA_Common.utils.logger import get_logger
from core.models.knowledge_chunk import KnowledgeChunk

logger = get_logger(__name__)


@dataclass
class ChunkConfig:
    """分块配置。"""

    min_chunk_size: int = 100
    max_chunk_size: int = 1500
    overlap_ratio: float = 0.2


class ContentChunker:
    """文档内容分块引擎。"""

    def __init__(self, config: Optional[ChunkConfig] = None) -> None:
        self.config = config or ChunkConfig()

    def chunk(self, content: str, title: str = "") -> List[KnowledgeChunk]:
        """
        将文档内容拆分为语义完整的分块。

        空内容返回空列表；短文档直接作为单分块返回；
        异常时退化为单分块返回。
        """
        if not content or not content.strip():
            return []

        try:
            return self._do_chunk(content, title)
        except Exception:
            logger.warning("分块过程异常，退化为单分块返回", exc_info=True)
            return [
                self._create_chunk(content, title, 0, len(content), 0)
            ]

    def _do_chunk(self, content: str, title: str) -> List[KnowledgeChunk]:
        """核心分块逻辑。"""
        # 短文档直接作为单分块
        if len(content) < self.config.min_chunk_size * 2:
            return [
                self._create_chunk(content, title, 0, len(content), 0)
            ]

        raw_pieces: List[Tuple[str, str, int]] = []  # (heading, text, start_pos)

        heading_sections = self._split_by_headings(content)
        if heading_sections:
            raw_pieces = heading_sections
        else:
            # 无标题，整体按段落处理
            paragraphs = self._split_by_paragraphs(content, 0)
            raw_pieces = [("", text, pos) for text, pos in paragraphs]

        # 对每个片段做二次切分
        final_pieces: List[Tuple[str, str, int]] = []
        for heading, text, start_pos in raw_pieces:
            if len(text) <= self.config.max_chunk_size:
                final_pieces.append((heading, text, start_pos))
            else:
                # 尝试段落分块
                sub_paragraphs = self._split_by_paragraphs(text, start_pos)
                for para_text, para_pos in sub_paragraphs:
                    if len(para_text) <= self.config.max_chunk_size:
                        final_pieces.append((heading, para_text, para_pos))
                    else:
                        # 滑动窗口切分
                        windows = self._sliding_window_split(para_text, para_pos)
                        for win_text, win_pos in windows:
                            final_pieces.append((heading, win_text, win_pos))

        # 过滤空片段，生成 KnowledgeChunk 列表
        chunks: List[KnowledgeChunk] = []
        chunk_index = 0
        for heading, text, start_pos in final_pieces:
            stripped = text.strip()
            if not stripped:
                continue
            end_pos = start_pos + len(text)
            chunks.append(
                self._create_chunk(stripped, heading, start_pos, end_pos, chunk_index)
            )
            chunk_index += 1

        # 兜底：如果所有片段都被过滤掉了，返回单分块
        if not chunks:
            return [
                self._create_chunk(content, title, 0, len(content), 0)
            ]

        return chunks

    def _split_by_headings(self, content: str) -> List[Tuple[str, str, int]]:
        """
        按 Markdown 标题结构分块。

        返回 (heading, section_content, start_position) 列表。
        如果没有标题，返回空列表（退化到段落分块）。
        """
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(content))

        if not matches:
            return []

        sections: List[Tuple[str, str, int]] = []

        # 标题前的内容作为无标题段
        if matches[0].start() > 0:
            pre_text = content[: matches[0].start()]
            if pre_text.strip():
                sections.append(("", pre_text, 0))

        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_text = content[start:end]
            if section_text.strip():
                sections.append((heading, section_text, start))

        return sections

    def _split_by_paragraphs(
        self, content: str, start_offset: int = 0
    ) -> List[Tuple[str, int]]:
        """
        按双换行符分隔段落。

        返回 (paragraph_text, start_position) 列表，过滤空段落。
        """
        parts = re.split(r"\n\n", content)
        result: List[Tuple[str, int]] = []
        pos = 0
        for part in parts:
            if part.strip():
                result.append((part, start_offset + pos))
            # 跳过当前段落长度 + 分隔符长度
            pos += len(part) + 2  # +2 for "\n\n"
        return result

    def _sliding_window_split(
        self, text: str, start_offset: int = 0
    ) -> List[Tuple[str, int]]:
        """
        滑动窗口切分超长文本。

        步长 = max_chunk_size * (1 - overlap_ratio)。
        返回 (chunk_text, start_position) 列表。
        """
        max_size = self.config.max_chunk_size
        step = int(max_size * (1 - self.config.overlap_ratio))
        if step <= 0:
            step = 1

        result: List[Tuple[str, int]] = []
        i = 0
        while i < len(text):
            end = min(i + max_size, len(text))
            chunk_text = text[i:end]
            if chunk_text.strip():
                result.append((chunk_text, start_offset + i))
            if end >= len(text):
                break
            i += step

        return result

    def _create_chunk(
        self,
        content: str,
        heading: str,
        start_pos: int,
        end_pos: int,
        chunk_index: int,
    ) -> KnowledgeChunk:
        """创建 KnowledgeChunk 实例，item_id 留空由调用方设置。"""
        return KnowledgeChunk(
            item_id="",
            chunk_index=chunk_index,
            content=content,
            heading=heading,
            start_position=start_pos,
            end_position=end_pos,
        )

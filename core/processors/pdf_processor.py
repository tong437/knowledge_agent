"""
PDF 文件处理器，用于从 PDF 文件中提取内容。
"""

import re
from pathlib import Path
from typing import Dict, Any, List

from .base_processor import BaseDataSourceProcessor
from core.models import DataSource, SourceType
from core.exceptions import ProcessingError


class PDFProcessor(BaseDataSourceProcessor):
    """
    PDF 文件处理器。

    支持：
    - 从 PDF 文件中提取文本
    - 提取元数据（作者、标题、创建日期等）
    - 结构化信息提取

    依赖：pypdf 或 PyPDF2
    """

    def __init__(self):
        """初始化 PDF 处理器。"""
        super().__init__()
        self._pdf_library = self._check_pdf_support()

    def _check_pdf_support(self) -> str:
        """
        检查可用的 PDF 库。

        Returns:
            str: 'pypdf'、'PyPDF2' 或 None
        """
        try:
            import pypdf
            return 'pypdf'
        except ImportError:
            pass

        try:
            import PyPDF2
            return 'PyPDF2'
        except ImportError:
            pass

        self.logger.warning(
            "No PDF library available. PDF support disabled. "
            "Install with: pip install pypdf"
        )
        return None

    def get_supported_types(self) -> List[SourceType]:
        """获取此处理器支持的数据源类型列表。"""
        return [SourceType.PDF]

    def validate(self, source: DataSource) -> bool:
        """
        验证 PDF 数据源是否可以被处理。

        Args:
            source: 待验证的数据源

        Returns:
            bool: 可处理返回 True，否则返回 False
        """
        if not super().validate(source):
            return False

        if not self._pdf_library:
            self.logger.warning("PDF library not available")
            return False

        path = Path(source.path)
        if path.suffix.lower() != '.pdf':
            self.logger.warning(f"Not a PDF file: {source.path}")
            return False

        return True

    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        从 PDF 数据源中提取元数据。

        Args:
            source: 待提取元数据的数据源

        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = super().get_metadata(source)
        metadata['document_type'] = 'pdf'

        try:
            if self._pdf_library == 'pypdf':
                import pypdf
                with open(source.path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    metadata['page_count'] = len(reader.pages)

                    if reader.metadata:
                        info = reader.metadata
                        if info.author:
                            metadata['author'] = info.author
                        if info.title:
                            metadata['pdf_title'] = info.title
                        if info.subject:
                            metadata['subject'] = info.subject
                        if info.creator:
                            metadata['creator'] = info.creator
                        if info.producer:
                            metadata['producer'] = info.producer
                        if info.creation_date:
                            metadata['pdf_created'] = str(info.creation_date)
                        if info.modification_date:
                            metadata['pdf_modified'] = str(info.modification_date)

            elif self._pdf_library == 'PyPDF2':
                import PyPDF2
                with open(source.path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    metadata['page_count'] = len(reader.pages)

                    if reader.metadata:
                        info = reader.metadata
                        if '/Author' in info:
                            metadata['author'] = info['/Author']
                        if '/Title' in info:
                            metadata['pdf_title'] = info['/Title']
                        if '/Subject' in info:
                            metadata['subject'] = info['/Subject']
                        if '/Creator' in info:
                            metadata['creator'] = info['/Creator']
                        if '/Producer' in info:
                            metadata['producer'] = info['/Producer']
                        if '/CreationDate' in info:
                            metadata['pdf_created'] = info['/CreationDate']
                        if '/ModDate' in info:
                            metadata['pdf_modified'] = info['/ModDate']

        except Exception as e:
            self.logger.warning(
                f"Error extracting PDF metadata from {source.path}: {str(e)}"
            )

        return metadata

    def _extract_content(self, source: DataSource) -> str:
        """
        从 PDF 文件中提取内容。

        Args:
            source: 待提取内容的数据源

        Returns:
            str: 提取的内容

        Raises:
            ProcessingError: 内容提取失败时抛出
        """
        if not self._pdf_library:
            raise ProcessingError(
                "PDF library not available. Install pypdf or PyPDF2."
            )

        try:
            if self._pdf_library == 'pypdf':
                return self._extract_with_pypdf(source)
            elif self._pdf_library == 'PyPDF2':
                return self._extract_with_pypdf2(source)
            else:
                raise ProcessingError("No PDF library available")

        except Exception as e:
            raise ProcessingError(
                f"Error extracting PDF content from {source.path}: {str(e)}"
            ) from e

    def _extract_with_pypdf(self, source: DataSource) -> str:
        """
        使用 pypdf 库提取内容。

        Args:
            source: 数据源

        Returns:
            str: 提取的内容
        """
        import pypdf

        with open(source.path, 'rb') as f:
            reader = pypdf.PdfReader(f)

            pages_text = []
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append(f"--- Page {page_num} ---\n{text}")
                except Exception as e:
                    self.logger.warning(
                        f"Error extracting page {page_num} from {source.path}: {str(e)}"
                    )

            content = '\n\n'.join(pages_text)
            content = self._clean_text(content)
            return content

    def _extract_with_pypdf2(self, source: DataSource) -> str:
        """
        使用 PyPDF2 库提取内容。

        Args:
            source: 数据源

        Returns:
            str: 提取的内容
        """
        import PyPDF2

        with open(source.path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            pages_text = []
            for page_num in range(len(reader.pages)):
                try:
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception as e:
                    self.logger.warning(
                        f"Error extracting page {page_num + 1} from {source.path}: {str(e)}"
                    )

            content = '\n\n'.join(pages_text)
            content = self._clean_text(content)
            return content

    def _clean_text(self, text: str) -> str:
        """
        清理和规范化 PDF 文本内容。

        Args:
            text: 待清理的文本

        Returns:
            str: 清理后的文本
        """
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        # 移除常见的 PDF 伪影字符
        text = re.sub(r'\x00', '', text)
        text = re.sub(r'[\x01-\x08\x0b-\x0c\x0e-\x1f]', '', text)
        text = text.strip()
        return text

    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        为 PDF 文档生成标题。

        优先从 PDF 元数据、首行非空内容、文件名中提取。

        Args:
            source: 数据源
            content: 提取的内容

        Returns:
            str: 生成的标题
        """
        metadata = self.get_metadata(source)
        if 'pdf_title' in metadata and metadata['pdf_title']:
            return metadata['pdf_title']

        if content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('--- Page'):
                    continue
                if line and len(line) < 100:
                    return line

        path = Path(source.path)
        return path.stem

"""
数据源处理器基类，提供通用处理功能。
"""

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from core.interfaces import DataSourceProcessor
from core.models import DataSource, KnowledgeItem, SourceType
from core.exceptions import ProcessingError, ValidationError
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("knowledge_agent.processors.base")


class BaseDataSourceProcessor(DataSourceProcessor, ABC):
    """
    DataSourceProcessor 的基础实现，提供通用功能。

    包含错误处理、验证逻辑和工具方法，
    供具体处理器实现复用。
    """

    def __init__(self):
        """初始化基础处理器。"""
        self.logger = logger

    def process(self, source: DataSource) -> KnowledgeItem:
        """
        处理数据源，包含错误处理。

        Args:
            source: 待处理的数据源

        Returns:
            KnowledgeItem: 生成的知识条目

        Raises:
            ProcessingError: 数据源无法处理时抛出
            ValidationError: 数据源验证失败时抛出
        """
        try:
            if not self.validate(source):
                raise ValidationError(
                    f"Data source validation failed: {source.path}"
                )

            if not self._file_exists(source.path):
                raise ProcessingError(
                    f"File not found: {source.path}"
                )

            metadata = self.get_metadata(source)
            content = self._extract_content(source)
            title = self._generate_title(source, content)

            knowledge_item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                source_type=source.source_type,
                source_path=source.path,
                metadata=metadata,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.logger.info(f"Successfully processed: {source.path}")
            return knowledge_item

        except ValidationError:
            self.logger.error(f"Validation error for: {source.path}")
            raise
        except ProcessingError:
            self.logger.error(f"Processing error for: {source.path}")
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error processing {source.path}: {str(e)}",
                exc_info=True
            )
            raise ProcessingError(
                f"Failed to process {source.path}: {str(e)}"
            ) from e

    def validate(self, source: DataSource) -> bool:
        """
        验证数据源是否可以被处理。

        Args:
            source: 待验证的数据源

        Returns:
            bool: 可处理返回 True，否则返回 False
        """
        try:
            if not source.is_valid():
                self.logger.warning(f"Invalid data source: {source.path}")
                return False

            if source.source_type not in self.get_supported_types():
                self.logger.warning(
                    f"Unsupported source type {source.source_type} for {source.path}"
                )
                return False

            if not self._file_exists(source.path):
                self.logger.warning(f"File not found: {source.path}")
                return False

            if not self._is_readable(source.path):
                self.logger.warning(f"File not readable: {source.path}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating {source.path}: {str(e)}")
            return False

    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        从数据源中提取通用元数据。

        Args:
            source: 待提取元数据的数据源

        Returns:
            Dict[str, Any]: 元数据字典
        """
        try:
            path = Path(source.path)
            stat = path.stat()

            metadata = {
                "file_name": path.name,
                "file_extension": path.suffix,
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "absolute_path": str(path.absolute()),
            }

            metadata.update(source.metadata)
            return metadata

        except Exception as e:
            self.logger.warning(f"Error extracting metadata from {source.path}: {str(e)}")
            return source.metadata.copy()

    @abstractmethod
    def _extract_content(self, source: DataSource) -> str:
        """
        从数据源中提取内容。

        子类必须实现此方法以处理特定文件格式。

        Args:
            source: 待提取内容的数据源

        Returns:
            str: 提取的内容

        Raises:
            ProcessingError: 内容提取失败时抛出
        """
        pass

    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        为知识条目生成标题。

        Args:
            source: 数据源
            content: 提取的内容

        Returns:
            str: 生成的标题
        """
        path = Path(source.path)
        title = path.stem

        if content:
            lines = content.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line and len(first_line) < 100:
                    title = first_line

        return title

    def _file_exists(self, path: str) -> bool:
        """检查文件是否存在。"""
        try:
            return Path(path).exists()
        except Exception:
            return False

    def _is_readable(self, path: str) -> bool:
        """检查文件是否可读。"""
        try:
            return os.access(path, os.R_OK)
        except Exception:
            return False

    def _read_file(self, path: str, encoding: str = 'utf-8') -> str:
        """
        读取文件内容，包含错误处理。

        Args:
            path: 文件路径
            encoding: 文件编码（默认 utf-8）

        Returns:
            str: 文件内容

        Raises:
            ProcessingError: 文件无法读取时抛出
        """
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        self.logger.info(f"Successfully read {path} with {enc} encoding")
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ProcessingError(f"Unable to decode file: {path}")
        except Exception as e:
            raise ProcessingError(f"Error reading file {path}: {str(e)}") from e

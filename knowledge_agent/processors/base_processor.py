"""
Base data source processor with common functionality.
"""

import os
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from ..interfaces.data_source_processor import DataSourceProcessor
from ..models import DataSource, KnowledgeItem, SourceType
from ..core.exceptions import ProcessingError, ValidationError


logger = logging.getLogger(__name__)


class BaseDataSourceProcessor(DataSourceProcessor, ABC):
    """
    Base implementation of DataSourceProcessor with common functionality.
    
    Provides error handling, validation logic, and utility methods
    that can be reused by specific processor implementations.
    """
    
    def __init__(self):
        """Initialize the base processor."""
        self.logger = logger
    
    def process(self, source: DataSource) -> KnowledgeItem:
        """
        Process a data source with error handling.
        
        Args:
            source: The data source to process
            
        Returns:
            KnowledgeItem: The generated knowledge item
            
        Raises:
            ProcessingError: If the source cannot be processed
            ValidationError: If the source fails validation
        """
        try:
            # Validate the source
            if not self.validate(source):
                raise ValidationError(
                    f"Data source validation failed: {source.path}"
                )
            
            # Check if file exists
            if not self._file_exists(source.path):
                raise ProcessingError(
                    f"File not found: {source.path}"
                )
            
            # Extract metadata
            metadata = self.get_metadata(source)
            
            # Process the content
            content = self._extract_content(source)
            
            # Generate title
            title = self._generate_title(source, content)
            
            # Create knowledge item
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
        Validate that a data source can be processed.
        
        Args:
            source: The data source to validate
            
        Returns:
            bool: True if the source can be processed, False otherwise
        """
        try:
            # Check if source is valid
            if not source.is_valid():
                self.logger.warning(f"Invalid data source: {source.path}")
                return False
            
            # Check if source type is supported
            if source.source_type not in self.get_supported_types():
                self.logger.warning(
                    f"Unsupported source type {source.source_type} for {source.path}"
                )
                return False
            
            # Check if file exists
            if not self._file_exists(source.path):
                self.logger.warning(f"File not found: {source.path}")
                return False
            
            # Check if file is readable
            if not self._is_readable(source.path):
                self.logger.warning(f"File not readable: {source.path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating {source.path}: {str(e)}")
            return False
    
    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        Extract common metadata from a data source.
        
        Args:
            source: The data source to extract metadata from
            
        Returns:
            Dict[str, Any]: Metadata dictionary
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
            
            # Merge with source metadata
            metadata.update(source.metadata)
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata from {source.path}: {str(e)}")
            return source.metadata.copy()
    
    @abstractmethod
    def _extract_content(self, source: DataSource) -> str:
        """
        Extract content from the data source.
        
        This method must be implemented by subclasses to handle
        specific file formats.
        
        Args:
            source: The data source to extract content from
            
        Returns:
            str: The extracted content
            
        Raises:
            ProcessingError: If content extraction fails
        """
        pass
    
    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        Generate a title for the knowledge item.
        
        Args:
            source: The data source
            content: The extracted content
            
        Returns:
            str: Generated title
        """
        # Use filename as default title
        path = Path(source.path)
        title = path.stem
        
        # Try to extract a better title from content
        # (can be overridden by subclasses)
        if content:
            lines = content.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line and len(first_line) < 100:
                    title = first_line
        
        return title
    
    def _file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        try:
            return Path(path).exists()
        except Exception:
            return False
    
    def _is_readable(self, path: str) -> bool:
        """Check if a file is readable."""
        try:
            return os.access(path, os.R_OK)
        except Exception:
            return False
    
    def _read_file(self, path: str, encoding: str = 'utf-8') -> str:
        """
        Read file content with error handling.
        
        Args:
            path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            str: File content
            
        Raises:
            ProcessingError: If file cannot be read
        """
        try:
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
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

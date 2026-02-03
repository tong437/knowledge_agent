"""
PDF processor for extracting content from PDF files.
"""

import re
from pathlib import Path
from typing import Dict, Any, List

from .base_processor import BaseDataSourceProcessor
from ..models import DataSource, SourceType
from ..core.exceptions import ProcessingError


class PDFProcessor(BaseDataSourceProcessor):
    """
    Processor for PDF files.
    
    Supports:
    - Text extraction from PDF files
    - Metadata extraction (author, title, creation date, etc.)
    - Structured information extraction
    
    Requires: PyPDF2 or pypdf library
    """
    
    def __init__(self):
        """Initialize the PDF processor."""
        super().__init__()
        self._pdf_library = self._check_pdf_support()
    
    def _check_pdf_support(self) -> str:
        """
        Check which PDF library is available.
        
        Returns:
            str: 'pypdf', 'PyPDF2', or None
        """
        # Try pypdf first (newer)
        try:
            import pypdf
            return 'pypdf'
        except ImportError:
            pass
        
        # Try PyPDF2 (older but still common)
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
        """Get the list of source types this processor supports."""
        return [SourceType.PDF]
    
    def validate(self, source: DataSource) -> bool:
        """
        Validate that a PDF source can be processed.
        
        Args:
            source: The data source to validate
            
        Returns:
            bool: True if the source can be processed, False otherwise
        """
        # Call parent validation
        if not super().validate(source):
            return False
        
        # Check if PDF library is available
        if not self._pdf_library:
            self.logger.warning("PDF library not available")
            return False
        
        # Check file extension
        path = Path(source.path)
        if path.suffix.lower() != '.pdf':
            self.logger.warning(f"Not a PDF file: {source.path}")
            return False
        
        return True
    
    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        Extract metadata from a PDF source.
        
        Args:
            source: The data source to extract metadata from
            
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = super().get_metadata(source)
        
        # Add PDF-specific metadata
        metadata['document_type'] = 'pdf'
        
        try:
            if self._pdf_library == 'pypdf':
                import pypdf
                with open(source.path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    
                    # Basic info
                    metadata['page_count'] = len(reader.pages)
                    
                    # Document info
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
                    
                    # Basic info
                    metadata['page_count'] = len(reader.pages)
                    
                    # Document info
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
        Extract content from the PDF file.
        
        Args:
            source: The data source to extract content from
            
        Returns:
            str: The extracted content
            
        Raises:
            ProcessingError: If content extraction fails
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
        Extract content using pypdf library.
        
        Args:
            source: The data source
            
        Returns:
            str: The extracted content
        """
        import pypdf
        
        with open(source.path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            # Extract text from all pages
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
            
            # Clean up the content
            content = self._clean_text(content)
            
            return content
    
    def _extract_with_pypdf2(self, source: DataSource) -> str:
        """
        Extract content using PyPDF2 library.
        
        Args:
            source: The data source
            
        Returns:
            str: The extracted content
        """
        import PyPDF2
        
        with open(source.path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Extract text from all pages
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
            
            # Clean up the content
            content = self._clean_text(content)
            
            return content
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize PDF text content.
        
        Args:
            text: The text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'\x00', '', text)  # Null bytes
        text = re.sub(r'[\x01-\x08\x0b-\x0c\x0e-\x1f]', '', text)  # Control characters
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        Generate a title for the PDF document.
        
        Tries to extract title from:
        1. PDF metadata
        2. First non-empty line of content
        3. Filename
        
        Args:
            source: The data source
            content: The extracted content
            
        Returns:
            str: Generated title
        """
        # Try to get title from metadata
        metadata = self.get_metadata(source)
        if 'pdf_title' in metadata and metadata['pdf_title']:
            return metadata['pdf_title']
        
        # Try first non-empty line from content
        if content:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                # Skip page markers
                if line.startswith('--- Page'):
                    continue
                if line and len(line) < 100:
                    return line
        
        # Fall back to filename
        path = Path(source.path)
        return path.stem

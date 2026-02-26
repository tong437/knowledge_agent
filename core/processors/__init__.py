"""
数据源处理器模块，用于从各种来源收集知识。
"""

from .base_processor import BaseDataSourceProcessor
from .document_processor import DocumentProcessor
from .pdf_processor import PDFProcessor
from .code_processor import CodeProcessor
from .web_processor import WebProcessor

__all__ = [
    "BaseDataSourceProcessor",
    "DocumentProcessor",
    "PDFProcessor",
    "CodeProcessor",
    "WebProcessor",
]

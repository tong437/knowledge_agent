"""
Data source processor interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models import DataSource, KnowledgeItem


class DataSourceProcessor(ABC):
    """
    Abstract base class for processing different types of data sources.
    
    Defines the interface that all data source processors must implement
    to handle knowledge collection from various sources.
    """
    
    @abstractmethod
    def process(self, source: DataSource) -> KnowledgeItem:
        """
        Process a data source and generate a knowledge item.
        
        Args:
            source: The data source to process
            
        Returns:
            KnowledgeItem: The generated knowledge item
            
        Raises:
            ProcessingError: If the source cannot be processed
        """
        pass
    
    @abstractmethod
    def validate(self, source: DataSource) -> bool:
        """
        Validate that a data source can be processed.
        
        Args:
            source: The data source to validate
            
        Returns:
            bool: True if the source can be processed, False otherwise
        """
        pass
    
    @abstractmethod
    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        Extract metadata from a data source.
        
        Args:
            source: The data source to extract metadata from
            
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list:
        """
        Get the list of source types this processor supports.
        
        Returns:
            list: List of supported SourceType values
        """
        pass
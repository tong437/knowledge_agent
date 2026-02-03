"""
Data source models and types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class SourceType(Enum):
    """Enumeration of supported data source types."""
    
    DOCUMENT = "document"  # Word, TXT, Markdown files
    PDF = "pdf"           # PDF files
    WEB = "web"           # Web pages
    CODE = "code"         # Code files
    IMAGE = "image"       # Image files
    UNKNOWN = "unknown"   # Unknown or unsupported types


@dataclass
class DataSource:
    """
    Represents a data source for knowledge collection.
    
    Contains information about the source location, type, and metadata
    needed for processing.
    """
    
    path: str
    source_type: SourceType
    metadata: Dict[str, Any]
    encoding: Optional[str] = None
    
    def __post_init__(self):
        """Validate the data source after initialization."""
        if not self.path:
            raise ValueError("Data source path cannot be empty")
    
    def is_valid(self) -> bool:
        """Check if the data source is valid for processing."""
        return bool(self.path) and self.source_type != SourceType.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the data source to a dictionary."""
        return {
            "path": self.path,
            "source_type": self.source_type.value,
            "metadata": self.metadata,
            "encoding": self.encoding,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSource":
        """Create a data source from a dictionary."""
        return cls(
            path=data["path"],
            source_type=SourceType(data["source_type"]),
            metadata=data.get("metadata", {}),
            encoding=data.get("encoding"),
        )
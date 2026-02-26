"""
数据源模型和类型定义。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class SourceType(Enum):
    """支持的数据源类型枚举。"""

    DOCUMENT = "document"
    PDF = "pdf"
    WEB = "web"
    CODE = "code"
    IMAGE = "image"
    UNKNOWN = "unknown"


@dataclass
class DataSource:
    """
    数据源定义，包含源位置、类型和处理所需的元数据。
    """

    path: str
    source_type: SourceType
    metadata: Dict[str, Any]
    encoding: Optional[str] = None

    def __post_init__(self):
        if not self.path:
            raise ValueError("Data source path cannot be empty")

    def is_valid(self) -> bool:
        return bool(self.path) and self.source_type != SourceType.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "source_type": self.source_type.value,
            "metadata": self.metadata,
            "encoding": self.encoding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSource":
        return cls(
            path=data["path"],
            source_type=SourceType(data["source_type"]),
            metadata=data.get("metadata", {}),
            encoding=data.get("encoding"),
        )

"""
标签数据模型。
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Tag:
    """
    知识标签，用于灵活地标记和筛选知识条目。

    支持使用计数追踪和颜色自定义。
    """

    id: str
    name: str
    color: str = "#007bff"
    usage_count: int = 0

    def __post_init__(self):
        if not self.id:
            raise ValueError("Tag ID cannot be empty")
        if not self.name:
            raise ValueError("Tag name cannot be empty")
        if self.usage_count < 0:
            raise ValueError("Tag usage count cannot be negative")

    def increment_usage(self) -> None:
        self.usage_count += 1

    def decrement_usage(self) -> None:
        if self.usage_count > 0:
            self.usage_count -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        return cls(
            id=data["id"],
            name=data["name"],
            color=data.get("color", "#007bff"),
            usage_count=data.get("usage_count", 0),
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Tag):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

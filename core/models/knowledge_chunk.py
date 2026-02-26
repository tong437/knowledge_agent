"""
知识分块数据模型。
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class KnowledgeChunk:
    """文档分块，KnowledgeItem 的子单元，表示文档中一个语义完整的片段。"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    chunk_index: int = 0
    content: str = ""
    heading: str = ""
    start_position: int = 0
    end_position: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "heading": self.heading,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeChunk":
        return cls(
            id=data["id"],
            item_id=data["item_id"],
            chunk_index=data["chunk_index"],
            content=data["content"],
            heading=data.get("heading", ""),
            start_position=data["start_position"],
            end_position=data["end_position"],
            metadata=data.get("metadata", {}),
        )

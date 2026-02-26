"""
数据源类型自动检测器。

根据文件路径或 URL 自动识别数据源类型，支持通过文件扩展名和 URL 模式进行检测。
检测优先级：URL 模式 > 文件扩展名 > 默认 DOCUMENT。
"""

from typing import Dict
from pathlib import Path

from core.models.data_source import SourceType


class SourceTypeDetector:
    """
    数据源类型自动检测器。

    通过分析文件路径的扩展名或 URL 模式，自动判断数据源所属的类型。
    支持常见的文档、PDF、代码、图片和网页类型。
    """

    # 文件扩展名到数据源类型的映射表
    EXTENSION_MAP: Dict[str, SourceType] = {
        ".pdf": SourceType.PDF,
        ".py": SourceType.CODE,
        ".js": SourceType.CODE,
        ".java": SourceType.CODE,
        ".cpp": SourceType.CODE,
        ".c": SourceType.CODE,
        ".go": SourceType.CODE,
        ".rs": SourceType.CODE,
        ".ts": SourceType.CODE,
        ".jsx": SourceType.CODE,
        ".tsx": SourceType.CODE,
        ".rb": SourceType.CODE,
        ".swift": SourceType.CODE,
        ".kt": SourceType.CODE,
        ".jpg": SourceType.IMAGE,
        ".jpeg": SourceType.IMAGE,
        ".png": SourceType.IMAGE,
        ".gif": SourceType.IMAGE,
        ".bmp": SourceType.IMAGE,
        ".webp": SourceType.IMAGE,
        ".txt": SourceType.DOCUMENT,
        ".md": SourceType.DOCUMENT,
        ".doc": SourceType.DOCUMENT,
        ".docx": SourceType.DOCUMENT,
        ".rtf": SourceType.DOCUMENT,
    }

    @staticmethod
    def detect(source_path: str) -> SourceType:
        """
        根据路径自动检测数据源类型。

        检测优先级：
        1. URL 模式（http:// 或 https:// 开头） -> WEB
        2. 文件扩展名匹配 -> 对应类型
        3. 未知扩展名 -> DOCUMENT（默认值）

        Args:
            source_path: 文件路径或 URL 字符串

        Returns:
            检测到的 SourceType 枚举值
        """
        if source_path.startswith("http://") or source_path.startswith("https://"):
            return SourceType.WEB

        suffix = Path(source_path).suffix.lower()
        return SourceTypeDetector.EXTENSION_MAP.get(suffix, SourceType.DOCUMENT)

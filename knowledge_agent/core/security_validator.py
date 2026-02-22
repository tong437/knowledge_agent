"""
安全路径验证器模块。

提供文件路径安全验证功能，包括路径遍历防护、扩展名黑名单检查
和允许路径范围限制。用于在文件操作前确保路径的安全性。
"""

import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 默认扩展名黑名单
DEFAULT_BLOCKED_EXTENSIONS: List[str] = [
    ".exe", ".bat", ".cmd", ".sh", ".bin", ".dll", ".so"
]


class SecurityValidator:
    """安全路径验证器。

    对文件路径进行安全性验证，防止路径遍历攻击，
    限制可访问的路径范围，并阻止危险扩展名的文件访问。
    """

    def __init__(
        self,
        allowed_paths: Optional[List[str]] = None,
        blocked_extensions: Optional[List[str]] = None,
    ):
        """初始化安全路径验证器。

        Args:
            allowed_paths: 允许访问的路径列表。为空或 None 时允许任意路径。
            blocked_extensions: 扩展名黑名单列表（如 [".exe", ".bat"]）。
                为 None 时使用默认黑名单，为空列表时不阻止任何扩展名。
        """
        self.allowed_paths: List[str] = allowed_paths or []
        self.blocked_extensions: List[str] = (
            blocked_extensions if blocked_extensions is not None
            else DEFAULT_BLOCKED_EXTENSIONS.copy()
        )

    def validate_path(self, file_path: str) -> bool:
        """验证文件路径是否安全可访问。

        执行以下检查：
        1. 解析为绝对路径，消除路径遍历序列（如 ../）
        2. 检查扩展名是否在黑名单中
        3. 检查路径是否在允许的路径范围内

        Args:
            file_path: 待验证的文件路径。

        Returns:
            路径安全返回 True，否则返回 False。
        """
        # 解析为绝对路径，消除 ../ 等遍历序列
        resolved = Path(file_path).resolve()

        # 检查扩展名是否在黑名单中
        if not self.validate_extension(file_path):
            return False

        # 如果设置了允许路径，检查是否在范围内
        if self.allowed_paths:
            in_allowed = any(
                str(resolved).startswith(str(Path(ap).resolve()))
                for ap in self.allowed_paths
            )
            if not in_allowed:
                logger.warning(
                    "路径不在允许范围内: %s（解析后: %s）", file_path, resolved
                )
                return False

        return True

    def validate_extension(self, file_path: str) -> bool:
        """验证文件扩展名是否允许。

        Args:
            file_path: 待验证的文件路径。

        Returns:
            扩展名合法返回 True，在黑名单中返回 False。
        """
        ext = Path(file_path).suffix.lower()
        if ext in self.blocked_extensions:
            logger.warning("文件扩展名被阻止: %s（扩展名: %s）", file_path, ext)
            return False
        return True

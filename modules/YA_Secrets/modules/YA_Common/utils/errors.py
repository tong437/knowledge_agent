"""
统一的错误与异常定义模块

约定：
- Error 类（数据类）：用于表示错误对象，通常作为函数返回值或 API 响应的一部分，需要支持可序列化（JSON 响应、日志记录）。
- Exception 类（异常类）：继承自 Python Exception，用于实际抛出和捕获异常，方便控制流程、错误传播。
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


# -------------------------------
# Error 数据对象
# -------------------------------
@dataclass
class Error:
    """错误对象，用于返回或序列化"""

    code: str  # 错误码，例如 "CONFIG_NOT_FOUND"
    message: str  # 错误信息
    details: Optional[Dict[str, Any]] = None  # 附加信息（可选）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details or {},
            }
        }


# -------------------------------
# Exception 基类
# -------------------------------
class MCPException(Exception):
    """所有 MCP 相关异常的基类"""

    def __init__(
        self, code: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")

    def to_error(self) -> Error:
        """转为 Error 对象（可返回给上层或序列化）"""
        return Error(code=self.code, message=self.message, details=self.details)


# -------------------------------
# 具体异常定义
# -------------------------------
class ConfigException(MCPException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("CONFIG_ERROR", message, details)


class DatabaseException(MCPException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("DATABASE_ERROR", message, details)


class HTTPException(MCPException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("HTTP_ERROR", message, details)


class ToolException(MCPException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("TOOL_ERROR", message, details)


class InternalException(MCPException):
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("INTERNAL_ERROR", message, details)

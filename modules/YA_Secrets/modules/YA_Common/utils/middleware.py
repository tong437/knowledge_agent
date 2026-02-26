"""
全局异常捕获中间件

用于在 MCP Server 中统一捕获 MCPException 与未处理的异常，
并将其转换为 JSON 格式的错误对象。
"""

import json
import sys
import traceback
from functools import wraps
from typing import Callable, Any, Coroutine

from .errors import MCPException, InternalException
from .logger import get_logger

logger = get_logger("middleware")


def exception_handler(func):
    """
    捕获 MCPException 和未知异常的装饰器
    - MCPException 会被转换为 JSON 错误输出（写到 stdout）。
    - 未知异常会被包装成 InternalException。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPException as e:
            error = e.to_error().to_dict()
            logger.error(f"MCPException: {e.code} - {e.message} | details={e.details}")

            sys.stdout.write(json.dumps(error, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            from utils.errors import InternalException

            ex = InternalException(str(e), {"traceback": traceback.format_exc()})
            error = ex.to_error().to_dict()
            logger.exception("Unhandled exception")
            sys.stdout.write(json.dumps(error, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    return wrapper


def async_exception_handler(func: Callable[..., Coroutine[Any, Any, Any]]):
    """
    捕获 MCPException 和未知异常的装饰器（异步版本）
    - MCPException 会被转换为 JSON 错误输出（写到 stdout）。
    - 未知异常会被包装成 InternalException。
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPException as e:
            error = e.to_error().to_dict()
            logger.error(f"MCPException: {e.code} - {e.message} | details={e.details}")
            sys.stdout.write(json.dumps(error, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            return None
        except Exception as e:
            ex = InternalException(str(e), {"traceback": traceback.format_exc()})
            error = ex.to_error().to_dict()
            logger.exception("Unhandled exception")
            sys.stdout.write(json.dumps(error, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            return None

    return wrapper

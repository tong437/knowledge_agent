"""
结构化日志记录和监控系统

提供结构化日志记录、性能监控和错误跟踪功能。
支持多种日志输出格式和日志级别配置。
"""

import logging
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from datetime import datetime
from functools import wraps
from contextlib import contextmanager


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器
    
    将日志记录格式化为结构化格式，便于解析和分析。
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 基本信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 添加位置信息
        if record.pathname:
            log_data["file"] = record.pathname
            log_data["line"] = record.lineno
            log_data["function"] = record.funcName
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # 格式化输出
        parts = [
            f"[{log_data['timestamp']}]",
            f"[{log_data['level']}]",
            f"[{log_data['logger']}]",
            log_data['message']
        ]
        
        # 添加位置信息（仅在DEBUG级别）
        if record.levelno == logging.DEBUG and "file" in log_data:
            parts.append(f"({log_data['file']}:{log_data['line']})")
        
        # 添加异常信息
        if "exception" in log_data:
            parts.append(f"\nException: {log_data['exception']['type']}: {log_data['exception']['message']}")
        
        return " ".join(parts)


class PerformanceMonitor:
    """性能监控器
    
    跟踪操作执行时间、调用次数和错误率。
    """
    
    def __init__(self):
        """初始化性能监控器"""
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("knowledge_agent.performance")
    
    def record_operation(self, operation: str, duration: float, success: bool = True) -> None:
        """记录操作性能指标
        
        Args:
            operation: 操作名称
            duration: 执行时间（秒）
            success: 是否成功
        """
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "total_duration": 0.0,
                "min_duration": float('inf'),
                "max_duration": 0.0,
                "success_count": 0,
                "error_count": 0,
            }
        
        metrics = self.metrics[operation]
        metrics["count"] += 1
        metrics["total_duration"] += duration
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标
        
        Args:
            operation: 操作名称，如果为None则返回所有指标
            
        Returns:
            性能指标字典
        """
        if operation:
            if operation not in self.metrics:
                return {}
            
            metrics = self.metrics[operation].copy()
            if metrics["count"] > 0:
                metrics["avg_duration"] = metrics["total_duration"] / metrics["count"]
                metrics["success_rate"] = metrics["success_count"] / metrics["count"]
            
            return {operation: metrics}
        
        # 返回所有指标
        result = {}
        for op, metrics in self.metrics.items():
            op_metrics = metrics.copy()
            if op_metrics["count"] > 0:
                op_metrics["avg_duration"] = op_metrics["total_duration"] / op_metrics["count"]
                op_metrics["success_rate"] = op_metrics["success_count"] / op_metrics["count"]
            result[op] = op_metrics
        
        return result
    
    def reset_metrics(self, operation: Optional[str] = None) -> None:
        """重置性能指标
        
        Args:
            operation: 操作名称，如果为None则重置所有指标
        """
        if operation:
            if operation in self.metrics:
                del self.metrics[operation]
        else:
            self.metrics.clear()
    
    def log_metrics(self, operation: Optional[str] = None) -> None:
        """记录性能指标到日志
        
        Args:
            operation: 操作名称，如果为None则记录所有指标
        """
        metrics = self.get_metrics(operation)
        
        if not metrics:
            self.logger.info("No performance metrics available")
            return
        
        self.logger.info("=" * 60)
        self.logger.info("Performance Metrics")
        self.logger.info("=" * 60)
        
        for op, op_metrics in metrics.items():
            self.logger.info(f"\nOperation: {op}")
            self.logger.info(f"  Total calls: {op_metrics['count']}")
            self.logger.info(f"  Success rate: {op_metrics.get('success_rate', 0):.2%}")
            self.logger.info(f"  Avg duration: {op_metrics.get('avg_duration', 0):.4f}s")
            self.logger.info(f"  Min duration: {op_metrics['min_duration']:.4f}s")
            self.logger.info(f"  Max duration: {op_metrics['max_duration']:.4f}s")
        
        self.logger.info("=" * 60)


class ErrorTracker:
    """错误跟踪器
    
    跟踪和统计系统错误。
    """
    
    def __init__(self):
        """初始化错误跟踪器"""
        self.errors: list[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        self.logger = logging.getLogger("knowledge_agent.errors")
    
    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """跟踪错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        error_type = type(error).__name__
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.errors.append(error_info)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 记录到日志
        self.logger.error(
            f"Error tracked: {error_type}: {error}",
            extra={"extra_fields": {"context": context}}
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要
        
        Returns:
            错误摘要字典
        """
        return {
            "total_errors": len(self.errors),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.errors[-10:] if self.errors else []
        }
    
    def clear_errors(self) -> None:
        """清除错误记录"""
        self.errors.clear()
        self.error_counts.clear()
    
    def log_error_summary(self) -> None:
        """记录错误摘要到日志"""
        summary = self.get_error_summary()
        
        self.logger.info("=" * 60)
        self.logger.info("Error Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Total errors: {summary['total_errors']}")
        
        if summary['error_counts']:
            self.logger.info("\nError counts by type:")
            for error_type, count in summary['error_counts'].items():
                self.logger.info(f"  {error_type}: {count}")
        
        self.logger.info("=" * 60)


# 全局监控实例
_performance_monitor: Optional[PerformanceMonitor] = None
_error_tracker: Optional[ErrorTracker] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_error_tracker() -> ErrorTracker:
    """获取全局错误跟踪器实例"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    structured: bool = True
) -> None:
    """设置日志系统
    
    Args:
        level: 日志级别
        log_file: 日志文件路径（可选）
        structured: 是否使用结构化格式
    """
    # 创建根日志记录器
    root_logger = logging.getLogger("knowledge_agent")
    root_logger.setLevel(level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 选择格式化器
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 添加文件处理器（如果指定）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    root_logger.info("Logging system initialized")


def monitor_performance(operation_name: Optional[str] = None):
    """性能监控装饰器
    
    Args:
        operation_name: 操作名称，如果为None则使用函数名
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_operation(op_name, duration, success)
        
        return wrapper
    return decorator


def track_errors(context: Optional[Dict[str, Any]] = None):
    """错误跟踪装饰器
    
    Args:
        context: 错误上下文信息
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tracker = get_error_tracker()
                error_context = context.copy() if context else {}
                error_context["function"] = func.__name__
                tracker.track_error(e, error_context)
                raise
        
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str):
    """性能监控上下文管理器
    
    Args:
        operation_name: 操作名称
    """
    monitor = get_performance_monitor()
    start_time = time.time()
    success = True
    
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.time() - start_time
        monitor.record_operation(operation_name, duration, success)


def log_system_info():
    """记录系统信息"""
    logger = logging.getLogger("knowledge_agent.system")
    
    logger.info("=" * 60)
    logger.info("System Information")
    logger.info("=" * 60)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("=" * 60)

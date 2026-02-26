from datetime import datetime
import sys
import logging
from pathlib import Path
from colorlog import ColoredFormatter
from logging.handlers import RotatingFileHandler

logging.getLogger("httpx").setLevel(logging.WARNING)


def load_logger_config():
    try:
        from .config import get_config

        return get_config().get("logging", {})
    except Exception:
        return {}


def setup_logger():
    cfg = load_logger_config()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # ------------- 控制台输出 -------------
    console_cfg = cfg.get("console", {})
    if console_cfg.get("enabled", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_cfg.get("level", "INFO").upper())

        color_format = (
            "%(log_color)s%(asctime)s | %(levelname)-8s | "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )

        console_format = ColoredFormatter(
            color_format,
            "%Y-%m-%d %H:%M:%S",
            log_colors={
                "TRACE": "cyan",
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # ------------- 文件输出 -------------
    file_cfg = cfg.get("file", {})
    if file_cfg.get("enabled", True):
        log_path = Path(
            datetime.now().strftime(file_cfg.get("path", "logs/%Y-%m-%d_%H-%M-%S.log"))
        )
        log_path.parent.mkdir(exist_ok=True, parents=True)

        handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=int(file_cfg.get("rotation_bytes", 10 * 1024 * 1024)),
            backupCount=int(file_cfg.get("retention_count", 7)),
            encoding="utf-8",
        )
        handler.setLevel(file_cfg.get("level", "INFO").upper())
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(file_format)
        logger.addHandler(handler)


def get_logger(name="mcp"):
    return logging.getLogger(name)


setup_logger()

if __name__ == "__main__":
    log = get_logger("demo")
    log.info("This is an info")
    log.error("This is an error")

"""
配置管理模块

用于加载和读取 YAML 配置文件，提供按层级获取配置的接口，
封装了常用的服务器相关配置（名称、描述、版本）的读取方法。
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path(os.getcwd()) / "config.yaml"
DEFAULT_NAME = "YA_Demo"
DEFAULT_AUTHOR = "YA Project"


class Config:
    def __init__(self, path: Path = CONFIG_PATH):
        self._path = path
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """加载 YAML 配置文件"""
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")
        with open(self._path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """按层级取配置，例如 get('server.name')"""
        parts = key.split(".")
        value: Any = self._config
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    def get_server_name(self) -> str:
        return self.get("server.name", DEFAULT_NAME)

    def get_server_author(self) -> str:
        return self.get("server.author", DEFAULT_AUTHOR)

    def get_server_description(self) -> str:
        return self.get("server.description", "")

    def get_server_version(self) -> str:
        return self.get("server.version", "0.0.1")


_config = Config()


def get_transport_type() -> str:
    """获取传输层类型"""
    return _config.get("transport.type", "stdio")


def is_default_server_name() -> bool:
    """检查当前服务器名称是否为默认名称"""
    return _config.get_server_name() == DEFAULT_NAME


def get_server_name() -> str:
    """获取服务器名称"""
    return _config.get_server_name()


def get_server_author() -> str:
    """获取服务器作者"""
    return _config.get_server_author()


def get_server_description() -> str:
    """获取服务器描述"""
    return _config.get_server_description()


def get_server_version() -> str:
    """获取服务器版本"""
    return _config.get_server_version()


def get_config(key: str, default: Any = None) -> Any:
    """按层级获取配置"""
    return _config.get(key, default)

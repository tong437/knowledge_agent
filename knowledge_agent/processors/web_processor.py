"""
网页数据源处理器模块，用于从网页中提取和处理内容。
"""

import re
import uuid
import time
import logging
from html import unescape
from html.parser import HTMLParser
from datetime import datetime
from typing import Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from .base_processor import BaseDataSourceProcessor
from ..models import DataSource, KnowledgeItem, SourceType
from ..core.exceptions import ProcessingError, ValidationError


logger = logging.getLogger(__name__)


class _HTMLTextExtractor(HTMLParser):
    """
    HTML 文本提取器，用于从 HTML 中提取纯文本内容。

    会自动跳过 script 和 style 标签中的内容。
    """

    def __init__(self):
        """初始化文本提取器。"""
        super().__init__()
        self._result: list = []
        self._skip = False
        # 需要跳过内容的标签集合
        self._skip_tags = {"script", "style"}

    def handle_starttag(self, tag: str, attrs) -> None:
        """处理开始标签，遇到 script/style 时标记跳过。"""
        if tag.lower() in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        """处理结束标签，离开 script/style 时取消跳过。"""
        if tag.lower() in self._skip_tags:
            self._skip = False

    def handle_data(self, data: str) -> None:
        """处理文本数据，跳过 script/style 中的内容。"""
        if not self._skip:
            self._result.append(data)

    def get_text(self) -> str:
        """获取提取的纯文本内容。"""
        return "".join(self._result)


class WebProcessor(BaseDataSourceProcessor):
    """
    网页数据源处理器，用于从网页 URL 获取并处理内容。

    支持 HTTP/HTTPS 协议的网页内容提取，自动清除 HTML 标签，
    保留纯文本内容。包含超时控制和重试机制。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化网页处理器。

        Args:
            config: 配置字典，可包含 web_scraping 子配置：
                - timeout: 请求超时时间（秒），默认 30
                - max_retries: 最大重试次数，默认 3
                - user_agent: 请求 User-Agent，默认 "KnowledgeAgent/1.0"
        """
        super().__init__()
        web_config = (config or {}).get("web_scraping", {})
        self.timeout: int = web_config.get("timeout", 30)
        self.max_retries: int = web_config.get("max_retries", 3)
        self.user_agent: str = web_config.get("user_agent", "KnowledgeAgent/1.0")

    def get_supported_types(self) -> List[SourceType]:
        """
        获取此处理器支持的数据源类型。

        Returns:
            List[SourceType]: 支持的数据源类型列表，仅包含 WEB 类型
        """
        return [SourceType.WEB]

    def validate(self, source: DataSource) -> bool:
        """
        验证网页数据源是否有效。

        检查数据源基本有效性、类型是否支持以及 URL 格式是否正确。

        Args:
            source: 要验证的数据源

        Returns:
            bool: 验证通过返回 True，否则返回 False
        """
        try:
            if not source.is_valid():
                self.logger.warning(f"Invalid data source: {source.path}")
                return False

            if source.source_type not in self.get_supported_types():
                self.logger.warning(
                    f"Unsupported source type {source.source_type} for {source.path}"
                )
                return False

            # 验证 URL 格式必须以 http:// 或 https:// 开头
            if not source.path.startswith(("http://", "https://")):
                self.logger.warning(f"Invalid URL format: {source.path}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating {source.path}: {str(e)}")
            return False

    def process(self, source: DataSource) -> KnowledgeItem:
        """
        处理网页数据源，生成知识条目。

        覆盖基类方法，跳过文件存在性检查，直接进行 URL 验证和内容提取。

        Args:
            source: 要处理的网页数据源

        Returns:
            KnowledgeItem: 生成的知识条目

        Raises:
            ProcessingError: 当网页无法处理时抛出
            ValidationError: 当数据源验证失败时抛出
        """
        try:
            # 验证数据源
            if not self.validate(source):
                raise ValidationError(
                    f"Data source validation failed: {source.path}"
                )

            # 提取元数据
            metadata = self.get_metadata(source)

            # 处理内容
            content = self._extract_content(source)

            # 生成标题
            title = self._generate_title(source, content)

            # 创建知识条目
            knowledge_item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                source_type=source.source_type,
                source_path=source.path,
                metadata=metadata,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            self.logger.info(f"Successfully processed: {source.path}")
            return knowledge_item

        except ValidationError:
            self.logger.error(f"Validation error for: {source.path}")
            raise
        except ProcessingError:
            self.logger.error(f"Processing error for: {source.path}")
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error processing {source.path}: {str(e)}",
                exc_info=True,
            )
            raise ProcessingError(
                f"Failed to process {source.path}: {str(e)}"
            ) from e

    def _fetch_html(self, url: str) -> str:
        """
        从 URL 获取 HTML 内容，包含重试机制。

        Args:
            url: 目标网页 URL

        Returns:
            str: 网页 HTML 内容

        Raises:
            ProcessingError: 当请求失败且重试耗尽时抛出
        """
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                request = Request(url, headers={"User-Agent": self.user_agent})
                response = urlopen(request, timeout=self.timeout)

                if response.status != 200:
                    raise ProcessingError(
                        f"HTTP error {response.status} for URL: {url}"
                    )

                # 检测编码
                content_type = response.headers.get("Content-Type", "")
                encoding = "utf-8"
                if "charset=" in content_type:
                    encoding = content_type.split("charset=")[-1].strip()

                return response.read().decode(encoding, errors="replace")

            except HTTPError as e:
                last_error = e
                self.logger.warning(
                    f"HTTP error {e.code} for {url} (attempt {attempt}/{self.max_retries})"
                )
                raise ProcessingError(
                    f"HTTP error {e.code} for URL: {url}"
                ) from e

            except URLError as e:
                last_error = e
                reason = str(e.reason)
                # 判断是否为超时错误
                if "timed out" in reason.lower():
                    self.logger.warning(
                        f"Timeout for {url} (attempt {attempt}/{self.max_retries})"
                    )
                    if attempt < self.max_retries:
                        time.sleep(1)
                        continue
                    raise ProcessingError(
                        f"Request timed out after {self.max_retries} retries for URL: {url}"
                    ) from e
                else:
                    self.logger.warning(
                        f"URL error for {url}: {reason} (attempt {attempt}/{self.max_retries})"
                    )
                    if attempt < self.max_retries:
                        time.sleep(1)
                        continue
                    raise ProcessingError(
                        f"Network error for URL {url}: {reason}"
                    ) from e

            except ProcessingError:
                raise

            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Error fetching {url}: {str(e)} (attempt {attempt}/{self.max_retries})"
                )
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue

        raise ProcessingError(
            f"Failed to fetch {url} after {self.max_retries} retries: {str(last_error)}"
        ) from last_error

    def _strip_html_tags(self, html: str) -> str:
        """
        清除 HTML 标签，保留纯文本。

        移除 script/style 标签及其内容，解析 HTML 实体，
        合并多余的空白字符。

        Args:
            html: 原始 HTML 字符串

        Returns:
            str: 清除标签后的纯文本
        """
        # 使用 HTMLParser 提取文本
        extractor = _HTMLTextExtractor()
        try:
            extractor.feed(html)
        except Exception:
            # 解析失败时回退到正则清除
            text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", "", text)
            text = unescape(text)
            return re.sub(r"\s+", " ", text).strip()

        text = extractor.get_text()
        # 处理 HTML 实体
        text = unescape(text)
        # 合并多余空白字符
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_content(self, source: DataSource) -> str:
        """
        从网页数据源中提取纯文本内容。

        获取网页 HTML 并清除标签，返回纯文本。

        Args:
            source: 网页数据源

        Returns:
            str: 提取的纯文本内容

        Raises:
            ProcessingError: 当内容提取失败时抛出
        """
        html = self._fetch_html(source.path)
        # 将原始 HTML 存储到 source 的 metadata 中，供标题提取使用
        source.metadata["_raw_html"] = html
        content = self._strip_html_tags(html)

        if not content:
            raise ProcessingError(f"No content extracted from URL: {source.path}")

        return content

    def _extract_title(self, html: str) -> str:
        """
        从 HTML 中提取标题。

        优先从 <title> 标签提取，若无则尝试 <h1> 标签。

        Args:
            html: 原始 HTML 字符串

        Returns:
            str: 提取的标题，若未找到则返回空字符串
        """
        # 尝试从 <title> 标签提取
        title_match = re.search(
            r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1).strip()
            title = self._strip_html_tags(title)
            if title:
                return title

        # 尝试从 <h1> 标签提取
        h1_match = re.search(
            r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL
        )
        if h1_match:
            title = h1_match.group(1).strip()
            title = self._strip_html_tags(title)
            if title:
                return title

        return ""

    def _generate_title(self, source: DataSource, content: str) -> str:
        """
        为网页知识条目生成标题。

        覆盖基类方法，优先使用 HTML 中的 title/h1 标签内容。

        Args:
            source: 数据源
            content: 提取的纯文本内容

        Returns:
            str: 生成的标题
        """
        # 尝试从缓存的原始 HTML 中提取标题
        raw_html = source.metadata.get("_raw_html", "")
        if raw_html:
            title = self._extract_title(raw_html)
            if title:
                return title

        # 回退：使用 URL 作为标题
        return source.path

    def get_metadata(self, source: DataSource) -> Dict[str, Any]:
        """
        提取网页特有的元数据。

        覆盖基类方法，返回 URL 相关的元数据而非文件系统元数据。

        Args:
            source: 网页数据源

        Returns:
            Dict[str, Any]: 包含 URL、来源类型和获取时间的元数据字典
        """
        metadata = {
            "url": source.path,
            "source_type": SourceType.WEB.value,
            "fetched_at": datetime.now().isoformat(),
            "user_agent": self.user_agent,
        }

        # 合并数据源自带的元数据（排除内部字段）
        for key, value in source.metadata.items():
            if not key.startswith("_"):
                metadata[key] = value

        return metadata

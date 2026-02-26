from dataclasses import field
import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from modules.YA_Common.types.mcp import MCPServerMetadata


class Metadata(BaseModel):
    """Structured metadata extracted from a repository.

    Fields intentionally mirror output from `scanner.scan_repo()`.
    """

    name: Optional[str]
    name_zh: Optional[str]
    author: Optional[str]
    description: Optional[str]
    description_zh: Optional[str]
    version: Optional[str]
    python_version: Optional[str]
    dependencies: List[str] = field(default_factory=list)


class RepoMetadata(BaseModel):
    """Typed container for a repository metadata snapshot stored in the registrar.

    Fields:
        - name: repository name
        - path: local path to the checked-out repo
        - last_seen: optional unix timestamp when the repo was last observed
        - metadata: mapping produced by the scanner (name/version/description/...)
    """

    name: str
    path: str
    last_seen: Optional[int]
    metadata: Metadata = field(default_factory=Metadata)


class ServerMetadata(BaseModel):
    name: str
    path: str
    port: int
    host: str
    last_seen: Optional[int] = None
    pid: Optional[int] = None

    repo: Optional[RepoMetadata] = None

    def get_metadata(self) -> MCPServerMetadata:
        return MCPServerMetadata(
            name=self.name,
            url=self.get_endpoint(),
            transport="sse",
        )

    def get_endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"

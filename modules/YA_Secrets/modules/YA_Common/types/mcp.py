from pydantic import BaseModel


class MCPServerMetadata(BaseModel):
    """MCP 服务器元数据"""

    name: str
    url: str
    transport: str

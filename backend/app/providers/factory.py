"""ProviderFactory 负责按需延迟创建并缓存 Provider 实例。

目前为了兼容旧的 MCP 调用链，依赖 mcp_service.client.MCPClient。
后续可以逐步替换为真正的 Provider 子类。"""

from __future__ import annotations

from typing import Dict

from mcp_service.client import MCPClient  # 依赖现有包
from mcp_service.config.settings import MCPSettings


class ProviderFactory:
    """简单 Provider 工厂，按名称创建 provider 并缓存。"""

    def __init__(self) -> None:
        self._mcp_client = MCPClient(MCPSettings.HOSTED_URL)
        self._cache: Dict[str, object] = {}

    def get(self, provider_name: str):  # 返回类型保持 object，兼容旧 manager
        if provider_name not in self._cache:
            self._cache[provider_name] = self._mcp_client.create_provider(provider_name)
        return self._cache[provider_name]


# 单例
factory = ProviderFactory() 
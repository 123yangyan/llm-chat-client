"""会话存储仓库包。默认使用内存实现。"""

from .in_memory import InMemorySessionRepo  # noqa: F401

# 默认单例实例
session_repo = InMemorySessionRepo() 
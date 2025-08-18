"""会话存储仓库包，可根据配置选择 InMemory 或 Redis 实现。"""

import os
from importlib import import_module

from backend.app.core.config import settings  # type: ignore

# 优先读取环境变量，避免测试环境动态修改时 settings 不刷新
redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)

if redis_url:
    try:
        import_module("backend.app.repositories.redis_repo")  # 确保已加载
        from backend.app.repositories.redis_repo import RedisSessionRepo  # type: ignore

        session_repo = RedisSessionRepo(redis_url)  # type: ignore
    except Exception as e:  # pragma: no cover
        # 回退到内存实现，打印警告
        print(f"警告：初始化 RedisSessionRepo 失败，使用 InMemoryRepo，错误: {e}")
        from .in_memory import InMemorySessionRepo  # type: ignore

        session_repo = InMemorySessionRepo()
else:
    from .in_memory import InMemorySessionRepo  # type: ignore

    session_repo = InMemorySessionRepo() 
"""统一 Redis 客户端。

在应用启动时即创建全局可复用的 Redis 连接，避免在各处重复初始化。
若未安装 redis 库，则在测试环境中可以通过 monkeypatch 提供伪模块。
"""

from __future__ import annotations

import os

# 测试场景可通过 monkeypatch 预先注入 `redis` 模块
import importlib


try:
    redis = importlib.import_module("redis")  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    redis = None  # type: ignore


def _create_client():  # noqa: D401
    """根据环境变量 REDIS_URL 创建 Redis 客户端。

    默认地址 ``redis://localhost:6379/0``，并开启 ``decode_responses=True`` 以返回 ``str``。
    若未安装 redis 库，则返回 ``None``；上层代码需自行处理。
    """

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    if redis is None:  # pragma: no cover
        return None
    return redis.Redis.from_url(url, decode_responses=True)


# 全局客户端实例
REDIS = _create_client() 
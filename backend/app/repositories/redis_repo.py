"""基于 Redis 的 SessionRepo 实现。"""

from __future__ import annotations

import json
from typing import List, Dict

try:
    import redis  # type: ignore
except ModuleNotFoundError:  # 在某些测试环境可用 monkeypatch 伪造
    redis = None  # type: ignore

from .session_base import SessionRepoBase


class RedisSessionRepo(SessionRepoBase):
    """使用 redis-py 简单存储会话历史。
    每个 session_id 对应一个 json 字符串。
    """

    def __init__(self, redis_url: str):
        if redis is None:
            raise RuntimeError("redis 库未安装，无法使用 RedisSessionRepo")
        # decode_responses=True 以便返回 str
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        data = self._client.get(session_id)
        if not data:
            return []
        try:
            return json.loads(data)
        except Exception:
            return []

    def save_history(self, session_id: str, history: List[Dict[str, str]]) -> None:
        self._client.set(session_id, json.dumps(history)) 
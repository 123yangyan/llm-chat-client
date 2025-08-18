"""基于 Redis 的 SessionRepo 实现。"""

from __future__ import annotations

import json
from typing import List, Dict

# ---------------------------------------------------------------------------
# 依赖基础设施层统一创建的 Redis 客户端
# ---------------------------------------------------------------------------

from backend.infra.redis_client import REDIS  # type: ignore

from .session_base import SessionRepoBase


class RedisSessionRepo(SessionRepoBase):
    """使用共用的 `backend.infra.redis_client.REDIS` 实例存储会话历史。
    会话数据以 JSON 字符串存储，键为 session_id。
    """

    def __init__(self, _redis_url: str | None = None):  # noqa: D401
        # 为保持向后兼容，保留 redis_url 参数但忽略。
        self._client = REDIS

    # ---------------------------------------------------------------------
    # SessionRepo 接口实现
    # ---------------------------------------------------------------------

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
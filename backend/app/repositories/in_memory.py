"""基于 Python dict 的 SessionRepo 实现。"""

from __future__ import annotations

from typing import Dict, List

from .session_base import SessionRepoBase


class InMemorySessionRepo(SessionRepoBase):
    def __init__(self) -> None:
        self._storage: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return list(self._storage.get(session_id, []))

    def save_history(self, session_id: str, history: List[Dict[str, str]]) -> None:
        self._storage[session_id] = history 
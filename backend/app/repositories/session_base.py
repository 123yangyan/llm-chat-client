"""Session 存储抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict


class SessionRepoBase(ABC):
    """会话历史仓库抽象"""

    @abstractmethod
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """获取指定 session 的消息历史，如不存在返回空列表"""

    @abstractmethod
    def save_history(self, session_id: str, history: List[Dict[str, str]]) -> None:
        """覆盖保存整段历史""" 
"""Provider 抽象基类。后续具体实现需继承本类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, AsyncGenerator


class BaseProvider(ABC):
    """LLM Provider 抽象接口。"""

    name: str  # 每个 Provider 的唯一名称（如 "silicon"）

    @abstractmethod
    def list_models(self) -> Dict[str, str]:
        """返回 {display_name: model_id} 列表"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False) -> str:
        """同步聊天接口"""

    async def chat_stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:  # noqa: D401,E501
        """默认不支持流式，可由子类重写"""
        raise NotImplementedError("stream is not implemented for this provider") 
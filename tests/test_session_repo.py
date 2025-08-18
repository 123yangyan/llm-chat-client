import pytest

from backend.app.repositories.in_memory import InMemorySessionRepo
from backend.app.manager import LLMManager


def test_session_history_accumulates(monkeypatch):
    """两次调用 chat_with_memory 应在 repo 中累积 4 条消息 (2 轮)"""
    repo = InMemorySessionRepo()
    manager = LLMManager(session_repo=repo)
    # 初始化 provider，但避免真实网络调用；monkeypatch mcp_client.chat
    manager.initialize_provider("silicon")

    def _fake_chat(provider, messages, model, stream=False, **kwargs):  # noqa: D401
        # 返回固定回复，省去真实模型调用
        return "assistant-reply"

    monkeypatch.setattr(manager.mcp_client, "chat", _fake_chat)

    session_id = "unit-test-session"
    manager.chat_with_memory(session_id=session_id, user_message="hello", model="dummy")
    assert len(repo.get_history(session_id)) == 2  # user + assistant

    manager.chat_with_memory(session_id=session_id, user_message="hi again", model="dummy")
    assert len(repo.get_history(session_id)) == 4 
from __future__ import annotations

from typing import List, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.logging_config import logger
from llm_api_project.manager import LLMManager

router = APIRouter(prefix="/api")

# 初始化 LLMManager
_manager = LLMManager()
try:
    from backend.app.core.config import settings  # type: ignore
    _default_provider = settings.DEFAULT_PROVIDER  # type: ignore[attr-defined]
except Exception:
    import os
    _default_provider = os.getenv("DEFAULT_PROVIDER", "silicon")

if not _manager.initialize_provider(_default_provider):
    logger.warning("无法初始化默认 provider '%s'", _default_provider)
else:
    logger.info("成功初始化 provider: %s", _default_provider)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: Optional[str] = None
    context_window: Optional[int] = None
    messages: Optional[List[Dict[str, str]]] = None
    model: str


class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None


class ProviderSwitchRequest(BaseModel):
    provider_name: str


@router.post("/provider/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """切换当前 Provider。"""
    if _manager.initialize_provider(request.provider_name):
        return {
            "status": "switched",
            "current_provider": request.provider_name,
            "models": _manager.get_available_models(),
        }
    raise HTTPException(status_code=400, detail=f"无法切换到 provider: {request.provider_name}")


@router.get("/models")
async def get_models():
    """返回当前 Provider 可用模型列表。"""
    return {"models": _manager.get_available_models()}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天接口，兼容带会话记忆和完整 messages 两种模式。"""
    if request.user_message is not None:
        session_id = request.session_id or _generate_session_id()
        result = _manager.chat_with_memory(
            session_id=session_id,
            user_message=request.user_message,
            model=request.model,
            context_window=request.context_window,
        )
    else:
        result = _manager.chat(messages=request.messages or [], model=request.model)

    if isinstance(result, dict) and result.get("status") == "success":
        return ChatResponse(response=result["response"], session_id=result.get("session_id"))

    logger.error("LLM 返回错误: %s", result)
    raise HTTPException(status_code=500, detail=result.get("error", "未知错误"))


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _generate_session_id() -> str:  # pragma: no cover
    import uuid

    return str(uuid.uuid4()) 
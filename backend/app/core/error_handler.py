from __future__ import annotations

"""FastAPI 全局异常处理模块。"""

import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.app.core.logging_config import logger


class ProviderError(Exception):
    """LLM Provider 相关错误。"""


_DEFAULT_HEADERS = {"Content-Type": "application/json; charset=utf-8"}


def _json(code: int, message: str, data: Any = None) -> JSONResponse:
    """统一 JSON 格式输出。"""
    return JSONResponse({"code": code, "message": message, "data": data}, status_code=code, headers=_DEFAULT_HEADERS)


def add_exception_handlers(app: FastAPI) -> None:
    """向 FastAPI 实例注册全局异常处理。"""

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def _validation_exc_handler(request: Request, exc: Exception):  # type: ignore[override]
        logger.error("ValidationError: %s\n%s", exc, traceback.format_exc())
        return _json(422, "请求参数验证失败", data=str(exc))

    @app.exception_handler(ProviderError)
    async def _provider_exc_handler(request: Request, exc: ProviderError):  # type: ignore[override]
        logger.error("ProviderError: %s", exc)
        return _json(500, f"ProviderError: {exc}")

    @app.exception_handler(Exception)
    async def _unhandled_exc_handler(request: Request, exc: Exception):  # type: ignore[override]
        logger.error("Unhandled Exception: %s\n%s", exc, traceback.format_exc())
        return _json(500, "服务器内部错误") 
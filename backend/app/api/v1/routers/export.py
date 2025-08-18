from __future__ import annotations

from typing import List, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.app.core.logging_config import logger

router = APIRouter(prefix="/api")


class ExportRequest(BaseModel):
    messages: List[Dict[str, str]]
    format: str
    title: str


@router.post("/export")
async def export_chat(request: ExportRequest):
    """导出聊天记录为 PDF 或 Word。"""
    try:
        from backend.app.services import export_service  # 延迟导入避免循环

        file_path = export_service.generate_export(
            messages=request.messages,
            title=request.title,
            fmt=request.format,
        )
        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=f"{request.title}.{request.format}",
        )
    except FileNotFoundError as exc:
        logger.exception("导出文件未找到: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    except ValueError as exc:
        logger.error("导出参数错误: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.exception("未知导出错误: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) 
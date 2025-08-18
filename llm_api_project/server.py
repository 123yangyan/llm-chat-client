from __future__ import annotations

"""简化后的服务器入口，仅负责创建 FastAPI 应用并提供 run_server。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.logging_config import logger


def create_app() -> FastAPI:
    """构建并返回 FastAPI 实例。"""

    from backend.app.api.v1.routers import chat as chat_router  # noqa: WPS433
    from backend.app.api.v1.routers import export as export_router  # noqa: WPS433

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router.router)
    app.include_router(export_router.router)
    return app


app = create_app()


def run_server() -> None:  # pragma: no cover
    """启动 Uvicorn 服务器。"""
    import uvicorn

    try:
        from backend.app.core.config import settings  # type: ignore

        host = settings.SERVER_HOST
        port = settings.SERVER_PORT
    except Exception as exc:  # pragma: no cover
        logger.warning("读取 Settings 失败，使用默认: %s", exc)
        host = "0.0.0.0"
        port = 8000

    logger.info("运行服务 host=%s port=%s", host, port)
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover
    run_server() 
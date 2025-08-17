"""运行后端 FastAPI 服务器。

使用新的入口 `backend.app.main:app` 启动，以便后续完全迁移路由后不用再次修改。"""

import uvicorn


def main():
    """CLI 入口"""
    # 从集中配置读取 host / port
    try:
        from backend.app.core.config import settings  # type: ignore
        host = settings.host
        port = settings.port
    except Exception:
        host = "0.0.0.0"
        port = 8000
    uvicorn.run("backend.app.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main() 
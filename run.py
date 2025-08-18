"""运行后端 FastAPI 服务器。

从集中配置读取 Settings 中的 SERVER_HOST/SERVER_PORT 并启动。
"""

import uvicorn
# 统一日志
from backend.app.core.logging_config import logger


def main():
    """CLI 入口。读取配置后启动 uvicorn。"""
    try:
        from backend.app.core.config import settings  # type: ignore
        host = settings.SERVER_HOST
        port = settings.SERVER_PORT
    except Exception as exc:  # pragma: no cover
        logger.warning("无法从 settings 读取主机/端口，使用默认值: %s", exc)
        host = "0.0.0.0"
        port = 8000

    logger.info("启动 API 服务，host=%s port=%s", host, port)
    uvicorn.run("backend.app.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main() 
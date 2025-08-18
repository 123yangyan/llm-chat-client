"""
统一日志配置模块。在 import 时即完成基础 logging 配置，并提供可直接引用的 ``logger`` 单例。

其它模块应统一：
    from backend.app.core.logging_config import logger

然后使用 ``logger.info/ debug / warning / error / exception`` 输出日志，禁止继续使用 ``print()``。
"""
import logging
import os
import sys

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "% (asctime)s | % (levelname)-8s | % (name)s:% (lineno)d | % (message)s".replace("% ", "%")


def _setup_logging() -> None:  # noqa: D401
    """配置根日志记录器并附加到 stdout。"""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # 避免重复添加 handler
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)


_setup_logging()

# 项目统一使用的 logger
logger = logging.getLogger("llm_api") 
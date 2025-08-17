"""应用统一配置模块（STEP 2）。

使用 pydantic-settings 读取 .env 文件并提供默认值，后续各模块应通过 `from backend.app.core.config import settings` 获取配置。
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # 项目根目录


class Settings(BaseSettings):
    # Web 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM 相关
    default_provider: str = "silicon"

    # 其他配置占位，可后续扩展

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 单例
settings = Settings() 
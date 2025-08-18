"""应用统一配置模块（STEP 2）。

使用 pydantic-settings 读取 .env 文件并提供默认值，后续各模块应通过 `from backend.app.core.config import settings` 获取配置。
"""

from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 修正：从当前文件位置向上查找，直到找到包含 .env 的目录
current_dir = Path(__file__).resolve().parent
while current_dir.parent != current_dir:  # 向上查找，直到到达根目录
    if (current_dir / ".env").exists():
        BASE_DIR = current_dir
        break
    current_dir = current_dir.parent
else:
    # 如果没找到，使用默认的项目根目录
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

env_path = BASE_DIR / ".env"
print(f"尝试加载配置文件: {env_path} (存在: {env_path.exists()})")

class Settings(BaseSettings):
    # Web 服务器
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # LLM 相关
    DEFAULT_PROVIDER: str = "silicon"
    # Redis 连接（可选，用于 SessionRepo）
    REDIS_URL: str | None = None

    # 会话上下文窗口
    memory_window: int = 5

    # 其他配置占位，可后续扩展

    model_config = SettingsConfigDict(
        env_file=str(env_path),  # 使用找到的 env_path
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 单例
settings = Settings()
print(f"配置加载结果: HOST={settings.SERVER_HOST}, PORT={settings.SERVER_PORT}, PROVIDER={settings.DEFAULT_PROVIDER}") 
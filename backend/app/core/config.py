"""核心配置模块，使用 Pydantic BaseSettings 统一读取 .env / 环境变量。"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 基础服务配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 默认 LLM 提供商
    default_provider: str = "silicon"

    # 上下文窗口默认值
    memory_window: int = 5

    # 其他可选配置
    wkhtmltopdf_path: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """FastAPI 依赖注入友好写法；缓存 Settings 实例。"""
    return Settings()


# 模块级别单例，方便现阶段直接引用
settings = get_settings() 
"""新的 FastAPI 入口。
目前为了保持系统稳定，仅简单地将现有 llm_api_project.server.app 暴露为 backend.app.main.app。
后续重构步骤会逐渐迁移路由与中间件到此处。"""

from llm_api_project.server import app as _legacy_app  # noqa: F401

# 对外暴露的 FastAPI 实例
app = _legacy_app 
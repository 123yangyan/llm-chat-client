"""新的 FastAPI 入口。
目前为了保持系统稳定，仅简单地将现有 llm_api_project.server.app 暴露为 backend.app.main.app。
后续重构步骤会逐渐迁移路由与中间件到此处。"""

# 直接导入已迁移到 backend.app.server 的 FastAPI 实例
from backend.app.server import app  # noqa: F401, F403

# 向下兼容旧变量名
_legacy_app = app

# 对外暴露的 FastAPI 实例
app = _legacy_app 
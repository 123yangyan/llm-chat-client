from __future__ import annotations

"""API v1 路由聚合模块。"""

from importlib import import_module

# 自动导入 chat 与 export 路由，以便 main.py 只需 include_router
for _mod in ("chat", "export"):
    import_module(f"backend.app.api.v1.routers.{_mod}") 
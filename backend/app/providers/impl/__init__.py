"""Provider 实现包装层（占位）。

当前阶段仅做路径过渡：保持代码逻辑在 `llm_api_project.*_provider`，
但对外暴露新的导入路径 `backend.app.providers.impl.*Provider`，
以便后续逐步迁移实现源码而不影响运行。"""

from importlib import import_module as _import


# 从旧包动态导入并重新导出类 --------------------------------------------------

_silicon_mod = _import("backend.app.providers.impl.silicon_provider")
SiliconProvider = _silicon_mod.SiliconProvider  # type: ignore

_google_mod = _import("backend.app.providers.impl.google_provider")
GoogleProvider = _google_mod.GoogleProvider  # type: ignore

_wisdom_mod = _import("backend.app.providers.impl.wisdom_gate_provider")
WisdomGateProvider = _wisdom_mod.WisdomGateProvider  # type: ignore


__all__ = [
    "SiliconProvider",
    "GoogleProvider",
    "WisdomGateProvider",
] 
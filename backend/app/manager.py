"""路径过渡：LLMManager 包装

在真正迁移实现前，保持旧模块 `llm_api_project.manager.LLMManager` 作为核心逻辑，
仅在新路径暴露同名符号，便于后续代码改动。"""

from importlib import import_module as _import


LLMManager = _import("llm_api_project.manager").LLMManager  # type: ignore

__all__: list[str] = ["LLMManager"] 
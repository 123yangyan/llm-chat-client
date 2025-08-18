import importlib, sys
# 兼容旧路径 llm_api_project.* → backend.app.*
legacy = importlib.import_module("backend.app")
sys.modules.setdefault("llm_api_project", legacy) 
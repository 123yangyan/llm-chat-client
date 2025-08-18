"""backend.app 包初始化。

提供兼容处理：
1. 当系统不存在 `llm_api_project` 时，映射到当前 `backend.app` 包。
2. 若旧包依然存在，则不做覆盖，避免破坏其内部相对导入。
"""

from __future__ import annotations

import importlib
import sys

# 若系统未安装旧包，则创建别名到 backend.app；否则保持原样
try:
    importlib.import_module("llm_api_project")
except ModuleNotFoundError:
    sys.modules["llm_api_project"] = importlib.import_module("backend.app") 
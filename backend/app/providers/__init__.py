"""Provider 包初始化，兼容旧 import 路径。"""

# ---------------------------------------------------------------------------
# 兼容性处理：
# 旧代码存在诸如 `from llm_api_project.silicon_provider import SiliconProvider`
# 的直接导入。为避免一次性全量替换，这里将旧路径指向当前实现。
# ---------------------------------------------------------------------------

import importlib
import sys

# legacy → real
_alias_map = {
    # legacy 路径重定向到新的实现文件
    "llm_api_project.silicon_provider": "backend.app.providers.impl.silicon_provider",
    "llm_api_project.google_provider": "backend.app.providers.impl.google_provider",
    "llm_api_project.wisdom_gate_provider": "backend.app.providers.impl.wisdom_gate_provider",
    # 新路径到实现文件
    "backend.app.providers.silicon_provider": "backend.app.providers.impl.silicon_provider",
    "backend.app.providers.google_provider": "backend.app.providers.impl.google_provider",
    "backend.app.providers.wisdom_gate_provider": "backend.app.providers.impl.wisdom_gate_provider",
}

# 注册别名
for legacy_path, real_path in _alias_map.items():
    try:
        module = importlib.import_module(real_path)
        sys.modules.setdefault(legacy_path, module)
    except ModuleNotFoundError:
        # 若实际模块尚未迁移，可忽略，等后续实现
        pass 
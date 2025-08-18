"""Provider 包初始化，兼容旧 import 路径。"""

# ---------------------------------------------------------------------------
# 兼容性处理：
# 旧代码存在诸如 `from llm_api_project.silicon_provider import SiliconProvider`
# 的直接导入。为避免一次性全量替换，这里将旧路径指向当前实现。
# ---------------------------------------------------------------------------

import importlib
import sys

_alias_map = {
    "llm_api_project.silicon_provider": "llm_api_project.silicon_provider",  # TODO: 后续迁移到 backend.app.providers.silicon_provider
    "llm_api_project.google_provider": "llm_api_project.google_provider",
    "llm_api_project.wisdom_gate_provider": "llm_api_project.wisdom_gate_provider",
}

# 注册别名
for legacy_path, real_path in _alias_map.items():
    try:
        module = importlib.import_module(real_path)
        sys.modules.setdefault(legacy_path, module)
    except ModuleNotFoundError:
        # 若实际模块尚未迁移，可忽略，等后续实现
        pass 
import importlib, sys, types, os

# --- 工具函数 --------------------------------------------------

def reload_repo_package():
    """重新加载 backend.app.repositories 并返回 session_repo"""
    if "backend.app.repositories" in sys.modules:
        del sys.modules["backend.app.repositories"]
    pkg = importlib.import_module("backend.app.repositories")
    return pkg.session_repo


def test_default_inmemory():
    """当未设置 REDIS_URL 时应使用 InMemorySessionRepo"""
    os.environ.pop("REDIS_URL", None)
    repo = reload_repo_package()
    from backend.app.repositories.in_memory import InMemorySessionRepo
    assert isinstance(repo, InMemorySessionRepo)


def test_redis_selection(monkeypatch):
    """设置 REDIS_URL 后应选择 RedisSessionRepo（使用假 redis 模块避免依赖）"""
    # 准备假 redis 模块
    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.store = {}
        def get(self, k):
            return self.store.get(k)
        def set(self, k, v):
            self.store[k] = v
    fake_redis = types.ModuleType("redis")
    fake_redis.Redis = types.SimpleNamespace(from_url=lambda *a, **kw: DummyClient())
    sys.modules["redis"] = fake_redis

    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    repo = reload_repo_package()
    from backend.app.repositories.redis_repo import RedisSessionRepo
    assert isinstance(repo, RedisSessionRepo) 
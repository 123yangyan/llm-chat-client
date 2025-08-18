import importlib
import sys
from types import ModuleType

from fastapi.testclient import TestClient


def test_root_returns_404():
    """后端不再挂载静态文件，GET / 应返回 404"""
    app_mod = importlib.import_module("backend.app.main")
    client = TestClient(app_mod.app)
    r = client.get("/")
    # FastAPI 对不存在路由默认为 404
    assert r.status_code == 404


def test_repo_uses_redis_when_url(monkeypatch):
    """设置 REDIS_URL 时应选择 RedisSessionRepo 实现"""
    # 构造假的 redis 模块，拦截 redis.Redis.from_url 调用
    fake_redis_mod = ModuleType("redis")

    class _FakeRedisClient:
        def __init__(self, *a, **kw):
            pass

        @classmethod
        def from_url(cls, url, decode_responses=True):  # noqa: D401
            return cls()

        # 确保 get/set 方法存在
        def get(self, key):
            return None

        def set(self, key, value):
            pass

    fake_redis_mod.Redis = _FakeRedisClient  # type: ignore
    sys.modules["redis"] = fake_redis_mod

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    # 重新加载 repositories 包以触发选择逻辑
    if "backend.app.repositories" in sys.modules:
        del sys.modules["backend.app.repositories"]
    repo_pkg = importlib.import_module("backend.app.repositories")

    assert repo_pkg.session_repo.__class__.__name__ == "RedisSessionRepo" 
import os
import importlib
import pytest
from fastapi.testclient import TestClient

# 确保在导入 server 前写好环境变量，避免读取到错误的默认值
os.environ.setdefault("DEFAULT_PROVIDER", "silicon")

# 动态导入以触发 server 中的初始化逻辑
server_module = importlib.import_module("backend.app.main")
app = getattr(server_module, "app")

client = TestClient(app)


def switch(provider: str):
    return client.post("/api/provider/switch", json={"provider_name": provider})


def test_models_endpoint():
    """默认 provider 下 /api/models 能正常返回列表"""
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "models" in data


def test_switch_google():
    """切换到 google provider 后 /api/models 更新且返回 200"""
    resp = switch("google")
    assert resp.status_code == 200
    out = resp.json()
    assert out.get("current_provider") == "google"
    # 再调用 /api/models
    models_resp = client.get("/api/models")
    assert models_resp.status_code == 200
    assert isinstance(models_resp.json().get("models"), (list, dict))


def test_invalid_provider():
    """切换到不存在的 provider 应返回 400"""
    resp = switch("foo_bar")
    assert resp.status_code == 400 
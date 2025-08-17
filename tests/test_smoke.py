import importlib


def test_import_server_module():
    """确保 FastAPI 服务器模块能够成功导入"""
    app_module = importlib.import_module("backend.app.main")
    assert hasattr(app_module, "app") 
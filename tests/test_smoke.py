import importlib


def test_import_server_module():
    """确保 FastAPI 服务器模块能够成功导入"""
    server_module = importlib.import_module("llm_api_project.server")
    assert hasattr(server_module, "app") 
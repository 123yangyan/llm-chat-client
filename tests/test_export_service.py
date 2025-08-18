import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
import importlib

# 动态导入 server 并获取 FastAPI app
server_module = importlib.import_module("backend.app.main")
app = getattr(server_module, "app")

client = TestClient(app)


def test_export_route_pdf(monkeypatch):
    """/api/export 应调用 generate_export 并返回文件内容 (PDF)"""
    # 伪造 generate_export 返回固定文件
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.write(b"dummy-pdf-content")
    temp_pdf.close()

    called = {}

    def _fake_generate_export(messages, title, fmt):  # noqa: D401
        called["fmt"] = fmt
        return temp_pdf.name

    monkeypatch.setattr("backend.app.services.export_service.generate_export", _fake_generate_export)

    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "format": "pdf",
        "title": "test",
    }
    resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200
    assert resp.content == b"dummy-pdf-content"
    assert called["fmt"] == "pdf"

    Path(temp_pdf.name).unlink(missing_ok=True)


def test_export_route_word(monkeypatch):
    """/api/export word 格式也能正常返回"""
    temp_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    temp_docx.write(b"dummy-docx")
    temp_docx.close()

    def _fake_generate_export(messages, title, fmt):
        return temp_docx.name

    monkeypatch.setattr("backend.app.services.export_service.generate_export", _fake_generate_export)

    payload = {
        "messages": [{"role": "assistant", "content": "hi"}],
        "format": "word",
        "title": "doc",
    }
    resp = client.post("/api/export", json=payload)
    assert resp.status_code == 200
    assert resp.content == b"dummy-docx"

    Path(temp_docx.name).unlink(missing_ok=True) 
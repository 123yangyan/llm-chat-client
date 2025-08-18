"""负责将聊天记录导出为 Word 或 PDF。"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from typing import List, Dict

import pdfkit
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.app.core.logging_config import logger
from backend.app.services.word_styles import create_document, append_messages

# -------------------- 内部工具 --------------------

def _get_wkhtmltopdf_path() -> str:
    """智能查找 ``wkhtmltopdf`` 可执行文件路径。

    优先顺序：

    1. backend/app/bin/             （历史位置）
    2. 项目根目录 bin/             （推荐放置位置）
    3. 系统 PATH (where / which)
    4. C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe

    如果都找不到则抛出 ``FileNotFoundError``。
    """

    import shutil

    current_dir = os.path.dirname(__file__)

    # 1) backend/app/bin/
    legacy_path = os.path.abspath(os.path.join(current_dir, "..", "bin", "wkhtmltopdf.exe"))
    if os.path.exists(legacy_path):
        return legacy_path

    # 2) 项目根目录 bin/
    project_root_bin = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "bin", "wkhtmltopdf.exe"))
    if os.path.exists(project_root_bin):
        return project_root_bin

    # 3) 系统 PATH
    which_result = shutil.which("wkhtmltopdf")
    if which_result:
        return which_result

    # 4) 默认安装路径（Windows）
    program_files_path = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    if os.path.exists(program_files_path):
        return program_files_path

    raise FileNotFoundError("未找到 wkhtmltopdf，可执行文件，请确认已安装或将其放置到项目根 bin 目录")

# PDF 选项常量
PDF_OPTIONS = {
    "page-size": "A4",
    "margin-top": "20mm",
    "margin-right": "20mm",
    "margin-bottom": "20mm",
    "margin-left": "20mm",
    "encoding": "UTF-8",
    "custom-header": [("Accept-Encoding", "gzip")],
    "no-outline": None,
    "quiet": "",
}

# -------------------- Word 生成 --------------------

def _generate_word(messages: List[Dict[str, str]], title: str, temp_file_path: str) -> None:
    """使用 word_styles 封装创建 Word 文档。"""
    doc = create_document(title)
    append_messages(doc, messages)
    doc.save(temp_file_path)

# -------------------- PDF 生成 --------------------

def _generate_pdf(messages: List[Dict[str, str]], title: str, temp_file_path: str) -> None:
    # 利用 Jinja2 模板渲染
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("export.html.j2")
    html_content = template.render(title=title, messages=messages, now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    wkhtmltopdf_path = _get_wkhtmltopdf_path()
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    pdfkit.from_string(html_content, temp_file_path, options=PDF_OPTIONS, configuration=config)

# -------------------- Public API --------------------

def generate_export(messages: List[Dict[str, str]], title: str, fmt: str) -> str:
    """生成导出文件并返回文件路径。"""
    fmt = fmt.lower()
    if fmt not in {"word", "pdf"}:
        raise ValueError("不支持的导出格式")

    suffix = ".docx" if fmt == "word" else ".pdf"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.close()  # 我们将手动写入

    try:
        if fmt == "word":
            _generate_word(messages, title, temp_file.name)
        else:
            _generate_pdf(messages, title, temp_file.name)
    except Exception as exc:
        logger.exception("导出失败: %s", exc)
        raise

    return temp_file.name 
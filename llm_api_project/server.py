from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
# 注意：为了与新的统一配置系统兼容，优先尝试从 backend.app.core.config 导入 settings；
# 若导入失败则回退到环境变量，确保兼容性。
import os
import sys
from pathlib import Path
from backend.app.core.logging_config import logger
try:
    from backend.app.core.config import settings as _app_settings  # noqa: F401
except Exception:  # pragma: no cover
    _app_settings = None
from dotenv import load_dotenv, find_dotenv
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
import pdfkit
import tempfile
from datetime import datetime
import uuid

# 查找并加载.env文件
env_path = find_dotenv()
if env_path:
    logger.info("找到.env文件: %s", env_path)
    load_dotenv(env_path)
else:
    logger.warning("未找到.env文件")

try:
    from llm_api_project.manager import LLMManager  # 改为绝对导入
except ImportError as e:
    logger.exception("无法导入LLMManager: %s", e)
    logger.error("请确认项目结构是否正确")
    raise

# 添加调试信息
if _app_settings is not None:
    logger.info("成功加载配置：HOST=%s, PORT=%s", _app_settings.SERVER_HOST, _app_settings.SERVER_PORT)
else:
    logger.warning("未能加载 backend.app.core.config，将使用环境变量")
    logger.warning("环境变量：SERVER_HOST=%s, SERVER_PORT=%s", os.getenv('SERVER_HOST'), os.getenv('SERVER_PORT'))

import uvicorn

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建LLM管理器实例
llm_manager = LLMManager()
# 读取默认提供商
if _app_settings is not None:
    default_provider = _app_settings.DEFAULT_PROVIDER  # type: ignore[attr-defined]
else:
    default_provider = os.getenv("DEFAULT_PROVIDER", "silicon")
if not llm_manager.initialize_provider(default_provider):
    logger.warning("无法初始化默认提供商 '%s'", default_provider)
else:
    logger.info("成功初始化提供商: %s", default_provider)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None  # 客户端的会话ID，可选
    user_message: Optional[str] = None  # 本轮用户输入
    context_window: Optional[int] = None  # 携带上下文轮数
    messages: Optional[List[Dict[str, str]]] = None  # 向后兼容：完整消息列表
    model: str

class ChatResponse(BaseModel):
    response: str
    session_id: Optional[str] = None

class ProviderSwitchRequest(BaseModel):
    provider_name: str

@app.post("/api/provider/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """切换LLM提供商"""
    success = llm_manager.initialize_provider(request.provider_name)
    if success:
        return {
            "status": "switched",
            "current_provider": request.provider_name,
            "models": llm_manager.get_available_models()
        }
    else:
        raise HTTPException(status_code=400, detail=f"无法切换到提供商: {request.provider_name}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        logger.info("收到聊天请求: %s", request)
        # 根据是否提供 user_message 决定使用会话记忆模式或兼容旧模式
        if request.user_message is not None:
            session_id = request.session_id or str(uuid.uuid4())
            result = llm_manager.chat_with_memory(
                session_id=session_id,
                user_message=request.user_message,
                model=request.model,
                context_window=request.context_window,
            )
        else:
            result = llm_manager.chat(
                messages=request.messages or [],
                model=request.model,
            )
        logger.debug("LLM返回结果: %s", result)
        
        if isinstance(result, dict) and result.get("status") == "success":
            return ChatResponse(response=result["response"], session_id=result.get("session_id"))
        elif isinstance(result, dict) and "error" in result:
            logger.error("LLM返回错误: %s", result)
            return JSONResponse(status_code=500, content=result)
        else:
            logger.error("未知的响应格式: %s", result)
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": "未知的响应格式"}
            )
    except Exception as e:
        import traceback
        logger.exception("发生异常: %s", e)
        logger.error("详细错误信息:\n%s", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@app.get("/api/models")
async def get_models():
    """获取可用模型列表"""
    try:
        models = llm_manager.get_available_models()
        return {"models": models}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

class ExportRequest(BaseModel):
    messages: List[Dict[str, str]]
    format: str
    title: str

# 获取wkhtmltopdf路径
def get_wkhtmltopdf_path():
    """获取wkhtmltopdf可执行文件的路径"""
    # 首先检查项目本地bin目录
    local_path = os.path.join(os.path.dirname(__file__), 'bin', 'wkhtmltopdf.exe')
    if os.path.exists(local_path):
        return local_path
    
    # 检查系统PATH中是否存在wkhtmltopdf
    if os.system('where wkhtmltopdf > nul 2>&1') == 0:
        return 'wkhtmltopdf'
    
    # 检查默认安装路径
    program_files_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if os.path.exists(program_files_path):
        return program_files_path
    
    raise FileNotFoundError("未找到wkhtmltopdf，请确保已安装或将其放置在正确位置")

# 配置PDF选项
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '20mm',
    'margin-right': '20mm',
    'margin-bottom': '20mm',
    'margin-left': '20mm',
    'encoding': 'UTF-8',
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None,
    'quiet': ''
}

@app.post("/api/export")
async def export_chat(request: ExportRequest):
    """导出聊天记录"""
    # 使用新的导出服务
    try:
        from backend.app.services import export_service  # 延迟导入避免循环

        file_path = export_service.generate_export(
            messages=request.messages,
            title=request.title,
            fmt=request.format,
        )

        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=f"{request.title}.{request.format}",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 前端静态资源不再由后端提供，后端仅暴露 API。
# app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

def run_server():
    """启动服务器的函数"""
    logger.info("启动 API 服务器（无前端静态文件挂载）...")
    # 启动服务器
    host = _app_settings.SERVER_HOST if _app_settings is not None else os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(_app_settings.SERVER_PORT if _app_settings is not None else os.getenv("SERVER_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server() 
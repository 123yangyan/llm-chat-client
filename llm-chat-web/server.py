from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# 查找并加载.env文件
env_path = find_dotenv()
if env_path:
    print(f"找到.env文件: {env_path}")
    load_dotenv(env_path)
else:
    print("警告: 未找到.env文件")

try:
    # 获取当前文件的目录
    current_dir = Path(__file__).parent
    # 获取项目根目录
    project_root = current_dir.parent
    # 获取manager.py的路径
    manager_path = project_root / "llm-api-project"
    if str(manager_path) not in sys.path:
        sys.path.append(str(manager_path))
    
    from manager import LLMManager
except ImportError as e:
    print(f"错误：无法导入LLMManager: {e}")
    print("请确认项目结构是否正确")
    raise

import uvicorn
import webbrowser
from threading import Timer

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
# 从环境变量读取默认提供商，如果未设置，则默认为 'silicon'
default_provider = os.getenv("DEFAULT_PROVIDER", "silicon")
if not llm_manager.initialize_provider(default_provider):
    print(f"警告：无法初始化默认提供商'{default_provider}'")
else:
    print(f"成功初始化提供商: {default_provider}")

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str

class ChatResponse(BaseModel):
    response: str

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
        print(f"收到聊天请求: {request}")
        result = llm_manager.chat(
            messages=request.messages,
            model=request.model
        )
        print(f"LLM返回结果: {result}")
        
        if isinstance(result, dict) and result.get("status") == "success":
            return ChatResponse(response=result["response"])
        elif isinstance(result, dict) and "error" in result:
            print(f"LLM返回错误: {result}")
            return JSONResponse(status_code=500, content=result)
        else:
            print(f"未知的响应格式: {result}")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "error": "未知的响应格式"}
            )
    except Exception as e:
        import traceback
        print(f"发生异常: {str(e)}")
        print("详细错误信息:")
        print(traceback.format_exc())
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

# 获取前端文件的路径
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

# 挂载静态文件
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

def open_browser():
    """在浏览器中打开应用"""
    webbrowser.open('http://localhost:8000')

if __name__ == "__main__":
    print("启动服务器...")
    print(f"前端目录: {FRONTEND_DIR}")
    
    # 延迟1秒后打开浏览器
    Timer(1.0, open_browser).start()
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 
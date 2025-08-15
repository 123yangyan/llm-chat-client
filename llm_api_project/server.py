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
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
import pdfkit
import tempfile
from datetime import datetime
from llm_api_project import config

# 查找并加载.env文件
env_path = find_dotenv()
if env_path:
    print(f"找到.env文件: {env_path}")
    load_dotenv(env_path)
else:
    print("警告: 未找到.env文件")

try:
    from .manager import LLMManager
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

class ModelSwitchRequest(BaseModel):
    model: str

@app.post("/api/provider/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """切换LLM提供商"""
    print("\n=== 切换供应商请求 ===")
    print(f"当前供应商: {llm_manager.current_provider.__class__.__name__ if llm_manager.current_provider else 'None'}")
    print(f"目标供应商: {request.provider_name}")
    
    success = llm_manager.initialize_provider(request.provider_name)
    
    if success:
        models = llm_manager.get_available_models()
        print("\n=== 切换成功 ===")
        print(f"新供应商: {request.provider_name}")
        print(f"默认模型: {llm_manager.current_model}")
        print(f"可用模型列表: {models}")
        print("================\n")
        return {
            "status": "switched",
            "current_provider": request.provider_name,
            "current_model": llm_manager.current_model,
            "models": models
        }
    else:
        print(f"\n=== 切换失败 ===")
        print(f"无法初始化供应商: {request.provider_name}")
        print("================\n")
        raise HTTPException(status_code=400, detail=f"无法切换到提供商: {request.provider_name}")

@app.post("/api/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换当前使用的模型"""
    try:
        print("\n=== 模型切换请求 ===")
        print(f"当前模型: {llm_manager.current_model}")
        print(f"目标模型: {request.model}")

        # 验证模型是否存在
        available_models = llm_manager.get_available_models()
        if request.model not in available_models.values():
            print("\n=== 切换失败 ===")
            print(f"错误: 模型 {request.model} 不存在")
            print("可用模型列表:")
            for name, model_id in available_models.items():
                print(f"- {name}: {model_id}")
            print("================\n")
            raise HTTPException(
                status_code=400,
                detail=f"模型 {request.model} 不存在"
            )

        # 更新当前模型
        old_model = llm_manager.current_model
        llm_manager.current_model = request.model

        print("\n=== 切换成功 ===")
        print(f"从 {old_model} 切换到 {request.model}")
        print("================\n")

        return {
            "status": "success",
            "previous_model": old_model,
            "current_model": request.model,
            "message": "模型切换成功"
        }

    except Exception as e:
        print("\n=== 切换失败 ===")
        print(f"错误信息: {str(e)}")
        print("================\n")
        raise HTTPException(
            status_code=500,
            detail=f"模型切换失败: {str(e)}"
        )

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 检查模型切换
        if request.model != llm_manager.current_model:
            print("\n=== 模型切换 ===")
            print(f"从 {llm_manager.current_model} 切换到 {request.model}")
            llm_manager.current_model = request.model
            print("================\n")

        # 复制一份消息，避免修改原始数据
        messages = list(request.messages)
        # 如果第一个消息不是 system，则插入
        if not messages or messages[0].get("role") != "system":
            system_prompt = config.ACTIVE_SYSTEM_PROMPT
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})

        print("=== 向大模型发送的原始请求 ===")
        print(f"当前模型: {request.model}")
        print("消息内容:")
        for msg in messages:
            print(f"- [{msg['role']}]: {msg['content']}")
        print("==========================")

        result = llm_manager.chat(
            messages=messages,
            model=request.model
        )

        print("=== 大模型返回的原始响应 ===")
        print(result)
        print("==========================")

        if isinstance(result, dict) and result.get("status") == "success":
            return ChatResponse(response=result["response"])
        elif isinstance(result, dict) and "error" in result:
            return JSONResponse(status_code=500, content=result)
        else:
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
        print("\n=== 获取模型列表 ===")
        print(f"当前供应商: {llm_manager.current_provider.__class__.__name__ if llm_manager.current_provider else 'None'}")
        print(f"当前模型: {llm_manager.current_model}")
        
        models = llm_manager.get_available_models()
        print(f"可用模型数量: {len(models)}")
        print(f"模型列表: {models}")
        print("==================\n")
        
        return {
            "status": "success",
            "current_provider": llm_manager.current_provider.__class__.__name__ if llm_manager.current_provider else None,
            "current_model": llm_manager.current_model,
            "models": models
        }
    except Exception as e:
        print("\n=== 获取模型列表失败 ===")
        print(f"错误信息: {str(e)}")
        print("=====================\n")
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
    try:
        if request.format not in ['word', 'pdf']:
            raise HTTPException(status_code=400, detail="不支持的导出格式")

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{request.format}') as temp_file:
            if request.format == 'word':
                # 创建Word文档
                doc = Document()
                
                # 设置文档基本样式
                section = doc.sections[0]
                section.page_width = Cm(21)  # A4纸宽度
                section.page_height = Cm(29.7)  # A4纸高度
                section.left_margin = Cm(2.54)
                section.right_margin = Cm(2.54)
                section.top_margin = Cm(2.54)
                section.bottom_margin = Cm(2.54)
                
                # 创建并应用标题样式
                title_style = doc.styles.add_style('CustomTitle', WD_STYLE_TYPE.PARAGRAPH)
                title_style.font.name = '微软雅黑'
                title_style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
                title_style.font.size = Pt(24)
                title_style.font.bold = True
                title_style.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                title_style.paragraph_format.space_after = Pt(20)
                
                # 添加标题
                title = doc.add_paragraph(request.title, style='CustomTitle')
                
                # 添加时间
                time_paragraph = doc.add_paragraph()
                time_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                time_run = time_paragraph.add_run(f"创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                time_run.font.name = '微软雅黑'
                time_run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
                time_run.font.size = Pt(10)
                time_run.font.color.rgb = RGBColor(128, 128, 128)
                
                # 添加分隔线
                separator = doc.add_paragraph()
                separator.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                separator_run = separator.add_run('=' * 40)
                separator_run.font.size = Pt(12)
                separator_run.font.color.rgb = RGBColor(200, 200, 200)
                
                # 创建消息样式
                message_style = doc.styles.add_style('MessageStyle', WD_STYLE_TYPE.PARAGRAPH)
                message_style.font.name = '微软雅黑'
                message_style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
                message_style.font.size = Pt(11)
                message_style.paragraph_format.space_before = Pt(12)
                message_style.paragraph_format.space_after = Pt(12)
                message_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
                
                # 添加消息内容
                for msg in request.messages:
                    # 添加角色
                    role_paragraph = doc.add_paragraph(style='MessageStyle')
                    role_run = role_paragraph.add_run(f"{msg['role']}：")
                    role_run.bold = True
                    role_run.font.color.rgb = RGBColor(0, 0, 0)
                    
                    # 添加内容
                    content_paragraph = doc.add_paragraph(style='MessageStyle')
                    content_run = content_paragraph.add_run(msg['content'])
                    content_run.font.color.rgb = RGBColor(51, 51, 51)
                    
                    # 添加间隔
                    doc.add_paragraph(style='MessageStyle')
                
                # 保存文档
                doc.save(temp_file.name)
                
            else:  # PDF
                # 创建HTML内容
                html_content = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        @font-face {{
                            font-family: 'Microsoft YaHei';
                            src: local('Microsoft YaHei');
                        }}
                        body {{
                            font-family: 'Microsoft YaHei', Arial, sans-serif;
                            margin: 40px;
                            line-height: 1.6;
                        }}
                        .title {{
                            text-align: center;
                            font-size: 24px;
                            margin-bottom: 10px;
                            font-weight: bold;
                        }}
                        .time {{
                            text-align: center;
                            font-size: 12px;
                            color: #666;
                            margin-bottom: 20px;
                        }}
                        .divider {{
                            border-top: 1px solid #ccc;
                            margin: 20px 0;
                        }}
                        .role {{
                            font-weight: bold;
                            margin-top: 15px;
                            color: #000;
                        }}
                        .content {{
                            margin: 5px 0 15px 20px;
                            color: #333;
                        }}
                    </style>
                </head>
                <body>
                    <div class="title">{request.title}</div>
                    <div class="time">创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    <div class="divider"></div>
                """
                
                for msg in request.messages:
                    html_content += f"""
                    <div class="role">{msg['role']}：</div>
                    <div class="content">{msg['content']}</div>
                    """
                
                html_content += "</body></html>"
                
                # 获取wkhtmltopdf路径
                wkhtmltopdf_path = get_wkhtmltopdf_path()
                
                # 配置wkhtmltopdf
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                
                # 使用pdfkit生成PDF
                pdfkit.from_string(
                    html_content,
                    temp_file.name,
                    options=PDF_OPTIONS,
                    configuration=config
                )
            
            # 返回文件
            return FileResponse(
                temp_file.name,
                media_type='application/octet-stream',
                filename=f"{request.title}.{request.format}"
            )
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取前端文件的路径
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "llm-chat-web")

# 挂载静态文件
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

def open_browser():
    """在浏览器中打开应用"""
    webbrowser.open('http://localhost:8000')

def run_server():
    """启动服务器的函数"""
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

if __name__ == "__main__":
    run_server() 
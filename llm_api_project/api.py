from fastapi import FastAPI, HTTPException
import pdfkit
from typing import List, Dict
import tempfile
from pathlib import Path
import os
import logging
from fastapi.responses import Response, JSONResponse
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 检查wkhtmltopdf是否安装
def check_wkhtmltopdf():
    try:
        path_wkhtmltopdf = os.environ.get('WKHTMLTOPDF_PATH', None)
        if path_wkhtmltopdf:
            config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        else:
            config = pdfkit.configuration()
        return config
    except Exception as e:
        logger.error(f"wkhtmltopdf配置错误: {str(e)}")
        return None

# PDF导出配置
pdf_options = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'custom-header': [
        ('Accept-Encoding', 'gzip')
    ],
    'no-outline': None,
    'enable-local-file-access': None,
    'quiet': None
}

def generate_chat_html(messages: List[Dict]) -> str:
    """生成聊天记录的HTML"""
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { 
                font-family: Arial, "Microsoft YaHei", sans-serif; 
                line-height: 1.6; 
                margin: 20px;
                background-color: white;
            }
            .message { 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                page-break-inside: avoid;
            }
            .user { 
                background-color: #f0f0f0; 
            }
            .assistant { 
                background-color: #f7f7f8; 
            }
            .role { 
                font-weight: bold; 
                margin-bottom: 5px;
                color: #333;
            }
            .content { 
                white-space: pre-wrap;
                word-break: break-word;
            }
            @page {
                margin: 1cm;
            }
        </style>
    </head>
    <body>
    """
    
    for msg in messages:
        role_class = "user" if msg["role"] == "我" else "assistant"
        role_text = "用户" if msg["role"] == "我" else "AI助手"
        html += f"""
        <div class="message {role_class}">
            <div class="role">{role_text}:</div>
            <div class="content">{msg["content"]}</div>
        </div>
        """
    
    html += "</body></html>"
    return html

@app.post("/api/export")
async def export_chat(data: dict):
    try:
        messages = data.get("messages", [])
        format = data.get("format", "pdf")
        title = data.get("title", "chat_export")
        
        if not messages:
            return JSONResponse(
                status_code=400,
                content={"detail": "没有可导出的内容"}
            )

        if format == "pdf":
            # 获取wkhtmltopdf配置
            config = check_wkhtmltopdf()
            if config is None:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "PDF生成工具未正确配置"}
                )

            # 生成HTML内容
            html_content = generate_chat_html(messages)
            
            try:
                # 创建临时HTML文件
                with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as temp_html:
                    temp_html.write(html_content)
                    temp_html_path = temp_html.name
                
                # 创建临时PDF文件
                temp_pdf_path = tempfile.mktemp(suffix='.pdf')
                
                try:
                    # 转换HTML为PDF
                    pdfkit.from_file(
                        temp_html_path, 
                        temp_pdf_path, 
                        options=pdf_options,
                        configuration=config
                    )
                    
                    # 读取生成的PDF
                    with open(temp_pdf_path, 'rb') as pdf_file:
                        pdf_content = pdf_file.read()
                    
                    return Response(
                        content=pdf_content,
                        media_type="application/pdf",
                        headers={
                            "Content-Disposition": f'attachment; filename="{title}.pdf"'
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"PDF生成失败: {str(e)}\n{traceback.format_exc()}")
                    raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
                    
                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(temp_html_path):
                            os.unlink(temp_html_path)
                        if os.path.exists(temp_pdf_path):
                            os.unlink(temp_pdf_path)
                    except Exception as e:
                        logger.error(f"清理临时文件失败: {str(e)}")
                        
            except Exception as e:
                logger.error(f"创建临时文件失败: {str(e)}\n{traceback.format_exc()}")
                raise HTTPException(status_code=500, detail=f"创建临时文件失败: {str(e)}")
            
        else:
            raise HTTPException(status_code=400, detail="不支持的导出格式")
            
    except Exception as e:
        logger.error(f"导出失败: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# ... 其他现有的API代码 ... 
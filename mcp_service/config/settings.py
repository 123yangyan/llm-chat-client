"""
MCP Settings

MCP服务的配置设置。
"""

import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class MCPSettings:
    """MCP服务的配置类"""
    
    # MCP服务的URL，优先从环境变量获取，如果没有则使用默认值
    HOSTED_URL = os.getenv('MCP_HOSTED_URL', 'https://mcp-default-url.modelscope.cn/sse')
    
    # 日志配置
    LOG_LEVEL = os.getenv('MCP_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 请求超时设置（秒）
    REQUEST_TIMEOUT = int(os.getenv('MCP_REQUEST_TIMEOUT', '30'))
    
    # 重试设置
    MAX_RETRIES = int(os.getenv('MCP_MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('MCP_RETRY_DELAY', '1')) 
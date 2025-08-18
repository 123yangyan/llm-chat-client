import os
import yaml
from dotenv import load_dotenv
from datetime import date
from typing import Dict, Any

# ---------------------------------------------------------------------------
# 获取项目根目录：自当前文件向上递归查找，直到发现 config.yml
# ---------------------------------------------------------------------------

current_dir = os.path.abspath(__file__)
while True:
    current_dir = os.path.dirname(current_dir)
    candidate = os.path.join(current_dir, "config.yml")
    if os.path.exists(candidate):
        BASE_DIR = current_dir
        break
    if current_dir == os.path.dirname(current_dir):  # 已到根目录
        BASE_DIR = os.getcwd()
        break

# 1. 加载 .env 文件中的环境变量
load_dotenv(os.path.join(BASE_DIR, '.env'))

# 2. 加载 yaml 配置文件
config_path = os.path.join(BASE_DIR, 'config.yml')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = yaml.safe_load(f)
except FileNotFoundError:
    _config = {}

# 3. 将配置项整理成易于访问的变量，可以提供默认值

# 服务配置
SERVER_HOST = _config.get('server', {}).get('host', '0.0.0.0')
SERVER_PORT = _config.get('server', {}).get('port', 8000)

# LLM 配置
LLM_CONFIG = _config.get('llm', {})
DEFAULT_PROVIDER = LLM_CONFIG.get('default_provider', 'google')

# 从环境变量中获取API密钥
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SILICON_API_KEY = os.getenv('SILICON_PROVIDER_API_KEY')

# MCP 配置
MCP_CONFIG = _config.get('mcp', {})
MCP_ENABLED = MCP_CONFIG.get('enabled', False)
MCP_TIMEOUT = MCP_CONFIG.get('timeout_seconds', 30)

# 获取当前激活的LLM配置
def get_active_llm_config():
    """获取当前激活的LLM配置，并处理动态变量"""
    config = LLM_CONFIG.get('providers', {}).get(DEFAULT_PROVIDER, {})
    
    # 处理系统提示词中的动态变量
    system_prompt = config.get('system_prompt', '')
    if system_prompt:
        system_prompt = system_prompt.format(
            current_date=date.today().strftime("%Y-%m-%d")
        )
        config['system_prompt'] = system_prompt
    
    return config

# 导出当前激活的配置
ACTIVE_LLM_CONFIG = get_active_llm_config()
ACTIVE_MODEL = ACTIVE_LLM_CONFIG.get('model')
ACTIVE_TEMPERATURE = ACTIVE_LLM_CONFIG.get('temperature', 0.7)
ACTIVE_STREAM = ACTIVE_LLM_CONFIG.get('stream', True)
ACTIVE_SYSTEM_PROMPT = ACTIVE_LLM_CONFIG.get('system_prompt', '') 

class Config:
    # MCP服务配置
    MCP_SERVICE_HOST = os.getenv("MCP_SERVICE_HOST", "localhost")
    MCP_SERVICE_PORT = int(os.getenv("MCP_SERVICE_PORT", "50051"))
    
    # 模型提供商配置
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "silicon")
    
    # 导出功能配置
    EXPORT_FORMATS = ["pdf", "word"]
    WKHTMLTOPDF_PATH = os.getenv("WKHTMLTOPDF_PATH")
    
    # Web服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    @staticmethod
    def get_mcp_config() -> Dict[str, Any]:
        """获取MCP服务配置"""
        return {
            "host": Config.MCP_SERVICE_HOST,
            "port": Config.MCP_SERVICE_PORT,
        }
    
    @staticmethod
    def get_export_config() -> Dict[str, Any]:
        """获取导出功能配置"""
        return {
            "formats": Config.EXPORT_FORMATS,
            "wkhtmltopdf_path": Config.WKHTMLTOPDF_PATH,
        } 
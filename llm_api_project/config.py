import os
import yaml
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, '.env'))

config_path = os.path.join(BASE_DIR, 'config.yml')
with open(config_path, 'r', encoding='utf-8') as f:
    _config = yaml.safe_load(f)

SERVER_HOST = _config.get('server', {}).get('host', '0.0.0.0')
SERVER_PORT = _config.get('server', {}).get('port', 8000)

LLM_CONFIG = _config.get('llm', {})
DEFAULT_PROVIDER = LLM_CONFIG.get('default_provider', 'google')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SILICON_API_KEY = os.getenv('SILICON_PROVIDER_API_KEY')

MCP_CONFIG = _config.get('mcp', {})
MCP_ENABLED = MCP_CONFIG.get('enabled', False)
MCP_TIMEOUT = MCP_CONFIG.get('timeout_seconds', 30)

ACTIVE_LLM_CONFIG = LLM_CONFIG.get('providers', {}).get(DEFAULT_PROVIDER, {})
ACTIVE_MODEL = ACTIVE_LLM_CONFIG.get('model')
ACTIVE_TEMPERATURE = ACTIVE_LLM_CONFIG.get('temperature', 0.7)
ACTIVE_STREAM = ACTIVE_LLM_CONFIG.get('stream', True)
ACTIVE_SYSTEM_PROMPT = ACTIVE_LLM_CONFIG.get('system_prompt', '') 
import os
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv

# 导入MCP客户端及配置
from mcp_service.client import MCPClient  # noqa: F401
from mcp_service.config.settings import MCPSettings
from .silicon_provider import SiliconProvider

class LLMManager:
    def __init__(self):
        """初始化LLM管理器"""
        self.current_provider = None
        self.providers = {}
        # 使用配置中的 URL 初始化 MCP 客户端
        self.mcp_client = MCPClient(MCPSettings.HOSTED_URL)
        print("初始化LLM管理器...")

    def initialize_provider(self, provider_name: str) -> bool:
        """初始化指定的LLM提供商"""
        try:
            if provider_name == "silicon":
                if provider_name not in self.providers:
                    # 使用MCP客户端创建提供商实例
                    self.providers[provider_name] = self.mcp_client.create_provider("silicon")
                self.current_provider = self.providers[provider_name]
                return True
            else:
                print(f"错误：不支持的提供商 {provider_name}")
                return False
        except Exception as e:
            print(f"初始化提供商失败: {str(e)}")
            return False

    def get_available_models(self) -> Dict[str, str]:
        """获取当前提供商可用的模型列表"""
        try:
            if not self.current_provider:
                print("错误：未初始化提供商")
                return {}
            # 通过MCP客户端获取模型列表
            return self.mcp_client.get_available_models(self.current_provider)
        except Exception as e:
            print(f"获取模型列表失败: {str(e)}")
            return {}

    def chat(self, messages: List[Dict[str, str]], model: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """处理聊天请求"""
        try:
            if not self.current_provider:
                return {"status": "error", "error": "未初始化提供商"}

            if not model:
                model = self.current_provider.default_model
                print(f"未指定模型，使用默认模型: {model}")

            # 使用MCP客户端发送聊天请求
            response = self.mcp_client.chat(
                provider=self.current_provider,
                messages=messages,
                model=model,
                stream=False  # 暂时不使用流式响应
            )
            
            return {
                "status": "success",
                "response": response,
                "messages": messages
            }

        except Exception as e:
            error_msg = str(e)
            print(f"聊天请求失败: {error_msg}")
            return {"status": "error", "error": error_msg} 
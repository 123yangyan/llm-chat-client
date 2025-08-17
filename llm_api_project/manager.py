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
        # 用于保存会话历史，key 为 session_id，value 为消息列表
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        # 默认携带的上下文轮数（可通过环境变量 MEMORY_WINDOW 设置）
        try:
            from backend.app.core.config import settings  # type: ignore
            self.default_context_window = settings.memory_window
        except Exception:
            # 兼容旧环境变量
            try:
                self.default_context_window = int(os.getenv("MEMORY_WINDOW", "5"))
            except ValueError:
                self.default_context_window = 5
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
            elif provider_name == "google":
                if provider_name not in self.providers:
                    self.providers[provider_name] = self.mcp_client.create_provider("google")
                self.current_provider = self.providers[provider_name]
                return True
            elif provider_name == "wisdom_gate":
                if provider_name not in self.providers:
                    self.providers[provider_name] = self.mcp_client.create_provider("wisdom_gate")
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

    def chat_with_memory(
        self,
        session_id: str,
        user_message: str,
        model: Optional[str] = None,
        context_window: Optional[int] = None,
    ) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """基于会话记忆处理聊天请求。"""
        try:
            if not self.current_provider:
                return {"status": "error", "error": "未初始化提供商"}
            if not model:
                model = self.current_provider.default_model
                print(f"未指定模型，使用默认模型: {model}")
            history = self.sessions.get(session_id, [])
            history.append({"role": "user", "content": user_message})
            if context_window is None or context_window <= 0:
                context_window = self.default_context_window
            prompt_messages = history[-context_window * 2:]
            response_text = self.mcp_client.chat(
                provider=self.current_provider,
                messages=prompt_messages,
                model=model,
                stream=False,
            )
            history.append({"role": "assistant", "content": response_text})
            self.sessions[session_id] = history
            return {
                "status": "success",
                "response": response_text,
                "session_id": session_id,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)} 
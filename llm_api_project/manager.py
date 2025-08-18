import os
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv

# 现阶段保留 MCPClient 用于 chat，但 provider 创建逻辑交由 ProviderFactory
from mcp_service.client import MCPClient  # noqa: F401
from mcp_service.config.settings import MCPSettings

# 引入新的 ProviderFactory
from backend.app.providers.factory import factory as provider_factory  # type: ignore

# 统一日志
from backend.app.core.logging_config import logger

class LLMManager:
    def __init__(self, session_repo=None):
        """初始化LLM管理器

        Args:
            session_repo: 会话存储仓库实例，默认使用 InMemory 实现。
        """
        # 延迟导入以避免循环
        if session_repo is None:
            from backend.app.repositories import session_repo as default_repo  # type: ignore
            session_repo = default_repo

        self.session_repo = session_repo

        self.current_provider = None
        self.providers = {}
        # 使用配置中的 URL 初始化 MCP 客户端
        self.mcp_client = MCPClient(MCPSettings.HOSTED_URL)
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
        logger.info("初始化LLM管理器...")

    def initialize_provider(self, provider_name: str) -> bool:
        """初始化指定的LLM提供商"""
        try:
            provider_instance = provider_factory.get(provider_name)
            if provider_instance is None:
                logger.error("错误：不支持的提供商 %s", provider_name)
                return False

            self.providers[provider_name] = provider_instance
            self.current_provider = provider_instance
            return True
        except Exception as e:
            logger.exception("初始化提供商失败: %s", e)
            return False

    def get_available_models(self) -> Dict[str, str]:
        """获取当前提供商可用的模型列表"""
        try:
            if not self.current_provider:
                logger.error("错误：未初始化提供商")
                return {}
            # 通过MCP客户端获取模型列表
            return self.mcp_client.get_available_models(self.current_provider)
        except Exception as e:
            logger.exception("获取模型列表失败: %s", e)
            return {}

    def chat(self, messages: List[Dict[str, str]], model: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """处理聊天请求"""
        try:
            if not self.current_provider:
                return {"status": "error", "error": "未初始化提供商"}

            if not model:
                model = self.current_provider.default_model
                logger.info("未指定模型，使用默认模型: %s", model)

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
            logger.exception("聊天请求失败: %s", error_msg)
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
                logger.info("未指定模型，使用默认模型: %s", model)
            history = self.session_repo.get_history(session_id)
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
            self.session_repo.save_history(session_id, history)
            return {
                "status": "success",
                "response": response_text,
                "session_id": session_id,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)} 
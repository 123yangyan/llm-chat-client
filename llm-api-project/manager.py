from silicon_provider import SiliconProvider
from google_provider import GoogleProvider
from typing import Dict, Optional, List
import json

class LLMManager:
    def __init__(self):
        self.current_provider = None
        self.providers = {
            'silicon': SiliconProvider,
            'google': GoogleProvider
        }
    
    def initialize_provider(self, provider_name: str) -> bool:
        """初始化指定的提供商"""
        if provider_name not in self.providers:
            return False
        
        try:
            self.current_provider = self.providers[provider_name]()
            return True
        except Exception as e:
            print(f"初始化提供商 {provider_name} 时出错: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """获取当前提供商支持的模型列表"""
        if not self.current_provider:
            return []
        return self.current_provider.get_available_models()

    def chat(self, messages: List[Dict[str, str]], model: str = None) -> Dict:
        """执行聊天请求"""
        if not self.current_provider:
            return {
                "status": "error",
                "error": "未初始化提供商"
            }

        try:
            response = self.current_provider.chat_completion(messages, model)
            return {
                "status": "success",
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 
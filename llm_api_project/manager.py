import os
from typing import Dict, Optional, Union, Generator, List
from dotenv import load_dotenv
from .silicon_provider import SiliconProvider
import json

# 加载环境变量
load_dotenv()

class LLMManager:
    def __init__(self):
        self.providers: Dict[str, type] = {
            'silicon': SiliconProvider
        }
        self.current_provider = None
        self.current_model = None

    def initialize_provider(self, provider_name: str) -> bool:
        try:
            print(f"尝试初始化提供商: {provider_name}")
            provider_class = self.providers.get(provider_name)
            if not provider_class:
                print(f"提供商 {provider_name} 不存在")
                return False
            self.current_provider = provider_class()
            self.current_model = self.current_provider.default_model
            print(f"成功初始化提供商: {provider_name}")
            return True
        except Exception as e:
            print(json.dumps({
                "error": "provider_init_failed",
                "message": str(e)
            }))
            return False

    def get_available_models(self) -> Dict[str, str]:
        if not self.current_provider:
            return {}
        return self.current_provider.get_available_models()

    def chat(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> dict:
        if not self.current_provider:
            return {
                "error": "no_provider",
                "message": "未初始化任何提供商"
            }
        try:
            response = self.current_provider.chat_completion(
                messages=messages,
                model=model or self.current_model,
                temperature=temperature,
                stream=True  # 默认使用流式输出
            )
            return {
                "status": "success",
                "provider": self.current_provider.__class__.__name__,
                "model": model or self.current_model,
                "request": {
                    "messages": messages,
                    "temperature": temperature
                },
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "error": "api_error",
                "message": str(e),
                "request": {
                    "messages": messages,
                    "model": model or self.current_model,
                    "temperature": temperature
                }
            } 
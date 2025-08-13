from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class LLMInterface(ABC):
    @abstractmethod
    def setup_client(self):
        """设置API客户端"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, str]:
        """获取可用的模型列表"""
        pass
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, stream: bool = True) -> str:
        """发送聊天请求并获取响应"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """获取默认模型名称"""
        pass 
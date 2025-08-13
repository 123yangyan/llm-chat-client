from dotenv import load_dotenv
from silicon_provider import SiliconProvider
from google_provider import GoogleProvider
from typing import Dict, Optional
import json

# 加载环境变量
load_dotenv()

class LLMManager:
    def __init__(self):
        self.providers: Dict[str, type] = {
            'silicon': SiliconProvider,
            'google': GoogleProvider
        }
        self.current_provider = None
        self.current_model = None
        
    def initialize_provider(self, provider_name: str) -> bool:
        try:
            provider_class = self.providers.get(provider_name)
            if not provider_class:
                return False
            
            self.current_provider = provider_class()
            self.current_model = self.current_provider.default_model
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
        """发送聊天请求并返回原始响应"""
        if not self.current_provider:
            return {
                "error": "no_provider",
                "message": "未初始化任何提供商"
            }
        
        try:
            response = self.current_provider.chat_completion(
                messages=messages,
                model=model or self.current_model,
                temperature=temperature
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

def main():
    manager = LLMManager()
    messages = []
    
    # 初始化提供商
    if not manager.initialize_provider('silicon'):
        if not manager.initialize_provider('google'):
            print(json.dumps({
                "error": "init_failed",
                "message": "无法初始化任何API提供商"
            }))
            return

    # 输出初始状态
    print(json.dumps({
        "status": "ready",
        "provider": manager.current_provider.__class__.__name__,
        "model": manager.current_model,
        "available_models": manager.get_available_models()
    }))
    
    while True:
        try:
            user_input = input().strip()
            
            # 检查是否是命令
            if user_input.startswith('/'):
                command = user_input[1:].lower()
                
                if command in ['exit', 'quit', '退出']:
                    break
                    
                elif command == '切换':
                    current = 'silicon' if isinstance(manager.current_provider, GoogleProvider) else 'google'
                    if manager.initialize_provider(current): # Changed from switch_provider to initialize_provider
                        print(json.dumps({
                            "status": "provider_switched",
                            "provider": current,
                            "model": manager.current_model
                        }))
                    continue
                    
                elif command == '模型':
                    print(json.dumps({
                        "status": "models_list",
                        "models": manager.get_available_models()
                    }))
                    continue
                    
                elif command == '清空':
                    messages = []
                    print(json.dumps({
                        "status": "history_cleared"
                    }))
                    continue
                    
                else:
                    print(json.dumps({
                        "error": "unknown_command",
                        "command": command
                    }))
                    continue
            
            # 处理聊天消息
            messages.append({"role": "user", "content": user_input})
            result = manager.chat(messages)
            print(json.dumps(result))
            
            if result["status"] == "success":
                messages.append({"role": "assistant", "content": result["response"]})
            
        except KeyboardInterrupt:
            break
            
        except Exception as e:
            print(json.dumps({
                "error": "runtime_error",
                "message": str(e)
            }))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "error": "fatal_error",
            "message": str(e)
        })) 
from dotenv import load_dotenv
from silicon_provider import SiliconProvider
from google_provider import GoogleProvider
from typing import Dict, Optional, Union, Generator
import json
import asyncio
from fastapi import WebSocket
import time

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
    
    async def chat_stream(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> Generator[str, None, None]:
        """流式聊天请求"""
        if not self.current_provider:
            yield json.dumps({
                "error": "no_provider",
                "message": "未初始化任何提供商"
            })
            return

        try:
            async for chunk in self.current_provider.chat_completion_stream(
                messages=messages,
                model=model or self.current_model,
                temperature=temperature
            ):
                yield chunk

        except Exception as e:
            yield json.dumps({
                "status": "error",
                "error": "api_error",
                "message": str(e),
                "request": {
                    "messages": messages,
                    "model": model or self.current_model,
                    "temperature": temperature
                }
            })

    def chat(self, messages: list, model: Optional[str] = None, temperature: float = 0.7) -> dict:
        """发送聊天请求并返回完整响应"""
        if not self.current_provider:
            return {
                "error": "no_provider",
                "message": "未初始化任何提供商"
            }
        
        try:
            # 打印原始请求数据
            print(json.dumps({
                "type": "request",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider": self.current_provider.__class__.__name__,
                "model": model or self.current_model,
                "temperature": temperature,
                "messages": messages
            }, ensure_ascii=False, indent=2))
            
            response = self.current_provider.chat_completion(
                messages=messages,
                model=model or self.current_model,
                temperature=temperature,
                stream=True  # 默认使用流式输出
            )
            
            # 打印原始响应数据
            result = {
                "type": "response",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success",
                "provider": self.current_provider.__class__.__name__,
                "model": model or self.current_model,
                "response": response
            }
            print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
            
            return result
            
        except Exception as e:
            error_result = {
                "type": "error",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error": "api_error",
                "message": str(e),
                "request": {
                    "messages": messages,
                    "model": model or self.current_model,
                    "temperature": temperature
                }
            }
            print("\n" + json.dumps(error_result, ensure_ascii=False, indent=2))
            return error_result

async def handle_websocket_chat(websocket: WebSocket, manager: LLMManager, messages: list):
    """处理WebSocket连接的流式聊天"""
    try:
        async for chunk in manager.chat_stream(messages):
            await websocket.send_text(chunk)
    except Exception as e:
        await websocket.send_json({
            "status": "error",
            "error": "stream_error",
            "message": str(e)
        })

def main():
    manager = LLMManager()
    messages = []
    
    # 初始化提供商
    if not manager.initialize_provider('silicon'):
        if not manager.initialize_provider('google'):
            print(json.dumps({
                "type": "system",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": "init_failed",
                "message": "无法初始化任何API提供商"
            }, ensure_ascii=False, indent=2))
            return

    # 输出初始状态
    print(json.dumps({
        "type": "system",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "ready",
        "provider": manager.current_provider.__class__.__name__,
        "model": manager.current_model,
        "available_models": manager.get_available_models()
    }, ensure_ascii=False, indent=2))
    
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
                    if manager.initialize_provider(current):
                        print(json.dumps({
                            "type": "system",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "status": "provider_switched",
                            "provider": current,
                            "model": manager.current_model
                        }, ensure_ascii=False, indent=2))
                    continue
                    
                elif command == '模型':
                    print(json.dumps({
                        "type": "system",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "models_list",
                        "models": manager.get_available_models()
                    }, ensure_ascii=False, indent=2))
                    continue
                    
                elif command == '清空':
                    messages = []
                    print(json.dumps({
                        "type": "system",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "history_cleared"
                    }, ensure_ascii=False, indent=2))
                    continue
                    
                else:
                    print(json.dumps({
                        "type": "system",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "error": "unknown_command",
                        "command": command
                    }, ensure_ascii=False, indent=2))
                    continue
            
            # 处理聊天消息
            messages.append({"role": "user", "content": user_input})
            result = manager.chat(messages)
            
            if result["status"] == "success":
                messages.append({"role": "assistant", "content": result["response"]})
            
        except KeyboardInterrupt:
            break
            
        except Exception as e:
            print(json.dumps({
                "type": "system",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": "runtime_error",
                "message": str(e)
            }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({
            "type": "system",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": "fatal_error",
            "message": str(e)
        }, ensure_ascii=False, indent=2)) 
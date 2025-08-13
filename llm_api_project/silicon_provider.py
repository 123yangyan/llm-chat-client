from openai import OpenAI
import os
from typing import Dict, List, Optional, Generator, AsyncGenerator
from .llm_interface import LLMInterface
import requests
import json
import asyncio

class SiliconProvider(LLMInterface):
    def __init__(self):
        self.api_key = os.getenv("SILICON_API_KEY")
        print(f"初始化硅基流动提供商...")
        print(f"API密钥状态: {'已设置' if self.api_key else '未设置'}")
        if not self.api_key:
            raise ValueError("请在.env文件中设置SILICON_API_KEY")
        self.setup_client()
        print("硅基流动提供商初始化完成")
    
    def setup_client(self):
        """设置API客户端"""
        self.base_url = "https://api.siliconflow.cn/v1"
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # 测试API密钥是否有效
            response = requests.get(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            if response.status_code == 401:
                raise ValueError("API密钥无效，请检查是否正确设置")
            elif response.status_code != 200:
                raise ValueError(f"API连接测试失败: {response.text}")
        except Exception as e:
            print(f"API客户端设置失败: {str(e)}")
            raise

    @property
    def default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-3.5-turbo"
    
    def get_available_models(self) -> Dict[str, str]:
        """获取可用的模型列表"""
        try:
            # 发送请求获取模型列表
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(f"{self.base_url}/models", headers=headers)
            
            if response.status_code == 401:
                print("API密钥无效，请检查是否正确设置")
                return self._get_default_models()
            elif response.status_code != 200:
                print(f"获取模型列表失败: {response.text}")
                return self._get_default_models()

            # 解析响应数据
            models_data = response.json()
            available_models = {}

            # 处理返回的模型数据
            for model in models_data.get("data", []):
                model_id = model.get("id")
                if model_id:
                    # 创建一个更友好的显示名称
                    display_name = self._get_display_name(model_id)
                    available_models[display_name] = model_id

            if not available_models:
                print("未找到可用模型，使用默认模型列表")
                return self._get_default_models()

            print(f"获取到的模型列表: {available_models}")
            return available_models

        except Exception as e:
            print(f"获取模型列表失败: {str(e)}")
            return self._get_default_models()

    def _get_default_models(self) -> Dict[str, str]:
        """获取默认的模型列表"""
        return {
            "GPT-3.5 Turbo": "gpt-3.5-turbo",
            "GPT-4": "gpt-4",
            "DeepSeek Chat": "deepseek-ai/DeepSeek-V2.5",
            "InternLM Chat": "internlm/internlm2_5-20b-chat",
            "Qwen Chat": "Qwen/Qwen2.5-72B-Instruct"
        }

    def _get_display_name(self, model_id: str) -> str:
        """将模型ID转换为友好的显示名称"""
        # 移除版本号和其他技术细节
        name = model_id.split('/')[-1] if '/' in model_id else model_id
        name = name.replace('-', ' ').title()
        
        # 特殊处理一些常见模型名称
        name_mapping = {
            "Gpt 4": "GPT-4",
            "Gpt 3.5 Turbo": "GPT-3.5 Turbo",
            "Deepseek V2.5": "DeepSeek Chat",
            "Internlm2 5 20B Chat": "InternLM Chat",
            "Qwen2.5 72B Instruct": "Qwen Chat"
        }
        
        return name_mapping.get(name, name)

    async def chat_completion_stream(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """异步流式聊天请求"""
        try:
            print(f"使用模型 {model} 发送流式请求...")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            )
            
            current_content = ""
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    current_content += content
                    # 发送当前累积的内容
                    yield json.dumps({
                        "status": "streaming",
                        "content": content,
                        "full_content": current_content
                    })
            
            # 发送完成信号
            yield json.dumps({
                "status": "complete",
                "content": current_content
            })

        except Exception as e:
            error_msg = str(e)
            print(f"流式API调用失败: {error_msg}")
            yield json.dumps({
                "status": "error",
                "error": "stream_error",
                "message": error_msg
            })

    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float = 0.7,
        stream: bool = True
    ) -> str:
        """发送聊天请求并获取响应"""
        try:
            print(f"使用模型 {model} 发送请求...")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=stream
            )
            
            if stream:
                # 处理流式响应
                full_response = ""
                print("\nAI: ", end="")
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        full_response += content
                return full_response
            else:
                # 处理非流式响应
                return response.choices[0].message.content
                
        except Exception as e:
            error_msg = str(e)
            print(f"API调用失败: {error_msg}")
            raise Exception(f"硅基流动API调用失败: {error_msg}") 
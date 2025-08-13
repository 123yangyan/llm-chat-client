import google.generativeai as genai
import os
from typing import Dict, List, Optional, Generator
from llm_interface import LLMInterface
import time
import asyncio

class GoogleProvider(LLMInterface):
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("请在.env文件中设置GOOGLE_API_KEY")
        self.setup_client()
        self.max_retries = 3
        self.retry_delay = 1  # 重试延迟（秒）
    
    def setup_client(self):
        """设置API客户端"""
        genai.configure(api_key=self.api_key)
        self.model = None  # 将在使用时根据选择的模型初始化
    
    @property
    def default_model(self) -> str:
        return "gemini-2.5-pro"  # 使用最新的高性能模型作为默认值
    
    def get_available_models(self) -> Dict[str, str]:
        """获取可用的模型列表"""
        try:
            # 获取实际可用的模型列表
            available_models = genai.list_models()
            model_dict = {}
            index = 1
            
            for model in available_models:
                if "gemini" in model.name:
                    model_dict[str(index)] = model.name
                    index += 1
            
            return model_dict if model_dict else {
                # Gemini 2.5 系列
                "1": "gemini-2.5-pro",        # 最强大的思考型模型，回答准确性最高
                "2": "gemini-2.5-flash",      # 性价比出色的模型，提供全面功能
                "3": "gemini-2.5-flash-lite", # 优化成本效益和延迟的模型
                
                # Gemini 2.0 系列
                "4": "gemini-2.0-pro",        # 基础专业版
                "5": "gemini-2.0-flash",      # 基础快速版
                "6": "gemini-2.0-flash-live-001", # 实时对话版本
                
                # 视觉模型
                "7": "gemini-pro-vision",     # 支持图像理解的专业版
            }
        except Exception as e:
            print(f"获取模型列表失败: {str(e)}")
            return {
                "1": "gemini-2.5-pro",        # 最强大的思考型模型
                "2": "gemini-2.5-flash",      # 性价比出色的模型
                "3": "gemini-2.5-flash-lite", # 优化的轻量版模型
            }
    
    def _initialize_model(self, model_name: str):
        """根据模型名称初始化对应的模型"""
        try:
            self.model = genai.GenerativeModel(model_name)
        except Exception as e:
            raise Exception(f"模型初始化失败: {str(e)}")
    
    def _create_generation_config(self, temperature: float) -> genai.types.GenerationConfig:
        """创建生成配置"""
        return genai.types.GenerationConfig(
            temperature=temperature,
            top_p=0.8,          # 控制采样的概率阈值
            top_k=40,           # 控制采样的token数量
            max_output_tokens=2048,  # 最大输出长度
            candidate_count=1    # 生成候选数量
        )

    def _process_stream_response(self, response_stream) -> Generator[str, None, None]:
        """处理流式响应"""
        try:
            for chunk in response_stream:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"处理流式响应失败: {str(e)}")

    async def _process_stream_response_async(self, response_stream) -> Generator[str, None, None]:
        """异步处理流式响应"""
        try:
            async for chunk in response_stream:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"处理流式响应失败: {str(e)}")
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, stream: bool = True) -> str:
        """发送聊天请求并获取响应"""
        retries = 0
        while retries < self.max_retries:
            try:
                # 确保模型已初始化且是正确的模型
                if not self.model or self.model.model_name != model:
                    self._initialize_model(model)
                
                # 创建生成配置
                generation_config = self._create_generation_config(temperature)
                
                # 创建聊天会话
                chat = self.model.start_chat(history=[])
                
                # 发送所有历史消息
                for message in messages[:-1]:
                    if message["role"] == "user":
                        chat.send_message(message["content"])
                
                # 发送最后一条消息并获取响应
                last_message = messages[-1]["content"]
                
                if stream:
                    # 流式响应
                    response = chat.send_message(
                        last_message,
                        generation_config=generation_config,
                        stream=True
                    )
                    
                    full_response = ""
                    print("\nAI: ", end="", flush=True)
                    
                    # 使用生成器处理流式响应
                    for text in self._process_stream_response(response):
                        print(text, end="", flush=True)
                        full_response += text
                    
                    return full_response
                else:
                    # 非流式响应
                    response = chat.send_message(
                        last_message,
                        generation_config=generation_config
                    )
                    return response.text
                    
            except Exception as e:
                retries += 1
                if retries < self.max_retries:
                    print(f"\n请求失败，正在重试 ({retries}/{self.max_retries})...")
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Google API调用失败 (已重试{retries}次): {str(e)}")
        
        raise Exception("超过最大重试次数")

    async def chat_completion_async(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> str:
        """异步发送聊天请求并获取响应"""
        try:
            # 确保模型已初始化且是正确的模型
            if not self.model or self.model.model_name != model:
                self._initialize_model(model)
            
            # 创建生成配置
            generation_config = self._create_generation_config(temperature)
            
            # 创建聊天会话
            chat = self.model.start_chat(history=[])
            
            # 发送所有历史消息
            for message in messages[:-1]:
                if message["role"] == "user":
                    await chat.send_message_async(message["content"])
            
            # 发送最后一条消息并获取响应
            last_message = messages[-1]["content"]
            
            # 流式响应
            response = await chat.send_message_async(
                last_message,
                generation_config=generation_config,
                stream=True
            )
            
            full_response = ""
            print("\nAI: ", end="", flush=True)
            
            # 使用异步生成器处理流式响应
            async for text in self._process_stream_response_async(response):
                print(text, end="", flush=True)
                full_response += text
            
            return full_response
                
        except Exception as e:
            raise Exception(f"Google API异步调用失败: {str(e)}") 
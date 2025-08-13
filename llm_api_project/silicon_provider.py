from openai import OpenAI
import os
from typing import Dict, List, Optional
from llm_interface import LLMInterface

class SiliconProvider(LLMInterface):
    def __init__(self):
        self.api_key = os.getenv("SILICON_API_KEY")
        if not self.api_key:
            raise ValueError("请在.env文件中设置SILICON_API_KEY")
        self.setup_client()
    
    def setup_client(self):
        """设置API客户端"""
        self.base_url = "https://api.siliconflow.cn/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    @property
    def default_model(self) -> str:
        return "deepseek-ai/DeepSeek-V2.5"
    
    def get_available_models(self) -> Dict[str, str]:
        """获取可用的模型列表"""
        return {
            # Deepseek 系列
            "1": "deepseek-ai/DeepSeek-V2.5",
            "2": "Pro/deepseek-ai/DeepSeek-R1",
            "3": "deepseek-ai/DeepSeek-R1",
            "4": "Pro/deepseek-ai/DeepSeek-R1-0120",
            "5": "Pro/deepseek-ai/DeepSeek-V3",
            "6": "deepseek-ai/DeepSeek-V3",
            "7": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "8": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            "9": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            "10": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            
            # 书生系列
            "11": "internlm/internlm2_5-20b-chat",
            "12": "internlm/internlm2_5-7b-chat",
            "13": "Pro/internlm/internlm2_5-7b-chat",
            
            # Qwen 系列
            "14": "Qwen/Qwen3-30B-A3B",
            "15": "Qwen/Qwen3-32B",
            "16": "Qwen/Qwen3-14B",
            "17": "Qwen/Qwen3-8B",
            "18": "Qwen/Qwen3-235B-A22B",
            "19": "Qwen/QwQ-32B",
            "20": "Qwen/Qwen2.5-72B-Instruct",
            "21": "Qwen/Qwen2.5-32B-Instruct",
            "22": "Qwen/Qwen2.5-14B-Instruct",
            "23": "Qwen/Qwen2.5-7B-Instruct",
            "24": "Pro/Qwen/Qwen2.5-7B-Instruct",
            
            # GLM 系列
            "25": "THUDM/glm-4-9b-chat",
            "26": "Pro/THUDM/glm-4-9b-chat",
            "27": "THUDM/GLM-Z1-32B-0414",
            "28": "THUDM/GLM-4-32B-0414",
            "29": "THUDM/GLM-Z1-Rumination-32B-0414",
            "30": "THUDM/GLM-4-9B-0414"
        }
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, stream: bool = True) -> str:
        """发送聊天请求并获取响应"""
        try:
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
            raise Exception(f"硅基流动API调用失败: {str(e)}") 
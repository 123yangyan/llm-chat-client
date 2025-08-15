import os
import json
import time
from typing import List, Dict, AsyncGenerator
import re

import requests

from .llm_interface import LLMInterface
from . import config


class WisdomGateProvider(LLMInterface):
    """智慧之门 (JuheAPI ‑ Wisdom Gate) LLM Provider"""

    BASE_URL = "https://wisdom-gate.juheapi.com/v1"

    def __init__(self):
        self.api_key = os.getenv("WISDOM_API_KEY")
        print(json.dumps({
            "type": "system",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "provider_init",
            "provider": "wisdom_gate",
            "api_key_status": "已设置" if self.api_key else "未设置"
        }, ensure_ascii=False, indent=2))

        if not self.api_key:
            raise ValueError("请在 .env 中配置 WISDOM_API_KEY")

        self.setup_client()
        print(json.dumps({
            "type": "system",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "provider_ready",
            "provider": "wisdom_gate"
        }, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------
    # 基础接口
    # ------------------------------------------------------------------
    def setup_client(self):
        """当前无需专门 SDK, 使用 requests 调用 REST 接口"""
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"  # Wisdom Gate 免费首推模型

    def get_available_models(self) -> Dict[str, str]:
        """从 Wisdom Gate 查询可用模型列表"""
        try:
            resp = self.session.get(f"{self.BASE_URL}/models")
            if resp.status_code == 200:
                data = resp.json()
                # 假设返回格式 {"data":[{"id":"model-id","name":"display"},...]} 
                models = {}
                for m in data.get("data", []):
                    display = self._get_display_name(m.get("name", m["id"]))
                    models[display] = m["id"]
                if models:
                    return models
            print(f"获取模型失败 {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"获取模型异常: {e}")
        # fallback list (核心文档中的热门模型)
        return {
            "Gemini 2.5 Flash": "gemini-2.5-flash",
            "Gemini 2.5 Pro": "gemini-2.5-pro",
            "GPT-4o": "gpt-4o",
            "Claude 3.5 Haiku": "claude-3-5-haiku-20241022"
        }

    def _get_display_name(self, raw_name: str) -> str:
        """清理 Wisdom Gate 返回的模型名称"""
        # 去除前缀: Free Wisdom AI / Wisdom-AI / WisdomAI 等
        name = re.sub(r"(?i)^\s*(free\s+)?wisdom[-\s]?ai\s+", "", raw_name).strip()
        # 再次移除单独的 Wisdom AI 关键字（如果出现在其他位置）
        name = re.sub(r"(?i)wisdom[-\s]?ai", "", name).strip()
        # 去掉括号及其中内容
        name = re.sub(r"\(.*?\)", "", name).strip()
        name = re.sub(r"\s{2,}", " ", name)
        # 去掉可能残留的前导短横线或破折号
        name = re.sub(r"^[\-–—\s]+", "", name)
        # 标准化大小写
        name = name.title().replace("Gpt", "GPT").replace("Gemini", "Gemini").replace("Glm", "GLM").replace("Claude", "Claude").replace("Deepseek", "DeepSeek").replace("Flux", "Flux")
        return name

    # ------------------------------------------------------------------
    # 私有工具
    # ------------------------------------------------------------------
    def _add_system_prompt(self, messages: List[Dict[str, str]]):
        if not messages or messages[0].get("role") != "system":
            sp = config.ACTIVE_SYSTEM_PROMPT
            if sp:
                messages.insert(0, {"role": "system", "content": sp})
        return messages

    def _convert_messages(self, messages: List[Dict[str, str]]):
        # Wisdom Gate 基于 OpenAI 格式, 直接返回
        return messages

    # ------------------------------------------------------------------
    # 聊天接口
    # ------------------------------------------------------------------
    def chat_completion(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, stream: bool = False) -> str:
        messages = self._add_system_prompt(messages)
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": stream
        }
        try:
            resp = self.session.post(f"{self.BASE_URL}/chat/completions", data=json.dumps(payload))
            if resp.status_code == 200:
                data = resp.json()
                if stream:
                    # 若后端支持 SSE, 这里简化直接返回完整 content
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            raise Exception(f"智慧之门 API 调用失败: {e}")

    async def chat_completion_stream(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """简单包装, 使用同步接口阻塞获取后一次性返回"""
        content = self.chat_completion(messages, model, temperature, stream=False)
        yield content 
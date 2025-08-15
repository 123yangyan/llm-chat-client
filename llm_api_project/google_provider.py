import os
import json
import time
from typing import List, Dict, AsyncGenerator

import google.generativeai as genai

from .llm_interface import LLMInterface
from . import config


class GoogleProvider(LLMInterface):
    """基于 Google Gemini 的 LLM Provider 实现"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        print(json.dumps({
            "type": "system",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "provider_init",
            "provider": "google",
            "api_key_status": "已设置" if self.api_key else "未设置"
        }, ensure_ascii=False, indent=2))

        if not self.api_key:
            raise ValueError("请在.env文件中设置GOOGLE_API_KEY")

        self.setup_client()
        print(json.dumps({
            "type": "system",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "provider_ready",
            "provider": "google"
        }, ensure_ascii=False, indent=2))

    # ---------------------------------------------------------------------
    # 基础接口实现
    # ---------------------------------------------------------------------
    def setup_client(self):
        """配置 Google Gemini SDK"""
        try:
            genai.configure(api_key=self.api_key)
            # 直接使用 genai 作为客户端
            self.client = genai
        except Exception as e:
            print(f"Google Gemini SDK 初始化失败: {e}")
            raise

    @property
    def default_model(self) -> str:
        """返回默认模型名称"""
        return "gemini-pro"

    def get_available_models(self) -> Dict[str, str]:
        """返回可用模型列表（动态调用Gemini API以确保最新）"""
        try:
            models = {}
            for model in genai.list_models():
                # 仅保留支持文本生成的方法
                if 'generateContent' in getattr(model, 'supported_generation_methods', []):
                    # model.name 形如 'models/gemini-2.5-pro'
                    model_id = model.name.split('/')[-1]
                    display_name = self._get_display_name(model_id)
                    models[display_name] = model_id

            # 如果未获取到任何模型则回退默认静态列表
            if not models:
                models = {
                    "Gemini Pro": "gemini-pro",
                    "Gemini Pro Vision": "gemini-pro-vision"
                }

            return models
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            # 出错时回退默认列表
            return {
                "Gemini Pro": "gemini-pro",
                "Gemini Pro Vision": "gemini-pro-vision"
            }

    # ------------------------------------------------------------------
    # 私有工具方法
    # ------------------------------------------------------------------

    def _add_system_prompt(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """在消息首部插入系统提示词（如有）"""
        if not messages or messages[0].get("role") != "system":
            system_prompt = config.ACTIVE_SYSTEM_PROMPT
            if system_prompt:
                messages.insert(0, {
                    "role": "system",
                    "content": system_prompt
                })
        return messages

    def _get_display_name(self, model_id: str) -> str:
        """根据官方模型ID生成友好显示名称"""
        name = model_id.replace('-', ' ').title()
        mapping = {
            "Gemini Pro": "Gemini Pro",
            "Gemini Pro Vision": "Gemini Pro Vision",
            "Gemini 2.5 Pro": "Gemini 2.5 Pro",
            "Gemini 2.5 Flash": "Gemini 2.5 Flash",
            "Gemini 2.5 Flash Lite Preview": "Gemini 2.5 Flash Lite",
            "Gemini 2.0 Flash": "Gemini 2.0 Flash"
        }
        return mapping.get(name, name)

    def _convert_messages(self, messages: List[Dict[str, str]]):
        role_map = {"user": "user", "assistant": "model", "system": "user"}
        return [{"role": role_map.get(m["role"], "user"), "parts": [m["content"]]} for m in messages]

    # ------------------------------------------------------------------
    # 聊天接口实现
    # ------------------------------------------------------------------

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """异步流式聊天接口（Gemini 暂不提供原生异步，使用线程池包装）"""
        # 由于 Gemini SDK 仅提供同步流式接口，简单地在协程中包裹即可
        import asyncio
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, lambda: list(self._sync_stream(messages, model, temperature))):
            yield chunk

    def _sync_stream(self, messages: List[Dict[str, str]], model: str, temperature: float):
        """同步流式生成，供异步包装调用"""
        messages = self._add_system_prompt(messages)
        print(json.dumps({
            "type": "request",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "stream_request",
            "provider": "google",
            "model": model,
            "temperature": temperature,
            "messages": messages
        }, ensure_ascii=False, indent=2))

        gemini_messages = self._convert_messages(messages)
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content(gemini_messages, generation_config={"temperature": temperature}, stream=True)

        current_content = ""
        for chunk in response:
            if getattr(chunk, "text", None):
                content = chunk.text
                current_content += content
                yield json.dumps({
                    "type": "stream_chunk",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "streaming",
                    "content": content,
                    "full_content": current_content
                }, ensure_ascii=False)
        yield json.dumps({
            "type": "stream_complete",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "complete",
            "content": current_content
        }, ensure_ascii=False)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        stream: bool = True
    ) -> str:
        """同步聊天接口"""
        try:
            messages = self._add_system_prompt(messages)
            print(json.dumps({
                "type": "request",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "chat_request",
                "provider": "google",
                "model": model,
                "temperature": temperature,
                "stream": stream,
                "messages": messages
            }, ensure_ascii=False, indent=2))

            gemini_messages = self._convert_messages(messages)
            model_obj = genai.GenerativeModel(model)

            if stream:
                full_response = ""
                response = model_obj.generate_content(gemini_messages, generation_config={"temperature": temperature}, stream=True)
                print(json.dumps({
                    "type": "response",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": "stream_start",
                    "provider": "google"
                }, ensure_ascii=False, indent=2))
                for chunk in response:
                    if getattr(chunk, "text", None):
                        content = chunk.text
                        full_response += content
                        print(content, end="", flush=True)
                print(json.dumps({
                    "type": "response",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": "stream_complete",
                    "provider": "google",
                    "content_length": len(full_response)
                }, ensure_ascii=False, indent=2))
                return full_response
            else:
                response = model_obj.generate_content(gemini_messages, generation_config={"temperature": temperature})
                content = response.text
                print(json.dumps({
                    "type": "response",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": "chat_response",
                    "provider": "google",
                    "content_length": len(content)
                }, ensure_ascii=False, indent=2))
                return content

        except Exception as e:
            error_msg = str(e)
            print(json.dumps({
                "type": "error",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "chat_error",
                "provider": "google",
                "error": error_msg
            }, ensure_ascii=False, indent=2))
            raise Exception(f"Google Gemini API 调用失败: {error_msg}") 
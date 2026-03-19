#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端服务
封装各种LLM的调用，统一接口
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    AZURE_OPENAI = "Azure-OpenAI"
    OLLAMA = "Ollama"
    LOCALAI = "LocalAI"
    GEMINI = "Google Gemini"
    CUSTOM = "Custom"

class LLMUsageType(str, Enum):
    """LLM用途枚举"""
    CHAT = "chat"
    TRANSLATION = "translation"
    REPORT = "report"
    AGENT = "agent"

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    enable_thinking: bool = False

@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str

class LLMClientBase:
    """LLM客户端基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """发送聊天请求"""
        raise NotImplementedError
        
    async def chat_with_json(self, messages: List[ChatMessage], **kwargs) -> Dict[str, Any]:
        """发送聊天请求并期望返回JSON"""
        raise NotImplementedError

class OpenAIClient(LLMClientBase):
    """OpenAI客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
        
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.openai.com/v1",
                max_retries=3
            )
            logger.info("OpenAI客户端初始化成功")
        except ImportError:
            logger.warning("OpenAI SDK未安装，将使用HTTP请求方式")
            self.client = None
            
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """发送聊天请求"""
        if self.client is None:
            return await self._chat_via_http(messages, **kwargs)
            
        try:
            msg_list = [{"role": m.role, "content": m.content} for m in messages]
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=msg_list,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI调用失败: {e}")
            raise
            
    async def _chat_via_http(self, messages: List[ChatMessage], **kwargs) -> str:
        """通过HTTP请求调用OpenAI API"""
        import aiohttp
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model_name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=300)
            async with session.post(
                f"{self.config.base_url or 'https://api.openai.com/v1'}/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout
            ) as resp:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]

class AnthropicClient(LLMClientBase):
    """Anthropic (Claude) 客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
        
    def _init_client(self):
        """初始化Anthropic客户端"""
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(
                api_key=self.config.api_key,
                max_retries=3
            )
            logger.info("Anthropic客户端初始化成功")
        except ImportError:
            logger.warning("Anthropic SDK未安装")
            self.client = None
            
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """发送聊天请求"""
        if self.client is None:
            return "Anthropic SDK未安装"
            
        try:
            system_msg = ""
            user_msgs = []
            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    user_msgs.append(msg)
                    
            response = await self.client.messages.create(
                model=self.config.model_name,
                system=system_msg,
                messages=[{"role": m.role, "content": m.content} for m in user_msgs],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic调用失败: {e}")
            raise

class OllamaClient(LLMClientBase):
    """Ollama本地模型客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
    async def chat(self, messages: List[ChatMessage], **kwargs) -> str:
        """发送聊天请求"""
        import aiohttp
        
        base_url = self.config.base_url or "http://localhost:11434"
        
        messages_list = [{"role": m.role, "content": m.content} for m in messages]
        
        if not self.config.enable_thinking and messages_list and messages_list[0].get("role") == "system":
            messages_list[0]["content"] += "\n\n请直接输出结果，不要进行任何解释或推理过程。"
        
        payload = {
            "model": self.config.model_name,
            "messages": messages_list,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": False
        }
        
        logger.info(f"[Ollama] 发送请求到 {base_url}/api/chat")
        logger.info(f"[Ollama] 模型: {self.config.model_name}")
        logger.info(f"[Ollama] 消息数量: {len(messages)}")
        logger.info(f"[Ollama] enable_thinking: {self.config.enable_thinking}")
        logger.info(f"[Ollama] 请求payload: {payload}")
        
        timeout = aiohttp.ClientTimeout(total=600)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info(f"[Ollama] 开始发送HTTP请求...")
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload
                ) as resp:
                    logger.info(f"[Ollama] 收到响应，状态码: {resp.status}")
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"[Ollama] 请求失败: {error_text}")
                        raise Exception(f"Ollama API返回错误: {resp.status} - {error_text}")
                    
                    result = await resp.json()
                    logger.info(f"[Ollama] 响应成功，内容长度: {len(result.get('message', {}).get('content', ''))}")
                    return result["message"]["content"]
        except Exception as e:
            logger.error(f"[Ollama] 调用异常: {str(e)}", exc_info=True)
            raise

class LLMClientFactory:
    """LLM客户端工厂"""

    _clients: Dict[str, LLMClientBase] = {}

    @classmethod
    def get_client(cls, provider: str, config: LLMConfig) -> LLMClientBase:
        """获取LLM客户端"""
        cache_key = f"{provider}:{config.model_name}"
        
        if cache_key in cls._clients:
            return cls._clients[cache_key]
            
        client: LLMClientBase
        switcher = {
            "OpenAI": OpenAIClient,
            "Anthropic": AnthropicClient,
            "Ollama": OllamaClient,
        }
        
        client_class = switcher.get(provider, OpenAIClient)
        client = client_class(config)
        cls._clients[cache_key] = client
        
        return client

class LLMService:
    """LLM服务 - 统一管理LLM调用"""
    
    def __init__(self):
        self.configs: Dict[str, LLMConfig] = {}
        self._load_configs()
        
    def _load_configs(self):
        """从环境变量加载LLM配置"""
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.configs["OpenAI"] = LLMConfig(
                provider="OpenAI",
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL"),
                max_tokens=4096
            )
            
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.configs["Anthropic"] = LLMConfig(
                provider="Anthropic",
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=anthropic_key,
                max_tokens=4096
            )
            
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            self.configs["Ollama"] = LLMConfig(
                provider="Ollama",
                model_name=os.getenv("OLLAMA_MODEL", "llama2"),
                api_key="not-needed",
                base_url=ollama_url,
                max_tokens=4096
            )
    
    def load_user_configs(self, user_configs: list):
        """从用户数据库配置加载LLM配置"""
        for config in user_configs:
            if config.get("status") != "1":
                continue
            provider = config.get("llm_factory")
            llm_config = LLMConfig(
                provider=provider,
                model_name=config.get("llm_name", ""),
                api_key=config.get("api_key", ""),
                base_url=config.get("api_base", ""),
                max_tokens=config.get("max_tokens", 4096),
                temperature=config.get("temperature", 0.7),
                enable_thinking=False
            )
            key = f"{provider}:{llm_config.model_name}"
            self.configs[key] = llm_config
            
    def get_available_providers(self) -> List[str]:
        """获取可用的LLM提供商"""
        return list(self.configs.keys())
    
    def get_client(self, provider: str = None) -> Optional[LLMClientBase]:
        """获取LLM客户端"""
        if provider is None:
            keys = list(self.configs.keys())
            if not keys:
                return None
            key = keys[0]
            provider = key.split(":")[0] if ":" in key else key
            return LLMClientFactory.get_client(provider, self.configs[key])
            
        for key, config in self.configs.items():
            if key.startswith(provider + ":"):
                return LLMClientFactory.get_client(provider, config)
            if provider in key:
                return LLMClientFactory.get_client(provider, config)
        
        return None
        
    async def chat(
        self, 
        prompt: str, 
        system_prompt: str = None,
        provider: str = None,
        **kwargs
    ) -> str:
        """发送聊天请求"""
        logger.info(f"[LLMService] chat调用开始: prompt长度={len(prompt)}, provider={provider}")
        logger.info(f"[LLMService] 当前可用配置: {list(self.configs.keys())}")
        
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))
        
        logger.info(f"[LLMService] 获取客户端...")
        client = self.get_client(provider)
        if client is None:
            logger.error(f"[LLMService] 未找到可用的LLM客户端")
            return "错误: 未配置LLM，请先在设置中配置LLM API Key"
        
        logger.info(f"[LLMService] 客户端获取成功: {client.__class__.__name__}")
        logger.info(f"[LLMService] 开始调用client.chat...")
        result = await client.chat(messages, **kwargs)
        logger.info(f"[LLMService] client.chat调用完成，结果长度={len(result)}")
        return result
        
    async def chat_json(
        self, 
        prompt: str, 
        system_prompt: str = None,
        provider: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送聊天请求并期望返回JSON"""
        full_prompt = f"{prompt}\n\n请以JSON格式返回结果。"
        result = await self.chat(full_prompt, system_prompt, provider, **kwargs)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"error": "JSON解析失败", "raw": result}

llm_service = LLMService()

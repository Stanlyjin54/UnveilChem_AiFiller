#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM翻译服务
基于LLM的智能翻译服务
"""

import hashlib
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from ..llm import llm_service, ChatMessage, prompt_manager

logger = logging.getLogger(__name__)

class TranslationStyle(str, Enum):
    """翻译风格"""
    PROFESSIONAL = "professional"
    TECHNICAL = "technical"
    CASUAL = "casual"

@dataclass
class TranslationRequest:
    """翻译请求"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    style: TranslationStyle = TranslationStyle.PROFESSIONAL
    provider: Optional[str] = None
    use_cache: bool = True

@dataclass
class TranslationResponse:
    """翻译响应"""
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = 1.0
    cached: bool = False

class TranslationCache:
    """翻译缓存"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, TranslationResponse] = {}
        self.max_size = max_size
        
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[TranslationResponse]:
        """获取缓存"""
        key = self._make_key(text, source_lang, target_lang)
        return self.cache.get(key)
    
    def set(self, text: str, source_lang: str, target_lang: str, response: TranslationResponse):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            first_key = next(iter(self.cache))
            del self.cache[first_key]
            
        key = self._make_key(text, source_lang, target_lang)
        self.cache[key] = response
        
    def _make_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """生成缓存键"""
        content = f"{text[:100]}:{source_lang}:{target_lang}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()

class LLMTranslationService:
    """基于LLM的翻译服务"""
    
    STYLE_PROMPTS = {
        TranslationStyle.PROFESSIONAL: "translation_professional",
        TranslationStyle.TECHNICAL: "translation_technical",
    }
    
    def __init__(self):
        self.llm = llm_service
        self.prompts = prompt_manager
        self.cache = TranslationCache()
        
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """执行翻译"""
        
        if request.use_cache:
            cached = self.cache.get(request.text, request.source_lang, request.target_lang)
            if cached:
                cached.cached = True
                return cached
            
        prompt = self._build_prompt(request)
        
        try:
            translated = await self.llm.chat(
                prompt,
                provider=request.provider,
                temperature=0.3
            )
            
            result = TranslationResponse(
                translated_text=translated,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                confidence=0.95
            )
            
            if request.use_cache:
                self.cache.set(request.text, request.source_lang, request.target_lang, result)
                
            return result
            
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            raise
            
    async def translate_document(
        self,
        document_content: str,
        target_lang: str = "zh",
        style: TranslationStyle = TranslationStyle.PROFESSIONAL,
        provider: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """翻译整个文档"""
        
        segments = self._split_text(document_content)
        results = []
        
        for i, segment in enumerate(segments):
            request = TranslationRequest(
                text=segment,
                target_lang=target_lang,
                style=style,
                provider=provider,
                use_cache=True
            )
            
            result = await self.translate(request)
            results.append(result.translated_text)
            
            if progress_callback:
                progress_callback((i + 1) / len(segments))
                
        return "\n".join(results)
    
    def _build_prompt(self, request: TranslationRequest) -> str:
        """构建翻译提示词"""
        prompt_key = self.STYLE_PROMPTS.get(request.style, "translation_professional")
        
        return self.prompts.get_prompt(
            prompt_key,
            target_lang=self._get_lang_name(request.target_lang),
            text=request.text
        )
    
    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """分段处理长文本"""
        paragraphs = text.split("\n\n")
        segments = []
        current = ""
        
        for para in paragraphs:
            if len(current) + len(para) <= max_length:
                current += para + "\n\n"
            else:
                if current:
                    segments.append(current.strip())
                current = para + "\n\n"
                
        if current:
            segments.append(current.strip())
            
        return segments if segments else [text]
    
    def _get_lang_name(self, code: str) -> str:
        """语言代码转名称"""
        lang_map = {
            "zh": "中文",
            "en": "英文",
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文"
        }
        return lang_map.get(code, code)
    
    def clear_cache(self):
        """清空翻译缓存"""
        self.cache.clear()

translation_service = LLMTranslationService()

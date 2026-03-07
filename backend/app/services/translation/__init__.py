#!/usr/bin/env python3
"""
翻译服务模块
提供基于LLM的翻译功能
"""

from .llm_translation_service import (
    LLMTranslationService,
    TranslationRequest,
    TranslationResponse,
    TranslationStyle,
    translation_service
)

__all__ = [
    "LLMTranslationService",
    "TranslationRequest",
    "TranslationResponse",
    "TranslationStyle",
    "translation_service"
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation API路由
提供翻译功能接口
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging
import os

from ..services.translation import (
    translation_service, 
    TranslationRequest, 
    TranslationStyle
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/translation", tags=["Translation"])

class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "zh"
    style: str = "professional"
    provider: Optional[str] = None

class TranslateResponse(BaseModel):
    """翻译响应"""
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float

@router.post("/translate")
async def translate_text(request: TranslateRequest):
    """翻译文本"""
    try:
        style = TranslationStyle(request.style) if request.style in [e.value for e in TranslationStyle] else TranslationStyle.PROFESSIONAL
        
        trans_request = TranslationRequest(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            style=style,
            provider=request.provider
        )
        
        result = await translation_service.translate(trans_request)
        
        return {
            "success": True,
            "data": {
                "translated_text": result.translated_text,
                "source_lang": result.source_lang,
                "target_lang": result.target_lang,
                "confidence": result.confidence,
                "cached": result.cached
            }
        }
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document")
async def translate_document(
    target_lang: str = "zh",
    style: str = "professional",
    provider: Optional[str] = None,
    file: UploadFile = File(...)
):
    """翻译文档"""
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        style_enum = TranslationStyle(style) if style in [e.value for e in TranslationStyle] else TranslationStyle.PROFESSIONAL
        
        translated = await translation_service.translate_document(
            document_content=text,
            target_lang=target_lang,
            style=style_enum,
            provider=provider
        )
        
        return {
            "success": True,
            "data": {
                "translated_content": translated,
                "target_lang": target_lang
            }
        }
    except Exception as e:
        logger.error(f"文档翻译失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages")
async def get_supported_languages():
    """获取支持的语言"""
    languages = [
        {"code": "zh", "name": "中文"},
        {"code": "en", "name": "英文"},
        {"code": "ja", "name": "日文"},
        {"code": "ko", "name": "韩文"},
        {"code": "fr", "name": "法文"},
        {"code": "de", "name": "德文"},
        {"code": "es", "name": "西班牙文"},
        {"code": "ru", "name": "俄文"}
    ]
    
    return {
        "success": True,
        "data": languages
    }

@router.post("/cache/clear")
async def clear_cache():
    """清空翻译缓存"""
    translation_service.clear_cache()
    return {
        "success": True,
        "message": "缓存已清空"
    }

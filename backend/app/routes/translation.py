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
from pathlib import Path
from sqlalchemy.orm import Session
from ..database import get_db

from ..services.translation import (
    translation_service, 
    TranslationRequest, 
    TranslationStyle
)
from ..services.document_parsers.pdf_math_translate_service import pdf_math_translate_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Translation"])

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
async def translate_text(request: TranslateRequest, db: Session = Depends(get_db)):
    """翻译文本"""
    logger.info(f"收到翻译请求: text={request.text[:50]}..., source={request.source_lang}, target={request.target_lang}")
    try:
        from ..services.llm.llm_config_service import LLMConfigService
        from ..services.llm.llm_client import llm_service
        
        logger.info("开始加载用户LLM配置...")
        user_configs = LLMConfigService.get_valid_configs(db, 1)
        logger.info(f"获取到用户配置: {user_configs}")
        if user_configs:
            logger.info(f"加载用户配置到llm_service: {user_configs}")
            llm_service.load_user_configs(user_configs)
            logger.info(f"llm_service当前配置: {llm_service.configs}")
        else:
            logger.warning("未找到有效的用户LLM配置")
        
        logger.info(f"检查可用providers: {llm_service.get_available_providers()}")
        
        style = TranslationStyle(request.style) if request.style in [e.value for e in TranslationStyle] else TranslationStyle.PROFESSIONAL
        
        logger.info(f"创建翻译请求: text长度={len(request.text)}, style={style}, provider={request.provider}")
        trans_request = TranslationRequest(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            style=style,
            provider=request.provider
        )
        
        logger.info("开始调用translation_service.translate...")
        result = await translation_service.translate(trans_request)
        logger.info(f"翻译完成: 结果长度={len(result.translated_text)}")
        
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
        import traceback
        logger.error(f"翻译失败: {e}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document")
async def translate_document(
    target_lang: str = "zh",
    style: str = "professional",
    provider: Optional[str] = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """翻译文档"""
    try:
        from ..services.llm.llm_config_service import LLMConfigService
        from ..services.llm.llm_client import llm_service
        
        user_configs = LLMConfigService.get_valid_configs(db, 1)
        if user_configs:
            llm_service.load_user_configs(user_configs)
        
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.error(f"文件解码失败: {e}")
            try:
                text = content.decode("gbk")
            except:
                text = content.decode("latin1", errors="replace")
        
        logger.info(f"文档翻译 - 内容长度: {len(text)}")
        
        style_enum = TranslationStyle(style) if style in [e.value for e in TranslationStyle] else TranslationStyle.PROFESSIONAL
        
        logger.info(f"开始文档翻译，共 {len(text)} 字符")
        
        progress = {"current": 0, "total": 0}
        
        def progress_callback(percent: float):
            progress["current"] = int(percent * 100)
            progress["total"] = 100
            logger.info(f"翻译进度: {progress['current']}%")
        
        translated = await translation_service.translate_document(
            document_content=text,
            target_lang=target_lang,
            style=style_enum,
            provider=provider,
            progress_callback=progress_callback
        )
        
        logger.info(f"文档翻译完成")
        
        return {
            "success": True,
            "data": {
                "translated_content": translated,
                "target_lang": target_lang
            }
        }
    except Exception as e:
        import traceback
        logger.error(f"文档翻译失败: {e}")
        logger.error(f"详细堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pdf")
async def translate_pdf(
    target_lang: str = "zh",
    source_lang: str = "en",
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """使用 PDFMathTranslate 翻译 PDF 文档（保留原文排版）"""
    from ..services.llm.llm_config_service import LLMConfigService
    from ..services.llm.llm_client import llm_service
    
    user_configs = LLMConfigService.get_valid_configs(db, 1)
    if user_configs:
        llm_service.load_user_configs(user_configs)
    
    if not pdf_math_translate_service.is_available():
        raise HTTPException(
            status_code=503, 
            detail="PDFMathTranslate 服务不可用"
        )
    
    import tempfile
    from pathlib import Path
    
    try:
        contents = await file.read()
        
        suffix = Path(file.filename).suffix.lower()
        if suffix != '.pdf':
            raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
        
        temp_dir = Path(tempfile.gettempdir()) / "pdf_translation"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = temp_dir / file.filename
        with open(input_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"开始翻译 PDF: {input_path}")
        
        result = pdf_math_translate_service.translate_pdf(
            pdf_path=str(input_path),
            lang_in=source_lang,
            lang_out=target_lang
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "翻译失败"))
        
        return {
            "success": True,
            "data": {
                "mono_pdf": result.get("mono_pdf"),
                "dual_pdf": result.get("dual_pdf"),
                "output_dir": result.get("output_dir"),
                "message": "PDF 翻译完成"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 翻译失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pdf-to-word")
async def translate_pdf_to_word(
    target_lang: str = "zh",
    source_lang: str = "en",
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """使用 PDF → Word → Ollama 方案翻译 PDF 文档（保留原文格式）"""
    from ..services.llm.llm_config_service import LLMConfigService
    from ..services.llm.llm_client import llm_service
    
    user_configs = LLMConfigService.get_valid_configs(db, 1)
    if user_configs:
        llm_service.load_user_configs(user_configs)
    
    import tempfile
    from pathlib import Path
    
    try:
        contents = await file.read()
        
        suffix = Path(file.filename).suffix.lower()
        if suffix != '.pdf':
            raise HTTPException(status_code=400, detail="仅支持 PDF 文件")
        
        temp_dir = Path(tempfile.gettempdir()) / "pdf_translation"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = temp_dir / file.filename
        with open(input_path, "wb") as f:
            f.write(contents)
        
        output_filename = f"{Path(file.filename).stem}_translated.docx"
        output_path = temp_dir / output_filename
        
        logger.info(f"开始翻译 PDF → Word: {input_path}")
        
        progress = {"current": 0, "total": 100}
        
        def progress_callback(percent: float):
            progress["current"] = int(percent * 100)
            logger.info(f"翻译进度: {progress['current']}%")
        
        result = await pdf_math_translate_service.translate_pdf_to_word(
            pdf_path=str(input_path),
            output_path=str(output_path),
            lang_in=source_lang,
            lang_out=target_lang,
            progress_callback=progress_callback
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "翻译失败"))
        
        logger.info(f"PDF → Word 翻译完成: {result['output_file']}")
        
        return {
            "success": True,
            "data": {
                "output_file": result.get("output_file"),
                "filename": output_filename,
                "message": "PDF 翻译完成，已生成 Word 文档"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF → Word 翻译失败: {e}")
        import traceback
        logger.error(f"详细堆栈: {traceback.format_exc()}")
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

@router.get("/files/download")
async def download_file(path: str):
    """下载翻译后的文件"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="路径不是文件")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

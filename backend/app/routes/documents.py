#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档解析路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os
import json
import time
from pathlib import Path
from pydantic import BaseModel

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse
from ..utils.auth import oauth2_scheme, verify_token
from ..services.document_parser import DocumentParser
from ..services.document_parsers.batch_api import BatchRequest, BatchResponse
from ..services.document_parsers.parser_manager import get_parser_manager

router = APIRouter()
parser = DocumentParser()
parser_manager = get_parser_manager()

# 批量处理端点
router_batch = APIRouter(prefix="/batch", tags=["batch-processing"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """上传文档文件"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件类型
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', 
                         '.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式: {file_ext}"
        )
    
    # 保存文件
    upload_dir = Path("uploads/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{user.id}_{file.filename}"
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 解析文档
        result = parser.parse_document(str(file_path))
        
        return {
            "success": True,
            "message": "文档上传成功",
            "file_path": str(file_path),
            "file_name": file.filename,
            "analysis_result": result
        }
        
    except Exception as e:
        # 删除上传的文件
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500, 
            detail=f"文档处理失败: {str(e)}"
        )

@router.post("/analyze")
async def analyze_document(
    file_path: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """分析已上传的文档"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        # 解析文档
        result = parser.parse_document(file_path)
        
        return {
            "success": True,
            "analysis_result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"文档分析失败: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文档格式"""
    # 获取支持的格式信息
    formats = parser.get_supported_formats()
    return {
        "current_support": formats.get("current_support", {}),
        "planned_support": formats.get("planned_support", {}),
        "note": formats.get("note", ""),
        "parsers_status": formats.get("parsers_status", {}),
        "parsers_loaded": len(formats.get("parsers_status", {}))
    }

# ==================== 批量处理端点 ====================

@router_batch.post("/upload-and-process")
async def upload_and_batch_process(
    files: List[UploadFile] = File(...),
    options: Dict[str, Any] = {},
    async_processing: bool = True,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """上传多个文件并进行批量处理"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件数量
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    
    if len(files) > 20:  # 限制批量处理数量
        raise HTTPException(status_code=400, detail="单次批量处理最多支持20个文件")
    
    # 允许的文件格式
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', 
                         '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.dxf', '.dwg']
    
    # 保存文件
    upload_dir = Path(f"uploads/documents/{user.id}/batch_{int(time.time())}")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_paths = []
    failed_files = []
    
    try:
        # 保存所有文件
        for file in files:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in allowed_extensions:
                failed_files.append({
                    "filename": file.filename,
                    "error": f"不支持的文件格式: {file_ext}"
                })
                continue
            
            file_path = upload_dir / f"{file.filename}"
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_paths.append(str(file_path))
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="没有有效的文件可以处理")
        
        # 准备批量处理请求
        batch_request = BatchRequest(
            file_paths=file_paths,
            options=options,
            async_processing=async_processing
        )
        
        # 导入批量处理API
        from ..services.document_parsers.batch_api import start_batch_processing, get_batch_processor
        
        # 启动批量处理
        processor = get_batch_processor()
        
        if async_processing:
            result = await start_batch_processing(batch_request, processor)
        else:
            # 同步处理
            batch_id = f"sync_batch_{int(time.time())}"
            sync_result = processor.process_batch_sync(file_paths)
            sync_result["batch_id"] = batch_id
            
            result = BatchResponse(
                batch_id=batch_id,
                status="completed",
                message="同步批量处理已完成"
            )
        
        return {
            "success": True,
            "message": "批量处理已启动",
            "batch_info": result,
            "uploaded_files": len(file_paths),
            "failed_files": failed_files,
            "file_paths": file_paths
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理已上传的文件
        for file_path in file_paths:
            try:
                Path(file_path).unlink()
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"批量处理启动失败: {str(e)}")

@router.get("/batch/{batch_id}/preview")
async def get_batch_file_preview(
    batch_id: str,
    file_index: int = 0,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取批量处理中特定文件的预览"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        from ..services.document_parsers.batch_api import get_batch_results, get_result_preview
        
        # 获取批量处理结果
        batch_results = await get_batch_results(batch_id, include_preview=True)
        
        if "file_previews" not in batch_results or file_index >= len(batch_results["file_previews"]):
            raise HTTPException(status_code=404, detail="文件预览不存在")
        
        return {
            "success": True,
            "batch_id": batch_id,
            "file_index": file_index,
            "preview": batch_results["file_previews"][file_index]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预览失败: {str(e)}")

@router.get("/batch/history")
async def get_user_batch_history(
    limit: int = 10,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户的批量处理历史"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        from ..services.document_parsers.batch_api import get_batch_history, get_batch_processor
        
        processor = get_batch_processor()
        history_data = await get_batch_history(limit=limit)
        
        return {
            "success": True,
            "user_id": user.id,
            "history": history_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

@router.get("/batch/{batch_id}/summary")
async def get_batch_summary(
    batch_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取批量处理摘要信息"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        from ..services.document_parsers.batch_api import get_batch_results
        
        batch_results = await get_batch_results(batch_id, include_preview=False)
        
        # 生成摘要信息
        summary = {
            "batch_id": batch_id,
            "processing_status": batch_results.get("status", "unknown"),
            "file_statistics": {
                "total": batch_results.get("summary", {}).get("total_files", 0),
                "completed": batch_results.get("summary", {}).get("completed_files", 0),
                "failed": batch_results.get("summary", {}).get("failed_files", 0)
            },
            "processing_performance": {
                "total_time": batch_results.get("summary", {}).get("processing_time", 0),
                "average_time_per_file": (
                    batch_results.get("summary", {}).get("processing_time", 0) / 
                    max(batch_results.get("summary", {}).get("total_files", 1), 1)
                )
            },
            "extraction_summary": batch_results.get("statistics", {}),
            "failed_files": batch_results.get("failed_files", [])
        }
        
        return {
            "success": True,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摘要失败: {str(e)}")

# 翻译请求模型
class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "en"
    target_lang: str = "zh"

@router.post("/translate")
async def translate_text(
    request: TranslateRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """翻译文本"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 调用翻译服务
        result = parser_manager.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")

# 报告生成请求模型
class ReportRequest(BaseModel):
    template_name: str
    data: Dict[str, Any]
    output_format: str = "pdf"

@router.post("/generate-report")
async def generate_report(
    request: ReportRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """生成报告"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 调用报告生成服务
        result = parser_manager.generate_report(
            template_name=request.template_name,
            data=request.data,
            output_format=request.output_format
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

@router.get("/report-templates")
async def list_report_templates(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取所有可用的报告模板"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 获取模板列表
        templates = parser_manager.report_generator.list_templates()
        
        return {
            "success": True,
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")
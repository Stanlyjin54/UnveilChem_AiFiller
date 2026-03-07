#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理进度跟踪API端点
"""

import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import time

from .batch_processor import BatchProcessor, ResultPreview
from .parser_manager import DocumentParserManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["batch-processing"])

# 全局实例
batch_processor = None
result_preview = None

def get_batch_processor() -> BatchProcessor:
    """获取批量处理器实例"""
    global batch_processor
    if batch_processor is None:
        parser_manager = DocumentParserManager()
        batch_processor = BatchProcessor(parser_manager)
    return batch_processor

def get_result_preview() -> ResultPreview:
    """获取结果预览实例"""
    global result_preview
    if result_preview is None:
        result_preview = ResultPreview()
    return result_preview

class BatchRequest(BaseModel):
    """批量处理请求模型"""
    file_paths: List[str]
    options: Optional[Dict[str, Any]] = {}
    async_processing: bool = True

class ProgressEvent(BaseModel):
    """进度事件模型"""
    event_type: str
    batch_id: str
    data: Dict[str, Any]
    timestamp: float

class BatchResponse(BaseModel):
    """批量处理响应模型"""
    batch_id: str
    status: str
    message: str
    estimated_completion_time: Optional[float] = None
    preview_url: Optional[str] = None

@router.post("/start", response_model=BatchResponse)
async def start_batch_processing(
    request: BatchRequest,
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """开始批量处理"""
    try:
        # 验证文件路径
        for file_path in request.file_paths:
            if not file_path:
                raise HTTPException(status_code=400, detail="文件路径不能为空")
        
        batch_id = f"batch_{int(time.time())}"
        
        # 创建进度回调
        progress_data = {}
        
        def progress_callback(data):
            progress_data.update(data)
        
        processor.add_progress_callback(progress_callback)
        
        # 根据配置选择处理方式
        if request.async_processing:
            # 异步处理
            result = await processor.process_batch_async(
                request.file_paths, 
                progress_callback=progress_callback
            )
        else:
            # 同步处理
            result = processor.process_batch_sync(
                request.file_paths, 
                progress_callback=progress_callback
            )
        
        # 生成预览
        if result.get("results"):
            preview = get_result_preview()
            for i, file_result in enumerate(result["results"]):
                cache_key = f"{batch_id}_{i}"
                preview.save_preview_cache(file_result, cache_key)
        
        return BatchResponse(
            batch_id=batch_id,
            status="started",
            message="批量处理已启动",
            estimated_completion_time=time.time() + result.get("processing_time", 0)
        )
        
    except Exception as e:
        logger.error(f"批量处理启动失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")

@router.get("/progress/{batch_id}")
async def get_batch_progress(
    batch_id: str,
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """获取批量处理进度"""
    try:
        # 从历史记录中查找
        history = processor.get_batch_history(limit=100)
        for batch_record in reversed(history):
            if batch_record.get("batch_id") == batch_id:
                return {
                    "batch_id": batch_id,
                    "status": batch_record.get("status", "unknown"),
                    "total_files": batch_record.get("total_files", 0),
                    "completed_files": batch_record.get("completed_files", 0),
                    "failed_files": batch_record.get("failed_files", 0),
                    "processing_time": batch_record.get("processing_time", 0),
                    "start_time": batch_record.get("start_time"),
                    "end_time": batch_record.get("end_time"),
                    "progress_percentage": (batch_record.get("completed_files", 0) / 
                                         max(batch_record.get("total_files", 1), 1)) * 100
                }
        
        raise HTTPException(status_code=404, detail="批量处理记录不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取进度失败: {str(e)}")

# @router.get("/stream/{batch_id}")
# async def stream_batch_progress(batch_id: str):
#     """流式推送进度更新"""
#     async def event_generator():
#         processor = get_batch_processor()
#         last_update = 0
        
#         while True:
#             try:
#                 # 获取最新进度
#                 history = processor.get_batch_history(limit=100)
#                 batch_record = None
                
#                 for record in reversed(history):
#                     if record.get("batch_id") == batch_id:
#                         batch_record = record
#                         break
                
#                 if batch_record and batch_record.get("end_time"):
#                     # 处理完成
#                     yield f"data: {json.dumps({
#                         'event': 'completed',
#                         'batch_id': batch_id,
#                         'result': batch_record
#                     }, ensure_ascii=False)}\n\n"
#                     break
                
#                 # 推送进度更新
#                 if batch_record:
#                     progress_data = {
#                         'event': 'progress',
#                         'batch_id': batch_id,
#                         'status': batch_record.get('status', 'processing'),
#                         'completed_files': batch_record.get('completed_files', 0),
#                         'failed_files': batch_record.get('failed_files', 0),
#                         'total_files': batch_record.get('total_files', 0),
#                         'processing_time': batch_record.get('processing_time', 0)
#                     }
                    
#                     yield f"data: {json.dumps(progress_data, ensure_ascii=False)}\n\n"
                
#                 # 等待1秒
#                 await asyncio.sleep(1)
                
#             except Exception as e:
#                 logger.error(f"进度流推送错误: {e}")
#                 yield f"data: {json.dumps({
#                     'event': 'error',
#                     'message': str(e)
#                 }, ensure_ascii=False)}\n\n"
#                 break
    
#     return EventSourceResponse(event_generator())

@router.get("/results/{batch_id}")
async def get_batch_results(
    batch_id: str,
    include_preview: bool = True,
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """获取批量处理结果"""
    try:
        # 查找批量处理记录
        history = processor.get_batch_history(limit=100)
        batch_record = None
        
        for record in reversed(history):
            if record.get("batch_id") == batch_id:
                batch_record = record
                break
        
        if not batch_record:
            raise HTTPException(status_code=404, detail="批量处理记录不存在")
        
        # 生成结果预览
        result_data = {
            "batch_id": batch_id,
            "status": batch_record.get("status"),
            "summary": {
                "total_files": batch_record.get("total_files", 0),
                "completed_files": batch_record.get("completed_files", 0),
                "failed_files": batch_record.get("failed_files", 0),
                "processing_time": batch_record.get("processing_time", 0)
            },
            "statistics": batch_record.get("statistics", {}),
            "failed_files": batch_record.get("failed_files", []),
            "processing_details": {
                "start_time": batch_record.get("start_time"),
                "end_time": batch_record.get("end_time"),
                "parser_performance": {}
            }
        }
        
        # 添加结果预览
        if include_preview and batch_record.get("results"):
            preview = get_result_preview()
            file_previews = []
            
            for i, file_result in enumerate(batch_record["results"]):
                cache_key = f"{batch_id}_{i}"
                file_preview = preview.get_cached_preview(cache_key)
                if not file_preview:
                    file_preview = preview.generate_preview(file_result)
                    preview.save_preview_cache(file_result, cache_key)
                
                file_previews.append(file_preview)
            
            result_data["file_previews"] = file_previews
        
        return result_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

@router.get("/history")
async def get_batch_history(
    limit: int = 10,
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """获取批量处理历史记录"""
    try:
        history = processor.get_batch_history(limit=limit)
        return {
            "history": history,
            "total_records": len(history),
            "performance_report": processor.get_performance_report()
        }
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")

@router.get("/performance")
async def get_performance_report(
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """获取性能报告"""
    try:
        return processor.get_performance_report()
    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取性能报告失败: {str(e)}")

@router.post("/cancel/{batch_id}")
async def cancel_batch_processing(
    batch_id: str,
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """取消批量处理"""
    try:
        # 这里需要实现取消逻辑
        # 可以通过设置取消标志来实现
        
        # 查找对应的批量处理记录
        history = processor.get_batch_history(limit=100)
        for record in reversed(history):
            if record.get("batch_id") == batch_id:
                # 标记为取消
                record["status"] = "cancelled"
                record["end_time"] = time.time()
                return {
                    "batch_id": batch_id,
                    "status": "cancelled",
                    "message": "批量处理已取消"
                }
        
        raise HTTPException(status_code=404, detail="批量处理记录不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消批量处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")

@router.delete("/history")
async def clear_batch_history(
    processor: BatchProcessor = Depends(get_batch_processor)
):
    """清理批量处理历史记录"""
    try:
        processor.batch_history.clear()
        preview = get_result_preview()
        preview.clear_cache()
        
        return {
            "message": "历史记录已清理",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"清理历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")
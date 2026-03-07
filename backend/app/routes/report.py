#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report API路由
提供报告生成功能接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..services.report import (
    report_generator,
    ReportRequest,
    ReportType,
    ReportFormat
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report", tags=["Report"])

class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    report_type: str
    source_data: Dict[str, Any]
    template: Optional[str] = None
    format: str = "markdown"
    title: Optional[str] = None
    custom_sections: Optional[List[str]] = None
    provider: Optional[str] = None

class GenerateReportResponse(BaseModel):
    """生成报告响应"""
    report_id: str
    content: str
    format: str
    created_at: str

@router.post("/generate")
async def generate_report(request: GenerateReportRequest):
    """生成报告"""
    try:
        report_type = ReportType(request.report_type) if request.report_type in [e.value for e in ReportType] else ReportType.PARAMETER_SUMMARY
        report_format = ReportFormat(request.format) if request.format in [e.value for e in ReportFormat] else ReportFormat.MARKDOWN
        
        report_request = ReportRequest(
            report_type=report_type,
            source_data=request.source_data,
            template=request.template,
            format=report_format,
            title=request.title,
            custom_sections=request.custom_sections,
            provider=request.provider
        )
        
        result = await report_generator.generate_report(report_request)
        
        return {
            "success": True,
            "data": {
                "report_id": result.report_id,
                "content": result.content,
                "format": result.format.value,
                "created_at": result.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameter_summary")
async def generate_parameter_summary(
    parameters: List[Dict[str, Any]],
    title: str = "参数汇总报告"
):
    """生成参数汇总报告"""
    try:
        result = await report_generator.generate_parameter_summary(
            parameters=parameters,
            title=title
        )
        
        return {
            "success": True,
            "data": {
                "report_id": result.report_id,
                "content": result.content,
                "created_at": result.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"参数汇总报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comparison")
async def generate_comparison_report(
    data_items: List[Dict[str, Any]],
    comparison_fields: List[str],
    title: str = "数据对比报告"
):
    """生成对比报告"""
    try:
        result = await report_generator.generate_comparison_report(
            data_items=data_items,
            comparison_fields=comparison_fields,
            title=title
        )
        
        return {
            "success": True,
            "data": {
                "report_id": result.report_id,
                "content": result.content,
                "created_at": result.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"对比报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_templates():
    """获取报告模板列表"""
    templates = [
        {
            "id": "parameter_summary",
            "name": "参数汇总报告",
            "type": ReportType.PARAMETER_SUMMARY.value,
            "description": "汇总文档中提取的参数信息"
        },
        {
            "id": "simulation_result",
            "name": "模拟结果报告",
            "type": ReportType.SIMULATION_RESULT.value,
            "description": "展示模拟运行结果和分析"
        },
        {
            "id": "data_comparison",
            "name": "数据对比报告",
            "type": ReportType.DATA_COMPARISON.value,
            "description": "对比分析多项数据"
        }
    ]
    
    return {
        "success": True,
        "data": templates
    }

@router.get("/formats")
async def list_formats():
    """获取支持的报告格式"""
    formats = [
        {"id": "markdown", "name": "Markdown", "extension": ".md"},
        {"id": "html", "name": "HTML", "extension": ".html"},
        {"id": "pdf", "name": "PDF", "extension": ".pdf"},
        {"id": "word", "name": "Word", "extension": ".docx"}
    ]
    
    return {
        "success": True,
        "data": formats
    }

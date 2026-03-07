#!/usr/bin/env python3
"""
报告服务模块
提供基于LLM的报告生成功能
"""

from .llm_report_generator import (
    LLMReportGenerator,
    ReportRequest,
    ReportResponse,
    ReportType,
    ReportFormat,
    ReportTemplate,
    report_generator
)

__all__ = [
    "LLMReportGenerator",
    "ReportRequest",
    "ReportResponse",
    "ReportType",
    "ReportFormat",
    "ReportTemplate",
    "report_generator"
]

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM报告生成服务
基于LLM的智能报告生成
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..llm import llm_service, prompt_manager

logger = logging.getLogger(__name__)

class ReportType(str, Enum):
    """报告类型"""
    PARAMETER_SUMMARY = "parameter_summary"
    SIMULATION_RESULT = "simulation_result"
    DATA_COMPARISON = "data_comparison"
    LITERATURE_REVIEW = "literature_review"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    """报告格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    WORD = "word"

@dataclass
class ReportRequest:
    """报告生成请求"""
    report_type: ReportType
    source_data: Dict[str, Any]
    template: Optional[str] = None
    format: ReportFormat = ReportFormat.MARKDOWN
    title: Optional[str] = None
    custom_sections: Optional[List[str]] = None
    provider: Optional[str] = None

@dataclass
class ReportResponse:
    """报告生成响应"""
    report_id: str
    content: str
    format: ReportFormat
    created_at: datetime

class ReportTemplate:
    """报告模板"""
    
    TEMPLATES = {
        ReportType.PARAMETER_SUMMARY: """# {title}

## 1. 概述

本报告汇总了从文档中提取的关键参数信息。

## 2. 提取的参数

{parameters_section}

## 3. 参数分类

{classification_section}

## 4. 建议

{recommendations_section}
""",

        ReportType.SIMULATION_RESULT: """# {title}

## 1. 模拟概述

{overview_section}

## 2. 模拟结果

{results_section}

## 3. 数据分析

{analysis_section}

## 4. 结论与建议

{conclusions_section}
""",

        ReportType.DATA_COMPARISON: """# {title}

## 1. 对比概述

{overview_section}

## 2. 数据对比

{comparison_section}

## 3. 差异分析

{difference_section}

## 4. 建议

{recommendations_section}
"""
    }
    
    @classmethod
    def get_template(cls, report_type: ReportType) -> str:
        """获取模板"""
        return cls.TEMPLATES.get(report_type, "")

class LLMReportGenerator:
    """基于LLM的报告生成器"""
    
    REPORT_PROMPTS = {
        ReportType.PARAMETER_SUMMARY: "report_parameter_summary",
        ReportType.SIMULATION_RESULT: "report_simulation_result",
        ReportType.DATA_COMPARISON: "report_data_comparison",
    }
    
    def __init__(self):
        self.llm = llm_service
        self.prompts = prompt_manager
        
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """生成报告"""
        
        content = ""
        
        if request.template:
            content = await self._generate_with_template(request)
        else:
            content = await self._generate_auto(request)
            
        return ReportResponse(
            report_id=self._generate_report_id(),
            content=content,
            format=request.format,
            created_at=datetime.now()
        )
    
    async def _generate_auto(self, request: ReportRequest) -> str:
        """自动生成报告"""
        
        prompt_key = self.REPORT_PROMPTS.get(request.report_type, "report_parameter_summary")
        
        prompt = self.prompts.get_prompt(
            prompt_key,
            data=json.dumps(request.source_data, ensure_ascii=False, indent=2)
        )
        
        if request.title:
            prompt = f"# {request.title}\n\n" + prompt
            
        if request.custom_sections:
            prompt += f"\n\n请包含以下章节：{', '.join(request.custom_sections)}"
            
        try:
            result = await self.llm.chat(
                prompt,
                provider=request.provider,
                temperature=0.5
            )
            return result
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            raise
    
    async def _generate_with_template(self, request: ReportRequest) -> str:
        """使用模板生成报告"""
        
        template = ReportTemplate.get_template(request.report_type)
        if not template:
            return await self._generate_auto(request)
            
        sections = {}
        for section in ["parameters_section", "classification_section", "overview_section", 
                       "results_section", "analysis_section", "comparison_section", 
                       "difference_section", "recommendations_section", "conclusions_section"]:
            if section in template:
                prompt = f"请从以下数据中提取{section.replace('_section', '')}部分的内容：\n\n{json.dumps(request.source_data, ensure_ascii=False)}"
                try:
                    sections[section] = await self.llm.chat(prompt, temperature=0.3)
                except:
                    sections[section] = "无数据"
                    
        title = request.title or "报告"
        
        try:
            return template.format(title=title, **sections)
        except KeyError as e:
            logger.warning(f"模板填充缺少字段: {e}")
            return await self._generate_auto(request)
    
    async def generate_comparison_report(
        self,
        data_items: List[Dict[str, Any]],
        comparison_fields: List[str],
        title: str = "数据对比报告"
    ) -> ReportResponse:
        """生成对比报告"""
        
        source_data = {
            "items": data_items,
            "comparison_fields": comparison_fields
        }
        
        request = ReportRequest(
            report_type=ReportType.DATA_COMPARISON,
            source_data=source_data,
            title=title,
            format=ReportFormat.MARKDOWN
        )
        
        return await self.generate_report(request)
    
    async def generate_parameter_summary(
        self,
        parameters: List[Dict[str, Any]],
        title: str = "参数汇总报告"
    ) -> ReportResponse:
        """生成参数汇总报告"""
        
        source_data = {"parameters": parameters}
        
        request = ReportRequest(
            report_type=ReportType.PARAMETER_SUMMARY,
            source_data=source_data,
            title=title,
            format=ReportFormat.MARKDOWN
        )
        
        return await self.generate_report(request)
    
    def _generate_report_id(self) -> str:
        """生成报告ID"""
        import uuid
        return f"report_{uuid.uuid4().hex[:12]}"

report_generator = LLMReportGenerator()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具编排器
协调各服务完成复杂任务
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ToolType(str, Enum):
    """工具类型"""
    DOCUMENT_PARSER = "document_parser"
    TRANSLATION = "translation"
    REPORT_GENERATOR = "report_generator"
    SIMULATION = "simulation"
    PARAMETER_MAPPER = "parameter_mapper"
    DATA_PROCESSOR = "data_processor"

@dataclass
class ToolExecution:
    """工具执行描述"""
    tool_name: str
    tool_type: ToolType
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_on_failure: bool = True
    max_retries: int = 3

@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    tool: ToolExecution
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class ToolOrchestrator:
    """工具编排器"""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self._register_tools()
        
    def _register_tools(self):
        """注册可用工具"""
        self.tools = {
            "document_parser": {
                "handler": self._execute_document_parser,
                "description": "文档解析",
                "supported_types": ["pdf", "docx", "xlsx", "txt"]
            },
            "translation": {
                "handler": self._execute_translation,
                "description": "文档翻译"
            },
            "report_generator": {
                "handler": self._execute_report_generator,
                "description": "报告生成"
            },
            "parameter_extractor": {
                "handler": self._execute_parameter_extractor,
                "description": "参数提取"
            },
            "parameter_mapper": {
                "handler": self._map_parameters,
                "description": "参数映射"
            },
            "aspen_plus": {
                "handler": self._execute_aspen_plus,
                "description": "Aspen Plus模拟"
            },
            "dwsim": {
                "handler": self._execute_dwsim,
                "description": "DWSIM模拟"
            }
        }
        
    async def execute_plan(
        self,
        execution_plan: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """执行完整的执行计划"""
        
        results = {}
        steps = []
        
        for i, step_config in enumerate(execution_plan.get("steps", [])):
            step = ExecutionStep(
                step_id=step_config.get("id", f"step_{i}"),
                tool=ToolExecution(
                    tool_name=step_config["tool"],
                    tool_type=ToolType(step_config.get("type", "data_processor")),
                    parameters=step_config.get("parameters", {}),
                    dependencies=step_config.get("dependencies", [])
                )
            )
            steps.append(step)
            
        total_steps = len(steps)
        
        for step in steps:
            if not self._check_dependencies(step.tool.dependencies, results):
                step.status = "failed"
                step.error = f"依赖未满足: {step.tool.dependencies}"
                continue
                
            try:
                step.status = "running"
                import time
                step.start_time = time.time()
                
                result = await self._execute_tool(
                    step.tool.tool_name,
                    step.tool.parameters,
                    results
                )
                
                step.status = "completed"
                step.result = result
                results[step.step_id] = result
                step.end_time = time.time()
                
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                logger.error(f"工具执行失败: {step.tool.tool_name}, 错误: {e}")
                
                if step.tool.retry_on_failure:
                    for retry in range(step.tool.max_retries):
                        try:
                            result = await self._execute_tool(
                                step.tool.tool_name,
                                step.tool.parameters,
                                results
                            )
                            step.status = "completed"
                            step.result = result
                            results[step.step_id] = result
                            break
                        except Exception as retry_error:
                            logger.warning(f"重试 {retry + 1}/{step.tool.max_retries} 失败")
                            continue
                            
            if progress_callback:
                completed = len([s for s in steps if s.status == "completed"])
                progress_callback(completed / total_steps)
                
        return {
            "status": "completed" if all(s.status == "completed" for s in steps) else "partial",
            "results": results,
            "steps": [
                {
                    "id": s.step_id,
                    "tool": s.tool.tool_name,
                    "status": s.status,
                    "error": s.error
                }
                for s in steps
            ]
        }
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """执行单个工具"""
        
        if tool_name not in self.tools:
            raise ValueError(f"未知工具: {tool_name}")
            
        tool_handler = self.tools[tool_name]["handler"]
        return await tool_handler(parameters, context)
    
    async def _execute_document_parser(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行文档解析"""
        from ..document_parsers.advanced_parser import AdvancedDocumentParser
        
        parser = AdvancedDocumentParser()
        file_path = parameters.get("file_path")
        
        result = await parser.parse_document(file_path)
        return result
    
    async def _execute_translation(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行翻译"""
        from ..translation import translation_service
        
        text = parameters.get("text") or context.get("parsed_content", "")
        target_lang = parameters.get("target_lang", "zh")
        
        if not text:
            return {"error": "没有可翻译的内容"}
            
        from ..translation import TranslationRequest
        result = await translation_service.translate(
            TranslationRequest(text=text, target_lang=target_lang)
        )
        
        return {"translated_text": result.translated_text}
    
    async def _execute_report_generator(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行报告生成"""
        from ..report import report_generator, ReportRequest, ReportType
        
        source_data = parameters.get("source_data") or context
        report_type = parameters.get("report_type", "parameter_summary")
        
        result = await report_generator.generate_report(
            ReportRequest(
                report_type=ReportType(report_type),
                source_data=source_data
            )
        )
        
        return {"report_content": result.content, "report_id": result.report_id}
    
    async def _execute_parameter_extractor(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行参数提取"""
        from ..document_parsers.advanced_parser import AdvancedDocumentParser
        
        parser = AdvancedDocumentParser()
        text = parameters.get("text") or context.get("parsed_content", "")
        
        if not text:
            return {"error": "没有可提取参数的文本"}
            
        extracted = await parser.extract_parameters(text)
        return extracted
    
    async def _map_parameters(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """参数映射"""
        from ..llm import llm_service, prompt_manager
        import json
        
        source = parameters.get("source_software", "generic")
        target = parameters.get("target_software", "generic")
        params = parameters.get("parameters", {})
        
        prompt = prompt_manager.get_prompt(
            "parameter_mapping",
            source_software=source,
            target_software=target,
            parameters=json.dumps(params, ensure_ascii=False)
        )
        
        try:
            result = await llm_service.chat_json(prompt, temperature=0.3)
            return result
        except Exception as e:
            logger.error(f"参数映射失败: {e}")
            return {"error": str(e)}
    
    async def _execute_aspen_plus(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行Aspen Plus模拟"""
        return {"error": "Aspen Plus集成尚未实现"}
    
    async def _execute_dwsim(
        self,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行DWSIM模拟"""
        return {"error": "DWSIM集成尚未实现"}
    
    def _check_dependencies(
        self,
        dependencies: List[str],
        results: Dict[str, Any]
    ) -> bool:
        """检查依赖是否满足"""
        for dep in dependencies:
            if dep not in results:
                return False
        return True

orchestrator = ToolOrchestrator()

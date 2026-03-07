#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent服务
智能任务处理核心服务
"""

import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field

from app.services.llm.llm_client import llm_service, ChatMessage
from app.services.llm.prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class TaskIntent(str, Enum):
    """任务意图枚举"""
    PARAMETER_EXTRACTION = "parameter_extraction"
    SIMULATION_RUN = "simulation_run"
    REPORT_GENERATION = "report_generation"
    DOCUMENT_TRANSLATION = "document_translation"
    SOFTWARE_OPERATION = "software_operation"
    GENERAL_CHAT = "general_chat"

@dataclass
class AgentRequest:
    """代理请求"""
    user_input: str
    context: Dict[str, Any] = field(default_factory=dict)
    attachments: List[str] = field(default_factory=list)
    target_software: Optional[str] = None
    provider: Optional[str] = None

@dataclass
class AgentResponse:
    """代理响应"""
    intent: TaskIntent
    confidence: float
    extracted_parameters: Dict[str, Any]
    suggested_actions: List[Dict[str, Any]]
    execution_plan: Optional[Dict[str, Any]]
    response_text: Optional[str] = None

class AgentService:
    """LLM代理服务"""
    
    def __init__(self, user_id: int = None):
        self.llm = llm_service
        self.prompts = prompt_manager
        self.user_id = user_id
        
    def load_user_llm_configs(self, db):
        """加载用户的LLM配置"""
        from ..services.llm.llm_config_service import LLMConfigService
        if self.user_id:
            configs = LLMConfigService.get_valid_configs(db, self.user_id)
            self.llm.load_user_configs(configs)
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """处理用户请求"""
        
        try:
            intent = await self._classify_intent(request.user_input)
            
            extracted_params = await self._extract_parameters(
                request.user_input,
                request.attachments,
                intent
            )
            
            if intent == TaskIntent.DOCUMENT_TRANSLATION:
                return await self._handle_translation(request, extracted_params)
            elif intent == TaskIntent.REPORT_GENERATION:
                return await self._handle_report_generation(request, extracted_params)
            elif intent == TaskIntent.GENERAL_CHAT:
                return await self._handle_chat(request)
            else:
                execution_plan = await self._generate_execution_plan(
                    intent,
                    extracted_params,
                    request.target_software
                )
                
                return AgentResponse(
                    intent=intent,
                    confidence=0.9,
                    extracted_parameters=extracted_params,
                    suggested_actions=execution_plan.get("steps", []) if execution_plan else [],
                    execution_plan=execution_plan
                )
        except Exception as e:
            logger.error(f"Agent处理请求失败: {e}")
            return AgentResponse(
                intent=TaskIntent.GENERAL_CHAT,
                confidence=0.0,
                extracted_parameters={},
                suggested_actions=[],
                execution_plan=None,
                response_text=f"处理请求时出错: {str(e)}"
            )
    
    async def _classify_intent(self, user_input: str) -> TaskIntent:
        """意图识别"""
        prompt = self.prompts.get_prompt("intent_classification", user_input=user_input)
        
        result = await self.llm.chat(
            prompt,
            provider=None,
            temperature=0.3
        )
        
        try:
            intent_str = result.strip().lower()
            for intent in TaskIntent:
                if intent.value == intent_str:
                    return intent
        except Exception as e:
            logger.warning(f"意图解析失败: {e}")
            
        return TaskIntent.GENERAL_CHAT
    
    async def _extract_parameters(
        self, 
        user_input: str, 
        attachments: List[str],
        intent: TaskIntent
    ) -> Dict[str, Any]:
        """参数提取"""
        if intent == TaskIntent.GENERAL_CHAT:
            return {}
            
        parameter_types = self._get_parameter_types(intent)
        
        input_text = user_input
        if attachments:
            input_text += f"\n\n附件: {', '.join(attachments)}"
            
        prompt = self.prompts.get_prompt(
            "parameter_extraction",
            parameter_types=json.dumps(parameter_types, ensure_ascii=False),
            input_text=input_text
        )
        
        try:
            result = await self.llm.chat_json(
                prompt,
                provider=None,
                temperature=0.2
            )
            return result.get("parameters", {})
        except Exception as e:
            logger.warning(f"参数提取失败: {e}")
            return {}
    
    def _get_parameter_types(self, intent: TaskIntent) -> Dict[str, Any]:
        """获取各意图类型的参数类型"""
        type_map = {
            TaskIntent.PARAMETER_EXTRACTION: {
                "temperature": "温度",
                "pressure": "压力",
                "flow_rate": "流量",
                "composition": "组成",
                "reaction_time": "反应时间"
            },
            TaskIntent.SIMULATION_RUN: {
                "simulation_file": "模拟文件",
                "operating_conditions": "操作条件",
                "convergence_criteria": "收敛标准"
            },
            TaskIntent.REPORT_GENERATION: {
                "report_type": "报告类型",
                "data_source": "数据源",
                "template": "模板"
            },
            TaskIntent.DOCUMENT_TRANSLATION: {
                "source_lang": "源语言",
                "target_lang": "目标语言",
                "translation_style": "翻译风格"
            }
        }
        return type_map.get(intent, {})
    
    async def _handle_translation(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理翻译请求"""
        target_lang = extracted_params.get("target_lang", "zh")
        style = extracted_params.get("translation_style", "professional")
        
        response_text = f"我将帮您翻译到{self._get_lang_name(target_lang)}。请提供需要翻译的文档内容或上传文档。"
        
        return AgentResponse(
            intent=TaskIntent.DOCUMENT_TRANSLATION,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "上传文档", "action": "upload_document"},
                {"label": "输入文本", "action": "input_text"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "tool": "document_parser",
                        "parameters": {"file": request.attachments}
                    },
                    {
                        "id": "step_2",
                        "tool": "translation",
                        "parameters": {"target_lang": target_lang, "style": style}
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_report_generation(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理报告生成请求"""
        report_type = extracted_params.get("report_type", "parameter_summary")
        
        response_text = f"我将帮您生成{self._get_report_type_name(report_type)}。请提供数据来源。"
        
        return AgentResponse(
            intent=TaskIntent.REPORT_GENERATION,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "上传数据文件", "action": "upload_data"},
                {"label": "选择已有数据", "action": "select_data"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "tool": "document_parser",
                        "parameters": {"file": request.attachments}
                    },
                    {
                        "id": "step_2",
                        "tool": "report_generator",
                        "parameters": {"report_type": report_type}
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_chat(self, request: AgentRequest) -> AgentResponse:
        """处理一般对话"""
        response_text = await self.llm.chat(
            request.user_input,
            system_prompt="你是一个化工领域助手，可以回答关于化工文档分析、参数提取、模拟软件使用等问题。",
            provider=request.provider
        )
        
        return AgentResponse(
            intent=TaskIntent.GENERAL_CHAT,
            confidence=0.9,
            extracted_parameters={},
            suggested_actions=[],
            execution_plan=None,
            response_text=response_text
        )
    
    async def _generate_execution_plan(
        self,
        intent: TaskIntent,
        extracted_params: Dict[str, Any],
        target_software: Optional[str]
    ) -> Dict[str, Any]:
        """生成执行计划"""
        prompt = self.prompts.get_prompt(
            "execution_plan",
            task_type=intent.value,
            parameters=json.dumps(extracted_params, ensure_ascii=False),
            target_software=target_software or "auto"
        )
        
        try:
            result = await self.llm.chat_json(
                prompt,
                temperature=0.3
            )
            return result
        except Exception as e:
            logger.warning(f"执行计划生成失败: {e}")
            return {"steps": [], "estimated_time": "未知"}
    
    def _get_lang_name(self, code: str) -> str:
        """语言代码转名称"""
        lang_map = {"zh": "中文", "en": "英文", "ja": "日文", "ko": "韩文", "fr": "法文", "de": "德文"}
        return lang_map.get(code, code)
    
    def _get_report_type_name(self, code: str) -> str:
        """报告类型代码转名称"""
        type_map = {
            "parameter_summary": "参数汇总报告",
            "simulation_result": "模拟结果报告",
            "data_comparison": "数据对比报告"
        }
        return type_map.get(code, "报告")

agent_service = AgentService()

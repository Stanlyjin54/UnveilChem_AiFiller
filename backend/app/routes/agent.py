#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent API路由
提供智能任务处理接口
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..services.agent import agent_service, AgentRequest, TaskIntent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])

class ProcessRequest(BaseModel):
    """处理请求"""
    user_input: str
    context: Dict[str, Any] = {}
    attachments: List[str] = []
    target_software: Optional[str] = None
    provider: Optional[str] = None

class IntentResponse(BaseModel):
    """意图响应"""
    name: str
    value: str
    description: str

INTENT_DESCRIPTIONS = {
    TaskIntent.PARAMETER_EXTRACTION: "从文档中提取参数",
    TaskIntent.SIMULATION_RUN: "运行化工模拟",
    TaskIntent.REPORT_GENERATION: "生成报告",
    TaskIntent.DOCUMENT_TRANSLATION: "翻译文档",
    TaskIntent.SOFTWARE_OPERATION: "操作软件",
    TaskIntent.GENERAL_CHAT: "一般对话"
}

@router.post("/process")
async def process_request(request: ProcessRequest):
    """处理用户请求"""
    try:
        agent_request = AgentRequest(
            user_input=request.user_input,
            context=request.context,
            attachments=request.attachments,
            target_software=request.target_software,
            provider=request.provider
        )
        
        response = await agent_service.process_request(agent_request)
        
        return {
            "success": True,
            "data": {
                "intent": response.intent.value,
                "confidence": response.confidence,
                "extracted_parameters": response.extracted_parameters,
                "suggested_actions": response.suggested_actions,
                "execution_plan": response.execution_plan,
                "response_text": response.response_text
            }
        }
    except Exception as e:
        logger.error(f"Agent处理请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/intents")
async def list_intents():
    """获取支持的意图类型"""
    intents = [
        {
            "name": intent.name,
            "value": intent.value,
            "description": INTENT_DESCRIPTIONS.get(intent, "")
        }
        for intent in TaskIntent
    ]
    
    return {
        "success": True,
        "data": intents
    }

@router.post("/execute_plan")
async def execute_plan(execution_plan: Dict[str, Any]):
    """执行生成的计划"""
    try:
        from ..services.orchestration.tool_orchestrator import ToolOrchestrator
        orchestrator = ToolOrchestrator()
        result = await orchestrator.execute_plan(execution_plan)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"执行计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

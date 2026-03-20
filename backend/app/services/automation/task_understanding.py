#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务理解服务
利用 LLM 理解用户的自然语言需求，自动规划执行步骤
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .skill import Skill, get_skill_registry, SkillMatchResult
from ..llm.llm_client import LLMClientBase, ChatMessage, LLMConfig

logger = logging.getLogger(__name__)


class ExecutionStep(BaseModel):
    """执行步骤"""
    step_id: int = Field(..., description="步骤ID")
    skill_name: str = Field(..., description="使用的 Skill 名称")
    action: str = Field(..., description="执行的操作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    depends_on: List[int] = Field(default_factory=list, description="依赖的前置步骤")
    description: str = Field(..., description="步骤描述")


class ExecutionPlan(BaseModel):
    """执行计划"""
    task_id: str = Field(..., description="任务ID")
    original_request: str = Field(..., description="原始用户请求")
    task_type: str = Field(..., description="任务类型")
    required_skills: List[str] = Field(default_factory=list, description="需要的 Skills")
    steps: List[ExecutionStep] = Field(default_factory=list, description="执行步骤")
    estimated_time: float = Field(0, description="预估执行时间（秒）")
    confidence: float = Field(0, description="置信度 (0-1)")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class TaskUnderstandingService:
    """任务理解服务"""

    TASK_UNDERSTANDING_PROMPT = """你是一个化工软件自动化助手。你的任务是将用户的自然语言请求转换为可执行的步骤计划。

## 可用技能 (Skills):
{skills_context}

## 用户请求:
{user_request}

## 输出要求:
请按以下 JSON 格式返回执行计划。不要添加任何解释或额外文本，只返回 JSON。

{{
    "task_type": "任务类型 (如: simulation, data_processing, document_analysis, etc)",
    "required_skills": ["需要的技能名称列表"],
    "confidence": 0.95,
    "estimated_time": 60.0,
    "steps": [
        {{
            "step_id": 1,
            "skill_name": "技能名称",
            "action": "操作名称",
            "parameters": {{参数键值对}},
            "depends_on": [],
            "description": "步骤描述"
        }}
    ]
}}

注意事项:
1. 只使用提供的 Skills，不要虚构不存在的技能
2. 确保参数与 Skill 定义的参数匹配
3. 如果请求不明确，设置较低的置信度
4. 步骤应该按逻辑顺序排列
"""

    def __init__(self, llm_client: Optional[LLMClientBase] = None):
        self.llm_client = llm_client
        self.skill_registry = get_skill_registry()

    def _build_skills_context(self, skills: List[Skill]) -> str:
        """构建 Skills 上下文"""
        context_parts = []
        for skill in skills:
            actions_str = ", ".join([a.name for a in skill.actions])
            context_parts.append(
                f"- {skill.name} ({skill.display_name}): {skill.description}\n"
                f"  关键词: {', '.join(skill.keywords)}\n"
                f"  可用操作: {actions_str}"
            )
        return "\n".join(context_parts)

    async def understand(
        self,
        user_request: str,
        max_steps: int = 10
    ) -> ExecutionPlan:
        """
        理解用户请求，生成执行计划

        Args:
            user_request: 用户自然语言请求
            max_steps: 最大步骤数

        Returns:
            ExecutionPlan: 包含步骤的执行计划
        """
        # 1. 获取所有启用的 Skills
        skills = self.skill_registry.get_enabled_skills()

        # 2. 构建上下文
        skills_context = self._build_skills_context(skills)

        # 3. 构建 Prompt
        prompt = self.TASK_UNDERSTANDING_PROMPT.format(
            skills_context=skills_context,
            user_request=user_request
        )

        # 4. 调用 LLM
        if self.llm_client:
            try:
                messages = [ChatMessage(role="user", content=prompt)]
                response = await self.llm_client.chat_with_json(messages)
                plan_data = json.loads(response) if isinstance(response, str) else response
            except Exception as e:
                logger.warning(f"LLM 调用失败，使用规则引擎降级: {e}")
                plan_data = self._fallback_plan(user_request)
        else:
            # 没有 LLM，使用规则引擎降级
            plan_data = self._fallback_plan(user_request)

        # 5. 构建执行计划
        task_id = str(uuid.uuid4())[:8]
        steps = []

        for step_data in plan_data.get("steps", [])[:max_steps]:
            step = ExecutionStep(
                step_id=step_data.get("step_id", len(steps) + 1),
                skill_name=step_data.get("skill_name", ""),
                action=step_data.get("action", ""),
                parameters=step_data.get("parameters", {}),
                depends_on=step_data.get("depends_on", []),
                description=step_data.get("description", "")
            )
            steps.append(step)

        plan = ExecutionPlan(
            task_id=task_id,
            original_request=user_request,
            task_type=plan_data.get("task_type", "unknown"),
            required_skills=plan_data.get("required_skills", []),
            steps=steps,
            estimated_time=plan_data.get("estimated_time", 0),
            confidence=plan_data.get("confidence", 0.5),
        )

        return plan

    def _fallback_plan(self, user_request: str) -> Dict[str, Any]:
        """
        降级方案：使用规则引擎解析请求
        当 LLM 不可用时的备选方案
        """
        user_request_lower = user_request.lower()

        matched_skills = self.skill_registry.search_by_keyword(user_request_lower)

        if not matched_skills:
            return {
                "task_type": "unknown",
                "required_skills": [],
                "confidence": 0.1,
                "estimated_time": 0,
                "steps": [],
                "error": "无法识别任务，请尝试更详细地描述您的需求"
            }

        best_match = matched_skills[0]
        skill = best_match.skill

        if skill.name == "dwsim":
            return self._generate_dwsim_fallback_plan(user_request, user_request_lower)

        action = "run_simulation"
        if "打开" in user_request or "加载" in user_request or "open" in user_request_lower or "读取" in user_request:
            action = "open"
        elif "设置" in user_request or "设置参数" in user_request:
            action = "set_parameters"
        elif "获取" in user_request or "结果" in user_request or "get" in user_request_lower or "读" in user_request:
            if skill.name == "dwsim":
                action = "get_results"
            else:
                action = "read_data"

        return {
            "task_type": "automation",
            "required_skills": [skill.name],
            "confidence": best_match.confidence,
            "estimated_time": 30.0,
            "steps": [
                {
                    "step_id": 1,
                    "skill_name": skill.name,
                    "action": action,
                    "parameters": {"request": user_request},
                    "depends_on": [],
                    "description": f"使用 {skill.display_name} 执行 {action}"
                }
            ]
        }

    def _generate_dwsim_fallback_plan(self, user_request: str, user_request_lower: str) -> Dict[str, Any]:
        """生成DWSIM任务的降级执行计划"""
        steps = []
        step_id = 1

        compound_keywords = {
            "water": "Water", "水": "Water",
            "ethanol": "Ethanol", "乙醇": "Ethanol",
            "methanol": "Methanol", "甲醇": "Methanol",
            "benzene": "Benzene", "苯": "Benzene",
            "toluene": "Toluene", "甲苯": "Toluene"
        }
        compounds = []
        for kw, compound in compound_keywords.items():
            if kw in user_request_lower:
                compounds.append(compound)
        compounds = list(set(compounds)) if compounds else ["Water", "Ethanol"]

        pp_keywords = {
            "peng-robinson": "Peng-Robinson (PR)", "pr": "Peng-Robinson (PR)",
            "srk": "Soave-Redlich-Kwong (SRK)", "soave": "Soave-Redlich-Kwong (SRK)",
            "nrtl": "NRTL", "uniquac": "UNIQUAC", "unifac": "UNIFAC"
        }
        property_package = "Peng-Robinson (PR)"
        for kw, pp in pp_keywords.items():
            if kw in user_request_lower:
                property_package = pp
                break

        equipment_keywords = {
            "pump": "pump", "泵": "pump",
            "compressor": "compressor", "压缩机": "compressor",
            "heater": "heater", "加热器": "heater", "加热炉": "heater",
            "cooler": "cooler", "冷却器": "cooler", "冷凝器": "cooler",
            "valve": "valve", "阀门": "valve",
            "mixer": "mixer", "混合器": "mixer",
            "splitter": "splitter", "分流器": "splitter",
            "heat_exchanger": "heat_exchanger", "换热器": "heat_exchanger",
            "reactor": "reactor", "反应器": "reactor",
            "distillation": "distillation_column", "精馏塔": "distillation_column", "蒸馏塔": "distillation_column",
            "flash": "flash_drum", "闪蒸": "flash_drum",
            "tank": "tank", "储罐": "tank"
        }

        is_create = any(kw in user_request_lower for kw in ["创建", "新建", "建立", "create", "new", "开始"])
        is_run = any(kw in user_request_lower for kw in ["运行", "计算", "仿真", "run", "calculate", "solve"])
        is_sensitivity = any(kw in user_request_lower for kw in ["灵敏度", "敏感性", "sensitivity", "sweep"])
        is_optimization = any(kw in user_request_lower for kw in ["优化", "最优", "optimize", "optimization"])
        is_add_equipment = any(kw in user_request_lower for kw in ["添加", "增加", "加入", "add"])
        is_load = any(kw in user_request_lower for kw in ["加载", "打开", "读取", "load", "open"])
        is_save = any(kw in user_request_lower for kw in ["保存", "存储", "save"])

        detected_equipment = None
        for kw, eq_type in equipment_keywords.items():
            if kw in user_request_lower:
                detected_equipment = eq_type
                break

        if is_load:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "load_flowsheet",
                "parameters": {"request": user_request},
                "depends_on": [step_id - 1],
                "description": "加载流程图"
            })
            step_id += 1

        elif is_sensitivity:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "sensitivity_analysis",
                "parameters": {
                    "variable_object": "Feed",
                    "variable_property": "Temperature",
                    "variable_range": [300, 350, 400],
                    "objective_object": "Product",
                    "objective_property": "MolarFlow"
                },
                "depends_on": [step_id - 1],
                "description": "执行灵敏度分析"
            })
            step_id += 1

        elif is_optimization:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "multi_objective_optimization",
                "parameters": {
                    "objectives": [],
                    "bounds": []
                },
                "depends_on": [step_id - 1],
                "description": "执行多目标优化"
            })
            step_id += 1

        elif is_add_equipment and detected_equipment:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": f"add_{detected_equipment}",
                "parameters": {
                    "name": f"{detected_equipment.capitalize()}_1",
                    "request": user_request
                },
                "depends_on": [step_id - 1],
                "description": f"添加{detected_equipment}"
            })
            step_id += 1

        elif is_create or is_run:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "create_flowsheet",
                "parameters": {},
                "depends_on": [step_id - 1],
                "description": "创建流程图"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "add_compounds",
                "parameters": {"compound_names": compounds},
                "depends_on": [step_id - 1],
                "description": f"添加化合物: {', '.join(compounds)}"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "create_and_add_property_package",
                "parameters": {"package_name": property_package},
                "depends_on": [step_id - 1],
                "description": f"添加物性包: {property_package}"
            })
            step_id += 1

            if is_run:
                steps.append({
                    "step_id": step_id,
                    "skill_name": "dwsim",
                    "action": "run_simulation",
                    "parameters": {},
                    "depends_on": [step_id - 1],
                    "description": "运行仿真计算"
                })
                step_id += 1
                steps.append({
                    "step_id": step_id,
                    "skill_name": "dwsim",
                    "action": "get_results",
                    "parameters": {},
                    "depends_on": [step_id - 1],
                    "description": "获取仿真结果"
                })
                step_id += 1

        elif is_save:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "save_flowsheet",
                "parameters": {"request": user_request},
                "depends_on": [step_id - 1],
                "description": "保存流程图"
            })
            step_id += 1

        else:
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "connect",
                "parameters": {},
                "depends_on": [],
                "description": "连接DWSIM"
            })
            step_id += 1
            steps.append({
                "step_id": step_id,
                "skill_name": "dwsim",
                "action": "run_simulation",
                "parameters": {"request": user_request},
                "depends_on": [step_id - 1],
                "description": "执行DWSIM操作"
            })
            step_id += 1

        return {
            "task_type": "dwsim_automation",
            "required_skills": ["dwsim"],
            "confidence": 0.8,
            "estimated_time": 60.0,
            "steps": steps
        }

    async def validate_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        验证执行计划的可行性

        Returns:
            验证结果，包含是否有效和错误列表
        """
        errors = []
        warnings = []

        # 1. 检查 Skill 是否存在
        for step in plan.steps:
            skill = self.skill_registry.get_skill(step.skill_name)
            if not skill:
                errors.append(f"步骤 {step.step_id}: Skill '{step.skill_name}' 不存在")
                continue

            # 2. 检查操作是否有效
            valid_actions = [a.name for a in skill.actions]
            if step.action not in valid_actions:
                warnings.append(
                    f"步骤 {step.step_id}: 操作 '{step.action}' 不是 Skill '{skill.name}' 的有效操作"
                )

            # 3. 检查依赖
            for dep in step.depends_on:
                if dep >= step.step_id:
                    errors.append(f"步骤 {step.step_id}: 依赖步骤 {dep} 不存在或循环依赖")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "plan": plan.model_dump()
        }


# 全局实例
_task_understanding_instance: Optional[TaskUnderstandingService] = None


def get_task_understanding_service(
    llm_client: Optional[LLMClientBase] = None
) -> TaskUnderstandingService:
    """获取任务理解服务实例"""
    global _task_understanding_instance
    if _task_understanding_instance is None:
        _task_understanding_instance = TaskUnderstandingService(llm_client)
    return _task_understanding_instance

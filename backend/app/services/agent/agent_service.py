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
    # DWSIM 特定意图
    DWSIM_CREATE_FLOWSHEET = "dwsim_create_flowsheet"
    DWSIM_RUN_SIMULATION = "dwsim_run_simulation"
    DWSIM_SENSITIVITY_ANALYSIS = "dwsim_sensitivity_analysis"
    DWSIM_OPTIMIZATION = "dwsim_optimization"
    DWSIM_ADD_EQUIPMENT = "dwsim_add_equipment"

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
            
            # DWSIM 特定意图处理
            if intent == TaskIntent.DWSIM_CREATE_FLOWSHEET:
                return await self._handle_dwsim_create_flowsheet(request, extracted_params)
            elif intent == TaskIntent.DWSIM_RUN_SIMULATION:
                return await self._handle_dwsim_run_simulation(request, extracted_params)
            elif intent == TaskIntent.DWSIM_SENSITIVITY_ANALYSIS:
                return await self._handle_dwsim_sensitivity_analysis(request, extracted_params)
            elif intent == TaskIntent.DWSIM_OPTIMIZATION:
                return await self._handle_dwsim_optimization(request, extracted_params)
            elif intent == TaskIntent.DWSIM_ADD_EQUIPMENT:
                return await self._handle_dwsim_add_equipment(request, extracted_params)
            # 通用意图处理
            elif intent == TaskIntent.DOCUMENT_TRANSLATION:
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
        """意图识别 - 增强版，优先识别DWSIM相关意图"""
        user_input_lower = user_input.lower()
        
        dwsim_keywords = [
            "dwsim", "流程模拟", "化工仿真", "精馏", "吸收", "反应器", "换热", "加热器", "冷却器",
            "泵", "压缩机", "阀门", "混合器", "分流器", "闪蒸", "塔", "灵敏度分析", "优化",
            "物料流", "物性包", "化合物", "仿真计算", "流程图"
        ]
        
        is_dwsim_related = any(kw in user_input_lower for kw in dwsim_keywords)
        
        if is_dwsim_related:
            dwsim_intent = await self._classify_dwsim_intent(user_input)
            if dwsim_intent:
                return dwsim_intent
        
        prompt = self.prompts.get_prompt("intent_classification", user_input=user_input)
        
        result = await self.llm.chat(
            prompt,
            provider=None,
            temperature=0.3,
            enable_thinking=False
        )
        
        try:
            intent_str = result.strip().lower()
            for intent in TaskIntent:
                if intent.value == intent_str:
                    return intent
        except Exception as e:
            logger.warning(f"意图解析失败: {e}")
            
        return TaskIntent.GENERAL_CHAT
    
    async def _classify_dwsim_intent(self, user_input: str) -> Optional[TaskIntent]:
        """识别DWSIM特定意图"""
        user_input_lower = user_input.lower()
        
        create_patterns = ["创建", "新建", "建立", "create", "new", "开始"]
        run_patterns = ["运行", "计算", "仿真", "run", "calculate", "solve"]
        sensitivity_patterns = ["灵敏度", "敏感性", "分析", "sensitivity", "sweep"]
        optimization_patterns = ["优化", "最优", "optimize", "optimization"]
        equipment_patterns = ["添加", "增加", "加入", "add", "泵", "压缩机", "加热", "冷却", "阀门", "混合", "反应器", "塔", "换热器"]
        stream_patterns = ["物料流", "进料", "出料", "stream", "feed", "product"]
        load_patterns = ["加载", "打开", "读取", "load", "open"]
        save_patterns = ["保存", "存储", "save"]
        connect_patterns = ["连接", "connect"]
        result_patterns = ["结果", "获取", "查看", "result", "get", "view"]
        
        if any(p in user_input_lower for p in sensitivity_patterns):
            return TaskIntent.DWSIM_SENSITIVITY_ANALYSIS
        if any(p in user_input_lower for p in optimization_patterns):
            return TaskIntent.DWSIM_OPTIMIZATION
        if any(p in user_input_lower for p in run_patterns) and not any(p in user_input_lower for p in create_patterns):
            return TaskIntent.DWSIM_RUN_SIMULATION
        if any(p in user_input_lower for p in equipment_patterns):
            return TaskIntent.DWSIM_ADD_EQUIPMENT
        if any(p in user_input_lower for p in create_patterns):
            return TaskIntent.DWSIM_CREATE_FLOWSHEET
        
        prompt = self.prompts.get_prompt("dwsim_intent_classification", user_input=user_input)
        try:
            result = await self.llm.chat(
                prompt,
                provider=None,
                temperature=0.2,
                enable_thinking=False
            )
            intent_str = result.strip().lower()
            for intent in TaskIntent:
                if intent.value == intent_str:
                    return intent
        except Exception as e:
            logger.warning(f"DWSIM意图解析失败: {e}")
        
        return None
    
    async def _extract_parameters(
        self, 
        user_input: str, 
        attachments: List[str],
        intent: TaskIntent
    ) -> Dict[str, Any]:
        """参数提取 - 增强版，支持DWSIM特定参数"""
        if intent == TaskIntent.GENERAL_CHAT:
            return {}
        
        dwsim_intents = [
            TaskIntent.DWSIM_CREATE_FLOWSHEET,
            TaskIntent.DWSIM_RUN_SIMULATION,
            TaskIntent.DWSIM_SENSITIVITY_ANALYSIS,
            TaskIntent.DWSIM_OPTIMIZATION,
            TaskIntent.DWSIM_ADD_EQUIPMENT
        ]
        
        if intent in dwsim_intents:
            return await self._extract_dwsim_parameters(user_input, intent)
        
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
                temperature=0.2,
                enable_thinking=False
            )
            return result.get("parameters", {})
        except Exception as e:
            logger.warning(f"参数提取失败: {e}")
            return {}
    
    async def _extract_dwsim_parameters(
        self, 
        user_input: str, 
        intent: TaskIntent
    ) -> Dict[str, Any]:
        """提取DWSIM特定参数"""
        prompt = self.prompts.get_prompt(
            "dwsim_parameter_extraction",
            input_text=user_input
        )
        
        try:
            result = await self.llm.chat_json(
                prompt,
                provider=None,
                temperature=0.2,
                enable_thinking=False
            )
            params = result.get("parameters", {})
            
            if intent == TaskIntent.DWSIM_ADD_EQUIPMENT:
                equipment_prompt = self.prompts.get_prompt(
                    "dwsim_equipment_mapping",
                    input_text=user_input
                )
                try:
                    equipment_result = await self.llm.chat_json(
                        equipment_prompt,
                        provider=None,
                        temperature=0.2,
                        enable_thinking=False
                    )
                    params.update(equipment_result)
                except Exception as e:
                    logger.warning(f"设备映射失败: {e}")
            
            return params
        except Exception as e:
            logger.warning(f"DWSIM参数提取失败: {e}")
            return self._fallback_dwsim_parameters(user_input, intent)
    
    def _fallback_dwsim_parameters(self, user_input: str, intent: TaskIntent) -> Dict[str, Any]:
        """DWSIM参数提取降级方案"""
        params = {}
        user_input_lower = user_input.lower()
        
        compound_keywords = {
            "water": "Water", "水": "Water",
            "ethanol": "Ethanol", "乙醇": "Ethanol",
            "methanol": "Methanol", "甲醇": "Methanol",
            "benzene": "Benzene", "苯": "Benzene",
            "toluene": "Toluene", "甲苯": "Toluene"
        }
        
        compounds = []
        for kw, compound in compound_keywords.items():
            if kw in user_input_lower:
                compounds.append(compound)
        if compounds:
            params["compounds"] = list(set(compounds))
        
        pp_keywords = {
            "peng-robinson": "Peng-Robinson (PR)", "pr": "Peng-Robinson (PR)",
            "srk": "Soave-Redlich-Kwong (SRK)", "soave": "Soave-Redlich-Kwong (SRK)",
            "nrtl": "NRTL", "uniquac": "UNIQUAC", "unifac": "UNIFAC"
        }
        for kw, pp in pp_keywords.items():
            if kw in user_input_lower:
                params["property_package"] = pp
                break
        
        equipment_keywords = {
            "pump": "pump", "泵": "pump",
            "compressor": "compressor", "压缩机": "compressor",
            "heater": "heater", "加热器": "heater", "加热炉": "heater",
            "cooler": "cooler", "冷却器": "cooler", "冷凝器": "cooler",
            "valve": "valve", "阀门": "valve",
            "mixer": "mixer", "混合器": "mixer",
            "splitter": "splitter", "分流器": "splitter",
            "reactor": "reactor", "反应器": "reactor",
            "distillation": "distillation_column", "精馏塔": "distillation_column", "蒸馏塔": "distillation_column",
            "flash": "flash_drum", "闪蒸": "flash_drum",
            "tank": "tank", "储罐": "tank"
        }
        for kw, eq_type in equipment_keywords.items():
            if kw in user_input_lower:
                params["equipment_type"] = eq_type
                break
        
        return params
    
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
            },
            TaskIntent.DWSIM_CREATE_FLOWSHEET: {
                "compounds": "化合物列表，如['Water', 'Ethanol']",
                "property_package": "物性包名称",
                "streams": "物料流列表",
                "equipment": "设备列表"
            },
            TaskIntent.DWSIM_RUN_SIMULATION: {
                "compounds": "化合物列表",
                "property_package": "物性包名称",
                "streams": "物料流参数",
                "equipment": "设备参数",
                "connections": "连接关系"
            },
            TaskIntent.DWSIM_SENSITIVITY_ANALYSIS: {
                "variable_object": "变化变量所属对象",
                "variable_property": "变化变量属性",
                "variable_range": "变量变化范围",
                "objective_object": "目标对象",
                "objective_property": "目标属性"
            },
            TaskIntent.DWSIM_OPTIMIZATION: {
                "objectives": "优化目标列表",
                "bounds": "参数边界",
                "population_size": "种群大小",
                "generations": "迭代代数"
            },
            TaskIntent.DWSIM_ADD_EQUIPMENT: {
                "equipment_type": "设备类型(pump/compressor/heater/cooler/valve/mixer/splitter/heat_exchanger/reactor/distillation_column/flash_drum/tank)",
                "equipment_name": "设备名称",
                "parameters": "设备参数"
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
            provider=request.provider,
            enable_thinking=False
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
                temperature=0.3,
                enable_thinking=False
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
    
    # ==================== DWSIM 特定意图处理 ====================
    
    async def _handle_dwsim_create_flowsheet(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理 DWSIM 创建流程图请求"""
        compounds = extracted_params.get("compounds", ["Water", "Ethanol"])
        property_package = extracted_params.get("property_package", "Peng-Robinson (PR)")
        
        response_text = f"我将帮您在 DWSIM 中创建流程图，包含化合物: {', '.join(compounds)}，使用 {property_package} 物性包。"
        
        return AgentResponse(
            intent=TaskIntent.DWSIM_CREATE_FLOWSHEET,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "添加物料流", "action": "add_stream"},
                {"label": "添加设备", "action": "add_equipment"},
                {"label": "运行仿真", "action": "run_simulation"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "skill": "dwsim",
                        "action": "connect",
                        "parameters": {}
                    },
                    {
                        "id": "step_2",
                        "skill": "dwsim",
                        "action": "create_flowsheet",
                        "parameters": {}
                    },
                    {
                        "id": "step_3",
                        "skill": "dwsim",
                        "action": "add_compounds",
                        "parameters": {"compound_names": compounds}
                    },
                    {
                        "id": "step_4",
                        "skill": "dwsim",
                        "action": "create_and_add_property_package",
                        "parameters": {"package_name": property_package}
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_dwsim_run_simulation(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理 DWSIM 运行仿真请求"""
        response_text = "我将帮您运行 DWSIM 仿真计算。"
        
        return AgentResponse(
            intent=TaskIntent.DWSIM_RUN_SIMULATION,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "查看结果", "action": "get_results"},
                {"label": "保存流程图", "action": "save_flowsheet"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "skill": "dwsim",
                        "action": "run_simulation",
                        "parameters": extracted_params
                    },
                    {
                        "id": "step_2",
                        "skill": "dwsim",
                        "action": "get_results",
                        "parameters": {}
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_dwsim_sensitivity_analysis(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理 DWSIM 灵敏度分析请求"""
        variable_object = extracted_params.get("variable_object", "Feed")
        variable_property = extracted_params.get("variable_property", "Temperature")
        variable_range = extracted_params.get("variable_range", [300, 350, 400])
        objective_object = extracted_params.get("objective_object", "Product")
        objective_property = extracted_params.get("objective_property", "MolarFlow")
        
        response_text = f"我将帮您执行灵敏度分析，变化 {variable_object}.{variable_property}，观察 {objective_object}.{objective_property}。"
        
        return AgentResponse(
            intent=TaskIntent.DWSIM_SENSITIVITY_ANALYSIS,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "查看分析结果", "action": "view_analysis"},
                {"label": "导出数据", "action": "export_data"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "skill": "dwsim",
                        "action": "sensitivity_analysis",
                        "parameters": {
                            "variable_object": variable_object,
                            "variable_property": variable_property,
                            "variable_range": variable_range,
                            "objective_object": objective_object,
                            "objective_property": objective_property
                        }
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_dwsim_optimization(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理 DWSIM 优化请求"""
        objectives = extracted_params.get("objectives", [])
        bounds = extracted_params.get("bounds", [])
        
        response_text = "我将帮您执行 DWSIM 参数优化。"
        
        return AgentResponse(
            intent=TaskIntent.DWSIM_OPTIMIZATION,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "查看优化结果", "action": "view_optimization"},
                {"label": "应用最优参数", "action": "apply_optimal"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "skill": "dwsim",
                        "action": "multi_objective_optimization",
                        "parameters": {
                            "objectives": objectives,
                            "bounds": bounds
                        }
                    }
                ]
            },
            response_text=response_text
        )
    
    async def _handle_dwsim_add_equipment(
        self, 
        request: AgentRequest, 
        extracted_params: Dict[str, Any]
    ) -> AgentResponse:
        """处理 DWSIM 添加设备请求"""
        equipment_type = extracted_params.get("equipment_type", "heater")
        equipment_name = extracted_params.get("equipment_name", "Equipment_1")
        parameters = extracted_params.get("parameters", {})
        
        equipment_names = {
            "pump": "泵",
            "compressor": "压缩机",
            "heater": "加热器",
            "cooler": "冷却器",
            "valve": "阀门",
            "mixer": "混合器",
            "splitter": "分流器",
            "heat_exchanger": "换热器",
            "reactor": "反应器",
            "distillation_column": "精馏塔",
            "flash_drum": "闪蒸罐",
            "tank": "储罐"
        }
        
        response_text = f"我将帮您添加{equipment_names.get(equipment_type, equipment_type)}: {equipment_name}。"
        
        return AgentResponse(
            intent=TaskIntent.DWSIM_ADD_EQUIPMENT,
            confidence=0.95,
            extracted_parameters=extracted_params,
            suggested_actions=[
                {"label": "连接物料流", "action": "connect_stream"},
                {"label": "设置参数", "action": "set_parameters"},
                {"label": "运行仿真", "action": "run_simulation"}
            ],
            execution_plan={
                "steps": [
                    {
                        "id": "step_1",
                        "skill": "dwsim",
                        "action": f"add_{equipment_type}",
                        "parameters": {
                            "name": equipment_name,
                            "parameters": parameters
                        }
                    }
                ]
            },
            response_text=response_text
        )

agent_service = AgentService()

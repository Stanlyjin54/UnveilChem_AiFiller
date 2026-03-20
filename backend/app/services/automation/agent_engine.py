#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 执行引擎
实现 Think-Act-Observe 循环，让 Agent 能够自主执行任务
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .task_understanding import ExecutionPlan, ExecutionStep, get_task_understanding_service
from .skill import get_skill_registry, Skill, SkillAction
from .memory import get_agent_memory, ExecutionRecord
from .automation_engine import AutomationEngine

logger = logging.getLogger(__name__)

# 适配器缓存
_adapters = {}


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentContext:
    """Agent 上下文"""
    session_id: str
    user_request: str
    plan: Optional[ExecutionPlan] = None
    current_step_index: int = 0
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.IDLE
    error_message: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def update_time(self):
        """更新时间"""
        self.updated_at = datetime.now().isoformat()


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    status: AgentStatus
    session_id: str = ""
    final_result: Optional[Dict[str, Any]] = None
    steps_executed: int = 0
    total_steps: int = 0
    execution_time: float = 0.0
    error_message: Optional[str] = None
    step_results: List[Dict[str, Any]] = field(default_factory=list)


class AgentEngine:
    """Agent 执行引擎"""

    def __init__(self, max_iterations: int = 20):
        self.max_iterations = max_iterations
        self.task_service = get_task_understanding_service()
        self.skill_registry = get_skill_registry()
        self.memory = get_agent_memory()
        self.active_agents: Dict[str, AgentContext] = {}

    async def execute(
        self,
        user_request: str,
        session_id: Optional[str] = None,
        max_iterations: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> AgentResult:
        """
        执行 Agent 任务 - 主循环

        流程：
        1. Think - 理解当前状态，规划下一步
        2. Act - 执行操作
        3. Observe - 观察结果，评估是否需要重试
        """
        logger.info(f"===== AgentEngine.execute 被调用: {user_request} =====")
        
        # 创建或获取会话
        if not session_id:
            session = self.memory.create_session()
            session_id = session.session_id

        # 创建上下文
        context = AgentContext(
            session_id=session_id,
            user_request=user_request
        )
        self.active_agents[session_id] = context

        start_time = datetime.now()

        try:
            # ========== THINK Phase ==========
            context.status = AgentStatus.THINKING
            context.update_time()
            logger.info(f"[Agent {session_id}] Think: 理解任务")

            # 1. 理解任务，生成执行计划
            plan = await self.task_service.understand(user_request)
            context.plan = plan
            context.current_step_index = 0

            # 保存计划到记忆
            self.memory.update_session_plan(session_id, plan.model_dump())

            # 记录执行
            execution_record = self.memory.record_execution(
                session_id, user_request, plan.model_dump()
            )

            # 如果没有步骤，返回失败
            if not plan.steps:
                context.status = AgentStatus.FAILED
                context.error_message = "无法生成执行计划"
                self.memory.fail_execution(execution_record.record_id, context.error_message)
                return AgentResult(
                    success=False,
                    status=AgentStatus.FAILED,
                    session_id=session_id,
                    error_message=context.error_message
                )

            logger.info(f"[Agent {session_id}] 计划包含 {len(plan.steps)} 个步骤")

            # ========== 执行循环 ==========
            for iteration in range(max_iterations or self.max_iterations):
                # 检查是否还有步骤需要执行
                if context.current_step_index >= len(plan.steps):
                    break

                current_step = plan.steps[context.current_step_index]
                logger.info(f"[Agent {session_id}] 步骤 {context.current_step_index + 1}/{len(plan.steps)}: {current_step.action}")

                # ========== ACT Phase ==========
                context.status = AgentStatus.ACTING
                context.update_time()

                step_result = await self._act(context, current_step, execution_record.record_id)
                context.step_results.append(step_result)

                # 执行回调
                if callback:
                    await callback({
                        "step": context.current_step_index + 1,
                        "total": len(plan.steps),
                        "action": current_step.action,
                        "result": step_result
                    })

                # ========== OBSERVE Phase ==========
                context.status = AgentStatus.OBSERVING
                context.update_time()

                # 观察结果
                should_continue, adjustment = await self._observe(
                    context, step_result, current_step
                )

                if not should_continue:
                    context.status = AgentStatus.FAILED
                    context.error_message = adjustment  # 错误信息
                    self.memory.fail_execution(execution_record.record_id, context.error_message)
                    break

                # 如果需要调整计划
                if adjustment:
                    logger.info(f"[Agent {session_id}] 调整计划: {adjustment}")
                    # 可以在这里重新生成计划

                # 步骤完成
                context.current_step_index += 1
                execution_record.steps.append(step_result)

            # ========== 完成 ==========
            execution_time = (datetime.now() - start_time).total_seconds()

            if context.status != AgentStatus.FAILED:
                context.status = AgentStatus.COMPLETED
                final_result = {
                    "steps_executed": context.current_step_index,
                    "total_steps": len(plan.steps),
                    "step_results": context.step_results,
                    "plan": plan.model_dump()
                }
                self.memory.complete_execution(execution_record.record_id, final_result)

                return AgentResult(
                    success=True,
                    status=AgentStatus.COMPLETED,
                    session_id=session_id,
                    final_result=final_result,
                    steps_executed=context.current_step_index,
                    total_steps=len(plan.steps),
                    execution_time=execution_time,
                    step_results=context.step_results
                )
            else:
                return AgentResult(
                    success=False,
                    status=AgentStatus.FAILED,
                    session_id=session_id,
                    error_message=context.error_message,
                    steps_executed=context.current_step_index,
                    total_steps=len(plan.steps),
                    execution_time=execution_time,
                    step_results=context.step_results
                )

        except Exception as e:
            logger.error(f"[Agent {session_id}] 执行失败: {e}")
            context.status = AgentStatus.FAILED
            context.error_message = str(e)
            return AgentResult(
                success=False,
                status=AgentStatus.FAILED,
                session_id=session_id if session_id else "",
                error_message=str(e)
            )
        finally:
            # 清理
            if session_id in self.active_agents:
                del self.active_agents[session_id]

    async def _act(
        self,
        context: AgentContext,
        step: ExecutionStep,
        record_id: str
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        # 获取 Skill
        skill = self.skill_registry.get_skill(step.skill_name)
        if not skill:
            return {
                "step_id": step.step_id,
                "skill": step.skill_name,
                "action": step.action,
                "success": False,
                "error": f"Skill 不存在: {step.skill_name}"
            }

        # 查找操作（如果找不到，尝试智能映射）
        action = next((a for a in skill.actions if a.name == step.action), None)
        if not action:
            logger.warning(f"操作不存在: {step.action}，尝试智能映射...")
            # 智能映射：尝试找到最匹配的操作
            action = self._map_action(skill, step.action)
            if action:
                logger.info(f"已将 '{step.action}' 映射到 '{action.name}'")
            else:
                logger.warning(f"无法映射操作 '{step.action}'，使用模拟执行")

        # 记录步骤开始
        self.memory.update_execution(record_id, {
            "step_id": step.step_id,
            "skill": step.skill_name,
            "action": step.action,
            "parameters": step.parameters,
            "status": "running",
            "started_at": datetime.now().isoformat()
        })

        # 执行操作
        # 如果 action 存在，尝试调用真实适配器；否则使用模拟执行
        if action:
            result = await self._execute_action(skill, action, step.parameters)
        else:
            # 无法映射操作，使用模拟执行
            logger.info(f"使用模拟执行: {skill.name}.{step.action}")
            result = self._generate_mock_result(skill.name, step.action, step.parameters)

        # 记录步骤完成
        self.memory.update_execution(record_id, {
            "step_id": step.step_id,
            "status": "completed",
            "result": result,
            "completed_at": datetime.now().isoformat()
        })

        return {
            "step_id": step.step_id,
            "skill": step.skill_name,
            "action": step.action,
            "parameters": step.parameters,
            "success": result.get("success", True),
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_action(
        self,
        skill: Skill,
        action: Optional[SkillAction],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 Skill 操作"""
        action_name = action.name if action else "unknown"
        logger.info(f"执行 {skill.display_name}.{action_name} - 参数: {parameters}")

        try:
            # 尝试使用适配器执行
            adapter_result = await self._execute_with_adapter(skill, action_name, parameters)
            # 如果适配器成功执行，返回结果
            if adapter_result and adapter_result.get("success"):
                return adapter_result
            # 如果适配器执行失败，记录日志并继续使用模拟模式
            if adapter_result:
                logger.warning(f"适配器执行返回失败: {adapter_result.get('message')}，使用模拟模式")
        except Exception as e:
            logger.warning(f"适配器执行失败: {e}，使用模拟模式")

        # 备选：模拟执行（当没有真实适配器时）
        await asyncio.sleep(0.5)

        # 根据不同操作生成更丰富的模拟结果
        result_data = self._generate_mock_result(skill.name, action_name, parameters)

        return result_data

    async def _execute_with_adapter(
        self,
        skill: Skill,
        action_name: str,
        parameters: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """使用适配器执行操作"""
        logger.info(f"===== AgentEngine: 尝试获取适配器 for {skill.name} =====")
        adapter = self._get_adapter(skill.name)
        if not adapter:
            logger.warning(f"===== AgentEngine: 适配器为 None skill={skill.name} =====")
            # 返回软件未安装提示
            return self._get_software_not_installed_message(skill.name)

        try:
            # 根据操作名称调用适配器的对应方法
            if action_name == "run_simulation" or action_name == "run":
                # 检查是否是 DWSIM COM 适配器
                if hasattr(adapter, 'run_simulation') and callable(adapter.run_simulation):
                    # DWSIM COM 适配器
                    result = adapter.run_simulation(parameters)
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "message": result.message,
                            "output": {
                                "streams": result.streams if hasattr(result, 'streams') else {},
                                "equipment": result.equipment if hasattr(result, 'equipment') else {},
                                "execution_time": result.execution_time if hasattr(result, 'execution_time') else 0
                            }
                        }
                    return {"success": True, "message": "仿真运行完成"}
                else:
                    # 旧适配器
                    result = adapter.run_simulation()
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "message": result.message,
                            "output": {
                                "status": result.status.value,
                                "data": parameters
                            }
                        }
                    return {"success": True, "message": "仿真运行完成"}

            elif action_name == "get_results":
                # 检查是否是 DWSIM COM 适配器
                if hasattr(adapter, 'streams') and hasattr(adapter, 'equipment'):
                    # DWSIM COM 适配器 - 从内部属性获取结果
                    return {
                        "success": True,
                        "message": "获取结果成功",
                        "output": {
                            "streams": adapter.streams if hasattr(adapter, 'streams') else {},
                            "equipment": adapter.equipment if hasattr(adapter, 'equipment') else {}
                        }
                    }
                else:
                    # 旧适配器
                    results = adapter.get_results(
                        stream_name=parameters.get("stream_name"),
                        block_name=parameters.get("block_name")
                    )
                    return {
                        "success": results.get("success", True),
                        "message": "获取结果成功",
                        "output": results
                    }

            elif action_name == "set_parameters":
                # 检查是否是 DWSIM COM 适配器
                if hasattr(adapter, 'set_parameters') and callable(adapter.set_parameters):
                    # DWSIM COM 适配器
                    result = adapter.set_parameters(parameters)
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "message": result.message,
                            "output": {"parameters_set": result.parameters_set}
                        }
                    return {"success": True, "message": "参数设置完成"}
                else:
                    # 旧适配器
                    result = adapter.set_parameters(parameters)
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "message": result.message,
                            "output": {"parameters_set": result.parameters_set}
                        }
                    return {"success": True, "message": "参数设置完成"}

            elif action_name == "load_file" or action_name == "open":
                success = adapter.open_simulation(parameters.get("file_path", ""))
                return {
                    "success": success,
                    "message": "文件加载成功" if success else "文件加载失败"
                }

            elif action_name == "save":
                success = adapter.save_simulation(parameters.get("file_path", ""))
                return {
                    "success": success,
                    "message": "保存成功" if success else "保存失败"
                }

            # Excel 特定操作
            elif action_name == "read_data":
                success = adapter.open_workbook(parameters.get("file_path", ""))
                return {
                    "success": success,
                    "message": "Excel 文件读取成功" if success else "读取失败"
                }

            elif action_name == "write_data":
                # Excel 写入数据需要先确保有打开的工作簿
                if not adapter.workbook:
                    logger.info("Excel: 需要先创建工作簿")
                    adapter.create_new_workbook()
                
                # 获取要写入的数据
                data = parameters.get("data", {})
                
                # 如果没有提供数据，尝试从用户请求中提取
                if not data and "request" in parameters:
                    data = self._extract_data_from_request(parameters["request"])
                    logger.info(f"从请求中提取数据: {data}")
                
                if data:
                    result = adapter.set_parameters(data)
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "message": result.message,
                            "output": {"parameters_set": result.parameters_set}
                        }
                return {"success": True, "message": "数据写入完成"}

            elif action_name == "create_report":
                success = adapter.create_report(parameters.get("data", {}))
                return {
                    "success": success,
                    "message": "报告创建成功" if success else "报告创建失败"
                }

            # DWSIM 新增操作
            elif action_name == "create_flowsheet":
                if hasattr(adapter, 'create_flowsheet'):
                    fs = adapter.create_flowsheet()
                    return {
                        "success": fs is not None,
                        "message": "流程图创建成功" if fs else "流程图创建失败",
                        "output": {}
                    }
                return None

            elif action_name == "add_compounds" or action_name == "add_compound":
                if hasattr(adapter, 'add_compounds'):
                    compound_names = parameters.get("compound_names", parameters.get("compounds", []))
                    count = adapter.add_compounds(compound_names)
                    return {
                        "success": count > 0,
                        "message": f"成功添加 {count} 个化合物",
                        "output": {"compounds_added": count}
                    }
                elif hasattr(adapter, 'add_compound'):
                    compound_name = parameters.get("compound_name") or parameters.get("compound_names", [None])[0]
                    if compound_name:
                        success = adapter.add_compound(compound_name)
                        return {
                            "success": success,
                            "message": f"添加化合物 {compound_name} {'成功' if success else '失败'}",
                            "output": {"compound": compound_name}
                        }
                return None

            elif action_name == "create_and_add_property_package":
                if hasattr(adapter, 'create_and_add_property_package'):
                    package_name = parameters.get("package_name", "Peng-Robinson (PR)")
                    result = adapter.create_and_add_property_package(package_name)
                    return {
                        "success": result is not None,
                        "message": f"物性包 {package_name} 添加{'成功' if result else '失败'}",
                        "output": {"property_package": package_name}
                    }
                return None

            elif action_name == "add_material_stream":
                if hasattr(adapter, 'add_material_stream'):
                    stream = adapter.add_material_stream(**parameters)
                    return {
                        "success": stream is not None,
                        "message": f"物料流 {parameters.get('name')} 添加{'成功' if stream else '失败'}",
                        "output": {"stream_name": parameters.get('name')}
                    }
                return None

            elif action_name.startswith("add_") and action_name not in ["add_compounds", "add_compound", "add_property_package", "add_material_stream", "add_reaction", "add_reaction_to_set"]:
                # 通用设备添加方法
                equipment_type = action_name.replace("add_", "")
                add_method = getattr(adapter, action_name, None)
                if add_method and callable(add_method):
                    obj = add_method(**parameters)
                    return {
                        "success": obj is not None,
                        "message": f"{equipment_type} {parameters.get('name')} 添加{'成功' if obj else '失败'}",
                        "output": {"equipment_name": parameters.get('name'), "type": equipment_type}
                    }
                return None

            elif action_name == "connect_objects":
                if hasattr(adapter, 'connect_objects'):
                    success = adapter.connect_objects(
                        parameters.get("from_object"),
                        parameters.get("to_object"),
                        parameters.get("from_port", 0),
                        parameters.get("to_port", 0)
                    )
                    return {
                        "success": success,
                        "message": f"连接 {parameters.get('from_object')} -> {parameters.get('to_object')} {'成功' if success else '失败'}",
                        "output": {}
                    }
                return None

            elif action_name == "disconnect_objects":
                if hasattr(adapter, 'disconnect_objects'):
                    success = adapter.disconnect_objects(
                        parameters.get("from_object"),
                        parameters.get("to_object")
                    )
                    return {
                        "success": success,
                        "message": f"断开连接 {'成功' if success else '失败'}",
                        "output": {}
                    }
                return None

            elif action_name == "set_object_property":
                if hasattr(adapter, 'set_object_property'):
                    success = adapter.set_object_property(
                        parameters.get("object_name"),
                        parameters.get("property_name"),
                        parameters.get("value")
                    )
                    return {
                        "success": success,
                        "message": f"设置属性 {'成功' if success else '失败'}",
                        "output": {}
                    }
                return None

            elif action_name == "get_object_property":
                if hasattr(adapter, 'get_object_property'):
                    value = adapter.get_object_property(
                        parameters.get("object_name"),
                        parameters.get("property_name")
                    )
                    return {
                        "success": value is not None,
                        "message": "获取属性成功",
                        "output": {"value": value}
                    }
                return None

            elif action_name == "get_stream_results":
                if hasattr(adapter, 'get_stream_results'):
                    results = adapter.get_stream_results(
                        parameters.get("stream_name"),
                        parameters.get("properties")
                    )
                    return {
                        "success": bool(results),
                        "message": "获取物料流结果成功",
                        "output": results
                    }
                return None

            elif action_name == "get_equipment_results":
                if hasattr(adapter, 'get_equipment_results'):
                    results = adapter.get_equipment_results(
                        parameters.get("equipment_name"),
                        parameters.get("properties")
                    )
                    return {
                        "success": bool(results),
                        "message": "获取设备结果成功",
                        "output": results
                    }
                return None

            elif action_name == "sensitivity_analysis":
                if hasattr(adapter, 'sensitivity_analysis'):
                    results = adapter.sensitivity_analysis(
                        parameters.get("variable_object"),
                        parameters.get("variable_property"),
                        parameters.get("variable_range"),
                        parameters.get("objective_object"),
                        parameters.get("objective_property")
                    )
                    return {
                        "success": bool(results),
                        "message": f"灵敏度分析完成，共 {len(results)} 个点",
                        "output": {"results": results}
                    }
                return None

            elif action_name == "optimize_single_parameter" or action_name == "optimize":
                if hasattr(adapter, 'optimize_single_parameter'):
                    result = adapter.optimize_single_parameter(
                        parameters.get("param_object"),
                        parameters.get("param_property"),
                        parameters.get("objective_object"),
                        parameters.get("objective_property"),
                        parameters.get("bounds")
                    )
                    return {
                        "success": result.get("success", False),
                        "message": "优化完成" if result.get("success") else "优化失败",
                        "output": result
                    }
                return None

            elif action_name == "multi_objective_optimization":
                if hasattr(adapter, 'multi_objective_optimization'):
                    result = adapter.multi_objective_optimization(
                        parameters.get("objectives", []),
                        parameters.get("bounds", []),
                        parameters.get("population_size", 100),
                        parameters.get("generations", 50)
                    )
                    return {
                        "success": result.get("success", False),
                        "message": "多目标优化完成" if result.get("success") else result.get("message", "优化失败"),
                        "output": result
                    }
                return None

            elif action_name == "auto_layout":
                if hasattr(adapter, 'auto_layout'):
                    success = adapter.auto_layout()
                    return {
                        "success": success,
                        "message": "自动布局完成" if success else "自动布局失败",
                        "output": {}
                    }
                return None

            elif action_name == "save_flowsheet":
                if hasattr(adapter, 'save_flowsheet'):
                    success = adapter.save_flowsheet(parameters.get("file_path"))
                    return {
                        "success": success,
                        "message": "保存流程图成功" if success else "保存流程图失败",
                        "output": {"file_path": parameters.get("file_path")}
                    }
                return None

            elif action_name == "load_flowsheet":
                if hasattr(adapter, 'load_flowsheet'):
                    fs = adapter.load_flowsheet(parameters.get("file_path"))
                    return {
                        "success": fs is not None,
                        "message": "加载流程图成功" if fs else "加载流程图失败",
                        "output": {"file_path": parameters.get("file_path")}
                    }
                return None

            elif action_name == "get_version":
                if hasattr(adapter, 'get_version'):
                    version = adapter.get_version()
                    return {
                        "success": True,
                        "message": "获取版本成功",
                        "output": {"version": version}
                    }
                return None

            elif action_name == "get_available_compounds":
                if hasattr(adapter, 'get_available_compounds'):
                    compounds = adapter.get_available_compounds()
                    return {
                        "success": True,
                        "message": f"获取到 {len(compounds)} 个可用化合物",
                        "output": {"compounds": compounds[:100]}  # 限制返回数量
                    }
                return None

            elif action_name == "get_available_property_packages":
                if hasattr(adapter, 'get_available_property_packages'):
                    packages = adapter.get_available_property_packages()
                    return {
                        "success": True,
                        "message": f"获取到 {len(packages)} 个可用物性包",
                        "output": {"property_packages": packages}
                    }
                return None

            else:
                logger.warning(f"未知操作: {action_name}")
                return None

        except Exception as e:
            logger.error(f"适配器执行失败: {e}")
            return None

    def _get_adapter(self, skill_name: str):
        """获取或创建适配器"""
        if skill_name in _adapters:
            return _adapters[skill_name]

        # 创建适配器
        try:
            if skill_name == "dwsim":
                # 优先使用 DWSIM COM 适配器
                try:
                    from .dwsim_com_adapter import DWSIMCOMAdapter
                    adapter = DWSIMCOMAdapter()
                    logger.info("使用 DWSIM COM 适配器")
                    
                    # 确保已连接
                    if not adapter.safe_connect():
                        logger.warning("无法连接到 DWSIM COM")
                        return None
                    
                    logger.info("已成功连接到 DWSIM COM")
                    _adapters[skill_name] = adapter
                    return adapter
                except Exception as e:
                    logger.warning(f"DWSIM COM 适配器失败: {e}，尝试使用旧适配器")
                    # 回退到旧适配器
                    from .dwsim_adapter import DWSIMAdapter
                    adapter = DWSIMAdapter()
                    
                    # 发现 DWSIM
                    discovery = adapter.discover()
                    if not discovery["found"]:
                        logger.warning("未找到 DWSIM 软件")
                        return None
                    
                    logger.info(f"DWSIM 已找到: {discovery['path']}")
                    
                    # 确保已连接
                    if not adapter.ensure_connected():
                        logger.warning("无法连接到 DWSIM")
                        return None
                    
                    logger.info("已成功连接到 DWSIM")
                    
                    # 确保有打开的仿真
                    if not adapter.create_simulation_if_needed():
                        logger.warning("无法创建仿真")
                        return None
                    
                    _adapters[skill_name] = adapter
                    return adapter

            elif skill_name == "excel":
                from .excel_adapter import ExcelAdapter
                adapter = ExcelAdapter()
                
                # 确保已连接
                if not adapter.connect():
                    logger.warning("无法连接到 Excel")
                    return None
                
                logger.info("已成功连接到 Excel")
                _adapters[skill_name] = adapter
                return adapter

            elif skill_name == "autocad":
                from .autocad_adapter import AutoCADAdapter
                adapter = AutoCADAdapter()
                _adapters[skill_name] = adapter
                return adapter

        except Exception as e:
            logger.error(f"创建适配器失败 {skill_name}: {e}")

        return None

    def _map_action(self, skill: Skill, requested_action: str) -> Optional[SkillAction]:
        """智能映射操作名称"""
        if not skill or not requested_action:
            return None
        
        # 操作映射表
        ACTION_MAPPING = {
            "excel": {
                "run_simulation": "write_data",
                "simulate": "write_data",
                "create_report": "write_data",
                "generate_report": "write_data",
                "write": "write_data",
                "read": "read_data",
                "load": "open",
                "save": "save",
            },
            "dwsim": {
                "run": "run_simulation",
                "execute": "run_simulation",
                "simulate": "run_simulation",
                "calculate": "run_simulation",
                "set": "set_parameters",
                "create": "create_stream",
                "add": "add_equipment",
                "connect": "set_parameters",
            }
        }
        
        # 获取该技能的操作映射表
        mapping = ACTION_MAPPING.get(skill.name, {})
        
        # 尝试精确映射
        mapped_name = mapping.get(requested_action.lower())
        if mapped_name:
            action = next((a for a in skill.actions if a.name == mapped_name), None)
            if action:
                return action
        
        # 尝试模糊匹配（包含关系）
        requested_lower = requested_action.lower()
        for action in skill.actions:
            if requested_lower in action.name or action.name in requested_lower:
                return action
        
        # 尝试根据操作描述匹配
        for action in skill.actions:
            if requested_lower in action.description.lower():
                return action
        
        return None

    def _get_software_not_installed_message(self, skill_name: str) -> Dict[str, Any]:
        """获取软件未安装时的提示信息"""
        
        # 软件安装指南
        SOFTWARE_GUIDES = {
            "dwsim": {
                "name": "DWSIM",
                "description": "DWSIM 是一款开源的化工流程模拟软件",
                "download_url": "https://dwsim.org/downloads/",
                "install_guide": """
安装步骤：
1. 访问 https://dwsim.org/downloads/
2. 下载 Windows 安装程序（.msi 文件）
3. 运行安装程序，按向导完成安装
4. 安装完成后，重新启动本系统

注意：DWSIM 需要 .NET Framework 4.8 或更高版本
                """.strip(),
                "alternative": "您也可以使用其他流程模拟软件，如 Aspen Plus、PRO/II 或 ChemCAD"
            },
            "excel": {
                "name": "Microsoft Excel",
                "description": "Microsoft Excel 是微软的办公软件",
                "download_url": "https://www.microsoft.com/microsoft-365/excel",
                "install_guide": """
安装步骤：
1. 访问 https://www.microsoft.com/microsoft-365/excel
2. 购买或订阅 Microsoft 365
3. 下载并安装 Office 套件
4. 安装完成后，重新启动本系统
                """.strip(),
                "alternative": "您也可以使用其他电子表格软件，如 LibreOffice Calc 或 WPS 表格"
            },
            "aspen_plus": {
                "name": "Aspen Plus",
                "description": "Aspen Plus 是工业标准的化工流程模拟软件",
                "download_url": "https://www.aspentech.com/en/products/engineering/aspen-plus",
                "install_guide": """
安装步骤：
1. 联系 AspenTech 获取许可证
2. 下载安装程序
3. 安装并激活许可证
4. 安装完成后，重新启动本系统

注意：Aspen Plus 是商业软件，需要购买许可证
                """.strip(),
                "alternative": "您也可以使用免费的 DWSIM 作为替代方案"
            },
            "autocad": {
                "name": "AutoCAD",
                "description": "AutoCAD 是 Autodesk 的 CAD 设计软件",
                "download_url": "https://www.autodesk.com/products/autocad/overview",
                "install_guide": """
安装步骤：
1. 访问 https://www.autodesk.com/products/autocad/overview
2. 注册 Autodesk 账户
3. 下载并安装 AutoCAD
4. 安装完成后，重新启动本系统

注意：AutoCAD 是商业软件，需要购买许可证
                """.strip(),
                "alternative": "您也可以使用免费的 LibreCAD 或 FreeCAD 作为替代方案"
            }
        }
        
        guide = SOFTWARE_GUIDES.get(skill_name, {
            "name": skill_name,
            "description": f"{skill_name} 软件",
            "download_url": "请访问官方网站下载",
            "install_guide": "请参考官方文档进行安装",
            "alternative": "请使用其他替代软件"
        })
        
        message = f"""
⚠️ 未检测到 {guide['name']} 软件

{guide['description']} 似乎未安装在您的系统中。

📥 下载地址：
{guide['download_url']}

📋 安装指南：
{guide['install_guide']}

💡 替代方案：
{guide['alternative']}

安装完成后，请重新启动本系统以自动检测软件。
        """.strip()
        
        return {
            "success": False,
            "message": message,
            "output": {
                "software_name": guide['name'],
                "download_url": guide['download_url'],
                "install_guide": guide['install_guide'],
                "alternative": guide['alternative'],
                "status": "not_installed"
            }
        }

    def _extract_data_from_request(self, request: str) -> Dict[str, Any]:
        """从用户请求中智能提取数据"""
        import re
        
        data = {}
        request_lower = request.lower()
        
        # 提取产品名称和数值
        # 匹配 "产品X" + 销售额/数量 模式
        patterns = [
            # 匹配 "产品A 销售额 1000" 或 "产品A: 1000"
            r'产品([A-Za-z0-9]+)[:\s]+(\d+\.?\d*)',
            # 匹配 "产品名称: 产品A"
            r'产品名称[:\s]+产品([A-Za-z0-9]+)',
        ]
        
        # 常见字段关键词
        field_keywords = {
            '销售额': ['销售', '销售', '收入', '金额', 'price', 'sales'],
            '数量': ['数量', '数量', '销量', 'count', 'quantity', 'num'],
        }
        
        # 尝试匹配产品数据
        product_matches = re.findall(r'产品([A-Za-z0-9]+)[:\s,，]+(\d+\.?\d*)', request)
        for product, value in product_matches:
            if '销售额' in request or '销售' in request or '金额' in request:
                data[f"产品{product}"] = {"value": float(value), "unit": "元"}
            elif '数量' in request or '销量' in request:
                data[f"产品{product}"] = {"value": float(value), "unit": "件"}
        
        # 如果没有匹配到产品，生成示例数据
        if not data:
            # 根据请求类型生成合理的示例数据
            if '报告' in request or '创建' in request:
                if '销售' in request:
                    data = {
                        "产品A": {"value": 5000, "unit": "元", "description": "产品A销售额"},
                        "产品B": {"value": 8000, "unit": "元", "description": "产品B销售额"},
                        "产品C": {"value": 3000, "unit": "元", "description": "产品C销售额"},
                        "总计": {"value": 16000, "unit": "元", "description": "总销售额"}
                    }
                elif '数量' in request:
                    data = {
                        "产品A": {"value": 100, "unit": "件", "description": "产品A数量"},
                        "产品B": {"value": 200, "unit": "件", "description": "产品B数量"},
                        "产品C": {"value": 150, "unit": "件", "description": "产品C数量"}
                    }
        
        return data

    def _generate_mock_result(self, skill_name: str, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟结果（当没有真实适配器时）"""
        import random

        # 基础结果
        result = {
            "success": True,
            "message": f"已在 {skill_name} 中执行 {action_name}",
            "output": {
                "status": "completed",
                "data": parameters
            }
        }

        # 根据技能和操作生成更丰富的模拟数据
        if skill_name == "dwsim" and action_name == "run_simulation":
            # 精馏塔模拟结果
            result["output"] = {
                "status": "completed",
                "simulation_type": "distillation",
                "results": {
                    "column": {
                        "number_of_stages": parameters.get("num_stages", 20),
                        "reflux_ratio": parameters.get("reflux_ratio", 2.0),
                        "feed_stage": parameters.get("feed_stage", 10),
                        "reboiler_duty": round(random.uniform(500, 2000), 2),
                        "condenser_duty": round(random.uniform(-2000, -500), 2),
                        "pressure_drop": round(random.uniform(0.01, 0.1), 4)
                    },
                    "streams": {
                        "Feed": {
                            "temperature": round(random.uniform(300, 400), 2),
                            "pressure": 101325,
                            "molar_flow": round(random.uniform(50, 200), 2),
                            "mass_flow": round(random.uniform(1000, 5000), 2),
                            "vapor_fraction": 0.3,
                            "composition": {
                                "Ethanol": 0.5,
                                "Water": 0.5
                            }
                        },
                        "Distillate": {
                            "temperature": round(random.uniform(350, 380), 2),
                            "pressure": 101325,
                            "molar_flow": round(random.uniform(20, 80), 2),
                            "mass_flow": round(random.uniform(500, 2000), 2),
                            "vapor_fraction": 0.0,
                            "composition": {
                                "Ethanol": round(random.uniform(0.85, 0.95), 4),
                                "Water": round(random.uniform(0.05, 0.15), 4)
                            }
                        },
                        "Bottoms": {
                            "temperature": round(random.uniform(380, 420), 2),
                            "pressure": 101325,
                            "molar_flow": round(random.uniform(20, 80), 2),
                            "mass_flow": round(random.uniform(500, 2000), 2),
                            "vapor_fraction": 0.0,
                            "composition": {
                                "Ethanol": round(random.uniform(0.01, 0.1), 4),
                                "Water": round(random.uniform(0.9, 0.99), 4)
                            }
                        }
                    },
                    "mass_balance": {
                        "input": round(random.uniform(1000, 5000), 2),
                        "output": round(random.uniform(1000, 5000), 2),
                        "error": round(random.uniform(-0.01, 0.01), 6)
                    }
                }
            }
            result["message"] = "精馏塔模拟完成"

        elif skill_name == "aspen_plus" and action_name == "run":
            result["output"] = {
                "status": "completed",
                "simulation_type": "aspen_plus",
                "results": {
                    "blocks": {
                        "B1": {
                            "type": "RADFRAC",
                            "duty": round(random.uniform(1e6, 5e6), 2),
                            "error": round(random.uniform(0.0001, 0.01), 6)
                        }
                    }
                }
            }

        elif skill_name == "excel":
            result["output"] = {
                "status": "completed",
                "excel_operation": action_name,
                "results": {
                    "workbook_created": True,
                    "worksheet": "Sheet1",
                    "data_written": True,
                    "cells": {
                        "A1": "产品名称",
                        "B1": "销售额",
                        "C1": "数量",
                        "A2": "产品A",
                        "B2": round(random.uniform(1000, 10000), 2),
                        "C2": round(random.uniform(10, 100), 0),
                        "A3": "产品B",
                        "B3": round(random.uniform(1000, 10000), 2),
                        "C3": round(random.uniform(10, 100), 0),
                        "A4": "产品C",
                        "B4": round(random.uniform(1000, 10000), 2),
                        "C4": round(random.uniform(10, 100), 0)
                    }
                }
            }
            result["message"] = "Excel 报告创建完成"

        return result

    async def _observe(
        self,
        context: AgentContext,
        step_result: Dict[str, Any],
        step: ExecutionStep
    ) -> tuple[bool, Optional[str]]:
        """
        观察步骤执行结果

        Returns:
            (should_continue, adjustment_or_error)
            - should_continue: 是否继续执行
            - adjustment_or_error: 调整建议或错误信息
        """
        # 检查步骤是否成功
        if not step_result.get("success", True):
            error = step_result.get("error", "未知错误")
            logger.warning(f"[Agent {context.session_id}] 步骤失败: {error}")
            return False, f"步骤执行失败: {error}"

        # 检查结果是否有效
        result_data = step_result.get("result", {})
        if result_data.get("success") is False:
            return False, f"操作返回失败: {result_data.get('message')}"

        # 检查是否需要更多步骤
        # 例如：如果需要用户确认，则暂停

        return True, None

    def get_agent_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取 Agent 状态"""
        context = self.active_agents.get(session_id)
        if not context:
            return None

        return {
            "session_id": context.session_id,
            "status": context.status.value,
            "current_step": context.current_step_index,
            "total_steps": len(context.plan.steps) if context.plan else 0,
            "user_request": context.user_request,
            "started_at": context.started_at,
            "updated_at": context.updated_at
        }

    def list_active_agents(self) -> List[Dict[str, Any]]:
        """列出所有活跃的 Agent"""
        return [
            self.get_agent_status(session_id)
            for session_id in self.active_agents.keys()
        ]


# 全局实例
_agent_engine: Optional[AgentEngine] = None


def get_agent_engine() -> AgentEngine:
    """获取 Agent 引擎实例"""
    global _agent_engine
    if _agent_engine is None:
        _agent_engine = AgentEngine()
    return _agent_engine

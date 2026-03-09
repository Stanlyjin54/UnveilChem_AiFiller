#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化API路由
提供软件自动化相关的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import json

from ..services.automation import AutomationEngine
from ..services.automation.error_handler import AutomationErrorHandler, ErrorSeverity, ErrorCategory
from ..services.automation.software_discovery import SoftwareDiscovery, scan_local_software
from ..services.automation.skill import SkillRegistry, get_skill_registry, Skill, SkillMatchResult
from ..services.automation.task_understanding import TaskUnderstandingService, get_task_understanding_service, ExecutionPlan
from ..services.automation.memory import AgentMemory, get_agent_memory, MemoryType
from ..services.automation.agent_engine import AgentEngine, get_agent_engine, AgentStatus
from ..database import get_db
from ..models.user import User
# 临时简化认证，直接返回模拟用户
from ..models.user import User
from typing import Optional

def get_current_user() -> Optional[User]:
    """临时简化认证函数 - 返回模拟管理员用户"""
    user = User()
    user.id = 1
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = "admin"
    user.is_active = True
    return user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["automation"])

# 全局自动化引擎实例
automation_engine = None
error_handler = None

def get_automation_engine() -> AutomationEngine:
    """获取自动化引擎实例"""
    global automation_engine
    if automation_engine is None:
        automation_engine = AutomationEngine(max_workers=4)
        automation_engine.start()
        logger.info("自动化引擎已启动")
    return automation_engine

def get_error_handler() -> AutomationErrorHandler:
    """获取错误处理器实例"""
    global error_handler
    if error_handler is None:
        error_handler = AutomationErrorHandler()
        logger.info("错误处理器已初始化")
    return error_handler

# Pydantic模型
class AutomationTaskRequest(BaseModel):
    """自动化任务请求"""
    name: str = Field(..., description="任务名称")
    parameters: Dict[str, Any] = Field(..., description="参数")
    target_software: str = Field(..., description="目标软件")
    adapter_type: str = Field(..., description="适配器类型")
    priority: int = Field(1, ge=1, le=10, description="优先级 (1-10)")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")

class BatchTaskRequest(BaseModel):
    """批量任务请求"""
    tasks: List[AutomationTaskRequest] = Field(..., description="任务列表")
    wait_for_completion: bool = Field(False, description="是否等待完成")

class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    name: str
    status: str
    target_software: str
    created_time: str
    retry_count: int = 0
    error_message: Optional[str] = None

class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    success: bool
    status: str
    message: str
    parameters_set: Dict[str, Any]
    execution_time: float
    error_details: Optional[str] = None

class AutomationStatistics(BaseModel):
    """自动化统计信息"""
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    queue_size: int
    supported_adapters: List[str]
    supported_software: List[str]

class ErrorReport(BaseModel):
    """错误报告"""
    error_id: str
    timestamp: str
    severity: str
    category: str
    message: str
    resolved: bool
    recovery_attempts: int

# API端点
@router.post("/submit-task", response_model=Dict[str, str])
async def submit_task(
    task_request: AutomationTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """提交自动化任务"""
    try:
        task_id = engine.submit_task(
            name=task_request.name,
            parameters=task_request.parameters,
            target_software=task_request.target_software,
            adapter_type=task_request.adapter_type,
            priority=task_request.priority,
            scheduled_time=task_request.scheduled_time
        )
        
        logger.info(f"用户 {current_user.username} 提交任务: {task_id}")
        return {"task_id": task_id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"提交任务失败: {e}")
        error_handler = get_error_handler()
        error_handler.handle_error(e, context={"user": current_user.username, "operation": "submit_task"})
        raise HTTPException(status_code=500, detail=f"提交任务失败: {str(e)}")

@router.post("/batch-submit", response_model=Dict[str, Any])
async def batch_submit_tasks(
    batch_request: BatchTaskRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """批量提交任务"""
    try:
        # 转换任务格式
        tasks_data = []
        for task in batch_request.tasks:
            tasks_data.append({
                'name': task.name,
                'parameters': task.parameters,
                'target_software': task.target_software,
                'adapter_type': task.adapter_type,
                'priority': task.priority,
                'scheduled_time': task.scheduled_time
            })
        
        # 批量提交
        task_ids = engine.batch_execute(tasks_data)
        
        logger.info(f"用户 {current_user.username} 批量提交 {len(task_ids)} 个任务")
        
        return {
            "task_ids": task_ids,
            "total_tasks": len(task_ids),
            "status": "submitted"
        }
        
    except Exception as e:
        logger.error(f"批量提交任务失败: {e}")
        error_handler = get_error_handler()
        error_handler.handle_error(e, context={"user": current_user.username, "operation": "batch_submit"})
        raise HTTPException(status_code=500, detail=f"批量提交任务失败: {str(e)}")

@router.get("/task-status/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取任务状态"""
    try:
        all_tasks = engine.get_all_tasks()
        
        # 查找任务
        task_info = None
        for task in all_tasks:
            if task['task_id'] == task_id:
                task_info = task
                break
        
        if not task_info:
            raise HTTPException(status_code=404, detail="任务未找到")
        
        return TaskResponse(**task_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/task-result/{task_id}", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取任务结果"""
    try:
        result = engine.get_task_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="任务结果未找到")
        
        return TaskResultResponse(
            task_id=task_id,
            success=result.success,
            status=result.status.value,
            message=result.message,
            parameters_set=result.parameters_set,
            execution_time=result.execution_time,
            error_details=result.error_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")

@router.get("/all-tasks", response_model=List[TaskResponse])
async def get_all_tasks(
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取所有任务"""
    try:
        all_tasks = engine.get_all_tasks()
        return [TaskResponse(**task) for task in all_tasks]
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/cancel-task/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """取消任务"""
    try:
        success = engine.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务未找到或无法取消")
        
        logger.info(f"用户 {current_user.username} 取消任务: {task_id}")
        return {"message": "任务已取消", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")

@router.post("/clear-completed")
async def clear_completed_tasks(
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """清除已完成的任务"""
    try:
        engine.clear_completed_tasks()
        logger.info(f"用户 {current_user.username} 清除已完成的任务")
        return {"message": "已完成的任务已清除"}
        
    except Exception as e:
        logger.error(f"清除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除任务失败: {str(e)}")

@router.get("/statistics", response_model=AutomationStatistics)
async def get_statistics(
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取自动化统计信息"""
    try:
        stats = engine.get_statistics()
        return AutomationStatistics(**stats)
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/supported-software")
async def get_supported_software(
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取支持的软件列表"""
    try:
        stats = engine.get_statistics()
        return {
            "supported_adapters": stats['supported_adapters'],
            "supported_software": stats['supported_software'],
            "total_software": len(stats['supported_software'])
        }
        
    except Exception as e:
        logger.error(f"获取支持软件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取支持软件列表失败: {str(e)}")

# 错误处理相关端点
@router.get("/errors", response_model=List[ErrorReport])
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=200, description="返回错误数量限制"),
    current_user: User = Depends(get_current_user),
    error_handler: AutomationErrorHandler = Depends(get_error_handler)
):
    """获取最近的错误"""
    try:
        errors = error_handler.get_recent_errors(limit)
        return [ErrorReport(**error) for error in errors]
        
    except Exception as e:
        logger.error(f"获取错误列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误列表失败: {str(e)}")

@router.get("/error-statistics")
async def get_error_statistics(
    current_user: User = Depends(get_current_user),
    error_handler: AutomationErrorHandler = Depends(get_error_handler)
):
    """获取错误统计信息"""
    try:
        stats = error_handler.get_error_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"获取错误统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误统计失败: {str(e)}")

@router.post("/export-errors")
async def export_error_log(
    current_user: User = Depends(get_current_user),
    error_handler: AutomationErrorHandler = Depends(get_error_handler)
):
    """导出错误日志"""
    try:
        import tempfile
        import os
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        # 导出错误日志
        error_handler.export_error_log(temp_path)
        
        # 读取文件内容
        with open(temp_path, 'r', encoding='utf-8') as f:
            error_data = json.load(f)
        
        # 清理临时文件
        os.unlink(temp_path)
        
        logger.info(f"用户 {current_user.username} 导出错误日志")
        return {
            "message": "错误日志已导出",
            "errors": error_data,
            "export_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"导出错误日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出错误日志失败: {str(e)}")

# 系统管理端点
@router.post("/start-engine")
async def start_automation_engine(
    current_user: User = Depends(get_current_user)
):
    """启动自动化引擎"""
    try:
        engine = get_automation_engine()
        engine.start_scheduler()
        logger.info(f"用户 {current_user.username} 启动自动化引擎")
        return {"message": "自动化引擎已启动"}
        
    except Exception as e:
        logger.error(f"启动自动化引擎失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动自动化引擎失败: {str(e)}")

@router.get("/test-connection/{adapter_type}")
async def test_adapter_connection(adapter_type: str):
    """测试适配器连接状态"""
    try:
        engine = get_automation_engine()
        
        # 检查适配器是否已注册
        if adapter_type in engine.adapters:
            adapter = engine.adapters[adapter_type]
            # 尝试连接测试
            connection_success = adapter.connect()
            if connection_success:
                adapter.disconnect()
                return {
                    "adapter_type": adapter_type,
                    "status": "connected",
                    "message": f"{adapter_type} 适配器连接成功"
                }
            else:
                return {
                    "adapter_type": adapter_type,
                    "status": "disconnected",
                    "message": f"{adapter_type} 适配器连接失败，请检查软件是否已安装"
                }
        else:
            return {
                "adapter_type": adapter_type,
                "status": "not_registered",
                "message": f"{adapter_type} 适配器未注册，请先调用注册接口"
            }
            
    except Exception as e:
        logger.error(f"测试适配器连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")

@router.post("/register-adapter/{adapter_type}")
async def register_missing_adapter(
    adapter_type: str,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """注册缺失的适配器"""
    try:
        success = engine.register_missing_adapter(adapter_type)
        
        if success:
            logger.info(f"用户 {current_user.username} 注册了适配器: {adapter_type}")
            return {
                "message": f"{adapter_type} 适配器注册成功",
                "adapter_type": adapter_type,
                "status": "registered"
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的适配器类型: {adapter_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册适配器失败: {e}")
        raise HTTPException(status_code=500, detail=f"注册适配器失败: {str(e)}")

@router.get("/available-adapters")
async def get_available_adapters(
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """获取所有可用的适配器信息"""
    try:
        # 已注册的适配器
        registered_adapters = list(engine.adapters.keys())
        
        # 预设的适配器列表
        all_adapters = [
            {"name": "excel", "display_name": "Microsoft Excel", "description": "Excel自动化操作"},
            {"name": "dwsim", "display_name": "DWSIM", "description": "DWSIM流程模拟软件"},
            {"name": "aspen_plus", "display_name": "Aspen Plus", "description": "Aspen Plus流程模拟软件"},
            {"name": "autocad", "display_name": "AutoCAD", "description": "AutoCAD绘图软件"},
            {"name": "pro_ii", "display_name": "PRO/II", "description": "PRO/II流程模拟软件"}
        ]
        
        # 标记注册状态
        for adapter in all_adapters:
            adapter["registered"] = adapter["name"] in registered_adapters
            
        return {
            "available_adapters": all_adapters,
            "registered_count": len(registered_adapters),
            "total_count": len(all_adapters)
        }
        
    except Exception as e:
        logger.error(f"获取适配器列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取适配器列表失败: {str(e)}")

@router.post("/engine/stop")
async def stop_engine(
    current_user: User = Depends(get_current_user)
):
    """停止自动化引擎"""
    try:
        global automation_engine
        if automation_engine:
            automation_engine.stop()
            automation_engine = None
            logger.info(f"用户 {current_user.username} 停止自动化引擎")
            return {"message": "自动化引擎已停止"}
        else:
            return {"message": "自动化引擎未运行"}
        
    except Exception as e:
        logger.error(f"停止自动化引擎失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止自动化引擎失败: {str(e)}")

# 初始化错误处理器
error_handler = get_error_handler()


# 软件发现相关端点
@router.get("/discover-software")
async def discover_software(
    current_user: User = Depends(get_current_user),
    software_type: str = Query(None, description="过滤软件类型: simulation, cad, office")
):
    """扫描本地安装的软件"""
    try:
        discovery = SoftwareDiscovery()
        software_list = discovery.scan_all()

        # 如果指定了软件类型，进行过滤
        if software_type:
            software_list = [s for s in software_list if s.software_type == software_type]

        return {
            "success": True,
            "data": discovery.to_dict(),
            "total": len(software_list)
        }

    except Exception as e:
        logger.error(f"软件扫描失败: {e}")
        raise HTTPException(status_code=500, detail=f"软件扫描失败: {str(e)}")


@router.get("/software-status/{software_name}")
async def get_software_status(
    software_name: str,
    current_user: User = Depends(get_current_user)
):
    """检查特定软件的运行状态"""
    try:
        discovery = SoftwareDiscovery()
        discovery.scan_all()

        # 查找指定软件
        for software in discovery.detected_software:
            if software.name == software_name:
                return {
                    "success": True,
                    "data": {
                        "name": software.name,
                        "display_name": software.display_name,
                        "version": software.version,
                        "status": software.status.value,
                        "install_path": software.install_path,
                        "executable_path": software.executable_path
                    }
                }

        return {
            "success": False,
            "message": f"未检测到软件: {software_name}",
            "data": None
        }

    except Exception as e:
        logger.error(f"获取软件状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取软件状态失败: {str(e)}")


@router.post("/register-discovered-software/{software_name}")
async def register_discovered_software(
    software_name: str,
    current_user: User = Depends(get_current_user),
    engine: AutomationEngine = Depends(get_automation_engine)
):
    """注册已发现的软件适配器"""
    try:
        # 尝试注册适配器
        success = engine.register_missing_adapter(software_name)

        if success:
            logger.info(f"用户 {current_user.username} 注册了软件: {software_name}")
            return {
                "success": True,
                "message": f"{software_name} 适配器注册成功"
            }
        else:
            return {
                "success": False,
                "message": f"不支持的软件类型: {software_name}"
            }

    except Exception as e:
        logger.error(f"注册软件适配器失败: {e}")
        raise HTTPException(status_code=500, detail=f"注册软件适配器失败: {str(e)}")


# Skill 相关端点
@router.get("/skills")
async def get_skills(
    current_user: User = Depends(get_current_user),
    category: str = Query(None, description="过滤分类: simulation, cad, office, chemical, data, general"),
    enabled_only: bool = Query(False, description="只返回启用的 Skills")
):
    """获取所有可用 Skills"""
    try:
        registry = get_skill_registry()

        skills = registry.get_all_skills()
        if enabled_only:
            skills = registry.get_enabled_skills()
        if category:
            from ..services.automation.skill import SkillCategory
            try:
                cat = SkillCategory(category)
                skills = [s for s in skills if s.category == cat]
            except ValueError:
                pass

        return {
            "success": True,
            "data": [s.model_dump() for s in skills],
            "total": len(skills)
        }

    except Exception as e:
        logger.error(f"获取 Skills 列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 Skills 列表失败: {str(e)}")


@router.get("/skills/{skill_name}")
async def get_skill_detail(
    skill_name: str,
    current_user: User = Depends(get_current_user)
):
    """获取 Skill 详情"""
    try:
        registry = get_skill_registry()
        skill = registry.get_skill(skill_name)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_name}")

        return {
            "success": True,
            "data": skill.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Skill 详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取 Skill 详情失败: {str(e)}")


@router.get("/skills/search/{keyword}")
async def search_skills(
    keyword: str,
    current_user: User = Depends(get_current_user)
):
    """通过关键词搜索 Skills"""
    try:
        registry = get_skill_registry()
        results = registry.search_by_keyword(keyword)

        return {
            "success": True,
            "data": [
                {
                    "skill": r.skill.model_dump(),
                    "confidence": r.confidence,
                    "matched_keywords": r.matched_keywords
                }
                for r in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"搜索 Skills 失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索 Skills 失败: {str(e)}")


@router.post("/skills/{skill_name}/toggle")
async def toggle_skill(
    skill_name: str,
    enabled: bool = Query(True, description="启用或禁用 Skill"),
    current_user: User = Depends(get_current_user)
):
    """启用或禁用 Skill"""
    try:
        registry = get_skill_registry()
        skill = registry.get_skill(skill_name)

        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill 不存在: {skill_name}")

        skill.is_enabled = enabled

        logger.info(f"用户 {current_user.username} {'启用' if enabled else '禁用'}了 Skill: {skill_name}")

        return {
            "success": True,
            "message": f"Skill {'已启用' if enabled else '已禁用'}: {skill_name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换 Skill 状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换 Skill 状态失败: {str(e)}")


# 任务理解相关端点
class TaskUnderstandRequest(BaseModel):
    """任务理解请求"""
    request: str = Field(..., description="用户自然语言请求")
    max_steps: int = Field(10, ge=1, le=20, description="最大步骤数")


class TaskUnderstandResponse(BaseModel):
    """任务理解响应"""
    task_id: str
    original_request: str
    task_type: str
    required_skills: List[str]
    steps: List[Dict[str, Any]]
    estimated_time: float
    confidence: float
    created_at: str


@router.post("/understand-task", response_model=Dict[str, Any])
async def understand_task(
    request: TaskUnderstandRequest,
    current_user: User = Depends(get_current_user)
):
    """理解用户任务请求，生成执行计划"""
    try:
        service = get_task_understanding_service()
        plan = await service.understand(request.request, request.max_steps)

        # 验证计划
        validation = await service.validate_plan(plan)

        return {
            "success": True,
            "data": {
                "task_id": plan.task_id,
                "original_request": plan.original_request,
                "task_type": plan.task_type,
                "required_skills": plan.required_skills,
                "steps": [step.model_dump() for step in plan.steps],
                "estimated_time": plan.estimated_time,
                "confidence": plan.confidence,
                "created_at": plan.created_at,
            },
            "validation": validation,
            "message": "任务理解成功"
        }

    except Exception as e:
        logger.error(f"任务理解失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务理解失败: {str(e)}")


@router.post("/validate-plan")
async def validate_plan(
    plan: ExecutionPlan,
    current_user: User = Depends(get_current_user)
):
    """验证执行计划的可行性"""
    try:
        service = get_task_understanding_service()
        result = await service.validate_plan(plan)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        logger.error(f"计划验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"计划验证失败: {str(e)}")


@router.get("/task-types")
async def get_task_types(
    current_user: User = Depends(get_current_user)
):
    """获取支持的任务类型列表"""
    try:
        task_types = [
            {"id": "simulation", "name": "流程模拟", "description": "化工流程模拟任务"},
            {"id": "data_processing", "name": "数据处理", "description": "Excel数据处理任务"},
            {"id": "document_analysis", "name": "文档分析", "description": "文档解析与分析任务"},
            {"id": "cad_design", "name": "CAD设计", "description": "CAD绘图任务"},
            {"id": "parameter_optimization", "name": "参数优化", "description": "工艺参数优化任务"},
            {"id": "unknown", "name": "未知", "description": "无法识别的任务类型"},
        ]

        return {
            "success": True,
            "data": task_types
        }

    except Exception as e:
        logger.error(f"获取任务类型失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务类型失败: {str(e)}")


# ========== Agent 记忆系统相关端点 ==========

@router.post("/memory/session")
async def create_session(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    try:
        memory = get_agent_memory()
        session = memory.create_session(user_id or current_user.id)

        return {
            "success": True,
            "data": {
                "session_id": session.session_id,
                "created_at": session.created_at
            },
            "message": "会话创建成功"
        }

    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/memory/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取会话详情"""
    try:
        memory = get_agent_memory()
        session = memory.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        return {
            "success": True,
            "data": {
                "session_id": session.session_id,
                "messages": [
                    {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                    for m in session.messages
                ],
                "current_plan": session.current_plan,
                "context": session.context,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.post("/memory/session/{session_id}/message")
async def add_session_message(
    session_id: str,
    role: str = Query(..., description="消息角色: user, assistant"),
    content: str = Query(..., description="消息内容"),
    current_user: User = Depends(get_current_user)
):
    """添加会话消息"""
    try:
        memory = get_agent_memory()
        session = memory.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        memory.add_session_message(session_id, role, content)

        return {
            "success": True,
            "message": "消息添加成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加消息失败: {str(e)}")


@router.post("/memory/knowledge")
async def add_knowledge(
    source_type: str = Query(..., description="知识来源类型"),
    source_name: str = Query(..., description="知识来源名称"),
    content: str = Query(..., description="知识内容"),
    keywords: str = Query("", description="关键词，逗号分隔"),
    current_user: User = Depends(get_current_user)
):
    """添加知识到知识库"""
    try:
        from ..services.automation.memory import KnowledgeChunk
        import uuid

        knowledge = KnowledgeChunk(
            chunk_id=str(uuid.uuid4())[:8],
            source_type=source_type,
            source_name=source_name,
            chunk_content=content,
            keywords=keywords.split(",") if keywords else []
        )

        memory = get_agent_memory()
        memory.add_knowledge(knowledge)

        return {
            "success": True,
            "data": {"chunk_id": knowledge.chunk_id},
            "message": "知识添加成功"
        }

    except Exception as e:
        logger.error(f"添加知识失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加知识失败: {str(e)}")


@router.get("/memory/knowledge/search")
async def search_knowledge(
    query: str = Query(..., description="搜索关键词"),
    top_k: int = Query(3, ge=1, le=10, description="返回结果数量"),
    current_user: User = Depends(get_current_user)
):
    """搜索知识库"""
    try:
        memory = get_agent_memory()
        results = memory.search_knowledge(query, top_k)

        return {
            "success": True,
            "data": [
                {
                    "content": r.content,
                    "source_type": r.source_type,
                    "source_name": r.source_name,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"搜索知识失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索知识失败: {str(e)}")


@router.get("/memory/search")
async def search_all_memory(
    query: str = Query(..., description="搜索关键词"),
    current_user: User = Depends(get_current_user)
):
    """统一搜索所有记忆"""
    try:
        memory = get_agent_memory()
        results = memory.search_all(query)

        return {
            "success": True,
            "data": {
                "knowledge": [
                    {
                        "content": r.content,
                        "source_type": r.source_type,
                        "source_name": r.source_name,
                        "score": r.score
                    }
                    for r in results.get("knowledge", [])
                ],
                "execution": [
                    {
                        "content": r.content,
                        "source_type": r.source_type,
                        "source_name": r.source_name,
                        "score": r.score,
                        "metadata": r.metadata
                    }
                    for r in results.get("execution", [])
                ]
            }
        }

    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索记忆失败: {str(e)}")


@router.get("/memory/stats")
async def get_memory_stats(
    current_user: User = Depends(get_current_user)
):
    """获取记忆系统统计"""
    try:
        memory = get_agent_memory()

        return {
            "success": True,
            "data": {
                "sessions": len(memory.sessions),
                "knowledge_chunks": len(memory.knowledge_chunks),
                "execution_history": memory.get_execution_stats()
            }
        }

    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


# ========== Agent 执行引擎相关端点 ==========

class AgentExecuteRequest(BaseModel):
    """Agent 执行请求"""
    request: str = Field(..., description="用户自然语言请求")
    session_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    max_iterations: int = Field(20, ge=1, le=50, description="最大迭代次数")


@router.post("/agent/execute", response_model=Dict[str, Any])
async def execute_agent(
    req: AgentExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    执行 Agent 任务
    使用 Think-Act-Observe 循环执行用户请求
    """
    try:
        engine = get_agent_engine()

        logger.info(f"用户 {current_user.username} 请求: {req.request}")

        # 执行任务
        result = await engine.execute(
            user_request=req.request,
            session_id=req.session_id,
            max_iterations=req.max_iterations
        )

        return {
            "success": result.success,
            "data": {
                "status": result.status.value,
                "session_id": result.session_id,
                "steps_executed": result.steps_executed,
                "total_steps": result.total_steps,
                "execution_time": result.execution_time,
                "final_result": result.final_result,
                "step_results": result.step_results
            },
            "message": "执行完成" if result.success else f"执行失败: {result.error_message}"
        }

    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@router.get("/agent/status/{session_id}")
async def get_agent_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取 Agent 执行状态"""
    try:
        engine = get_agent_engine()
        status = engine.get_agent_status(session_id)

        if not status:
            raise HTTPException(status_code=404, detail="会话不存在或 Agent 已结束")

        return {
            "success": True,
            "data": status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 Agent 状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/agent/active")
async def list_active_agents(
    current_user: User = Depends(get_current_user)
):
    """列出所有活跃的 Agent"""
    try:
        engine = get_agent_engine()
        agents = engine.list_active_agents()

        return {
            "success": True,
            "data": agents,
            "total": len(agents)
        }

    except Exception as e:
        logger.error(f"获取活跃 Agent 列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/agent/executions")
async def get_execution_history(
    session_id: Optional[str] = Query(None, description="过滤特定会话"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(get_current_user)
):
    """获取执行历史"""
    try:
        memory = get_agent_memory()

        history = []
        for record in memory.execution_history[-limit:]:
            if session_id and record.session_id != session_id:
                continue

            history.append({
                "record_id": record.record_id,
                "session_id": record.session_id,
                "request": record.request,
                "status": record.status,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "steps_count": len(record.steps)
            })

        return {
            "success": True,
            "data": history,
            "total": len(history)
        }

    except Exception as e:
        logger.error(f"获取执行历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/agent/execution/{record_id}")
async def get_execution_detail(
    record_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取执行详情"""
    try:
        memory = get_agent_memory()

        record = next(
            (r for r in memory.execution_history if r.record_id == record_id),
            None
        )

        if not record:
            raise HTTPException(status_code=404, detail="执行记录不存在")

        return {
            "success": True,
            "data": {
                "record_id": record.record_id,
                "session_id": record.session_id,
                "request": record.request,
                "plan": record.plan,
                "status": record.status,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "error_message": record.error_message,
                "steps": record.steps
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取执行详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


# 参数映射相关模型
class ParameterMappingCreate(BaseModel):
    standard_parameter: str = Field(..., description="标准参数名称")
    software_specific_parameter: str = Field(..., description="软件特定参数名称")
    software_name: str = Field(..., description="软件名称")
    adapter_type: str = Field(..., description="适配器类型")
    description: str = Field(default="", description="映射描述")
    enabled: bool = Field(default=True, description="是否启用")


class ParameterMappingUpdate(BaseModel):
    standard_parameter: Optional[str] = None
    software_specific_parameter: Optional[str] = None
    software_name: Optional[str] = None
    adapter_type: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class ParameterMappingBatch(BaseModel):
    mappings: List[ParameterMappingCreate]


class ParameterMappingToggle(BaseModel):
    enabled: bool


# 临时内存存储参数映射
_parameter_mappings = []


@router.get("/parameter-mappings", response_model=Dict[str, Any])
async def get_parameter_mappings(
    current_user: User = Depends(get_current_user)
):
    """获取所有参数映射"""
    try:
        return {
            "success": True,
            "mappings": _parameter_mappings
        }
    except Exception as e:
        logger.error(f"获取参数映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取参数映射失败: {str(e)}")


@router.post("/parameter-mappings", response_model=Dict[str, Any])
async def create_parameter_mapping(
    mapping: ParameterMappingCreate,
    current_user: User = Depends(get_current_user)
):
    """创建参数映射"""
    try:
        new_mapping = {
            "id": str(len(_parameter_mappings) + 1),
            **mapping.dict(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        _parameter_mappings.append(new_mapping)
        return {
            "success": True,
            "mapping": new_mapping
        }
    except Exception as e:
        logger.error(f"创建参数映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建参数映射失败: {str(e)}")


@router.put("/parameter-mappings/{mapping_id}", response_model=Dict[str, Any])
async def update_parameter_mapping(
    mapping_id: str,
    mapping: ParameterMappingUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新参数映射"""
    try:
        for i, m in enumerate(_parameter_mappings):
            if m["id"] == mapping_id:
                update_data = {k: v for k, v in mapping.dict().items() if v is not None}
                _parameter_mappings[i].update(update_data)
                _parameter_mappings[i]["updated_at"] = datetime.now().isoformat()
                return {
                    "success": True,
                    "mapping": _parameter_mappings[i]
                }
        raise HTTPException(status_code=404, detail="参数映射不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新参数映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新参数映射失败: {str(e)}")


@router.delete("/parameter-mappings/{mapping_id}", response_model=Dict[str, Any])
async def delete_parameter_mapping(
    mapping_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除参数映射"""
    try:
        for i, m in enumerate(_parameter_mappings):
            if m["id"] == mapping_id:
                _parameter_mappings.pop(i)
                return {
                    "success": True,
                    "message": "删除成功"
                }
        raise HTTPException(status_code=404, detail="参数映射不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除参数映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除参数映射失败: {str(e)}")


@router.patch("/parameter-mappings/{mapping_id}/toggle", response_model=Dict[str, Any])
async def toggle_parameter_mapping(
    mapping_id: str,
    toggle: ParameterMappingToggle,
    current_user: User = Depends(get_current_user)
):
    """切换参数映射启用状态"""
    try:
        for m in _parameter_mappings:
            if m["id"] == mapping_id:
                m["enabled"] = toggle.enabled
                m["updated_at"] = datetime.now().isoformat()
                return {
                    "success": True,
                    "mapping": m
                }
        raise HTTPException(status_code=404, detail="参数映射不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换参数映射状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"切换参数映射状态失败: {str(e)}")


@router.post("/parameter-mappings/batch", response_model=Dict[str, Any])
async def batch_create_parameter_mappings(
    batch: ParameterMappingBatch,
    current_user: User = Depends(get_current_user)
):
    """批量创建参数映射"""
    try:
        created_mappings = []
        for mapping in batch.mappings:
            new_mapping = {
                "id": str(len(_parameter_mappings) + len(created_mappings) + 1),
                **mapping.dict(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            _parameter_mappings.append(new_mapping)
            created_mappings.append(new_mapping)
        
        return {
            "success": True,
            "mappings": created_mappings,
            "count": len(created_mappings)
        }
    except Exception as e:
        logger.error(f"批量创建参数映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量创建参数映射失败: {str(e)}")
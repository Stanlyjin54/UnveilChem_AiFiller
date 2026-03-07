"""
自动化API路由
提供自动化任务的创建、查询、控制和监控功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from ..services.automation.automation_service import get_automation_service
from ..services.automation.error_handler import ErrorSeverity, ErrorCategory
from ..services.automation.automation_engine import AutomationEngine
from ..services.automation.scheduler import TaskScheduler
from ..schemas.automation import (
    AutomationTaskCreate,
    AutomationTaskResponse,
    AutomationTaskStatus,
    AutomationTaskResult,
    ErrorStatistics,
    ErrorInfoResponse,
    BatchTaskCreate,
    BatchTaskResponse
)
# 临时简化认证，直接返回模拟用户
from ..models.user import User
from typing import Optional

def get_current_user() -> Optional[User]:
    """临时简化认证函数 - 返回模拟管理员用户"""
    return User(id=1, username="admin", email="admin@example.com", is_admin=True)
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["automation"])

# 获取自动化服务实例
async def get_service():
    return await get_automation_service()

# 全局错误处理器实例
error_handler = None
automation_engine = None
task_scheduler = None

# 初始化全局实例
async def init_global_instances():
    """初始化全局实例"""
    global error_handler, automation_engine, task_scheduler
    service = await get_automation_service()
    error_handler = service.error_handler
    automation_engine = service.automation_engine
    task_scheduler = service.task_scheduler

@router.post("/tasks", response_model=AutomationTaskResponse)
async def create_automation_task(
    task: AutomationTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """创建自动化任务"""
    try:
        # 使用服务创建任务
        return await service.create_task(task, current_user.id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"创建自动化任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.get("/tasks/{task_id}", response_model=AutomationTaskStatus)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """获取任务状态"""
    try:
        # 使用服务获取任务状态
        return service.get_task_status(task_id, current_user.id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.get("/tasks", response_model=List[AutomationTaskStatus])
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """获取任务列表"""
    try:
        # 使用服务获取用户任务列表
        return service.get_user_tasks(current_user.id, status, limit)
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """取消任务"""
    try:
        # 使用服务取消任务
        success = service.cancel_task(task_id, current_user.id)
        
        if success:
            return {"message": "任务已取消"}
        else:
            raise HTTPException(status_code=400, detail="无法取消任务")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")

@router.get("/tasks/{task_id}/result", response_model=AutomationTaskResult)
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """获取任务结果"""
    try:
        # 使用服务获取任务结果
        return service.get_task_result(task_id, current_user.id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务结果失败: {str(e)}")

@router.post("/batch-tasks", response_model=BatchTaskResponse)
async def create_batch_tasks(
    batch_task: BatchTaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """创建批量任务"""
    try:
        # 使用服务创建批量任务
        return service.create_batch_tasks(batch_task, current_user.id)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建批量任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建批量任务失败: {str(e)}")

@router.get("/errors/statistics", response_model=ErrorStatistics)
async def get_error_statistics(
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """获取错误统计信息"""
    try:
        # 只有管理员可以查看错误统计
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权限访问错误统计")
        
        # 初始化全局实例（如果需要）
        if not error_handler:
            await init_global_instances()
        
        stats = error_handler.get_error_statistics()
        return ErrorStatistics(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取错误统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误统计失败: {str(e)}")

@router.get("/errors", response_model=List[ErrorInfoResponse])
async def get_recent_errors(
    limit: int = 50,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """获取最近的错误信息"""
    try:
        # 只有管理员可以查看错误信息
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权限访问错误信息")
        
        # 初始化全局实例（如果需要）
        if not error_handler:
            await init_global_instances()
        
        errors = error_handler.get_recent_errors(limit)
        
        # 根据严重程度和类别过滤
        filtered_errors = errors
        if severity:
            filtered_errors = [e for e in filtered_errors if e['severity'] == severity]
        if category:
            filtered_errors = [e for e in filtered_errors if e['category'] == category]
        
        return [
            ErrorInfoResponse(**error)
            for error in filtered_errors
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取错误信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取错误信息失败: {str(e)}")

@router.post("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: str,
    current_user: User = Depends(get_current_user),
    service = Depends(get_service)
):
    """标记错误为已解决"""
    try:
        # 只有管理员可以标记错误为已解决
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权限执行此操作")
        
        # 初始化全局实例（如果需要）
        if not error_handler:
            await init_global_instances()
        
        # 查找错误
        found = False
        for error in error_handler.error_log:
            if error.error_id == error_id:
                error.resolved = True
                error.resolved_time = datetime.now()
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="错误不存在")
        
        return {"message": "错误已标记为已解决"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记错误为已解决失败: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")

@router.get("/health")
async def check_system_health(
    service = Depends(get_service)
):
    """检查系统健康状态"""
    try:
        # 初始化全局实例（如果需要）
        if not automation_engine or not task_scheduler or not error_handler:
            await init_global_instances()
        
        # 检查自动化引擎状态
        engine_status = automation_engine.get_status()
        
        # 检查调度器状态
        scheduler_status = task_scheduler.get_status()
        
        # 获取错误统计
        error_stats = error_handler.get_error_statistics()
        
        # 判断系统是否健康
        is_healthy = (
            engine_status.get('status') == 'running' and
            scheduler_status.get('status') == 'running' and
            error_stats.get('recent_errors_24h', 0) < 10  # 24小时内错误数少于10个
        )
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "engine": engine_status,
            "scheduler": scheduler_status,
            "errors": error_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"检查系统健康状态失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
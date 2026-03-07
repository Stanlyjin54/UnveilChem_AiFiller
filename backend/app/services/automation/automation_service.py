"""
自动化服务层
提供自动化任务的统一管理和协调
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from .automation_engine import AutomationEngine
from .scheduler import TaskScheduler, ScheduledTask as SchedulerTask, TaskPriority, TaskStatus
from .error_handler import AutomationErrorHandler, ErrorContext
from ...schemas.automation import (
    AutomationTaskCreate,
    AutomationTaskResponse,
    AutomationTaskStatus,
    AutomationTaskResult,
    BatchTaskCreate,
    BatchTaskResponse
)

logger = logging.getLogger(__name__)


class AutomationService:
    """自动化服务"""
    
    def __init__(self):
        self.engine = AutomationEngine()
        self.scheduler = TaskScheduler()
        self.error_handler = AutomationErrorHandler()
        self._initialized = False
        
        logger.info("自动化服务初始化完成")
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        try:
            # 启动调度器
            self.scheduler.start()
            
            # 启动引擎
            await self.engine.initialize()
            
            # 设置错误处理器
            self.engine.error_handler = self.error_handler
            
            self._initialized = True
            logger.info("自动化服务初始化成功")
            
        except Exception as e:
            logger.error(f"自动化服务初始化失败: {e}")
            raise
    
    async def create_task(self, task_data: AutomationTaskCreate, user_id: str) -> AutomationTaskResponse:
        """创建自动化任务"""
        try:
            # 创建调度任务
            scheduled_task = SchedulerTask(
                id=f"task_{uuid4().hex}",
                name=task_data.name,
                adapter_type=task_data.software_type,
                parameters=task_data.parameters,
                priority=TaskPriority(task_data.priority),
                user_id=user_id,
                created_at=datetime.now(),
                status=TaskStatus.PENDING,
                max_retries=task_data.retry_count
            )
            
            # 提交到调度器
            success = self.scheduler.submit_task(scheduled_task)
            if not success:
                raise Exception("任务提交失败")
            
            # 异步执行任务
            asyncio.create_task(self._execute_task(scheduled_task))
            
            return AutomationTaskResponse(
                task_id=scheduled_task.id,
                name=scheduled_task.name,
                status=scheduled_task.status.value,
                created_at=scheduled_task.created_at,
                message="任务已创建并提交执行"
            )
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            # 记录错误
            error_context = ErrorContext(
                operation="create_task",
                user_id=user_id,
                task_name=task_data.name,
                parameters=task_data.parameters
            )
            self.error_handler.handle_error(e, error_context)
            raise
    
    async def create_batch_tasks(self, batch_data: BatchTaskCreate, user_id: str) -> BatchTaskResponse:
        """创建批量任务"""
        try:
            task_ids = []
            
            # 为每个参数集创建任务
            for i, param_set in enumerate(batch_data.parameter_sets):
                task_name = f"{batch_data.name}_{i+1}"
                
                scheduled_task = SchedulerTask(
                    id=f"batch_task_{uuid4().hex}_{i}",
                    name=task_name,
                    adapter_type=batch_data.software_type,
                    parameters=param_set,
                    priority=TaskPriority(batch_data.priority),
                    user_id=user_id,
                    created_at=datetime.now(),
                    status=TaskStatus.PENDING,
                    parent_id=batch_data.batch_id
                )
                
                # 提交到调度器
                success = self.scheduler.submit_task(scheduled_task)
                if success:
                    task_ids.append(scheduled_task.id)
                    # 异步执行任务
                    asyncio.create_task(self._execute_task(scheduled_task))
            
            return BatchTaskResponse(
                batch_id=batch_data.batch_id,
                task_ids=task_ids,
                total_tasks=len(task_ids),
                message=f"批量任务已创建，共{len(task_ids)}个子任务"
            )
            
        except Exception as e:
            logger.error(f"创建批量任务失败: {e}")
            error_context = ErrorContext(
                operation="create_batch_tasks",
                user_id=user_id,
                batch_id=batch_data.batch_id
            )
            self.error_handler.handle_error(e, error_context)
            raise
    
    def get_task_status(self, task_id: str, user_id: str) -> AutomationTaskStatus:
        """获取任务状态"""
        try:
            # 从调度器获取任务
            task = self.scheduler.get_task(task_id)
            if not task:
                raise ValueError("任务不存在")
            
            # 检查权限
            if task.user_id != user_id:
                raise PermissionError("无权限访问此任务")
            
            return AutomationTaskStatus(
                task_id=task.id,
                name=task.name,
                status=task.status.value,
                progress=task.progress,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                error_message=task.error_message,
                result=task.result
            )
            
        except ValueError as e:
            raise
        except PermissionError as e:
            raise
        except Exception as e:
            logger.error(f"获取任务状态失败: {e}")
            raise
    
    def get_user_tasks(self, user_id: str, status: Optional[str] = None, limit: int = 50) -> List[AutomationTaskStatus]:
        """获取用户的任务列表"""
        try:
            # 获取用户的任务列表
            tasks = self.scheduler.get_user_tasks(user_id, status, limit)
            
            return [
                AutomationTaskStatus(
                    task_id=task.id,
                    name=task.name,
                    status=task.status.value,
                    progress=task.progress,
                    created_at=task.created_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    error_message=task.error_message,
                    result=task.result
                )
                for task in tasks
            ]
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}")
            raise
    
    def get_task_result(self, task_id: str, user_id: str) -> AutomationTaskResult:
        """获取任务结果"""
        try:
            task = self.scheduler.get_task(task_id)
            if not task:
                raise ValueError("任务不存在")
            
            # 检查权限
            if task.user_id != user_id:
                raise PermissionError("无权限访问此任务")
            
            # 检查任务是否完成
            if task.status != TaskStatus.COMPLETED:
                return AutomationTaskResult(
                    task_id=task_id,
                    ready=False,
                    message="任务尚未完成"
                )
            
            return AutomationTaskResult(
                task_id=task_id,
                ready=True,
                success=task.result.get('success', False) if task.result else False,
                data=task.result,
                execution_time=task.execution_time
            )
            
        except ValueError as e:
            raise
        except PermissionError as e:
            raise
        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            raise
    
    def cancel_task(self, task_id: str, user_id: str) -> bool:
        """取消任务"""
        try:
            task = self.scheduler.get_task(task_id)
            if not task:
                raise ValueError("任务不存在")
            
            # 检查权限
            if task.user_id != user_id:
                raise PermissionError("无权限访问此任务")
            
            # 取消任务
            return self.scheduler.cancel_task(task_id)
            
        except ValueError as e:
            raise
        except PermissionError as e:
            raise
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            raise
    
    async def _execute_task(self, task: SchedulerTask):
        """执行任务"""
        try:
            # 更新任务状态
            self.scheduler.update_task_status(
                task.id, 
                TaskStatus.RUNNING,
                progress=10.0
            )
            
            # 执行引擎任务
            result = await self.engine.execute_task_async(task)
            
            # 更新任务状态
            if result.get('success', False):
                self.scheduler.update_task_status(
                    task.id,
                    TaskStatus.COMPLETED,
                    progress=100.0,
                    result=result
                )
            else:
                self.scheduler.update_task_status(
                    task.id,
                    TaskStatus.FAILED,
                    progress=100.0,
                    error_message=result.get('error', '未知错误'),
                    result=result
                )
                
        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            # 更新任务状态
            self.scheduler.update_task_status(
                task.id,
                TaskStatus.FAILED,
                error_message=str(e)
            )
            
            # 记录错误
            error_context = ErrorContext(
                operation="execute_task",
                user_id=task.user_id,
                task_id=task.id,
                task_name=task.name,
                parameters=task.parameters
            )
            self.error_handler.handle_error(e, error_context)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        return self.error_handler.get_error_statistics()
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        return self.error_handler.get_recent_errors(limit)
    
    def resolve_error(self, error_id: str) -> bool:
        """标记错误为已解决"""
        return self.error_handler.resolve_error(error_id)
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 检查调度器状态
            scheduler_status = self.scheduler.get_status()
            
            # 检查引擎状态
            engine_status = self.engine.get_status()
            
            # 获取错误统计
            error_stats = self.get_error_statistics()
            
            # 判断系统是否健康
            is_healthy = (
                scheduler_status.get('status') == 'running' and
                engine_status.get('status') == 'running' and
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
            logger.error(f"获取系统健康状态失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局服务实例
_automation_service: Optional[AutomationService] = None


async def get_automation_service() -> AutomationService:
    """获取自动化服务实例"""
    global _automation_service
    if _automation_service is None:
        _automation_service = AutomationService()
        await _automation_service.initialize()
    return _automation_service


async def shutdown_automation_service():
    """关闭自动化服务"""
    global _automation_service
    if _automation_service:
        # 这里可以添加清理逻辑
        _automation_service = None
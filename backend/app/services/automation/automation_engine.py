#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化执行引擎
协调参数映射、软件适配器和调度功能
"""

import logging
import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus
from .parameter_mapper import ParameterMapper
from .error_handler import AutomationErrorHandler, ErrorSeverity, ErrorCategory, ErrorContext

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AutomationTask:
    """自动化任务"""
    task_id: str
    name: str
    parameters: Dict[str, Any]
    target_software: str
    adapter_type: str
    priority: int = 1
    created_time: datetime = None
    scheduled_time: datetime = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[AutomationResult] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now()

class AutomationEngine:
    """自动化执行引擎"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        from .parameter_mapper import AspenPlusParameterMapper, DWSIMParameterMapper, AutoCADParameterMapper, ExcelParameterMapper, PROIIParameterMapper, SoftwareType
        self.parameter_mappers: Dict[str, ParameterMapper] = {
            "aspen_plus": AspenPlusParameterMapper(SoftwareType.ASPEN_PLUS),
            "dwsim": DWSIMParameterMapper(SoftwareType.DWSIM),
            "autocad": AutoCADParameterMapper(SoftwareType.AUTOCAD),
            "excel": ExcelParameterMapper(SoftwareType.EXCEL),
            "pro_ii": PROIIParameterMapper(SoftwareType.PRO_II)
        }
        self.adapters: Dict[str, SoftwareAutomationAdapter] = {}
        self.task_queue = queue.PriorityQueue()
        self.running_tasks: Dict[str, AutomationTask] = {}
        self.completed_tasks: Dict[str, AutomationTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_running = False
        self.scheduler_thread = None
        self.task_counter = 0
        
        # 注册默认适配器
        self._register_default_adapters()
        
        # 初始化错误处理器
        self.error_handler = AutomationErrorHandler()
        
    def _register_default_adapters(self):
        """注册默认的软件适配器"""
        # 只注册基础适配器，避免服务启动失败
        self._register_safe_adapter("excel", "Excel", self._create_excel_adapter)
        self._register_safe_adapter("dwsim", "DWSIM", self._create_dwsim_adapter)
        
        # 跳过依赖特定软件的适配器，由用户手动启用
        logger.info("自动化引擎初始化完成 - 仅注册基础适配器")
        logger.info("提示：如需使用Aspen Plus、AutoCAD等适配器，请确保对应软件已安装")
    
    def _register_safe_adapter(self, adapter_name: str, display_name: str, adapter_factory):
        """安全地注册适配器，如果失败不影响服务启动"""
        try:
            adapter = adapter_factory()
            self.register_adapter(adapter_name, adapter)
            logger.info(f"注册 {display_name} 适配器")
        except Exception as e:
            logger.warning(f"注册 {display_name} 适配器失败: {e} - 服务将继续运行")
    
    def _create_excel_adapter(self):
        """创建Excel适配器"""
        from .excel_adapter import ExcelAdapter
        return ExcelAdapter()
    
    def _create_dwsim_adapter(self):
        """创建DWSIM适配器"""
        from .dwsim_adapter import DWSIMAdapter
        return DWSIMAdapter()
    
    def register_missing_adapter(self, adapter_name: str):
        """运行时注册缺失的适配器"""
        adapter_factories = {
            "aspen_plus": self._create_aspen_plus_adapter,
            "autocad": self._create_autocad_adapter,
            "pro_ii": self._create_pro_ii_adapter
        }
        
        if adapter_name in adapter_factories:
            self._register_safe_adapter(adapter_name, adapter_name.replace('_', ' ').title(), adapter_factories[adapter_name])
            return True
        return False
    
    def _create_aspen_plus_adapter(self):
        """创建Aspen Plus适配器"""
        from .aspen_plus import AspenPlusAdapter
        return AspenPlusAdapter()
    
    def _create_autocad_adapter(self):
        """创建AutoCAD适配器"""
        from .autocad_adapter import AutoCADAdapter
        return AutoCADAdapter()
    
    def _create_pro_ii_adapter(self):
        """创建PRO/II适配器"""
        from .pro_ii_adapter import PROIIAdapter
        return PROIIAdapter()
    
    def register_adapter(self, adapter_name: str, adapter: SoftwareAutomationAdapter):
        """注册软件适配器"""
        self.adapters[adapter_name] = adapter
        logger.info(f"注册适配器: {adapter_name}")
    
    def start(self):
        """启动自动化引擎"""
        if self.is_running:
            logger.warning("自动化引擎已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("自动化引擎已启动")
    
    def stop(self):
        """停止自动化引擎"""
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # 关闭所有适配器
        for adapter in self.adapters.values():
            try:
                adapter.disconnect()
            except Exception as e:
                logger.error(f"断开适配器连接失败: {e}")
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("自动化引擎已停止")
    
    def submit_task(self, name: str, parameters: Dict[str, Any], 
                   target_software: str, adapter_type: str,
                   priority: int = 1, scheduled_time: datetime = None) -> str:
        """提交自动化任务"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{int(time.time())}"
        
        task = AutomationTask(
            task_id=task_id,
            name=name,
            parameters=parameters,
            target_software=target_software,
            adapter_type=adapter_type,
            priority=priority,
            scheduled_time=scheduled_time
        )
        
        # 添加到任务队列
        self.task_queue.put((priority, task.created_time, task))
        
        logger.info(f"提交任务: {task_id} - {name}")
        return task_id
    
    def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器循环已启动")
        
        while self.is_running:
            try:
                # 从队列获取任务（非阻塞）
                try:
                    priority, created_time, task = self.task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # 检查是否到了执行时间
                if task.scheduled_time and datetime.now() < task.scheduled_time:
                    # 还未到执行时间，重新放回队列
                    self.task_queue.put((priority, created_time, task))
                    time.sleep(1)
                    continue
                
                # 执行任务
                self._execute_task(task)
                
            except Exception as e:
                logger.error(f"调度器循环出错: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: AutomationTask):
        """执行单个任务"""
        try:
            logger.info(f"开始执行任务: {task.task_id} - {task.name}")
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            self.running_tasks[task.task_id] = task
            
            # 获取适配器
            adapter = self.adapters.get(task.adapter_type)
            if not adapter:
                raise ValueError(f"未找到适配器: {task.adapter_type}")
            
            # 参数映射
            logger.info(f"映射参数到 {task.target_software}...")
            parameter_mapper = self.parameter_mappers.get(task.adapter_type)
            if not parameter_mapper:
                raise ValueError(f"未找到参数映射器: {task.adapter_type}")
            
            mapped_parameters = parameter_mapper.map_parameters(task.parameters)
            
            if not mapped_parameters:
                raise ValueError("参数映射失败")
            
            # 执行自动化
            future = self.executor.submit(self._run_automation, task)
            
            # 等待任务完成（带超时）
            try:
                result = future.result(timeout=300)  # 5分钟超时
                task.result = result
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                
                if not result.success and task.retry_count < task.max_retries:
                    # 重试任务
                    task.retry_count += 1
                    logger.warning(f"任务失败，准备重试 (第{task.retry_count}次): {task.task_id}")
                    task.status = TaskStatus.PENDING
                    self.task_queue.put((task.priority, task.created_time, task))
                    return
                
            except Exception as e:
                logger.error(f"任务执行超时或失败: {e}")
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                
                # 检查是否需要重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    logger.warning(f"任务失败，准备重试 (第{task.retry_count}次): {task.task_id}")
                    task.status = TaskStatus.PENDING
                    self.task_queue.put((task.priority, task.created_time, task))
                    return
            
            # 移动到完成任务列表
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
            
            logger.info(f"任务执行完成: {task.task_id} - 状态: {task.status.value}")
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self.completed_tasks[task.task_id] = task
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    def _run_automation(self, task: AutomationTask) -> AutomationResult:
        """运行自动化任务"""
        try:
            logger.info(f"开始执行自动化任务: {task.task_id}")
            
            # 获取适配器
            adapter = self.adapters.get(task.adapter_type)
            if not adapter:
                return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"不支持的软件类型: {task.adapter_type}",
                parameters_set={},
                execution_time=0.0,
                error_details=f"不支持的软件类型: {task.adapter_type}"
            )
            
            # 构建错误上下文
            error_context = ErrorContext(
                task_id=task.task_id,
                adapter_name=task.adapter_type,
                operation="execute_automation",
                parameters=task.parameters,
                user_id=task.user_id if hasattr(task, 'user_id') else None
            )
            
            # 使用错误处理器的重试策略执行自动化
            result = self.error_handler.retry_with_policy(
                func=adapter.execute_automation,
                context=error_context,
                parameters=task.parameters
            )
            
            logger.info(f"自动化任务执行成功: {task.task_id}")
            return result
            
        except Exception as e:
            logger.error(f"自动化任务执行失败: {task.task_id}, 错误: {e}")
            
            # 构建错误上下文
            error_context = ErrorContext(
                task_id=task.task_id,
                adapter_name=task.adapter_type,
                operation="execute_automation",
                parameters=task.parameters,
                user_id=task.user_id if hasattr(task, 'user_id') else None
            )
            
            # 使用错误处理器记录错误
            self.error_handler.handle_error(
                e,
                context=error_context,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.EXECUTION
            )
            
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=str(e),
                parameters_set={},
                execution_time=0.0,
                error_details=str(e)
            )
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].status
        
        # 检查已完成的任务
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        
        return None
    
    def get_task_result(self, task_id: str) -> Optional[AutomationResult]:
        """获取任务结果"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].result
        
        # 检查已完成的任务
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].result
        
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务信息"""
        all_tasks = []
        
        # 运行中的任务
        for task in self.running_tasks.values():
            all_tasks.append({
                'task_id': task.task_id,
                'name': task.name,
                'status': task.status.value,
                'target_software': task.target_software,
                'created_time': task.created_time.isoformat(),
                'retry_count': task.retry_count
            })
        
        # 已完成的任务
        for task in self.completed_tasks.values():
            all_tasks.append({
                'task_id': task.task_id,
                'name': task.name,
                'status': task.status.value,
                'target_software': task.target_software,
                'created_time': task.created_time.isoformat(),
                'retry_count': task.retry_count,
                'error_message': task.error_message
            })
        
        return all_tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 检查运行中的任务
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            self.completed_tasks[task_id] = task
            del self.running_tasks[task_id]
            logger.info(f"任务已取消: {task_id}")
            return True
        
        return False
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        self.completed_tasks.clear()
        logger.info("已清除所有已完成的任务")
    
    def batch_execute(self, tasks: List[Dict[str, Any]], 
                     callback: Optional[Callable[[str, AutomationResult], None]] = None) -> List[str]:
        """批量执行任务"""
        task_ids = []
        
        for task_data in tasks:
            task_id = self.submit_task(
                name=task_data.get('name', 'Batch Task'),
                parameters=task_data.get('parameters', {}),
                target_software=task_data.get('target_software', ''),
                adapter_type=task_data.get('adapter_type', ''),
                priority=task_data.get('priority', 1),
                scheduled_time=task_data.get('scheduled_time')
            )
            task_ids.append(task_id)
        
        # 等待所有任务完成（可选）
        if callback:
            self._wait_for_tasks(task_ids, callback)
        
        return task_ids
    
    def _wait_for_tasks(self, task_ids: List[str], 
                       callback: Callable[[str, AutomationResult], None], 
                       timeout: float = 300):
        """等待任务完成并调用回调"""
        start_time = time.time()
        
        while task_ids and (time.time() - start_time) < timeout:
            remaining_ids = []
            
            for task_id in task_ids:
                result = self.get_task_result(task_id)
                if result:
                    # 任务已完成，调用回调
                    callback(task_id, result)
                else:
                    # 任务仍在运行
                    remaining_ids.append(task_id)
            
            task_ids = remaining_ids
            if task_ids:
                time.sleep(1)
    
    def schedule_task(self, name: str, parameters: Dict[str, Any], 
                     target_software: str, adapter_type: str,
                     scheduled_time: datetime, priority: int = 1) -> str:
        """调度任务（定时执行）"""
        return self.submit_task(
            name=name,
            parameters=parameters,
            target_software=target_software,
            adapter_type=adapter_type,
            priority=priority,
            scheduled_time=scheduled_time
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.running_tasks) + len(self.completed_tasks)
        completed_tasks = sum(1 for task in self.completed_tasks.values() 
                            if task.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for task in self.completed_tasks.values() 
                          if task.status == TaskStatus.FAILED)
        
        return {
            'total_tasks': total_tasks,
            'running_tasks': len(self.running_tasks),
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'queue_size': self.task_queue.qsize(),
            'supported_adapters': list(self.adapters.keys()),
            'supported_software': list(self.parameter_mappers.keys())
        }
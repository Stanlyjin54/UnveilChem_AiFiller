"""
调度引擎 - 支持批量处理和定时任务
提供任务调度、队列管理、优先级处理等功能
"""

import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import heapq

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ScheduledTask:
    """定时任务配置"""
    task_id: str
    name: str
    schedule_time: datetime
    parameters: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    recurring: bool = False
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 60
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    execution_info: Dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    """任务队列 - 基于优先级的最小堆实现"""
    
    def __init__(self):
        self._queue = []  # 优先级队列 (priority, timestamp, task_id, task)
        self._tasks = {}  # task_id -> task 映射
        self._lock = threading.Lock()
    
    def put(self, task: ScheduledTask):
        """添加任务到队列"""
        with self._lock:
            # 使用优先级和时间戳作为排序键
            priority_value = task.priority.value
            timestamp = time.time()
            heapq.heappush(self._queue, (-priority_value, timestamp, task.task_id, task))
            self._tasks[task.task_id] = task
    
    def get(self, timeout: float = 0) -> Optional[ScheduledTask]:
        """从队列获取任务"""
        with self._lock:
            if not self._queue:
                return None
            
            # 获取最高优先级的任务
            _, _, task_id, task = heapq.heappop(self._queue)
            if task_id in self._tasks:
                del self._tasks[task_id]
                return task
            else:
                # 任务已被移除，递归获取下一个
                return self.get(timeout)
    
    def remove(self, task_id: str) -> bool:
        """从队列移除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                # 重新构建队列（移除已删除的任务）
                self._queue = [
                    (priority, timestamp, tid, task)
                    for priority, timestamp, tid, task in self._queue
                    if tid != task_id
                ]
                heapq.heapify(self._queue)
                return True
            return False
    
    def size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._tasks)
    
    def get_all_tasks(self) -> List[ScheduledTask]:
        """获取所有任务"""
        with self._lock:
            return list(self._tasks.values())


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = TaskQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        
        # 调度状态
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # 锁和事件
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._schedule_event = asyncio.Event()
        
        logger.info(f"任务调度器初始化完成，工作线程数: {max_workers}")
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    def schedule_task(self, name: str, parameters: Dict[str, Any], 
                     schedule_time: Optional[datetime] = None,
                     priority: TaskPriority = TaskPriority.NORMAL,
                     recurring: bool = False,
                     interval_seconds: Optional[int] = None,
                     cron_expression: Optional[str] = None,
                     max_retries: int = 3) -> str:
        """调度任务"""
        task_id = str(uuid.uuid4())
        
        # 如果没有指定时间，立即执行
        if schedule_time is None:
            schedule_time = datetime.now()
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule_time=schedule_time,
            parameters=parameters,
            priority=priority,
            recurring=recurring,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            max_retries=max_retries
        )
        
        # 计算下次运行时间
        if recurring:
            task.next_run = schedule_time
        
        with self._lock:
            self.scheduled_tasks[task_id] = task
        
        # 如果任务可以立即执行，加入队列
        if schedule_time <= datetime.now():
            self.task_queue.put(task)
            logger.info(f"任务已加入队列: {task_id} - {name}")
        else:
            logger.info(f"任务已调度: {task_id} - {name}，执行时间: {schedule_time}")
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            # 从队列中移除
            removed_from_queue = self.task_queue.remove(task_id)
            
            # 从调度任务中移除
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
                logger.info(f"任务已取消: {task_id}")
                return True
            
            # 取消正在运行的任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
                logger.info(f"正在运行的任务已取消: {task_id}")
                return True
            
            return removed_from_queue
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        return self.task_results.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        with self._lock:
            tasks = []
            
            # 队列中的任务
            for task in self.task_queue.get_all_tasks():
                tasks.append({
                    'task_id': task.task_id,
                    'name': task.name,
                    'status': TaskStatus.PENDING.value,
                    'priority': task.priority.value,
                    'schedule_time': task.schedule_time.isoformat(),
                    'parameters': task.parameters
                })
            
            # 正在运行的任务
            for task_id, task in self.running_tasks.items():
                tasks.append({
                    'task_id': task_id,
                    'name': getattr(task, 'name', 'Unknown'),
                    'status': TaskStatus.RUNNING.value,
                    'start_time': datetime.now().isoformat()
                })
            
            # 已完成的任务
            for task_id, result in self.task_results.items():
                tasks.append({
                    'task_id': task_id,
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat() if result.start_time else None,
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'error': result.error
                })
            
            # 调度的任务
            for task in self.scheduled_tasks.values():
                if task.task_id not in [t['task_id'] for t in tasks]:
                    tasks.append({
                        'task_id': task.task_id,
                        'name': task.name,
                        'status': 'scheduled',
                        'priority': task.priority.value,
                        'schedule_time': task.schedule_time.isoformat(),
                        'next_run': task.next_run.isoformat() if task.next_run else None,
                        'recurring': task.recurring
                    })
            
            return tasks
    
    async def _execute_task(self, task: ScheduledTask) -> TaskResult:
        """执行任务"""
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )
        
        try:
            # 获取任务处理器
            task_type = task.parameters.get('task_type', 'default')
            handler = self.task_handlers.get(task_type)
            
            if not handler:
                raise ValueError(f"未找到任务处理器: {task_type}")
            
            logger.info(f"开始执行任务: {task.task_id} - {task.name}")
            
            # 执行任务
            task_result = await asyncio.get_event_loop().run_in_executor(
                self.executor, handler, task.parameters
            )
            
            # 更新结果
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            result.end_time = datetime.now()
            
            logger.info(f"任务执行成功: {task.task_id}")
            
        except asyncio.CancelledError:
            result.status = TaskStatus.CANCELLED
            result.error = "任务被取消"
            logger.warning(f"任务被取消: {task.task_id}")
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            result.retry_count += 1
            
            logger.error(f"任务执行失败: {task.task_id} - {e}")
            
            # 重试机制
            if result.retry_count < task.max_retries:
                result.status = TaskStatus.RETRYING
                logger.info(f"任务重试: {task.task_id} (尝试 {result.retry_count + 1}/{task.max_retries})")
                
                # 延迟重试
                await asyncio.sleep(task.retry_delay)
                
                # 重新加入队列
                task.schedule_time = datetime.now() + timedelta(seconds=task.retry_delay)
                self.task_queue.put(task)
        
        return result
    
    async def _process_tasks(self):
        """处理任务队列"""
        while self.is_running:
            try:
                # 获取待执行任务
                task = self.task_queue.get(timeout=1.0)
                
                if task:
                    # 添加到运行任务列表
                    with self._lock:
                        self.running_tasks[task.task_id] = asyncio.create_task(self._execute_task(task))
                    
                    # 等待任务完成
                    result = await self.running_tasks[task.task_id]
                    
                    # 更新结果
                    with self._lock:
                        self.task_results[task.task_id] = result
                        if task.task_id in self.running_tasks:
                            del self.running_tasks[task.task_id]
                    
                    # 处理循环任务
                    if task.recurring and result.status != TaskStatus.CANCELLED:
                        if task.interval_seconds:
                            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
                            task.schedule_time = task.next_run
                            self.scheduled_tasks[task.task_id] = task
                        # TODO: 支持 cron 表达式
                
                # 检查定时任务
                await self._check_scheduled_tasks()
                
            except asyncio.TimeoutError:
                # 检查定时任务
                await self._check_scheduled_tasks()
                continue
                
            except Exception as e:
                logger.error(f"处理任务时出错: {e}")
    
    async def _check_scheduled_tasks(self):
        """检查定时任务"""
        now = datetime.now()
        tasks_to_schedule = []
        
        with self._lock:
            for task_id, task in list(self.scheduled_tasks.items()):
                if task.enabled and task.next_run and task.next_run <= now:
                    tasks_to_schedule.append(task)
                    if task.recurring:
                        # 更新下次运行时间
                        if task.interval_seconds:
                            task.next_run = now + timedelta(seconds=task.interval_seconds)
                        # 重新加入调度列表
                        self.scheduled_tasks[task_id] = task
                    else:
                        # 非循环任务，从调度列表中移除
                        del self.scheduled_tasks[task_id]
        
        # 将到期的任务加入队列
        for task in tasks_to_schedule:
            self.task_queue.put(task)
    
    def _scheduler_loop(self):
        """调度器循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            self.scheduler_task = loop.create_task(self._process_tasks())
            loop.run_until_complete(self.scheduler_task)
        except Exception as e:
            logger.error(f"调度器循环出错: {e}")
        finally:
            loop.close()
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self._stop_event.clear()
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        logger.info("正在停止任务调度器...")
        self.is_running = False
        self._stop_event.set()
        
        # 取消所有正在运行的任务
        with self._lock:
            for task in self.running_tasks.values():
                task.cancel()
        
        # 等待调度线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5.0)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("任务调度器已停止")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'queue_size': self.task_queue.size(),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.task_results),
            'scheduled_tasks': len(self.scheduled_tasks),
            'max_workers': self.max_workers,
            'is_running': self.is_running
        }


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.batch_tasks: Dict[str, List[str]] = {}  # batch_id -> task_ids
        self.batch_results: Dict[str, Dict[str, Any]] = {}  # batch_id -> batch_info
    
    def create_batch(self, batch_name: str, tasks: List[Dict[str, Any]], 
                    priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """创建批量任务"""
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # 创建批量任务
        for i, task_config in enumerate(tasks):
            task_name = f"{batch_name}_{i}"
            task_id = self.scheduler.schedule_task(
                name=task_name,
                parameters=task_config,
                priority=priority
            )
            task_ids.append(task_id)
        
        # 记录批量任务信息
        self.batch_tasks[batch_id] = task_ids
        self.batch_results[batch_id] = {
            'batch_id': batch_id,
            'batch_name': batch_name,
            'task_count': len(tasks),
            'created_at': datetime.now().isoformat(),
            'task_ids': task_ids,
            'status': 'pending'
        }
        
        logger.info(f"批量任务已创建: {batch_id}，包含 {len(tasks)} 个任务")
        return batch_id
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批量任务状态"""
        if batch_id not in self.batch_tasks:
            return None
        
        task_ids = self.batch_tasks[batch_id]
        batch_info = self.batch_results[batch_id].copy()
        
        # 统计任务状态
        task_statuses = []
        completed_count = 0
        failed_count = 0
        running_count = 0
        pending_count = 0
        
        for task_id in task_ids:
            result = self.scheduler.get_task_status(task_id)
            if result:
                task_info = {
                    'task_id': task_id,
                    'status': result.status.value,
                    'start_time': result.start_time.isoformat() if result.start_time else None,
                    'end_time': result.end_time.isoformat() if result.end_time else None,
                    'error': result.error
                }
                
                if result.status == TaskStatus.COMPLETED:
                    completed_count += 1
                elif result.status == TaskStatus.FAILED:
                    failed_count += 1
                elif result.status == TaskStatus.RUNNING:
                    running_count += 1
                
                task_statuses.append(task_info)
            else:
                # 任务还在队列中
                pending_count += 1
                task_statuses.append({
                    'task_id': task_id,
                    'status': 'pending'
                })
        
        # 更新批量状态
        if failed_count > 0:
            batch_info['status'] = 'failed'
        elif completed_count == len(task_ids):
            batch_info['status'] = 'completed'
        elif running_count > 0:
            batch_info['status'] = 'running'
        else:
            batch_info['status'] = 'pending'
        
        batch_info.update({
            'completed_count': completed_count,
            'failed_count': failed_count,
            'running_count': running_count,
            'pending_count': pending_count,
            'task_statuses': task_statuses
        })
        
        return batch_info
    
    def cancel_batch(self, batch_id: str) -> bool:
        """取消批量任务"""
        if batch_id not in self.batch_tasks:
            return False
        
        task_ids = self.batch_tasks[batch_id]
        cancelled_count = 0
        
        for task_id in task_ids:
            if self.scheduler.cancel_task(task_id):
                cancelled_count += 1
        
        logger.info(f"批量任务已取消: {batch_id}，取消了 {cancelled_count} 个任务")
        return True
    
    def get_all_batches(self) -> List[Dict[str, Any]]:
        """获取所有批量任务"""
        return list(self.batch_results.values())


# 全局调度器实例
_scheduler: Optional[TaskScheduler] = None
_batch_processor: Optional[BatchProcessor] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def get_batch_processor() -> BatchProcessor:
    """获取全局批量处理器实例"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(get_scheduler())
    return _batch_processor


def initialize_scheduler(max_workers: int = 4):
    """初始化调度器"""
    global _scheduler, _batch_processor
    
    if _scheduler is None:
        _scheduler = TaskScheduler(max_workers=max_workers)
        _batch_processor = BatchProcessor(_scheduler)
        logger.info(f"调度器初始化完成，工作线程数: {max_workers}")
    
    return _scheduler, _batch_processor


def start_scheduler():
    """启动调度器"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """停止调度器"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None


def schedule_task(name: str, parameters: Dict[str, Any], **kwargs) -> str:
    """调度任务"""
    scheduler = get_scheduler()
    return scheduler.schedule_task(name, parameters, **kwargs)


def create_batch(batch_name: str, tasks: List[Dict[str, Any]], **kwargs) -> str:
    """创建批量任务"""
    batch_processor = get_batch_processor()
    return batch_processor.create_batch(batch_name, tasks, **kwargs)


def get_task_status(task_id: str) -> Optional[TaskResult]:
    """获取任务状态"""
    scheduler = get_scheduler()
    return scheduler.get_task_status(task_id)


def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """获取批量任务状态"""
    batch_processor = get_batch_processor()
    return batch_processor.get_batch_status(batch_id)
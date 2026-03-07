"""
自动化相关的数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutomationTaskCreate(BaseModel):
    """创建自动化任务的请求模型"""
    name: str = Field(..., description="任务名称")
    software_type: str = Field(..., description="软件类型 (solidworks, autocad, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    priority: str = Field(default="normal", description="任务优先级")
    retry_count: int = Field(default=3, description="重试次数")
    timeout: int = Field(default=300, description="超时时间(秒)")


class AutomationTaskResponse(BaseModel):
    """创建任务的响应模型"""
    task_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    message: str = Field(..., description="响应消息")


class AutomationTaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: str = Field(..., description="任务状态")
    progress: float = Field(default=0.0, description="进度(0-100)")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误消息")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")


class AutomationTaskResult(BaseModel):
    """任务结果模型"""
    task_id: str = Field(..., description="任务ID")
    ready: bool = Field(..., description="结果是否就绪")
    success: Optional[bool] = Field(None, description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="结果数据")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    message: Optional[str] = Field(None, description="消息")


class BatchTaskCreate(BaseModel):
    """批量任务创建模型"""
    batch_id: str = Field(..., description="批次ID")
    name: str = Field(..., description="批次名称")
    software_type: str = Field(..., description="软件类型")
    parameter_sets: List[Dict[str, Any]] = Field(..., description="参数集合列表")
    priority: str = Field(default="normal", description="任务优先级")


class BatchTaskResponse(BaseModel):
    """批量任务响应模型"""
    batch_id: str = Field(..., description="批次ID")
    task_ids: List[str] = Field(..., description="任务ID列表")
    total_tasks: int = Field(..., description="总任务数")
    message: str = Field(..., description="响应消息")


class ErrorSeverity(str, Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """错误类别"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    SYSTEM = "system"
    BUSINESS = "business"
    UNKNOWN = "unknown"


class ErrorInfoResponse(BaseModel):
    """错误信息响应模型"""
    error_id: str = Field(..., description="错误ID")
    error_code: Optional[str] = Field(None, description="错误代码")
    message: str = Field(..., description="错误消息")
    severity: str = Field(..., description="严重程度")
    category: str = Field(..., description="错误类别")
    context: Dict[str, Any] = Field(default_factory=dict, description="错误上下文")
    occurred_at: datetime = Field(..., description="发生时间")
    resolved: bool = Field(default=False, description="是否已解决")
    resolved_time: Optional[datetime] = Field(None, description="解决时间")
    retry_count: int = Field(default=0, description="重试次数")
    recovery_attempts: int = Field(default=0, description="恢复尝试次数")


class ErrorStatistics(BaseModel):
    """错误统计模型"""
    total_errors: int = Field(..., description="总错误数")
    recent_errors_24h: int = Field(..., description="24小时内错误数")
    recent_errors_7d: int = Field(..., description="7天内错误数")
    errors_by_severity: Dict[str, int] = Field(..., description="按严重程度分类的错误数")
    errors_by_category: Dict[str, int] = Field(..., description="按类别分类的错误数")
    top_error_types: List[Dict[str, Any]] = Field(..., description="最常见的错误类型")
    resolution_rate: float = Field(..., description="解决率")


class SystemHealth(BaseModel):
    """系统健康状态模型"""
    status: str = Field(..., description="系统状态")
    engine_status: Dict[str, Any] = Field(..., description="引擎状态")
    scheduler_status: Dict[str, Any] = Field(..., description="调度器状态")
    error_stats: Dict[str, Any] = Field(..., description="错误统计")
    timestamp: datetime = Field(..., description="检查时间")


class AutomationConfig(BaseModel):
    """自动化配置模型"""
    max_concurrent_tasks: int = Field(default=5, description="最大并发任务数")
    default_retry_count: int = Field(default=3, description="默认重试次数")
    default_timeout: int = Field(default=300, description="默认超时时间")
    enable_error_notifications: bool = Field(default=True, description="启用错误通知")
    notification_threshold: str = Field(default="high", description="通知阈值")
    enable_auto_recovery: bool = Field(default=True, description="启用自动恢复")
    recovery_max_attempts: int = Field(default=3, description="最大恢复尝试次数")


class TaskExecutionLog(BaseModel):
    """任务执行日志模型"""
    log_id: str = Field(..., description="日志ID")
    task_id: str = Field(..., description="任务ID")
    step_name: str = Field(..., description="步骤名称")
    status: str = Field(..., description="执行状态")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: datetime = Field(..., description="时间戳")


class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    metric_id: str = Field(..., description="指标ID")
    task_id: str = Field(..., description="任务ID")
    operation: str = Field(..., description="操作名称")
    duration: float = Field(..., description="执行时间(秒)")
    memory_usage: Optional[float] = Field(None, description="内存使用(MB)")
    cpu_usage: Optional[float] = Field(None, description="CPU使用(%)")
    timestamp: datetime = Field(..., description="时间戳")
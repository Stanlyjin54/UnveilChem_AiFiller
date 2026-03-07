"""
错误处理和容错机制
提供统一的错误处理、重试机制、错误恢复和监控功能
"""

import logging
import time
import traceback
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import threading
import json
from datetime import datetime, timedelta
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别"""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    EXECUTION = "execution"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """错误上下文信息"""
    task_id: Optional[str] = None
    adapter_name: Optional[str] = None
    operation: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on: List[ErrorCategory] = field(default_factory=lambda: [ErrorCategory.CONNECTION, ErrorCategory.TIMEOUT])

@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: str
    stack_trace: str
    context: ErrorContext
    recovery_attempts: int = 0
    resolved: bool = False
    resolved_time: Optional[datetime] = None
    retry_count: int = 0
    notification_sent: bool = False

class NotificationHandler(ABC):
    """通知处理器基类"""
    
    @abstractmethod
    async def send_notification(self, error_info: ErrorInfo, config: Dict[str, Any]) -> bool:
        """发送通知"""
        pass

class EmailNotificationHandler(NotificationHandler):
    """邮件通知处理器"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send_notification(self, error_info: ErrorInfo, config: Dict[str, Any]) -> bool:
        """发送邮件通知"""
        try:
            recipients = config.get('recipients', [])
            if not recipients:
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"自动化错误通知 - {error_info.severity.value.upper()}"
            
            body = f"""
            错误详情：
            - 错误ID: {error_info.error_id}
            - 时间: {error_info.timestamp}
            - 严重程度: {error_info.severity.value}
            - 类别: {error_info.category.value}
            - 消息: {error_info.message}
            - 上下文: {error_info.context}
            - 重试次数: {error_info.retry_count}
            - 恢复尝试: {error_info.recovery_attempts}
            
            堆栈跟踪：
            {error_info.stack_trace}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"邮件通知发送成功: {error_info.error_id}")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            return False

class LogNotificationHandler(NotificationHandler):
    """日志通知处理器"""
    
    async def send_notification(self, error_info: ErrorInfo, config: Dict[str, Any]) -> bool:
        """记录日志通知"""
        try:
            log_level = config.get('level', 'error')
            if log_level == 'critical':
                logger.critical(f"关键错误: {error_info.error_id} - {error_info.message}")
            elif log_level == 'error':
                logger.error(f"错误: {error_info.error_id} - {error_info.message}")
            elif log_level == 'warning':
                logger.warning(f"警告: {error_info.error_id} - {error_info.message}")
            else:
                logger.info(f"信息: {error_info.error_id} - {error_info.message}")
            
            return True
            
        except Exception as e:
            logger.error(f"日志通知失败: {e}")
            return False

class RetryPolicy:
    """重试策略"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def get_delay(self, attempt: int) -> float:
        """获取重试延迟时间"""
        if attempt >= self.config.max_retries:
            return 0.0
        
        # 指数退避
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # 限制最大延迟
        delay = min(delay, self.config.max_delay)
        
        # 添加随机抖动
        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """检查是否应该重试"""
        return (
            error_info.retry_count < self.config.max_retries and
            error_info.category in self.config.retry_on
        )

class ErrorRecoveryStrategy:
    """错误恢复策略"""
    
    def __init__(self, name: str, condition: Callable[[ErrorInfo], bool],
                 recovery_action: Callable[[ErrorInfo], bool],
                 priority: int = 1):
        self.name = name
        self.condition = condition
        self.recovery_action = recovery_action
        self.priority = priority
    
    def can_handle(self, error_info: ErrorInfo) -> bool:
        """检查是否能处理此错误"""
        try:
            return self.condition(error_info)
        except Exception as e:
            logger.error(f"检查恢复策略条件失败: {e}")
            return False
    
    def recover(self, error_info: ErrorInfo) -> bool:
        """执行恢复操作"""
        try:
            logger.info(f"执行恢复策略: {self.name} - 错误ID: {error_info.error_id}")
            result = self.recovery_action(error_info)
            error_info.recovery_attempts += 1
            return result
        except Exception as e:
            logger.error(f"执行恢复策略失败: {e}")
            return False

class AutomationErrorHandler:
    """自动化错误处理器"""
    
    def __init__(self):
        self.error_log: List[ErrorInfo] = []
        self.retry_policies: Dict[str, RetryPolicy] = {}
        self.recovery_strategies: List[ErrorRecoveryStrategy] = []
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        self.notification_handlers: Dict[str, NotificationHandler] = {}
        self.lock = threading.Lock()
        
        # 设置默认重试策略
        self.set_retry_policy("default", RetryPolicy(RetryConfig()))
        
        # 注册默认恢复策略
        self._register_default_recovery_strategies()
        
        # 注册默认通知处理器
        self._register_default_notification_handlers()
    
    def _register_default_recovery_strategies(self):
        """注册默认恢复策略"""
        
        # 连接错误恢复策略
        connection_recovery = ErrorRecoveryStrategy(
            name="重新连接",
            condition=lambda error: error.category == ErrorCategory.CONNECTION,
            recovery_action=self._reconnect_recovery,
            priority=1
        )
        self.register_recovery_strategy(connection_recovery)
        
        # 认证错误恢复策略
        auth_recovery = ErrorRecoveryStrategy(
            name="重新认证",
            condition=lambda error: error.category == ErrorCategory.AUTHENTICATION,
            recovery_action=self._reauthenticate_recovery,
            priority=2
        )
        self.register_recovery_strategy(auth_recovery)
        
        # 资源错误恢复策略
        resource_recovery = ErrorRecoveryStrategy(
            name="资源清理",
            condition=lambda error: error.category == ErrorCategory.RESOURCE,
            recovery_action=self._resource_cleanup_recovery,
            priority=3
        )
        self.register_recovery_strategy(resource_recovery)
    
    def set_retry_policy(self, policy_name: str, retry_policy: RetryPolicy):
        """设置重试策略"""
        self.retry_policies[policy_name] = retry_policy
        logger.info(f"设置重试策略: {policy_name}")
    
    def register_recovery_strategy(self, strategy: ErrorRecoveryStrategy):
        """注册恢复策略"""
        self.recovery_strategies.append(strategy)
        # 按优先级排序
        self.recovery_strategies.sort(key=lambda x: x.priority)
        logger.info(f"注册恢复策略: {strategy.name}")
    
    def register_error_callback(self, callback: Callable[[ErrorInfo], None]):
        """注册错误回调"""
        self.error_callbacks.append(callback)
    
    def register_notification_handler(self, name: str, handler: NotificationHandler):
        """注册通知处理器"""
        self.notification_handlers[name] = handler
        logger.info(f"注册通知处理器: {name}")
    
    def _register_default_notification_handlers(self):
        """注册默认通知处理器"""
        # 日志通知处理器
        log_handler = LogNotificationHandler()
        self.register_notification_handler("log", log_handler)
    
    async def send_notifications(self, error_info: ErrorInfo):
        """发送错误通知"""
        if error_info.notification_sent:
            return
        
        # 根据严重程度决定通知级别
        notification_configs = self._get_notification_configs(error_info.severity)
        
        for config in notification_configs:
            handler_name = config.get('handler')
            handler = self.notification_handlers.get(handler_name)
            if handler:
                try:
                    await handler.send_notification(error_info, config)
                except Exception as e:
                    logger.error(f"通知发送失败 {handler_name}: {e}")
        
        error_info.notification_sent = True
    
    def _get_notification_configs(self, severity: ErrorSeverity) -> List[Dict[str, Any]]:
        """获取通知配置"""
        configs = []
        
        # 所有错误都记录日志
        configs.append({
            'handler': 'log',
            'level': 'error'
        })
        
        # 高严重程度和关键错误发送邮件
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            configs.append({
                'handler': 'email',
                'recipients': ['admin@unveilchem.com']
            })
        
        return configs
    
    def handle_error(self, exception: Exception, context: ErrorContext = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = None) -> ErrorInfo:
        """处理错误"""
        
        # 生成错误ID
        error_id = f"error_{uuid.uuid4().hex}"
        
        # 确定错误类别
        if category is None:
            category = self._categorize_error(exception)
        
        # 创建错误信息
        error_info = ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(exception),
            details=self._get_error_details(exception),
            stack_trace=traceback.format_exc(),
            context=context or ErrorContext()
        )
        
        # 记录错误
        with self.lock:
            self.error_log.append(error_info)
            # 限制错误日志大小
            if len(self.error_log) > 1000:
                self.error_log = self.error_log[-1000:]
        
        # 记录到日志
        logger.error(f"错误处理: {error_info.error_id} - {error_info.message}")
        
        # 触发错误回调
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"错误回调执行失败: {e}")
        
        # 异步发送通知
        try:
            # 检查是否有运行的事件循环
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.send_notifications(error_info))
        except RuntimeError:
            # 没有运行的事件循环，同步发送通知
            asyncio.run(self.send_notifications(error_info))
        
        return error_info
    
    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """分类错误"""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__.lower()
        
        # COM错误处理
        if "com" in error_message or "com_error" in exception_type:
            if any(keyword in error_message for keyword in ["connect", "connection", "network"]):
                return ErrorCategory.CONNECTION
            elif any(keyword in error_message for keyword in ["permission", "access", "denied"]):
                return ErrorCategory.AUTHENTICATION
            elif any(keyword in error_message for keyword in ["memory", "resource", "disk", "space"]):
                return ErrorCategory.RESOURCE
            else:
                return ErrorCategory.EXECUTION
        
        # 通用错误分类
        if any(keyword in error_message for keyword in ["connection", "connect", "network", "refused", "reset"]):
            return ErrorCategory.CONNECTION
        elif any(keyword in error_message for keyword in ["auth", "permission", "unauthorized", "forbidden", "access denied"]):
            return ErrorCategory.AUTHENTICATION
        elif any(keyword in error_message for keyword in ["validation", "invalid", "format", "schema", "constraint"]):
            return ErrorCategory.VALIDATION
        elif any(keyword in error_message for keyword in ["memory", "resource", "disk", "quota", "space", "limit"]):
            return ErrorCategory.RESOURCE
        elif any(keyword in error_message for keyword in ["timeout", "time out", "expired", "deadline"]):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_message for keyword in ["not found", "missing", "doesn\'t exist", "unavailable"]):
            return ErrorCategory.EXECUTION
        else:
            return ErrorCategory.EXECUTION
    
    def _get_error_details(self, exception: Exception) -> str:
        """获取错误详情"""
        details = []
        
        # 异常类型
        details.append(f"异常类型: {type(exception).__name__}")
        
        # 异常参数
        if exception.args:
            details.append(f"异常参数: {exception.args}")
        
        # 特殊处理某些异常类型
        if hasattr(exception, 'errno'):
            details.append(f"错误码: {exception.errno}")
        
        if hasattr(exception, 'strerror'):
            details.append(f"错误描述: {exception.strerror}")
        
        # COM错误特殊处理
        if hasattr(exception, 'hresult'):
            details.append(f"COM错误码: {hex(exception.hresult)}")
        
        if hasattr(exception, 'excepinfo'):
            details.append(f"COM异常信息: {exception.excepinfo}")
        
        return "; ".join(details)
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """尝试错误恢复"""
        
        for strategy in self.recovery_strategies:
            if strategy.can_handle(error_info):
                try:
                    if strategy.recover(error_info):
                        error_info.resolved = True
                        error_info.resolved_time = datetime.now()
                        logger.info(f"错误恢复成功: {error_info.error_id}")
                        return True
                except Exception as e:
                    logger.error(f"恢复策略执行失败: {e}")
        
        return False
    
    def retry_with_policy(self, func: Callable, policy_name: str = "default",
                         context: ErrorContext = None, *args, **kwargs):
        """使用重试策略执行函数"""
        
        retry_policy = self.retry_policies.get(policy_name)
        if not retry_policy:
            retry_policy = self.retry_policies["default"]
        
        last_exception = None
        
        for attempt in range(retry_policy.config.max_retries + 1):
            try:
                logger.info(f"执行尝试 {attempt + 1}/{retry_policy.config.max_retries + 1}")
                result = func(*args, **kwargs)
                
                # 如果成功，返回结果
                logger.info(f"执行成功 - 尝试 {attempt + 1}")
                return result
                
            except Exception as e:
                last_exception = e
                
                # 创建错误信息但不立即处理，避免重复记录
                error_info = ErrorInfo(
                    error_id=f"error_{uuid.uuid4().hex}",
                    timestamp=datetime.now(),
                    severity=ErrorSeverity.MEDIUM,
                    category=self._categorize_error(e),
                    message=str(e),
                    details=self._get_error_details(e),
                    stack_trace=traceback.format_exc(),
                    context=context or ErrorContext(),
                    retry_count=attempt
                )
                
                # 检查是否应该重试
                if retry_policy.should_retry(error_info) and attempt < retry_policy.config.max_retries:
                    delay = retry_policy.get_delay(attempt)
                    logger.warning(f"执行失败 - 尝试 {attempt + 1}, "
                                 f"等待 {delay:.1f}秒后重试: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"执行最终失败 - 尝试 {attempt + 1}: {e}")
                    break
        
        # 所有重试都失败，处理错误
        final_error_info = self.handle_error(
            last_exception,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=self._categorize_error(last_exception)
        )
        
        # 尝试恢复
        self._attempt_recovery(final_error_info)
        
        # 重新抛出异常
        raise last_exception
    
    def _try_recovery(self, error_info: ErrorInfo) -> bool:
        """尝试错误恢复 (兼容旧版本)"""
        return self._attempt_recovery(error_info)
    
    def _reconnect_recovery(self, error_info: ErrorInfo) -> bool:
        """重新连接恢复策略"""
        try:
            logger.info(f"尝试重新连接恢复: {error_info.error_id}")
            
            # 这里可以添加具体的重新连接逻辑
            # 例如：关闭现有连接，重新初始化适配器等
            
            time.sleep(2)  # 等待一段时间后重试
            return True
            
        except Exception as e:
            logger.error(f"重新连接恢复失败: {e}")
            return False
    
    def _reauthenticate_recovery(self, error_info: ErrorInfo) -> bool:
        """重新认证恢复策略"""
        try:
            logger.info(f"尝试重新认证恢复: {error_info.error_id}")
            
            # 这里可以添加具体的重新认证逻辑
            # 例如：刷新令牌，重新登录等
            
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"重新认证恢复失败: {e}")
            return False
    
    def _resource_cleanup_recovery(self, error_info: ErrorInfo) -> bool:
        """资源清理恢复策略"""
        try:
            logger.info(f"尝试资源清理恢复: {error_info.error_id}")
            
            # 这里可以添加具体的资源清理逻辑
            # 例如：释放内存，关闭文件句柄，清理临时文件等
            
            import gc
            gc.collect()  # 垃圾回收
            
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"资源清理恢复失败: {e}")
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        with self.lock:
            total_errors = len(self.error_log)
            
            # 按类别统计
            category_stats = {}
            for error in self.error_log:
                category = error.category.value
                category_stats[category] = category_stats.get(category, 0) + 1
            
            # 按严重程度统计
            severity_stats = {}
            for error in self.error_log:
                severity = error.severity.value
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            # 最近24小时错误数
            recent_errors = sum(1 for error in self.error_log 
                              if datetime.now() - error.timestamp < timedelta(hours=24))
            
            # 已解决错误数
            resolved_errors = sum(1 for error in self.error_log if error.resolved)
            
            return {
                'total_errors': total_errors,
                'recent_errors_24h': recent_errors,
                'resolved_errors': resolved_errors,
                'unresolved_errors': total_errors - resolved_errors,
                'category_breakdown': category_stats,
                'severity_breakdown': severity_stats,
                'recovery_success_rate': resolved_errors / total_errors if total_errors > 0 else 0.0
            }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        with self.lock:
            recent_errors = sorted(
                self.error_log, 
                key=lambda x: x.timestamp, 
                reverse=True
            )[:limit]
            
            return [
                {
                    'error_id': error.error_id,
                    'timestamp': error.timestamp.isoformat(),
                    'severity': error.severity.value,
                    'category': error.category.value,
                    'message': error.message,
                    'resolved': error.resolved,
                    'recovery_attempts': error.recovery_attempts
                }
                for error in recent_errors
            ]
    
    def export_error_log(self, filepath: str):
        """导出错误日志"""
        try:
            with self.lock:
                error_data = [
                    {
                        'error_id': error.error_id,
                        'timestamp': error.timestamp.isoformat(),
                        'severity': error.severity.value,
                        'category': error.category.value,
                        'message': error.message,
                        'details': error.details,
                        'stack_trace': error.stack_trace,
                        'context': error.context,
                        'recovery_attempts': error.recovery_attempts,
                        'resolved': error.resolved,
                        'resolved_time': error.resolved_time.isoformat() if error.resolved_time else None
                    }
                    for error in self.error_log
                ]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"错误日志已导出到: {filepath}")
            
        except Exception as e:
            logger.error(f"导出错误日志失败: {e}")
            raise

def error_handler(severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = None,
                 context: ErrorContext = None,
                 retry_policy: str = None):
    """错误处理装饰器"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取错误处理器实例
            error_handler = getattr(func, '__error_handler__', None)
            if not error_handler:
                error_handler = AutomationErrorHandler()
                setattr(func, '__error_handler__', error_handler)
            
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                # 构建错误上下文
                error_context = context or ErrorContext()
                error_context.operation = func.__name__
                
                # 处理错误
                error_info = error_handler.handle_error(
                    e, 
                    context=error_context,
                    severity=severity,
                    category=category
                )
                
                # 如果需要重试，使用重试策略
                if retry_policy:
                    return error_handler.retry_with_policy(
                        func, 
                        policy_name=retry_policy,
                        context=error_context,
                        *args, 
                        **kwargs
                    )
                
                # 重新抛出异常
                raise
        
        return wrapper
    
    return decorator
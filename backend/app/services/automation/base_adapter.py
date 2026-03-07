#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件自动化适配器基类
定义所有软件适配器的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AutomationStatus(Enum):
    """自动化执行状态"""
    PENDING = "pending"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SETTING_PARAMETERS = "setting_parameters"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AutomationResult:
    """自动化执行结果"""
    success: bool
    status: AutomationStatus
    message: str
    parameters_set: Dict[str, Any]
    execution_time: float
    error_details: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SoftwareInfo:
    """软件信息"""
    name: str
    version: str
    is_running: bool
    connection_status: str
    supported_parameters: List[str]

class SoftwareAutomationAdapter(ABC):
    """软件自动化适配器基类"""
    
    def __init__(self, software_name: str, version: str = None):
        self.software_name = software_name
        self.version = version
        self.is_connected = False
        self.connection_timeout = 30  # 连接超时时间（秒）
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试延迟（秒）
        
    @abstractmethod
    def connect(self) -> bool:
        """
        连接目标软件
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        断开与目标软件的连接
        
        Returns:
            bool: 断开是否成功
        """
        pass
    
    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """
        批量设置参数
        
        Args:
            parameters: 参数字典，格式：{参数名: 参数值}
            
        Returns:
            AutomationResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_software_info(self) -> SoftwareInfo:
        """
        获取软件信息
        
        Returns:
            SoftwareInfo: 软件信息对象
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证参数的有效性
        
        Args:
            parameters: 待验证的参数
            
        Returns:
            Dict[str, Any]: 验证后的参数（可能包含修正）
        """
        pass
    
    def safe_connect(self) -> bool:
        """安全的连接方法，包含重试机制"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试连接 {self.software_name} (第{attempt + 1}次)")
                if self.connect():
                    self.is_connected = True
                    logger.info(f"成功连接到 {self.software_name}")
                    return True
            except Exception as e:
                logger.warning(f"连接失败 (第{attempt + 1}次): {e}")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.retry_delay)
        
        logger.error(f"无法连接到 {self.software_name}")
        return False
    
    def safe_disconnect(self) -> bool:
        """安全的断开连接方法"""
        try:
            result = self.disconnect()
            self.is_connected = False
            logger.info(f"成功断开与 {self.software_name} 的连接")
            return result
        except Exception as e:
            logger.error(f"断开连接时出错: {e}")
            return False
    
    def execute_automation(self, parameters: Dict[str, Any]) -> AutomationResult:
        """
        执行完整的自动化流程
        
        Args:
            parameters: 参数字典
            
        Returns:
            AutomationResult: 自动化执行结果
        """
        import time
        start_time = time.time()
        
        try:
            # 1. 验证参数
            validated_params = self.validate_parameters(parameters)
            
            # 2. 连接软件
            if not self.safe_connect():
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message=f"无法连接到 {self.software_name}",
                    parameters_set={},
                    execution_time=time.time() - start_time,
                    error_details="连接失败"
                )
            
            # 3. 设置参数
            result = self.set_parameters(validated_params)
            
            # 4. 断开连接
            self.safe_disconnect()
            
            return result
            
        except Exception as e:
            logger.error(f"自动化执行失败: {e}")
            self.safe_disconnect()
            
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"自动化执行失败: {str(e)}",
                parameters_set={},
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.safe_connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.safe_disconnect()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件自动化服务模块
实现文档解析参数到各类化工软件的自动填写功能
"""

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus
from .parameter_mapper import ParameterMapper
from .automation_engine import AutomationEngine, AutomationTask, TaskStatus
from .error_handler import AutomationErrorHandler, ErrorSeverity, ErrorCategory, RetryPolicy

__all__ = [
    'SoftwareAutomationAdapter',
    'AutomationResult', 
    'AspenPlusAdapter',
    'DWSIMAdapter',
    'AutoCADAdapter',
    'ExcelAdapter',
    'AutomationEngine',
    'ParameterMapper'
]
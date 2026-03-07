#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aspen Plus 自动化适配器
通过 COM 接口与 Aspen Plus 进行交互
"""

import win32com.client
import pythoncom
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

class AspenPlusAdapter(SoftwareAutomationAdapter):
    """Aspen Plus 自动化适配器"""
    
    def __init__(self, version: str = "V12.0"):
        super().__init__("Aspen Plus", version)
        self.aspen_app = None
        self.current_case = None
        self.connection_timeout = 60  # Aspen Plus 启动较慢
        
    def connect(self) -> bool:
        """连接 Aspen Plus"""
        try:
            logger.info("正在连接 Aspen Plus...")
            
            # 初始化 COM
            pythoncom.CoInitialize()
            
            # 创建 Aspen Plus 应用实例
            self.aspen_app = win32com.client.Dispatch("Apwn.Document")
            
            logger.info("成功连接到 Aspen Plus")
            return True
            
        except Exception as e:
            logger.error(f"连接 Aspen Plus 失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 Aspen Plus 的连接"""
        try:
            if self.aspen_app:
                # 关闭当前案例
                if self.current_case:
                    try:
                        self.current_case.Close()
                    except:
                        pass
                
                # 退出应用
                try:
                    self.aspen_app.Quit()
                except:
                    pass
                
                self.aspen_app = None
                self.current_case = None
                
            # 释放 COM
            pythoncom.CoUninitialize()
            
            logger.info("已断开与 Aspen Plus 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def open_case(self, case_path: str) -> bool:
        """打开 Aspen Plus 案例文件"""
        try:
            if not self.aspen_app:
                logger.error("未连接到 Aspen Plus")
                return False
            
            # 检查文件是否存在
            if not Path(case_path).exists():
                logger.error(f"案例文件不存在: {case_path}")
                return False
            
            logger.info(f"正在打开案例文件: {case_path}")
            
            # 打开案例
            self.current_case = self.aspen_app.Open(case_path)
            
            # 等待案例加载完成
            time.sleep(3)
            
            logger.info("案例文件打开成功")
            return True
            
        except Exception as e:
            logger.error(f"打开案例文件失败: {e}")
            return False
    
    def create_new_case(self, template: str = None) -> bool:
        """创建新案例"""
        try:
            if not self.aspen_app:
                logger.error("未连接到 Aspen Plus")
                return False
            
            logger.info("正在创建新案例...")
            
            # 创建新案例
            self.current_case = self.aspen_app.New()
            
            # 等待创建完成
            time.sleep(2)
            
            logger.info("新案例创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建新案例失败: {e}")
            return False
    
    def save_case(self, save_path: str) -> bool:
        """保存案例"""
        try:
            if not self.current_case:
                logger.error("没有打开的案例")
                return False
            
            logger.info(f"正在保存案例到: {save_path}")
            
            # 保存案例
            self.current_case.SaveAs(save_path)
            
            logger.info("案例保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存案例失败: {e}")
            return False
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置参数"""
        import time
        start_time = time.time()
        
        try:
            if not self.current_case:
                logger.error("没有打开的案例")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="没有打开的案例",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"开始设置 {len(parameters)} 个参数...")
            
            parameters_set = {}
            
            # 获取流程数据表
            data_table = self.current_case.Data.Tables
            
            for param_name, param_value in parameters.items():
                try:
                    # 根据参数名查找对应的 Aspen Plus 字段
                    aspen_field = self._find_aspen_field(param_name)
                    
                    if aspen_field:
                        # 设置参数值
                        self._set_parameter_value(aspen_field, param_value)
                        parameters_set[param_name] = param_value
                        logger.debug(f"设置参数成功: {param_name} = {param_value}")
                    else:
                        logger.warning(f"未找到对应的 Aspen Plus 字段: {param_name}")
                        
                except Exception as e:
                    logger.error(f"设置参数失败 {param_name}: {e}")
                    continue
            
            # 运行模拟（可选）
            if parameters_set:
                logger.info("参数设置完成，运行模拟...")
                self._run_simulation()
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message=f"成功设置 {len(parameters_set)} 个参数",
                parameters_set=parameters_set,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"设置参数失败: {str(e)}",
                parameters_set=parameters_set,
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def _find_aspen_field(self, param_name: str) -> Optional[str]:
        """查找 Aspen Plus 字段名"""
        # 参数映射表
        field_mappings = {
            'TEMP': ['temperature', 'temp', 'T'],
            'PRES': ['pressure', 'pres', 'P'],
            'FLOW': ['flow_rate', 'flow', 'F'],
            'COMPOSITION': ['composition', 'comp', 'x'],
            'REBOILER_DUTY': ['reboiler_duty', 'QR'],
            'CONDENSER_DUTY': ['condenser_duty', 'QC'],
            'REFLUX_RATIO': ['reflux_ratio', 'RR'],
            'NUMBER_STAGES': ['number_stages', 'NSTAGES']
        }
        
        # 查找匹配的字段
        for aspen_field, aliases in field_mappings.items():
            if param_name.upper() in [alias.upper() for alias in aliases]:
                return aspen_field
        
        # 如果没有找到，尝试直接使用参数名
        return param_name.upper()
    
    def _set_parameter_value(self, field_name: str, value: Any):
        """设置参数值"""
        try:
            # 获取数据表
            data_table = self.current_case.Data.Tables
            
            # 查找并设置参数
            # 这里需要根据具体的 Aspen Plus 对象模型进行调整
            # 以下是一个简化的示例
            
            # 尝试在物流表中设置
            try:
                streams = data_table.Item("STREAMS")
                if streams and field_name in str(streams):
                    # 设置物流参数
                    streams.SetValue(field_name, value)
                    return
            except:
                pass
            
            # 尝试在单元操作表中设置
            try:
                blocks = data_table.Item("BLOCKS")
                if blocks and field_name in str(blocks):
                    # 设置单元操作参数
                    blocks.SetValue(field_name, value)
                    return
            except:
                pass
            
            # 尝试直接通过路径设置
            try:
                self.current_case.SetValue(field_name, value)
            except:
                logger.warning(f"无法设置参数 {field_name} = {value}")
                
        except Exception as e:
            logger.error(f"设置参数值失败 {field_name}: {e}")
            raise
    
    def _run_simulation(self):
        """运行模拟"""
        try:
            logger.info("正在运行模拟...")
            
            # 运行模拟
            self.current_case.Run()
            
            # 等待模拟完成
            time.sleep(5)
            
            logger.info("模拟运行完成")
            
        except Exception as e:
            logger.error(f"运行模拟失败: {e}")
            # 不抛出异常，因为参数设置可能已经成功
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            is_running = self.aspen_app is not None
            connection_status = "已连接" if is_running else "未连接"
            
            # 获取支持的参数列表
            supported_params = [
                'temperature', 'pressure', 'flow_rate', 'composition',
                'reboiler_duty', 'condenser_duty', 'reflux_ratio', 'number_stages'
            ]
            
            return SoftwareInfo(
                name=self.software_name,
                version=self.version,
                is_running=is_running,
                connection_status=connection_status,
                supported_parameters=supported_params
            )
            
        except Exception as e:
            logger.error(f"获取软件信息失败: {e}")
            return SoftwareInfo(
                name=self.software_name,
                version=self.version,
                is_running=False,
                connection_status="错误",
                supported_parameters=[]
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated_params = {}
        
        for param_name, param_value in parameters.items():
            try:
                # 根据参数类型进行验证
                if param_name.lower() in ['temperature', 'temp']:
                    # 温度验证：-273.15 到 1000 °C
                    temp_val = float(param_value)
                    if -273.15 <= temp_val <= 1000:
                        validated_params[param_name] = temp_val
                    else:
                        logger.warning(f"温度参数超出范围: {temp_val}")
                        
                elif param_name.lower() in ['pressure', 'pres']:
                    # 压力验证：0.001 到 1000 bar
                    pres_val = float(param_value)
                    if 0.001 <= pres_val <= 1000:
                        validated_params[param_name] = pres_val
                    else:
                        logger.warning(f"压力参数超出范围: {pres_val}")
                        
                elif param_name.lower() in ['flow_rate', 'flow']:
                    # 流量验证：正数
                    flow_val = float(param_value)
                    if flow_val > 0:
                        validated_params[param_name] = flow_val
                    else:
                        logger.warning(f"流量参数必须为正数: {flow_val}")
                        
                else:
                    # 其他参数直接通过
                    validated_params[param_name] = param_value
                    
            except (ValueError, TypeError) as e:
                logger.error(f"参数验证失败 {param_name}: {e}")
                continue
        
        return validated_params
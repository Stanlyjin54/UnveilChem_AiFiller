#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRO/II 自动化适配器
通过 COM 接口与 PRO/II 进行交互
"""

import win32com.client
import pythoncom
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

class PROIIAdapter(SoftwareAutomationAdapter):
    """PRO/II 自动化适配器"""
    
    def __init__(self, version: str = "10.2"):
        super().__init__("PRO/II", version)
        self.pro2_app = None
        self.current_case = None
        self.connection_timeout = 45  # PRO/II 启动时间适中
        
    def connect(self) -> bool:
        """连接 PRO/II"""
        try:
            logger.info("正在连接 PRO/II...")
            
            # 初始化 COM
            pythoncom.CoInitialize()
            
            # 创建 PRO/II 应用实例
            # PRO/II 的 COM 接口名称可能因版本而异
            try:
                self.pro2_app = win32com.client.Dispatch("PROII.Application")
            except:
                # 尝试其他可能的 COM 接口名称
                try:
                    self.pro2_app = win32com.client.Dispatch("SimSci.PROII")
                except:
                    self.pro2_app = win32com.client.Dispatch("PROII.Application.1")
            
            logger.info("成功连接到 PRO/II")
            return True
            
        except Exception as e:
            logger.error(f"连接 PRO/II 失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 PRO/II 的连接"""
        try:
            if self.pro2_app:
                # 关闭当前案例
                if self.current_case:
                    try:
                        self.current_case.Close()
                    except:
                        pass
                
                # 退出应用
                try:
                    self.pro2_app.Quit()
                except:
                    pass
                
                self.pro2_app = None
                self.current_case = None
                
            # 释放 COM
            pythoncom.CoUninitialize()
            
            logger.info("已断开与 PRO/II 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def open_case(self, case_path: str) -> bool:
        """打开 PRO/II 案例文件"""
        try:
            if not self.pro2_app:
                logger.error("未连接到 PRO/II")
                return False
            
            # 检查文件是否存在
            if not Path(case_path).exists():
                logger.error(f"案例文件不存在: {case_path}")
                return False
            
            logger.info(f"正在打开案例文件: {case_path}")
            
            # 打开案例
            self.current_case = self.pro2_app.Open(case_path)
            
            # 等待案例加载完成
            time.sleep(2)
            
            logger.info("案例文件打开成功")
            return True
            
        except Exception as e:
            logger.error(f"打开案例文件失败: {e}")
            return False
    
    def create_new_case(self, template: str = None) -> bool:
        """创建新案例"""
        try:
            if not self.pro2_app:
                logger.error("未连接到 PRO/II")
                return False
            
            logger.info("正在创建新案例...")
            
            # 创建新案例
            self.current_case = self.pro2_app.New()
            
            # 等待创建完成
            time.sleep(1)
            
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
            
            # PRO/II 的参数设置方式
            # 获取流程数据表或单元操作
            try:
                # 尝试获取流程数据
                flowsheet = self.current_case.Flowsheet
                
                for param_name, param_value in parameters.items():
                    try:
                        # 根据参数名查找对应的 PRO/II 字段
                        pro2_field = self._find_pro2_field(param_name)
                        
                        if pro2_field:
                            # 设置参数值
                            self._set_parameter_value(pro2_field, param_value)
                            parameters_set[param_name] = param_value
                            logger.debug(f"设置参数成功: {param_name} = {param_value}")
                        else:
                            logger.warning(f"未找到对应的 PRO/II 字段: {param_name}")
                            
                    except Exception as e:
                        logger.error(f"设置参数失败 {param_name}: {e}")
                        continue
                        
            except AttributeError:
                logger.warning("无法访问 Flowsheet，尝试其他方法")
                # 尝试直接设置参数
                for param_name, param_value in parameters.items():
                    try:
                        # 直接通过案例对象设置参数
                        if hasattr(self.current_case, param_name):
                            setattr(self.current_case, param_name, param_value)
                            parameters_set[param_name] = param_value
                            logger.debug(f"设置参数成功: {param_name} = {param_value}")
                        else:
                            logger.warning(f"PRO/II 案例对象没有属性: {param_name}")
                            
                    except Exception as e:
                        logger.error(f"设置参数失败 {param_name}: {e}")
                        continue
            
            # 运行计算（可选）
            if parameters_set:
                logger.info("参数设置完成，运行计算...")
                self._run_calculation()
            
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
                parameters_set={},
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def _find_pro2_field(self, param_name: str) -> Optional[str]:
        """查找 PRO/II 参数字段"""
        # PRO/II 参数字段映射
        pro2_field_map = {
            "TEMP": "Temperature",
            "PRES": "Pressure", 
            "FLOW": "Flowrate",
            "COMP": "Composition",
            "REFLUX": "RefluxRatio",
            "STAGES": "NumberOfStages"
        }
        
        return pro2_field_map.get(param_name.upper())
    
    def _set_parameter_value(self, field_name: str, value: Any) -> bool:
        """设置参数值"""
        try:
            # 尝试通过流程表设置
            if hasattr(self.current_case, 'Flowsheet'):
                flowsheet = self.current_case.Flowsheet
                if hasattr(flowsheet, field_name):
                    setattr(flowsheet, field_name, value)
                    return True
            
            # 尝试直接设置到案例
            if hasattr(self.current_case, field_name):
                setattr(self.current_case, field_name, value)
                return True
                
            logger.warning(f"无法找到字段: {field_name}")
            return False
            
        except Exception as e:
            logger.error(f"设置字段值失败 {field_name}: {e}")
            return False
    
    def _run_calculation(self) -> bool:
        """运行计算"""
        try:
            logger.info("开始运行 PRO/II 计算...")
            
            # 尝试运行计算
            if hasattr(self.current_case, 'RunCalculation'):
                self.current_case.RunCalculation()
            elif hasattr(self.current_case, 'Calculate'):
                self.current_case.Calculate()
            else:
                logger.warning("无法找到计算方法，可能需要手动运行")
                return False
            
            # 等待计算完成
            time.sleep(3)
            
            logger.info("PRO/II 计算完成")
            return True
            
        except Exception as e:
            logger.error(f"运行计算失败: {e}")
            return False
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            is_running = self.pro2_app is not None
            connection_status = "已连接" if is_running else "未连接"
            
            # PRO/II 支持的参数
            supported_params = [
                "temperature", "pressure", "flow_rate", "composition",
                "reflux_ratio", "stages"
            ]
            
            return SoftwareInfo(
                name="PRO/II",
                version=self.version,
                is_running=is_running,
                connection_status=connection_status,
                supported_parameters=supported_params
            )
            
        except Exception as e:
            logger.error(f"获取软件信息失败: {e}")
            return SoftwareInfo(
                name="PRO/II",
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
                # 基本验证
                if param_name in ["temperature", "pressure", "flow_rate", "composition", "reflux_ratio", "stages"]:
                    # 数值验证
                    if isinstance(param_value, (int, float)):
                        if param_name == "temperature" and param_value < -273.15:
                            logger.warning(f"温度值过低: {param_value}")
                            continue
                        elif param_name == "pressure" and param_value < 0:
                            logger.warning(f"压力值为负: {param_value}")
                            continue
                        elif param_name == "flow_rate" and param_value < 0:
                            logger.warning(f"流量值为负: {param_value}")
                            continue
                        elif param_name == "reflux_ratio" and param_value < 0:
                            logger.warning(f"回流比为负: {param_value}")
                            continue
                        elif param_name == "stages" and (param_value < 1 or param_value > 200):
                            logger.warning(f"塔板数超出范围: {param_value}")
                            continue
                        
                        validated_params[param_name] = param_value
                        
                    elif param_name == "composition" and isinstance(param_value, dict):
                        # 组成验证
                        valid_composition = True
                        for comp, value in param_value.items():
                            if not (0 <= value <= 1):
                                logger.warning(f"组成值超出范围: {comp} = {value}")
                                valid_composition = False
                                break
                        
                        if valid_composition:
                            validated_params[param_name] = param_value
                            
                else:
                    # 未知参数，记录警告但保留
                    logger.warning(f"未知参数: {param_name}")
                    validated_params[param_name] = param_value
                    
            except Exception as e:
                logger.error(f"参数验证失败 {param_name}: {e}")
                continue
        
        return validated_params
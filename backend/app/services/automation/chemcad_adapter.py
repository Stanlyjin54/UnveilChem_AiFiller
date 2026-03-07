#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChemCAD自动化适配器
通过COM接口连接ChemCAD,实现参数设置和仿真运行
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus
from .parameter_mapper import ParameterMapper

logger = logging.getLogger(__name__)

try:
    import win32com.client
    import pythoncom
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    logger.warning("win32com 不可用,ChemCAD适配器功能受限")

@dataclass
class ChemCADParameter:
    """ChemCAD参数定义"""
    name: str
    value: Any
    unit: str
    description: str
    location: str  # 在ChemCAD中的位置路径

class ChemCADAdapter(SoftwareAutomationAdapter):
    """ChemCAD自动化适配器"""
    
    def __init__(self):
        super().__init__()
        self.parameter_mapper = ParameterMapper()
        self.cc = None  # ChemCAD应用实例
        self.simulation_case = None
        self.is_connected = False
        
        # ChemCAD参数映射表
        self.chemcad_parameter_map = {
            # 温度参数
            'temperature': {
                'reactor_temp': 'CCUnitOp.Temperature',
                'distill_temp': 'CCDistillation.Temperature',
                'flash_temp': 'CCFlash.Temperature',
                'heat_temp': 'CCHeatExchanger.Temperature'
            },
            # 压力参数
            'pressure': {
                'reactor_pressure': 'CCUnitOp.Pressure',
                'distill_pressure': 'CCDistillation.Pressure',
                'flash_pressure': 'CCFlash.Pressure',
                'pump_pressure': 'CCPump.Pressure'
            },
            # 流量参数
            'flow_rate': {
                'feed_flow': 'CCStream.FlowRate',
                'product_flow': 'CCProduct.FlowRate',
                'reflux_flow': 'CCReflux.FlowRate'
            },
            # 组分参数
            'composition': {
                'feed_composition': 'CCStream.Composition',
                'product_composition': 'CCProduct.Composition'
            },
            # 设备参数
            'equipment': {
                'reactor_volume': 'CCReactor.Volume',
                'column_stages': 'CCDistillation.Stages',
                'column_diameter': 'CCDistillation.Diameter',
                'heat_area': 'CCHeatExchanger.Area'
            }
        }
    
    def connect(self, **kwargs) -> bool:
        """连接到ChemCAD"""
        try:
            if not COM_AVAILABLE:
                raise RuntimeError("COM接口不可用，无法连接ChemCAD")
            
            logger.info("正在连接到ChemCAD...")
            
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 创建ChemCAD应用实例
            self.cc = win32com.client.Dispatch("ChemCAD.Application")
            
            # 验证连接
            if self.cc is None:
                raise RuntimeError("无法创建ChemCAD应用实例")
            
            self.is_connected = True
            logger.info("成功连接到ChemCAD")
            return True
            
        except Exception as e:
            logger.error(f"连接ChemCAD失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """断开ChemCAD连接"""
        try:
            if self.cc:
                # 关闭仿真案例
                if self.simulation_case:
                    try:
                        self.simulation_case.Close()
                    except:
                        pass
                
                # 退出ChemCAD
                try:
                    self.cc.Quit()
                except:
                    pass
                
                self.cc = None
                self.simulation_case = None
            
            self.is_connected = False
            logger.info("已断开ChemCAD连接")
            return True
            
        except Exception as e:
            logger.error(f"断开ChemCAD连接失败: {e}")
            return False
    
    def open_case(self, case_path: str) -> bool:
        """打开仿真案例"""
        try:
            if not self.is_connected:
                raise RuntimeError("未连接到ChemCAD")
            
            logger.info(f"正在打开ChemCAD案例: {case_path}")
            
            # 打开案例文件
            self.simulation_case = self.cc.OpenDocument(case_path)
            
            if self.simulation_case is None:
                raise RuntimeError("无法打开ChemCAD案例文件")
            
            logger.info("成功打开ChemCAD案例")
            return True
            
        except Exception as e:
            logger.error(f"打开ChemCAD案例失败: {e}")
            return False
    
    def create_new_case(self, template: str = "Default") -> bool:
        """创建新案例"""
        try:
            if not self.is_connected:
                raise RuntimeError("未连接到ChemCAD")
            
            logger.info(f"正在创建新ChemCAD案例 (模板: {template})")
            
            # 创建新案例
            self.simulation_case = self.cc.NewDocument(template)
            
            if self.simulation_case is None:
                raise RuntimeError("无法创建新ChemCAD案例")
            
            logger.info("成功创建新ChemCAD案例")
            return True
            
        except Exception as e:
            logger.error(f"创建新ChemCAD案例失败: {e}")
            return False
    
    def save_case(self, case_path: str) -> bool:
        """保存案例"""
        try:
            if not self.simulation_case:
                raise RuntimeError("没有打开的案例")
            
            logger.info(f"正在保存ChemCAD案例: {case_path}")
            
            # 保存案例
            self.simulation_case.SaveAs(case_path)
            
            logger.info("成功保存ChemCAD案例")
            return True
            
        except Exception as e:
            logger.error(f"保存ChemCAD案例失败: {e}")
            return False
    
    def set_parameter(self, param_path: str, value: Any, unit: str = None) -> bool:
        """设置参数"""
        try:
            if not self.simulation_case:
                raise RuntimeError("没有打开的案例")
            
            logger.info(f"正在设置ChemCAD参数: {param_path} = {value} {unit or ''}")
            
            # 解析参数路径
            path_parts = param_path.split('.')
            current_obj = self.simulation_case
            
            # 遍历路径获取参数对象
            for part in path_parts[:-1]:
                current_obj = getattr(current_obj, part, None)
                if current_obj is None:
                    raise ValueError(f"无效的参数路径: {param_path}")
            
            # 设置参数值
            param_name = path_parts[-1]
            setattr(current_obj, param_name, value)
            
            logger.info(f"成功设置ChemCAD参数: {param_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置ChemCAD参数失败: {e}")
            return False
    
    def get_parameter(self, param_path: str) -> Optional[Any]:
        """获取参数值"""
        try:
            if not self.simulation_case:
                raise RuntimeError("没有打开的案例")
            
            # 解析参数路径
            path_parts = param_path.split('.')
            current_obj = self.simulation_case
            
            # 遍历路径获取参数对象
            for part in path_parts[:-1]:
                current_obj = getattr(current_obj, part, None)
                if current_obj is None:
                    return None
            
            # 获取参数值
            param_name = path_parts[-1]
            return getattr(current_obj, param_name, None)
            
        except Exception as e:
            logger.error(f"获取ChemCAD参数失败: {e}")
            return None
    
    def run_simulation(self) -> bool:
        """运行仿真"""
        try:
            if not self.simulation_case:
                raise RuntimeError("没有打开的案例")
            
            logger.info("正在运行ChemCAD仿真...")
            
            # 运行仿真
            result = self.simulation_case.RunSimulation()
            
            if not result:
                raise RuntimeError("ChemCAD仿真运行失败")
            
            logger.info("ChemCAD仿真运行成功")
            return True
            
        except Exception as e:
            logger.error(f"运行ChemCAD仿真失败: {e}")
            return False
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, bool]:
        """验证参数"""
        validation_results = {}
        
        for param_name, param_value in parameters.items():
            try:
                # 查找参数映射
                mapped_param = self._find_parameter_mapping(param_name)
                
                if not mapped_param:
                    validation_results[param_name] = False
                    logger.warning(f"未找到参数映射: {param_name}")
                    continue
                
                # 验证参数类型和范围
                is_valid = self._validate_single_parameter(mapped_param, param_value)
                validation_results[param_name] = is_valid
                
                if not is_valid:
                    logger.warning(f"参数验证失败: {param_name} = {param_value}")
                
            except Exception as e:
                validation_results[param_name] = False
                logger.error(f"验证参数 {param_name} 时出错: {e}")
        
        return validation_results
    
    def _find_parameter_mapping(self, param_name: str) -> Optional[str]:
        """查找参数映射"""
        # 首先尝试直接映射
        for category, mappings in self.chemcad_parameter_map.items():
            if param_name in mappings:
                return mappings[param_name]
        
        # 使用参数映射器进行智能映射
        mapped_params = self.parameter_mapper.map_parameters(
            {param_name: None}, "chemcad"
        )
        
        if mapped_params and param_name in mapped_params:
            return mapped_params[param_name]
        
        return None
    
    def _validate_single_parameter(self, param_path: str, value: Any) -> bool:
        """验证单个参数"""
        try:
            # 基于参数路径的验证规则
            if 'Temperature' in param_path:
                # 温度范围验证 (K)
                return 200 <= float(value) <= 1000
            elif 'Pressure' in param_path:
                # 压力范围验证 (Pa)
                return 1000 <= float(value) <= 10000000
            elif 'FlowRate' in param_path:
                # 流量范围验证 (kg/s)
                return 0.01 <= float(value) <= 1000
            elif 'Composition' in param_path:
                # 组分验证 (摩尔分数)
                return 0 <= float(value) <= 1
            elif 'Volume' in param_path:
                # 体积验证 (m³)
                return 0.1 <= float(value) <= 1000
            elif 'Stages' in param_path:
                # 塔板数验证
                return 2 <= int(value) <= 100
            elif 'Diameter' in param_path:
                # 直径验证 (m)
                return 0.1 <= float(value) <= 10
            elif 'Area' in param_path:
                # 面积验证 (m²)
                return 1 <= float(value) <= 1000
            else:
                # 默认验证通过
                return True
                
        except (ValueError, TypeError):
            return False
    
    def get_software_info(self) -> Dict[str, Any]:
        """获取软件信息"""
        try:
            if not self.is_connected:
                return {
                    "name": "ChemCAD",
                    "version": "Unknown",
                    "connected": False,
                    "case_loaded": False
                }
            
            # 获取版本信息
            version = getattr(self.cc, 'Version', 'Unknown')
            
            return {
                "name": "ChemCAD",
                "version": version,
                "connected": True,
                "case_loaded": self.simulation_case is not None,
                "case_path": getattr(self.simulation_case, 'Path', None) if self.simulation_case else None
            }
            
        except Exception as e:
            logger.error(f"获取ChemCAD信息失败: {e}")
            return {
                "name": "ChemCAD",
                "version": "Unknown",
                "connected": self.is_connected,
                "case_loaded": self.simulation_case is not None,
                "error": str(e)
            }
    
    def execute_automation(self, parameters: Dict[str, Any]) -> AutomationResult:
        """执行自动化流程"""
        start_time = time.time()
        
        try:
            logger.info("开始执行ChemCAD自动化流程")
            
            # 验证参数
            validation_results = self.validate_parameters(parameters)
            if not all(validation_results.values()):
                invalid_params = [k for k, v in validation_results.items() if not v]
                raise ValueError(f"参数验证失败: {invalid_params}")
            
            # 参数映射
            mapped_parameters = self.parameter_mapper.map_parameters(
                parameters, "chemcad"
            )
            
            if not mapped_parameters:
                raise ValueError("参数映射失败")
            
            # 设置参数
            parameters_set = {}
            for param_name, param_value in mapped_parameters.items():
                # 查找ChemCAD参数路径
                param_path = self._find_parameter_mapping(param_name)
                
                if param_path:
                    if self.set_parameter(param_path, param_value):
                        parameters_set[param_name] = param_value
                        logger.info(f"设置参数成功: {param_name} = {param_value}")
                    else:
                        logger.warning(f"设置参数失败: {param_name}")
            
            # 运行仿真
            simulation_success = self.run_simulation()
            
            if not simulation_success:
                raise RuntimeError("ChemCAD仿真运行失败")
            
            execution_time = time.time() - start_time
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message="ChemCAD自动化执行成功",
                parameters_set=parameters_set,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"ChemCAD自动化执行失败: {e}")
            
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"ChemCAD自动化执行失败: {str(e)}",
                parameters_set={},
                execution_time=execution_time,
                error_details=str(e)
            )
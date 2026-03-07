#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWSIM COM 自动化适配器
通过 COM 接口与 DWSIM 进行交互，用于化工流程仿真
"""

import sys
import os
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

@dataclass
class StreamData:
    """物料流数据"""
    name: str
    temperature: float = 298.15
    pressure: float = 101325
    molar_flow: float = 100
    composition: List[float] = field(default_factory=list)
    compounds: List[str] = field(default_factory=list)

@dataclass
class EquipmentData:
    """设备数据"""
    name: str
    equipment_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SimulationResult:
    """仿真结果"""
    success: bool
    message: str
    streams: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    equipment: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    execution_time: float = 0

class DWSIMCOMAdapter(SoftwareAutomationAdapter):
    """DWSIM COM 自动化适配器"""
    
    def __init__(self, dwsim_path: str = None):
        super().__init__("DWSIM", "9.0")
        
        # DWSIM 安装路径
        if dwsim_path:
            self.dwsim_path = dwsim_path
        else:
            # 默认路径
            self.dwsim_path = r"C:\Users\54905\AppData\Local\DWSIM"
        
        # COM 对象
        self.dwsim = None
        self.flowsheet = None
        
        # 仿真数据
        self.compounds = []
        self.streams = {}
        self.equipment = {}
        
        # 初始化 Python.NET
        self._init_pythonnet()
        
    def _init_pythonnet(self):
        """初始化 Python.NET"""
        try:
            import clr
            self.clr = clr
            
            # 添加 DWSIM 路径到 Python 路径
            if self.dwsim_path not in sys.path:
                sys.path.insert(0, self.dwsim_path)
            
            # 加载 DWSIM 程序集
            self.clr.AddReference(os.path.join(self.dwsim_path, "DWSIM.Automation"))
            self.clr.AddReference(os.path.join(self.dwsim_path, "DWSIM.Interfaces"))
            
            # 导入 DWSIM 类
            from DWSIM.Automation import Automation3
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType
            
            self.Automation3 = Automation3
            self.ObjectType = ObjectType
            
            logger.info("Python.NET 初始化成功")
            
        except Exception as e:
            logger.error(f"Python.NET 初始化失败: {e}")
            raise
    
    def connect(self) -> bool:
        """连接 DWSIM"""
        try:
            logger.info("正在连接 DWSIM...")
            
            # 创建 DWSIM 自动化实例
            self.dwsim = self.Automation3()
            
            # 创建流程
            self.flowsheet = self.dwsim.CreateFlowsheet()
            
            logger.info("成功连接到 DWSIM")
            return True
            
        except Exception as e:
            logger.error(f"连接 DWSIM 失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 DWSIM 的连接"""
        try:
            if self.dwsim:
                # 释放资源
                self.dwsim.ReleaseResources()
                self.dwsim = None
                self.flowsheet = None
            
            logger.info("已断开与 DWSIM 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置仿真参数并运行仿真"""
        import time
        start_time = time.time()
        
        try:
            if not self.flowsheet:
                logger.error("未连接到 DWSIM")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="未连接到 DWSIM",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"开始设置仿真参数...")
            
            # 1. 添加化合物
            compounds = parameters.get("compounds", [])
            for compound in compounds:
                self.flowsheet.AddCompound(compound)
            self.compounds = compounds
            logger.info(f"添加了 {len(compounds)} 个化合物")
            
            # 2. 添加物性包
            property_package = parameters.get("property_package", "Peng-Robinson (PR)")
            pp = self.flowsheet.CreatePropertyPackage(property_package)
            self.flowsheet.AddPropertyPackage(pp)
            logger.info(f"添加物性包: {property_package}")
            
            # 3. 添加物料流
            streams = parameters.get("streams", [])
            for stream_data in streams:
                self._add_stream(stream_data)
            logger.info(f"添加了 {len(streams)} 个物料流")
            
            # 4. 添加设备
            equipment = parameters.get("equipment", [])
            for equip_data in equipment:
                self._add_equipment(equip_data)
            logger.info(f"添加了 {len(equipment)} 个设备")
            
            # 5. 连接物流
            connections = parameters.get("connections", [])
            for conn in connections:
                self._connect_streams(conn)
            logger.info(f"连接了 {len(connections)} 个物流")
            
            # 6. 运行仿真
            logger.info("开始运行仿真...")
            exceptions = self.dwsim.CalculateFlowsheet2(self.flowsheet)
            
            if exceptions and len(exceptions) > 0:
                logger.warning(f"仿真有警告: {exceptions}")
            else:
                logger.info("仿真运行成功")
            
            # 7. 获取结果
            results = self._get_results()
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message=f"仿真完成，处理了 {len(streams)} 个物料流和 {len(equipment)} 个设备",
                parameters_set=parameters,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"设置参数失败: {str(e)}",
                parameters_set={},
                execution_time=time.time() - start_time
            )
    
    def _add_stream(self, stream_data: Dict[str, Any]):
        """添加物料流"""
        name = stream_data.get("name", f"Stream_{len(self.streams) + 1}")
        
        # 创建物料流对象
        stream = self.flowsheet.AddObject(self.ObjectType.MaterialStream, 100, 100 + len(self.streams) * 50, name)
        
        # 设置参数
        if "temperature" in stream_data:
            stream.SetPropertyValue("Temperature", stream_data["temperature"])
        if "pressure" in stream_data:
            stream.SetPropertyValue("Pressure", stream_data["pressure"])
        if "molar_flow" in stream_data:
            stream.SetPropertyValue("MolarFlow", stream_data["molar_flow"])
        if "composition" in stream_data:
            stream.SetPropertyValue("MolarComposition", stream_data["composition"])
        
        self.streams[name] = stream
        return stream
    
    def _add_equipment(self, equip_data: Dict[str, Any]):
        """添加设备"""
        name = equip_data.get("name", f"Equipment_{len(self.equipment) + 1}")
        equip_type = equip_data.get("type", "Heater")
        
        # 根据设备类型创建对象
        if equip_type == "Heater":
            equipment = self.flowsheet.AddObject(self.ObjectType.Heater, 300, 100 + len(self.equipment) * 50, name)
        elif equip_type == "Cooler":
            equipment = self.flowsheet.AddObject(self.ObjectType.Cooler, 300, 100 + len(self.equipment) * 50, name)
        elif equip_type == "Mixer":
            equipment = self.flowsheet.AddObject(self.ObjectType.Mixer, 300, 100 + len(self.equipment) * 50, name)
        elif equip_type == "Splitter":
            equipment = self.flowsheet.AddObject(self.ObjectType.Splitter, 300, 100 + len(self.equipment) * 50, name)
        else:
            # 默认使用 Heater
            equipment = self.flowsheet.AddObject(self.ObjectType.Heater, 300, 100 + len(self.equipment) * 50, name)
        
        # 设置设备参数
        for param_name, param_value in equip_data.get("parameters", {}).items():
            try:
                equipment.SetPropertyValue(param_name, param_value)
            except Exception as e:
                logger.warning(f"设置设备参数 {param_name} 失败: {e}")
        
        self.equipment[name] = equipment
        return equipment
    
    def _connect_streams(self, conn: Dict[str, Any]):
        """连接物流"""
        from_obj = self.streams.get(conn.get("from"))
        to_obj = self.equipment.get(conn.get("to"))
        
        if from_obj and to_obj:
            self.flowsheet.ConnectObjects(from_obj.GraphicObject, to_obj.GraphicObject, 0, 0)
            logger.info(f"连接: {conn.get('from')} -> {conn.get('to')}")
    
    def _get_results(self) -> SimulationResult:
        """获取仿真结果"""
        start_time = time.time()
        
        results = {
            "streams": {},
            "equipment": {}
        }
        
        # 获取物料流结果
        for name, stream in self.streams.items():
            try:
                results["streams"][name] = {
                    "temperature": stream.GetPropertyValue("Temperature"),
                    "pressure": stream.GetPropertyValue("Pressure"),
                    "molar_flow": stream.GetPropertyValue("MolarFlow")
                }
            except Exception as e:
                logger.warning(f"获取物料流 {name} 结果失败: {e}")
        
        # 获取设备结果
        for name, equip in self.equipment.items():
            try:
                results["equipment"][name] = {
                    "type": type(equip).__name__
                }
            except Exception as e:
                logger.warning(f"获取设备 {name} 结果失败: {e}")
        
        return SimulationResult(
            success=True,
            message="仿真完成",
            streams=results["streams"],
            equipment=results["equipment"],
            execution_time=time.time() - start_time
        )
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            version = self.dwsim.GetVersion() if self.dwsim else "Unknown"
            
            return SoftwareInfo(
                name="DWSIM",
                version=version,
                is_connected=self.is_connected,
                connection_status="connected" if self.is_connected else "disconnected",
                supported_parameters=[
                    "compounds",
                    "property_package",
                    "streams",
                    "equipment",
                    "connections"
                ]
            )
        except Exception as e:
            logger.error(f"获取软件信息失败: {e}")
            return SoftwareInfo(
                name="DWSIM",
                version="Unknown",
                is_connected=False,
                connection_status="error",
                supported_parameters=[]
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数有效性"""
        validated = parameters.copy()
        
        # 验证化合物
        if "compounds" not in validated or not validated["compounds"]:
            validated["compounds"] = ["Water", "Ethanol"]
        
        # 验证物性包
        if "property_package" not in validated:
            validated["property_package"] = "Peng-Robinson (PR)"
        
        # 验证物料流
        if "streams" not in validated:
            validated["streams"] = [{
                "name": "Feed",
                "temperature": 298.15,
                "pressure": 101325,
                "molar_flow": 100,
                "composition": [0.5, 0.5]
            }]
        
        return validated
    
    def run_simulation(self, parameters: Dict[str, Any]) -> SimulationResult:
        """运行仿真（便捷方法）"""
        try:
            # 连接
            if not self.safe_connect():
                return SimulationResult(
                    success=False,
                    message="无法连接到 DWSIM",
                    execution_time=0
                )
            
            # 设置参数并运行
            result = self.set_parameters(parameters)
            
            # 断开连接
            self.safe_disconnect()
            
            if result.success:
                # 获取详细结果
                sim_results = self._get_results()
                return sim_results
            else:
                return SimulationResult(
                    success=False,
                    message=result.message,
                    execution_time=result.execution_time
                )
                
        except Exception as e:
            logger.error(f"运行仿真失败: {e}")
            self.safe_disconnect()
            return SimulationResult(
                success=False,
                message=f"运行仿真失败: {str(e)}",
                execution_time=0
            )

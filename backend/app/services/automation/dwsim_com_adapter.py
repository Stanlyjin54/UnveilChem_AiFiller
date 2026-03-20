#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWSIM COM 自动化适配器 - 完整版
通过 COM/pythonnet 接口与 DWSIM 进行交互，实现完整的化工流程仿真自动化

支持功能:
- 流程图创建与管理
- 化合物与物性包管理
- 单元操作添加与配置
- 物料流创建与连接
- 仿真计算与结果获取
- 反应管理
- 灵敏度分析与优化
"""

import sys
import os
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """DWSIM 对象类型枚举"""
    MATERIAL_STREAM = 0
    PUMP = 1
    COMPRESSOR = 2
    HEATER = 3
    COOLER = 4
    VALVE = 5
    MIXER = 6
    SPLITTER = 7
    HEAT_EXCHANGER = 8
    REACTOR = 9
    DISTILLATION_COLUMN = 10
    ABSORPTION_COLUMN = 11
    TANK = 14
    SHORTCUT_COLUMN = 22
    FLASH_DRUM = 23


@dataclass
class StreamData:
    """物料流数据"""
    name: str
    temperature: float = 298.15
    pressure: float = 101325
    molar_flow: float = 100
    mass_flow: float = 0
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
    """
    DWSIM COM 自动化适配器 - 完整版
    
    通过 pythonnet 与 DWSIM.Automation.Automation3 接口交互
    支持完整的流程仿真自动化能力
    """
    
    # 默认物性包列表
    PROPERTY_PACKAGES = [
        "Peng-Robinson (PR)",
        "Soave-Redlich-Kwong (SRK)",
        "NRTL",
        "UNIQUAC",
        "UNIFAC",
        "Wilson",
        "CoolProp",
        "Steam Tables (IAPWS-IF97)",
        "Ideal Solution (Aqueous Electrolytes)",
        "Black Oil"
    ]
    
    def __init__(self, dwsim_path: str = None):
        super().__init__("DWSIM", "9.0")
        
        # DWSIM 安装路径
        if dwsim_path:
            self.dwsim_path = dwsim_path
        else:
            self.dwsim_path = self._find_dwsim_path()
        
        # COM 对象
        self.dwsim = None
        self.flowsheet = None
        
        # 仿真数据缓存
        self.compounds: List[str] = []
        self.streams: Dict[str, Any] = {}
        self.equipment: Dict[str, Any] = {}
        self.property_packages: List[str] = []
        
        # 初始化 Python.NET
        self._init_pythonnet()
        
    def _find_dwsim_path(self) -> str:
        """查找 DWSIM 安装路径"""
        user_profile = os.environ.get('USERPROFILE', '')
        
        possible_paths = [
            os.path.join(user_profile, r"AppData\Local\DWSIM"),
            r"C:\Program Files\DWSIM",
            r"C:\Program Files (x86)\DWSIM",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                automation_dll = os.path.join(path, "DWSIM.Automation.dll")
                if os.path.exists(automation_dll):
                    logger.info(f"找到 DWSIM 安装路径: {path}")
                    return path
        
        logger.warning("未找到 DWSIM 安装路径，使用默认路径")
        return os.path.join(user_profile, r"AppData\Local\DWSIM")
        
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
            from DWSIM.Interfaces.Enums.GraphicObjects import ObjectType as DWSIMObjectType
            
            self.Automation3 = Automation3
            self.DWSIMObjectType = DWSIMObjectType
            
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
            
            logger.info("成功连接到 DWSIM")
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"连接 DWSIM 失败: {e}")
            self.is_connected = False
            return False
    
    def safe_connect(self, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
        """
        安全连接 DWSIM，带重试机制
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        
        Returns:
            bool: 连接是否成功
        """
        if self.is_connected and self.dwsim is not None:
            return True
        
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试连接 DWSIM (第 {attempt + 1}/{max_retries} 次)...")
                
                if self.connect():
                    logger.info("DWSIM 连接成功")
                    return True
                
                if attempt < max_retries - 1:
                    logger.warning(f"连接失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                logger.error(f"连接尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error(f"DWSIM 连接失败，已尝试 {max_retries} 次")
        self.is_connected = False
        return False
    
    def ensure_flowsheet(self) -> bool:
        """
        确保有可用的流程图
        
        Returns:
            bool: 是否有可用的流程图
        """
        if self.flowsheet is not None:
            return True
        
        if not self.safe_connect():
            return False
        
        try:
            self.flowsheet = self.create_flowsheet()
            return self.flowsheet is not None
        except Exception as e:
            logger.error(f"创建流程图失败: {e}")
            return False
    
    def reset_connection(self) -> bool:
        """
        重置连接状态
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self.disconnect()
            time.sleep(0.5)
            return self.safe_connect()
        except Exception as e:
            logger.error(f"重置连接失败: {e}")
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
            self.is_connected = False
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    # ==================== 流程图管理 ====================
    
    def create_flowsheet(self, name: str = None) -> Any:
        """创建新的流程图"""
        try:
            if not self.dwsim:
                if not self.safe_connect():
                    return None
            
            self.flowsheet = self.dwsim.CreateFlowsheet()
            logger.info(f"创建流程图成功")
            return self.flowsheet
            
        except Exception as e:
            logger.error(f"创建流程图失败: {e}")
            return None
    
    def load_flowsheet(self, file_path: str) -> Any:
        """从文件加载流程图"""
        try:
            if not self.dwsim:
                if not self.safe_connect():
                    return None
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return None
            
            self.flowsheet = self.dwsim.LoadFlowsheet(file_path)
            logger.info(f"加载流程图成功: {file_path}")
            return self.flowsheet
            
        except Exception as e:
            logger.error(f"加载流程图失败: {e}")
            return None
    
    def save_flowsheet(self, file_path: str, flowsheet: Any = None) -> bool:
        """保存流程图到文件"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有可保存的流程图")
                return False
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            self.dwsim.SaveFlowsheet(fs, file_path)
            logger.info(f"保存流程图成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存流程图失败: {e}")
            return False
    
    def auto_layout(self, flowsheet: Any = None) -> bool:
        """自动排列流程图中的对象"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            fs.AutoLayout()
            logger.info("自动布局完成")
            return True
            
        except Exception as e:
            logger.error(f"自动布局失败: {e}")
            return False
    
    # ==================== 化合物管理 ====================
    
    def add_compound(self, compound_name: str, flowsheet: Any = None) -> bool:
        """添加化合物到流程图"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            fs.AddCompound(compound_name)
            if compound_name not in self.compounds:
                self.compounds.append(compound_name)
            logger.info(f"添加化合物: {compound_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加化合物失败: {e}")
            return False
    
    def add_compounds(self, compound_names: List[str], flowsheet: Any = None) -> int:
        """批量添加化合物"""
        success_count = 0
        for compound in compound_names:
            if self.add_compound(compound, flowsheet):
                success_count += 1
        return success_count
    
    def get_available_compounds(self) -> List[str]:
        """获取所有可用化合物列表"""
        try:
            if not self.dwsim:
                if not self.safe_connect():
                    return []
            
            compounds = self.dwsim.AvailableCompounds
            return list(compounds) if compounds else []
            
        except Exception as e:
            logger.error(f"获取化合物列表失败: {e}")
            return []
    
    # ==================== 物性包管理 ====================
    
    def create_property_package(self, package_name: str, flowsheet: Any = None) -> Any:
        """创建物性包"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return None
            
            pp = fs.CreatePropertyPackage(package_name)
            logger.info(f"创建物性包: {package_name}")
            return pp
            
        except Exception as e:
            logger.error(f"创建物性包失败: {e}")
            return None
    
    def add_property_package(self, package: Any, flowsheet: Any = None) -> bool:
        """添加物性包到流程图"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            fs.AddPropertyPackage(package)
            logger.info("添加物性包成功")
            return True
            
        except Exception as e:
            logger.error(f"添加物性包失败: {e}")
            return False
    
    def create_and_add_property_package(self, package_name: str, flowsheet: Any = None) -> Any:
        """创建并添加物性包（一步完成）"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return None
            
            fs.CreateAndAddPropertyPackage(package_name)
            if package_name not in self.property_packages:
                self.property_packages.append(package_name)
            logger.info(f"创建并添加物性包: {package_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建并添加物性包失败: {e}")
            return None
    
    def get_available_property_packages(self) -> List[str]:
        """获取所有可用物性包列表"""
        return self.PROPERTY_PACKAGES.copy()
    
    # ==================== 对象管理 ====================
    
    def add_object(self, object_type, x: int, y: int, name: str, flowsheet: Any = None) -> Any:
        """
        添加任意类型对象（通用方法）
        
        Args:
            object_type: 对象类型（可以是 int 或 DWSIMObjectType 枚举）
            x: X坐标位置
            y: Y坐标位置
            name: 对象名称
            flowsheet: 流程图对象（可选）
        
        Returns:
            添加的对象，失败返回 None
        """
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return None
            
            if isinstance(object_type, int):
                dwsim_obj_type = self.DWSIMObjectType(object_type)
            else:
                dwsim_obj_type = object_type
            
            try:
                obj = fs.AddObject(dwsim_obj_type, x, y, name)
                logger.info(f"添加对象成功: {name} (类型: {dwsim_obj_type})")
                return obj
            except Exception as e1:
                logger.warning(f"AddObject 失败: {e1}，尝试其他方法")
                
                try:
                    obj = fs.AddSimulationObject(dwsim_obj_type, name, x, y)
                    logger.info(f"添加对象(AddSimulationObject): {name}")
                    return obj
                except Exception as e2:
                    logger.warning(f"AddSimulationObject 失败: {e2}")
                    
                    try:
                        obj = fs.AddFlowsheetObject(dwsim_obj_type, x, y, name)
                        logger.info(f"添加对象(AddFlowsheetObject): {name}")
                        return obj
                    except Exception as e3:
                        logger.error(f"所有添加对象方法都失败: {e3}")
                        return None
            
        except Exception as e:
            logger.error(f"添加对象失败: {e}")
            return None
    
    def add_material_stream(self, name: str, x: int = 100, y: int = 100, 
                           temperature: float = None, pressure: float = None,
                           molar_flow: float = None, composition: List[float] = None,
                           flowsheet: Any = None) -> Any:
        """添加物料流"""
        try:
            obj = self.add_object(self.DWSIMObjectType.MaterialStream, x, y, name, flowsheet)
            if not obj:
                return None
            
            if temperature is not None:
                self.set_object_property(name, "Temperature", temperature, flowsheet)
            if pressure is not None:
                self.set_object_property(name, "Pressure", pressure, flowsheet)
            if molar_flow is not None:
                self.set_object_property(name, "MolarFlow", molar_flow, flowsheet)
            if composition is not None:
                self.set_object_property(name, "MolarComposition", composition, flowsheet)
            
            self.streams[name] = obj
            return obj
            
        except Exception as e:
            logger.error(f"添加物料流失败: {e}")
            return None
    
    def add_pump(self, name: str, x: int = 200, y: int = 100, 
                 parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加泵"""
        obj = self.add_object(self.DWSIMObjectType.Pump, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_compressor(self, name: str, x: int = 200, y: int = 100,
                       parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加压缩机"""
        obj = self.add_object(self.DWSIMObjectType.Compressor, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_heater(self, name: str, x: int = 200, y: int = 100,
                   parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加加热器"""
        obj = self.add_object(self.DWSIMObjectType.Heater, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_cooler(self, name: str, x: int = 200, y: int = 100,
                   parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加冷却器"""
        obj = self.add_object(self.DWSIMObjectType.Cooler, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_valve(self, name: str, x: int = 200, y: int = 100,
                  parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加阀门"""
        obj = self.add_object(self.DWSIMObjectType.Valve, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_mixer(self, name: str, x: int = 200, y: int = 100,
                  parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加混合器"""
        obj = self.add_object(self.DWSIMObjectType.Mixer, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_splitter(self, name: str, x: int = 200, y: int = 100,
                     parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加分流器"""
        obj = self.add_object(self.DWSIMObjectType.Splitter, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_heat_exchanger(self, name: str, x: int = 200, y: int = 100,
                           parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加换热器"""
        obj = self.add_object(self.DWSIMObjectType.HeatExchanger, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_reactor(self, name: str, x: int = 200, y: int = 100,
                    reactor_type: str = "Equilibrium", parameters: Dict[str, Any] = None,
                    flowsheet: Any = None) -> Any:
        """添加反应器"""
        obj = self.add_object(ObjectType.REACTOR.value, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_distillation_column(self, name: str, x: int = 200, y: int = 100,
                                stages: int = 10, parameters: Dict[str, Any] = None,
                                flowsheet: Any = None) -> Any:
        """添加精馏塔"""
        obj = self.add_object(ObjectType.DISTILLATION_COLUMN.value, x, y, name, flowsheet)
        if obj:
            if stages:
                self.set_object_property(name, "NumberOfStages", stages, flowsheet)
            if parameters:
                self._set_equipment_parameters(obj, parameters)
            self.equipment[name] = obj
        return obj
    
    def add_flash_drum(self, name: str, x: int = 200, y: int = 100,
                       parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加闪蒸罐"""
        obj = self.add_object(ObjectType.FLASH_DRUM.value, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def add_tank(self, name: str, x: int = 200, y: int = 100,
                 parameters: Dict[str, Any] = None, flowsheet: Any = None) -> Any:
        """添加储罐"""
        obj = self.add_object(ObjectType.TANK.value, x, y, name, flowsheet)
        if obj and parameters:
            self._set_equipment_parameters(obj, parameters)
        if obj:
            self.equipment[name] = obj
        return obj
    
    def _set_equipment_parameters(self, obj: Any, parameters: Dict[str, Any]):
        """设置设备参数"""
        for param_name, param_value in parameters.items():
            try:
                obj.SetPropertyValue(param_name, param_value)
            except Exception as e:
                logger.warning(f"设置参数 {param_name} 失败: {e}")
    
    # ==================== 连接管理 ====================
    
    def connect_objects(self, from_object: str, to_object: str, 
                        from_port: int = 0, to_port: int = 0,
                        flowsheet: Any = None) -> bool:
        """连接两个对象"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            # 获取对象
            from_obj = self.streams.get(from_object) or self.equipment.get(from_object)
            to_obj = self.streams.get(to_object) or self.equipment.get(to_object)
            
            if not from_obj or not to_obj:
                logger.error(f"找不到对象: {from_object} 或 {to_object}")
                return False
            
            # 连接
            fs.ConnectObjects(from_obj.GraphicObject, to_obj.GraphicObject, from_port, to_port)
            logger.info(f"连接: {from_object} -> {to_object}")
            return True
            
        except Exception as e:
            logger.error(f"连接对象失败: {e}")
            return False
    
    def disconnect_objects(self, from_object: str, to_object: str,
                          flowsheet: Any = None) -> bool:
        """断开两个对象的连接"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            from_obj = self.streams.get(from_object) or self.equipment.get(from_object)
            to_obj = self.streams.get(to_object) or self.equipment.get(to_object)
            
            if not from_obj or not to_obj:
                logger.error(f"找不到对象: {from_object} 或 {to_object}")
                return False
            
            fs.DisconnectObjects(from_obj.GraphicObject, to_obj.GraphicObject)
            logger.info(f"断开连接: {from_object} -> {to_object}")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    # ==================== 参数设置 ====================
    
    def set_object_property(self, object_name: str, property_name: str, 
                           value: Any, flowsheet: Any = None) -> bool:
        """设置对象属性值"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            obj = self.streams.get(object_name) or self.equipment.get(object_name)
            if not obj:
                # 尝试从流程图获取
                try:
                    obj = fs.SimulationObjects.get_Item(object_name)
                except:
                    pass
            
            if not obj:
                logger.error(f"找不到对象: {object_name}")
                return False
            
            obj.SetPropertyValue(property_name, value)
            logger.debug(f"设置属性: {object_name}.{property_name} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"设置属性失败: {e}")
            return False
    
    def get_object_property(self, object_name: str, property_name: str,
                           flowsheet: Any = None) -> Any:
        """获取对象属性值"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return None
            
            obj = self.streams.get(object_name) or self.equipment.get(object_name)
            if not obj:
                try:
                    obj = fs.SimulationObjects.get_Item(object_name)
                except:
                    pass
            
            if not obj:
                logger.error(f"找不到对象: {object_name}")
                return None
            
            return obj.GetPropertyValue(property_name)
            
        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            return None
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置仿真参数并运行仿真"""
        start_time = time.time()
        
        try:
            if not self.flowsheet:
                self.create_flowsheet()
            
            logger.info(f"开始设置仿真参数...")
            
            # 1. 添加化合物
            compounds = parameters.get("compounds", [])
            for compound in compounds:
                self.add_compound(compound)
            logger.info(f"添加了 {len(compounds)} 个化合物")
            
            # 2. 添加物性包
            property_package = parameters.get("property_package", "Peng-Robinson (PR)")
            self.create_and_add_property_package(property_package)
            logger.info(f"添加物性包: {property_package}")
            
            # 3. 添加物料流
            streams = parameters.get("streams", [])
            for stream_data in streams:
                self.add_material_stream(**stream_data)
            logger.info(f"添加了 {len(streams)} 个物料流")
            
            # 4. 添加设备
            equipment = parameters.get("equipment", [])
            for equip_data in equipment:
                self._add_equipment_from_dict(equip_data)
            logger.info(f"添加了 {len(equipment)} 个设备")
            
            # 5. 连接物流
            connections = parameters.get("connections", [])
            for conn in connections:
                self.connect_objects(**conn)
            logger.info(f"连接了 {len(connections)} 个物流")
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message=f"参数设置完成",
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
    
    def _add_equipment_from_dict(self, equip_data: Dict[str, Any]):
        """从字典添加设备"""
        equip_type = equip_data.get("type", "heater").lower()
        name = equip_data.get("name")
        x = equip_data.get("x", 200)
        y = equip_data.get("y", 100)
        parameters = equip_data.get("parameters", {})
        
        type_map = {
            "pump": self.add_pump,
            "compressor": self.add_compressor,
            "heater": self.add_heater,
            "cooler": self.add_cooler,
            "valve": self.add_valve,
            "mixer": self.add_mixer,
            "splitter": self.add_splitter,
            "heat_exchanger": self.add_heat_exchanger,
            "reactor": self.add_reactor,
            "distillation_column": self.add_distillation_column,
            "flash_drum": self.add_flash_drum,
            "tank": self.add_tank,
        }
        
        add_func = type_map.get(equip_type)
        if add_func:
            add_func(name=name, x=x, y=y, parameters=parameters)
        else:
            logger.warning(f"未知设备类型: {equip_type}")
    
    # ==================== 仿真计算 ====================
    
    def run_simulation(self, parameters: Dict[str, Any] = None, 
                       flowsheet: Any = None) -> SimulationResult:
        """运行仿真计算"""
        start_time = time.time()
        
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return SimulationResult(
                    success=False,
                    message="没有流程图",
                    execution_time=0
                )
            
            # 如果提供了参数，先设置
            if parameters:
                result = self.set_parameters(parameters)
                if not result.success:
                    return SimulationResult(
                        success=False,
                        message=result.message,
                        execution_time=result.execution_time
                    )
            
            logger.info("开始运行仿真...")
            
            # 运行仿真
            exceptions = self.dwsim.CalculateFlowsheet2(fs)
            
            if exceptions and len(exceptions) > 0:
                logger.warning(f"仿真有警告: {exceptions}")
            
            logger.info("仿真运行成功")
            
            # 获取结果
            results = self._get_results()
            
            return SimulationResult(
                success=True,
                message="仿真完成",
                streams=results["streams"],
                equipment=results["equipment"],
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"运行仿真失败: {e}")
            return SimulationResult(
                success=False,
                message=f"运行仿真失败: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def check_status(self, flowsheet: Any = None) -> str:
        """检查计算状态"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                return "No flowsheet"
            
            return fs.CheckStatus()
            
        except Exception as e:
            logger.error(f"检查状态失败: {e}")
            return "Error"
    
    def request_calculation(self, flowsheet: Any = None) -> bool:
        """请求计算（异步）"""
        try:
            fs = flowsheet or self.flowsheet
            if not fs:
                logger.error("没有流程图")
                return False
            
            fs.RequestCalculation()
            logger.info("已请求计算")
            return True
            
        except Exception as e:
            logger.error(f"请求计算失败: {e}")
            return False
    
    # ==================== 结果获取 ====================
    
    def get_results(self, stream_name: str = None, equipment_name: str = None) -> Dict[str, Any]:
        """获取仿真结果"""
        return self._get_results(stream_name, equipment_name)
    
    def get_stream_results(self, stream_name: str, 
                           properties: List[str] = None) -> Dict[str, Any]:
        """获取物料流结果"""
        try:
            obj = self.streams.get(stream_name)
            if not obj:
                logger.error(f"找不到物料流: {stream_name}")
                return {}
            
            if properties is None:
                properties = ["Temperature", "Pressure", "MolarFlow", "MassFlow", "MolarComposition"]
            
            results = {}
            for prop in properties:
                try:
                    results[prop] = obj.GetPropertyValue(prop)
                except Exception as e:
                    logger.warning(f"获取属性 {prop} 失败: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"获取物料流结果失败: {e}")
            return {}
    
    def get_equipment_results(self, equipment_name: str,
                              properties: List[str] = None) -> Dict[str, Any]:
        """获取设备结果"""
        try:
            obj = self.equipment.get(equipment_name)
            if not obj:
                logger.error(f"找不到设备: {equipment_name}")
                return {}
            
            results = {"type": type(obj).__name__}
            
            if properties:
                for prop in properties:
                    try:
                        results[prop] = obj.GetPropertyValue(prop)
                    except Exception as e:
                        logger.warning(f"获取属性 {prop} 失败: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"获取设备结果失败: {e}")
            return {}
    
    def _get_results(self, stream_name: str = None, equipment_name: str = None) -> Dict[str, Any]:
        """获取所有结果"""
        results = {
            "streams": {},
            "equipment": {}
        }
        
        # 获取物料流结果
        for name, stream in self.streams.items():
            if stream_name and name != stream_name:
                continue
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
            if equipment_name and name != equipment_name:
                continue
            try:
                results["equipment"][name] = {
                    "type": type(equip).__name__
                }
            except Exception as e:
                logger.warning(f"获取设备 {name} 结果失败: {e}")
        
        return results
    
    # ==================== 反应管理 ====================
    
    def create_equilibrium_reaction(self, name: str, reactants: Dict[str, float] = None,
                                    products: Dict[str, float] = None,
                                    equilibrium_constant: float = None) -> Any:
        """创建平衡反应"""
        try:
            if not self.flowsheet:
                logger.error("没有流程图")
                return None
            
            reaction = self.flowsheet.CreateEquilibriumReaction(name)
            # TODO: 设置反应参数
            logger.info(f"创建平衡反应: {name}")
            return reaction
            
        except Exception as e:
            logger.error(f"创建平衡反应失败: {e}")
            return None
    
    def create_kinetic_reaction(self, name: str, reactants: Dict[str, float] = None,
                                products: Dict[str, float] = None,
                                rate_expression: str = None) -> Any:
        """创建动力学反应"""
        try:
            if not self.flowsheet:
                logger.error("没有流程图")
                return None
            
            reaction = self.flowsheet.CreateKineticReaction(name)
            logger.info(f"创建动力学反应: {name}")
            return reaction
            
        except Exception as e:
            logger.error(f"创建动力学反应失败: {e}")
            return None
    
    def create_conversion_reaction(self, name: str, reactants: Dict[str, float] = None,
                                   products: Dict[str, float] = None,
                                   conversion: float = None) -> Any:
        """创建转化反应"""
        try:
            if not self.flowsheet:
                logger.error("没有流程图")
                return None
            
            reaction = self.flowsheet.CreateConversionReaction(name)
            logger.info(f"创建转化反应: {name}")
            return reaction
            
        except Exception as e:
            logger.error(f"创建转化反应失败: {e}")
            return None
    
    def create_reaction_set(self, name: str, reactions: List[Any] = None) -> Any:
        """创建反应集"""
        try:
            if not self.flowsheet:
                logger.error("没有流程图")
                return None
            
            reaction_set = self.flowsheet.CreateReactionSet(name)
            logger.info(f"创建反应集: {name}")
            return reaction_set
            
        except Exception as e:
            logger.error(f"创建反应集失败: {e}")
            return None
    
    # ==================== 高级功能 ====================
    
    def sensitivity_analysis(self, variable_object: str, variable_property: str,
                            variable_range: List[float], objective_object: str,
                            objective_property: str) -> List[Tuple[float, float]]:
        """执行灵敏度分析"""
        try:
            results = []
            
            for value in variable_range:
                # 设置变量
                self.set_object_property(variable_object, variable_property, value)
                
                # 运行仿真
                sim_result = self.run_simulation()
                
                if sim_result.success:
                    # 获取目标值
                    obj_value = self.get_object_property(objective_object, objective_property)
                    results.append((value, obj_value))
                else:
                    results.append((value, None))
            
            logger.info(f"灵敏度分析完成，共 {len(results)} 个点")
            return results
            
        except Exception as e:
            logger.error(f"灵敏度分析失败: {e}")
            return []
    
    def optimize_single_parameter(self, param_object: str, param_property: str,
                                  objective_object: str, objective_property: str,
                                  bounds: Tuple[float, float], method: str = "scipy") -> Dict[str, Any]:
        """单参数优化"""
        try:
            from scipy.optimize import minimize_scalar
            
            def objective(x):
                self.set_object_property(param_object, param_property, x)
                sim_result = self.run_simulation()
                if sim_result.success:
                    return self.get_object_property(objective_object, objective_property)
                return float('inf')
            
            result = minimize_scalar(objective, bounds=bounds, method='bounded')
            
            return {
                "success": True,
                "optimal_value": result.x,
                "optimal_objective": result.fun,
                "iterations": result.nfev
            }
            
        except Exception as e:
            logger.error(f"优化失败: {e}")
            return {"success": False, "message": str(e)}
    
    def multi_objective_optimization(self, objectives: List[Dict[str, Any]],
                                     bounds: List[Tuple[float, float]],
                                     population_size: int = 100,
                                     generations: int = 50) -> Dict[str, Any]:
        """多目标优化（使用 NSGA-II）"""
        try:
            from pymoo.algorithms.moo.nsga2 import NSGA2
            from pymoo.optimize import minimize as mo_minimize
            from pymoo.core.problem import Problem
            import numpy as np
            
            class DWSIMProblem(Problem):
                def __init__(self, adapter, objectives, bounds):
                    self.adapter = adapter
                    self.objectives = objectives
                    super().__init__(
                        n_var=len(bounds),
                        n_obj=len(objectives),
                        xl=[b[0] for b in bounds],
                        xu=[b[1] for b in bounds]
                    )
                
                def _evaluate(self, x, out, *args, **kwargs):
                    f = []
                    for xi in x:
                        results = []
                        for i, obj in enumerate(self.objectives):
                            self.adapter.set_object_property(
                                obj['object'], obj['property'], xi[i]
                            )
                        self.adapter.run_simulation()
                        for obj in self.objectives:
                            val = self.adapter.get_object_property(
                                obj['object'], obj['property']
                            )
                            results.append(val if val is not None else float('inf'))
                        f.append(results)
                    out["F"] = np.array(f)
            
            problem = DWSIMProblem(self, objectives, bounds)
            algorithm = NSGA2(pop_size=population_size)
            result = mo_minimize(problem, algorithm, ('n_gen', generations))
            
            return {
                "success": True,
                "pareto_front": result.F.tolist(),
                "pareto_solutions": result.X.tolist()
            }
            
        except ImportError:
            logger.warning("pymoo 未安装，无法执行多目标优化")
            return {"success": False, "message": "pymoo 未安装"}
        except Exception as e:
            logger.error(f"多目标优化失败: {e}")
            return {"success": False, "message": str(e)}
    
    # ==================== 工具方法 ====================
    
    def get_version(self) -> str:
        """获取 DWSIM 版本信息"""
        try:
            if not self.dwsim:
                if not self.safe_connect():
                    return "Unknown"
            return self.dwsim.GetVersion()
        except Exception as e:
            logger.error(f"获取版本失败: {e}")
            return "Unknown"
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            version = self.get_version()
            
            return SoftwareInfo(
                name="DWSIM",
                version=version,
                is_connected=self.is_connected,
                connection_status="connected" if self.is_connected else "disconnected",
                supported_parameters=[
                    "compounds", "property_package", "streams", "equipment", "connections",
                    "temperature", "pressure", "molar_flow", "mass_flow", "composition"
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

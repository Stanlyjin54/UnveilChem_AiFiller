"""
参数映射系统 - 标准化的参数-软件字段映射库
提供统一的参数映射接口，支持多种化工软件的参数转换
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    """参数类型枚举"""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW_RATE = "flow_rate"
    COMPOSITION = "composition"
    ENERGY = "energy"
    DIMENSION = "dimension"
    MATERIAL_PROPERTY = "material_property"
    OPERATING_CONDITION = "operating_condition"
    EQUIPMENT_SPEC = "equipment_spec"
    GEOMETRY = "geometry"


class SoftwareType(Enum):
    """支持的软件类型"""
    ASPEN_PLUS = "aspen_plus"
    DWSIM = "dwsim"
    CHEMCAD = "chemcad"
    PRO_II = "pro_ii"
    AUTOCAD = "autocad"
    SOLIDWORKS = "solidworks"
    EXCEL = "excel"


@dataclass
class ParameterMapping:
    """参数映射配置"""
    standard_name: str
    software_name: str
    parameter_type: ParameterType
    software_type: SoftwareType
    unit: str
    conversion_factor: float = 1.0
    description: str = ""
    validation_rules: Dict[str, Any] = None
    default_value: Any = None
    required: bool = False


@dataclass
class ValidationRule:
    """验证规则配置"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    regex_pattern: Optional[str] = None
    custom_validator: Optional[str] = None
    error_message: str = ""


class ParameterMapper(ABC):
    """参数映射器基类"""
    
    def __init__(self, software_type: SoftwareType):
        self.software_type = software_type
        self.mappings: Dict[str, ParameterMapping] = {}
        self.validation_rules: Dict[str, ValidationRule] = {}
        self._initialize_mappings()
    
    @abstractmethod
    def _initialize_mappings(self):
        """初始化参数映射 - 由子类实现"""
        pass
    
    def add_mapping(self, mapping: ParameterMapping):
        """添加参数映射"""
        self.mappings[mapping.standard_name] = mapping
        if mapping.validation_rules:
            self.validation_rules[mapping.standard_name] = ValidationRule(**mapping.validation_rules)
    
    def get_mapping(self, standard_name: str) -> Optional[ParameterMapping]:
        """获取参数映射"""
        return self.mappings.get(standard_name)
    
    def get_software_parameter(self, standard_name: str) -> Optional[str]:
        """获取软件特定的参数名"""
        mapping = self.get_mapping(standard_name)
        return mapping.software_name if mapping else None
    
    def convert_value(self, standard_name: str, value: Any) -> Any:
        """转换参数值"""
        mapping = self.get_mapping(standard_name)
        if not mapping:
            logger.warning(f"未找到参数映射: {standard_name}")
            return value
        
        # 应用转换因子
        if mapping.conversion_factor != 1.0:
            try:
                value = float(value) * mapping.conversion_factor
            except (ValueError, TypeError):
                logger.warning(f"无法转换参数值: {value}")
        
        return value
    
    def validate_parameter(self, standard_name: str, value: Any) -> tuple[bool, str]:
        """验证参数"""
        mapping = self.get_mapping(standard_name)
        if not mapping:
            return False, f"未找到参数映射: {standard_name}"
        
        rule = self.validation_rules.get(standard_name)
        if not rule:
            return True, ""
        
        # 数值范围验证
        if rule.min_value is not None and float(value) < rule.min_value:
            return False, rule.error_message or f"值必须大于等于 {rule.min_value}"
        
        if rule.max_value is not None and float(value) > rule.max_value:
            return False, rule.error_message or f"值必须小于等于 {rule.max_value}"
        
        # 允许值验证
        if rule.allowed_values is not None and value not in rule.allowed_values:
            return False, rule.error_message or f"值必须在允许列表中: {rule.allowed_values}"
        
        # 正则表达式验证
        if rule.regex_pattern is not None:
            import re
            if not re.match(rule.regex_pattern, str(value)):
                return False, rule.error_message or f"值格式不符合要求"
        
        return True, ""
    
    def map_parameters(self, standard_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """映射标准参数到软件特定参数"""
        software_parameters = {}
        
        for standard_name, value in standard_parameters.items():
            mapping = self.get_mapping(standard_name)
            if mapping:
                # 验证参数
                is_valid, error_msg = self.validate_parameter(standard_name, value)
                if not is_valid:
                    logger.error(f"参数验证失败: {standard_name} - {error_msg}")
                    continue
                
                # 转换值
                converted_value = self.convert_value(standard_name, value)
                software_parameters[mapping.software_name] = converted_value
            else:
                logger.warning(f"未找到参数映射: {standard_name}")
                # 保留原始参数作为后备
                software_parameters[standard_name] = value
        
        return software_parameters
    
    def reverse_map_parameters(self, software_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """反向映射软件参数到标准参数"""
        standard_parameters = {}
        
        # 创建反向映射字典
        reverse_mappings = {mapping.software_name: name for name, mapping in self.mappings.items()}
        
        for software_name, value in software_parameters.items():
            standard_name = reverse_mappings.get(software_name)
            if standard_name:
                # 反向转换值
                mapping = self.mappings[standard_name]
                if mapping.conversion_factor != 1.0:
                    try:
                        value = float(value) / mapping.conversion_factor
                    except (ValueError, TypeError):
                        logger.warning(f"无法反向转换参数值: {value}")
                
                standard_parameters[standard_name] = value
            else:
                logger.warning(f"未找到反向参数映射: {software_name}")
                standard_parameters[software_name] = value
        
        return standard_parameters


class AspenPlusParameterMapper(ParameterMapper):
    """Aspen Plus 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 Aspen Plus 参数映射"""
        # 温度参数
        self.add_mapping(ParameterMapping(
            standard_name="temperature",
            software_name="TEMP",
            parameter_type=ParameterType.TEMPERATURE,
            software_type=SoftwareType.ASPEN_PLUS,
            unit="C",
            conversion_factor=1.0,
            description="温度",
            validation_rules={"min_value": -273.15, "max_value": 1000, "error_message": "温度必须在-273.15到1000°C之间"},
            required=True
        ))
        
        # 压力参数
        self.add_mapping(ParameterMapping(
            standard_name="pressure",
            software_name="PRES",
            parameter_type=ParameterType.PRESSURE,
            software_type=SoftwareType.ASPEN_PLUS,
            unit="Pa",
            conversion_factor=1.0,
            description="压力",
            validation_rules={"min_value": 0, "max_value": 1e8, "error_message": "压力必须在0到1e8 Pa之间"},
            required=True
        ))
        
        # 流量参数
        self.add_mapping(ParameterMapping(
            standard_name="flow_rate",
            software_name="FLOW",
            parameter_type=ParameterType.FLOW_RATE,
            software_type=SoftwareType.ASPEN_PLUS,
            unit="kmol/hr",
            conversion_factor=1.0,
            description="摩尔流量",
            validation_rules={"min_value": 0, "error_message": "流量必须大于0"},
            required=True
        ))
        
        # 组成参数
        self.add_mapping(ParameterMapping(
            standard_name="composition",
            software_name="COMP",
            parameter_type=ParameterType.COMPOSITION,
            software_type=SoftwareType.ASPEN_PLUS,
            unit="fraction",
            conversion_factor=1.0,
            description="组分组成",
            validation_rules={"min_value": 0, "max_value": 1, "error_message": "组成必须在0到1之间"},
            required=False
        ))


class DWSIMParameterMapper(ParameterMapper):
    """DWSIM 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 DWSIM 参数映射"""
        # 温度参数
        self.add_mapping(ParameterMapping(
            standard_name="temperature",
            software_name="Temperature",
            parameter_type=ParameterType.TEMPERATURE,
            software_type=SoftwareType.DWSIM,
            unit="K",
            conversion_factor=273.15,  # 摄氏度转开尔文
            description="温度",
            validation_rules={"min_value": 0, "max_value": 1273.15, "error_message": "温度必须在0到1000°C之间"},
            required=True
        ))
        
        # 压力参数
        self.add_mapping(ParameterMapping(
            standard_name="pressure",
            software_name="Pressure",
            parameter_type=ParameterType.PRESSURE,
            software_type=SoftwareType.DWSIM,
            unit="Pa",
            conversion_factor=1.0,
            description="压力",
            validation_rules={"min_value": 0, "max_value": 1e8, "error_message": "压力必须在0到1e8 Pa之间"},
            required=True
        ))
        
        # 流量参数
        self.add_mapping(ParameterMapping(
            standard_name="flow_rate",
            software_name="MassFlow",
            parameter_type=ParameterType.FLOW_RATE,
            software_type=SoftwareType.DWSIM,
            unit="kg/s",
            conversion_factor=1/3600,  # kg/hr 转 kg/s
            description="质量流量",
            validation_rules={"min_value": 0, "error_message": "流量必须大于0"},
            required=True
        ))


class ChemCADParameterMapper(ParameterMapper):
    """ChemCAD 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 ChemCAD 参数映射"""
        # 温度参数
        self.add_mapping(ParameterMapping(
            standard_name="temperature",
            software_name="TEMP",
            parameter_type=ParameterType.TEMPERATURE,
            software_type=SoftwareType.CHEMCAD,
            unit="C",
            conversion_factor=1.0,
            description="温度",
            validation_rules={"min_value": -273.15, "max_value": 1000, "error_message": "温度必须在-273.15到1000°C之间"},
            required=True
        ))
        
        # 压力参数
        self.add_mapping(ParameterMapping(
            standard_name="pressure",
            software_name="PRES",
            parameter_type=ParameterType.PRESSURE,
            software_type=SoftwareType.CHEMCAD,
            unit="bar",
            conversion_factor=1e-5,  # Pa 转 bar
            description="压力",
            validation_rules={"min_value": 0, "max_value": 1000, "error_message": "压力必须在0到1000 bar之间"},
            required=True
        ))


class AutoCADParameterMapper(ParameterMapper):
    """AutoCAD 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 AutoCAD 参数映射"""
        # 几何参数
        self.add_mapping(ParameterMapping(
            standard_name="diameter",
            software_name="DIAMETER",
            parameter_type=ParameterType.GEOMETRY,
            software_type=SoftwareType.AUTOCAD,
            unit="mm",
            conversion_factor=1000,  # m 转 mm
            description="直径",
            validation_rules={"min_value": 0.001, "error_message": "直径必须大于0.001m"},
            required=True
        ))
        
        self.add_mapping(ParameterMapping(
            standard_name="length",
            software_name="LENGTH",
            parameter_type=ParameterType.GEOMETRY,
            software_type=SoftwareType.AUTOCAD,
            unit="mm",
            conversion_factor=1000,  # m 转 mm
            description="长度",
            validation_rules={"min_value": 0.001, "error_message": "长度必须大于0.001m"},
            required=True
        ))
        
        self.add_mapping(ParameterMapping(
            standard_name="angle",
            software_name="ANGLE",
            parameter_type=ParameterType.GEOMETRY,
            software_type=SoftwareType.AUTOCAD,
            unit="degree",
            conversion_factor=1.0,
            description="角度",
            validation_rules={"min_value": 0, "max_value": 360, "error_message": "角度必须在0到360度之间"},
            required=False
        ))


class SolidWorksParameterMapper(ParameterMapper):
    """SolidWorks 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 SolidWorks 参数映射"""
        # 几何参数
        self.add_mapping(ParameterMapping(
            standard_name="diameter",
            software_name="D1@Sketch1",
            parameter_type=ParameterType.GEOMETRY,
            software_type=SoftwareType.SOLIDWORKS,
            unit="m",
            conversion_factor=1.0,
            description="直径",
            validation_rules={"min_value": 0.001, "error_message": "直径必须大于0.001m"},
            required=True
        ))
        
        self.add_mapping(ParameterMapping(
            standard_name="length",
            software_name="D2@Extrude1",
            parameter_type=ParameterType.GEOMETRY,
            software_type=SoftwareType.SOLIDWORKS,
            unit="m",
            conversion_factor=1.0,
            description="长度",
            validation_rules={"min_value": 0.001, "error_message": "长度必须大于0.001m"},
            required=True
        ))
        
        # 材料属性
        self.add_mapping(ParameterMapping(
            standard_name="density",
            software_name="Density",
            parameter_type=ParameterType.MATERIAL_PROPERTY,
            software_type=SoftwareType.SOLIDWORKS,
            unit="kg/m3",
            conversion_factor=1.0,
            description="密度",
            validation_rules={"min_value": 1, "max_value": 20000, "error_message": "密度必须在1到20000 kg/m3之间"},
            required=False
        ))


class ExcelParameterMapper(ParameterMapper):
    """Excel 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 Excel 参数映射"""
        # 单元格参数
        self.add_mapping(ParameterMapping(
            standard_name="cell_value",
            software_name="CELL_VALUE",
            parameter_type=ParameterType.OPERATING_CONDITION,
            software_type=SoftwareType.EXCEL,
            unit="any",
            conversion_factor=1.0,
            description="单元格值",
            required=False
        ))
        
        self.add_mapping(ParameterMapping(
            standard_name="cell_range",
            software_name="CELL_RANGE",
            parameter_type=ParameterType.OPERATING_CONDITION,
            software_type=SoftwareType.EXCEL,
            unit="range",
            conversion_factor=1.0,
            description="单元格范围",
            validation_rules={"regex_pattern": r"^[A-Z]+[0-9]+:[A-Z]+[0-9]+$", "error_message": "无效的单元格范围格式"},
            required=False
        ))


class PROIIParameterMapper(ParameterMapper):
    """PRO/II 参数映射器"""
    
    def _initialize_mappings(self):
        """初始化 PRO/II 参数映射"""
        # 温度参数
        self.add_mapping(ParameterMapping(
            standard_name="temperature",
            software_name="TEMP",
            parameter_type=ParameterType.TEMPERATURE,
            software_type=SoftwareType.PRO_II,
            unit="C",
            conversion_factor=1.0,
            description="温度",
            validation_rules={"min_value": -273.15, "max_value": 1000, "error_message": "温度必须在-273.15到1000°C之间"},
            required=True
        ))
        
        # 压力参数
        self.add_mapping(ParameterMapping(
            standard_name="pressure",
            software_name="PRES",
            parameter_type=ParameterType.PRESSURE,
            software_type=SoftwareType.PRO_II,
            unit="bar",
            conversion_factor=1e-5,  # Pa 转 bar
            description="压力",
            validation_rules={"min_value": 0, "max_value": 1000, "error_message": "压力必须在0到1000 bar之间"},
            required=True
        ))
        
        # 流量参数
        self.add_mapping(ParameterMapping(
            standard_name="flow_rate",
            software_name="FLOW",
            parameter_type=ParameterType.FLOW_RATE,
            software_type=SoftwareType.PRO_II,
            unit="kmol/hr",
            conversion_factor=1.0,
            description="摩尔流量",
            validation_rules={"min_value": 0, "error_message": "流量必须大于0"},
            required=True
        ))
        
        # 组成参数
        self.add_mapping(ParameterMapping(
            standard_name="composition",
            software_name="COMP",
            parameter_type=ParameterType.COMPOSITION,
            software_type=SoftwareType.PRO_II,
            unit="fraction",
            conversion_factor=1.0,
            description="组分组成",
            validation_rules={"min_value": 0, "max_value": 1, "error_message": "组成必须在0到1之间"},
            required=False
        ))
        
        # 回流比参数（PRO/II特有）
        self.add_mapping(ParameterMapping(
            standard_name="reflux_ratio",
            software_name="REFLUX",
            parameter_type=ParameterType.OPERATING_CONDITION,
            software_type=SoftwareType.PRO_II,
            unit="ratio",
            conversion_factor=1.0,
            description="回流比",
            validation_rules={"min_value": 0, "error_message": "回流比必须大于0"},
            required=False
        ))
        
        # 塔板数参数（PRO/II特有）
        self.add_mapping(ParameterMapping(
            standard_name="stages",
            software_name="STAGES",
            parameter_type=ParameterType.EQUIPMENT_SPEC,
            software_type=SoftwareType.PRO_II,
            unit="count",
            conversion_factor=1.0,
            description="理论塔板数",
            validation_rules={"min_value": 1, "max_value": 200, "error_message": "塔板数必须在1到200之间"},
            required=False
        ))


class ParameterMappingRegistry:
    """参数映射注册表"""
    
    def __init__(self):
        self.mappers: Dict[SoftwareType, ParameterMapper] = {}
        self._register_default_mappers()
    
    def _register_default_mappers(self):
        """注册默认的参数映射器"""
        self.register_mapper(SoftwareType.ASPEN_PLUS, AspenPlusParameterMapper(SoftwareType.ASPEN_PLUS))
        self.register_mapper(SoftwareType.DWSIM, DWSIMParameterMapper(SoftwareType.DWSIM))
        self.register_mapper(SoftwareType.CHEMCAD, ChemCADParameterMapper(SoftwareType.CHEMCAD))
        self.register_mapper(SoftwareType.PRO_II, PROIIParameterMapper(SoftwareType.PRO_II))
        self.register_mapper(SoftwareType.AUTOCAD, AutoCADParameterMapper(SoftwareType.AUTOCAD))
        self.register_mapper(SoftwareType.SOLIDWORKS, SolidWorksParameterMapper(SoftwareType.SOLIDWORKS))
        self.register_mapper(SoftwareType.EXCEL, ExcelParameterMapper(SoftwareType.EXCEL))
    
    def register_mapper(self, software_type: SoftwareType, mapper: ParameterMapper):
        """注册参数映射器"""
        self.mappers[software_type] = mapper
        logger.info(f"已注册参数映射器: {software_type.value}")
    
    def get_mapper(self, software_type: SoftwareType) -> Optional[ParameterMapper]:
        """获取参数映射器"""
        return self.mappers.get(software_type)
    
    def get_supported_software(self) -> List[str]:
        """获取支持的软件列表"""
        return [software.value for software in self.mappers.keys()]
    
    def get_parameter_info(self, software_type: SoftwareType, parameter_name: str) -> Optional[Dict[str, Any]]:
        """获取参数信息"""
        mapper = self.get_mapper(software_type)
        if not mapper:
            return None
        
        mapping = mapper.get_mapping(parameter_name)
        if not mapping:
            return None
        
        return {
            "standard_name": mapping.standard_name,
            "software_name": mapping.software_name,
            "parameter_type": mapping.parameter_type.value,
            "unit": mapping.unit,
            "description": mapping.description,
            "required": mapping.required,
            "default_value": mapping.default_value
        }
    
    def validate_all_parameters(self, software_type: SoftwareType, parameters: Dict[str, Any]) -> Dict[str, tuple[bool, str]]:
        """验证所有参数"""
        mapper = self.get_mapper(software_type)
        if not mapper:
            return {param: (False, f"不支持的软件类型: {software_type.value}") for param in parameters.keys()}
        
        results = {}
        for param_name, value in parameters.items():
            results[param_name] = mapper.validate_parameter(param_name, value)
        
        return results


# 全局参数映射注册表实例
parameter_registry = ParameterMappingRegistry()


def get_parameter_mapper(software_type: Union[str, SoftwareType]) -> Optional[ParameterMapper]:
    """获取参数映射器"""
    if isinstance(software_type, str):
        try:
            software_type = SoftwareType(software_type)
        except ValueError:
            logger.error(f"不支持的软件类型: {software_type}")
            return None
    
    return parameter_registry.get_mapper(software_type)


def map_parameters(software_type: Union[str, SoftwareType], standard_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """映射参数"""
    mapper = get_parameter_mapper(software_type)
    if not mapper:
        logger.warning(f"未找到参数映射器，返回原始参数: {software_type}")
        return standard_parameters
    
    return mapper.map_parameters(standard_parameters)


def reverse_map_parameters(software_type: Union[str, SoftwareType], software_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """反向映射参数"""
    mapper = get_parameter_mapper(software_type)
    if not mapper:
        logger.warning(f"未找到参数映射器，返回原始参数: {software_type}")
        return software_parameters
    
    return mapper.reverse_map_parameters(software_parameters)


def validate_parameters(software_type: Union[str, SoftwareType], parameters: Dict[str, Any]) -> Dict[str, tuple[bool, str]]:
    """验证参数"""
    mapper = get_parameter_mapper(software_type)
    if not mapper:
        return {param: (False, f"不支持的软件类型: {software_type}") for param in parameters.keys()}
    
    return mapper.validate_all_parameters(software_type, parameters)


def get_supported_software() -> List[str]:
    """获取支持的软件列表"""
    return parameter_registry.get_supported_software()


def get_parameter_info(software_type: Union[str, SoftwareType], parameter_name: str) -> Optional[Dict[str, Any]]:
    """获取参数信息"""
    if isinstance(software_type, str):
        try:
            software_type = SoftwareType(software_type)
        except ValueError:
            return None
    
    return parameter_registry.get_parameter_info(software_type, parameter_name)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档解析结果数据模型
定义化工文档解析的结构化输出格式
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ParameterType(str, Enum):
    """工艺参数类型枚举"""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    FLOW_RATE = "flow_rate"
    CONCENTRATION = "concentration"
    PH = "ph"
    TIME = "time"
    VOLUME = "volume"
    MASS = "mass"

class EquipmentType(str, Enum):
    """设备类型枚举"""
    REACTOR = "reactor"
    PUMP = "pump"
    HEAT_EXCHANGER = "heat_exchanger"
    TANK = "tank"
    VALVE = "valve"
    PIPE = "pipe"
    INSTRUMENT = "instrument"
    TOWER = "tower"

class ChemicalEntityType(str, Enum):
    """化学实体类型枚举"""
    COMPOUND = "compound"
    REAGENT = "reagent"
    PRODUCT = "product"
    SOLVENT = "solvent"
    CATALYST = "catalyst"
    INTERMEDIATE = "intermediate"

class ProcessParameter(BaseModel):
    """工艺参数数据模型"""
    parameter_type: ParameterType = Field(..., description="参数类型")
    value: Union[float, str] = Field(..., description="参数值")
    unit: Optional[str] = Field(None, description="单位")
    min_value: Optional[float] = Field(None, description="最小值")
    max_value: Optional[float] = Field(None, description="最大值")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    source: str = Field("extraction", description="数据来源")
    location: Optional[str] = Field(None, description="在文档中的位置")
    context: Optional[str] = Field(None, description="上下文信息")
    
    class Config:
        use_enum_values = True

class ChemicalEntity(BaseModel):
    """化学实体数据模型"""
    name: str = Field(..., description="化学名称")
    formula: Optional[str] = Field(None, description="化学式")
    cas_number: Optional[str] = Field(None, description="CAS号")
    concentration: Optional[Dict[str, Any]] = Field(None, description="浓度信息")
    phase: Optional[str] = Field(None, description="物相（固/液/气）")
    purity: Optional[float] = Field(None, ge=0.0, le=100.0, description="纯度(%)")
    temperature: Optional[Dict[str, Any]] = Field(None, description="温度条件")
    pressure: Optional[Dict[str, Any]] = Field(None, description="压力条件")
    entity_type: ChemicalEntityType = Field(ChemicalEntityType.COMPOUND, description="实体类型")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="识别置信度")
    safety_info: Optional[Dict[str, Any]] = Field(None, description="安全信息")
    
    class Config:
        use_enum_values = True

class EquipmentInfo(BaseModel):
    """设备信息数据模型"""
    equipment_type: EquipmentType = Field(..., description="设备类型")
    name: Optional[str] = Field(None, description="设备名称")
    specifications: Optional[Dict[str, Any]] = Field(None, description="规格参数")
    location: Optional[str] = Field(None, description="位置信息")
    connections: Optional[List[str]] = Field(None, description="连接信息")
    operating_conditions: Optional[Dict[str, Any]] = Field(None, description="操作条件")
    
    class Config:
        use_enum_values = True

class RecipeInfo(BaseModel):
    """配方信息数据模型"""
    ingredients: List[Dict[str, Any]] = Field(default_factory=list, description="原料列表")
    quantities: List[Dict[str, Any]] = Field(default_factory=list, description="用量列表")
    instructions: List[str] = Field(default_factory=list, description="操作步骤")
    yield_percentage: Optional[float] = Field(None, description="产率(%)")
    time_required: Optional[str] = Field(None, description="所需时间")
    temperature: Optional[Dict[str, Any]] = Field(None, description="反应温度")
    pressure: Optional[Dict[str, Any]] = Field(None, description="反应压力")
    notes: Optional[List[str]] = Field(None, description="备注信息")
    
class DocumentParseResult(BaseModel):
    """文档解析结果数据模型"""
    success: bool = Field(..., description="解析是否成功")
    content: Optional[str] = Field(None, description="提取的文本内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    process_parameters: List[ProcessParameter] = Field(default_factory=list, description="工艺参数")
    chemical_entities: List[ChemicalEntity] = Field(default_factory=list, description="化学实体")
    equipment_info: Optional[Dict[str, Any]] = Field(None, description="设备信息")
    recipe_info: Optional[Dict[str, Any]] = Field(None, description="配方信息")
    text_content: Optional[str] = Field(None, description="完整文本内容")
    error: Optional[str] = Field(None, description="错误信息")
    parse_time: Optional[str] = Field(None, description="解析时间戳")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return self.dict()
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return self.json(ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentParseResult':
        """从字典创建实例"""
        return cls(**data)

class BatchProcessRequest(BaseModel):
    """批量处理请求数据模型"""
    file_paths: List[str] = Field(..., description="文件路径列表")
    options: Optional[Dict[str, Any]] = Field(None, description="解析选项")
    priority: str = Field("normal", description="处理优先级")
    callback_url: Optional[str] = Field(None, description="回调URL")
    
    class Config:
        use_enum_values = True

class BatchProcessResponse(BaseModel):
    """批量处理响应数据模型"""
    batch_id: str = Field(..., description="批次ID")
    status: str = Field(..., description="处理状态")
    total_files: int = Field(..., description="总文件数")
    processed_files: int = Field(0, description="已处理文件数")
    failed_files: int = Field(0, description="失败文件数")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="进度百分比")
    results: Optional[List[DocumentParseResult]] = Field(None, description="解析结果")
    error_summary: Optional[str] = Field(None, description="错误摘要")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    
    class Config:
        use_enum_values = True

class ParserStatus(BaseModel):
    """解析器状态数据模型"""
    parser_name: str = Field(..., description="解析器名称")
    supported_formats: List[str] = Field(..., description="支持的文件格式")
    is_available: bool = Field(..., description="是否可用")
    last_updated: Optional[str] = Field(None, description="最后更新时间")
    performance_stats: Optional[Dict[str, Any]] = Field(None, description="性能统计")
    features: List[str] = Field(default_factory=list, description="功能特性")
    
class SupportedFormatsResponse(BaseModel):
    """支持格式响应数据模型"""
    parsers: List[ParserStatus] = Field(..., description="解析器状态列表")
    total_parsers: int = Field(..., description="解析器总数")
    supported_extensions: List[str] = Field(..., description="支持的文件扩展名")
    batch_processing: bool = Field(False, description="是否支持批量处理")
    real_time_processing: bool = Field(False, description="是否支持实时处理")
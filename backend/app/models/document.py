#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化工文档解析数据模型
支持多格式文档解析、化学实体识别和工艺参数提取
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum

class DocumentStatus(str, enum.Enum):
    """文档状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ParserType(str, enum.Enum):
    """解析器类型枚举"""
    PDF = "pdf"
    WORD = "word"
    IMAGE = "image"
    CAD = "cad"
    PID = "pid"
    ENHANCED_PDF = "enhanced_pdf"
    BATCH = "batch"

class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    mime_type = Column(String(100))
    upload_user_id = Column(Integer, ForeignKey("users.id"))
    
    # 解析相关字段
    parse_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    parser_type = Column(Enum(ParserType))
    parse_started_at = Column(DateTime)
    parse_completed_at = Column(DateTime)
    parse_duration = Column(Float)  # 解析耗时（秒）
    
    # 结果相关字段
    extracted_text = Column(Text)
    doc_metadata = Column(JSON)
    error_message = Column(Text)
    
    # 关联关系
    user = relationship("User", back_populates="documents")
    parse_results = relationship("DocumentParseResult", back_populates="document", cascade="all, delete-orphan")
    batch_items = relationship("BatchProcessItem", back_populates="document", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class DocumentParseResult(Base):
    """文档解析结果模型"""
    __tablename__ = "document_parse_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # 基本结果信息
    success = Column(Boolean, default=False)
    content = Column(Text)
    confidence_score = Column(Float, default=0.0)
    
    # 提取的工艺参数
    process_parameters = Column(JSON)  # 存储为JSON格式
    
    # 化学实体信息
    chemical_entities = Column(JSON)  # 存储为JSON格式
    
    # 设备信息
    equipment_info = Column(JSON)  # 存储为JSON格式
    
    # 配方信息
    recipe_info = Column(JSON)  # 存储为JSON格式
    
    # 解析元数据
    parse_metadata = Column(JSON)  # 存储为JSON格式
    extraction_summary = Column(Text)  # 提取摘要
    
    # 关联关系
    document = relationship("Document", back_populates="parse_results")
    process_params = relationship("ProcessParameter", back_populates="parse_result", cascade="all, delete-orphan")
    chemical_entities_rel = relationship("ChemicalEntity", back_populates="parse_result", cascade="all, delete-orphan")
    equipment_info_rel = relationship("EquipmentInfo", back_populates="parse_result", cascade="all, delete-orphan")
    
    created_at = Column(DateTime, default=func.now())

class ProcessParameter(Base):
    """工艺参数模型"""
    __tablename__ = "process_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    parse_result_id = Column(Integer, ForeignKey("document_parse_results.id"))
    
    # 参数基本信息
    parameter_type = Column(String(50), nullable=False)  # temperature, pressure, flow_rate, etc.
    value = Column(Float)
    unit = Column(String(20))
    min_value = Column(Float)
    max_value = Column(Float)
    
    # 识别信息
    confidence = Column(Float, default=0.0)
    source = Column(String(50), default="extraction")
    location = Column(String(200))  # 在文档中的位置
    context = Column(Text)  # 上下文信息
    
    # 关联关系
    parse_result = relationship("DocumentParseResult", back_populates="process_params")
    
    created_at = Column(DateTime, default=func.now())

class ChemicalEntity(Base):
    """化学实体模型"""
    __tablename__ = "chemical_entities"
    
    id = Column(Integer, primary_key=True, index=True)
    parse_result_id = Column(Integer, ForeignKey("document_parse_results.id"))
    
    # 基本信息
    name = Column(String(200), nullable=False)
    formula = Column(String(100))
    cas_number = Column(String(20))
    
    # 化学特性
    concentration = Column(JSON)  # 浓度信息
    phase = Column(String(20))  # 物相
    purity = Column(Float)  # 纯度
    
    # 条件信息
    temperature = Column(JSON)  # 温度条件
    pressure = Column(JSON)  # 压力条件
    
    # 分类信息
    entity_type = Column(String(50), default="compound")
    confidence = Column(Float, default=0.0)
    safety_info = Column(JSON)  # 安全信息
    
    # 关联关系
    parse_result = relationship("DocumentParseResult", back_populates="chemical_entities_rel")
    
    created_at = Column(DateTime, default=func.now())

class EquipmentInfo(Base):
    """设备信息模型"""
    __tablename__ = "equipment_info"
    
    id = Column(Integer, primary_key=True, index=True)
    parse_result_id = Column(Integer, ForeignKey("document_parse_results.id"))
    
    # 设备基本信息
    equipment_type = Column(String(50), nullable=False)
    name = Column(String(200))
    specifications = Column(JSON)  # 规格参数
    
    # 位置和连接
    location = Column(String(200))
    connections = Column(JSON)  # 连接信息
    
    # 操作条件
    operating_conditions = Column(JSON)
    
    # 关联关系
    parse_result = relationship("DocumentParseResult", back_populates="equipment_info_rel")
    
    created_at = Column(DateTime, default=func.now())

class BatchProcessRequest(Base):
    """批量处理请求模型"""
    __tablename__ = "batch_process_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 处理状态
    status = Column(String(20), default="pending")
    priority = Column(String(20), default="normal")
    
    # 统计信息
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    
    # 配置信息
    options = Column(JSON)  # 解析选项
    callback_url = Column(String(500))  # 回调URL
    
    # 时间信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User")
    batch_items = relationship("BatchProcessItem", back_populates="batch_request", cascade="all, delete-orphan")

class BatchProcessItem(Base):
    """批量处理项目模型"""
    __tablename__ = "batch_process_items"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_request_id = Column(Integer, ForeignKey("batch_process_requests.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # 处理状态
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    
    # 结果
    result_summary = Column(Text)
    
    # 关联关系
    batch_request = relationship("BatchProcessRequest", back_populates="batch_items")
    document = relationship("Document", back_populates="batch_items")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ParseHistory(Base):
    """解析历史模型"""
    __tablename__ = "parse_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    # 解析信息
    parser_type = Column(String(50))
    parse_duration = Column(Float)  # 解析耗时
    success = Column(Boolean)
    
    # 统计信息
    parameters_count = Column(Integer, default=0)
    entities_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    
    # 关联关系
    user = relationship("User")
    
    created_at = Column(DateTime, default=func.now())

# 扩展User模型以包含新的关系
def get_user_relationships():
    """获取用户模型的新关系"""
    return {
        "documents": relationship("Document", back_populates="user"),
        "parse_history": relationship("ParseHistory", back_populates="user"),
        "batch_requests": relationship("BatchProcessRequest", back_populates="user")
    }
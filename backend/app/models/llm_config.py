#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM配置数据模型
支持多租户LLM配置管理
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class LLMFactory(str, enum.Enum):
    """支持的LLM厂商"""
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    OLLAMA = "Ollama"
    AZURE_OPENAI = "Azure-OpenAI"
    GOOGLE = "Google"
    LOCALAI = "LocalAI"
    OPENAI_COMPATIBLE = "OpenAI-API-Compatible"


class LLMType(str, enum.Enum):
    """LLM模型类型"""
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    IMAGE2TEXT = "image2text"
    SPEECH2TEXT = "speech2text"
    TTS = "tts"
    OCR = "ocr"


class LLMConfig(Base):
    """LLM配置模型"""
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    llm_factory = Column(String(50), nullable=False)
    llm_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    
    # API配置
    api_key = Column(String(500))
    api_base = Column(String(500))
    api_version = Column(String(50))
    
    # 模型配置
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    
    # 状态
    status = Column(String(10), default="1")  # "1"=启用, "0"=禁用
    is_valid = Column(Boolean, default=True)
    
    # 使用统计
    used_tokens = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    tenant = relationship("User", back_populates="llm_configs")


class LLMAvailableFactory(Base):
    """可用的LLM厂商列表"""
    __tablename__ = "llm_available_factories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100))
    tags = Column(String(200))  # 厂商标签，如 "chat,embedding"
    status = Column(String(10), default="1")
    created_at = Column(DateTime, default=func.now())


class LLMModel(Base):
    """LLM模型信息"""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    fid = Column(String(50), nullable=False)  # 厂商ID
    llm_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    max_tokens = Column(Integer, default=4096)
    status = Column(String(10), default="1")
    created_at = Column(DateTime, default=func.now())

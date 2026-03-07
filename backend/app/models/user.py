#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)  # 改为可选
    phone = Column(String(20), unique=True, index=True, nullable=True)  # 新增手机号字段
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 新增版本和配额字段
    version = Column(String(20), default="basic")  # basic, pro, enterprise
    monthly_quota = Column(Integer, default=100)  # 每月解析次数配额
    used_quota = Column(Integer, default=0)  # 已使用的配额
    last_reset = Column(DateTime, default=func.now())  # 配额最后重置时间
    
    # 文档解析相关关系
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    parse_history = relationship("ParseHistory", back_populates="user", cascade="all, delete-orphan")
    batch_requests = relationship("BatchProcessRequest", back_populates="user", cascade="all, delete-orphan")
    
    # LLM配置相关关系
    llm_configs = relationship("LLMConfig", back_populates="tenant", cascade="all, delete-orphan")
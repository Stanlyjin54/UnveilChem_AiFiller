#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户相关的Pydantic模式
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """用户创建模式"""
    password: str

class UserUpdate(BaseModel):
    """用户更新模式"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # 新增版本和配额字段
    version: str
    monthly_quota: int
    used_quota: int
    last_reset: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """令牌响应模式"""
    access_token: str
    token_type: str
    user: UserResponse

class LoginRequest(BaseModel):
    """登录请求模式"""
    username: str
    password: str

class PasswordChange(BaseModel):
    """密码修改模式"""
    old_password: str
    new_password: str
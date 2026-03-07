#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, Token, LoginRequest, UserUpdate, PasswordChange
from ..utils.auth import verify_password, get_password_hash, create_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册 - 优先使用手机号验证，其次邮箱"""
    # 验证至少提供手机号或邮箱之一
    if not user_data.phone and not user_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供手机号或邮箱进行验证"
        )
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查手机号是否已存在（如果提供了手机号）
    if user_data.phone:
        existing_phone = db.query(User).filter(User.phone == user_data.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号已被注册"
            )
    
    # 检查邮箱是否已存在（如果提供了邮箱）
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 检查是否是第一个用户（系统管理员）
    is_first_user = db.query(User).count() == 0
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        password_hash=hashed_password,
        role="admin" if is_first_user else "user"  # 第一个用户自动成为管理员
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录 - 支持用户名、手机号或邮箱登录"""
    # 查找用户（支持用户名、手机号或邮箱登录）
    user = db.query(User).filter(
        (User.username == login_data.username) | 
        (User.phone == login_data.username) | 
        (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名/手机号/邮箱或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    from ..utils.auth import verify_token
    
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新个人资料 - 普通用户可以更新自己的资料"""
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    if user_data.email:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.username != username
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = user_data.email
    
    if user_data.full_name:
        user.full_name = user_data.full_name
    
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/change-password")
async def change_password(
    password_data: PasswordChange,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """修改密码 - 普通用户可以修改自己的密码"""
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证原密码
    if not verify_password(password_data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 更新密码
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}
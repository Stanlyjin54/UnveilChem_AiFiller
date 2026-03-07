#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse, UserUpdate
from ..utils.auth import oauth2_scheme, verify_token

router = APIRouter()

async def verify_admin(token: str, db: Session):
    """验证管理员权限"""
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return user

@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员权限）"""
    await verify_admin(token, db)
    
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取用户详情（管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新用户信息（管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    if user_data.email:
        # 检查邮箱是否已被其他用户使用
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
        user.email = user_data.email
    
    if user_data.full_name:
        user.full_name = user_data.full_name
    
    if user_data.password:
        from ..utils.auth import get_password_hash
        user.password_hash = get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """删除用户（管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    current_user = await verify_admin(token, db)
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    db.delete(user)
    db.commit()
    
    return {"message": "用户删除成功"}

@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """激活用户账户（管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.is_active = True
    db.commit()
    
    return {"message": "用户账户已激活"}

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """禁用用户账户（管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.is_active = False
    db.commit()
    
    return {"message": "用户账户已禁用"}

@router.get("/statistics")
async def get_statistics(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取系统统计信息（管理员权限）"""
    await verify_admin(token, db)
    
    # 获取用户统计
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    
    # 这里可以添加更多统计信息，如文档数量、解析次数等
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users
        },
        "documents": {
            "total": 0,  # 需要实现文档统计
            "processed": 0
        },
        "system": {
            "uptime": "24小时",  # 需要实现系统运行时间统计
            "version": "1.0.0"
        }
    }

@router.post("/users/{user_id}/promote")
async def promote_to_admin(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """将用户提升为管理员（需要管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="用户已经是管理员")
    
    user.role = "admin"
    db.commit()
    
    return {"message": f"用户 {user.username} 已成功提升为管理员"}

@router.post("/users/{user_id}/demote")
async def demote_from_admin(
    user_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """将管理员降级为普通用户（需要管理员权限）"""
    await verify_admin(token, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.role != "admin":
        raise HTTPException(status_code=400, detail="用户不是管理员")
    
    # 检查是否还有至少一个管理员
    admin_count = db.query(User).filter(User.role == "admin").count()
    if admin_count <= 1:
        raise HTTPException(status_code=400, detail="系统中必须至少保留一个管理员")
    
    user.role = "user"
    db.commit()
    
    return {"message": f"用户 {user.username} 已降级为普通用户"}

@router.put("/users/{user_id}/version")
async def update_user_version(
    user_id: int,
    request: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """更新用户版本（需要管理员权限）"""
    await verify_admin(token, db)
    
    # 获取版本值
    version = request.get("version")
    if not version:
        raise HTTPException(
            status_code=400, 
            detail="版本值不能为空"
        )
    
    # 验证版本值
    valid_versions = ["basic", "pro", "enterprise"]
    if version not in valid_versions:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的版本值，必须是 {', '.join(valid_versions)} 之一"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户版本
    user.version = version
    
    # 根据版本设置默认配额
    if version == "basic":
        user.monthly_quota = 100
    elif version == "pro":
        user.monthly_quota = 500
    elif version == "enterprise":
        user.monthly_quota = 0  # 0表示无限
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"用户 {user.username} 版本已更新为 {version}",
        "user": user
    }
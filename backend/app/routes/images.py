#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片解析路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from pathlib import Path

from ..database import get_db
from ..models.user import User
from ..utils.auth import oauth2_scheme, verify_token
from ..services.document_parser import DocumentParser

router = APIRouter()
parser = DocumentParser()

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """上传图片文件"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件类型
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的图片格式: {file_ext}"
        )
    
    # 保存文件
    upload_dir = Path("uploads/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{user.id}_{file.filename}"
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 解析图片
        result = parser.parse_document(str(file_path))
        
        return {
            "success": True,
            "message": "图片上传成功",
            "file_path": str(file_path),
            "file_name": file.filename,
            "analysis_result": result
        }
        
    except Exception as e:
        # 删除上传的文件
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500, 
            detail=f"图片处理失败: {str(e)}"
        )

@router.post("/analyze")
async def analyze_image(
    file_path: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """分析已上传的图片"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        # 解析图片
        result = parser.parse_document(file_path)
        
        return {
            "success": True,
            "analysis_result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"图片分析失败: {str(e)}"
        )

@router.post("/chemical-structure")
async def detect_chemical_structure(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """检测图片中的化学结构"""
    # 验证用户
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 检查文件类型
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的图片格式: {file_ext}"
        )
    
    # 保存文件
    upload_dir = Path("uploads/chemical_structures")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{user.id}_{file.filename}"
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 这里可以集成化学结构识别算法
        # 目前返回模拟结果
        result = {
            "chemical_structures": [
                {
                    "type": "molecule",
                    "name": "苯环",
                    "confidence": 0.85,
                    "coordinates": {"x": 100, "y": 150, "width": 200, "height": 200}
                },
                {
                    "type": "functional_group",
                    "name": "羟基",
                    "confidence": 0.72,
                    "coordinates": {"x": 350, "y": 200, "width": 50, "height": 50}
                }
            ],
            "text_content": "图片中包含苯环和羟基结构"
        }
        
        return {
            "success": True,
            "message": "化学结构检测完成",
            "file_path": str(file_path),
            "detection_result": result
        }
        
    except Exception as e:
        # 删除上传的文件
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500, 
            detail=f"化学结构检测失败: {str(e)}"
        )
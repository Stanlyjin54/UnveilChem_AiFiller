#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "UnveilChem API"
    app_version: str = "1.0.0"
    debug: bool = False  # 生产环境关闭调试
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # 数据库配置
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./unveilchem.db"
    )
    
    # JWT配置
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 文件上传配置
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [".pdf", ".doc", ".docx", ".xls", ".xlsx", 
                              ".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    
    # 阿里云OSS配置
    oss_access_key: Optional[str] = os.getenv("OSS_ACCESS_KEY")
    oss_secret_key: Optional[str] = os.getenv("OSS_SECRET_KEY")
    oss_endpoint: str = os.getenv("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    oss_bucket: str = os.getenv("OSS_BUCKET", "unveilchem")
    
    # 阿里云OCR配置
    aliyun_ocr_access_key: Optional[str] = os.getenv("ALIYUN_OCR_ACCESS_KEY")
    aliyun_ocr_secret_key: Optional[str] = os.getenv("ALIYUN_OCR_SECRET_KEY")
    aliyun_ocr_region: str = os.getenv("ALIYUN_OCR_REGION", "cn-hangzhou")
    
    # OCR配置
    tesseract_path: Optional[str] = None
    
    # 化学解析配置
    chemdataextractor_enabled: bool = True
    
    # CORS配置
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "https://www.unveilchem.com",
        "https://unveilchem.com"
    ]
    
    class Config:
        env_file = ".env"

# 全局配置实例
settings = Settings()
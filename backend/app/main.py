#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnveilChem 后端API主程序
智能化工软件自动化平台 - FastAPI后端服务
"""

import logging
import logging.handlers
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from typing import List, Optional
import uvicorn
import os
from pathlib import Path
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)

logger = logging.getLogger("unveilchem")

from .config import settings
from .database import engine, Base, get_db
from .models.user import User
from .models import *  # 导入所有模型
from .routes import auth, documents, images, admin, automation, agent, translation, report, llm_config
from .services.document_parsers.batch_api import router as router_batch
from .utils.auth import get_password_hash
from .services.llm.llm_config_service import init_default_llm_data

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化管理员账号
def init_admin_account():
    """初始化管理员账号"""
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    
    # 检查是否已存在管理员账号
    admin_user = db.query(User).filter(User.username == "admin").first()
    
    if not admin_user:
        # 创建管理员账号
        admin_user = User(
            username="admin",
            email="admin@unveilchem.com",
            password_hash=get_password_hash("admin123"),
            full_name="系统管理员",
            role="admin",
            is_active=True,
            version="enterprise",
            monthly_quota=0,  # 0表示无限
            used_quota=0
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("管理员账号已创建: username=admin, password=admin123")
    else:
        print("管理员账号已存在")
    
    db.close()

# 初始化LLM默认数据
def init_llm_data():
    """初始化LLM默认厂商和模型数据"""
    from sqlalchemy.orm import Session
    db = Session(bind=engine)
    try:
        init_default_llm_data(db)
        print("LLM默认数据初始化完成")
    except Exception as e:
        print(f"LLM默认数据初始化失败: {e}")
    finally:
        db.close()

# 调用初始化函数
init_admin_account()
init_llm_data()

app = FastAPI(
    title="UnveilChem API",
    description="化工文档参数提取工具后端API",
    version="1.0.0",
    docs_url=None,  # 禁用默认文档
    redoc_url=None,  # 禁用默认ReDoc
    openapi_url="/api/openapi.json"
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.datetime.now()
    
    # 记录请求信息
    logger.info(f"REQUEST: {request.method} {request.url} - Headers: {dict(request.headers)}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = datetime.datetime.now() - start_time
    
    # 记录响应信息
    logger.info(f"RESPONSE: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time.total_seconds()*1000:.2f}ms")
    
    return response

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 自定义Swagger UI文档路由
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

# 自定义ReDoc文档路由
@app.get("/api/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@2.1.3/bundles/redoc.standalone.js"
    )

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(documents.router, prefix="/api/documents", tags=["文档"])
app.include_router(images.router, prefix="/api/images", tags=["图片"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(automation.router, prefix="/api/automation", tags=["自动化"])
app.include_router(router_batch, prefix="/api/batch", tags=["批量处理"])
app.include_router(agent.router, prefix="/api/agent", tags=["智能Agent"])
app.include_router(translation.router, prefix="/api/translation", tags=["翻译"])
app.include_router(report.router, prefix="/api/report", tags=["报告"])
app.include_router(llm_config.router, prefix="/api/llm", tags=["LLM配置"])

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "UnveilChem API服务运行中",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check(db=Depends(get_db)):
    """健康检查接口"""
    import datetime
    import psutil
    
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    # 获取系统信息
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "system": {
            "cpu_usage": f"{cpu_usage}%",
            "memory_usage": f"{memory.percent}%",
            "disk_usage": f"{disk.percent}%",
            "total_memory": f"{memory.total / (1024**3):.2f} GB",
            "available_memory": f"{memory.available / (1024**3):.2f} GB"
        },
        "database": {
            "status": db_status,
            "engine": str(engine.url)
        },
        "service": {
            "name": "UnveilChem API",
            "version": "1.0.0",
            "docs_url": "/api/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
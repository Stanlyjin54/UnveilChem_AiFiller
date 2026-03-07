"""
API路由模块
"""

from fastapi import APIRouter
from .automation import router as automation_router

# 创建主路由器
api_router = APIRouter()

# 注册子路由器
api_router.include_router(automation_router, prefix="/automation", tags=["自动化"])
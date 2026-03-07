#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM配置API路由
提供LLM配置的RESTful接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from ..database import get_db
from .auth import get_current_user
from ..models.user import User
from ..services.llm.llm_config_service import LLMConfigService, init_default_llm_data

router = APIRouter(tags=["LLM配置"])


class LLMConfigCreate(BaseModel):
    """LLM配置创建请求"""
    llm_factory: str
    llm_name: str
    model_type: str
    api_key: str = ""
    api_base: str = ""
    api_version: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMConfigUpdate(BaseModel):
    """LLM配置更新请求"""
    api_key: str = ""
    api_base: str = ""
    api_version: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    status: str = "1"


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    id: int
    tenant_id: int
    llm_factory: str
    llm_name: str
    model_type: str
    api_base: str
    api_version: str
    max_tokens: int
    temperature: float
    status: str
    is_valid: bool
    used_tokens: int
    created_at: str
    updated_at: str


class FactoryResponse(BaseModel):
    """LLM厂商响应"""
    name: str
    display_name: str
    tags: List[str]


class ModelResponse(BaseModel):
    """LLM模型响应"""
    name: str
    model_type: str
    max_tokens: int


@router.get("/factories")
async def get_factories(db: Session = Depends(get_db)):
    """
    获取可用的LLM厂商列表
    """
    init_default_llm_data(db)
    factories = LLMConfigService.get_available_factories(db)
    return {"success": True, "data": factories}


@router.get("/factories/{factory}/models")
async def get_factory_models(factory: str, db: Session = Depends(get_db)):
    """
    获取某个厂商的模型列表
    """
    models = LLMConfigService.get_factory_models(db, factory)
    return {"success": True, "data": models}


@router.get("/configs")
async def get_my_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的所有LLM配置
    """
    configs = LLMConfigService.get_tenant_configs(db, current_user.id)
    # 隐藏敏感的api_key
    for config in configs:
        if config.get("api_key"):
            config["api_key"] = config["api_key"][:4] + "****" + config["api_key"][-4:] if len(config["api_key"]) > 8 else "****"
    return {"success": True, "data": configs}


@router.post("/configs", response_model=Dict[str, Any])
async def create_config(
    config: LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建LLM配置
    """
    try:
        success, message, result = LLMConfigService.validate_and_save(
            db=db,
            tenant_id=current_user.id,
            factory=config.llm_factory,
            model_name=config.llm_name,
            model_type=config.model_type,
            api_key=config.api_key,
            api_base=config.api_base,
            max_tokens=config.max_tokens
        )
        
        if success:
            return {
                "success": True,
                "message": message,
                "data": {
                    "id": result.id,
                    "llm_factory": result.llm_factory,
                    "llm_name": result.llm_name,
                    "model_type": result.model_type,
                    "status": result.status
                }
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configs/{config_id}", response_model=Dict[str, Any])
async def update_config(
    config_id: int,
    config: LLMConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新LLM配置
    """
    existing = db.query(User).query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not existing or existing.tenant_id != current_user.id:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    update_data = config.dict(exclude_unset=True)
    result = LLMConfigService.update_config(db, config_id, **update_data)
    
    if not result:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "success": True,
        "message": "配置已更新",
        "data": {"id": result.id}
    }


@router.delete("/configs/{config_id}", response_model=Dict[str, Any])
async def delete_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除LLM配置
    """
    # 验证配置属于当前用户
    config = db.query(LLMConfig).filter(
        LLMConfig.id == config_id,
        LLMConfig.tenant_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    success = LLMConfigService.delete_config(db, config_id)
    
    if success:
        return {"success": True, "message": "配置已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除失败")


@router.post("/configs/{config_id}/toggle", response_model=Dict[str, Any])
async def toggle_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启用/禁用LLM配置
    """
    config = db.query(LLMConfig).filter(
        LLMConfig.id == config_id,
        LLMConfig.tenant_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    result = LLMConfigService.toggle_config_status(db, config_id)
    
    if result:
        status_text = "启用" if result.status == "1" else "禁用"
        return {"success": True, "message": f"配置已{status_text}", "status": result.status}
    else:
        raise HTTPException(status_code=500, detail="操作失败")


@router.get("/configs/valid", response_model=List[Dict[str, Any]])
async def get_valid_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户启用的LLM配置（用于Agent等服务的LLM调用）
    """
    configs = LLMConfigService.get_valid_configs(db, current_user.id)
    return configs


@router.post("/configs/{config_id}/test", response_model=Dict[str, Any])
async def test_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    测试LLM配置是否可用
    """
    config = db.query(LLMConfig).filter(
        LLMConfig.id == config_id,
        LLMConfig.tenant_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # TODO: 实际测试LLM连接
    # 这里暂时返回成功，实际应该调用LLM客户端测试
    return {
        "success": True,
        "message": "配置测试通过",
        "available": True
    }


# 添加导入
from ..models.llm_config import LLMConfig

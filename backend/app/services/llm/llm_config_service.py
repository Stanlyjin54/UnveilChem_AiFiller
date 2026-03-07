#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM配置服务层
提供LLM配置的增删改查功能
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.llm_config import LLMConfig, LLMAvailableFactory, LLMModel


class LLMConfigService:
    """LLM配置服务"""
    
    @staticmethod
    def get_available_factories(db: Session) -> List[Dict[str, Any]]:
        """获取可用的LLM厂商列表"""
        factories = db.query(LLMAvailableFactory).filter(
            LLMAvailableFactory.status == "1"
        ).all()
        return [
            {
                "name": f.name,
                "display_name": f.display_name or f.name,
                "tags": f.tags.split(",") if f.tags else []
            }
            for f in factories
        ]
    
    @staticmethod
    def get_factory_models(db: Session, factory: str) -> List[Dict[str, Any]]:
        """获取某个厂商的模型列表"""
        models = db.query(LLMModel).filter(
            and_(
                LLMModel.fid == factory,
                LLMModel.status == "1"
            )
        ).all()
        return [
            {
                "name": m.llm_name,
                "model_type": m.model_type,
                "max_tokens": m.max_tokens
            }
            for m in models
        ]
    
    @staticmethod
    def get_tenant_configs(db: Session, tenant_id: int) -> List[Dict[str, Any]]:
        """获取租户的所有LLM配置"""
        configs = db.query(LLMConfig).filter(
            LLMConfig.tenant_id == tenant_id
        ).all()
        return [c.to_dict() for c in configs]
    
    @staticmethod
    def get_tenant_config(
        db: Session, 
        tenant_id: int, 
        factory: str, 
        model_name: str
    ) -> Optional[LLMConfig]:
        """获取租户的特定LLM配置"""
        return db.query(LLMConfig).filter(
            and_(
                LLMConfig.tenant_id == tenant_id,
                LLMConfig.llm_factory == factory,
                LLMConfig.llm_name == model_name
            )
        ).first()
    
    @staticmethod
    def create_config(
        db: Session,
        tenant_id: int,
        factory: str,
        model_name: str,
        model_type: str,
        api_key: str,
        api_base: str = "",
        api_version: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMConfig:
        """创建LLM配置"""
        config = LLMConfig(
            tenant_id=tenant_id,
            llm_factory=factory,
            llm_name=model_name,
            model_type=model_type,
            api_key=api_key,
            api_base=api_base,
            api_version=api_version,
            max_tokens=max_tokens,
            temperature=temperature,
            status="1",
            is_valid=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def update_config(
        db: Session,
        config_id: int,
        **kwargs
    ) -> Optional[LLMConfig]:
        """更新LLM配置"""
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            return None
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def delete_config(db: Session, config_id: int) -> bool:
        """删除LLM配置"""
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            return False
        
        db.delete(config)
        db.commit()
        return True
    
    @staticmethod
    def toggle_config_status(db: Session, config_id: int) -> Optional[LLMConfig]:
        """切换LLM配置状态"""
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if not config:
            return None
        
        config.status = "0" if config.status == "1" else "1"
        db.commit()
        db.refresh(config)
        return config
    
    @staticmethod
    def validate_and_save(
        db: Session,
        tenant_id: int,
        factory: str,
        model_name: str,
        model_type: str,
        api_key: str,
        api_base: str = "",
        max_tokens: int = 4096
    ) -> tuple[bool, str, Optional[LLMConfig]]:
        """
        验证API Key并保存配置
        返回: (是否成功, 消息, 配置对象)
        """
        # 本地部署的厂商不需要验证 API Key
        local_factories = ['Ollama', 'LocalAI']
        
        # 检查是否已存在配置
        existing = LLMConfigService.get_tenant_config(
            db, tenant_id, factory, model_name
        )
        
        if existing:
            # 更新现有配置
            config = LLMConfigService.update_config(
                db,
                existing.id,
                api_key=api_key,
                api_base=api_base,
                max_tokens=max_tokens,
                is_valid=True
            )
            return True, "配置已更新", config
        
        # 非本地部署厂商需要验证 API Key
        if factory not in local_factories and not api_key:
            return False, "请输入API Key", None
        
        # 创建新配置
        config = LLMConfigService.create_config(
            db,
            tenant_id,
            factory,
            model_name,
            model_type,
            api_key,
            api_base,
            max_tokens=max_tokens
        )
        return True, "配置已保存", config
    
    @staticmethod
    def get_valid_configs(db: Session, tenant_id: int) -> List[Dict[str, Any]]:
        """获取租户的有效LLM配置"""
        configs = db.query(LLMConfig).filter(
            and_(
                LLMConfig.tenant_id == tenant_id,
                LLMConfig.status == "1",
                LLMConfig.is_valid == True
            )
        ).all()
        return [c.to_dict() for c in configs]


# 为LLMConfig模型添加to_dict方法
def _llm_config_to_dict(self):
    return {
        "id": self.id,
        "tenant_id": self.tenant_id,
        "llm_factory": self.llm_factory,
        "llm_name": self.llm_name,
        "model_type": self.model_type,
        "api_key": self.api_key,
        "api_base": self.api_base,
        "api_version": self.api_version,
        "max_tokens": self.max_tokens,
        "temperature": self.temperature,
        "status": self.status,
        "is_valid": self.is_valid,
        "used_tokens": self.used_tokens,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None
    }

LLMConfig.to_dict = _llm_config_to_dict


# 初始化默认LLM厂商数据
DEFAULT_FACTORIES = [
    {"name": "OpenAI", "display_name": "OpenAI", "tags": "chat,embedding"},
    {"name": "Anthropic", "display_name": "Anthropic (Claude)", "tags": "chat"},
    {"name": "Ollama", "display_name": "Ollama (本地)", "tags": "chat,embedding"},
    {"name": "Azure-OpenAI", "display_name": "Azure OpenAI", "tags": "chat,embedding"},
    {"name": "Google", "display_name": "Google AI", "tags": "chat"},
    {"name": "LocalAI", "display_name": "LocalAI", "tags": "chat,embedding"},
    {"name": "OpenAI-API-Compatible", "display_name": "OpenAI 兼容接口", "tags": "chat,embedding"},
]

DEFAULT_MODELS = [
    # OpenAI
    {"fid": "OpenAI", "llm_name": "gpt-4o", "model_type": "chat", "max_tokens": 128000},
    {"fid": "OpenAI", "llm_name": "gpt-4-turbo", "model_type": "chat", "max_tokens": 128000},
    {"fid": "OpenAI", "llm_name": "gpt-3.5-turbo", "model_type": "chat", "max_tokens": 16385},
    {"fid": "OpenAI", "llm_name": "text-embedding-3-small", "model_type": "embedding", "max_tokens": 8192},
    {"fid": "OpenAI", "llm_name": "text-embedding-ada-002", "model_type": "embedding", "max_tokens": 8192},
    # Anthropic
    {"fid": "Anthropic", "llm_name": "claude-3-5-sonnet-20241022", "model_type": "chat", "max_tokens": 200000},
    {"fid": "Anthropic", "llm_name": "claude-3-opus-20240229", "model_type": "chat", "max_tokens": 200000},
    {"fid": "Anthropic", "llm_name": "claude-3-haiku-20240307", "model_type": "chat", "max_tokens": 200000},
    # Ollama
    {"fid": "Ollama", "llm_name": "llama3.1", "model_type": "chat", "max_tokens": 32768},
    {"fid": "Ollama", "llm_name": "qwen2.5", "model_type": "chat", "max_tokens": 32768},
    {"fid": "Ollama", "llm_name": "mixtral", "model_type": "chat", "max_tokens": 32768},
    # Azure OpenAI
    {"fid": "Azure-OpenAI", "llm_name": "gpt-4o", "model_type": "chat", "max_tokens": 128000},
    {"fid": "Azure-OpenAI", "llm_name": "gpt-35-turbo", "model_type": "chat", "max_tokens": 16385},
    # Google
    {"fid": "Google", "llm_name": "gemini-1.5-pro", "model_type": "chat", "max_tokens": 128000},
    {"fid": "Google", "llm_name": "gemini-1.5-flash", "model_type": "chat", "max_tokens": 128000},
]


def init_default_llm_data(db: Session):
    """初始化默认LLM数据"""
    # 初始化厂商
    for factory in DEFAULT_FACTORIES:
        existing = db.query(LLMAvailableFactory).filter(
            LLMAvailableFactory.name == factory["name"]
        ).first()
        if not existing:
            db.add(LLMAvailableFactory(**factory))
    
    # 初始化模型
    for model in DEFAULT_MODELS:
        existing = db.query(LLMModel).filter(
            and_(
                LLMModel.fid == model["fid"],
                LLMModel.llm_name == model["llm_name"]
            )
        ).first()
        if not existing:
            db.add(LLMModel(**model))
    
    db.commit()

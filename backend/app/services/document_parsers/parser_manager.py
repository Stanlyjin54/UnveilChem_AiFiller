#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一文档解析管理器
整合所有文档解析器，提供统一接口
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import importlib.util
import sys

from . import BaseDocumentParser
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .cad_parser import CADParser
from .image_parser import ImageParser
from .translation_service import TranslationService
from .report_generator import ReportGenerator

# 尝试导入高级解析器
try:
    from .advanced_parser import AdvancedParser
    ADVANCED_PARSER_AVAILABLE = True
except ImportError:
    ADVANCED_PARSER_AVAILABLE = False
    logging.warning("高级解析器不可用")

logger = logging.getLogger(__name__)

class DocumentParserManager:
    """文档解析管理器"""
    
    def __init__(self):
        self.parsers: Dict[str, BaseDocumentParser] = {}
        self._load_parsers()
        # 初始化翻译服务
        self.translation_service = TranslationService()
        # 初始化报告生成服务
        self.report_generator = ReportGenerator()
    
    def _load_parsers(self):
        """加载所有可用的解析器"""
        # PDF解析器
        try:
            self.parsers['pdf'] = PDFParser()
            logger.info("PDF解析器已加载")
        except Exception as e:
            logger.warning(f"PDF解析器加载失败: {e}")
        
        # Word解析器
        try:
            self.parsers['word'] = WordParser()
            logger.info("Word解析器已加载")
        except Exception as e:
            logger.warning(f"Word解析器加载失败: {e}")
        
        # CAD解析器
        try:
            self.parsers['cad'] = CADParser()
            logger.info("CAD解析器已加载")
        except Exception as e:
            logger.warning(f"CAD解析器加载失败: {e}")
        
        # 图像解析器
        try:
            self.parsers['image'] = ImageParser()
            logger.info("图像解析器已加载")
        except Exception as e:
            logger.warning(f"图像解析器加载失败: {e}")
        
        # 高级解析器
        if ADVANCED_PARSER_AVAILABLE:
            try:
                self.parsers['advanced'] = AdvancedParser()
                logger.info("高级解析器已加载")
            except Exception as e:
                logger.warning(f"高级解析器加载失败: {e}")
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """获取增强的格式支持信息"""
        current_support = {
            "documents": [],
            "images": []
        }
        
        planned_support = {
            "documents": ['.pdf', '.docx', '.doc'],
            "images": ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        }
        
        for parser_name, parser in self.parsers.items():
            for ext in parser.supported_extensions:
                if ext in ['.pdf', '.docx', '.doc']:
                    if ext not in current_support["documents"]:
                        current_support["documents"].append(ext)
                elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.dxf', '.dwg']:
                    if ext not in current_support["images"]:
                        current_support["images"].append(ext)
        
        # Get parser detailed status
        parsers_status = {}
        for name, parser in self.parsers.items():
            parsers_status[name] = {
                "available": True,
                "supported_extensions": parser.supported_extensions,
                "parser_name": parser.parser_name,
                "capabilities": parser.get_capabilities() if hasattr(parser, 'get_capabilities') else {},
                "performance_stats": parser.get_performance_stats() if hasattr(parser, 'get_performance_stats') else {}
            }
        
        # Add new feature flags
        return {
            "current_support": current_support,
            "planned_support": planned_support,
            "parsers_status": parsers_status,
            "features": {
                "batch_processing": True,
                "progress_tracking": True,
                "result_preview": True,
                "parameter_validation": True,
                "chemical_entity_recognition": True,
                "multi_language_support": True
            },
            "note": "系统支持多格式解析，具备批量处理、进度跟踪、结果预览等高级功能"
        }
    
    def get_available_parsers(self, user_version: str = "basic") -> List[BaseDocumentParser]:
        """根据用户版本获取可用的解析器
        
        Args:
            user_version: 用户版本，可选值：basic, pro, enterprise
            
        Returns:
            可用的解析器列表
        """
        available_parsers = []
        
        for parser in self.parsers.values():
            # 根据资源等级和用户版本决定是否可用
            if parser.resource_level == "low":
                # 低资源解析器对所有版本开放
                available_parsers.append(parser)
            elif parser.resource_level == "medium" and user_version in ["pro", "enterprise"]:
                # 中资源解析器对专业版和企业版开放
                available_parsers.append(parser)
            elif parser.resource_level == "high" and user_version == "enterprise":
                # 高资源解析器只对企业版开放
                available_parsers.append(parser)
        
        return available_parsers
    
    def find_suitable_parser(self, file_path: Path, user_version: str = "basic") -> Optional[BaseDocumentParser]:
        """查找适合的解析器
        
        Args:
            file_path: 文件路径
            user_version: 用户版本，可选值：basic, pro, enterprise
            
        Returns:
            适合的解析器，或None
        """
        available_parsers = self.get_available_parsers(user_version)
        
        for parser in available_parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def parse_document(self, file_path: Path, user_version: str = "basic") -> Dict[str, Any]:
        """解析文档（主入口）
        
        Args:
            file_path: 文件路径
            user_version: 用户版本，可选值：basic, pro, enterprise
            
        Returns:
            解析结果
        """
        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {file_path}",
                "file_path": str(file_path)
            }
        
        # 查找适合的解析器
        parser = self.find_suitable_parser(file_path, user_version)
        
        if not parser:
            return {
                "success": False,
                "error": f"不支持的文件格式: {file_path.suffix}，或当前版本不支持该解析器",
                "file_path": str(file_path),
                "supported_formats": self.get_supported_formats(),
                "user_version": user_version
            }
        
        # 执行解析
        try:
            result = parser.parse(file_path)
            
            # 添加通用元数据
            if result.get("success"):
                result["metadata"]["parser_loaded"] = True
                result["metadata"]["file_hash"] = self._calculate_file_hash(file_path)
                result["metadata"]["parse_timestamp"] = int(__import__('time').time())
                result["metadata"]["user_version"] = user_version
            
            return result
            
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            return {
                "success": False,
                "error": f"解析过程中发生错误: {str(e)}",
                "file_path": str(file_path),
                "parser_name": parser.parser_name,
                "user_version": user_version
            }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        import hashlib
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return "unknown"
    
    def validate_file_before_parse(self, file_path: Path) -> Dict[str, Any]:
        """解析前验证文件"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_info": {}
        }
        
        # 检查文件存在性
        if not file_path.exists():
            validation_result["valid"] = False
            validation_result["errors"].append("文件不存在")
            return validation_result
        
        # 获取文件信息
        try:
            stat = file_path.stat()
            validation_result["file_info"] = {
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "extension": file_path.suffix.lower(),
                "modified_time": stat.st_mtime
            }
            
            # 检查文件大小
            if stat.st_size == 0:
                validation_result["valid"] = False
                validation_result["errors"].append("文件为空")
            elif stat.st_size > 100 * 1024 * 1024:  # 100MB
                validation_result["warnings"].append("文件较大，可能影响解析速度")
            
            # 检查支持性
            parser = self.find_suitable_parser(file_path)
            if not parser:
                validation_result["valid"] = False
                validation_result["errors"].append(f"不支持的文件格式: {file_path.suffix}")
            else:
                validation_result["parser_info"] = {
                    "name": parser.parser_name,
                    "supported_extensions": parser.supported_extensions
                }
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"文件信息获取失败: {str(e)}")
        
        return validation_result
    
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> Dict[str, Any]:
        """翻译文本
        
        Args:
            text: 待翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            翻译结果
        """
        try:
            translated_text = self.translation_service.translate(text, source_lang, target_lang)
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
        except Exception as e:
            logger.error(f"文本翻译失败: {e}")
            return {
                "success": False,
                "error": f"翻译过程中发生错误: {str(e)}",
                "original_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
    
    def generate_report(self, template_name: str, data: Dict[str, Any], output_format: str = "pdf") -> Dict[str, Any]:
        """生成报告
        
        Args:
            template_name: 模板名称
            data: 报告数据
            output_format: 输出格式，支持pdf、word、html
            
        Returns:
            报告生成结果
        """
        try:
            report_content = self.report_generator.generate_report(template_name, data, output_format)
            return {
                "success": True,
                "report_content": report_content,
                "template_name": template_name,
                "output_format": output_format,
                "report_size": len(report_content)
            }
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return {
                "success": False,
                "error": f"报告生成过程中发生错误: {str(e)}",
                "template_name": template_name,
                "output_format": output_format
            }

# 全局解析器管理器实例
parser_manager = DocumentParserManager()

def get_parser_manager() -> DocumentParserManager:
    """获取解析器管理器实例"""
    return parser_manager

def parse_document(file_path: str) -> Dict[str, Any]:
    """便捷函数：解析文档"""
    return parser_manager.parse_document(Path(file_path))

def get_supported_formats() -> Dict[str, Any]:
    """便捷函数：获取支持的格式"""
    return parser_manager.get_supported_formats()
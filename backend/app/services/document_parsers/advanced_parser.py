#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级文档解析器

集成parsers目录下的UnifiedDocumentParser，提供统一的高级解析能力
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from . import BaseDocumentParser

# 导入高级解析器
try:
    import sys
    import os
    sys.path.append(os.path.abspath('d:\\UnveilChem_AiFiller'))
    from parsers.unified_parser import UnifiedDocumentParser, ParseRequest, DocumentType
    ADVANCED_PARSER_AVAILABLE = True
except ImportError as e:
    UnifiedDocumentParser = None
    ParseRequest = None
    DocumentType = None
    ADVANCED_PARSER_AVAILABLE = False
    logger.warning(f"高级解析器导入失败: {e}")

class AdvancedParser(BaseDocumentParser):
    """高级文档解析器，集成UnifiedDocumentParser"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.html', '.xml', '.rtf', '.odt', '.ods', '.csv',
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'
        ]
        self.parser_name = "ADVANCED_PARSER_V1"
        self.resource_level = "high"  # 设置资源等级为高
        
        # 初始化高级解析器
        self.unified_parser = None
        if ADVANCED_PARSER_AVAILABLE:
            try:
                self.unified_parser = UnifiedDocumentParser()
                logging.info("高级解析器初始化成功")
            except Exception as e:
                logging.warning(f"高级解析器初始化失败: {e}")
                self.unified_parser = None
    
    def can_parse(self, file_path: Path) -> bool:
        """检查是否能解析指定文件"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """解析文档并返回结构化数据"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        result = {
            "success": False,
            "parser_used": self.parser_name,
            "file_path": str(file_path),
            "metadata": self.get_metadata(file_path),
            "text_content": "",
            "tables": [],
            "images": [],
            "parameters": {},
            "errors": []
        }
        
        try:
            if not self.unified_parser:
                result["errors"].append("高级解析器未初始化")
                return result
            
            # 检测文档类型
            document_type = self.unified_parser.detect_document_type(file_path)
            
            # 创建解析请求
            request = ParseRequest(
                file_path=str(file_path),
                document_type=document_type
            )
            
            # 使用高级解析器解析
            unified_result = self.unified_parser.parse_document(request)
            
            # 转换结果格式
            if unified_result.success:
                result["success"] = True
                result["text_content"] = unified_result.content
                result["tables"] = unified_result.tables
                result["images"] = unified_result.images
                result["parameters"] = unified_result.parameters
                result["metadata"].update({
                    "advanced_parser_used": [p.value for p in unified_result.parser_used],
                    "confidence_score": unified_result.confidence_score,
                    "processing_time": unified_result.processing_time
                })
            else:
                result["errors"].append(f"高级解析器解析失败: {unified_result.error_message}")
            
        except Exception as e:
            result["errors"].append(f"高级解析器解析失败: {str(e)}")
            logging.error(f"高级解析器解析错误: {e}")
        
        return result
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文档格式"""
        if self.unified_parser:
            return self.unified_parser.get_supported_formats()
        return {}
    
    def get_parser_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        if self.unified_parser:
            return self.unified_parser.get_parser_statistics()
        return {}

# 更新以匹配增强的基类接口
BaseDocumentParser.register(AdvancedParser)
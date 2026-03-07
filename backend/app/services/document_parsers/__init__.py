#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档解析器统一架构

提供多格式文档解析的统一接口和基础架构
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import time

# 配置日志
logger = logging.getLogger(__name__)

class BaseDocumentParser(ABC):
    """增强版文档解析器抽象基类"""
    
    def __init__(self):
        self.supported_extensions: List[str] = []
        self.mime_types: List[str] = []
        self.parser_name: str = ""
        self.resource_level = "low"  # 资源等级：low/medium/high
        self.max_file_size = 50 * 1024 * 1024  # 50MB默认限制
        self.confidence_threshold = 0.7
        self.parse_statistics = {
            "total_files_parsed": 0,
            "success_count": 0,
            "error_count": 0,
            "average_parse_time": 0.0
        }
        
    @abstractmethod
    def can_parse(self, file_path: Union[str, Path]) -> bool:
        """检查是否能解析指定文件"""
        pass
    
    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """解析文档并返回结构化数据"""
        pass
    
    def get_metadata(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """获取文档元数据"""
        try:
            path = Path(file_path)
            return {
                "file_path": str(path),
                "file_size": path.stat().st_size if path.exists() else 0,
                "file_extension": path.suffix.lower(),
                "parser_used": self.parser_name,
                "supported_extensions": self.supported_extensions,
                "parse_capabilities": self.get_capabilities()
            }
        except Exception as e:
            logger.error(f"获取元数据失败: {e}")
            return {"error": str(e)}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取解析器能力描述"""
        return {
            "text_extraction": True,
            "table_extraction": False,
            "image_extraction": False,
            "metadata_extraction": True,
            "parameter_extraction": True,
            "chemical_entity_recognition": True
        }
    
    def validate_file(self, file_path: Union[str, Path]) -> tuple[bool, str]:
        """验证文件是否满足解析条件"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "文件不存在"
            
            if not self.can_parse(file_path):
                return False, f"不支持的文件格式: {path.suffix}"
            
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return False, f"文件大小超过限制 ({file_size / 1024 / 1024:.1f}MB)"
            
            return True, "文件验证通过"
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            return False, f"文件验证失败: {str(e)}"
    
    def _standardize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工艺参数"""
        standard_units = {
            'temperature': '°C',
            'pressure': 'bar',
            'flow_rate': 'm³/h',
            'concentration': 'mol/L'
        }
        
        standardized = {}
        for param_name, param_data in parameters.items():
            if isinstance(param_data, dict):
                # 标准化单位
                if param_name in standard_units:
                    param_data['unit'] = param_data.get('unit', standard_units[param_name])
                
                # 标准化数值
                if 'value' in param_data:
                    try:
                        param_data['value'] = float(param_data['value'])
                    except (ValueError, TypeError):
                        param_data['value'] = None
                
                # 添加置信度
                if 'confidence' not in param_data:
                    param_data['confidence'] = 0.8
                    
            standardized[param_name] = param_data
        
        return standardized
    
    def _extract_chemical_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取化学实体（基础实现）"""
        import re
        
        # 简单的化学实体识别规则
        chemical_patterns = {
            'chemical_formula': r'\b[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*\b',
            'cas_number': r'\b\d{2,7}-\d{2}-\d\b',
            'iupac_name': r'\b(?:meth|eth|prop|but|pent|hex|hept|oct)an(?:e|oic|ol)?\b'
        }
        
        entities = []
        for entity_type, pattern in chemical_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'text': match,
                    'confidence': 0.7
                })
        
        return entities
    
    def _timed_parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """带时间统计的解析"""
        start_time = time.time()
        self.parse_statistics["total_files_parsed"] += 1
        
        try:
            result = self.parse(file_path)
            parse_time = time.time() - start_time
            
            # 更新统计信息
            self.parse_statistics["success_count"] += 1
            self._update_average_time(parse_time)
            
            # 添加解析时间信息
            result["parse_time"] = parse_time
            result["parser_statistics"] = self.parse_statistics.copy()
            
            return result
        except Exception as e:
            self.parse_statistics["error_count"] += 1
            parse_time = time.time() - start_time
            logger.error(f"解析失败: {e}")
            
            return {
                "error": str(e),
                "parse_time": parse_time,
                "parser_statistics": self.parse_statistics.copy()
            }
    
    def _update_average_time(self, parse_time: float):
        """更新平均解析时间"""
        total = self.parse_statistics["success_count"]
        current_avg = self.parse_statistics["average_parse_time"]
        self.parse_statistics["average_parse_time"] = (
            (current_avg * (total - 1) + parse_time) / total
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total = self.parse_statistics["total_files_parsed"]
        if total == 0:
            return self.parse_statistics
        
        return {
            **self.parse_statistics,
            "success_rate": self.parse_statistics["success_count"] / total,
            "error_rate": self.parse_statistics["error_count"] / total
        }

# 增强的异常类定义
class ParserError(Exception):
    """解析器基础异常"""
    pass

class UnsupportedFormatError(ParserError):
    """不支持的格式异常"""
    pass

class ParsingError(ParserError):
    """解析过程异常"""
    pass

class FileValidationError(ParserError):
    """文件验证异常"""
    pass

class ConfigurationError(ParserError):
    """配置错误异常"""
    pass

class PerformanceError(ParserError):
    """性能相关异常"""
    pass
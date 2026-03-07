#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档解析服务 - 统一解析接口
使用新的解析器架构，支持多格式解析
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 导入新的解析器架构
from .document_parsers.parser_manager import get_parser_manager, DocumentParserManager

# 可选依赖导入
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("OCR功能不可用,请安装pytesseract和PIL")

try:
    from chemdataextractor import Document
    from chemdataextractor.model import Compound
    CHEM_AVAILABLE = True
except ImportError:
    CHEM_AVAILABLE = False
    logging.warning("化学文献解析功能不可用,请安装chemdataextractor")

logger = logging.getLogger(__name__)

class DocumentParser:
    """文档解析器 - 统一接口"""
    
    def __init__(self):
        # 使用新的解析器管理器
        self.parser_manager: DocumentParserManager = get_parser_manager()
        logger.info("文档解析器已初始化，使用新的解析器架构")
        
        # 获取初始格式信息
        formats = self.parser_manager.get_supported_formats()
        logger.info("当前支持的格式信息: %s", formats)
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """解析文档文件（使用新架构）"""
        import time
        start_time = time.time()
        file_path = Path(file_path)
        
        # 文件验证
        validation_start = time.time()
        validation_result = self.parser_manager.validate_file_before_parse(file_path)
        validation_time = time.time() - validation_start
        logger.info(f"文件验证耗时: {validation_time:.2f}秒, 文件: {file_path.name}")
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "文件验证失败",
                "validation_result": validation_result,
                "file_path": str(file_path)
            }
        
        # 解析文档
        parse_start = time.time()
        parse_result = self.parser_manager.parse_document(file_path)
        parse_time = time.time() - parse_start
        logger.info(f"文档解析耗时: {parse_time:.2f}秒, 文件: {file_path.name}")
        
        # 标准化返回格式以保持向后兼容
        standardize_start = time.time()
        standardized_result = self._standardize_result(parse_result)
        standardize_time = time.time() - standardize_start
        logger.info(f"结果标准化耗时: {standardize_time:.2f}秒, 文件: {file_path.name}")
        
        total_time = time.time() - start_time
        logger.info(f"总处理耗时: {total_time:.2f}秒, 文件: {file_path.name}")
        
        return standardized_result
    
    def _standardize_result(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """标准化解析结果格式以匹配前端期望"""
        standardized = {
            "file_path": parse_result.get("file_path", ""),
            "file_type": Path(parse_result.get("file_path", "")).suffix.lower(),
            "extracted_text": "",
            "chemical_entities": [],
            "process_parameters": [],
            "metadata": {},
            "success": parse_result.get("success", False),
            "error": None
        }
        
        if parse_result.get("success"):
            # 提取文本内容
            if "text_content" in parse_result:
                standardized["extracted_text"] = parse_result["text_content"]
            
            # 提取化学实体
            if "chemical_entities" in parse_result and isinstance(parse_result["chemical_entities"], list):
                standardized["chemical_entities"] = parse_result["chemical_entities"]
            elif "entities" in parse_result and isinstance(parse_result["entities"], list):
                # 兼容旧格式
                standardized["chemical_entities"] = parse_result["entities"]
            
            # 尝试从文本中提取简单的化学实体（无论之前是否有提取到）
            text = standardized["extracted_text"]
            if text:
                # 简单的化学实体提取逻辑（示例）
                import re
                # 匹配常见的化学分子式
                formulas = re.findall(r'[A-Z][a-z]?\d*', text)
                if formulas:
                    # 去重并创建化学实体
                    unique_formulas = list(set(formulas))
                    for formula in unique_formulas[:10]:  # 最多提取10个
                        # 检查是否已经存在相同的化学实体
                        existing_entity = next((e for e in standardized["chemical_entities"] 
                                            if e["text"] == formula), None)
                        if not existing_entity:
                            standardized["chemical_entities"].append({
                                "text": formula,
                                "type": "compound",
                                "confidence": 0.7,
                                "position": {
                                    "start": text.find(formula),
                                    "end": text.find(formula) + len(formula)
                                }
                            })
            
            # 提取工艺参数
            if "process_parameters" in parse_result and isinstance(parse_result["process_parameters"], list):
                standardized["process_parameters"] = parse_result["process_parameters"]
            elif "parameters" in parse_result and isinstance(parse_result["parameters"], dict):
                # 转换字典格式为数组格式
                for name, value in parse_result["parameters"].items():
                    standardized["process_parameters"].append({
                        "name": name,
                        "value": str(value),
                        "unit": "",
                        "confidence": 0.8,
                        "original_text": f"{name}: {value}"
                    })
            elif "parameters" in parse_result and isinstance(parse_result["parameters"], list):
                standardized["process_parameters"] = parse_result["parameters"]
            
            # 确保extracted_text字段不为空
            if not standardized["extracted_text"] and "text_content" in parse_result:
                standardized["extracted_text"] = parse_result["text_content"]
            
            # 尝试从文本中提取简单的工艺参数（无论之前是否有提取到）
            text = standardized["extracted_text"]
            if text:
                # 简单的工艺参数提取逻辑（示例）
                import re
                # 匹配类似 "温度: 25°C" 或 "压力=1.0 atm" 的模式
                param_patterns = [
                    r'(\w+)[:：]\s*([\d.]+)\s*([A-Za-z°%]+)',  # 温度: 25°C
                    r'(\w+)\s*=\s*([\d.]+)\s*([A-Za-z°%]+)',  # 压力=1.0 atm
                    r'(\w+)[:：]\s*([\d.]+)',  # 流量: 100
                ]
                
                for pattern in param_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if len(match) == 3:
                            name, value, unit = match
                        else:
                            name, value = match
                            unit = ""
                        
                        # 检查是否已经存在相同的参数
                        existing_param = next((p for p in standardized["process_parameters"] 
                                            if p["name"] == name and p["value"] == value and p["unit"] == unit), None)
                        if not existing_param:
                            standardized["process_parameters"].append({
                                "name": name,
                                "value": value,
                                "unit": unit,
                                "confidence": 0.6,
                                "original_text": f"{name}: {value} {unit}"
                            })
                
                # 去重和限制数量
                seen = set()
                unique_params = []
                for param in standardized["process_parameters"]:
                    key = f"{param['name']}-{param['value']}-{param['unit']}"
                    if key not in seen:
                        seen.add(key)
                        unique_params.append(param)
                standardized["process_parameters"] = unique_params[:15]  # 最多提取15个
            
            # 提取元数据
            if "metadata" in parse_result:
                standardized["metadata"].update(parse_result["metadata"])
            
            # CAD特殊处理
            if "entities" in parse_result and "entities" not in standardized["metadata"]:
                standardized["metadata"]["entities"] = parse_result["entities"]
            if "pipes" in parse_result:
                standardized["metadata"]["pipes"] = parse_result["pipes"]
            if "equipment" in parse_result:
                standardized["metadata"]["equipment"] = parse_result["equipment"]
            if "standardized_units" in parse_result:
                standardized["metadata"]["standardized_units"] = parse_result["standardized_units"]
            
            # 图片特殊处理
            if "images" in parse_result:
                standardized["metadata"]["extracted_images"] = parse_result["images"]
                
        else:
            # 错误处理
            standardized["error"] = parse_result.get("error", "解析失败")
        
        return standardized
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的格式信息"""
        return self.parser_manager.get_supported_formats()
    
    def parse_document_advanced(self, file_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """高级解析选项（为未来扩展预留）"""
        # 当前返回标准解析结果
        # 未来可以添加OCR增强、精确参数提取等高级选项
        return self.parse_document(file_path)
    
    def batch_parse_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """批量解析文档"""
        results = []
        for file_path in file_paths:
            try:
                result = self.parse_document(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": f"批量解析失败: {str(e)}"
                })
        return results
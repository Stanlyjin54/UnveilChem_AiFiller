#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD图纸解析器 - 支持AutoCAD和DXF/DWG格式
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import re

# CAD相关依赖（可选）
try:
    import ezdxf
    CAD_AVAILABLE = True
except ImportError:
    CAD_AVAILABLE = False
    logging.warning("CAD解析依赖缺失,请安装ezdxf")

try:
    import dxfgrabber
    DXFGRABBER_AVAILABLE = True
except ImportError:
    DXFGRABBER_AVAILABLE = False

from . import BaseDocumentParser

class CADParser(BaseDocumentParser):
    """CAD图纸解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.dxf', '.dwg']
        self.parser_name = "CAD_PARSER_V1"
        self.standard_units = {
            "mm": 1.0,
            "cm": 10.0,
            "m": 1000.0,
            "in": 25.4,
            "ft": 304.8
        }
    
    def can_parse(self, file_path: Path) -> bool:
        """检查是否是CAD文件"""
        return file_path.suffix.lower() in ['.dxf', '.dwg']
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """解析CAD图纸文件"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        result = {
            "success": False,
            "parser_used": self.parser_name,
            "file_path": str(file_path),
            "metadata": self.get_metadata(file_path),
            "entities": [],
            "dimensions": [],
            "annotations": [],
            "pipes": [],
            "equipment": [],
            "standardized_units": {},
            "errors": []
        }
        
        try:
            if file_path.suffix.lower() == '.dxf':
                return self._parse_dxf_file(file_path, result)
            elif file_path.suffix.lower() == '.dwg':
                return self._parse_dwg_file(file_path, result)
            else:
                result["errors"].append("不支持的CAD文件格式")
                
        except Exception as e:
            result["errors"].append(f"CAD解析失败: {str(e)}")
            logging.error(f"CAD解析错误: {e}")
        
        return result
    
    def _parse_dxf_file(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """解析DXF文件"""
        
        # 方法1: 使用ezdxf（推荐）
        if CAD_AVAILABLE:
            try:
                return self._parse_with_ezdxf(file_path, result)
            except Exception as e:
                result["errors"].append(f"ezdxf解析失败: {str(e)}")
        
        # 方法2: 使用dxfgrabber作为备用
        if DXFGRABBER_AVAILABLE:
            try:
                return self._parse_with_dxfgrabber(file_path, result)
            except Exception as e:
                result["errors"].append(f"dxfgrabber解析失败: {str(e)}")
        
        # 方法3: 简单文本解析（最基础）
        return self._parse_dxf_as_text(file_path, result)
    
    def _parse_with_ezdxf(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """使用ezdxf解析DXF"""
        doc = ezdxf.readfile(str(file_path))
        msp = doc.modelspace()
        
        # 获取图纸信息
        result["metadata"]["dxf_version"] = doc.dxfversion
        result["metadata"]["units"] = doc.header.get('$INSUNITS', 'Unknown')
        result["metadata"]["entities_count"] = len(list(msp))
        
        # 解析实体
        entities = []
        for entity in msp:
            entity_info = self._extract_entity_info(entity)
            if entity_info:
                entities.append(entity_info)
        
        result["entities"] = entities
        
        # 分类实体
        self._classify_entities(result)
        
        # 单位标准化
        result["standardized_units"] = self._standardize_units(doc)
        
        result["success"] = True
        return result
    
    def _parse_with_dxfgrabber(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """使用dxfgrabber解析DXF"""
        dxf = dxfgrabber.readfile(str(file_path))
        
        # 获取文件信息
        result["metadata"]["dxf_version"] = dxf.dxfversion
        result["metadata"]["encoding"] = dxf.encoding
        result["metadata"]["entities_count"] = len(dxf.entities)
        
        # 解析实体
        entities = []
        for entity in dxf.entities:
            if hasattr(entity, 'dxftype'):
                entity_info = {
                    "type": entity.dxftype,
                    "layer": getattr(entity, 'layer', ''),
                    "color": getattr(entity, 'color', 0)
                }
                
                # 提取位置信息
                if hasattr(entity, 'start') and entity.start:
                    entity_info["start"] = list(entity.start)
                if hasattr(entity, 'end') and entity.end:
                    entity_info["end"] = list(entity.end)
                if hasattr(entity, 'center') and entity.center:
                    entity_info["center"] = list(entity.center)
                
                entities.append(entity_info)
        
        result["entities"] = entities
        self._classify_entities(result)
        
        result["success"] = True
        return result
    
    def _parse_dxf_as_text(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """简单的文本解析（最基础的实现）"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 查找基本实体
            entities = []
            lines = content.split('\n')
            
            current_section = None
            for line in lines:
                line = line.strip()
                if line == 'ENTITIES':
                    current_section = 'ENTITIES'
                    continue
                elif line == 'ENDSEC':
                    current_section = None
                    continue
                
                if current_section == 'ENTITIES':
                    if line == 'LINE':
                        entities.append({"type": "LINE", "basic": True})
                    elif line == 'CIRCLE':
                        entities.append({"type": "CIRCLE", "basic": True})
                    elif line == 'TEXT':
                        entities.append({"type": "TEXT", "basic": True})
            
            result["entities"] = entities
            result["metadata"]["parsing_method"] = "text_based_fallback"
            result["metadata"]["basic_entities_found"] = len(entities)
            
            result["success"] = True
            return result
            
        except Exception as e:
            result["errors"].append(f"文本解析失败: {str(e)}")
            return result
    
    def _extract_entity_info(self, entity) -> Optional[Dict[str, Any]]:
        """提取实体信息"""
        entity_info = {
            "type": entity.dxftype(),
            "layer": getattr(entity, 'dxf.layer', '0'),
            "color": getattr(entity, 'dxf.color', 0)
        }
        
        # 提取位置和尺寸信息
        if hasattr(entity, 'dxf'):
            if hasattr(entity.dxf, 'start'):
                entity_info["start"] = [entity.dxf.start.x, entity.dxf.start.y, entity.dxf.start.z]
            if hasattr(entity.dxf, 'end'):
                entity_info["end"] = [entity.dxf.end.x, entity.dxf.end.y, entity.dxf.end.z]
            if hasattr(entity.dxf, 'center'):
                entity_info["center"] = [entity.dxf.center.x, entity.dxf.center.y, entity.dxf.center.z]
            if hasattr(entity.dxf, 'radius'):
                entity_info["radius"] = entity.dxf.radius
            if hasattr(entity.dxf, 'text'):
                entity_info["text"] = entity.dxf.text
        
        return entity_info
    
    def _classify_entities(self, result: Dict[str, Any]):
        """分类实体"""
        entities = result.get("entities", [])
        
        # 识别管道
        pipes = []
        for entity in entities:
            if entity.get("type") == "LINE":
                # 检查是否是管道（基于图层名称或尺寸）
                if self._is_pipe_entity(entity):
                    pipes.append(entity)
            elif entity.get("type") == "CIRCLE":
                # 检查是否是管道组件
                if self._is_pipe_component(entity):
                    pipes.append(entity)
        
        result["pipes"] = pipes
        
        # 识别设备
        equipment = []
        for entity in entities:
            if self._is_equipment_entity(entity):
                equipment.append(entity)
        
        result["equipment"] = equipment
        
        # 提取标注
        annotations = []
        for entity in entities:
            if entity.get("type") == "TEXT":
                annotations.append(entity)
        
        result["annotations"] = annotations
    
    def _is_pipe_entity(self, entity: Dict[str, Any]) -> bool:
        """判断是否是管道实体"""
        layer_name = entity.get("layer", "").lower()
        entity_type = entity.get("type", "").lower()
        
        # 管道识别规则
        pipe_keywords = ["pipe", "管线", "管道", "flow", "流体"]
        
        # 检查图层名称
        for keyword in pipe_keywords:
            if keyword in layer_name:
                return True
        
        # 检查实体的起止点
        if entity_type == "line":
            start = entity.get("start", [0, 0, 0])
            end = entity.get("end", [0, 0, 0])
            
            # 计算长度
            import math
            length = math.sqrt(
                (end[0] - start[0])**2 + 
                (end[1] - start[1])**2 + 
                (end[2] - start[2])**2
            )
            
            # 长直线可能是管道
            if length > 100:  # 假设单位是mm
                return True
        
        return False
    
    def _is_pipe_component(self, entity: Dict[str, Any]) -> bool:
        """判断是否是管道组件（阀门、三通等）"""
        layer_name = entity.get("layer", "").lower()
        
        # 组件识别关键词
        component_keywords = ["valve", "阀门", "fitting", "配件", "tee", "三通", "elbow", "弯头"]
        
        for keyword in component_keywords:
            if keyword in layer_name:
                return True
        
        return False
    
    def _is_equipment_entity(self, entity: Dict[str, Any]) -> bool:
        """判断是否是设备实体"""
        layer_name = entity.get("layer", "").lower()
        
        # 设备识别关键词
        equipment_keywords = ["pump", "泵", "reactor", "反应器", "tank", "罐", "heat", "换热"]
        
        for keyword in equipment_keywords:
            if keyword in layer_name:
                return True
        
        return False
    
    def _standardize_units(self, doc) -> Dict[str, Any]:
        """单位标准化"""
        try:
            # 获取原始单位
            insunits = doc.header.get('$INSUNITS', 1)  # 默认值1对应mm
            angunits = doc.header.get('$ANGUNITS', 1)  # 角度单位
            
            unit_mapping = {
                0: "unitless",
                1: "inches",
                2: "feet", 
                3: "miles",
                4: "mm",
                5: "m",
                6: "km",
                7: "microinches",
                8: "mils",
                9: "yards",
                10: "angstroms",
                11: "nanometers",
                12: "microns",
                13: "decimeters",
                14: "centimeters"
            }
            
            standardized = {
                "original_linear_unit": unit_mapping.get(insunits, "unknown"),
                "original_angular_unit": "degrees" if angunits == 0 else "radians",
                "standardized_to": "mm",
                "conversion_factor": 1.0
            }
            
            return standardized
            
        except Exception as e:
            logging.warning(f"单位标准化失败: {e}")
            return {"error": str(e)}
    
    def _parse_dwg_file(self, file_path: Path, result: Dict[str, Any]) -> Dict[str, Any]:
        """解析DWG文件"""
        # DWG文件需要专门的库支持，这里提供基础支持
        result["errors"].append("DWG文件解析需要额外的依赖库")
        result["metadata"]["dwg_support"] = "limited"
        
        # 尝试作为DXF处理（某些DWG文件可以）
        if file_path.with_suffix('.dxf').exists():
            return self._parse_dxf_file(file_path.with_suffix('.dxf'), result)
        
        return result
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强PDF解析器
集成化学实体识别、工艺参数提取和智能分析功能
"""

import re
import json
import fitz  # PyMuPDF
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageEnhance
import pytesseract
import io
import base64
import logging
from pathlib import Path
from datetime import datetime

from .base_parser import BaseDocumentParser
from .chemical_entity_recognizer import ChemicalEntityRecognizer, ChemicalEntity, ChemicalReaction
from .pdf_parser import PDFParser
from ...schemas.document import DocumentParseResult, ProcessParameter, ChemicalEntity as SchemaChemicalEntity

class EnhancedPDFParser(PDFParser):
    """增强的PDF解析器,集成化学实体识别"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.chemical_recognizer = ChemicalEntityRecognizer()
        
        # 化工专业术语词典
        self.chemical_terms = {
            "反应器": ["反应器", "reactor", "反应罐", "搅拌反应器", "固定床反应器"],
            "换热器": ["换热器", "heat exchanger", "冷凝器", "蒸发器", "再沸器"],
            "泵": ["泵", "pump", "离心泵", "齿轮泵", "螺杆泵"],
            "储罐": ["储罐", "tank", "贮罐", "贮槽", "贮存罐"],
            "塔器": ["塔", "tower", "精馏塔", "吸收塔", "萃取塔"],
            "管道": ["管道", "pipe", "管线", "导管"],
            "阀门": ["阀门", "valve", "调节阀", "截止阀", "安全阀"],
            "仪表": ["仪表", "instrument", "传感器", "变送器", "控制器"],
        }
        
        # 工艺参数正则表达式增强
        self.enhanced_parameter_patterns = {
            "temperature": [
                # 温度范围
                re.compile(r'(\d+(?:\.\d+)?)\s*[-~至]\s*(\d+(?:\.\d+)?)\s*°?[CcFfK]?\s*[-至]?\s*(\d+(?:\.\d+)?)\s*°?[CcFfK]?'),
                # 单一温度
                re.compile(r'(\d+(?:\.\d+)?)\s*°?[CcFfK]?'),
                # 特殊温度条件
                re.compile(r'(室温|room temperature|RT|回流|reflux|冰浴|ice bath|高温|high temp|低温|low temp)'),
            ],
            "pressure": [
                # 压力范围
                re.compile(r'(\d+(?:\.\d+)?)\s*[-~至]\s*(\d+(?:\.\d+)?)\s*(?:atm|bar|Pa|kPa|MPa|mmHg|torr|psi)'),
                # 单一压力
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:atm|bar|Pa|kPa|MPa|mmHg|torr|psi)'),
                # 特殊压力条件
                re.compile(r'(常压|atmospheric|减压|reduced|加压|pressurized|真空|vacuum)'),
            ],
            "flow_rate": [
                # 流量范围
                re.compile(r'(\d+(?:\.\d+)?)\s*[-~至]\s*(\d+(?:\.\d+)?)\s*(?:L|ml|m3|ft3|g|kg|t)\s*[/]\s*(?:h|min|s|day|year)?'),
                # 单一流量
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:L|ml|m3|ft3|g|kg|t)\s*[/]\s*(?:h|min|s|day|year)?'),
                # 特殊流量条件
                re.compile(r'(流量|flow rate|流速|velocity|流率|flow)'),
            ],
            "concentration": [
                # 浓度范围
                re.compile(r'(\d+(?:\.\d+)?)\s*[-~至]\s*(\d+(?:\.\d+)?)\s*%'),
                # 摩尔浓度
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:mol|M)\s*/\s*L'),
                # 质量浓度
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:g|mg|kg)\s*/\s*L'),
                # 百分比
                re.compile(r'(\d+(?:\.\d+)?)\s*%'),
            ],
        }

    def parse(self, file_path: str, options: Optional[Dict] = None) -> DocumentParseResult:
        """解析PDF文件并返回增强结果"""
        try:
            # 执行基础PDF解析
            base_result = super().parse(file_path, options)
            
            # 获取完整文本
            full_text = self._extract_all_text(file_path)
            
            # 提取化学实体
            chemical_entities = self.chemical_recognizer.extract_chemical_entities(full_text)
            
            # 提取化学反应
            chemical_reactions = self.chemical_recognizer.extract_chemical_reactions(full_text)
            
            # 增强工艺参数提取
            enhanced_parameters = self._extract_enhanced_parameters(full_text)
            
            # 提取设备信息
            equipment_info = self._extract_equipment_info(full_text)
            
            # 提取配方信息
            recipe_info = self._extract_recipe_info(full_text)
            
            # 构建增强结果
            enhanced_result = self._build_enhanced_result(
                base_result=base_result,
                chemical_entities=chemical_entities,
                chemical_reactions=chemical_reactions,
                enhanced_parameters=enhanced_parameters,
                equipment_info=equipment_info,
                recipe_info=recipe_info,
                full_text=full_text
            )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Enhanced PDF parsing error: {e}")
            return DocumentParseResult(
                success=False,
                error=str(e),
                metadata={"parser_type": "enhanced_pdf"}
            )

    def _extract_all_text(self, file_path: str) -> str:
        """提取PDF中的所有文本"""
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_parts.append(text)
            doc.close()
            
            return "\n".join(text_parts)
        except Exception as e:
            self.logger.warning(f"Text extraction error: {e}")
            return ""

    def _extract_enhanced_parameters(self, text: str) -> List[ProcessParameter]:
        """增强的工艺参数提取"""
        parameters = []
        
        for param_type, patterns in self.enhanced_parameter_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        # 处理范围值
                        if len(match) >= 2:
                            param = ProcessParameter(
                                parameter_type=param_type,
                                value=float(match[0]),
                                unit=self._extract_unit(param_type, match[0]),
                                min_value=float(match[0]),
                                max_value=float(match[1]) if len(match) > 1 else None,
                                confidence=0.8,
                                source="enhanced_extraction"
                            )
                        else:
                            param = ProcessParameter(
                                parameter_type=param_type,
                                value=float(match[0]),
                                unit=self._extract_unit(param_type, match[0]),
                                confidence=0.7,
                                source="enhanced_extraction"
                            )
                    else:
                        # 处理单一值或文本条件
                        param = ProcessParameter(
                            parameter_type=param_type,
                            value=match,
                            unit=self._extract_unit(param_type, match),
                            confidence=0.6,
                            source="enhanced_extraction"
                        )
                    
                    parameters.append(param)
        
        return self._deduplicate_parameters(parameters)

    def _extract_equipment_info(self, text: str) -> Dict[str, List[str]]:
        """提取设备信息"""
        equipment = {}
        
        for equipment_type, terms in self.chemical_terms.items():
            found_equipment = []
            for term in terms:
                pattern = re.compile(rf'{re.escape(term)}[^。！？\n]*')
                matches = pattern.findall(text)
                found_equipment.extend([match.strip() for match in matches])
            
            if found_equipment:
                equipment[equipment_type] = list(set(found_equipment))
        
        return equipment

    def _extract_recipe_info(self, text: str) -> Dict[str, Any]:
        """提取配方信息"""
        recipe_info = {
            "ingredients": [],
            "quantities": [],
            "instructions": [],
            "yield": None,
            "time_required": None
        }
        
        # 提取原料和用量
        ingredient_patterns = [
            re.compile(r'(.{1,20})\s*[\::]\s*(\d+(?:\.\d+)?)\s*(g|kg|L|ml|mg)'),
            re.compile(r'取\s*(.{1,20})\s*(\d+(?:\.\d+)?)\s*(g|kg|L|ml|mg)'),
        ]
        
        for pattern in ingredient_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) >= 3:
                    ingredient, quantity, unit = match[0].strip(), match[1], match[2]
                    recipe_info["ingredients"].append(ingredient)
                    recipe_info["quantities"].append(f"{quantity} {unit}")
        
        # 提取步骤
        step_pattern = re.compile(r'(\d+[、.]\s*[^。！？\n]+)')
        steps = step_pattern.findall(text)
        recipe_info["instructions"] = steps[:10]  # 限制前10步
        
        # 提取产率
        yield_pattern = re.compile(r'产率[::]?\s*(\d+(?:\.\d+)?)\s*%')
        yield_match = yield_pattern.search(text)
        if yield_match:
            recipe_info["yield"] = float(yield_match.group(1))
        
        # 提取时间
        time_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(小时|hour|h|分钟|min|分钟)')
        time_match = time_pattern.search(text)
        if time_match:
            recipe_info["time_required"] = f"{time_match.group(1)} {time_match.group(2)}"
        
        return recipe_info

    def _extract_unit(self, param_type: str, value: str) -> str:
        """提取参数单位"""
        if isinstance(value, str):
            if "°" in value or "C" in value or "F" in value or "K" in value:
                return "°C"
            elif any(unit in value for unit in ["atm", "bar", "Pa", "kPa", "MPa", "mmHg"]):
                return "atm"
            elif any(unit in value for unit in ["L", "ml", "m³", "ft³"]):
                return "L"
            elif any(unit in value for unit in ["g", "kg", "t"]):
                return "g"
            elif "%" in value:
                return "%"
            elif "mol" in value or "M" in value:
                return "mol/L"
        
        # 默认单位
        defaults = {
            "temperature": "°C",
            "pressure": "atm", 
            "flow_rate": "L/h",
            "concentration": "mol/L"
        }
        return defaults.get(param_type, "")

    def _deduplicate_parameters(self, parameters: List[ProcessParameter]) -> List[ProcessParameter]:
        """去重工艺参数"""
        seen = set()
        deduplicated = []
        
        for param in parameters:
            key = (param.parameter_type, param.value, param.unit)
            if key not in seen:
                seen.add(key)
                deduplicated.append(param)
        
        return deduplicated

    def _build_enhanced_result(self, base_result: DocumentParseResult, 
                             chemical_entities: List[ChemicalEntity],
                             chemical_reactions: List[ChemicalReaction],
                             enhanced_parameters: List[ProcessParameter],
                             equipment_info: Dict[str, List[str]],
                             recipe_info: Dict[str, Any],
                             full_text: str) -> DocumentParseResult:
        """构建增强解析结果"""
        
        # 转换化学实体
        schema_entities = []
        for entity in chemical_entities:
            schema_entity = SchemaChemicalEntity(
                name=entity.name,
                formula=entity.formula,
                cas_number=entity.cas_number,
                concentration=entity.concentration,
                phase=entity.phase,
                entity_type=entity.entity_type,
                confidence=entity.confidence
            )
            schema_entities.append(schema_entity)
        
        # 合并所有工艺参数
        all_parameters = list(base_result.process_parameters) if base_result.process_parameters else []
        all_parameters.extend(enhanced_parameters)
        
        # 构建增强元数据
        enhanced_metadata = dict(base_result.metadata) if base_result.metadata else {}
        enhanced_metadata.update({
            "parser_type": "enhanced_pdf",
            "chemical_entities_count": len(chemical_entities),
            "chemical_reactions_count": len(chemical_reactions),
            "equipment_types_found": list(equipment_info.keys()),
            "recipe_detected": bool(recipe_info.get("ingredients")),
            "extraction_timestamp": datetime.now().isoformat()
        })
        
        return DocumentParseResult(
            success=True,
            content=base_result.content,
            metadata=enhanced_metadata,
            process_parameters=all_parameters,
            chemical_entities=schema_entities,
            equipment_info=equipment_info,
            recipe_info=recipe_info,
            text_content=full_text
        )

    def extract_chemical_safety_info(self, text: str) -> Dict[str, Any]:
        """提取化学品安全信息"""
        safety_info = {
            "hazards": [],
            "precautions": [],
            "first_aid": [],
            "storage": [],
            "handling": []
        }
        
        # 危险化学品识别
        hazard_patterns = [
            re.compile(r'(易燃|flammable|有毒|toxic|腐蚀|corrosive|爆炸|explosive)'),
            re.compile(r'(危险化学品|hazardous chemicals)'),
            re.compile(r'(GHS\d+|H\d+P\d+)'),
        ]
        
        for pattern in hazard_patterns:
            matches = pattern.findall(text)
            safety_info["hazards"].extend(matches)
        
        # 安全措施
        precaution_patterns = [
            re.compile(r'(佩戴.*?防护|wear.*?protection)'),
            re.compile(r'(避免.*?接触|avoid.*?contact)'),
            re.compile(r'(使用.*?通风|use.*?ventilation)'),
        ]
        
        for pattern in precaution_patterns:
            matches = pattern.findall(text)
            safety_info["precautions"].extend(matches)
        
        return safety_info

    def analyze_process_efficiency(self, parameters: List[ProcessParameter], 
                                 equipment: Dict[str, List[str]]) -> Dict[str, Any]:
        """分析工艺效率"""
        efficiency_analysis = {
            "temperature_efficiency": "normal",
            "pressure_efficiency": "normal", 
            "flow_efficiency": "normal",
            "equipment_utilization": {},
            "optimization_suggestions": []
        }
        
        # 温度效率分析
        temps = [p for p in parameters if p.parameter_type == "temperature"]
        if temps:
            avg_temp = sum(p.value for p in temps) / len(temps)
            if avg_temp > 200:
                efficiency_analysis["temperature_efficiency"] = "high_energy"
                efficiency_analysis["optimization_suggestions"].append("考虑降低反应温度以节约能源")
            elif avg_temp < 50:
                efficiency_analysis["temperature_efficiency"] = "low_reaction"
                efficiency_analysis["optimization_suggestions"].append("可能需要提高反应温度以提高转化率")
        
        # 设备利用率分析
        for eq_type, items in equipment.items():
            efficiency_analysis["equipment_utilization"][eq_type] = {
                "count": len(items),
                "efficiency_rating": "optimal" if len(items) > 0 else "underutilized"
            }
        
        return efficiency_analysis

# 注册解析器
BaseDocumentParser.register(EnhancedPDFParser)
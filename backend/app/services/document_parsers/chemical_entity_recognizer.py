#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化学实体识别器
用于识别和解析化工文档中的化学物质、反应过程和配方信息
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging

@dataclass
class ChemicalEntity:
    """化学实体数据类"""
    name: str
    formula: Optional[str] = None
    cas_number: Optional[str] = None
    concentration: Optional[Dict] = None
    phase: Optional[str] = None  # 固/液/气态
    purity: Optional[float] = None
    temperature: Optional[Dict] = None
    pressure: Optional[Dict] = None
    entity_type: str = "compound"  # compound, reagent, product, solvent
    confidence: float = 0.0

@dataclass
class ChemicalReaction:
    """化学反应数据类"""
    reactants: List[ChemicalEntity]
    products: List[ChemicalEntity]
    conditions: Dict
    catalyst: Optional[ChemicalEntity] = None
    reaction_type: Optional[str] = None
    yield_percentage: Optional[float] = None
    time: Optional[Dict] = None

class ChemicalEntityRecognizer:
    """化学实体识别器主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 常见化学物质字典（可扩展）
        self.common_chemicals = {
            "水": {"formula": "H2O", "cas": "7732-18-5", "phase": "liquid"},
            "乙醇": {"formula": "C2H5OH", "cas": "64-17-5", "phase": "liquid"},
            "甲醇": {"formula": "CH3OH", "cas": "67-56-1", "phase": "liquid"},
            "丙酮": {"formula": "C3H6O", "cas": "67-64-1", "phase": "liquid"},
            "苯": {"formula": "C6H6", "cas": "71-43-2", "phase": "liquid"},
            "甲苯": {"formula": "C7H8", "cas": "108-88-3", "phase": "liquid"},
            "乙酸": {"formula": "CH3COOH", "cas": "64-19-7", "phase": "liquid"},
            "氢氧化钠": {"formula": "NaOH", "cas": "1310-73-2", "phase": "solid"},
            "盐酸": {"formula": "HCl", "cas": "7647-01-0", "phase": "liquid"},
            "硫酸": {"formula": "H2SO4", "cas": "7664-93-9", "phase": "liquid"},
            "氯化钠": {"formula": "NaCl", "cas": "7647-14-5", "phase": "solid"},
            "碳酸钙": {"formula": "CaCO3", "cas": "471-34-1", "phase": "solid"},
            "铁": {"formula": "Fe", "cas": "7439-89-6", "phase": "solid"},
            "铜": {"formula": "Cu", "cas": "7440-50-8", "phase": "solid"},
            "铝": {"formula": "Al", "cas": "7429-90-5", "phase": "solid"},
        }
        
        # CAS号正则表达式
        self.cas_pattern = re.compile(r'\b\d{2,7}-\d{2}-\d\b')
        
        # 化学式正则表达式
        self.formula_pattern = re.compile(r'\b[A-Z][a-z]?\d*[A-Z]?[a-z]?\d*\b')
        
        # 浓度表达式模式
        self.concentration_patterns = [
            re.compile(r'(\d+(?:\.\d+)?)\s*%'),  # 百分比
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:g|mg|kg)/L'),  # 质量浓度
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:mol|M)/L'),  # 摩尔浓度
            re.compile(r'(\d+(?:\.\d+)?)\s*(?:ppm|ppb)'),  # 微量浓度
        ]
        
        # 反应条件模式
        self.condition_patterns = {
            "temperature": [
                re.compile(r'(\d+(?:\.\d+)?)\s*°?[CcFfK]?'),
                re.compile(r'室温|room temperature|RT'),
                re.compile(r'回流|reflux'),
                re.compile(r'冰浴|ice bath'),
            ],
            "pressure": [
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:atm|bar|Pa|kPa|mmHg|torr)'),
                re.compile(r'常压|atmospheric pressure'),
                re.compile(r'减压|reduced pressure'),
                re.compile(r'加压|increased pressure'),
            ],
            "time": [
                re.compile(r'(\d+(?:\.\d+)?)\s*(?:小时|hour|h|分钟|minute|min|秒|second|s)'),
                re.compile(r'过夜|overnight'),
            ]
        }

    def extract_chemical_entities(self, text: str) -> List[ChemicalEntity]:
        """从文本中提取化学实体"""
        entities = []
        
        # 提取化学名称
        chemical_names = self._extract_chemical_names(text)
        
        # 提取CAS号
        cas_numbers = self._extract_cas_numbers(text)
        
        # 提取化学式
        formulas = self._extract_chemical_formulas(text)
        
        # 提取浓度信息
        concentrations = self._extract_concentrations(text)
        
        # 组合信息创建实体
        for name in chemical_names:
            entity = ChemicalEntity(name=name, entity_type="compound")
            
            # 添加已知信息
            if name in self.common_chemicals:
                chem_info = self.common_chemicals[name]
                entity.formula = chem_info.get("formula")
                entity.cas_number = chem_info.get("cas")
                entity.phase = chem_info.get("phase")
                entity.confidence = 0.9
            else:
                entity.confidence = 0.6
            
            # 匹配CAS号
            for cas in cas_numbers:
                if self._is_related_to_chemical(cas, name, text):
                    entity.cas_number = cas
                    entity.confidence += 0.1
                    break
            
            # 匹配化学式
            for formula in formulas:
                if self._is_related_to_chemical(formula, name, text):
                    entity.formula = formula
                    entity.confidence += 0.1
                    break
            
            # 匹配浓度
            for conc in concentrations:
                if self._is_related_to_chemical(conc["value"], name, text):
                    entity.concentration = conc
                    entity.confidence += 0.1
                    break
            
            entities.append(entity)
        
        return self._deduplicate_entities(entities)

    def extract_chemical_reactions(self, text: str) -> List[ChemicalReaction]:
        """从文本中提取化学反应"""
        reactions = []
        
        # 寻找反应方程式模式
        reaction_patterns = [
            re.compile(r'([^→→>]+)\s*(?:→|→|>)\s*([^]+)'),  # A → B
            re.compile(r'([^=]+)\s*=\s*([^]+)'),  # A = B
        ]
        
        for pattern in reaction_patterns:
            matches = pattern.findall(text)
            for match in matches:
                reactants_text, products_text = match
                
                # 解析反应物和产物
                reactants = self._parse_chemical_list(reactants_text)
                products = self._parse_chemical_list(products_text)
                
                # 提取反应条件
                conditions = self._extract_reaction_conditions(text)
                
                reaction = ChemicalReaction(
                    reactants=reactants,
                    products=products,
                    conditions=conditions
                )
                
                reactions.append(reaction)
        
        return reactions

    def standardize_chemical_names(self, text: str) -> Dict[str, str]:
        """标准化化学名称"""
        standardized = {}
        
        for chem_name in self.common_chemicals.keys():
            # 查找不同写法的化学名称
            patterns = [
                chem_name,
                chem_name.lower(),
                chem_name.replace("（", "(").replace("）", ")"),
            ]
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    standardized[pattern] = chem_name
                    break
        
        return standardized

    def validate_chemical_data(self, entity: ChemicalEntity) -> Dict[str, bool]:
        """验证化学实体数据的有效性"""
        validation = {
            "name_valid": bool(entity.name and len(entity.name.strip()) > 0),
            "formula_valid": self._validate_formula(entity.formula) if entity.formula else False,
            "cas_valid": self._validate_cas_number(entity.cas_number) if entity.cas_number else False,
            "concentration_valid": self._validate_concentration(entity.concentration) if entity.concentration else False,
        }
        
        entity.confidence = sum(validation.values()) / len(validation) if any(validation.values()) else 0.0
        
        return validation

    def _extract_chemical_names(self, text: str) -> List[str]:
        """提取化学名称"""
        names = []
        
        # 查找常见化学物质
        for chem_name in self.common_chemicals.keys():
            if re.search(chem_name, text, re.IGNORECASE):
                names.append(chem_name)
        
        # 查找可能的化学名称模式（中文）
        chinese_chem_pattern = re.compile(r'[一二三四五六七八九十百千万]?[酸碱盐氧化物 hydroxide oxide]|[甲乙丙丁戊己庚辛壬癸][烷烯炔醇酚醛酮酸]')
        matches = chinese_chem_pattern.findall(text)
        names.extend(matches)
        
        return list(set(names))

    def _extract_cas_numbers(self, text: str) -> List[str]:
        """提取CAS号"""
        return self.cas_pattern.findall(text)

    def _extract_chemical_formulas(self, text: str) -> List[str]:
        """提取化学式"""
        formulas = self.formula_pattern.findall(text)
        
        # 过滤常见非化学式词汇
        filtered_formulas = []
        for formula in formulas:
            if len(formula) >= 2 and not formula.lower() in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she']:
                filtered_formulas.append(formula)
        
        return list(set(filtered_formulas))

    def _extract_concentrations(self, text: str) -> List[Dict]:
        """提取浓度信息"""
        concentrations = []
        
        for pattern in self.concentration_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    value = float(match[0])
                else:
                    value = float(match)
                
                concentrations.append({
                    "value": value,
                    "unit": self._extract_unit(pattern, text),
                    "type": self._determine_concentration_type(pattern)
                })
        
        return concentrations

    def _extract_reaction_conditions(self, text: str) -> Dict:
        """提取反应条件"""
        conditions = {}
        
        for condition_type, patterns in self.condition_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    conditions[condition_type] = matches
                    break
        
        return conditions

    def _parse_chemical_list(self, text: str) -> List[ChemicalEntity]:
        """解析化学物质列表"""
        entities = []
        
        # 按常见分隔符分割
        parts = re.split(r'[+，、;\s]+', text)
        
        for part in parts:
            part = part.strip()
            if part:
                entity = ChemicalEntity(name=part, confidence=0.5)
                entities.append(entity)
        
        return entities

    def _is_related_to_chemical(self, item: str, chemical_name: str, text: str) -> bool:
        """判断项目是否与化学物质相关"""
        # 检查在文本中的位置关系
        item_pos = text.find(item)
        name_pos = text.find(chemical_name)
        
        if item_pos != -1 and name_pos != -1:
            distance = abs(item_pos - name_pos)
            return distance < 50  # 50字符内的距离认为相关
        
        return False

    def _deduplicate_entities(self, entities: List[ChemicalEntity]) -> List[ChemicalEntity]:
        """去重化学实体"""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            key = (entity.name.lower(), entity.formula)
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)
        
        return deduplicated

    def _validate_formula(self, formula: str) -> bool:
        """验证化学式"""
        if not formula:
            return False
        
        # 基本化学式验证
        return bool(re.match(r'^[A-Z][a-z]?\d*$', formula) or 
                   re.match(r'^[A-Z][a-z]?\d*[A-Z]?[a-z]?\d*$', formula))

    def _validate_cas_number(self, cas_number: str) -> bool:
        """验证CAS号"""
        if not cas_number:
            return False
        
        return bool(self.cas_pattern.match(cas_number))

    def _validate_concentration(self, concentration: Dict) -> bool:
        """验证浓度信息"""
        if not concentration:
            return False
        
        return "value" in concentration and isinstance(concentration["value"], (int, float))

    def _extract_unit(self, pattern, text: str) -> str:
        """提取单位"""
        if "%" in text:
            return "%"
        elif "g/L" in text or "mg/L" in text:
            return "g/L"
        elif "mol/L" in text or "M" in text:
            return "mol/L"
        return ""

    def _determine_concentration_type(self, pattern) -> str:
        """确定浓度类型"""
        if "%" in str(pattern.pattern):
            return "percentage"
        elif "g" in str(pattern.pattern):
            return "mass_concentration"
        elif "mol" in str(pattern.pattern):
            return "molar_concentration"
        return "unknown"

    def to_dict(self, entity: ChemicalEntity) -> Dict:
        """将化学实体转换为字典"""
        return {
            "name": entity.name,
            "formula": entity.formula,
            "cas_number": entity.cas_number,
            "concentration": entity.concentration,
            "phase": entity.phase,
            "purity": entity.purity,
            "temperature": entity.temperature,
            "pressure": entity.pressure,
            "entity_type": entity.entity_type,
            "confidence": entity.confidence
        }

    def to_json(self, entity: ChemicalEntity) -> str:
        """将化学实体转换为JSON字符串"""
        return json.dumps(self.to_dict(entity), ensure_ascii=False, indent=2)


# 工厂函数
def create_chemical_recognizer() -> ChemicalEntityRecognizer:
    """创建化学实体识别器实例"""
    return ChemicalEntityRecognizer()
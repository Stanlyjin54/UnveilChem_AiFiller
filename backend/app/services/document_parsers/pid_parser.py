#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P&ID(工艺流程图)专用解析器

专门针对化工工艺流程图的设计，支持设备识别、管道网络、
仪表控制和工艺参数提取
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import BaseDocumentParser, ParserError

logger = logging.getLogger(__name__)

class PIDParser(BaseDocumentParser):
    """P&ID图纸解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pid', '.pfd', '.p&id', '.dwg', '.dxf']
        self.supported_mime_types = [
            'application/acad',
            'image/vnd.dwg',
            'image/vnd.dxf',
            'application/dxf'
        ]
        self.parser_name = "P&ID_Parser"
        self.capabilities = [
            "设备识别", "管道网络", "仪表控制", 
            "工艺参数", "设备规格", "安全阀", "控制系统"
        ]
        
        # P&ID专用设备和符号识别
        self.equipment_patterns = {
            "反应器": [r"反应器", r"REACTOR", r"R-\d+", r"^R$"],
            "泵": [r"泵", r"PUMP", r"P-\d+", r"^P$"],
            "换热器": [r"换热器", r"HEAT\s*EXCHANGER", r"E-\d+", r"^E$", r"换热", r"HEX"],
            "蒸馏塔": [r"蒸馏塔", r"DISTILLATION", r"COLUMN", r"T-\d+", r"^T$"],
            "储罐": [r"储罐", r"TANK", r"V-\d+", r"^V$", r"罐"],
            "压缩机": [r"压缩机", r"COMPRESSOR", r"C-\d+", r"^C$"],
            "安全阀": [r"安全阀", r"SAFETY\s*VALVE", r"SV-\d+", r"^SV$"],
            "控制阀": [r"控制阀", r"CONTROL\s*VALVE", r"CV-\d+", r"^CV$", r"调节阀"],
            "流量计": [r"流量计", r"FLOW\s*METER", r"FE-\d+", r"^FE$", r"FIC", r"FIC-\d+"],
            "压力表": [r"压力表", r"PRESSURE", r"PG-\d+", r"^PG$", r"PIC", r"PIC-\d+"],
            "温度计": [r"温度表", r"TEMPERATURE", r"TG-\d+", r"^TG$", r"TIC", r"TIC-\d+"]
        }
        
        # 管道规格识别
        self.pipe_specs = {
            "材质": [r"碳钢", r"不锈钢",r"合金", r"CS", r"SS", r"PVC", r"PE"],
            "尺寸": [r"DN\d+", r"NPS?\d+", r"\d+寸", r"\d+\"", r"DN\s*\d+"],
            "压力等级": [r"PN\d+", r"CL\d+", r"Class\s*\d+", r"压力\d+"],
            "保温": [r"保温", r"INSULATED", r"伴热", r"HEAT\s*TRACED"]
        }
        
        # 工艺参数识别模式
        self.parameter_patterns = {
            "温度": [r"(\d+\.?\d*)\s*°C", r"TEMP\s*[:=]\s*(\d+\.?\d*)", r"温度\s*[:=]\s*(\d+\.?\d*)"],
            "压力": [r"(\d+\.?\d*)\s*MPa", r"(\d+\.?\d*)\s*bar", r"(\d+\.?\d*)\s*psi", r"PRESS\s*[:=]\s*(\d+\.?\d*)"],
            "流量": [r"(\d+\.?\d*)\s*m³/h", r"(\d+\.?\d*)\s*L/h", r"FLOW\s*[:=]\s*(\d+\.?\d*)"],
            "液位": [r"(\d+\.?\d*)\s*%", r"LEVEL\s*[:=]\s*(\d+\.?\d*)", r"液位\s*[:=]\s*(\d+\.?\d*)"],
            "密度": [r"(\d+\.?\d*)\s*kg/m³", r"DENSITY\s*[:=]\s*(\d+\.?\d*)"],
            "浓度": [r"(\d+\.?\d*)\s*%", r"(\d+\.?\d*)\s*wt%", r"CONC\s*[:=]\s*(\d+\.?\d*)"]
        }
        
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析P&ID文件"""
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_extensions:
            return False
        
        # 检查文件是否存在
        if not Path(file_path).exists():
            return False
            
        return True
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析P&ID图纸文件"""
        try:
            start_time = self._start_parsing()
            
            # 初始化结果
            result = {
                "file_path": str(file_path),
                "file_name": Path(file_path).name,
                "file_type": "P&ID",
                "parser_used": self.parser_name,
                "parsing_capabilities": self.capabilities,
                "parse_time": 0,
                "success": True
            }
            
            # 根据文件类型选择解析方法
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.dwg', '.dxf']:
                result.update(self._parse_cad_pid(file_path))
            elif file_ext in ['.pid', '.pfd', '.p&id']:
                result.update(self._parse_pid_document(file_path))
            else:
                raise ParserError(f"不支持的P&ID文件格式: {file_ext}")
            
            # 提取P&ID专用信息
            result.update(self._extract_pid_specific_info(result))
            
            # 添加统计信息
            result["parse_time"] = self._end_parsing(start_time)
            result["statistics"] = self._generate_statistics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"P&ID解析失败 {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "file_name": Path(file_path).name,
                "file_type": "P&ID",
                "parser_used": self.parser_name,
                "success": False,
                "error": str(e),
                "parse_time": 0
            }
    
    def _parse_cad_pid(self, file_path: str) -> Dict[str, Any]:
        """解析CAD格式的P&ID文件"""
        try:
            # 尝试使用CAD解析器的功能
            from .cad_parser import CADParser
            cad_parser = CADParser()
            
            if cad_parser.can_parse(file_path):
                cad_result = cad_parser.parse(file_path)
                
                return {
                    "text_content": cad_result.get("text_content", ""),
                    "entities": cad_result.get("entities", []),
                    "images": cad_result.get("images", []),
                    "tables": cad_result.get("tables", []),
                    "metadata": cad_result.get("metadata", {}),
                    "parsing_method": "CAD_Enhanced"
                }
            else:
                # 基础图像处理
                return self._parse_image_pid(file_path)
                
        except Exception as e:
            logger.warning(f"CAD解析P&ID失败，使用图像解析: {e}")
            return self._parse_image_pid(file_path)
    
    def _parse_pid_document(self, file_path: str) -> Dict[str, Any]:
        """解析P&ID文档文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "text_content": content,
                "parsing_method": "Text_Document"
            }
            
        except Exception as e:
            # 如果读取失败，尝试图像处理
            logger.warning(f"P&ID文档解析失败,使用图像解析: {e}")
            return self._parse_image_pid(file_path)
    
    def _parse_image_pid(self, file_path: str) -> Dict[str, Any]:
        """使用图像处理解析P&ID"""
        try:
            # 读取图像
            image = cv2.imread(file_path)
            if image is None:
                raise ParserError("无法读取P&ID图像文件")
            
            # 图像预处理
            processed_image = self._preprocess_pid_image(image)
            
            # OCR文字识别
            text_content = self._extract_text_from_image(processed_image)
            
            # 设备识别
            equipment = self._identify_equipment(processed_image, text_content)
            
            # 管道识别
            pipelines = self._identify_pipelines(processed_image, text_content)
            
            return {
                "text_content": text_content,
                "equipment": equipment,
                "pipelines": pipelines,
                "images": [f"processed_{Path(file_path).name}"],
                "parsing_method": "Image_Processing"
            }
            
        except Exception as e:
            logger.error(f"图像解析P&ID失败: {e}")
            raise ParserError(f"图像解析失败: {str(e)}")
    
    def _preprocess_pid_image(self, image: np.ndarray) -> np.ndarray:
        """预处理P&ID图像"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 噪声去除
        denoised = cv2.medianBlur(gray, 3)
        
        # 对比度增强
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(denoised)
        
        # 二值化
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _extract_text_from_image(self, image: np.ndarray) -> str:
        """从图像中提取文字"""
        try:
            import pytesseract
            # OCR识别
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            return text
        except ImportError:
            logger.warning("pytesseract未安装,跳过OCR识别")
            return ""
        except Exception as e:
            logger.warning(f"OCR识别失败: {e}")
            return ""
    
    def _identify_equipment(self, image: np.ndarray, text_content: str) -> List[Dict[str, Any]]:
        """识别设备"""
        equipment = []
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查每种设备类型
            for equip_type, patterns in self.equipment_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        equipment.append({
                            "type": equip_type,
                            "name": line,
                            "detected_by": "text",
                            "confidence": 0.8
                        })
                        break
        
        # 使用轮廓检测辅助设备识别
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 10000:  # 适中的区域大小
                # 简化轮廓
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # 根据形状特征推测设备类型
                equip_type = self._classify_equipment_shape(approx)
                if equip_type:
                    equipment.append({
                        "type": equip_type,
                        "shape": "detected",
                        "area": area,
                        "detected_by": "shape",
                        "confidence": 0.6
                    })
        
        return equipment
    
    def _classify_equipment_shape(self, approx: np.ndarray) -> Optional[str]:
        """根据形状特征分类设备"""
        vertices = len(approx)
        
        if vertices == 4:
            return "rectangular_equipment"  # 可能是方形设备
        elif vertices >= 6:
            return "circular_equipment"  # 可能是圆形设备（储罐、换热器等）
        else:
            return None
    
    def _identify_pipelines(self, image: np.ndarray, text_content: str) -> List[Dict[str, Any]]:
        """识别管道网络"""
        pipelines = []
        
        # 使用霍夫变换检测直线
        lines = cv2.HoughLinesP(image, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                pipelines.append({
                    "type": "pipe",
                    "start_point": (x1, y1),
                    "end_point": (x2, y2),
                    "detected_by": "line_detection",
                    "confidence": 0.7
                })
        
        # 解析管道规格信息
        pipe_specs = self._parse_pipe_specifications(text_content)
        pipelines.extend(pipe_specs)
        
        return pipelines
    
    def _parse_pipe_specifications(self, text_content: str) -> List[Dict[str, Any]]:
        """解析管道规格信息"""
        specs = []
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析管道规格
            for spec_type, patterns in self.pipe_specs.items():
                for pattern in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        specs.append({
                            "type": "pipe_specification",
                            "spec_type": spec_type,
                            "value": match.group(0),
                            "context": line,
                            "detected_by": "text"
                        })
                        break
        
        return specs
    
    def _extract_pid_specific_info(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """提取P&ID专用信息"""
        pid_info = {
            "control_loops": [],
            "safety_systems": [],
            "instrumentation": [],
            "piping_network": {},
            "equipment_layout": {},
            "process_parameters": {},
            "design_specifications": {}
        }
        
        text_content = result.get("text_content", "")
        if not text_content:
            return pid_info
        
        # 解析控制回路
        pid_info["control_loops"] = self._parse_control_loops(text_content)
        
        # 解析安全系统
        pid_info["safety_systems"] = self._parse_safety_systems(text_content)
        
        # 解析仪表系统
        pid_info["instrumentation"] = self._parse_instrumentation(text_content)
        
        # 解析工艺参数
        pid_info["process_parameters"] = self._parse_process_parameters(text_content)
        
        # 解析设计规格
        pid_info["design_specifications"] = self._parse_design_specs(text_content)
        
        return pid_info
    
    def _parse_control_loops(self, text_content: str) -> List[Dict[str, Any]]:
        """解析控制回路"""
        loops = []
        
        # 查找控制回路标识
        loop_patterns = [
            r"FIC-?\d+",  # 流量控制
            r"PIC-?\d+",  # 压力控制
            r"TIC-?\d+",  # 温度控制
            r"LIC-?\d+",  # 液位控制
        ]
        
        for pattern in loop_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                loops.append({
                    "loop_id": match,
                    "loop_type": self._classify_control_loop(match),
                    "detected_by": "pattern_matching"
                })
        
        return loops
    
    def _classify_control_loop(self, loop_id: str) -> str:
        """分类控制回路类型"""
        if loop_id.upper().startswith("FIC"):
            return "流量控制"
        elif loop_id.upper().startswith("PIC"):
            return "压力控制"
        elif loop_id.upper().startswith("TIC"):
            return "温度控制"
        elif loop_id.upper().startswith("LIC"):
            return "液位控制"
        else:
            return "未知控制"
    
    def _parse_safety_systems(self, text_content: str) -> List[Dict[str, Any]]:
        """解析安全系统"""
        safety_systems = []
        
        safety_keywords = ["安全阀", "泄压阀", "紧急停车", "安全联锁", "PSV", "SV", "ESD"]
        
        for keyword in safety_keywords:
            if keyword.lower() in text_content.lower():
                safety_systems.append({
                    "system_type": "safety_device",
                    "keyword": keyword,
                    "detected_by": "keyword_matching"
                })
        
        return safety_systems
    
    def _parse_instrumentation(self, text_content: str) -> List[Dict[str, Any]]:
        """解析仪表系统"""
        instruments = []
        
        # 仪表标识符模式
        instrument_patterns = [
            r"[A-Z]{2}\d+",  # 标准仪表标识
            r"PT-\d+",       # 压力变送器
            r"TT-\d+",       # 温度变送器
            r"FT-\d+",       # 流量变送器
            r"LT-\d+",       # 液位变送器
        ]
        
        for pattern in instrument_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                instruments.append({
                    "instrument_id": match,
                    "instrument_type": self._classify_instrument(match),
                    "detected_by": "pattern_matching"
                })
        
        return instruments
    
    def _classify_instrument(self, instrument_id: str) -> str:
        """分类仪表类型"""
        if instrument_id.upper().startswith("PT"):
            return "压力变送器"
        elif instrument_id.upper().startswith("TT"):
            return "温度变送器"
        elif instrument_id.upper().startswith("FT"):
            return "流量变送器"
        elif instrument_id.upper().startswith("LT"):
            return "液位变送器"
        else:
            return "通用仪表"
    
    def _parse_process_parameters(self, text_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """解析工艺参数"""
        parameters = {}
        
        for param_type, patterns in self.parameter_patterns.items():
            parameters[param_type] = []
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    value = match.group(1) if match.groups() else match.group(0)
                    parameters[param_type].append({
                        "value": value,
                        "context": match.string,
                        "position": match.span(),
                        "detected_by": "pattern_matching"
                    })
        
        return parameters
    
    def _parse_design_specs(self, text_content: str) -> Dict[str, List[Dict[str, Any]]]:
        """解析设计规格"""
        specs = {}
        
        # 设计规格模式
        design_patterns = {
            "设计压力": r"设计压力[::]\s*(\d+\.?\d*)\s*MPa",
            "设计温度": r"设计温度[::]\s*(\d+\.?\d*)\s*°C",
            "材质等级": r"材质[::]\s*([A-Za-z0-9]+)",
            "焊缝系数": r"焊缝系数[::]\s*(\d+\.?\d*)",
            "腐蚀余量": r"腐蚀余量[::]\s*(\d+\.?\d*)\s*mm"
        }
        
        for spec_type, pattern in design_patterns.items():
            specs[spec_type] = []
            matches = re.finditer(pattern, text_content, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.groups() else match.group(0)
                specs[spec_type].append({
                    "value": value,
                    "context": match.string,
                    "position": match.span(),
                    "detected_by": "pattern_matching"
                })
        
        return specs
    
    def _generate_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成解析统计信息"""
        stats = {
            "equipment_count": 0,
            "pipeline_count": 0,
            "control_loop_count": 0,
            "instrument_count": 0,
            "parameter_count": 0,
            "safety_system_count": 0
        }
        
        # 统计设备数量
        equipment = result.get("equipment", [])
        stats["equipment_count"] = len(equipment)
        
        # 统计管道数量
        pipelines = result.get("pipelines", [])
        stats["pipeline_count"] = len(pipelines)
        
        # 统计控制回路
        control_loops = result.get("control_loops", [])
        stats["control_loop_count"] = len(control_loops)
        
        # 统计仪表
        instruments = result.get("instrumentation", [])
        stats["instrument_count"] = len(instruments)
        
        # 统计参数
        parameters = result.get("process_parameters", {})
        stats["parameter_count"] = sum(len(values) for values in parameters.values())
        
        # 统计安全系统
        safety_systems = result.get("safety_systems", [])
        stats["safety_system_count"] = len(safety_systems)
        
        return stats

# 注册解析器
BaseDocumentParser.register(PIDParser)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像解析器 - 集成PaddleOCR和Tesseract
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 依赖导入
try:
    from PIL import Image, ImageEnhance
    import pytesseract
    TESSERACT_AVAILABLE = True
    
    # 自动检测 Tesseract 路径
    import shutil
    tesseract_cmd = shutil.which('tesseract')
    if not tesseract_cmd:
        # 尝试常见安装路径
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(Path.home().name),
        ]
        for path in possible_paths:
            if Path(path).exists():
                tesseract_cmd = path
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                logging.info(f"找到 Tesseract: {tesseract_cmd}")
                break
    elif tesseract_cmd:
        logging.info(f"使用系统 Tesseract: {tesseract_cmd}")
    else:
        logging.warning("未找到 Tesseract 可执行文件")
        TESSERACT_AVAILABLE = False
        
except ImportError:
    TESSERACT_AVAILABLE = False
    Image = None
    ImageEnhance = None
    logging.warning("Tesseract依赖缺失,请安装pillow, pytesseract")

# 导入PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logging.warning("PaddleOCR依赖缺失,请安装paddleocr")

from . import BaseDocumentParser

class ImageParser(BaseDocumentParser):
    """图像文档解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        self.parser_name = "IMAGE_PARSER_V1"
        self.resource_level = "low"  # 设置资源等级（改为low，对所有版本开放）
        
        # 初始化PaddleOCR - 支持中英文混合识别
        self.ocr = None
        if PADDLEOCR_AVAILABLE:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True)
                logging.info("PaddleOCR初始化成功（支持中英文混合识别）")
            except Exception as e:
                logging.warning(f"PaddleOCR初始化失败: {e}")
                self.ocr = None
    
    def can_parse(self, file_path: Path) -> bool:
        """检查是否是图像文件"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """解析图像文件"""
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
            # 方法1: 尝试使用PaddleOCR进行高精度OCR
            if self.ocr:
                paddle_result = self._extract_text_with_paddleocr(file_path)
                if paddle_result["success"]:
                    result.update(paddle_result)
                    result["success"] = True
            
            # 方法2: 如果PaddleOCR不可用或失败，尝试Tesseract
            if not result["success"] and TESSERACT_AVAILABLE:
                tesseract_result = self._extract_text_with_tesseract(file_path)
                if tesseract_result["success"]:
                    result.update(tesseract_result)
                    result["success"] = True
            
            # 提取参数
            if result["text_content"]:
                result["parameters"] = self._extract_parameters(result["text_content"])
            
        except Exception as e:
            result["errors"].append(f"图像解析失败: {str(e)}")
            logging.error(f"图像解析错误: {e}")
        
        return result
    
    def _extract_text_with_paddleocr(self, file_path: Path) -> Dict[str, Any]:
        """使用PaddleOCR提取图像文本"""
        result = {
            "success": False,
            "method": "paddleocr_extraction",
            "text_content": "",
            "metadata": {
                "extraction_method": "PaddleOCR",
                "image_enhanced": False
            },
            "errors": []
        }
        
        try:
            if not self.ocr:
                result["errors"].append("PaddleOCR未初始化")
                return result
            
            # 使用PaddleOCR解析图像
            ocr_result = self.ocr.ocr(str(file_path), cls=True)
            
            if not ocr_result:
                result["errors"].append("PaddleOCR解析结果为空")
                return result
            
            # 处理OCR结果
            all_text = []
            for page in ocr_result:
                for line in page:
                    text = line[1][0]
                    if text.strip():
                        all_text.append(text)
            
            # 更新结果
            result["text_content"] = "\n".join(all_text)
            result["success"] = True
            
            logging.info(f"OCR提取成功，文本长度: {len(result['text_content'])}")
            logging.info(f"OCR提取文本: {result['text_content'][:200] if len(result['text_content']) > 200 else result['text_content']}")
            
        except Exception as e:
            result["errors"].append(f"PaddleOCR解析失败: {str(e)}")
            logging.error(f"PaddleOCR解析错误: {e}")
        
        return result
    
    def _extract_text_with_tesseract(self, file_path: Path) -> Dict[str, Any]:
        """使用Tesseract提取图像文本"""
        result = {
            "success": False,
            "method": "tesseract_extraction",
            "text_content": "",
            "metadata": {
                "extraction_method": "Tesseract",
                "image_enhanced": True
            },
            "errors": []
        }
        
        try:
            # 打开图像
            image = Image.open(str(file_path))
            
            # 增强图像
            enhanced_image = self._enhance_image_for_ocr(image)
            
            # 使用Tesseract提取文本
            text = pytesseract.image_to_string(enhanced_image, lang='chi_sim+eng')
            
            if text.strip():
                result["text_content"] = text
                result["success"] = True
            
            logging.info(f"Tesseract提取成功，文本长度: {len(result['text_content'])}")
            logging.info(f"Tesseract提取文本: {result['text_content'][:200] if len(result['text_content']) > 200 else result['text_content']}")
            
        except Exception as e:
            result["errors"].append(f"Tesseract解析失败: {str(e)}")
            logging.error(f"Tesseract解析错误: {e}")
        
        return result
    
    def _enhance_image_for_ocr(self, image) -> object:
        """增强图像以提高OCR识别率"""
        if ImageEnhance is None:
            return image
        
        # 转换为灰度
        if image.mode != 'L':
            image = image.convert('L')
        
        # 对比度增强
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # 降噪处理
        from PIL import ImageFilter
        image = image.filter(ImageFilter.MedianFilter())
        
        return image
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """从图像文本中提取工艺参数"""
        import re
        parameters = {}
        
        # 温度参数
        temp_patterns = [
            r'(?:温度|Temperature|TEMP)[:\s]*([\d.]+)\s*[°℃]?C?',
            r'([\d.]+)\s*[°℃](?:\s*温度|\s*Temperature)?',
            r'T\s*[=]\s*([\d.]+)\s*[°℃]?'
        ]
        
        # 压力参数
        pressure_patterns = [
            r'(?:压力|Pressure|PRESS)[:\s]*([\d.]+)\s*(?:MPa|kPa|Pa)?',
            r'([\d.]+)\s*(?:MPa|kPa|Pa)(?:\s*压力|\s*Pressure)?',
            r'P\s*[=]\s*([\d.]+)\s*(?:MPa|kPa|Pa)?'
        ]
        
        # 流量参数
        flow_patterns = [
            r'(?:流量|Flow|FLOW)[:\s]*([\d.]+)\s*(?:m³/h|L/min|kg/h)?',
            r'([\d.]+)\s*(?:m³/h|L/min|kg/h)(?:\s*流量|\s*Flow)?'
        ]
        
        # 提取各类参数
        for pattern_list, param_type in [
            (temp_patterns, "temperature"),
            (pressure_patterns, "pressure"),
            (flow_patterns, "flow")
        ]:
            values = []
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value = float(match.group(1))
                        # 验证数值合理性
                        if self._validate_parameter_value(param_type, value):
                            values.append({
                                "value": value,
                                "unit": self._extract_unit(match.group(0), param_type),
                                "context": match.group(0).strip(),
                                "position": match.span()
                            })
                    except (ValueError, IndexError):
                        continue
            
            if values:
                parameters[param_type] = values
        
        return parameters
    
    def _validate_parameter_value(self, param_type: str, value: float) -> bool:
        """验证参数值是否合理"""
        validation_rules = {
            "temperature": (-100, 1000),  # -100°C 到 1000°C
            "pressure": (0, 50),          # 0 到 50 MPa
            "flow": (0, 10000)            # 0 到 10000 m³/h
        }
        
        if param_type in validation_rules:
            min_val, max_val = validation_rules[param_type]
            return min_val <= value <= max_val
        
        return True
    
    def _extract_unit(self, text: str, param_type: str) -> str:
        """提取参数单位"""
        import re
        
        unit_patterns = {
            "temperature": [r'°C', r'℃', r'C(?![a-zA-Z])'],
            "pressure": [r'MPa', r'kPa', r'Pa'],
            "flow": [r'm³/h', r'L/min', r'kg/h']
        }
        
        if param_type in unit_patterns:
            for pattern in unit_patterns[param_type]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        # 默认单位
        default_units = {
            "temperature": "°C",
            "pressure": "MPa", 
            "flow": "m³/h"
        }
        
        return default_units.get(param_type, "")

# 更新以匹配增强的基类接口
BaseDocumentParser.register(ImageParser)
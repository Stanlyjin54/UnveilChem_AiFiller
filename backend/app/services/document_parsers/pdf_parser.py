#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF解析器 - 集成Apache Tika和PyPDF2
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 依赖导入（可选）
try:
    import pytesseract
    from PIL import Image, ImageEnhance
    import fitz  # PyMuPDF
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    Image = None
    ImageEnhance = None
    fitz = None
    logging.warning("PDF解析依赖缺失,请安装pymupdf, pillow, pytesseract")

# 导入Pix2Text
try:
    from pix2text import Pix2Text
    PIX2TEXT_AVAILABLE = True
except ImportError:
    PIX2TEXT_AVAILABLE = False
    logging.warning("Pix2Text依赖缺失,请安装pix2text")

from . import BaseDocumentParser

class PDFParser(BaseDocumentParser):
    """PDF文档解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        self.parser_name = "PDF_PARSER_V1"
        self.resource_level = "low"  # 设置资源等级 - low表示快速解析
        
        # 初始化Pix2Text
        self.p2t = None
        if PIX2TEXT_AVAILABLE:
            try:
                self.p2t = Pix2Text()
                logging.info("Pix2Text初始化成功")
            except Exception as e:
                logging.warning(f"Pix2Text初始化失败: {e}")
                self.p2t = None
    
    def can_parse(self, file_path: Path) -> bool:
        """检查是否是PDF文件"""
        return file_path.suffix.lower() == '.pdf'
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """解析PDF文件 - 优化版本：优先直接文本提取，成功后立即返回"""
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
            logging.info(f"[PDF解析] 开始解析文件: {file_path}")
            
            # 方法1: 优先直接文本提取 - PyMuPDF直接提取文本，速度最快
            logging.info("[PDF解析] 尝试方法1: 直接文本提取 (PyMuPDF)")
            text_result = self._extract_text_directly(file_path)
            if text_result["success"]:
                logging.info(f"[PDF解析] 直接文本提取成功! 提取文本长度: {len(text_result.get('text_content', ''))}")
                result.update(text_result)
                result["success"] = True
                # 成功后直接返回，不再尝试其他方法
                if result["text_content"]:
                    result["parameters"] = self._extract_parameters(result["text_content"])
                return result
            
            logging.warning(f"[PDF解析] 直接文本提取失败: {text_result.get('error', '未知错误')}")
            
            # 方法2: 如果直接提取失败，尝试OCR方法
            if not result["success"] and OCR_AVAILABLE:
                logging.info("[PDF解析] 尝试方法2: OCR文本提取")
                ocr_result = self._extract_text_via_ocr(file_path)
                if ocr_result["success"]:
                    logging.info(f"[PDF解析] OCR提取成功! 提取文本长度: {len(ocr_result.get('text_content', ''))}")
                    result.update(ocr_result)
                    result["success"] = True
                    if result["text_content"]:
                        result["parameters"] = self._extract_parameters(result["text_content"])
                    return result
                
                logging.warning(f"[PDF解析] OCR提取失败: {ocr_result.get('error', '未知错误')}")
            
            # 方法3: 如果有Pix2Text，尝试解析复杂PDF（包含表格、公式）
            if self.p2t and not result["success"]:
                logging.info("[PDF解析] 尝试方法3: Pix2Text解析")
                pix2text_result = self._extract_text_with_pix2text(file_path)
                if pix2text_result["success"]:
                    logging.info(f"[PDF解析] Pix2Text提取成功!")
                    if pix2text_result.get("tables"):
                        result["tables"] = pix2text_result["tables"]
                    if pix2text_result.get("text_content"):
                        result["text_content"] = pix2text_result["text_content"]
                    result["success"] = True
                    if result["text_content"]:
                        result["parameters"] = self._extract_parameters(result["text_content"])
                    return result
            
            logging.error(f"[PDF解析] 所有方法都失败，最终文本为空")
            
        except Exception as e:
            result["errors"].append(f"PDF解析失败: {str(e)}")
            logging.error(f"PDF解析错误: {e}")
        
        return result
    
    def _extract_text_directly(self, file_path: Path) -> Dict[str, Any]:
        """直接文本提取（更高效）"""
        result = {
            "success": False,
            "method": "direct_text_extraction",
            "text_content": "",
            "page_count": 0,
            "metadata": {}
        }
        
        try:
            # 使用PyMuPDF提取文本
            doc = fitz.open(str(file_path))
            result["page_count"] = doc.page_count
            
            all_text = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    all_text.append(f"=== 第{page_num + 1}页 ===\n{text}")
            
            doc.close()
            
            if all_text:
                result["text_content"] = "\n".join(all_text)
                result["success"] = True
                result["metadata"] = {
                    "extraction_method": "PyMuPDF_direct",
                    "pages_processed": result["page_count"]
                }
            
        except Exception as e:
            result["error"] = f"直接文本提取失败: {str(e)}"
        
        return result
    
    def _extract_text_via_ocr(self, file_path: Path) -> Dict[str, Any]:
        """通过OCR方法提取文本(备用方案)"""
        result = {
            "success": False,
            "method": "ocr_extraction",
            "text_content": "",
            "page_count": 0,
            "metadata": {}
        }
        
        try:
            doc = fitz.open(str(file_path))
            result["page_count"] = doc.page_count
            
            all_text = []
            for page_num in range(doc.page_count):
                # 渲染页面为图像
                mat = fitz.Matrix(2.0, 2.0)  # 2倍放大以提高OCR精度
                pix = doc.load_page(page_num).get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # 转换为PIL Image
                import io
                image = Image.open(io.BytesIO(img_data))
                
                # 增强图像
                image = self._enhance_image_for_ocr(image)
                
                # OCR识别
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                if text.strip():
                    all_text.append(f"=== 第{page_num + 1}页(OCR) ===\n{text}")
            
            doc.close()
            
            if all_text:
                result["text_content"] = "\n".join(all_text)
                result["success"] = True
                result["metadata"] = {
                    "extraction_method": "OCR_via_PyMuPDF",
                    "pages_processed": result["page_count"],
                    "ocr_enhanced": True
                }
            
        except Exception as e:
            result["error"] = f"OCR文本提取失败: {str(e)}"
        
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
        """提取工艺参数"""
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
    
    def _extract_images_and_ocr(self, file_path: Path) -> Dict[str, Any]:
        """从PDF中提取图片并进行OCR识别"""
        result = {
            "success": False,
            "method": "image_ocr_extraction",
            "text_content": "",
            "images": [],
            "image_count": 0,
            "ocr_processed_count": 0,
            "errors": []
        }
        
        try:
            doc = fitz.open(str(file_path))
            image_count = 0
            ocr_processed_count = 0
            image_texts = []
            images_list = []
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                
                # 提取页面中的图片
                images = page.get_images(full=True)
                
                for img_index, img in enumerate(images):
                    image_count += 1
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image["image"]
                    img_ext = base_image["ext"]
                    
                    # 转换为PIL Image
                    import io
                    image = Image.open(io.BytesIO(img_bytes))
                    
                    # 增强图像以提高OCR识别率
                    enhanced_image = self._enhance_image_for_ocr(image)
                    
                    # OCR识别
                    try:
                        ocr_text = pytesseract.image_to_string(enhanced_image, lang='chi_sim+eng')
                        if ocr_text.strip():
                            image_texts.append(f"=== 第{page_num + 1}页图片{img_index + 1} (OCR) ===\n{ocr_text}")
                            ocr_processed_count += 1
                    except Exception as ocr_error:
                        result["errors"].append(f"第{page_num + 1}页图片{img_index + 1} OCR识别失败: {str(ocr_error)}")
                        logging.warning(f"第{page_num + 1}页图片{img_index + 1} OCR识别失败: {ocr_error}")
                    
                    # 添加图片信息
                    images_list.append(f"page_{page_num + 1}_image_{img_index + 1}.{img_ext}")
            
            doc.close()
            
            if image_texts:
                result["text_content"] = "\n".join(image_texts)
            
            result["images"] = images_list
            result["image_count"] = image_count
            result["ocr_processed_count"] = ocr_processed_count
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"提取图片并OCR识别失败: {str(e)}")
            logging.error(f"提取图片并OCR识别失败: {e}")
        
        return result
    
    def _extract_text_with_pix2text(self, file_path: Path) -> Dict[str, Any]:
        """使用Pix2Text提取复杂PDF文本，特别是表格和公式"""
        result = {
            "success": False,
            "method": "pix2text_extraction",
            "text_content": "",
            "tables": [],
            "metadata": {
                "extraction_method": "Pix2Text",
                "pages_processed": 0
            },
            "errors": []
        }
        
        try:
            if not self.p2t:
                result["errors"].append("Pix2Text未初始化")
                return result
            
            # 使用Pix2Text解析PDF
            pdf_result = self.p2t.recognize_pdf(str(file_path))
            
            if not pdf_result:
                result["errors"].append("Pix2Text解析结果为空")
                return result
            
            # 处理解析结果
            all_text = []
            all_tables = []
            page_count = len(pdf_result)
            
            for page_num, page_data in enumerate(pdf_result):
                # 提取文本
                page_text = page_data.get("text", "")
                if page_text.strip():
                    all_text.append(f"=== 第{page_num + 1}页 ===\n{page_text}")
                
                # 提取表格
                page_tables = page_data.get("tables", [])
                if page_tables:
                    for table in page_tables:
                        all_tables.append({
                            "page": page_num + 1,
                            "table": table,
                            "confidence": table.get("confidence", 0.8)
                        })
            
            # 更新结果
            result["text_content"] = "\n".join(all_text)
            result["tables"] = all_tables
            result["metadata"]["pages_processed"] = page_count
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(f"Pix2Text解析失败: {str(e)}")
            logging.error(f"Pix2Text解析错误: {e}")
        
        return result

# 更新以匹配增强的基类接口
BaseDocumentParser.register(PDFParser)
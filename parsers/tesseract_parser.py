#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesseract OCR文字识别解析器

基于Tesseract OCR实现图像文档中的文字识别,支持多语言和化工专业术语识别。
这是实现需求文档7.4.1节中"OCR与图像识别"功能的核心组件。

特性:
- 支持多种图像格式 (PNG, JPEG, TIFF, BMP等)
- 多语言文字识别支持
- 化工专业术语增强识别
- 图像预处理和优化
- 批量图像处理
- 识别结果置信度评估

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

import io
import os
import re
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
import base64

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract OCR或PIL未安装. 请运行: pip install pytesseract pillow")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas未安装. 识别结果数据处理功能受限")

logger = logging.getLogger(__name__)

@dataclass
class OCRConfig:
    """OCR识别配置"""
    language: str = 'chi_sim+eng'  # 支持语言 'chi_sim'中文简体, 'eng'英文, 'chi_sim+eng'中英文混合
    psm: int = 6  # 页面分割模式 (0-13, 6为自动页面分割)
    oem: int = 3  # OCR引擎模式
    dpi: int = 300  # 图像DPI
    contrast: float = 1.2  # 对比度增强
    sharpness: float = 1.1  # 锐化程度
    whitelist: Optional[str] = None  # 允许的字符集
    blacklist: Optional[str] = None  # 禁止的字符集
    preprocessing: bool = True  # 是否启用图像预处理
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'language': self.language,
            'psm': self.psm,
            'oem': self.oem,
            'dpi': self.dpi,
            'contrast': self.contrast,
            'sharpness': self.sharpness,
            'whitelist': self.whitelist,
            'blacklist': self.blacklist,
            'preprocessing': self.preprocessing
        }

@dataclass
class BoundingBox:
    """文字边界框"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'x': self.x, 'y': self.y, 
            'width': self.width, 'height': self.height,
            'confidence': self.confidence
        }

@dataclass
class RecognizedText:
    """识别文本结果"""
    text: str
    confidence: float
    bbox: Optional[BoundingBox] = None
    line_number: int = 0
    word_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox.to_dict() if self.bbox else None,
            'line_number': self.line_number,
            'word_number': self.word_number
        }

@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    words: List[RecognizedText]
    lines: List[RecognizedText]
    processing_time: float
    image_path: str
    config: OCRConfig
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'words': [word.to_dict() for word in self.words],
            'lines': [line.to_dict() for line in self.lines],
            'processing_time': self.processing_time,
            'image_path': self.image_path,
            'config': self.config.to_dict(),
            'metadata': self.metadata
        }

class TesseractOCRParser:
    """
    Tesseract OCR文字识别解析器
    
    实现图像文档中的高精度文字识别，特别针对化工文档进行优化。
    支持中英文混合识别、化工专业术语识别等功能。
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        初始化Tesseract OCR解析器
        
        Args:
            tesseract_cmd: Tesseract可执行文件路径，为None时使用系统默认
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self._check_dependencies()
        
        # 默认配置
        self.default_config = OCRConfig()
        
        # 化工专业术语词典
        self.chemical_terms = {
            # 化工设备
            'reactor': '反应器',
            'separator': '分离器', 
            'distillation': '蒸馏',
            'extraction': '萃取',
            'crystallization': '结晶',
            'filtration': '过滤',
            'drying': '干燥',
            'heat_exchanger': '换热器',
            
            # 化工参数
            'temperature': '温度',
            'pressure': '压力',
            'flow_rate': '流量',
            'concentration': '浓度',
            'purity': '纯度',
            'conversion': '转化率',
            'selectivity': '选择性',
            'yield': '收率',
            'efficiency': '效率',
            
            # 化学单位
            'mole': '摩尔',
            'gram': '克',
            'liter': '升',
            'meter': '米',
            'second': '秒',
            'minute': '分钟',
            'hour': '小时',
            'day': '天',
            'pascal': '帕斯卡',
            'celsius': '摄氏度',
            'kelvin': '开尔文',
            
            # 化工工艺
            'batch': '间歇',
            'continuous': '连续',
            'semi_batch': '半间歇',
            'downstream': '下游',
            'upstream': '上游',
            'feed': '进料',
            'product': '产品',
            'byproduct': '副产物',
            'solvent': '溶剂',
            'catalyst': '催化剂'
        }
        
        # 数值模式
        self.number_patterns = {
            'temperature': r'(-?\d+\.?\d*)\s*°?[CcFf]?',
            'pressure': r'(-?\d+\.?\d*)\s*[Pp]a|[Bb]ar|[Mm]Pa',
            'flow_rate': r'(-?\d+\.?\d*)\s*[Ll]/?[Hh]|[Mm]³/?[Hh]',
            'concentration': r'(-?\d+\.?\d*)\s*%|[Mm]ol/?[Ll]|[Gg]/?[Ll]',
            'time': r'(-?\d+\.?\d*)\s*[Ss]|[Mmm]in|[Hh]'
        }
        
        logger.info("Tesseract OCR解析器初始化完成")
    
    def _check_dependencies(self):
        """检查依赖库的可用性"""
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "Tesseract OCR或PIL未安装.\n"
                "请运行: pip install pytesseract pillow\n"
                "请确保系统中已安装Tesseract OCR引擎"
            )
        
        # 测试Tesseract是否可用
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract版本: {version}")
        except Exception as e:
            raise ImportError(f"Tesseract不可用: {str(e)}")
        
        if not PANDAS_AVAILABLE:
            logger.warning("pandas未安装，识别结果数据处理功能受限")
    
    def recognize_image(self, image_path: Union[str, Path], 
                       config: Optional[OCRConfig] = None) -> OCRResult:
        """
        识别单个图像中的文字
        
        Args:
            image_path: 图像文件路径
            config: OCR配置，为None时使用默认配置
            
        Returns:
            识别结果
        """
        import time
        start_time = time.time()
        
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        
        if config is None:
            config = self.default_config
        
        logger.info(f"开始识别图像文字: {image_path}")
        
        try:
            # 加载和预处理图像
            image = self._load_and_preprocess_image(image_path, config)
            
            # 识别文字
            recognized_data = self._recognize_text_with_details(image, config)
            
            # 处理识别结果
            words, lines = self._parse_recognized_data(recognized_data)
            full_text = ' '.join([word.text for word in words])
            
            # 增强识别结果
            enhanced_words = self._enhance_recognition(words, config)
            
            # 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(enhanced_words)
            
            # 提取化工参数
            chemical_params = self._extract_chemical_parameters(full_text)
            
            processing_time = time.time() - start_time
            
            result = OCRResult(
                text=full_text,
                confidence=overall_confidence,
                words=enhanced_words,
                lines=lines,
                processing_time=processing_time,
                image_path=str(image_path),
                config=config,
                metadata={
                    'chemical_parameters': chemical_params,
                    'image_size': image.size,
                    'tesseract_version': pytesseract.get_tesseract_version(),
                    'enhancement_applied': True
                }
            )
            
            logger.info(f"图像文字识别完成，置信度: {overall_confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"图像文字识别失败: {str(e)}")
            raise
    
    def _load_and_preprocess_image(self, image_path: Path, config: OCRConfig) -> Image.Image:
        """加载和预处理图像"""
        try:
            # 加载图像
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if config.preprocessing:
                    img = self._preprocess_image(img, config)
                
                return img
                
        except Exception as e:
            logger.error(f"图像加载失败: {str(e)}")
            raise
    
    def _preprocess_image(self, image: Image.Image, config: OCRConfig) -> Image.Image:
        """图像预处理以提高识别精度"""
        processed = image.copy()
        
        # 1. 增强对比度
        if config.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(processed)
            processed = enhancer.enhance(config.contrast)
        
        # 2. 锐化图像
        if config.sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(processed)
            processed = enhancer.enhance(config.sharpness)
        
        # 3. 转换为灰度图（对于OCR通常效果更好）
        processed = processed.convert('L')
        
        # 4. 应用自适应阈值
        processed = ImageOps.autocontrast(processed)
        
        # 5. 去除噪声
        processed = processed.filter(ImageFilter.MedianFilter())
        
        # 6. 提高DPI（如果需要）
        if config.dpi != 300:
            # 调整DPI需要重新采样图像
            current_dpi = 72  # PIL默认DPI
            scale_factor = config.dpi / current_dpi
            new_size = (int(processed.width * scale_factor), 
                       int(processed.height * scale_factor))
            processed = processed.resize(new_size, Image.Resampling.LANCZOS)
        
        return processed
    
    def _recognize_text_with_details(self, image: Image.Image, config: OCRConfig) -> Any:
        """使用详细模式识别文字"""
        try:
            # 构建识别配置字符串
            config_str = f'--oem {config.oem} --psm {config.psm}'
            
            if config.whitelist:
                config_str += f' -c tessedit_char_whitelist={config.whitelist}'
            
            if config.blacklist:
                config_str += f' -c tessedit_char_blacklist={config.blacklist}'
            
            # 使用详细模式获取识别数据
            data = pytesseract.image_to_data(
                image, 
                config=config_str,
                lang=config.language,
                output_type=pytesseract.Output.DICT
            )
            
            return data
            
        except Exception as e:
            logger.error(f"文字识别失败: {str(e)}")
            raise
    
    def _parse_recognized_data(self, data: Any) -> Tuple[List[RecognizedText], List[RecognizedText]]:
        """解析识别数据"""
        words = []
        lines = []
        
        try:
            n_boxes = len(data['text'])
            
            # 处理每个识别的字符
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                if conf > 30:  # 过滤低置信度结果
                    text = data['text'][i].strip()
                    if text:
                        bbox = BoundingBox(
                            x=data['left'][i],
                            y=data['top'][i],
                            width=data['width'][i],
                            height=data['height'][i],
                            confidence=conf / 100.0
                        )
                        
                        word = RecognizedText(
                            text=text,
                            confidence=conf / 100.0,
                            bbox=bbox,
                            line_number=data.get('line_num', [0])[i] if i < len(data.get('line_num', [])) else 0,
                            word_number=data.get('word_num', [0])[i] if i < len(data.get('word_num', [])) else 0
                        )
                        
                        words.append(word)
            
            # 按行分组
            line_groups = {}
            for word in words:
                line_num = word.line_number
                if line_num not in line_groups:
                    line_groups[line_num] = []
                line_groups[line_num].append(word)
            
            # 创建行对象
            for line_num, word_list in line_groups.items():
                if word_list:
                    line_text = ' '.join([w.text for w in word_list])
                    line_confidence = sum(w.confidence for w in word_list) / len(word_list)
                    
                    # 计算行的边界框
                    min_x = min(w.bbox.x for w in word_list)
                    min_y = min(w.bbox.y for w in word_list)
                    max_x = max(w.bbox.x + w.bbox.width for w in word_list)
                    max_y = max(w.bbox.y + w.bbox.height for w in word_list)
                    
                    line_bbox = BoundingBox(
                        x=min_x, y=min_y,
                        width=max_x - min_x, height=max_y - min_y,
                        confidence=line_confidence
                    )
                    
                    line = RecognizedText(
                        text=line_text,
                        confidence=line_confidence,
                        bbox=line_bbox,
                        line_number=line_num
                    )
                    
                    lines.append(line)
            
            return words, lines
            
        except Exception as e:
            logger.error(f"识别数据解析失败: {str(e)}")
            return [], []
    
    def _enhance_recognition(self, words: List[RecognizedText], config: OCRConfig) -> List[RecognizedText]:
        """增强识别结果"""
        enhanced_words = []
        
        for word in words:
            enhanced_text = self._enhance_single_word(word.text)
            enhanced_word = RecognizedText(
                text=enhanced_text,
                confidence=word.confidence,
                bbox=word.bbox,
                line_number=word.line_number,
                word_number=word.word_number
            )
            enhanced_words.append(enhanced_word)
        
        return enhanced_words
    
    def _enhance_single_word(self, text: str) -> str:
        """增强单个词的识别结果"""
        enhanced = text.strip()
        
        # 化工术语替换
        for eng_term, chn_term in self.chemical_terms.items():
            if eng_term.lower() in enhanced.lower():
                enhanced = enhanced.lower().replace(eng_term.lower(), chn_term)
        
        # 标准化单位
        enhanced = re.sub(r'°C|℃', '°C', enhanced)
        enhanced = re.sub(r'°F|℉', '°F', enhanced)
        enhanced = re.sub(r'Pa|pa', 'Pa', enhanced)
        enhanced = re.sub(r'MPa|MPA', 'MPa', enhanced)
        enhanced = re.sub(r'kPa|KPA', 'kPa', enhanced)
        enhanced = re.sub(r'L/h|l/h', 'L/h', enhanced)
        enhanced = re.sub(r'm³/h|m3/h', 'm³/h', enhanced)
        
        return enhanced
    
    def _calculate_overall_confidence(self, words: List[RecognizedText]) -> float:
        """计算整体置信度"""
        if not words:
            return 0.0
        
        # 加权平均置信度
        total_confidence = sum(word.confidence for word in words)
        return total_confidence / len(words)
    
    def _extract_chemical_parameters(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """从识别文本中提取化工参数"""
        parameters = {
            'temperature': [],
            'pressure': [],
            'flow_rate': [],
            'concentration': [],
            'time': []
        }
        
        for param_type, pattern in self.number_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = float(match.group(1))
                unit = match.group(0).replace(str(value), '').strip()
                
                parameters[param_type].append({
                    'value': value,
                    'unit': unit,
                    'position': match.span()
                })
        
        return parameters
    
    def recognize_batch(self, image_paths: List[Union[str, Path]], 
                       max_workers: int = 2) -> Dict[str, OCRResult]:
        """
        批量识别多个图像
        
        Args:
            image_paths: 图像文件路径列表
            max_workers: 最大并发数
            
        Returns:
            文件路径到识别结果的映射
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.recognize_image, image_path): image_path 
                for image_path in image_paths
            }
            
            for future in as_completed(future_to_path):
                image_path = future_to_path[future]
                try:
                    result = future.result()
                    results[str(image_path)] = result
                except Exception as e:
                    logger.error(f"批量识别失败 {image_path}: {str(e)}")
                    results[str(image_path)] = None
        
        return results
    
    def recognize_from_base64(self, image_base64: str, 
                            config: Optional[OCRConfig] = None) -> OCRResult:
        """
        从base64字符串识别图像
        
        Args:
            image_base64: base64编码的图像数据
            config: OCR配置
            
        Returns:
            识别结果
        """
        try:
            # 解码base64图像
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # 使用默认配置或指定配置
            if config is None:
                config = self.default_config
            
            return self._recognize_from_pil_image(image, config)
            
        except Exception as e:
            logger.error(f"Base64图像识别失败: {str(e)}")
            raise
    
    def _recognize_from_pil_image(self, image: Image.Image, config: OCRConfig) -> OCRResult:
        """从PIL图像对象进行识别"""
        import time
        start_time = time.time()
        
        try:
            # 预处理图像
            if config.preprocessing:
                image = self._preprocess_image(image, config)
            
            # 识别文字
            recognized_data = self._recognize_text_with_details(image, config)
            
            # 处理识别结果
            words, lines = self._parse_recognized_data(recognized_data)
            full_text = ' '.join([word.text for word in words])
            
            # 增强识别结果
            enhanced_words = self._enhance_recognition(words, config)
            
            # 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(enhanced_words)
            
            # 提取化工参数
            chemical_params = self._extract_chemical_parameters(full_text)
            
            processing_time = time.time() - start_time
            
            result = OCRResult(
                text=full_text,
                confidence=overall_confidence,
                words=enhanced_words,
                lines=lines,
                processing_time=processing_time,
                image_path="<PIL_Image>",
                config=config,
                metadata={
                    'chemical_parameters': chemical_params,
                    'image_size': image.size,
                    'tesseract_version': pytesseract.get_tesseract_version(),
                    'enhancement_applied': True,
                    'source_type': 'PIL_Image'
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"PIL图像识别失败: {str(e)}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"获取支持语言失败: {str(e)}")
            return ['eng', 'chi_sim']
    
    def create_chemical_word_list(self) -> str:
        """创建化工专业术语词列表"""
        return '\n'.join(self.chemical_terms.values())
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"TesseractOCRParser(default_config={self.default_config})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建解析器实例
    parser = TesseractOCRParser()
    
    # 支持的语言
    print("支持的语言:", parser.get_supported_languages())
    
    # 示例图像路径（请替换为实际路径）
    test_image = "test_chemical_diagram.png"
    
    try:
        if Path(test_image).exists():
            # 识别单个图像
            result = parser.recognize_image(test_image)
            
            print(f"\n=== 识别结果 ===")
            print(f"识别文本: {result.text}")
            print(f"置信度: {result.confidence:.2f}")
            print(f"处理时间: {result.processing_time:.2f}秒")
            
            print(f"\n化工参数:")
            for param_type, values in result.metadata['chemical_parameters'].items():
                if values:
                    print(f"  {param_type}: {values}")
            
            print(f"\n识别词汇数: {len(result.words)}")
            print(f"识别行数: {len(result.lines)}")
        else:
            print(f"测试图像不存在: {test_image}")
            
    except Exception as e:
        print(f"OCR识别失败: {str(e)}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnveilChem 文档解析器模块

这个模块包含了所有文档解析器的实现，支持：
- Apache Tika: 多格式文档解析 (1000+种格式)
- Camelot-py: PDF表格高精度提取 (≥99.02%准确率)
- Tesseract OCR: 图像文字识别
- PyMuPDF: 增强PDF解析引擎

所有解析器都遵循统一的接口设计，确保代码的可维护性和扩展性。

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

from .tika_parser import TikaDocumentParser
from .camelot_parser import CamelotTableParser
from .tesseract_parser import TesseractOCRParser
from .pymupdf_parser import PyMuPDFParser

__all__ = [
    'TikaDocumentParser',
    'CamelotTableParser', 
    'TesseractOCRParser',
    'PyMuPDFParser'
]

__version__ = "1.0.0"
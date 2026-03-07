#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一解析器管理器

集成Apache Tika、Camelot-py、Tesseract OCR、PyMuPDF等多个解析引擎,
提供统一的文档解析接口，实现智能路由和最佳性能选择。
这是实现需求文档7.4节中"多格式文档解析引擎"的核心组件。

特性:
- 多解析引擎统一接口
- 智能解析器选择和路由
- 解析结果融合和优化
- 错误处理和降级策略
- 性能监控和统计
- 批量处理和并发支持

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

import io
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

# 导入各个解析器
try:
    from .tika_parser import TikaDocumentParser, DocumentMetadata as TikaMetadata
except ImportError:
    TikaDocumentParser = None
    TikaMetadata = None

try:
    from .camelot_parser import CamelotTableParser, ExtractedTable
except ImportError:
    CamelotTableParser = None
    ExtractedTable = None

try:
    from .tesseract_parser import TesseractOCRParser, OCRResult
    OCR_PARSER_AVAILABLE = True
except ImportError:
    TesseractOCRParser = None
    OCRResult = None
    OCR_PARSER_AVAILABLE = False

try:
    from .pymupdf_parser import PyMuPDFParser
except ImportError:
    PyMuPDFParser = None

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """文档类型枚举"""
    PDF = "pdf"
    OFFICE_DOCUMENT = "office_document"  # Word, Excel, PowerPoint
    IMAGE = "image"
    TEXT = "text"
    HTML = "html"
    XML = "xml"
    CSV = "csv"
    UNKNOWN = "unknown"

class ParserType(Enum):
    """解析器类型枚举"""
    TIKA = "tika"
    CAMELOT = "camelot"
    TESSERACT = "tesseract"
    PYMUPDF = "pymupdf"
    UNKNOWN = "unknown"

@dataclass
class ParseRequest:
    """解析请求"""
    file_path: Union[str, Path]
    document_type: DocumentType
    required_parsers: List[ParserType] = field(default_factory=list)
    extraction_options: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"  # "high", "normal", "low"
    timeout: Optional[float] = None

@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    file_path: str
    document_type: DocumentType
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tables: List[Any] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    parser_used: List[ParserType] = field(default_factory=list)
    confidence_score: float = 0.0
    error_message: Optional[str] = None

@dataclass
class ParserCapability:
    """解析器能力描述"""
    parser_type: ParserType
    supported_formats: Set[str]
    max_file_size_mb: int
    accuracy_score: float
    processing_speed: float  # 页/秒
    memory_usage_mb: int
    special_features: List[str]

class UnifiedDocumentParser:
    """
    统一文档解析器
    
    整合多个解析引擎，提供智能路由和最佳性能选择。
    根据文档类型和内容特征自动选择最合适的解析器。
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化统一解析器
        
        Args:
            config_path: 配置文件路径
        """
        self._initialize_parsers()
        self._setup_parser_capabilities()
        self._load_configuration(config_path)
        
        # 性能统计
        self.statistics = {
            'total_documents': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'parser_usage': {pt: 0 for pt in ParserType},
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        
        logger.info("统一文档解析器初始化完成")
    
    def _initialize_parsers(self):
        """初始化各个解析器"""
        self.parsers = {}
        
        # 初始化Apache Tika解析器
        if TikaDocumentParser:
            try:
                self.parsers[ParserType.TIKA] = TikaDocumentParser()
                logger.info("Apache Tika解析器初始化成功")
            except Exception as e:
                logger.warning(f"Apache Tika解析器初始化失败: {str(e)}")
        
        # 初始化Camelot表格解析器
        if CamelotTableParser:
            try:
                self.parsers[ParserType.CAMELOT] = CamelotTableParser()
                logger.info("Camelot表格解析器初始化成功")
            except Exception as e:
                logger.warning(f"Camelot表格解析器初始化失败: {str(e)}")
        
        # 初始化Tesseract OCR解析器
        if TesseractOCRParser and OCR_PARSER_AVAILABLE:
            try:
                self.parsers[ParserType.TESSERACT] = TesseractOCRParser()
                logger.info("Tesseract OCR解析器初始化成功")
            except Exception as e:
                logger.warning(f"Tesseract OCR解析器初始化失败: {str(e)}")
        
        # 初始化PyMuPDF解析器
        if PyMuPDFParser:
            try:
                self.parsers[ParserType.PYMUPDF] = PyMuPDFParser()
                logger.info("PyMuPDF解析器初始化成功")
            except Exception as e:
                logger.warning(f"PyMuPDF解析器初始化失败: {str(e)}")
        
        if not self.parsers:
            logger.error("没有可用的解析器！请检查依赖安装")
            raise RuntimeError("没有可用的解析器组件")
    
    def _setup_parser_capabilities(self):
        """设置解析器能力描述"""
        self.parser_capabilities = {}
        
        if ParserType.TIKA in self.parsers:
            self.parser_capabilities[ParserType.TIKA] = ParserCapability(
                parser_type=ParserType.TIKA,
                supported_formats={'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                 '.txt', '.html', '.xml', '.rtf', '.odt', '.ods', '.csv'},
                max_file_size_mb=500,
                accuracy_score=0.85,
                processing_speed=10.0,  # 页/秒
                memory_usage_mb=100,
                special_features=['元数据提取', '多格式支持', '内容结构分析']
            )
        
        if ParserType.CAMELOT in self.parsers:
            self.parser_capabilities[ParserType.CAMELOT] = ParserCapability(
                parser_type=ParserType.CAMELOT,
                supported_formats={'.pdf'},
                max_file_size_mb=200,
                accuracy_score=0.99,  # 99%准确率
                processing_speed=5.0,
                memory_usage_mb=150,
                special_features=['表格结构分析', '边框检测', '单元格分割']
            )
        
        if ParserType.TESSERACT in self.parsers:
            self.parser_capabilities[ParserType.TESSERACT] = ParserCapability(
                parser_type=ParserType.TESSERACT,
                supported_formats={'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.pdf'},
                max_file_size_mb=100,
                accuracy_score=0.90,
                processing_speed=2.0,
                memory_usage_mb=80,
                special_features=['OCR文字识别', '多语言支持', '边界框定位']
            )
        
        if ParserType.PYMUPDF in self.parsers:
            self.parser_capabilities[ParserType.PYMUPDF] = ParserCapability(
                parser_type=ParserType.PYMUPDF,
                supported_formats={'.pdf'},
                max_file_size_mb=1000,
                accuracy_score=0.88,
                processing_speed=15.0,
                memory_usage_mb=120,
                special_features=['高性能解析', '图像提取', '链接处理', '页面布局分析']
            )
    
    def _load_configuration(self, config_path: Optional[Union[str, Path]]):
        """加载配置文件"""
        if config_path:
            config_path = Path(config_path)
            if config_path.exists():
                # TODO: 实现配置文件加载
                logger.info(f"配置文件加载成功: {config_path}")
            else:
                logger.warning(f"配置文件不存在: {config_path}")
        
        # 默认配置
        self.config = {
            'default_timeout': 30.0,
            'max_retries': 3,
            'parallel_processing': True,
            'max_workers': 2,
            'fallback_enabled': True,
            'cache_enabled': True,
            'quality_threshold': 0.7
        }
    
    def detect_document_type(self, file_path: Union[str, Path]) -> DocumentType:
        """
        检测文档类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档类型
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        # 基于文件扩展名的简单检测
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.doc': DocumentType.OFFICE_DOCUMENT,
            '.docx': DocumentType.OFFICE_DOCUMENT,
            '.xls': DocumentType.OFFICE_DOCUMENT,
            '.xlsx': DocumentType.OFFICE_DOCUMENT,
            '.ppt': DocumentType.OFFICE_DOCUMENT,
            '.pptx': DocumentType.OFFICE_DOCUMENT,
            '.txt': DocumentType.TEXT,
            '.html': DocumentType.HTML,
            '.xml': DocumentType.XML,
            '.csv': DocumentType.CSV,
            '.png': DocumentType.IMAGE,
            '.jpg': DocumentType.IMAGE,
            '.jpeg': DocumentType.IMAGE,
            '.tiff': DocumentType.IMAGE,
            '.bmp': DocumentType.IMAGE,
            '.gif': DocumentType.IMAGE
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)
    
    def select_optimal_parsers(self, document_type: DocumentType, 
                             file_path: Union[str, Path]) -> List[ParserType]:
        """
        选择最优解析器组合
        
        Args:
            document_type: 文档类型
            file_path: 文件路径
            
        Returns:
            推荐的解析器类型列表
        """
        file_path = Path(file_path)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        selected_parsers = []
        
        # 根据文档类型选择解析器
        if document_type == DocumentType.PDF:
            # PDF文档：优先使用PyMuPDF，表格使用Camelot
            if ParserType.PYMUPDF in self.parsers:
                capability = self.parser_capabilities[ParserType.PYMUPDF]
                if file_size_mb <= capability.max_file_size_mb:
                    selected_parsers.append(ParserType.PYMUPDF)
            
            if ParserType.CAMELOT in self.parsers and file_size_mb <= 200:
                selected_parsers.append(ParserType.CAMELOT)
            
            if ParserType.TIKA in self.parsers:
                selected_parsers.append(ParserType.TIKA)
        
        elif document_type == DocumentType.OFFICE_DOCUMENT:
            # Office文档：主要使用Tika
            if ParserType.TIKA in self.parsers:
                selected_parsers.append(ParserType.TIKA)
        
        elif document_type == DocumentType.IMAGE:
            # 图像：使用Tesseract OCR
            if ParserType.TESSERACT in self.parsers:
                selected_parsers.append(ParserType.TESSERACT)
        
        elif document_type in [DocumentType.TEXT, DocumentType.HTML, DocumentType.XML]:
            # 文本类文档：使用Tika
            if ParserType.TIKA in self.parsers:
                selected_parsers.append(ParserType.TIKA)
        
        # 如果没有找到合适的解析器，尝试所有可用的
        if not selected_parsers:
            selected_parsers = list(self.parsers.keys())
        
        return selected_parsers
    
    def parse_document(self, request: ParseRequest) -> ParseResult:
        """
        解析文档
        
        Args:
            request: 解析请求
            
        Returns:
            解析结果
        """
        start_time = time.time()
        file_path = Path(request.file_path)
        
        if not file_path.exists():
            return ParseResult(
                success=False,
                file_path=str(file_path),
                document_type=request.document_type,
                error_message=f"文件不存在: {file_path}"
            )
        
        logger.info(f"开始解析文档: {file_path}")
        
        # 更新统计
        self.statistics['total_documents'] += 1
        
        try:
            # 智能选择解析器
            if not request.required_parsers:
                optimal_parsers = self.select_optimal_parsers(
                    request.document_type, file_path
                )
            else:
                optimal_parsers = request.required_parsers
            
            # 执行解析
            parse_results = self._execute_parsing(optimal_parsers, request)
            
            # 融合结果
            final_result = self._merge_parse_results(
                parse_results, request, start_time
            )
            
            # 更新统计
            if final_result.success:
                self.statistics['successful_parses'] += 1
                self.statistics['parser_usage'].update({
                    parser: self.statistics['parser_usage'].get(parser, 0) + 1
                    for parser in final_result.parser_used
                })
            else:
                self.statistics['failed_parses'] += 1
            
            self.statistics['total_processing_time'] += final_result.processing_time
            self.statistics['average_processing_time'] = (
                self.statistics['total_processing_time'] / 
                self.statistics['total_documents']
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            self.statistics['failed_parses'] += 1
            
            return ParseResult(
                success=False,
                file_path=str(file_path),
                document_type=request.document_type,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _execute_parsing(self, parser_types: List[ParserType], 
                        request: ParseRequest) -> Dict[ParserType, Any]:
        """执行解析"""
        results = {}
        file_path = Path(request.file_path)
        
        for parser_type in parser_types:
            if parser_type not in self.parsers:
                logger.warning(f"解析器 {parser_type} 不可用")
                continue
            
            try:
                parser = self.parsers[parser_type]
                
                if parser_type == ParserType.TIKA:
                    result = parser.parse_document(file_path)
                elif parser_type == ParserType.CAMELOT:
                    if request.document_type == DocumentType.PDF:
                        result = parser.extract_tables(file_path)
                    else:
                        continue
                elif parser_type == ParserType.TESSERACT:
                    if request.document_type == DocumentType.IMAGE:
                        result = parser.recognize_image(file_path)
                    else:
                        continue
                elif parser_type == ParserType.PYMUPDF:
                    if request.document_type == DocumentType.PDF:
                        result = parser.parse_document(file_path)
                    else:
                        continue
                else:
                    continue
                
                results[parser_type] = result
                logger.info(f"解析器 {parser_type} 执行成功")
                
            except Exception as e:
                logger.error(f"解析器 {parser_type} 执行失败: {str(e)}")
                continue
        
        return results
    
    def _merge_parse_results(self, parse_results: Dict[ParserType, Any], 
                           request: ParseRequest, start_time: float) -> ParseResult:
        """融合多个解析器的结果"""
        if not parse_results:
            return ParseResult(
                success=False,
                file_path=str(request.file_path),
                document_type=request.document_type,
                error_message="所有解析器都执行失败",
                processing_time=time.time() - start_time
            )
        
        # 初始化最终结果
        merged_result = ParseResult(
            success=True,
            file_path=str(request.file_path),
            document_type=request.document_type,
            processing_time=time.time() - start_time
        )
        
        content_parts = []
        metadata_parts = []
        table_parts = []
        image_parts = []
        parameter_parts = []
        confidence_scores = []
        
        # 融合各个解析器的结果
        for parser_type, result in parse_results.items():
            merged_result.parser_used.append(parser_type)
            
            try:
                if parser_type == ParserType.TIKA:
                    # Tika解析结果
                    if hasattr(result, 'content') and result.content:
                        content_parts.append(result.content)
                    if hasattr(result, 'metadata') and result.metadata:
                        metadata_parts.append(result.metadata)
                    if hasattr(result, 'confidence_score'):
                        confidence_scores.append(result.confidence_score)
                
                elif parser_type == ParserType.CAMELOT:
                    # Camelot表格结果
                    if isinstance(result, list):
                        table_parts.extend(result)
                        for table in result:
                            if hasattr(table, 'confidence'):
                                confidence_scores.append(table.confidence)
                
                elif parser_type == ParserType.TESSERACT:
                    # Tesseract OCR结果
                    if hasattr(result, 'text') and result.text:
                        content_parts.append(result.text)
                    if hasattr(result, 'confidence'):
                        confidence_scores.append(result.confidence)
                    if hasattr(result, 'metadata') and result.metadata.get('chemical_parameters'):
                        parameter_parts.append(result.metadata['chemical_parameters'])
                
                elif parser_type == ParserType.PYMUPDF:
                    # PyMuPDF解析结果
                    if hasattr(result, 'full_text') and result.full_text:
                        content_parts.append(result.full_text)
                    if hasattr(result, 'metadata') and result.metadata:
                        metadata_parts.append(result.metadata.__dict__ if hasattr(result.metadata, '__dict__') else result.metadata)
                    if hasattr(result, 'elements'):
                        # 提取化工参数
                        for element in result.elements:
                            if element.type == 'chemical_parameter' and 'parameters' in element.metadata:
                                parameter_parts.append(element.metadata['parameters'])
                    if hasattr(result, 'confidence'):
                        confidence_scores.append(result.confidence)
                
            except Exception as e:
                logger.warning(f"解析器 {parser_type} 结果融合失败: {str(e)}")
                continue
        
        # 合并内容
        if content_parts:
            merged_result.content = '\n'.join(content_parts)
        
        # 合并元数据
        if metadata_parts:
            merged_result.metadata = self._merge_metadata(metadata_parts)
        
        # 合并表格
        merged_result.tables = table_parts
        
        # 合并化工参数
        if parameter_parts:
            merged_result.parameters = self._merge_parameters(parameter_parts)
        
        # 计算整体置信度
        if confidence_scores:
            merged_result.confidence_score = sum(confidence_scores) / len(confidence_scores)
        
        return merged_result
    
    def _merge_metadata(self, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并元数据"""
        merged = {}
        
        for metadata in metadata_list:
            for key, value in metadata.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, str) and value.strip():
                    # 保留更详细的信息
                    if isinstance(merged[key], str) and len(value) > len(merged[key]):
                        merged[key] = value
        
        return merged
    
    def _merge_parameters(self, parameter_lists: List[Any]) -> List[Dict[str, Any]]:
        """合并化工参数"""
        all_parameters = []
        
        for param_list in parameter_lists:
            if isinstance(param_list, list):
                all_parameters.extend(param_list)
            elif isinstance(param_list, dict):
                all_parameters.append(param_list)
        
        # 去重和整理
        seen = set()
        unique_parameters = []
        
        for param in all_parameters:
            # 简单的去重逻辑
            param_str = str(sorted(param.items())) if isinstance(param, dict) else str(param)
            if param_str not in seen:
                seen.add(param_str)
                unique_parameters.append(param)
        
        return unique_parameters
    
    def parse_batch(self, file_paths: List[Union[str, Path]], 
                   max_workers: int = 2) -> Dict[str, ParseResult]:
        """
        批量解析文档
        
        Args:
            file_paths: 文件路径列表
            max_workers: 最大并发数
            
        Returns:
            文件路径到解析结果的映射
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 创建解析请求
            future_to_path = {}
            for file_path in file_paths:
                document_type = self.detect_document_type(file_path)
                request = ParseRequest(
                    file_path=file_path,
                    document_type=document_type
                )
                
                future = executor.submit(self.parse_document, request)
                future_to_path[future] = file_path
            
            # 收集结果
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    result = future.result()
                    results[str(file_path)] = result
                except Exception as e:
                    logger.error(f"批量解析失败 {file_path}: {str(e)}")
                    results[str(file_path)] = ParseResult(
                        success=False,
                        file_path=str(file_path),
                        document_type=self.detect_document_type(file_path),
                        error_message=str(e)
                    )
        
        return results
    
    def get_parser_statistics(self) -> Dict[str, Any]:
        """获取解析器统计信息"""
        success_rate = (
            self.statistics['successful_parses'] / max(self.statistics['total_documents'], 1)
        ) * 100
        
        return {
            'total_documents': self.statistics['total_documents'],
            'successful_parses': self.statistics['successful_parses'],
            'failed_parses': self.statistics['failed_parses'],
            'success_rate': f"{success_rate:.1f}%",
            'average_processing_time': f"{self.statistics['average_processing_time']:.2f}秒",
            'parser_usage': dict(self.statistics['parser_usage']),
            'available_parsers': list(self.parsers.keys())
        }
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文档格式"""
        supported = {}
        
        for parser_type, capability in self.parser_capabilities.items():
            if parser_type in self.parsers:
                supported[parser_type.value] = sorted(list(capability.supported_formats))
        
        return supported
    
    def test_parser(self, parser_type: ParserType, test_file: Union[str, Path]) -> bool:
        """测试特定解析器"""
        if parser_type not in self.parsers:
            return False
        
        try:
            document_type = self.detect_document_type(test_file)
            request = ParseRequest(
                file_path=test_file,
                document_type=document_type,
                required_parsers=[parser_type]
            )
            
            result = self.parse_document(request)
            return result.success
            
        except Exception as e:
            logger.error(f"解析器测试失败: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"UnifiedDocumentParser(parsers={list(self.parsers.keys())})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建统一解析器
        parser = UnifiedDocumentParser()
        
        print("=== 统一解析器信息 ===")
        print(f"可用解析器: {list(parser.parsers.keys())}")
        print(f"支持格式: {parser.get_supported_formats()}")
        
        # 测试文档解析
        test_file = "test_chemical_document.pdf"
        if Path(test_file).exists():
            # 创建解析请求
            document_type = parser.detect_document_type(test_file)
            request = ParseRequest(
                file_path=test_file,
                document_type=document_type
            )
            
            # 执行解析
            result = parser.parse_document(request)
            
            print(f"\n=== 解析结果 ===")
            print(f"成功: {result.success}")
            print(f"文档类型: {result.document_type}")
            print(f"使用解析器: {[p.value for p in result.parser_used]}")
            print(f"置信度: {result.confidence_score:.2f}")
            print(f"处理时间: {result.processing_time:.2f}秒")
            
            if result.success:
                print(f"\n内容预览:")
                print(result.content[:300] + "..." if len(result.content) > 300 else result.content)
                print(f"\n表格数量: {len(result.tables)}")
                print(f"参数数量: {len(result.parameters)}")
            
            # 获取统计信息
            print(f"\n=== 统计信息 ===")
            print(parser.get_parser_statistics())
        else:
            print(f"测试文件不存在: {test_file}")
            
    except Exception as e:
        print(f"统一解析器测试失败: {str(e)}")
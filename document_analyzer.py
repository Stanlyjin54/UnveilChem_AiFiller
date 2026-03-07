#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能化工参数识别输入软件 - 统一文档分析器

基于Apache Tika、Camelot、Tesseract等工具实现多格式文档处理,
实现化工专业参数的智能提取和识别。
这是满足需求文档7.4节技术栈选型要求的统一文档解析引擎。

主要功能:
- 多格式文档解析(PDF、Office文档、图像等)
- 化工专业参数识别（温度、压力、流量等）
- 表格数据提取和分析
- P&ID图元素识别
- 自动化参数映射和软件填写

技术栈:
- Apache Tika: 多格式文档解析
- Camelot-py: PDF表格提取
- Tesseract OCR: 图像文字识别
- PyMuPDF: 高性能PDF处理
- 正则表达式: 参数模式匹配

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

import io
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import traceback

# 导入统一解析器
try:
    from parsers.unified_parser import (
        UnifiedDocumentParser, ParseRequest, DocumentType, 
        ParserType, ParseResult
    )
    from parsers.tika_parser import TikaDocumentParser
    from parsers.camelot_parser import CamelotTableParser
    from parsers.tesseract_parser import TesseractOCRParser
    from parsers.pymupdf_parser import PyMuPDFParser
except ImportError as e:
    print(f"解析器模块导入失败: {e}")
    print("请确保所有解析器文件已正确安装")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessParameter:
    """工艺参数数据类"""
    name: str
    value: str
    unit: str
    category: str
    location: str
    confidence: float = 0.0

@dataclass
class PIDElement:
    """P&ID图元素"""
    element_type: str
    symbol: str
    description: str
    position: Tuple[int, int]
    connections: List[str]

class DocumentType(Enum):
    """文档类型"""
    PDF = "pdf"
    OFFICE = "office"
    IMAGE = "image"
    TEXT = "text"
    UNKNOWN = "unknown"

class ExtractionMethod(Enum):
    """提取方法"""
    AUTO = "auto"  # 自动选择
    TIKA = "tika"  # 使用Apache Tika
    CAMELOT = "camelot"  # 使用Camelot表格提取
    TESSERACT = "tesseract"  # 使用Tesseract OCR
    PYMUPDF = "pymupdf"  # 使用PyMuPDF

class ChemDocAnalyzer:
    """
    化工文档分析器
    
    集成多个解析引擎，实现化工专业文档的参数提取和分析。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析器
        
        Args:
            config: 配置选项
        """
        self.config = config or {}
        
        # 初始化统一解析器
        try:
            self.unified_parser = UnifiedDocumentParser()
            logger.info("统一解析器初始化成功")
        except Exception as e:
            logger.error(f"统一解析器初始化失败: {str(e)}")
            raise
        
        # 设置化工参数识别模式
        self._setup_parameter_patterns()
        
        # 设置P&ID图识别模式
        self._setup_pid_patterns()
        
        logger.info("化工文档分析器初始化完成")
    
    def _setup_parameter_patterns(self):
        """设置化工参数识别正则表达式模式"""
        self.parameter_patterns = {
            # 温度参数
            'temperature': [
                r'温度\s*[::]\s*([\d.,]+)\s*°?([CFK])?',
                r'T(emperature)?\s*[::]\s*([\d.,]+)\s*°?([CFK])?',
                r'([\d.,]+)\s*°?([CFK])\s*温度',
                r'([\d.,]+)\s*°?([CFK])\s*Temp',
            ],
            
            # 压力参数
            'pressure': [
                r'压力\s*[::]\s*([\d.,]+)\s*(MPa|kPa|bar|psi|atm)?',
                r'P(ressure)?\s*[::]\s*([\d.,]+)\s*(MPa|kPa|bar|psi|atm)?',
                r'([\d.,]+)\s*(MPa|kPa|bar|psi|atm)\s*压力',
                r'([\d.,]+)\s*(MPa|kPa|bar|psi|atm)\s*Press',
            ],
            
            # 流量参数
            'flow_rate': [
                r'流量\s*[::]\s*([\d.,]+)\s*(m³/h|L/min|m³/s|m³/d)?',
                r'F(low)?\s*[::]\s*([\d.,]+)\s*(m³/h|L/min|m³/s|m³/d)?',
                r'([\d.,]+)\s*(m³/h|L/min|m³/s|m³/d)\s*流量',
                r'([\d.,]+)\s*(m³/h|L/min|m³/s|m³/d)\s*Flow',
            ],
            
            # 液位参数
            'level': [
                r'液位\s*[::]\s*([\d.,]+)\s*(%|mm|m)?',
                r'L(evel)?\s*[::]\s*([\d.,]+)\s*(%|mm|m)?',
                r'([\d.,]+)\s*(%|mm|m)\s*液位',
                r'([\d.,]+)\s*(%|mm|m)\s*Level',
            ],
            
            # pH值
            'ph': [
                r'pH\s*[::]\s*([\d.,]+)',
                r'酸碱度\s*[::]\s*([\d.,]+)',
            ],
            
            # 浓度
            'concentration': [
                r'浓度\s*[::]\s*([\d.,]+)\s*(%|mg/L|g/L|mol/L)?',
                r'C(oncentration)?\s*[::]\s*([\d.,]+)\s*(%|mg/L|g/L|mol/L)?',
                r'([\d.,]+)\s*(%|mg/L|g/L|mol/L)\s*浓度',
                r'([\d.,]+)\s*(%|mg/L|g/L|mol/L)\s*Conc',
            ],
            
            # 转速
            'speed': [
                r'转速\s*[::]\s*([\d.,]+)\s*(rpm|r/s)?',
                r'Speed\s*[::]\s*([\d.,]+)\s*(rpm|r/s)?',
                r'([\d.,]+)\s*(rpm|r/s)\s*转速',
                r'([\d.,]+)\s*(rpm|r/s)\s*Speed',
            ]
        }
        
        # 参数类别映射
        self.parameter_categories = {
            'temperature': '温度参数',
            'pressure': '压力参数',
            'flow_rate': '流量参数',
            'level': '液位参数',
            'ph': '酸碱度',
            'concentration': '浓度参数',
            'speed': '转速参数'
        }
        
        logger.info("参数识别模式设置完成")
    
    def _setup_pid_patterns(self):
        """设置P&ID图元素识别模式"""
        self.pid_patterns = {
            # 反应器
            'reactor': [
                r'反应器',
                r'Reactor',
                r'R\d*',  # R-001, R-002等
            ],
            
            # 泵
            'pump': [
                r'泵',
                r'Pump',
                r'P\d*',  # P-001, P-002等
            ],
            
            # 换热器
            'heat_exchanger': [
                r'换热器',
                r'Heat\s*Exchanger',
                r'E\d*',  # E-001, E-002等
            ],
            
            # 储罐
            'tank': [
                r'储罐',
                r'Tank',
                r'T\d*',  # T-001, T-002等
            ],
            
            # 阀门
            'valve': [
                r'阀门',
                r'Valve',
                r'V\d*',  # V-001, V-002等
            ],
            
            # 管道
            'pipe': [
                r'管道',
                r'Pipe',
                r'管道\d*',
            ]
        }
        
        logger.info("P&ID图识别模式设置完成")
    
    def analyze_document(self, file_path: Union[str, Path], 
                        method: ExtractionMethod = ExtractionMethod.AUTO) -> Dict[str, Any]:
        """
        分析文档主接口
        
        Args:
            file_path: 文档路径
            method: 提取方法
            
        Returns:
            分析结果字典
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始分析文档: {file_path}")
        
        try:
            # 检测文档类型
            document_type = self._detect_document_type(file_path)
            
            # 创建解析请求
            parse_request = self._create_parse_request(file_path, document_type, method)
            
            # 执行解析
            parse_result = self.unified_parser.parse_document(parse_request)
            
            if not parse_result.success:
                raise RuntimeError(f"文档解析失败: {parse_result.error_message}")
            
            # 提取化工参数
            chemical_parameters = self._extract_chemical_parameters(parse_result)
            
            # 识别P&ID图元素
            pid_elements = self._identify_pid_elements(parse_result)
            
            # 提取表格数据
            table_data = self._extract_table_data(parse_result)
            
            # 生成分析报告
            analysis_result = {
                'file_info': {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'document_type': document_type.value,
                    'file_size': file_path.stat().st_size,
                    'parsers_used': [p.value for p in parse_result.parser_used]
                },
                'content_summary': {
                    'content_length': len(parse_result.content),
                    'content_preview': parse_result.content[:500] + "..." if len(parse_result.content) > 500 else parse_result.content,
                    'metadata': parse_result.metadata,
                    'processing_time': parse_result.processing_time,
                    'confidence_score': parse_result.confidence_score
                },
                'chemical_parameters': chemical_parameters,
                'pid_elements': pid_elements,
                'table_data': table_data,
                'extraction_summary': {
                    'total_parameters': len(chemical_parameters),
                    'pid_elements_found': len(pid_elements),
                    'tables_extracted': len(table_data),
                    'extraction_method': method.value,
                    'success_rate': parse_result.confidence_score
                }
            }
            
            logger.info(f"文档分析完成: {len(chemical_parameters)}个参数, {len(pid_elements)}个P&ID元素")
            return analysis_result
            
        except Exception as e:
            logger.error(f"文档分析失败: {str(e)}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            raise
    
    def _detect_document_type(self, file_path: Path) -> DocumentType:
        """检测文档类型"""
        extension = file_path.suffix.lower()
        
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.doc': DocumentType.OFFICE,
            '.docx': DocumentType.OFFICE,
            '.xls': DocumentType.OFFICE,
            '.xlsx': DocumentType.OFFICE,
            '.ppt': DocumentType.OFFICE,
            '.pptx': DocumentType.OFFICE,
            '.txt': DocumentType.TEXT,
            '.png': DocumentType.IMAGE,
            '.jpg': DocumentType.IMAGE,
            '.jpeg': DocumentType.IMAGE,
            '.tiff': DocumentType.IMAGE,
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)
    
    def _create_parse_request(self, file_path: Path, document_type: DocumentType, 
                             method: ExtractionMethod) -> ParseRequest:
        """创建解析请求"""
        # 根据提取方法确定需要的解析器
        required_parsers = []
        
        if method == ExtractionMethod.AUTO:
            # 自动选择所有可用的解析器
            pass  # 统一解析器会自动选择
        elif method == ExtractionMethod.TIKA:
            required_parsers = [ParserType.TIKA]
        elif method == ExtractionMethod.CAMELOT:
            required_parsers = [ParserType.CAMELOT]
        elif method == ExtractionMethod.TESSERACT:
            required_parsers = [ParserType.TESSERACT]
        elif method == ExtractionMethod.PYMUPDF:
            required_parsers = [ParserType.PYMUPDF]
        
        # 转换DocumentType
        unified_doc_type_map = {
            DocumentType.PDF: "pdf",
            DocumentType.OFFICE: "office_document", 
            DocumentType.IMAGE: "image",
            DocumentType.TEXT: "text"
        }
        
        return ParseRequest(
            file_path=str(file_path),
            document_type=unified_doc_type_map.get(document_type, "unknown"),
            required_parsers=required_parsers,
            extraction_options=self.config.get('extraction_options', {}),
            priority=self.config.get('priority', 'normal')
        )
    
    def _extract_chemical_parameters(self, parse_result: ParseResult) -> List[ProcessParameter]:
        """提取化工参数"""
        parameters = []
        text_content = parse_result.content
        
        if not text_content:
            logger.warning("没有文本内容可分析")
            return parameters
        
        # 从参数列表中提取
        for param_list in parse_result.parameters:
            if isinstance(param_list, list):
                for param in param_list:
                    if isinstance(param, dict):
                        process_param = ProcessParameter(
                            name=param.get('name', ''),
                            value=param.get('value', ''),
                            unit=param.get('unit', ''),
                            category=param.get('category', ''),
                            location=param.get('location', ''),
                            confidence=param.get('confidence', 0.8)
                        )
                        parameters.append(process_param)
        
        # 使用正则表达式提取参数
        for param_type, patterns in self.parameter_patterns.items():
            category = self.parameter_categories.get(param_type, param_type)
            
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    try:
                        # 提取数值和单位
                        groups = match.groups()
                        
                        if param_type == 'temperature':
                            value = groups[0] if groups else match.group(1)
                            unit = groups[1] if len(groups) > 1 and groups[1] else '°C'
                        elif param_type == 'pressure':
                            value = groups[0] if groups else match.group(1)
                            unit = groups[1] if len(groups) > 1 and groups[1] else 'MPa'
                        elif param_type == 'flow_rate':
                            value = groups[0] if groups else match.group(1)
                            unit = groups[1] if len(groups) > 1 and groups[1] else 'm³/h'
                        elif param_type == 'ph':
                            value = groups[0] if groups else match.group(1)
                            unit = ''
                        else:
                            value = groups[0] if groups else match.group(1)
                            unit = groups[1] if len(groups) > 1 and groups[1] else ''
                        
                        # 创建参数对象
                        param = ProcessParameter(
                            name=param_type,
                            value=str(value),
                            unit=str(unit),
                            category=category,
                            location=match.group(0),
                            confidence=0.9
                        )
                        
                        parameters.append(param)
                        
                    except Exception as e:
                        logger.warning(f"参数提取错误: {str(e)}")
                        continue
        
        # 去重和优化
        unique_parameters = self._deduplicate_parameters(parameters)
        
        logger.info(f"提取到 {len(unique_parameters)} 个化工参数")
        return unique_parameters
    
    def _deduplicate_parameters(self, parameters: List[ProcessParameter]) -> List[ProcessParameter]:
        """参数去重和优化"""
        seen = set()
        unique_params = []
        
        for param in parameters:
            # 创建唯一标识
            key = (param.name, param.value, param.unit)
            
            if key not in seen:
                seen.add(key)
                unique_params.append(param)
            else:
                # 如果已存在，保留置信度更高的
                existing = next((p for p in unique_params if 
                               (p.name, p.value, p.unit) == key), None)
                if existing and param.confidence > existing.confidence:
                    unique_params.remove(existing)
                    unique_params.append(param)
        
        return unique_params
    
    def _identify_pid_elements(self, parse_result: ParseResult) -> List[PIDElement]:
        """识别P&ID图元素"""
        elements = []
        text_content = parse_result.content
        
        if not text_content:
            return elements
        
        for element_type, patterns in self.pid_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                
                for match in matches:
                    element = PIDElement(
                        element_type=element_type,
                        symbol=match.group(0),
                        description=element_type,
                        position=(0, 0),  # 需要图像处理才能获得精确位置
                        connections=[]
                    )
                    elements.append(element)
        
        logger.info(f"识别到 {len(elements)} 个P&ID元素")
        return elements
    
    def _extract_table_data(self, parse_result: ParseResult) -> List[Dict[str, Any]]:
        """提取表格数据"""
        tables_data = []
        
        for table in parse_result.tables:
            try:
                # 统一表格数据格式
                if hasattr(table, 'data') and table.data:
                    tables_data.append({
                        'table_data': table.data,
                        'headers': getattr(table, 'headers', []),
                        'dimensions': {
                            'rows': len(table.data),
                            'columns': len(table.data[0]) if table.data else 0
                        },
                        'confidence': getattr(table, 'confidence', 0.0)
                    })
                elif isinstance(table, dict):
                    tables_data.append(table)
                    
            except Exception as e:
                logger.warning(f"表格数据提取错误: {str(e)}")
                continue
        
        logger.info(f"提取到 {len(tables_data)} 个表格")
        return tables_data
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """生成分析摘要"""
        summary = f"""
=== 文档分析摘要 ===
文件: {analysis_result['file_info']['file_name']}
文档类型: {analysis_result['file_info']['document_type']}
解析器: {', '.join(analysis_result['file_info']['parsers_used'])}

内容统计:
- 内容长度: {analysis_result['content_summary']['content_length']} 字符
- 处理时间: {analysis_result['content_summary']['processing_time']:.2f} 秒
- 置信度: {analysis_result['content_summary']['confidence_score']:.2f}

提取结果:
- 化工参数: {analysis_result['extraction_summary']['total_parameters']} 个
- P&ID元素: {analysis_result['extraction_summary']['pid_elements_found']} 个
- 表格数据: {analysis_result['extraction_summary']['tables_extracted']} 个

主要参数:
"""
        
        # 添加主要参数信息
        parameters = analysis_result.get('chemical_parameters', [])
        if parameters:
            param_by_category = {}
            for param in parameters:
                category = param.get('category', '其他')
                if category not in param_by_category:
                    param_by_category[category] = []
                param_by_category[category].append(param)
            
            for category, params in param_by_category.items():
                summary += f"\n{category}:\n"
                for param in params[:3]:  # 只显示前3个
                    summary += f"  - {param['value']} {param['unit']} ({param['name']})\n"
        
        return summary
    
    def export_to_json(self, analysis_result: Dict[str, Any], output_path: Union[str, Path]):
        """导出分析结果为JSON"""
        import json
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析结果已导出到: {output_path}")
    
    def batch_analyze(self, file_paths: List[Union[str, Path]], 
                     output_dir: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
        """批量分析文档"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for file_path in file_paths:
            try:
                file_path = Path(file_path)
                analysis_result = self.analyze_document(file_path)
                results[str(file_path)] = analysis_result
                
                # 导出单个文件的分析结果
                output_file = output_dir / f"{file_path.stem}_analysis.json"
                self.export_to_json(analysis_result, output_file)
                
            except Exception as e:
                logger.error(f"批量分析失败 {file_path}: {str(e)}")
                results[str(file_path)] = {'error': str(e)}
        
        # 导出批量分析汇总
        summary_file = output_dir / "batch_analysis_summary.json"
        import json
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': len(file_paths),
                'successful_parses': sum(1 for r in results.values() if 'error' not in r),
                'failed_parses': sum(1 for r in results.values() if 'error' in r),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"批量分析完成，成功 {len([r for r in results.values() if 'error' not in r])}/{len(file_paths)} 个文件")
        return results

# 使用示例
if __name__ == "__main__":
    try:
        # 创建分析器
        analyzer = ChemDocAnalyzer()
        
        # 测试文档分析
        test_files = [
            "test_chemical_parameters.pdf",
            "test_pid_diagram.pdf", 
            "test_equipment_list.xlsx"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                print(f"\n=== 分析文档: {test_file} ===")
                
                # 执行分析
                result = analyzer.analyze_document(test_file)
                
                # 打印摘要
                print(analyzer.get_analysis_summary(result))
                
                # 保存详细结果
                output_file = f"{Path(test_file).stem}_result.json"
                analyzer.export_to_json(result, output_file)
                print(f"\n详细结果已保存到: {output_file}")
            else:
                print(f"测试文件不存在: {test_file}")
        
        # 批量分析示例
        batch_files = [f for f in test_files if Path(f).exists()]
        if batch_files:
            print(f"\n=== 批量分析测试 ===")
            batch_results = analyzer.batch_analyze(batch_files, "batch_results")
            print(f"批量分析完成，处理了 {len(batch_results)} 个文件")
            
    except Exception as e:
        print(f"分析器测试失败: {str(e)}")
        print(traceback.format_exc())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析器运行演示脚本
展示如何运行Camelot表格解析器和Backend PDF解析器
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_camelot_parser():
    """演示Camelot表格解析器的使用"""
    logger.info("=" * 60)
    logger.info("演示1: Camelot表格解析器")
    logger.info("=" * 60)
    
    try:
        from parsers.camelot_parser import CamelotTableParser, TableExtractionConfig
        
        # 初始化解析器
        parser = CamelotTableParser()
        logger.info("Camelot表格解析器初始化成功")
        
        # 配置提取参数
        config = TableExtractionConfig(
            flavor='stream',  # 使用stream模式
            pages='1-2',      # 只提取前2页
            line_scale=15
        )
        
        # 查找PDF文件
        pdf_files = list(project_root.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning("未找到PDF文件，使用模拟数据演示")
            return demo_camelot_with_mock_data()
        
        pdf_file = pdf_files[0]
        logger.info(f"使用PDF文件: {pdf_file}")
        
        # 提取表格
        tables = parser.extract_tables(pdf_file, config)
        
        logger.info(f"成功提取 {len(tables)} 个表格")
        
        # 输出结果
        for i, table in enumerate(tables):
            logger.info(f"表格 {i+1}:")
            logger.info(f"  ID: {table.table_id}")
            logger.info(f"  置信度: {table.confidence:.2%}")
            logger.info(f"  形状: {table.data.shape}")
            logger.info(f"  方法: {table.metadata.get('extraction_method', 'unknown')}")
            logger.info(f"  化工参数表: {table.metadata.get('is_chemical_table', False)}")
            
            if not table.data.empty:
                logger.info("  数据预览:")
                logger.info(f"    {table.data.head(3).to_string()}")
            logger.info("-" * 40)
        
        return tables
        
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.info("请确保已安装所需依赖: pip install camelot-py[cv] pandas")
        return None
    except Exception as e:
        logger.error(f"Camelot解析失败: {e}")
        return None

def demo_camelot_with_mock_data():
    """使用模拟数据演示Camelot功能"""
    logger.info("使用模拟数据演示Camelot表格解析器")
    
    try:
        import pandas as pd
        from parsers.camelot_parser import ExtractedTable
        
        # 创建模拟化工参数表数据
        mock_data = pd.DataFrame({
            '参数名': ['反应温度', '操作压力', '进料流量', '催化剂用量'],
            '数值': [250.0, 2.5, 150.0, 5.0],
            '单位': ['°C', 'MPa', 'm³/h', 'kg'],
            '正常范围': ['200-300°C', '1-5MPa', '100-200m³/h', '3-8kg'],
            '当前状态': ['正常', '正常', '偏高', '正常']
        })
        
        # 创建模拟表格对象
        table = ExtractedTable(
            table_id="mock_chemical_table_01",
            data=mock_data,
            metadata={
                'extraction_method': 'mock_data',
                'accuracy': 99.5,
                'is_chemical_table': True,
                'processing_time': 0.15
            },
            cells=[],
            confidence=0.95,
            processing_time=0.15,
            source_file="mock_document.pdf",
            page_number=1
        )
        
        logger.info("模拟化工参数表:")
        logger.info(f"  置信度: {table.confidence:.2%}")
        logger.info(f"  化工参数表: {table.metadata.get('is_chemical_table')}")
        logger.info(f"  数据:\n{table.data.to_string(index=False)}")
        
        return [table]
        
    except Exception as e:
        logger.error(f"模拟数据演示失败: {e}")
        return None

def demo_backend_parser():
    """演示Backend PDF解析器的使用"""
    logger.info("=" * 60)
    logger.info("演示2: Backend PDF解析器")
    logger.info("=" * 60)
    
    try:
        # 尝试导入后端解析器
        sys.path.insert(0, str(project_root / "backend"))
        from app.services.document_parsers.pdf_parser import PDFParser
        
        parser = PDFParser()
        logger.info("Backend PDF解析器初始化成功")
        
        # 查找PDF文件
        pdf_files = list(project_root.glob("**/*.pdf"))
        if not pdf_files:
            logger.warning("未找到PDF文件，使用模拟演示")
            return demo_backend_with_mock_data()
        
        pdf_file = pdf_files[0]
        logger.info(f"使用PDF文件: {pdf_file}")
        
        # 解析PDF
        result = parser.parse(pdf_file)
        
        logger.info(f"解析结果:")
        logger.info(f"  成功: {result['success']}")
        logger.info(f"  解析器: {result['parser_used']}")
        logger.info(f"  文本内容长度: {len(result['text_content'])}")
        logger.info(f"  提取的参数: {list(result['parameters'].keys())}")
        logger.info(f"  页数: {result['metadata'].get('page_count', 0)}")
        
        if result['text_content']:
            logger.info("  文本内容预览:")
            text_preview = result['text_content'][:200] + "..." if len(result['text_content']) > 200 else result['text_content']
            logger.info(f"    {text_preview}")
        
        # 显示提取的参数
        for param_type, values in result['parameters'].items():
            logger.info(f"  {param_type}: {len(values)} 个值")
            if values:
                sample = values[0]
                logger.info(f"    示例: {sample['value']} {sample.get('unit', '')}")
        
        return result
        
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.info("请确保backend模块路径正确")
        return None
    except Exception as e:
        logger.error(f"Backend解析失败: {e}")
        return None

def demo_backend_with_mock_data():
    """使用模拟数据演示Backend解析器"""
    logger.info("使用模拟数据演示Backend PDF解析器")
    
    try:
        from app.services.document_parsers.pdf_parser import PDFParser
        
        parser = PDFParser()
        
        # 创建模拟结果
        mock_result = {
            "success": True,
            "parser_used": "PDF_PARSER_V1",
            "file_path": "mock_document.pdf",
            "metadata": {
                "page_count": 3,
                "extraction_method": "PyMuPDF_direct"
            },
            "text_content": """
=== 第1页 ===
化工工艺参数表
反应温度: 250°C
操作压力: 2.5 MPa
进料流量: 150 m³/h

=== 第2页 ===
催化剂性质
纯度: 98.5%
转化率: 85.2%
选择性: 92.1%
            """,
            "tables": [],
            "images": [],
            "parameters": {
                "temperature": [
                    {"value": 250.0, "unit": "°C", "context": "反应温度: 250°C"}
                ],
                "pressure": [
                    {"value": 2.5, "unit": "MPa", "context": "操作压力: 2.5 MPa"}
                ],
                "flow": [
                    {"value": 150.0, "unit": "m³/h", "context": "进料流量: 150 m³/h"}
                ]
            },
            "errors": []
        }
        
        logger.info("模拟解析结果:")
        logger.info(f"  成功: {mock_result['success']}")
        logger.info(f"  解析器: {mock_result['parser_used']}")
        logger.info(f"  提取参数: {list(mock_result['parameters'].keys())}")
        
        return mock_result
        
    except Exception as e:
        logger.error(f"模拟数据演示失败: {e}")
        return None

def demo_unified_parser():
    """演示统一解析器的使用"""
    logger.info("=" * 60)
    logger.info("演示3: 统一解析器 (推荐)")
    logger.info("=" * 60)
    
    try:
        from parsers.unified_parser import UnifiedDocumentParser
        
        parser = UnifiedDocumentParser()
        logger.info("统一解析器初始化成功")
        
        # 查找PDF文件
        pdf_files = list(project_root.glob("**/*.pdf"))
        if not pdf_files:
            logger.info("未找到PDF文件，使用模拟数据演示")
            return demo_unified_with_mock_data()
        
        pdf_file = pdf_files[0]
        logger.info(f"使用PDF文件: {pdf_file}")
        
        # 解析文档
        result = parser.parse_document(pdf_file)
        
        logger.info(f"统一解析结果:")
        logger.info(f"  文档类型: {result.document_type}")
        logger.info(f"  解析器: {result.parser_used}")
        logger.info(f"  成功: {result.success}")
        logger.info(f"  文本长度: {len(result.text_content)}")
        logger.info(f"  表格数量: {len(result.tables)}")
        logger.info(f"  参数数量: {len(result.parameters)}")
        
        return result
        
    except Exception as e:
        logger.error(f"统一解析器演示失败: {e}")
        return None

def demo_unified_with_mock_data():
    """使用模拟数据演示统一解析器"""
    logger.info("使用模拟数据演示统一解析器")
    
    try:
        from parsers.unified_parser import UnifiedDocumentParser, DocumentType, ParseResult
        
        parser = UnifiedDocumentParser()
        
        # 手动创建模拟解析结果
        mock_result = ParseResult(
            success=True,
            file_path="mock_document.pdf",
            document_type=DocumentType.PDF,
            content="模拟的化工文档内容，包含温度、压力、流量等参数...",
            metadata={"extraction_method": "mock", "page_count": 1},
            tables=[],
            images=[],
            parameters=[{"name": "temperature", "value": 250.0, "unit": "°C"},
                       {"name": "pressure", "value": 2.5, "unit": "MPa"}],
            processing_time=0.15,
            parser_used=[],
            confidence_score=0.9
        )
        
        logger.info("统一解析器模拟结果:")
        logger.info(f"  文档类型: {mock_result.document_type}")
        logger.info(f"  成功状态: {mock_result.success}")
        logger.info(f"  置信度: {mock_result.confidence_score}")
        
        return mock_result
        
    except Exception as e:
        logger.error(f"统一解析器模拟演示失败: {e}")
        return None

def main():
    """主函数"""
    logger.info("开始解析器运行演示")
    logger.info(f"项目根目录: {project_root}")
    
    # 演示1: Camelot表格解析器
    camelot_result = demo_camelot_parser()
    
    # 演示2: Backend PDF解析器
    backend_result = demo_backend_parser()
    
    # 演示3: 统一解析器
    unified_result = demo_unified_parser()
    
    # 总结
    logger.info("=" * 60)
    logger.info("演示总结")
    logger.info("=" * 60)
    logger.info("1. Camelot表格解析器: 适合专门提取PDF中的表格数据")
    logger.info("2. Backend PDF解析器: 适合作为API服务提供解析功能")
    logger.info("3. 统一解析器: 集成所有解析引擎，智能选择最佳方案")
    logger.info("")
    logger.info("推荐使用统一解析器，获得最佳解析效果")
    
    return {
        'camelot': camelot_result,
        'backend': backend_result,
        'unified': unified_result
    }

if __name__ == "__main__":
    results = main()
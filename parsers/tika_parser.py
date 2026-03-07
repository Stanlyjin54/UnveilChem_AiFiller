#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apache Tika 文档解析器

基于Apache Tika实现多格式文档内容提取,支持1000+种文档格式。
这是实现需求文档7.4.1节中"多格式文档解析引擎"的核心组件。

支持格式包括：
- PDF, Word, Excel, PowerPoint
- HTML, XML, JSON
- 图像文件 (EXIF数据)
- 邮件文件 (EML, PST)
- 压缩文件 (ZIP, RAR)
- 以及更多格式...

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

import os
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import hashlib

try:
    from tika import tika
    from tika.tika import parse as tika_parse
    from tika.tika import parse1 as tika_parse1
    TIKA_AVAILABLE = True
except ImportError:
    TIKA_AVAILABLE = False
    logging.warning("Apache Tika未安装. 请运行: pip install tika")

logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """文档元数据结构"""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    content_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'title': self.title,
            'author': self.author,
            'subject': self.subject,
            'creator': self.creator,
            'producer': self.producer,
            'creation_date': self.creation_date,
            'modification_date': self.modification_date,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'language': self.language,
            'content_type': self.content_type
        }

@dataclass
class ParseResult:
    """解析结果数据结构"""
    content: str
    metadata: DocumentMetadata
    confidence: float
    processing_time: float
    file_path: str
    content_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'content': self.content,
            'metadata': self.metadata.to_dict(),
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'file_path': self.file_path,
            'content_type': self.content_type
        }

class TikaDocumentParser:
    """
    Apache Tika文档解析器
    
    提供统一的接口来解析各种格式的文档，提取文本内容和元数据。
    支持1000+种文档格式，是多格式文档解析引擎的核心组件。
    """
    
    def __init__(self, tika_server_url: str = "http://localhost:9998/tika"):
        """
        初始化Tika文档解析器
        
        Args:
            tika_server_url: Tika服务器的URL地址
        """
        self.tika_server_url = tika_server_url
        self._check_tika_availability()
        
        # 支持的文档类型映射
        self.supported_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.xml': 'text/xml',
            '.json': 'application/json',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf',
            '.odt': 'application/vnd.oasis.opendocument.text',
            '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
            '.odp': 'application/vnd.oasis.opendocument.presentation',
            '.csv': 'text/csv',
            '.eml': 'message/rfc822',
            '.msg': 'application/vnd.ms-outlook',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip'
        }
    
    def _check_tika_availability(self):
        """检查Tika的可用性"""
        if not TIKA_AVAILABLE:
            raise ImportError(
                "Apache Tika未安装. 请运行: pip install tika\n"
                "如果问题仍然存在,请检查Java运行时环境是否安装。"
            )
        
        # 检查Tika服务器状态
        try:
            import requests
            response = requests.get(f"{self.tika_server_url}/meta", timeout=5)
            logger.info(f"Tika服务器连接成功: {self.tika_server_url}")
        except Exception as e:
            logger.warning(f"无法连接到Tika服务器 {self.tika_server_url}: {e}")
            logger.info("将使用内联模式尝试解析文档")
    
    def parse_document(self, file_path: Union[str, Path], 
                      extract_metadata: bool = True,
                      extract_content: bool = True) -> ParseResult:
        """
        解析文档并提取内容
        
        Args:
            file_path: 文档文件路径
            extract_metadata: 是否提取元数据
            extract_content: 是否提取文本内容
            
        Returns:
            ParseResult: 解析结果
        """
        import time
        start_time = time.time()
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始解析文档: {file_path}")
        
        try:
            # 准备解析选项
            meta_data = {}
            content = ""
            
            if extract_metadata:
                meta_data = self._extract_metadata(file_path)
            
            if extract_content:
                content = self._extract_content(file_path)
            
            # 计算置信度
            confidence = self._calculate_confidence(content, meta_data)
            
            # 解析元数据
            metadata = self._parse_metadata(meta_data, file_path)
            
            processing_time = time.time() - start_time
            
            result = ParseResult(
                content=content,
                metadata=metadata,
                confidence=confidence,
                processing_time=processing_time,
                file_path=str(file_path),
                content_type=file_path.suffix.lower()
            )
            
            logger.info(f"文档解析完成，耗时: {processing_time:.2f}s, 置信度: {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"文档解析失败: {str(e)}")
            raise
    
    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """提取文档元数据"""
        try:
            # 使用Tika API提取元数据
            meta = tika_parse1("meta", str(file_path), self.tika_server_url)
            return meta
        except Exception as e:
            logger.warning(f"元数据提取失败: {e}")
            return {}
    
    def _extract_content(self, file_path: Path) -> str:
        """提取文档内容"""
        try:
            # 使用Tika API提取内容
            content = tika_parse1("text", str(file_path), self.tika_server_url)
            return content
        except Exception as e:
            logger.warning(f"内容提取失败: {e}")
            return ""
    
    def _parse_metadata(self, raw_metadata: Dict[str, Any], file_path: Path) -> DocumentMetadata:
        """解析原始元数据"""
        metadata = DocumentMetadata()
        
        # 映射Tika元数据字段到我们的数据结构
        mapping = {
            'title': ['dc:title', 'title', 'resourceName'],
            'author': ['dc:creator', 'author', 'Creator'],
            'subject': ['dc:subject', 'subject', 'Subject'],
            'creator': ['xmp:CreatorTool', 'creator', 'CreatorTool'],
            'producer': ['pdf:Producer', 'producer', 'Producer'],
            'creation_date': ['xmp:CreateDate', 'creationDate', 'Creation-Date'],
            'modification_date': ['xmp:ModifyDate', 'modificationDate', 'Last-Modified'],
            'page_count': ['xmpTPg:NPages', 'pageCount', 'Pages'],
            'word_count': ['meta:word-count', 'wordCount'],
            'language': ['dc:language', 'language']
        }
        
        for field, possible_keys in mapping.items():
            for key in possible_keys:
                if key in raw_metadata and raw_metadata[key]:
                    setattr(metadata, field, str(raw_metadata[key]))
                    break
        
        # 补充额外信息
        metadata.content_type = self._get_content_type(file_path)
        metadata.title = metadata.title or file_path.stem
        
        return metadata
    
    def _get_content_type(self, file_path: Path) -> str:
        """根据文件扩展名获取MIME类型"""
        return self.supported_types.get(file_path.suffix.lower(), 'application/octet-stream')
    
    def _calculate_confidence(self, content: str, metadata: Dict[str, Any]) -> float:
        """计算解析结果的可信度"""
        confidence = 0.0
        
        # 基于内容长度
        if content:
            content_length = len(content.strip())
            confidence += min(content_length / 1000, 0.4)  # 最多40%基于长度
        
        # 基于元数据完整性
        metadata_fields = ['title', 'author', 'subject', 'page_count']
        filled_fields = sum(1 for field in metadata_fields if metadata.get(field))
        confidence += (filled_fields / len(metadata_fields)) * 0.3  # 最多30%基于元数据
        
        # 基于Tika的成功解析
        if metadata:
            confidence += 0.3  # 基础30%分
        
        return min(confidence, 1.0)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文档格式列表"""
        return list(self.supported_types.keys())
    
    def is_format_supported(self, file_path: Union[str, Path]) -> bool:
        """检查文件格式是否支持"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_types
    
    def batch_parse(self, file_paths: List[Union[str, Path]], 
                   max_workers: int = 4) -> List[ParseResult]:
        """
        批量解析文档
        
        Args:
            file_paths: 文件路径列表
            max_workers: 最大并发数
            
        Returns:
            解析结果列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.parse_document, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"批量解析失败 {file_path}: {str(e)}")
                    # 创建错误结果
                    error_result = ParseResult(
                        content="",
                        metadata=DocumentMetadata(),
                        confidence=0.0,
                        processing_time=0.0,
                        file_path=str(file_path),
                        content_type=Path(file_path).suffix.lower()
                    )
                    results.append(error_result)
        
        return results

    def parse_with_tika_server(self, file_path: Union[str, Path], 
                              language: str = 'zh') -> Dict[str, Any]:
        """
        使用Tika服务器直接解析文档
        
        Args:
            file_path: 文档路径
            language: 语言设置
            
        Returns:
            解析结果字典
        """
        try:
            # 配置Tika服务器选项
            options = {
                'Content-Type': 'text/plain',
                'Accept': 'text/plain',
                'Content-Language': language
            }
            
            # 发送文件到Tika服务器
            with open(file_path, 'rb') as file:
                import requests
                response = requests.put(
                    f"{self.tika_server_url}/tika",
                    data=file,
                    headers=options,
                    timeout=30
                )
            
            if response.status_code == 200:
                return {
                    'content': response.text,
                    'status': 'success',
                    'status_code': response.status_code
                }
            else:
                logger.error(f"Tika服务器返回错误: {response.status_code}")
                return {
                    'content': '',
                    'status': 'error',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            logger.error(f"Tika服务器解析失败: {str(e)}")
            return {
                'content': '',
                'status': 'error',
                'error': str(e)
            }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"TikaDocumentParser(server={self.tika_server_url}, formats={len(self.supported_types)})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建解析器实例
    parser = TikaDocumentParser()
    
    # 示例文档路径（请替换为实际路径）
    test_files = [
        "test_document.pdf",
        "test_report.docx", 
        "data_sheet.xlsx"
    ]
    
    for file_path in test_files:
        try:
            if Path(file_path).exists():
                result = parser.parse_document(file_path)
                print(f"\n=== 解析结果: {file_path} ===")
                print(f"内容长度: {len(result.content)} 字符")
                print(f"置信度: {result.confidence:.2f}")
                print(f"处理时间: {result.processing_time:.2f}s")
                print(f"元数据: {result.metadata.to_dict()}")
                
                # 显示内容预览
                if result.content:
                    preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                    print(f"内容预览: {preview}")
            else:
                print(f"文件不存在: {file_path}")
                
        except Exception as e:
            print(f"解析失败 {file_path}: {str(e)}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyMuPDF文档解析器

基于PyMuPDF (fitz)实现PDF文档的全面解析,包括文本、图像、元数据等。
这是实现需求文档7.4.1节中"现代PDF解析引擎"的核心组件。

特性:
- 高性能PDF文本提取和布局分析
- 图像、矢量图形提取
- 超链接和注释处理
- 页面级别的内容访问
- 化工文档特殊结构识别
- 表格边界检测
- 文字搜索和定位

作者: UnveilChem开发团队
版本: 1.0.0
许可: MIT License
"""

import io
import re
import logging
import base64
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Iterator
from dataclasses import dataclass
from datetime import datetime

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF未安装. 请运行: pip install pymupdf")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas未安装. 表格数据处理功能受限")

logger = logging.getLogger(__name__)

@dataclass
class DocumentPage:
    """文档页面数据结构"""
    page_number: int
    text: str
    images: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    bbox: Tuple[float, float, float, float]

@dataclass
class DocumentElement:
    """文档元素"""
    type: str  # 'text', 'image', 'table', 'formula', 'chart'
    content: Any
    bbox: Tuple[float, float, float, float]
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str
    author: str
    subject: str
    keywords: List[str]
    creator: str
    producer: str
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]
    page_count: int
    language: Optional[str]

@dataclass
class PyMuPDFParseResult:
    """PyMuPDF解析结果"""
    metadata: DocumentMetadata
    pages: List[DocumentPage]
    elements: List[DocumentElement]
    full_text: str
    processing_time: float
    source_file: str
    success: bool
    error_message: Optional[str]

class PyMuPDFParser:
    """
    PyMuPDF文档解析器
    
    基于PyMuPDF实现PDF文档的高性能解析，特别针对化工文档进行优化。
    支持复杂的文档结构分析和元素提取。
    """
    
    def __init__(self):
        """初始化PyMuPDF解析器"""
        self._check_dependencies()
        
        # 化工文档特征模式
        self.chemical_patterns = {
            'temperature': [
                r'(-?\d+\.?\d*)\s*°?[CcFf]',
                r'温度[:：]?\s*(-?\d+\.?\d*)',
                r'Temperature[:：]?\s*(-?\d+\.?\d*)'
            ],
            'pressure': [
                r'(-?\d+\.?\d*)\s*[Pp]a|[Bb]ar|[Mm]Pa',
                r'压力[:：]?\s*(-?\d+\.?\d*)',
                r'Pressure[:：]?\s*(-?\d+\.?\d*)'
            ],
            'flow_rate': [
                r'(-?\d+\.?\d*)\s*[Ll]/?[Hh]|[Mm]³/?[Hh]',
                r'流量[:：]?\s*(-?\d+\.?\d*)',
                r'Flow\s*Rate[:：]?\s*(-?\d+\.?\d*)'
            ],
            'concentration': [
                r'(-?\d+\.?\d*)\s*%|[Mm]ol/?[Ll]|[Gg]/?[Ll]',
                r'浓度[:：]?\s*(-?\d+\.?\d*)',
                r'Concentration[:：]?\s*(-?\d+\.?\d*)'
            ],
            'equipment': [
                r'(反应器|换热器|分离器|塔器|泵|压缩机|反应釜)',
                r'(Reactor|Heat\s*Exchanger|Separator|Tower|Pump|Compressor)'
            ],
            'chemical_formula': [
                r'[A-Z][a-z]?\d*',
                r'[A-Z][a-z]?\d*[+-]',
                r'C\d*H\d*O\d*',
                r'化学式[:：]?\s*([A-Za-z0-9()+\-]+)'
            ]
        }
        
        # 表格检测模式
        self.table_indicators = [
            r'^[\|\-]+$',  # 表格边框
            r'^\s*[\|\:]+',  # 表格分割线
            r'^\s*-{3,}',  # 横线
            r'^\s*\+-{3,}\+',  # 网格线
        ]
        
        logger.info("PyMuPDF解析器初始化完成")
    
    def _check_dependencies(self):
        """检查依赖库的可用性"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF未安装. 请运行: pip install pymupdf"
            )
        
        logger.info(f"PyMuPDF版本: {fitz.version}")
        
        if not PANDAS_AVAILABLE:
            logger.warning("pandas未安装，表格数据处理功能受限")
    
    def parse_document(self, pdf_path: Union[str, Path]) -> PyMuPDFParseResult:
        """
        解析PDF文档
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            解析结果
        """
        import time
        start_time = time.time()
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        logger.info(f"开始解析PDF文档: {pdf_path}")
        
        try:
            # 打开PDF文档
            doc = fitz.open(str(pdf_path))
            
            try:
                # 提取文档元数据
                metadata = self._extract_metadata(doc)
                
                # 解析所有页面
                pages = []
                elements = []
                full_text_parts = []
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # 解析页面内容
                    page_data = self._parse_page(page, page_num + 1)
                    pages.append(page_data)
                    
                    # 提取页面元素
                    page_elements = self._extract_page_elements(page, page_num + 1)
                    elements.extend(page_elements)
                    
                    # 收集全文文本
                    full_text_parts.append(page_data.text)
                
                # 合并所有文本
                full_text = '\n'.join(full_text_parts)
                
                # 分析文档结构
                elements = self._analyze_document_structure(elements, full_text)
                
                processing_time = time.time() - start_time
                
                result = PyMuPDFParseResult(
                    metadata=metadata,
                    pages=pages,
                    elements=elements,
                    full_text=full_text,
                    processing_time=processing_time,
                    source_file=str(pdf_path),
                    success=True,
                    error_message=None
                )
                
                logger.info(f"PDF文档解析完成，耗时: {processing_time:.2f}秒")
                return result
                
            finally:
                doc.close()
                
        except Exception as e:
            logger.error(f"PDF文档解析失败: {str(e)}")
            return PyMuPDFParseResult(
                metadata=self._empty_metadata(),
                pages=[],
                elements=[],
                full_text="",
                processing_time=time.time() - start_time,
                source_file=str(pdf_path),
                success=False,
                error_message=str(e)
            )
    
    def _extract_metadata(self, doc) -> DocumentMetadata:
        """提取文档元数据"""
        try:
            meta = doc.metadata
            
            # 解析创建和修改日期
            creation_date = self._parse_pdf_date(meta.get('creationDate', ''))
            modification_date = self._parse_pdf_date(meta.get('modDate', ''))
            
            return DocumentMetadata(
                title=meta.get('title', ''),
                author=meta.get('author', ''),
                subject=meta.get('subject', ''),
                keywords=meta.get('keywords', '').split(',') if meta.get('keywords') else [],
                creator=meta.get('creator', ''),
                producer=meta.get('producer', ''),
                creation_date=creation_date,
                modification_date=modification_date,
                page_count=len(doc),
                language=meta.get('lang', None)
            )
        except Exception as e:
            logger.warning(f"元数据提取失败: {str(e)}")
            return self._empty_metadata()
    
    def _empty_metadata(self) -> DocumentMetadata:
        """返回空的元数据对象"""
        return DocumentMetadata(
            title="", author="", subject="", keywords=[],
            creator="", producer="", creation_date=None, modification_date=None,
            page_count=0, language=None
        )
    
    def _parse_pdf_date(self, date_str: str) -> Optional[datetime]:
        """解析PDF日期格式"""
        if not date_str:
            return None
        
        try:
            # PDF日期格式通常为: D:YYYYMMDDHHmmSSOHH'mm'
            # 简化处理，只取前14位数字
            import re
            date_match = re.search(r'(\d{14})', date_str)
            if date_match:
                date_part = date_match.group(1)
                return datetime.strptime(date_part, '%Y%m%d%H%M%S')
        except Exception as e:
            logger.warning(f"日期解析失败: {str(e)}")
        
        return None
    
    def _parse_page(self, page, page_number: int) -> DocumentPage:
        """解析单个页面"""
        try:
            # 提取文本
            text = page.get_text()
            
            # 提取图像信息
            images = self._extract_images_info(page)
            
            # 提取超链接
            links = self._extract_links(page)
            
            # 提取注释
            annotations = self._extract_annotations(page)
            
            # 获取页面边界
            bbox = page.bound()
            
            # 页面元数据
            page_metadata = {
                'rotation': page.rotation,
                'mediabox': page.mediabox,
                'cropbox': page.cropbox,
                'scale': page.zoom,
                'colorspace': page.colorspace.name if page.colorspace else None
            }
            
            return DocumentPage(
                page_number=page_number,
                text=text,
                images=images,
                links=links,
                annotations=annotations,
                metadata=page_metadata,
                bbox=bbox
            )
            
        except Exception as e:
            logger.error(f"页面解析失败 {page_number}: {str(e)}")
            return DocumentPage(
                page_number=page_number,
                text="",
                images=[],
                links=[],
                annotations=[],
                metadata={},
                bbox=(0, 0, 0, 0)
            )
    
    def _extract_images_info(self, page) -> List[Dict[str, Any]]:
        """提取页面图像信息"""
        images = []
        try:
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                # 获取图像信息
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                image_info = {
                    'index': img_index,
                    'xref': xref,
                    'width': pix.width,
                    'height': pix.height,
                    'colorspace': pix.colorspace.name if pix.colorspace else None,
                    'bpc': pix.bpc,
                    'size': pix.width * pix.height,
                    'base64': pix.tobytes().hex() if pix.n < 5 else None  # 限制为RGB图像
                }
                
                # 获取图像在页面中的位置
                try:
                    image_rects = page.get_image_rects(img)
                    if image_rects:
                        image_info['bbox'] = image_rects[0]
                except:
                    pass
                
                images.append(image_info)
                pix = None  # 释放内存
                
        except Exception as e:
            logger.warning(f"图像信息提取失败: {str(e)}")
        
        return images
    
    def _extract_links(self, page) -> List[Dict[str, Any]]:
        """提取页面超链接"""
        links = []
        try:
            for link in page.get_links():
                link_info = {
                    'bbox': link.get('bbox', (0, 0, 0, 0)),
                    'uri': link.get('uri', ''),
                    'kind': link.get('kind', 0),
                    'is_internal': link.get('page', -1) >= 0
                }
                links.append(link_info)
        except Exception as e:
            logger.warning(f"超链接提取失败: {str(e)}")
        
        return links
    
    def _extract_annotations(self, page) -> List[Dict[str, Any]]:
        """提取页面注释"""
        annotations = []
        try:
            for annot in page.annots():
                annot_info = {
                    'type': annot.type[0],
                    'content': annot.content,
                    'bbox': annot.rect,
                    'info': annot.info,
                    'colors': annot.colors
                }
                annotations.append(annot_info)
        except Exception as e:
            logger.warning(f"注释提取失败: {str(e)}")
        
        return annotations
    
    def _extract_page_elements(self, page, page_number: int) -> List[DocumentElement]:
        """提取页面元素"""
        elements = []
        
        try:
            # 获取文本块
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:  # 文本块
                    text_content = ""
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    
                    # 提取文本内容
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text_content += span.get("text", "")
                    
                    if text_content.strip():
                        # 判断文本类型
                        element_type = self._classify_text_element(text_content)
                        
                        element = DocumentElement(
                            type=element_type,
                            content=text_content.strip(),
                            bbox=bbox,
                            confidence=0.8,  # 基于PyMuPDF的默认置信度
                            metadata={'page_number': page_number}
                        )
                        elements.append(element)
                
                elif "image" in block:  # 图像块
                    # PyMuPDF的图像块识别
                    element = DocumentElement(
                        type="image",
                        content={'image_info': block},
                        bbox=block.get("bbox", (0, 0, 0, 0)),
                        confidence=1.0,
                        metadata={'page_number': page_number}
                    )
                    elements.append(element)
                    
        except Exception as e:
            logger.warning(f"页面元素提取失败: {str(e)}")
        
        return elements
    
    def _classify_text_element(self, text: str) -> str:
        """分类文本元素"""
        text = text.strip().lower()
        
        # 检查是否为标题
        if len(text) < 50 and text.endswith(('：', ':', '。', '.', '!', '!')):
            return "heading"
        
        # 检查是否为列表项
        if re.match(r'^[\d\-\*\•\·\s]+', text):
            return "list_item"
        
        # 检查是否为表格行
        if '|' in text or re.match(r'^[\-\s\|]+$', text):
            return "table_row"
        
        # 检查是否为公式
        if re.search(r'[\^\._\{\}\[\]\(\)]+', text) and any(c in text for c in '=+−×÷'):
            return "formula"
        
        # 检查是否为参数
        if any(pattern in text.lower() for patterns in self.chemical_patterns.values() 
               for pattern in patterns):
            return "parameter"
        
        return "text"
    
    def _analyze_document_structure(self, elements: List[DocumentElement], 
                                  full_text: str) -> List[DocumentElement]:
        """分析文档结构并增强元素信息"""
        try:
            # 检测标题层级
            elements = self._detect_heading_levels(elements)
            
            # 检测表格结构
            elements = self._enhance_table_detection(elements)
            
            # 增强化工参数识别
            elements = self._enhance_chemical_parameters(elements, full_text)
            
            return elements
            
        except Exception as e:
            logger.warning(f"文档结构分析失败: {str(e)}")
            return elements
    
    def _detect_heading_levels(self, elements: List[DocumentElement]) -> List[DocumentElement]:
        """检测标题层级"""
        for element in elements:
            if element.type == "heading":
                content = element.content.lower()
                
                # 基于内容特征判断标题层级
                if any(keyword in content for keyword in ['第一章', '第1章', '1.', '一、', '1 ']):
                    level = 1
                elif any(keyword in content for keyword in ['1.1', '（一）', '二、', '2.']):
                    level = 2
                elif any(keyword in content for keyword in ['1.1.1', '（二）', '三、', '3.']):
                    level = 3
                else:
                    level = 4
                
                element.metadata['heading_level'] = level
        
        return elements
    
    def _enhance_table_detection(self, elements: List[DocumentElement]) -> List[DocumentElement]:
        """增强表格检测"""
        table_elements = []
        
        for element in elements:
            if element.type == "table_row":
                content = element.content
                
                # 检查是否为表格的分隔行
                if re.match(r'^[\|\-\s]+$', content):
                    element.type = "table_separator"
                    element.confidence = 0.9
                
                # 检查是否为表格数据行
                elif '|' in content or '\t' in content:
                    # 分析表格数据
                    cells = re.split(r'[\|\t]+', content)
                    if len(cells) >= 2:
                        element.type = "table_data"
                        element.metadata['cells'] = cells
                        element.confidence = 0.8
                
                table_elements.append(element)
        
        return table_elements
    
    def _enhance_chemical_parameters(self, elements: List[DocumentElement], 
                                   full_text: str) -> List[DocumentElement]:
        """增强化工参数识别"""
        for element in elements:
            if element.type in ["text", "parameter"]:
                content = element.content
                
                # 识别化工参数
                detected_params = {}
                for param_type, patterns in self.chemical_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if param_type not in detected_params:
                                detected_params[param_type] = []
                            detected_params[param_type].append({
                                'value': match.group(1) if match.groups() else match.group(0),
                                'position': match.span(),
                                'full_match': match.group(0)
                            })
                
                if detected_params:
                    element.type = "chemical_parameter"
                    element.metadata['parameters'] = detected_params
                    element.confidence = 0.9
                else:
                    # 基于关键词进行分类
                    if any(keyword in content.lower() for keyword in ['温度', 'pressure', 'flow']):
                        element.type = "parameter"
                        element.confidence = 0.7
        
        return elements
    
    def extract_images(self, pdf_path: Union[str, Path], 
                      output_dir: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        """
        提取PDF中的所有图像
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录，为None时不保存文件
            
        Returns:
            图像信息列表
        """
        pdf_path = Path(pdf_path)
        
        if output_dir is not None:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        images_info = []
        
        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # 创建图像信息
                    image_info = {
                        'source_file': str(pdf_path),
                        'page_number': page_num + 1,
                        'image_index': img_index,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.colorspace.name if pix.colorspace else None,
                        'bpc': pix.bpc,
                        'size': pix.width * pix.height
                    }
                    
                    # 如果指定了输出目录，保存图像
                    if output_dir is not None:
                        output_path = output_dir / f"{pdf_path.stem}_p{page_num+1}_i{img_index}.png"
                        pix.save(str(output_path))
                        image_info['saved_path'] = str(output_path)
                    
                    images_info.append(image_info)
                    pix = None  # 释放内存
            
            doc.close()
            
            logger.info(f"从{pdf_path}提取了{len(images_info)}个图像")
            return images_info
            
        except Exception as e:
            logger.error(f"图像提取失败: {str(e)}")
            return []
    
    def search_text(self, pdf_path: Union[str, Path], 
                   search_term: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        在PDF中搜索文本
        
        Args:
            pdf_path: PDF文件路径
            search_term: 搜索词
            case_sensitive: 是否区分大小写
            
        Returns:
            搜索结果列表
        """
        pdf_path = Path(pdf_path)
        results = []
        
        try:
            doc = fitz.open(str(pdf_path))
            
            # 设置搜索选项
            flags = fitz.TEXT_IGNORECASE if not case_sensitive else 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 在页面中搜索
                areas = page.search_for(search_term, flags=flags)
                
                for rect in areas:
                    result = {
                        'text': search_term,
                        'page_number': page_num + 1,
                        'bbox': rect,
                        'position': (rect.x0, rect.y0, rect.x1, rect.y1)
                    }
                    results.append(result)
            
            doc.close()
            
            logger.info(f"搜索'{search_term}'找到{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"文本搜索失败: {str(e)}")
            return []
    
    def get_page_text(self, pdf_path: Union[str, Path], 
                     page_number: int) -> str:
        """
        获取指定页面的文本内容
        
        Args:
            pdf_path: PDF文件路径
            page_number: 页码（从1开始）
            
        Returns:
            页面文本内容
        """
        pdf_path = Path(pdf_path)
        
        try:
            doc = fitz.open(str(pdf_path))
            
            if 1 <= page_number <= len(doc):
                page = doc[page_number - 1]
                text = page.get_text()
                doc.close()
                return text
            else:
                doc.close()
                raise ValueError(f"页码超出范围: {page_number}")
                
        except Exception as e:
            logger.error(f"获取页面文本失败: {str(e)}")
            return ""
    
    def convert_to_text(self, pdf_path: Union[str, Path], 
                       output_path: Optional[Union[str, Path]] = None) -> str:
        """
        将PDF转换为纯文本
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文本文件路径，为None时不保存文件
            
        Returns:
            提取的文本内容
        """
        result = self.parse_document(pdf_path)
        
        if output_path is not None:
            output_path = Path(output_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.full_text)
            logger.info(f"文本已保存到: {output_path}")
        
        return result.full_text
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"PyMuPDFParser()"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建解析器实例
    parser = PyMuPDFParser()
    
    # 示例PDF路径（请替换为实际路径）
    test_pdf = "test_chemical_document.pdf"
    
    try:
        if Path(test_pdf).exists():
            # 解析文档
            result = parser.parse_document(test_pdf)
            
            print(f"\n=== 解析结果 ===")
            print(f"成功: {result.success}")
            print(f"页数: {result.metadata.page_count}")
            print(f"处理时间: {result.processing_time:.2f}秒")
            
            if result.success:
                print(f"\n文档元数据:")
                print(f"  标题: {result.metadata.title}")
                print(f"  作者: {result.metadata.author}")
                print(f"  主题: {result.metadata.subject}")
                
                print(f"\n文档内容预览:")
                print(result.full_text[:500] + "..." if len(result.full_text) > 500 else result.full_text)
                
                print(f"\n文档元素统计:")
                element_types = {}
                for element in result.elements:
                    element_types[element.type] = element_types.get(element.type, 0) + 1
                
                for element_type, count in element_types.items():
                    print(f"  {element_type}: {count}")
        else:
            print(f"测试文件不存在: {test_pdf}")
            
    except Exception as e:
        print(f"PDF解析失败: {str(e)}")
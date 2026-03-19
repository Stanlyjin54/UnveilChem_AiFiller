#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDFMathTranslate 翻译服务
通过子进程调用 pdf2zh 命令行工具进行 PDF 翻译
支持 PDFMathTranslate v2.x (pdf2zh-next)
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os

from .pdf_to_word_translator import PDFToWordTranslator

logger = logging.getLogger(__name__)

PDF2ZH_DIR = Path(__file__).parent.parent / "temp_pdf2zh"
PYTHON312_EXE = Path(__file__).parent.parent.parent / "python.exe"
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_CACHE_DIR = PROJECT_ROOT / "models" / "doclayout"

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

def check_pdf2zh_available() -> bool:
    """检查 pdf2zh 是否可用"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pdf2zh"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        if result.returncode == 0:
            logger.info(f"pdf2zh 已安装: {result.stdout}")
            return True
        else:
            logger.warning(f"pdf2zh 未安装")
            return False
    except Exception as e:
        logger.warning(f"PDF2Zh 可用性检查失败: {e}")
        return False


class PDFMathTranslateService:
    """PDFMathTranslate 翻译服务类"""
    
    def __init__(self):
        """初始化翻译服务"""
        self.pdf2zh_dir = PDF2ZH_DIR
        self.python_exe = Path(sys.executable)
        self._available = None
        self.word_translator = PDFToWordTranslator()
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        if self._available is not None:
            return self._available
        self._available = check_pdf2zh_available()
        return self._available
        
    def translate_pdf(
        self,
        pdf_path: str,
        output_dir: str = "",
        lang_in: str = "en",
        lang_out: str = "zh",
        mode: str = "mono"
    ) -> Dict[str, Any]:
        """
        翻译 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            lang_in: 源语言
            lang_out: 目标语言
            mode: 翻译模式 (mono: 单语, dual: 双语)
            
        Returns:
            翻译结果
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {pdf_path}"
            }
        
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = pdf_path.parent / f"{pdf_path.stem}_translated"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # 构建命令，调用 pdf2zh 的 extract_text 函数，使用原始字符串避免路径转义问题
            # 设置本地模型缓存目录和离线模式
            # 使用 Ollama 本地翻译调用 HY-MT1.5-1.8B 模型
            model_dir = str(MODEL_CACHE_DIR).replace('\\', '\\\\')
            pdf_path_str = str(pdf_path).replace('\\', '/')
            cmd = [
                str(self.python_exe),
                "-c", f"import os; os.environ['HF_HUB_CACHE']=r'{model_dir}'; os.environ['HF_HUB_OFFLINE']='1'; from pdf2zh.pdf2zh import extract_text; extract_text(files=['{pdf_path_str}'], lang_in='{lang_in}', lang_out='{lang_out}', service='ollama', model='demonbyron/HY-MT1.5-1.8B:latest', thread=4)"
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=600
            )
            
            if result.returncode != 0:
                logger.error(f"翻译失败: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "翻译失败"
                }
            
            # pdf2zh 1.7.9 在当前目录生成翻译文件
            mono_file = Path.cwd() / f"{pdf_path.stem}-zh.pdf"
            dual_file = Path.cwd() / f"{pdf_path.stem}-dual.pdf"
            
            return {
                "success": True,
                "mono_pdf": str(mono_file) if mono_file.exists() else None,
                "dual_pdf": str(dual_file) if dual_file.exists() else None,
                "output_dir": str(output_path)
            }
            
        except subprocess.TimeoutExpired:
            logger.error("翻译超时")
            return {
                "success": False,
                "error": "翻译超时"
            }
        except Exception as e:
            logger.error(f"翻译错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def translate_pdf_to_word(
        self,
        pdf_path: str,
        output_path: str,
        lang_in: str = "en",
        lang_out: str = "zh",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        使用 PDF → Word → Ollama 方案翻译 PDF
        
        Args:
            pdf_path: PDF 文件路径
            output_path: 输出 Word 文件路径
            lang_in: 源语言
            lang_out: 目标语言
            progress_callback: 进度回调函数
            
        Returns:
            翻译结果
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {pdf_path}"
            }
        
        try:
            result = await self.word_translator.translate_pdf_to_word(
                str(pdf_path),
                output_path,
                lang_in,
                lang_out,
                progress_callback
            )
            
            return {
                "success": True,
                "output_file": result
            }
        except Exception as e:
            logger.error(f"PDF → Word 翻译错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }


pdf_math_translate_service = PDFMathTranslateService()

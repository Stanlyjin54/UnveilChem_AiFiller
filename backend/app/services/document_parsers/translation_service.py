#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档翻译服务
"""

from transformers import pipeline
from typing import Dict, Any, Optional

class TranslationService:
    """文档翻译服务类"""
    
    def __init__(self):
        """初始化翻译服务"""
        # 延迟加载翻译模型
        self.translator = None
        self._model_loaded = False
        
        # 初始化化学专业术语词典
        self.chemical_terms = {
            "catalyst": "催化剂",
            "reaction": "反应",
            "temperature": "温度",
            "pressure": "压力",
            "yield": "产率",
            "selectivity": "选择性",
            "conversion": "转化率",
            "reactant": "反应物",
            "product": "产物",
            "solvent": "溶剂",
            "reactor": "反应器"
        }
    
    def _load_translator(self):
        """延迟加载翻译模型"""
        if self._model_loaded:
            return
        try:
            from transformers import pipeline
            self.translator = pipeline(
                "translation", 
                model="Helsinki-NLP/opus-mt-en-zh",
                device=-1
            )
            self._model_loaded = True
            print("Hugging Face翻译模型加载成功")
        except Exception as e:
            print(f"Hugging Face翻译模型加载失败: {e}")
            print("将使用术语词典进行简单翻译")
            self._model_loaded = True
    
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        """翻译文本
        
        Args:
            text: 待翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            翻译后的文本
        """
        if not text:
            return ""
        
        # 延迟加载翻译模型
        if not self._model_loaded:
            self._load_translator()
        
        translated_text = text
        
        # 先应用化学专业术语词典
        for term, translation in self.chemical_terms.items():
            translated_text = translated_text.replace(term, translation)
        
        # 如果Hugging Face模型可用，使用模型进行翻译
        if self.translator is not None:
            try:
                result = self.translator(text, max_length=512)
                model_translated = result[0]["translation_text"]
                # 对模型翻译结果再次应用术语词典
                for term, translation in self.chemical_terms.items():
                    model_translated = model_translated.replace(term, translation)
                translated_text = model_translated
            except Exception as e:
                print(f"Hugging Face翻译失败: {e}")
                # 继续使用术语词典翻译结果
        
        return translated_text
    
    def add_chemical_term(self, term: str, translation: str) -> None:
        """添加化学专业术语
        
        Args:
            term: 英文术语
            translation: 中文翻译
        """
        self.chemical_terms[term] = translation
    
    def batch_translate(self, texts: list[str], source_lang: str = "en", target_lang: str = "zh") -> list[str]:
        """批量翻译文本
        
        Args:
            texts: 待翻译的文本列表
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            翻译后的文本列表
        """
        return [self.translate(text, source_lang, target_lang) for text in texts]
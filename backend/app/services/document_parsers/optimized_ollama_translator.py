#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的 Ollama 翻译器
继承自 pdf2zh 的 BaseTranslator，添加禁用 thinking 的优化
"""

import ollama
from pdf2zh.translator import BaseTranslator


class OptimizedOllamaTranslator(BaseTranslator):
    """优化的 Ollama 翻译器，禁用 thinking 模式"""
    
    def __init__(self, service, lang_out, lang_in, model):
        lang_out = 'zh-CN' if lang_out == 'auto' else lang_out
        lang_in = 'en' if lang_in == 'auto' else lang_in
        super().__init__(service, lang_out, lang_in, model)
        
        self.options = {
            "temperature": 0,
            "num_predict": -1
        }
        self.client = ollama.Client()
    
    def translate(self, text) -> str:
        """翻译文本，使用优化的 system prompt 禁用 thinking"""
        system_prompt = "You are a professional, authentic machine translation engine. Please translate directly without any explanation or reasoning process."
        
        user_prompt = f"""Translate the following markdown source text to {self.lang_out}. Keep the formula notation $v*$ unchanged. Output translation directly without any additional text.

Source Text: {text}
Translated Text:"""
        
        response = self.client.chat(
            model=self.model,
            options=self.options,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        return response["message"]["content"].strip()

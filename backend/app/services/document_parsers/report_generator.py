#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成服务
"""

from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any, Optional
import os
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import json

class ReportGenerator:
    """报告生成服务类"""
    
    def __init__(self):
        """初始化报告生成服务"""
        # 初始化Jinja2环境
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
        
        # 初始化报告样式
        self.styles = getSampleStyleSheet()
    
    def generate_report(self, template_name: str, data: Dict[str, Any], output_format: str = "pdf") -> bytes:
        """生成报告
        
        Args:
            template_name: 模板名称
            data: 报告数据
            output_format: 输出格式，支持pdf、word、html
            
        Returns:
            报告内容的字节流
        """
        try:
            # 加载模板
            template = self.env.get_template(template_name)
            
            # 渲染模板
            rendered_content = template.render(data)
            
            # 根据输出格式生成报告
            if output_format == "pdf":
                return self._generate_pdf(rendered_content)
            elif output_format == "word":
                return self._generate_word(rendered_content)
            elif output_format == "html":
                return rendered_content.encode("utf-8")
            else:
                raise ValueError(f"不支持的输出格式: {output_format}")
        except Exception as e:
            print(f"报告生成失败: {e}")
            raise
    
    def _generate_pdf(self, content: str) -> bytes:
        """生成PDF报告
        
        Args:
            content: 报告内容
            
        Returns:
            PDF报告的字节流
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
            temp_path = temp.name
        
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(temp_path, pagesize=letter)
            elements = []
            
            # 添加内容
            for paragraph in content.split("\n"):
                if paragraph.strip():
                    elements.append(Paragraph(paragraph, self.styles["Normal"]))
                    elements.append(Spacer(1, 12))
            
            # 生成PDF
            doc.build(elements)
            
            # 读取PDF内容
            with open(temp_path, "rb") as f:
                pdf_content = f.read()
            
            return pdf_content
        finally:
            # 删除临时文件
            os.unlink(temp_path)
    
    def _generate_word(self, content: str) -> bytes:
        """生成Word报告
        
        Args:
            content: 报告内容
            
        Returns:
            Word报告的字节流
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp:
            temp_path = temp.name
        
        try:
            # 创建Word文档
            doc = Document()
            
            # 添加内容
            for paragraph in content.split("\n"):
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            
            # 保存Word文档
            doc.save(temp_path)
            
            # 读取Word内容
            with open(temp_path, "rb") as f:
                word_content = f.read()
            
            return word_content
        finally:
            # 删除临时文件
            os.unlink(temp_path)
    
    def create_template(self, template_name: str, template_content: str) -> None:
        """创建报告模板
        
        Args:
            template_name: 模板名称
            template_content: 模板内容
        """
        template_path = os.path.join(self.template_dir, template_name)
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)
    
    def list_templates(self) -> list[str]:
        """列出所有可用模板
        
        Returns:
            模板名称列表
        """
        return [f for f in os.listdir(self.template_dir) if f.endswith(".html") or f.endswith(".txt")]
    
    def generate_chart(self, chart_type: str, data: Dict[str, Any]) -> str:
        """生成图表
        
        Args:
            chart_type: 图表类型，支持line、bar、pie
            data: 图表数据
            
        Returns:
            图表的HTML或Base64编码
        """
        if chart_type == "line":
            return self._generate_line_chart(data)
        elif chart_type == "bar":
            return self._generate_bar_chart(data)
        elif chart_type == "pie":
            return self._generate_pie_chart(data)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")
    
    def _generate_line_chart(self, data: Dict[str, Any]) -> str:
        """生成折线图
        
        Args:
            data: 图表数据
            
        Returns:
            图表的HTML
        """
        fig = go.Figure(data=go.Scatter(
            x=data["x"],
            y=data["y"],
            mode="lines+markers"
        ))
        
        fig.update_layout(
            title=data.get("title", "折线图"),
            xaxis_title=data.get("x_label", "X轴"),
            yaxis_title=data.get("y_label", "Y轴")
        )
        
        return fig.to_html(full_html=False)
    
    def _generate_bar_chart(self, data: Dict[str, Any]) -> str:
        """生成柱状图
        
        Args:
            data: 图表数据
            
        Returns:
            图表的HTML
        """
        fig = go.Figure(data=go.Bar(
            x=data["x"],
            y=data["y"]
        ))
        
        fig.update_layout(
            title=data.get("title", "柱状图"),
            xaxis_title=data.get("x_label", "X轴"),
            yaxis_title=data.get("y_label", "Y轴")
        )
        
        return fig.to_html(full_html=False)
    
    def _generate_pie_chart(self, data: Dict[str, Any]) -> str:
        """生成饼图
        
        Args:
            data: 图表数据
            
        Returns:
            图表的HTML
        """
        fig = go.Figure(data=go.Pie(
            labels=data["labels"],
            values=data["values"]
        ))
        
        fig.update_layout(
            title=data.get("title", "饼图")
        )
        
        return fig.to_html(full_html=False)
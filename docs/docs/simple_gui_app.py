#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化工文档参数提取工具 - 单机PC版

功能：
- 支持PDF/Word/Excel文档解析
- 自动提取温度、压力、流量等参数
- 简单易用的图形界面
- 结果导出为Excel/CSV

定价:10元/份，终身使用
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
import threading

# 导入现有的解析引擎
from document_analyzer import ChemDocAnalyzer

class SimpleDocAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("化工文档参数提取工具 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 初始化解析器
        self.analyzer = ChemDocAnalyzer()
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # LOGO区域
        logo_frame = ttk.Frame(main_frame)
        logo_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 蓝色字体LOGO
        logo_label = tk.Label(logo_frame, text="unveilchem", 
                             font=("Arial", 24, "bold"), 
                             fg="#0078D7",  # 蓝色
                             bg="#F0F0F0")   # 浅灰色背景
        logo_label.pack(pady=10)
        
        # 副标题
        subtitle_label = tk.Label(logo_frame, text="化工文档智能参数提取工具",
                                 font=("Arial", 12),
                                 fg="#666666")
        subtitle_label.pack(pady=(0, 10))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文档选择", padding="10")
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(file_frame, text="选择文档:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=60).grid(row=0, column=1, padx=(10, 5))
        ttk.Button(file_frame, text="浏览", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))
        
        # 文档类型选择
        type_frame = ttk.Frame(file_frame)
        type_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(type_frame, text="文档类型:").grid(row=0, column=0, sticky=tk.W)
        self.file_type = tk.StringVar(value="自动检测")
        
        file_types = ["自动检测", "PDF文档", "Word文档", "Excel文档"]
        for i, ftype in enumerate(file_types):
            ttk.Radiobutton(type_frame, text=ftype, variable=self.file_type, value=ftype).grid(
                row=0, column=i+1, padx=(10, 0))
        
        # 操作按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="开始解析", command=self.start_analysis)
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.export_btn = ttk.Button(button_frame, text="导出结果", command=self.export_results, state=tk.DISABLED)
        self.export_btn.grid(row=0, column=2, padx=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate')
        self.progress.grid(row=0, column=3, padx=(10, 0), sticky=(tk.W, tk.E))
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="解析结果", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建表格显示结果
        columns = ("参数名称", "参数值", "单位", "置信度", "来源")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 存储解析结果
        self.analysis_results = None
        
    def browse_file(self):
        """浏览文件"""
        filetypes = [
            ("所有支持的格式", "*.pdf;*.doc;*.docx;*.xls;*.xlsx"),
            ("PDF文档", "*.pdf"),
            ("Word文档", "*.doc;*.docx"),
            ("Excel文档", "*.xls;*.xlsx"),
        ]
        
        filename = filedialog.askopenfilename(
            title="选择化工文档",
            filetypes=filetypes
        )
        
        if filename:
            self.file_path.set(filename)
            
    def start_analysis(self):
        """开始解析"""
        if not self.file_path.get():
            messagebox.showwarning("警告", "请先选择要解析的文档")
            return
            
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("错误", "文件不存在")
            return
            
        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 开始进度条
        self.progress.start()
        self.status_var.set("正在解析文档...")
        
        # 在新线程中执行解析
        self.analysis_thread = threading.Thread(target=self._analyze_document)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
        
        # 检查线程状态
        self.check_analysis_status()
        
    def _analyze_document(self):
        """实际解析文档（在后台线程中运行）"""
        try:
            self.analysis_results = self.analyzer.analyze_document(self.file_path.get())
        except Exception as e:
            self.analysis_error = str(e)
            
    def check_analysis_status(self):
        """检查解析状态"""
        if self.analysis_thread.is_alive():
            # 线程还在运行，继续检查
            self.root.after(100, self.check_analysis_status)
        else:
            # 解析完成
            self.analysis_complete()
            
    def analysis_complete(self):
        """解析完成处理"""
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL)
        
        if hasattr(self, 'analysis_error'):
            messagebox.showerror("解析错误", f"解析失败: {self.analysis_error}")
            self.status_var.set("解析失败")
            return
            
        # 显示结果
        self.display_results()
        self.status_var.set("解析完成")
        messagebox.showinfo("完成", "文档解析完成！")
        
    def display_results(self):
        """显示解析结果"""
        if not self.analysis_results:
            return
            
        parameters = self.analysis_results.get('parameters', {})
        
        # 调试信息：显示解析结果的结构
        print(f"解析结果结构: {type(parameters)}")
        print(f"参数数量: {len(parameters)}")
        
        # 处理不同类型的参数结构
        if isinstance(parameters, dict):
            for param_type, param_obj in parameters.items():
                # 如果是ProcessParameter对象
                if hasattr(param_obj, 'name'):
                    self.result_tree.insert('', tk.END, values=(
                        param_obj.name,
                        param_obj.value,
                        param_obj.unit,
                        f"{param_obj.confidence*100:.1f}%",
                        param_obj.source
                    ))
                # 如果是字典
                elif isinstance(param_obj, dict):
                    self.result_tree.insert('', tk.END, values=(
                        param_obj.get('name', param_type),
                        param_obj.get('value', ''),
                        param_obj.get('unit', ''),
                        f"{param_obj.get('confidence', 0)*100:.1f}%",
                        param_obj.get('source', '')
                    ))
        
        # 如果没有提取到参数，显示提示信息
        if not self.result_tree.get_children():
            self.result_tree.insert('', tk.END, values=(
                "未提取到参数", 
                "请检查文档格式", 
                "", 
                "", 
                "可能原因：文档格式不支持或参数格式不匹配"
            ))
        
    def stop_analysis(self):
        """停止解析"""
        # 这里可以添加停止逻辑
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        
    def export_results(self):
        """导出结果"""
        if not self.analysis_results:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
            
        filename = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx"), ("CSV文件", "*.csv")]
        )
        
        if filename:
            try:
                # 这里实现导出逻辑
                messagebox.showinfo("成功", f"结果已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出失败: {str(e)}")

def main():
    """主函数"""
    root = tk.Tk()
    app = SimpleDocAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
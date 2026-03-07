#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化工文档参数提取工具 - 高级版

功能：
- 双工作区：左侧参数列表（可复制），右侧文档全文显示
- 参数高亮定位：点击参数可定位到文档对应位置
- 用户注册验证系统
- API关联功能
- 智能参数录入助手
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
from pathlib import Path
import threading
import json
import re
from datetime import datetime

# 导入现有的解析引擎
from document_analyzer import ChemDocAnalyzer

class AdvancedDocAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("unveilchem - 智能参数录入助手 v2.0")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        # 初始化解析器
        self.analyzer = ChemDocAnalyzer()
        
        # 用户信息
        self.user_info = {
            'registered': False,
            'username': '',
            'api_key': ''
        }
        
        # 存储文档全文
        self.document_text = ""
        self.parameter_positions = {}
        
        # 创建界面
        self.create_widgets()
        
        # 检查用户注册状态
        self.check_registration()
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 顶部LOGO区域
        self.create_logo_area()
        
        # 主工作区 - 水平分割
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        # 左侧：参数工作区
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # 右侧：文档工作区
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        # 配置左侧参数工作区
        self.create_parameter_workspace(left_frame)
        
        # 配置右侧文档工作区
        self.create_document_workspace(right_frame)
        
        # 底部状态栏和操作区
        self.create_bottom_area()
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
    def create_logo_area(self):
        """创建LOGO区域"""
        logo_frame = ttk.Frame(self.root)
        logo_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=(10, 0))
        
        # 图像LOGO
        try:
            # 加载PNG图像
            image_path = os.path.join(os.path.dirname(__file__), "unveilchem_logo.png")
            img = Image.open(image_path)
            img = img.resize((60, 60), Image.Resampling.LANCZOS)
            photo_img = ImageTk.PhotoImage(img)
            
            # 创建图像标签
            image_label = tk.Label(logo_frame, image=photo_img, bg="#F0F0F0")
            image_label.image = photo_img  # 保持引用
            image_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception as e:
            # 图像加载失败时显示备用文字
            backup_label = tk.Label(logo_frame, text="UC", font=("Arial", 18, "bold"), bg="#1E40AF", fg="white", width=3)
            backup_label.pack(side=tk.LEFT, padx=(0, 10))

        # 蓝色字体LOGO
        logo_label = tk.Label(logo_frame, text="unveilchem", 
                             font=('Arial', 24, 'bold'), 
                             fg="#0078D7",
                             bg="#F0F0F0")
        logo_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # 副标题
        subtitle_label = tk.Label(logo_frame, text="智能参数录入助手",
                                 font=("Arial", 12),
                                 fg="#666666")
        subtitle_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # 用户状态显示
        self.user_status_label = tk.Label(logo_frame, text="未注册",
                                         font=("Arial", 10),
                                         fg="#FF6B6B")
        self.user_status_label.pack(side=tk.RIGHT)
        
        # 注册/设置按钮
        settings_btn = ttk.Button(logo_frame, text="用户设置", 
                                 command=self.show_settings)
        settings_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
    def create_parameter_workspace(self, parent):
        """创建参数工作区"""
        # 参数列表标题
        param_label = ttk.Label(parent, text="提取的参数列表", font=("Arial", 12, "bold"))
        param_label.pack(pady=(0, 10))
        
        # 参数表格
        columns = ("参数名称", "参数值", "单位", "操作")
        self.param_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        # 设置列宽
        self.param_tree.column("参数名称", width=120)
        self.param_tree.column("参数值", width=100)
        self.param_tree.column("单位", width=80)
        self.param_tree.column("操作", width=100)
        
        for col in columns:
            self.param_tree.heading(col, text=col)
        
        # 滚动条
        param_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.param_tree.yview)
        self.param_tree.configure(yscrollcommand=param_scrollbar.set)
        
        self.param_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定点击事件
        self.param_tree.bind("<ButtonRelease-1>", self.on_parameter_click)
        
        # 操作按钮区域
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="复制选中参数", 
                  command=self.copy_selected_parameter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="复制全部参数", 
                  command=self.copy_all_parameters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="录入到目标软件", 
                  command=self.export_to_target).pack(side=tk.LEFT)
        
    def create_document_workspace(self, parent):
        """创建文档工作区"""
        # 文档显示标题
        doc_label = ttk.Label(parent, text="文档全文显示", font=("Arial", 12, "bold"))
        doc_label.pack(pady=(0, 10))
        
        # 文档文本显示区域
        self.doc_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, width=60, height=25)
        self.doc_text.pack(fill=tk.BOTH, expand=True)
        self.doc_text.config(state=tk.DISABLED)  # 初始为只读
        
        # 搜索框
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(search_frame, text="搜索", 
                  command=self.search_text).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="高亮参数", 
                  command=self.highlight_parameters).pack(side=tk.LEFT)
        
    def create_bottom_area(self):
        """创建底部区域"""
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        # 文件选择区域
        file_frame = ttk.Frame(bottom_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="选择文档:").pack(side=tk.LEFT)
        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=60)
        file_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(file_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT, padx=(0, 10))
        
        # 文档类型选择
        type_frame = ttk.Frame(file_frame)
        type_frame.pack(side=tk.LEFT)
        
        ttk.Label(type_frame, text="文档类型:").pack(side=tk.LEFT)
        self.file_type = tk.StringVar(value="自动检测")
        
        file_types = ["自动检测", "PDF文档", "Word文档", "Excel文档"]
        for ftype in file_types:
            ttk.Radiobutton(type_frame, text=ftype, variable=self.file_type, value=ftype).pack(side=tk.LEFT, padx=(5, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="开始解析", command=self.start_analysis)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_analysis, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 进度条
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(button_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
    def browse_file(self):
        """浏览文件"""
        filetypes = [
            ("所有支持的格式", "*.pdf;*.doc;*.docx;*.xls;*.xlsx"),
            ("PDF文档", "*.pdf"),
            ("Word文档", "*.doc;*.docx"),
            ("Excel文档", "*.xls;*.xlsx"),
        ]
        
        filename = filedialog.askopenfilename(title="选择化工文档", filetypes=filetypes)
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
        
        # 清空结果
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
            
        # 清空文档显示
        self.doc_text.config(state=tk.NORMAL)
        self.doc_text.delete(1.0, tk.END)
        self.doc_text.config(state=tk.DISABLED)
        
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
        """实际解析文档"""
        try:
            self.analysis_results = self.analyzer.analyze_document(self.file_path.get())
            # 提取文档全文（简化版）
            self.document_text = self.extract_document_text(self.file_path.get())
        except Exception as e:
            self.analysis_error = str(e)
            
    def extract_document_text(self, file_path):
        """提取文档全文（简化实现）"""
        try:
            # 这里应该根据文件类型使用相应的解析库
            # 暂时返回简单文本
            return f"文档内容预览: {os.path.basename(file_path)}\n\n" + \
                   "这是文档全文的预览区域。实际实现中，这里会显示文档的完整文本内容，\n" + \
                   "并且参数值会在文档中高亮显示，方便用户核对。"
        except:
            return "无法提取文档全文"
            
    def check_analysis_status(self):
        """检查解析状态"""
        if self.analysis_thread.is_alive():
            self.root.after(100, self.check_analysis_status)
        else:
            self.analysis_complete()
            
    def analysis_complete(self):
        """解析完成处理"""
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if hasattr(self, 'analysis_error'):
            messagebox.showerror("解析错误", f"解析失败: {self.analysis_error}")
            self.status_var.set("解析失败")
            return
            
        # 显示结果
        self.display_results()
        self.status_var.set("解析完成")
        
    def display_results(self):
        """显示解析结果"""
        if not self.analysis_results:
            return
            
        parameters = self.analysis_results.get('parameters', {})
        
        # 清空参数表格
        for item in self.param_tree.get_children():
            self.param_tree.delete(item)
            
        # 显示参数
        if isinstance(parameters, dict):
            for param_type, param_obj in parameters.items():
                if hasattr(param_obj, 'name'):
                    # ProcessParameter对象
                    self.param_tree.insert('', tk.END, values=(
                        param_obj.name,
                        param_obj.value,
                        param_obj.unit,
                        "点击复制"
                    ), tags=(param_type,))
                elif isinstance(param_obj, dict):
                    # 字典格式
                    self.param_tree.insert('', tk.END, values=(
                        param_obj.get('name', param_type),
                        param_obj.get('value', ''),
                        param_obj.get('unit', ''),
                        "点击复制"
                    ), tags=(param_type,))
        
        # 显示文档全文
        self.doc_text.config(state=tk.NORMAL)
        self.doc_text.delete(1.0, tk.END)
        self.doc_text.insert(tk.END, self.document_text)
        self.doc_text.config(state=tk.DISABLED)
        
        # 如果没有提取到参数
        if not self.param_tree.get_children():
            self.param_tree.insert('', tk.END, values=(
                "未提取到参数", "", "", ""
            ))
            
    def on_parameter_click(self, event):
        """参数点击事件"""
        item = self.param_tree.selection()
        if item:
            values = self.param_tree.item(item, 'values')
            if values and values[0] != "未提取到参数":
                # 复制参数值到剪贴板
                param_value = f"{values[0]}: {values[1]} {values[2]}"
                self.root.clipboard_clear()
                self.root.clipboard_append(param_value)
                messagebox.showinfo("复制成功", f"已复制参数: {param_value}")
                
                # 在文档中高亮显示该参数
                self.highlight_specific_parameter(values[0])
                
    def copy_selected_parameter(self):
        """复制选中参数"""
        item = self.param_tree.selection()
        if item:
            values = self.param_tree.item(item, 'values')
            if values and values[0] != "未提取到参数":
                param_value = f"{values[0]}: {values[1]} {values[2]}"
                self.root.clipboard_clear()
                self.root.clipboard_append(param_value)
                messagebox.showinfo("复制成功", f"已复制参数: {param_value}")
                
    def copy_all_parameters(self):
        """复制全部参数"""
        all_params = []
        for item in self.param_tree.get_children():
            values = self.param_tree.item(item, 'values')
            if values and values[0] != "未提取到参数":
                all_params.append(f"{values[0]}: {values[1]} {values[2]}")
                
        if all_params:
            param_text = "\n".join(all_params)
            self.root.clipboard_clear()
            self.root.clipboard_append(param_text)
            messagebox.showinfo("复制成功", "已复制全部参数到剪贴板")
        else:
            messagebox.showwarning("警告", "没有可复制的参数")
            
    def highlight_parameters(self):
        """高亮显示所有参数"""
        # 这里实现参数高亮逻辑
        messagebox.showinfo("提示", "参数高亮功能将在完整版中实现")
        
    def highlight_specific_parameter(self, param_name):
        """高亮特定参数"""
        # 这里实现特定参数高亮逻辑
        pass
        
    def search_text(self):
        """搜索文本"""
        search_term = self.search_var.get()
        if search_term:
            # 这里实现搜索功能
            messagebox.showinfo("搜索", f"搜索功能将在完整版中实现: {search_term}")
            
    def export_to_target(self):
        """录入到目标软件"""
        if not self.user_info['registered']:
            messagebox.showwarning("需要注册", "请先完成用户注册才能使用API功能")
            self.show_settings()
            return
            
        # 这里实现API调用逻辑
        messagebox.showinfo("API功能", "参数录入API功能将在完整版中实现")
        
    def show_settings(self):
        """显示用户设置窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("用户设置")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 用户注册区域
        reg_frame = ttk.LabelFrame(settings_window, text="用户注册", padding=10)
        reg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(reg_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(reg_frame, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(reg_frame, text="API密钥:").grid(row=1, column=0, sticky=tk.W, pady=5)
        api_entry = ttk.Entry(reg_frame, width=30, show="*")
        api_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 如果已注册，显示当前信息
        if self.user_info['registered']:
            username_entry.insert(0, self.user_info['username'])
            api_entry.insert(0, self.user_info['api_key'])
            
        def save_registration():
            username = username_entry.get()
            api_key = api_entry.get()
            
            if username and api_key:
                self.user_info.update({
                    'registered': True,
                    'username': username,
                    'api_key': api_key
                })
                self.save_user_info()
                self.update_user_status()
                settings_window.destroy()
                messagebox.showinfo("成功", "用户信息已保存")
            else:
                messagebox.showwarning("警告", "请填写完整的用户信息")
                
        ttk.Button(reg_frame, text="保存", command=save_registration).grid(row=2, column=1, sticky=tk.E, pady=10)
        
    def check_registration(self):
        """检查用户注册状态"""
        try:
            if os.path.exists("user_info.json"):
                with open("user_info.json", "r", encoding="utf-8") as f:
                    self.user_info = json.load(f)
        except:
            pass
            
        self.update_user_status()
        
    def save_user_info(self):
        """保存用户信息"""
        try:
            with open("user_info.json", "w", encoding="utf-8") as f:
                json.dump(self.user_info, f, ensure_ascii=False, indent=2)
        except:
            pass
            
    def update_user_status(self):
        """更新用户状态显示"""
        if self.user_info['registered']:
            self.user_status_label.config(
                text=f"已注册: {self.user_info['username']}",
                fg="#28A745"
            )
        else:
            self.user_status_label.config(text="未注册", fg="#FF6B6B")
            
    def stop_analysis(self):
        """停止解析"""
        self.progress.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("已停止")

def main():
    """主函数"""
    root = tk.Tk()
    app = AdvancedDocAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
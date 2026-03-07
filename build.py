#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化工文档参数提取工具 - 打包脚本
"""

import os
import sys
import subprocess

def main():
    print("=" * 50)
    print("化工文档参数提取工具 - 打包脚本")
    print("=" * 50)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 使用最简单的格式，避免转义问题
    data_file1 = "--add-data=document_analyzer.py;."
    data_file2 = "--add-data=unveilchem_logo.png;."
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=化工文档参数提取工具",
        data_file1,
        data_file2,
        "advanced_gui_app.py"
    ]
    
    print("开始打包应用...")
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ 打包成功！")
        print("可执行文件位置: dist/化工文档参数提取工具.exe")
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return 1
    
    print("=" * 50)
    input("按Enter键退出...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
@echo off
echo ========================================
echo 化工文档参数提取工具 - 打包脚本
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python,请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 安装PyInstaller...
    pip install pyinstaller
)

REM 创建打包目录
if not exist "dist" mkdir dist

REM 打包应用
echo 开始打包应用...
pyinstaller --onefile --windowed --name="化工文档参数提取工具" --icon=app.ico simple_gui_app.py

if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo ========================================
echo 打包成功！
echo 可执行文件位置: dist\\化工文档参数提取工具.exe
echo ========================================

pause
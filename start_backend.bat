@echo off
echo ========================================
echo 启动 UnveilChem 后端服务
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python,请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查是否在虚拟环境中
if not defined VIRTUAL_ENV (
    echo 警告: 建议在虚拟环境中运行
    echo 创建虚拟环境: python -m venv venv
    echo 激活虚拟环境: venv\Scripts\activate
)

REM 进入后端目录
cd backend

REM 检查依赖是否安装
if not exist "venv" (
    echo 安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo 启动后端服务...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
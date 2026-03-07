@echo off
echo ========================================
echo 启动 UnveilChem 前端服务
echo ========================================

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js,请先安装Node.js 16+
    pause
    exit /b 1
)

REM 检查npm是否安装
npm --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到npm
    pause
    exit /b 1
)

REM 进入前端目录
cd frontend

REM 检查依赖是否安装
if not exist "node_modules" (
    echo 安装依赖...
    npm install
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo 启动前端服务...
npm run dev

pause
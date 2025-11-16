@echo off
chcp 65001
echo ====================================
echo 金融多模态知识库问答系统
echo ====================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo [1] 快速启动（推荐）
echo [2] 仅生成结果文件
echo [3] 启动API服务器
echo [4] 运行测试
echo [5] 安装依赖
echo.

set /p choice="请选择操作 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 正在运行快速启动...
    python quick_start.py
) else if "%choice%"=="2" (
    echo.
    echo 正在生成结果文件...
    python generate_result.py
) else if "%choice%"=="3" (
    echo.
    echo 正在启动API服务器...
    echo 访问 http://localhost:8000/docs 查看API文档
    python api_server.py
) else if "%choice%"=="4" (
    echo.
    echo 正在运行测试...
    python test_system.py
) else if "%choice%"=="5" (
    echo.
    echo 正在安装依赖...
    pip install -r requirements.txt
) else (
    echo.
    echo 无效选择
)

echo.
pause


@echo off
echo 启动网络扰动测试系统
echo =============================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH
    echo 请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查Streamlit是否安装
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo 启动网络扰动测试系统...
echo 应用将在浏览器中自动打开
echo 测试网络延迟、丢包等扰动对分布式系统的影响
echo.
streamlit run streamlit_app.py

pause

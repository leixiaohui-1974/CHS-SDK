@echo off
echo 启动集成扰动框架测试系统
echo ====================================
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

echo 启动集成扰动框架测试系统...
echo 应用将在浏览器中自动打开
echo.
echo ⚙️ 主要功能特色：
echo - 智能时间点捕获，解决"未命中关键时间点"问题
echo - 图文并茂的可视化界面，包含业务流程图
echo - 多维度结果分析图表，6个子图全面展示
echo - 完全简体中文界面，操作简单直观
echo - 实时状态监控和历史结果管理
echo.
streamlit run app.py

pause

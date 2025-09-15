@echo off
echo 启动水位变化计算测试系统
echo ==================================
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

echo 启动水位变化计算测试系统...
echo 应用将在浏览器中自动打开
echo.
echo 📐 水位计算测试功能：
echo - 获取和分析水库完整物理参数
echo - 解析库容曲线并计算分段表面积
echo - 验证理论水位变化计算的准确性
echo - 预测扰动效果并提供优化建议
echo.
streamlit run streamlit_app.py

pause

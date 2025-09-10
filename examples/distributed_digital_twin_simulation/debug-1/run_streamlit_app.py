#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动执行器和传感器干扰分析 Streamlit 应用
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """安装必要的依赖包"""
    requirements_file = Path(__file__).parent / "requirements_streamlit.txt"
    
    if requirements_file.exists():
        print("正在安装依赖包...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ])
            print("✅ 依赖包安装完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖包安装失败: {e}")
            return False
    else:
        print("⚠️  requirements文件不存在，跳过依赖安装")
    
    return True

def run_streamlit_app():
    """运行Streamlit应用"""
    app_file = Path(__file__).parent / "actuator_sensor_disturbance_streamlit.py"
    
    if not app_file.exists():
        print(f"❌ 应用文件不存在: {app_file}")
        return False
    
    print("🚀 启动Streamlit应用...")
    print("📱 应用将在浏览器中打开")
    print("🔗 默认地址: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_file),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n⏹️  应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🔧 执行器和传感器干扰分析系统")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return
    
    # 安装依赖
    if not install_requirements():
        return
    
    # 运行应用
    run_streamlit_app()

if __name__ == "__main__":
    main()

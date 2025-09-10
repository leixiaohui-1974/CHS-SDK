#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的启动脚本 - 专门用于 debug-1 目录
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """主函数"""
    print("🔧 执行器和传感器干扰分析系统 - Debug版本")
    print("=" * 60)
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    app_file = current_dir / "actuator_sensor_disturbance_streamlit.py"
    
    if not app_file.exists():
        print(f"❌ 应用文件不存在: {app_file}")
        return
    
    print(f"📁 工作目录: {current_dir}")
    print(f"📄 应用文件: {app_file}")
    print()
    
    # 检查依赖
    print("🔍 检查依赖包...")
    try:
        import streamlit
        import pandas
        import numpy
        import matplotlib
        import scipy
        import plotly
        print("✅ 所有依赖包已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install streamlit pandas numpy matplotlib scipy plotly")
        return
    
    print()
    print("🚀 启动Streamlit应用...")
    print("📱 应用将在浏览器中打开")
    print("🔗 默认地址: http://localhost:8501")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 60)
    
    try:
        # 切换到应用目录
        os.chdir(current_dir)
        
        # 启动Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "actuator_sensor_disturbance_streamlit.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n⏹️  应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")
        print("\n🔧 故障排除建议:")
        print("1. 确保所有依赖包已安装")
        print("2. 检查端口8501是否被占用")
        print("3. 尝试使用其他端口: streamlit run actuator_sensor_disturbance_streamlit.py --server.port 8502")

if __name__ == "__main__":
    main()

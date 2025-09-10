#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Streamlit 应用的基本功能
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """测试所有必要的导入"""
    print("🔍 测试依赖包导入...")
    
    try:
        import streamlit as st
        print("✅ streamlit 导入成功")
    except ImportError as e:
        print(f"❌ streamlit 导入失败: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas 导入成功")
    except ImportError as e:
        print(f"❌ pandas 导入失败: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ numpy 导入成功")
    except ImportError as e:
        print(f"❌ numpy 导入失败: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✅ matplotlib 导入成功")
    except ImportError as e:
        print(f"❌ matplotlib 导入失败: {e}")
        return False
    
    try:
        from scipy import signal
        print("✅ scipy 导入成功")
    except ImportError as e:
        print(f"❌ scipy 导入失败: {e}")
        return False
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        print("✅ plotly 导入成功")
    except ImportError as e:
        print(f"❌ plotly 导入失败: {e}")
        return False
    
    return True

def test_analyzer():
    """测试分析器类"""
    print("\n🔍 测试分析器类...")
    
    try:
        from actuator_sensor_disturbance_streamlit import ActuatorSensorDisturbanceAnalyzer
        
        analyzer = ActuatorSensorDisturbanceAnalyzer()
        print("✅ 分析器类实例化成功")
        
        # 测试示例数据生成
        sample_data = analyzer.generate_sample_data(duration=100, dt=1.0)
        print(f"✅ 示例数据生成成功，数据形状: {sample_data.shape}")
        
        # 测试特征提取
        features = analyzer.extract_disturbance_features(sample_data)
        print(f"✅ 特征提取成功，提取了 {len(features)} 个特征组")
        
        return True
    except Exception as e:
        print(f"❌ 分析器测试失败: {e}")
        return False

def test_files():
    """测试必要文件是否存在"""
    print("\n🔍 检查必要文件...")
    
    required_files = [
        "actuator_sensor_disturbance_streamlit.py",
        "simple_flow_diagram.md",
        "README_streamlit.md",
        "requirements_streamlit.txt"
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("🧪 Streamlit 应用功能测试")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 依赖包测试失败，请安装必要的包")
        print("运行: pip install streamlit pandas numpy matplotlib scipy plotly")
        return False
    
    # 测试文件
    if not test_files():
        print("\n❌ 文件检查失败，请确保所有必要文件存在")
        return False
    
    # 测试分析器
    if not test_analyzer():
        print("\n❌ 分析器测试失败，请检查代码")
        return False
    
    print("\n🎉 所有测试通过！应用可以正常运行")
    print("\n🚀 运行应用:")
    print("   python start_app.py")
    print("   或")
    print("   streamlit run actuator_sensor_disturbance_streamlit.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

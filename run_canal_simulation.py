#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渠道仿真系统快速启动脚本

简化版本的仿真启动脚本，用于快速测试和演示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 检查必要的依赖
try:
    import matplotlib.pyplot as plt
    print("✅ matplotlib 可用")
except ImportError:
    print("⚠️  matplotlib 未安装，将跳过图表显示")
    print("   安装命令: pip install matplotlib")

try:
    from canal_gate_reservoir_simulation import main
    
    print("🚀 启动渠道-闸门-渠道-水库仿真系统...\n")
    
    # 运行主仿真
    success = main()
    
    if success:
        print("\n✅ 仿真成功完成!")
        print("\n📊 结果文件:")
        print("   - canal_gate_reservoir_simulation_results.png (可视化图表)")
        print("\n💡 提示:")
        print("   - 可以修改 canal_gate_reservoir_simulation.py 中的参数来调试不同场景")
        print("   - GateController 类控制闸门开度策略")
        print("   - 调整组件参数可以观察不同的系统响应")
    else:
        print("❌ 仿真执行失败，请检查错误信息")
        
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("\n🔧 可能的解决方案:")
    print("1. 确保在正确的 Python 环境中运行")
    print("2. 检查 PYTHONPATH 设置")
    print("3. 确认 core_lib 模块可访问")
    
except Exception as e:
    print(f"❌ 运行错误: {e}")
    import traceback
    traceback.print_exc()

input("\n按 Enter 键退出...")

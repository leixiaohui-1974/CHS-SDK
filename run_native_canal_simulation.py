#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动基于Core-Lib原生架构的渠道仿真系统

这个脚本使用core_lib的原生组件和架构：
- UnifiedCanal, Gate, Reservoir (物理对象)
- SimulationHarness (仿真执行器)
- 消息总线 (组件通信)
- 不重新定义任何控制器类
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """检查依赖项"""
    print("🔍 检查依赖项...")
    
    missing_deps = []
    
    # 检查matplotlib
    try:
        import matplotlib.pyplot as plt
        print("  ✅ matplotlib")
    except ImportError:
        missing_deps.append("matplotlib")
        print("  ❌ matplotlib")
    
    # 检查numpy
    try:
        import numpy as np
        print("  ✅ numpy")
    except ImportError:
        missing_deps.append("numpy")
        print("  ❌ numpy")
    
    # 检查core_lib组件
    try:
        from core_lib.physical_objects import UnifiedCanal, Gate, Reservoir
        print("  ✅ physical_objects")
    except ImportError as e:
        print(f"  ❌ physical_objects: {e}")
        return False
    
    try:
        from core_lib.core_engine.testing.simulation_harness import SimulationHarness
        print("  ✅ simulation_harness")
    except ImportError as e:
        print(f"  ❌ simulation_harness: {e}")
        return False
    
    try:
        from core_lib.core.event_bus import get_global_event_bus
        print("  ✅ event_bus")
    except ImportError as e:
        print(f"  ❌ event_bus: {e}")
        return False
    
    if missing_deps:
        print(f"\n⚠️  缺少依赖项: {', '.join(missing_deps)}")
        print("安装命令:")
        for dep in missing_deps:
            print(f"  pip install {dep}")
        return False
    
    print("✅ 所有依赖项检查通过")
    return True


def run_simulation():
    """运行仿真"""
    try:
        from canal_gate_reservoir_simulation_native import main
        
        print("\n🚀 启动基于Core-Lib原生架构的仿真系统...")
        print("📋 系统特点:")
        print("  - 使用core_lib原生SimulationHarness")
        print("  - 通过消息总线控制闸门")
        print("  - 完整的物理对象拓扑连接")
        print("  - 不重新定义控制器类")
        print()
        
        # 运行仿真
        success = main()
        
        if success:
            print("\n🎊 仿真成功完成!")
            print("\n📁 输出文件:")
            print("  - native_canal_simulation_results.png (结果图表)")
            print("\n💡 说明:")
            print("  - 本仿真完全基于core_lib原生架构")
            print("  - 演示了渠道-闸门-渠道-水库的完整水力学仿真")
            print("  - 包含时间驱动的智能闸门控制策略")
            print("  - 可视化展示了水位、流量、控制响应等关键指标")
            
        return success
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 确保canal_gate_reservoir_simulation_native.py存在")
        print("2. 检查Python路径设置")
        print("3. 确认core_lib模块可正常访问")
        return False
        
    except Exception as e:
        print(f"❌ 仿真执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🌊 Core-Lib原生架构渠道仿真系统")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖项检查失败，无法继续")
        return False
    
    print()
    
    # 运行仿真
    success = run_simulation()
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        
        if not success:
            print("\n💡 提示: 如果遇到问题，请检查:")
            print("  1. Python环境配置")
            print("  2. core_lib模块路径")
            print("  3. 依赖项安装")
        
        input("\n按 Enter 键退出...")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        sys.exit(0 if locals().get('success', False) else 1)

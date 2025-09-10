#!/usr/bin/env python3
"""
测试 pump_efficiency.py 的修复
"""

import sys
import os
sys.path.insert(0, '.')

def test_pump_efficiency_import():
    """测试导入和基本功能"""
    try:
        from examples.agent_based.05_equipment_control.01_pump_control.pump_efficiency import (
            create_efficiency_optimization_system,
            PumpEfficiencyModel,
            EfficiencyOptimizationAgent,
            VariableDemandAgent
        )
        print("✅ 导入成功")
        
        # 测试系统创建
        harness, message_bus, demand_topic, control_topic, pump_station, pump_params = create_efficiency_optimization_system()
        print("✅ 系统创建成功")
        
        # 测试效率模型
        efficiency_model = PumpEfficiencyModel(pump_params)
        print("✅ 效率模型创建成功")
        
        # 测试代理创建
        demand_agent = VariableDemandAgent("test_demand", message_bus, demand_topic)
        efficiency_agent = EfficiencyOptimizationAgent(
            "test_efficiency", message_bus, demand_topic, pump_station, efficiency_model
        )
        print("✅ 代理创建成功")
        
        print("🎉 所有测试通过！pump_efficiency.py 修复成功")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pump_efficiency_import()
    if success:
        print("\n✅ pump_efficiency.py 现在可以正常使用了！")
    else:
        print("\n❌ 还需要进一步修复")

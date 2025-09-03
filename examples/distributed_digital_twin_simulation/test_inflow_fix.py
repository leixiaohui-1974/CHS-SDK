#!/usr/bin/env python3
"""
测试inflow参数修复效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from core_lib.io.yaml_loader import SimulationBuilder

def test_inflow_parameter():
    """测试components.yml中的inflow参数是否正确设置到水库组件"""
    print("=== 测试inflow参数修复效果 ===")
    
    # 创建仿真构建器并加载配置
    scenario_path = '.'
    builder = SimulationBuilder(scenario_path)
    harness = builder.load()
    
    # 获取水库组件
    components = harness.components
    print(f"\n找到 {len(components)} 个组件:")
    
    for comp_name, component in components.items():
        print(f"- {comp_name}: {type(component).__name__}")
        if hasattr(component, '_inflow'):
            print(f"  当前_inflow值: {component._inflow}")
        if hasattr(component, '_params') and 'inflow' in component._params:
            print(f"  参数中的inflow值: {component._params['inflow']}")
    
    # 特别检查Upstream_Reservoir
    upstream_reservoir = components.get('Upstream_Reservoir')
    
    if upstream_reservoir:
        print(f"\n=== Upstream_Reservoir详细信息 ===")
        print(f"类型: {type(upstream_reservoir).__name__}")
        print(f"_inflow属性: {upstream_reservoir._inflow}")
        print(f"参数: {upstream_reservoir._params}")
        
        # 检查components.yml中配置的inflow值是否正确设置
        expected_inflow = 100.0  # 根据components.yml中的配置
        if upstream_reservoir._inflow == expected_inflow:
            print(f"✅ 成功！inflow参数已正确设置为 {expected_inflow}")
        else:
            print(f"❌ 失败！期望inflow为 {expected_inflow}，实际为 {upstream_reservoir._inflow}")
    else:
        print("❌ 未找到Upstream_Reservoir组件")

if __name__ == '__main__':
    test_inflow_parameter()
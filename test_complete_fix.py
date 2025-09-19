#!/usr/bin/env python3
"""
完整修复流量平衡问题的测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.core_engine.testing.simulation_harness import SimulationHarness
    from core_lib.physical_objects.reservoir import Reservoir
    from core_lib.physical_objects.gate import Gate
    from core_lib.physical_objects.unified_canal import UnifiedCanal
    from core_lib.physical_objects.disturbance_node import DisturbanceNode
    print("✅ 成功导入核心组件")
except ImportError as e:
    print(f"❌ 导入核心库失败: {e}")
    sys.exit(1)

def create_balanced_system():
    """创建流量平衡的仿真系统"""
    try:
        config = {
            'start_time': 0,
            'end_time': 30,
            'time_step': 5
        }
        harness = SimulationHarness(config)
        
        # 1. 上游水库 - 作为系统驱动
        reservoir = Reservoir(
            name="Reservoir_1",
            initial_state={'water_level': 100.0, 'volume': 5000000.0, 'inflow': 0.0, 'outflow': 50.0},
            parameters={'surface_area': 50000.0, 'capacity': 10000000.0, 'min_level': 80.0, 'max_level': 120.0}
        )
        
        # 2. 渠道 - 基本流量传递
        channel = UnifiedCanal(
            name="Channel_2",
            initial_state={'water_level': 62.83, 'inflow': 50.0, 'outflow': 50.0},
            parameters={
                'length': 1000.0,
                'width': 10.0,
                'roughness': 0.025,
                'slope': 0.001,
                'model_type': 'integral_delay',
                'gain': 0.1,
                'delay': 10.0,
                'inflow': 50.0
            }
        )
        
        # 3. 分水口（简单传递，不分流）
        diversion = DisturbanceNode(
            name="Diversion_1",
            initial_state={'outflow': 50.0},
            parameters={
                'timeSeries': [
                    [0, 0.0],   # 不分流
                    [30, 0.0]
                ]
            }
        )
        
        # 4. 闸门
        gate = Gate(
            name="Gate_1",
            initial_state={'opening': 0.5, 'outflow': 25.0},
            parameters={
                'width': 5.0,
                'discharge_coefficient': 0.65,
                'max_opening': 2.0
            }
        )
        
        # 5. 下游水库 - 平衡出流
        downstream_reservoir = Reservoir(
            name="Downstream_Reservoir",
            initial_state={'water_level': 57.83, 'volume': 1000000.0, 'inflow': 0.0, 'outflow': 25.0},
            parameters={
                'surface_area': 20000.0, 
                'capacity': 5000000.0, 
                'min_level': 50.0, 
                'max_level': 70.0,
                'outflow': 25.0  # 设置合理的出流以平衡系统
            }
        )
        
        # 添加组件
        harness.add_component("Reservoir_1", reservoir)
        harness.add_component("Channel_2", channel)
        harness.add_component("Diversion_1", diversion)
        harness.add_component("Gate_1", gate)
        harness.add_component("Downstream_Reservoir", downstream_reservoir)
        
        # 定义连接
        harness.add_connection("Reservoir_1", "Channel_2")
        harness.add_connection("Channel_2", "Diversion_1")
        harness.add_connection("Diversion_1", "Gate_1")
        harness.add_connection("Gate_1", "Downstream_Reservoir")
        
        # 构建仿真
        harness.build()
        
        print(f"✅ 成功创建平衡系统: {len(harness.components)} 个组件")
        return harness
        
    except Exception as e:
        print(f"❌ 创建仿真失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_complete_solution():
    """测试完整解决方案"""
    harness = create_balanced_system()
    if not harness:
        return False
    
    print("\n=== 完整解决方案测试 ===")
    
    # 记录初始状态
    print("初始状态检查:")
    for comp_name, component in harness.components.items():
        state = component.get_state()
        print(f"  {comp_name}: 入流={state.get('inflow', 0):.1f}, 出流={state.get('outflow', 0):.1f}")
    
    # 运行几步仿真
    for step in range(3):
        print(f"\n--- 步骤 {step}: t={harness.t:.1f}s ---")
        
        harness.step()
        
        # 检查状态
        print("仿真后状态:")
        system_inflow = 0
        system_outflow = 0
        
        for comp_name, component in harness.components.items():
            state = component.get_state()
            inflow = state.get('inflow', 0)
            outflow = state.get('outflow', 0)
            
            print(f"  {comp_name}: 入流={inflow:.1f}, 出流={outflow:.1f}")
            
            # 计算系统边界流量
            if comp_name == "Reservoir_1":
                # 上游水库的固定入流作为系统入流
                fixed_inflow = getattr(component, '_inflow', 0) if hasattr(component, '_inflow') else 0
                system_inflow = fixed_inflow
            elif comp_name == "Downstream_Reservoir":
                system_outflow = outflow
        
        balance = system_inflow - system_outflow
        print(f"系统流量平衡: 入流={system_inflow:.1f}, 出流={system_outflow:.1f}, 平衡={balance:.1f}")
        
        # 检查平衡性
        if abs(balance) < 5.0:  # 容许误差5 m³/s
            print("✅ 流量基本平衡")
        else:
            print("⚠️  流量不平衡")
    
    return True

def main():
    print("🔧 完整流量平衡解决方案测试")
    print("=" * 60)
    
    success = test_complete_solution()
    
    if success:
        print("\n🎉 测试完成！")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
详细分析水库出流和流量守恒问题
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

def create_test_simulation():
    """创建测试仿真"""
    try:
        config = {
            'start_time': 0,
            'end_time': 50,
            'time_step': 5
        }
        harness = SimulationHarness(config)
        
        # 1. 上游水库
        reservoir = Reservoir(
            name="Reservoir_1",
            initial_state={'water_level': 100.0, 'volume': 5000000.0, 'inflow': 50.0, 'outflow': 0.0},
            parameters={'surface_area': 50000.0, 'capacity': 10000000.0, 'min_level': 80.0, 'max_level': 120.0}
        )
        
        # 2. 渠道
        channel = UnifiedCanal(
            name="Channel_2",
            initial_state={'water_level': 62.83, 'inflow': 50.0, 'outflow': 0.0},
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
        
        # 3. 分水口（简化，不分流）
        diversion = DisturbanceNode(
            name="Diversion_1",
            initial_state={'outflow': 0.0},
            parameters={
                'timeSeries': [
                    [0, 0.0],   # 不分流，全部通过
                    [50, 0.0]
                ]
            }
        )
        
        # 4. 闸门
        gate = Gate(
            name="Gate_1",
            initial_state={'opening': 0.5, 'outflow': 0.0},
            parameters={
                'width': 5.0,
                'discharge_coefficient': 0.65,
                'max_opening': 2.0
            }
        )
        
        # 5. 下游水库 - 根据记忆，需要调整出流参数来实现水量平衡
        downstream_reservoir = Reservoir(
            name="Downstream_Reservoir",
            initial_state={'water_level': 57.83, 'volume': 1000000.0, 'inflow': 0.0, 'outflow': 0.0},
            parameters={
                'surface_area': 20000.0, 
                'capacity': 5000000.0, 
                'min_level': 50.0, 
                'max_level': 70.0,
                'outflow': 15.0  # 设置合理的出流以接近上游入流
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
        
        print(f"✅ 成功创建仿真: {len(harness.components)} 个组件")
        return harness
        
    except Exception as e:
        print(f"❌ 创建仿真失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_flow_balance():
    """分析流量平衡问题"""
    harness = create_test_simulation()
    if not harness:
        return False
    
    print("\n=== 详细流量平衡分析 ===")
    
    for step in range(5):
        print(f"\n--- 步骤 {step}: t={harness.t:.1f}s ---")
        
        # 仿真前获取状态
        print("仿真前状态:")
        for comp_name, component in harness.components.items():
            state = component.get_state()
            print(f"  {comp_name}: 入流={state.get('inflow', 0):.3f}, 出流={state.get('outflow', 0):.3f}, "
                  f"水位={state.get('water_level', 0):.3f}, 库容={state.get('volume', 0):.0f}")
        
        # 执行一步仿真
        harness.step()
        
        # 仿真后获取状态
        print("仿真后状态:")
        total_inflow = 0
        total_outflow = 0
        
        for comp_name, component in harness.components.items():
            state = component.get_state()
            inflow = state.get('inflow', 0)
            outflow = state.get('outflow', 0)
            
            print(f"  {comp_name}: 入流={inflow:.3f}, 出流={outflow:.3f}, "
                  f"水位={state.get('water_level', 0):.3f}, 库容={state.get('volume', 0):.0f}")
            
            # 边界组件计算总入流和出流
            if comp_name == "Reservoir_1":
                # 上游水库：使用其参数中的固定入流作为系统总入流
                reservoir_inflow = component._params.get('inflow', 0)
                total_inflow += reservoir_inflow  # 系统总入流
            elif comp_name == "Downstream_Reservoir":
                total_outflow += outflow  # 系统总出流
        
        print(f"系统流量平衡: 总入流={total_inflow:.3f}, 总出流={total_outflow:.3f}, "
              f"不平衡量={total_inflow - total_outflow:.3f}")
        
        # 分析问题
        downstream_state = harness.components["Downstream_Reservoir"].get_state()
        if downstream_state.get('outflow', 0) == 0:
            print("⚠️  问题发现: 下游水库出流为0")
        
        # 检查分水口逻辑
        diversion_state = harness.components["Diversion_1"].get_state()
        diversion_inflow = diversion_state.get('inflow', 0)
        diversion_outflow = diversion_state.get('outflow', 0)
        diversion_flow = diversion_state.get('diversion_flow', 0)
        print(f"分水口分析: 入流={diversion_inflow:.3f}, 出流={diversion_outflow:.3f}, "
              f"分流={diversion_flow:.3f}")

def main():
    print("🔧 水库出流和流量平衡问题分析")
    print("=" * 60)
    
    analyze_flow_balance()

if __name__ == "__main__":
    main()
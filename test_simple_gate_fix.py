#!/usr/bin/env python3
"""
简化的闸门流量稳定性测试
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

def create_simple_test():
    """创建简单的测试场景"""
    print("🔧 创建简单测试场景...")
    
    try:
        # 创建仿真平台
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
                'delay': 10.0,  # 使用'delay'而不是'delay_time'
                'inflow': 50.0  # 需要在parameters中指定初始入流
            }
        )
        
        # 3. 分水口（带时间序列）
        diversion = DisturbanceNode(
            name="Diversion_1",
            initial_state={'outflow': 0.0},
            parameters={
                'timeSeries': [
                    [0, 0.0],
                    [20, 50.0],
                    [40, 0.0]
                ]
            }
        )
        
        # 4. 闸门（固定开度）
        gate = Gate(
            name="Gate_1",
            initial_state={'opening': 0.5, 'outflow': 0.0},
            parameters={
                'width': 5.0,
                'discharge_coefficient': 0.65,
                'max_opening': 2.0
            }
        )
        
        # 5. 下游水库（提供下游水位）
        downstream_reservoir = Reservoir(
            name="Downstream_Reservoir",
            initial_state={'water_level': 57.83, 'volume': 1000000.0, 'inflow': 0.0, 'outflow': 20.0},
            parameters={'surface_area': 20000.0, 'capacity': 5000000.0, 'min_level': 50.0, 'max_level': 70.0}
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

def run_test():
    """运行测试"""
    harness = create_simple_test()
    if not harness:
        return False
    
    print("\n=== 开始仿真测试 ===")
    
    # 记录数据
    data = []
    
    for step in range(10):
        harness.step()
        
        # 获取状态
        gate_state = harness.components['Gate_1'].get_state()
        channel_state = harness.components['Channel_2'].get_state()
        diversion_state = harness.components['Diversion_1'].get_state()
        
        step_data = {
            'step': step,
            'time': harness.t,
            'gate_opening': gate_state.get('opening', 0),
            'gate_flow': gate_state.get('outflow', 0),
            'channel_level': channel_state.get('water_level', 0),
            'diversion_flow': diversion_state.get('diversion_flow', 0)
        }
        data.append(step_data)
        
        print(f"步骤 {step}: t={harness.t:.1f}s, 闸门开度={step_data['gate_opening']:.3f}, "
              f"闸门流量={step_data['gate_flow']:.3f}, 渠道水位={step_data['channel_level']:.3f}m, "
              f"分流量={step_data['diversion_flow']:.3f}")
    
    # 分析结果
    print("\n=== 分析结果 ===")
    
    gate_flows = [d['gate_flow'] for d in data]
    flow_variation = max(gate_flows) - min(gate_flows)
    
    channel_levels = [d['channel_level'] for d in data]
    level_variation = max(channel_levels) - min(channel_levels)
    
    print(f"闸门流量变化: {flow_variation:.3f} m³/s")
    print(f"渠道水位变化: {level_variation:.3f} m")
    
    # 判断是否改善
    if flow_variation < 20.0 and level_variation < 10.0:
        print("✅ 问题已得到改善！")
        return True
    else:
        print("⚠️  问题仍需进一步解决")
        return False

def main():
    print("🔧 闸门流量稳定性测试")
    print("=" * 50)
    
    success = run_test()
    
    if success:
        print("\n🎉 测试通过！")
        return 0
    else:
        print("\n⚠️  测试未完全通过")
        return 1

if __name__ == "__main__":
    sys.exit(main())
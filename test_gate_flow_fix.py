#!/usr/bin/env python3
"""
测试脚本：验证闸门开度不变但流量变化问题的修复
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core_lib.io.enhanced_yaml_loader import YamlSimulationLoader
    print("✅ 成功导入核心库")
except ImportError:
    # 尝试使用其他导入方式
    try:
        from core_lib.core_engine.testing.simulation_harness import SimulationHarness
        from core_lib.physical_objects.reservoir import Reservoir
        from core_lib.physical_objects.gate import Gate
        from core_lib.physical_objects.unified_canal import UnifiedCanal
        from core_lib.physical_objects.disturbance_node import DisturbanceNode
        from core_lib.physical_objects.inverted_siphon import InvertedSiphon
        print("✅ 成功导入核心组件")
        YamlSimulationLoader = None  # 标记没有加载器
    except ImportError as e:
        print(f"❌ 导入核心库失败: {e}")
        sys.exit(1)

def create_test_simulation():
    """手动创建测试仿真环境"""
    print("🔧 手动创建测试仿真...")
    
    try:
        # 创建仿真平台
        config = {
            'start_time': 0,
            'end_time': 100,
            'time_step': 10
        }
        harness = SimulationHarness(config)
        
        # 创建组件
        # 1. 上游水库
        reservoir = Reservoir(
            name="Reservoir_1",
            initial_state={'water_level': 100.0, 'volume': 5000000.0, 'inflow': 50.0, 'outflow': 0.0},
            parameters={'surface_area': 50000.0, 'capacity': 10000000.0, 'min_level': 80.0, 'max_level': 120.0}
        )
        
        # 2. 渠道
        channel2 = UnifiedCanal(
            name="Channel_2",
            initial_state={'water_level': 62.83, 'outflow': 0.0},
            parameters={
                'length': 1000.0,
                'width': 10.0,
                'roughness': 0.025,
                'slope': 0.001,
                'model_type': 'integral_delay',
                'gain': 0.1,
                'delay_time': 10.0
            }
        )
        
        # 3. 分水口（支持时间序列）
        diversion = DisturbanceNode(
            name="Diversion_1",
            initial_state={'outflow': 0.0},
            parameters={
                'timeSeries': [
                    [0, 0.0],
                    [30, 50.0],
                    [60, 0.0],
                    [90, 0.0]
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
        
        # 5. 下游渠道
        channel3 = UnifiedCanal(
            name="Channel_3",
            initial_state={'water_level': 57.83, 'outflow': 0.0},
            parameters={
                'length': 800.0,
                'width': 8.0,
                'roughness': 0.025,
                'slope': 0.001,
                'model_type': 'integral_delay',
                'gain': 0.1,
                'delay_time': 8.0
            }
        )
        
        # 6. 倒虚吸
        siphon = InvertedSiphon(
            name="Siphon_1",
            initial_state={'outflow': 0.0},
            parameters={
                'length': 200.0,
                'diameter': 1.5,
                'roughness': 0.015,
                'inlet_loss_coeff': 0.5,
                'outlet_loss_coeff': 1.0,
                'orifice_width': 1.5,
                'orifice_height': 1.5
            }
        )
        
        # 添加组件到仿真平台
        harness.add_component("Reservoir_1", reservoir)
        harness.add_component("Channel_2", channel2)
        harness.add_component("Diversion_1", diversion)
        harness.add_component("Gate_1", gate)
        harness.add_component("Channel_3", channel3)
        harness.add_component("Siphon_1", siphon)
        
        # 定义连接
        harness.add_connection("Reservoir_1", "Channel_2")
        harness.add_connection("Channel_2", "Diversion_1")
        harness.add_connection("Diversion_1", "Gate_1")
        harness.add_connection("Gate_1", "Channel_3")
        harness.add_connection("Channel_3", "Siphon_1")
        
        # 构建仿真
        harness.build()
        
        print(f"✅ 成功创建仿真: {len(harness.components)} 个组件")
        return harness
        
    except Exception as e:
        print(f"❌ 创建仿真失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_gate_flow_stability():
    """测试闸门流量稳定性"""
    print("\n=== 测试闸门流量稳定性 ===")
    
    # 尝试使用YAML加载器
    harness = None
    if YamlSimulationLoader:
        try:
            scenario_path = project_root / "examples" / "topology"
            loader = YamlSimulationLoader(str(scenario_path))
            harness, message_bus = loader.load()
            print("✅ 使用YAML加载器成功")
        except Exception as e:
            print(f"⚠️ YAML加载器失败: {e}")
    
    # 如果没有YAML加载器或加载失败，手动创建
    if not harness:
        harness = create_test_simulation()
    
    if not harness:
        print("❌ 无法创建仿真")
        return False
        
        # 记录前几步的关键数据
        key_data = []
        
        for step in range(10):  # 运行10步
            harness.step()
            
            # 获取关键组件状态
            gate_state = harness.components.get('Gate_1', {}).get_state() if harness.components.get('Gate_1') else {}
            channel2_state = harness.components.get('Channel_2', {}).get_state() if harness.components.get('Channel_2') else {}
            diversion_state = harness.components.get('Diversion_1', {}).get_state() if harness.components.get('Diversion_1') else {}
            
            step_data = {
                'step': step,
                'time': harness.t,
                'gate_opening': gate_state.get('opening', 0),
                'gate_flow': gate_state.get('outflow', 0),
                'channel2_level': channel2_state.get('water_level', 0),
                'diversion_flow': diversion_state.get('diversion_flow', 0) if diversion_state else 0
            }
            key_data.append(step_data)
            
            print(f"步骤 {step}: t={harness.t:.1f}s, 闸门开度={step_data['gate_opening']:.3f}, "
                  f"闸门流量={step_data['gate_flow']:.3f}, Channel_2水位={step_data['channel2_level']:.3f}m, "
                  f"分流量={step_data['diversion_flow']:.3f}")
        
        # 分析结果
        print("\n=== 分析结果 ===")
        
        # 检查闸门开度是否保持稳定
        gate_openings = [d['gate_opening'] for d in key_data]
        opening_stable = all(abs(o - gate_openings[0]) < 0.01 for o in gate_openings)
        
        # 检查闸门流量变化
        gate_flows = [d['gate_flow'] for d in key_data]
        max_flow = max(gate_flows)
        min_flow = min(gate_flows)
        flow_variation = max_flow - min_flow
        
        # 检查Channel_2水位变化
        water_levels = [d['channel2_level'] for d in key_data]
        max_level = max(water_levels)
        min_level = min(water_levels)
        level_variation = max_level - min_level
        
        print(f"闸门开度稳定性: {'✅ 稳定' if opening_stable else '❌ 不稳定'}")
        print(f"闸门开度范围: {min(gate_openings):.3f} - {max(gate_openings):.3f}")
        print(f"闸门流量变化: {flow_variation:.3f} m³/s (范围: {min_flow:.3f} - {max_flow:.3f})")
        print(f"Channel_2水位变化: {level_variation:.3f} m (范围: {min_level:.3f} - {max_level:.3f})")
        
        # 判断修复是否成功
        success_criteria = [
            ("闸门开度稳定", opening_stable),
            ("闸门流量变化小于20 m³/s", flow_variation < 20.0),
            ("Channel_2水位变化小于10m", level_variation < 10.0)
        ]
        
        all_passed = all(passed for _, passed in success_criteria)
        
        print(f"\n=== 修复验证结果 ===")
        for criterion, passed in success_criteria:
            print(f"{'✅' if passed else '❌'} {criterion}")
        
        print(f"\n{'🎉 问题已解决！' if all_passed else '⚠️  问题仍存在，需要进一步调试'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔧 闸门流量稳定性测试")
    print("=" * 50)
    
    success = test_gate_flow_stability()
    
    if success:
        print("\n🎉 所有测试通过！闸门流量问题已修复。")
        return 0
    else:
        print("\n⚠️  测试未通过，问题仍需进一步解决。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
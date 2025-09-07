#!/usr/bin/env python3
"""
数据链路调试脚本 - 按步骤分析泵站控制系统的数据流
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.common.demand_patterns import StepDemandPattern
from core_lib.local_agents.control.unified_pump_station_control_agent import UnifiedPumpStationControlAgent
from core_lib.local_agents.control.pump_control_strategies import ControlStrategyType

def debug_data_flow():
    """调试数据流"""
    print("=== 数据链路调试分析 ===\n")
    
    # 1. 创建仿真环境
    print("1. 创建仿真环境")
    simulation_config = {'end_time': 10, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    print(f"✅ SimulationHarness created: {harness}")
    print(f"✅ MessageBus created: {message_bus}")
    
    # 2. 创建物理组件
    print("\n2. 创建物理组件")
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 25.0, 'volume': 100e6},
        parameters={'surface_area': 4.0e6}
    )
    downstream_reservoir = Reservoir(
        name="downstream_reservoir", 
        initial_state={'water_level': 8.0, 'volume': 20e6},
        parameters={'surface_area': 2.5e6}
    )
    print(f"✅ Upstream reservoir: {upstream_reservoir.get_state()}")
    print(f"✅ Downstream reservoir: {downstream_reservoir.get_state()}")
    
    # 3. 创建泵
    print("\n3. 创建泵")
    pumps = []
    pump_specs = [
        {'max_flow_rate': 8.0, 'max_head': 25.0, 'power_consumption_kw': 40, 'efficiency': 0.85},
        {'max_flow_rate': 12.0, 'max_head': 30.0, 'power_consumption_kw': 60, 'efficiency': 0.82},
        {'max_flow_rate': 15.0, 'max_head': 20.0, 'power_consumption_kw': 50, 'efficiency': 0.88},
        {'max_flow_rate': 6.0, 'max_head': 35.0, 'power_consumption_kw': 35, 'efficiency': 0.80}
    ]
    
    for i, specs in enumerate(pump_specs):
        pump = Pump(
            name=f"pump_{i+1}",
            initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0},
            parameters=specs,
            message_bus=message_bus,
            action_topic=f"action.pump.pump_{i+1}"
        )
        pumps.append(pump)
        print(f"✅ Pump {i+1}: {pump.get_state()}")
    
    # 4. 创建泵站
    print("\n4. 创建泵站")
    pump_station = PumpStation(
        name="test_pump_station",
        initial_state={},
        parameters={},
        pumps=pumps
    )
    print(f"✅ PumpStation created with {len(pump_station.pumps)} pumps")
    
    # 5. 创建需求代理
    print("\n5. 创建需求代理")
    demand_agent = StepDemandPattern(
        agent_id="test_demand_agent",
        message_bus=message_bus,
        demand_topic="demand.flow",
        steps={5: 20.0}  # 在t=5s时需求变为20 m³/s
    )
    print(f"✅ DemandAgent created")
    
    # 6. 创建控制代理
    print("\n6. 创建控制代理")
    pump_control_agent = UnifiedPumpStationControlAgent(
        agent_id="test_pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic="demand.flow",
        control_topic_prefix="action.pump",
        control_strategy_type=ControlStrategyType.OPTIMAL,
        dt=1.0
    )
    print(f"✅ PumpControlAgent created")
    
    # 7. 添加组件到仿真
    print("\n7. 添加组件到仿真")
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("test_pump_station", pump_station)
    harness.add_agent(demand_agent)
    harness.add_agent(pump_control_agent)
    print("✅ All components added")
    
    # 8. 构建仿真
    print("\n8. 构建仿真")
    harness.build()
    print("✅ Simulation built")
    
    # 9. 运行仿真并追踪数据流
    print("\n9. 运行仿真并追踪数据流")
    
    for step in range(10):
        current_time = step * harness.dt
        print(f"\n--- Step {step} (Time: {current_time}s) ---")
        
        # 9.1 需求生成
        print("9.1 需求生成")
        demand_agent.run(current_time)
        print(f"✅ Demand generated")
        
        # 9.2 控制代理处理
        print("9.2 控制代理处理")
        pump_control_agent.run(current_time)
        print(f"✅ Control agent processed")
        
        # 9.3 物理组件更新
        print("9.3 物理组件更新")
        action = {
            'upstream_level': upstream_reservoir.get_state()['water_level'],
            'downstream_level': downstream_reservoir.get_state()['water_level']
        }
        
        # 更新泵站
        pump_station_state = pump_station.step(action, harness.dt)
        print(f"✅ PumpStation state: {pump_station_state}")
        
        # 检查每个泵的状态
        for i, pump in enumerate(pumps):
            pump_state = pump.get_state()
            print(f"   Pump {i+1}: status={pump_state['status']}, flow={pump_state['outflow']}, power={pump_state['power_draw_kw']}")
        
        # 9.4 验证数据一致性
        print("9.4 验证数据一致性")
        total_flow = sum(pump.get_state()['outflow'] for pump in pumps)
        pump_station_flow = pump_station_state['total_outflow']
        
        if abs(total_flow - pump_station_flow) > 0.001:
            print(f"❌ ERROR: Flow mismatch! Individual pumps: {total_flow}, PumpStation: {pump_station_flow}")
        else:
            print(f"✅ Flow consistency verified: {total_flow} m³/s")
        
        # 9.5 检查控制逻辑
        if current_time >= 5.0:  # 需求阶段
            expected_flow = 20.0
            actual_flow = pump_station_flow
            error = abs(actual_flow - expected_flow)
            
            if error > 1.0:  # 1 m³/s 误差阈值
                print(f"❌ WARNING: Large flow error! Expected: {expected_flow}, Actual: {actual_flow}, Error: {error}")
            else:
                print(f"✅ Flow control working: {actual_flow} m³/s (error: {error})")

if __name__ == "__main__":
    debug_data_flow()

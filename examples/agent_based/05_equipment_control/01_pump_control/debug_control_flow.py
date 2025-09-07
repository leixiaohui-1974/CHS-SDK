#!/usr/bin/env python3
"""
调试控制流程的简化脚本
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.common.demand_patterns import StepDemandPattern
from core_lib.local_agents.control.unified_pump_station_control_agent import UnifiedPumpStationControlAgent
from core_lib.local_agents.control.pump_control_strategies import ControlStrategyType
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

def test_control_flow():
    """测试控制流程"""
    print("=== Testing Control Flow ===")
    
    # 创建简化的仿真环境
    simulation_config = {'end_time': 10, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 创建物理组件
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
    
    # 创建单个泵
    pump = Pump(
        name="test_pump",
        initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0},
        parameters={'max_flow_rate': 15.0, 'max_head': 25.0, 'power_consumption_kw': 75},
        message_bus=message_bus,
        action_topic="action.pump.test_pump"
    )
    
    pump_station = PumpStation(
        name="test_pump_station",
        initial_state={},
        parameters={},
        pumps=[pump]
    )
    
    # 创建需求代理
    demand_agent = StepDemandPattern(
        agent_id="test_demand_agent",
        message_bus=message_bus,
        demand_topic="demand.flow",
        steps={5: 10.0}  # 在t=5s时需求变为10 m³/s
    )
    
    # 创建控制代理
    pump_control_agent = UnifiedPumpStationControlAgent(
        agent_id="test_pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic="demand.flow",
        control_topic_prefix="action.pump",
        control_strategy_type=ControlStrategyType.OPTIMAL,
        dt=1.0
    )
    
    # 添加组件
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("test_pump_station", pump_station)
    
    # 添加代理
    harness.add_agent(demand_agent)
    harness.add_agent(pump_control_agent)
    
    # 构建仿真
    harness.build()
    
    print("\n=== Running Simulation ===")
    
    # 手动运行几步仿真
    for i in range(10):
        current_time = i * harness.dt
        
        # 运行代理
        demand_agent.run(current_time)
        pump_control_agent.run(current_time)
        
        # 步进物理模型
        harness._step_physical_models(harness.dt)
        
        # 检查泵状态
        pump_state = pump.get_state()
        print(f"Time {current_time:.0f}s: Pump status={pump_state['status']}, "
              f"flow={pump_state['outflow']:.1f} m³/s, "
              f"power={pump_state['power_draw_kw']:.1f} kW")
    
    print("\n=== Simulation Complete ===")

if __name__ == "__main__":
    test_control_flow()

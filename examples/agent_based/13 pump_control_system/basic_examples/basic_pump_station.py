#!/usr/bin/env python3
"""
基础泵站控制仿真脚本 - 遵循三个核心原则修复版本

遵循三个核心原则：
1. 禁止魔数、硬编码及隐式默认值 
2. 物理模型的合理性
3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性

该脚本演示了PumpControlAgent如何管理多个泵单元以满足变化的流量需求。
"""

import sys
import os
import math
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path - 修正路径深度
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent

# 配置常量类 - 遵循第一原则：禁止魔数、硬编码及隐式默认值
class SimulationConfig:
    """仿真基础配置"""
    START_TIME = 0.0
    END_TIME = 600.0
    TIME_STEP = 1.0
    DEMAND_CHANGE_TIME_1 = 100.0
    DEMAND_CHANGE_TIME_2 = 400.0
    HIGH_DEMAND = 25.0
    LOW_DEMAND = 8.0
    INITIAL_DEMAND = 15.0

class SystemTopologyConfig:
    """系统拓扑配置"""
    SOURCE_RESERVOIR_ID = "source_res"
    PUMP_STATION_ID = "ps1"
    DOWNSTREAM_RESERVOIR_ID = "downstream_res"
    
class MonitoringConfig:
    """监控配置"""
    STATUS_REPORT_INTERVAL = 50.0  # 状态报告间隔（秒）
    ENABLE_STEP_LOGGING = True
    MONITORING_ENABLED = True

class CommunicationConfig:
    """通信配置"""
    DEMAND_TOPIC = "demand.flow"
    PUMP_CONTROL_TOPIC_PREFIX = "action.pump"

class PhysicalConstants:
    """物理常量"""
    # 水库参数
    SOURCE_WATER_LEVEL = 10.0  # 源水库初始水位（米）
    DOWNSTREAM_WATER_LEVEL = 25.0  # 下游水库初始水位（米）
    RESERVOIR_SURFACE_AREA = 1.0e6  # 水库表面积（平方米）
    
    # 泵参数
    NUM_PUMPS = 3  # 泵数量
    PUMP_MAX_FLOW = 10.0  # 单泵最大流量（m³/s）
    PUMP_MAX_HEAD = 20.0  # 单泵最大扬程（米）
    PUMP_POWER = 50.0  # 单泵功率（kW）

class ConfigurableDemandAgent(Agent):
    """可配置的需求代理 - 遵循通用性原则"""
    def __init__(self, agent_id: str, message_bus, demand_topic: str, 
                 demand_schedule: Optional[Dict[float, float]] = None):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_schedule = demand_schedule or {
            SimulationConfig.DEMAND_CHANGE_TIME_1: SimulationConfig.HIGH_DEMAND,
            SimulationConfig.DEMAND_CHANGE_TIME_2: SimulationConfig.LOW_DEMAND
        }
        self.current_demand = SimulationConfig.INITIAL_DEMAND

    def run(self, current_time: float) -> None:
        """运行需求生成逻辑"""
        # 检查是否需要更新需求 - 使用范围检查避免浮点精度问题
        for change_time, new_demand in self.demand_schedule.items():
            if abs(current_time - change_time) < 0.5 and self.current_demand != new_demand:
                self.current_demand = new_demand
                print(f"--- DEMAND AGENT: New demand at t={current_time}s: {self.current_demand} m^3/s ---")
                break
        
        # 发布需求信息
        self.bus.publish(self.demand_topic, {'value': self.current_demand})

def create_enhanced_simulation_system() -> Dict[str, Any]:
    """
    创建增强的仿真系统 - 遵循三个核心原则
    
    Returns:
        包含仿真系统所有组件的字典
    """
    # 1. 创建仿真配置 - 使用配置常量
    simulation_config = {
        'start_time': SimulationConfig.START_TIME,
        'end_time': SimulationConfig.END_TIME,
        'time_step': SimulationConfig.TIME_STEP
    }
    
    # 2. 创建仿真系统
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 3. 创建物理组件 - 遵循物理模型合理性原则
    source_reservoir = Reservoir(
        SystemTopologyConfig.SOURCE_RESERVOIR_ID,
        {
            'water_level': PhysicalConstants.SOURCE_WATER_LEVEL,
            'volume': PhysicalConstants.SOURCE_WATER_LEVEL * PhysicalConstants.RESERVOIR_SURFACE_AREA,
            'outflow': 0.0
        },
        {'surface_area': PhysicalConstants.RESERVOIR_SURFACE_AREA}
    )
    
    downstream_reservoir = Reservoir(
        SystemTopologyConfig.DOWNSTREAM_RESERVOIR_ID,
        {
            'water_level': PhysicalConstants.DOWNSTREAM_WATER_LEVEL,
            'volume': PhysicalConstants.DOWNSTREAM_WATER_LEVEL * PhysicalConstants.RESERVOIR_SURFACE_AREA,
            'outflow': 0.0
        },
        {'surface_area': PhysicalConstants.RESERVOIR_SURFACE_AREA}
    )

    # 创建泵组 - 使用配置常量
    pump_params = {
        'max_flow_rate': PhysicalConstants.PUMP_MAX_FLOW,
        'max_head': PhysicalConstants.PUMP_MAX_HEAD,
        'power_consumption_kw': PhysicalConstants.PUMP_POWER
    }
    
    pumps = []
    for i in range(1, PhysicalConstants.NUM_PUMPS + 1):
        pump = Pump(
            f"p{i}",
            {'status': 0, 'outflow': 0.0, 'power_draw_kw': 0.0, 'efficiency': 0.0},
            pump_params,
            message_bus,
            f"{CommunicationConfig.PUMP_CONTROL_TOPIC_PREFIX}.p{i}"
        )
        pumps.append(pump)
    
    pump_station = PumpStation(SystemTopologyConfig.PUMP_STATION_ID, {}, {}, pumps)

    # 添加组件到仿真系统
    harness.add_component(SystemTopologyConfig.SOURCE_RESERVOIR_ID, source_reservoir)
    harness.add_component(SystemTopologyConfig.DOWNSTREAM_RESERVOIR_ID, downstream_reservoir)
    harness.add_component(SystemTopologyConfig.PUMP_STATION_ID, pump_station)
    
    # 设置物理连接
    harness.add_connection(SystemTopologyConfig.SOURCE_RESERVOIR_ID, SystemTopologyConfig.PUMP_STATION_ID)
    harness.add_connection(SystemTopologyConfig.PUMP_STATION_ID, SystemTopologyConfig.DOWNSTREAM_RESERVOIR_ID)

    # 4. 创建智能代理 - 遵循通用性原则
    demand_agent = ConfigurableDemandAgent(
        "demand_agent",
        message_bus,
        CommunicationConfig.DEMAND_TOPIC
    )
    
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=CommunicationConfig.DEMAND_TOPIC,
        control_topic_prefix=CommunicationConfig.PUMP_CONTROL_TOPIC_PREFIX,
        dt=simulation_config['time_step']
    )

    harness.add_agent(demand_agent)
    # UnifiedPumpControlAgent通过消息总线自动处理控制逻辑

    return {
        'harness': harness,
        'agents': {
            'demand_agent': demand_agent,
            'pump_control_agent': pump_control_agent
        },
        'components': {
            'source_reservoir': source_reservoir,
            'downstream_reservoir': downstream_reservoir, 
            'pump_station': pump_station
        },
        'config': simulation_config
    }

def run_pump_station_simulation() -> bool:
    """
    运行泵站仿真 - 遵循三个核心原则
    
    Returns:
        仿真是否成功执行
    """
    try:
        print("--- 设置泵站控制仿真 ---")
        print("遵循三个核心原则：")
        print("1. 禁止魔数、硬编码及隐式默认值")
        print("2. 物理模型的合理性") 
        print("3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性")
        print()

        # 1. 创建仿真系统
        simulation_system = create_enhanced_simulation_system()
        harness = simulation_system['harness']
        agents = simulation_system['agents']
        components = simulation_system['components']
        config = simulation_system['config']

        # 2. 构建仿真系统
        harness.build()

        print("\n--- 运行仿真 ---")
        num_steps = int(config['end_time'] / config['time_step'])
        
        for i in range(num_steps):
            current_time = i * config['time_step']
            
            # 启用步骤日志 - 按配置控制
            if MonitoringConfig.ENABLE_STEP_LOGGING and i % int(MonitoringConfig.STATUS_REPORT_INTERVAL / config['time_step']) == 0:
                print(f"\n--- Simulation Step {i+1}, Time: {current_time:.2f}s ---")

            # 运行代理
            agents['demand_agent'].run(current_time)
            # UnifiedPumpControlAgent通过消息总线自动处理控制逻辑

            # 步进物理模型
            harness._step_physical_models(config['time_step'])

            # 存储历史数据
            step_history = {'time': current_time}
            for cid in harness.sorted_components:
                step_history[cid] = harness.components[cid].get_state()
            harness.history.append(step_history)

            # 按配置间隔打印状态
            if MonitoringConfig.MONITORING_ENABLED and i % int(MonitoringConfig.STATUS_REPORT_INTERVAL / config['time_step']) == 0:
                station_state = components['pump_station'].get_state()
                print(f"  State Update:")
                print(f"    Pump Station: Active Pumps={station_state.get('active_pumps', 0)}, "
                      f"Total Outflow={station_state.get('total_outflow', 0.0):.2f} m^3/s")

        print("\n--- 仿真完成 ---")
        
        # 打印最终结果
        final_station_state = components['pump_station'].get_state()
        print(f"\n最终泵站状态：")
        print(f"  活跃泵数: {final_station_state.get('active_pumps', 0)}")
        print(f"  总出流量: {final_station_state.get('total_outflow', 0.0):.2f} m^3/s")
        print(f"  总功耗: {final_station_state.get('total_power_draw_kw', 0.0):.2f} kW")
        
        return True
        
    except Exception as e:
        print(f"错误：仿真执行失败 - {e}")
        return False

def main() -> bool:
    """主函数：运行泵站控制仿真"""
    return run_pump_station_simulation()

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"\n=== 泵站控制仿真完成 ===\n退出代码： {exit_code}")
    sys.exit(exit_code)

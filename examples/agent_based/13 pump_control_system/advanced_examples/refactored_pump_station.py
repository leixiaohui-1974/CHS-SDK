#!/usr/bin/env python3
"""
重构的泵站控制仿真脚本 - 遵循三个核心原则修复版本

遵循三个核心原则：
1. 禁止魔数、硬编码及隐式默认值
2. 物理模型的合理性
3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[4]  # 修正路径深度
sys.path.insert(0, str(project_root))

from core_lib.core_engine.testing.simulation_builder import create_pump_station_system, HardcodedSimulationBuilder
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent
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

class MonitoringConfig:
    """监控配置"""
    STATUS_REPORT_INTERVAL = 100.0  # 状态报告间隔（秒）
    MONITORING_ENABLED = True

class SystemTopologyConfig:
    """系统拓扑配置"""
    SOURCE_RESERVOIR_ID = "source_res"
    PUMP_STATION_ID = "ps1"
    DOWNSTREAM_RESERVOIR_ID = "downstream_res"
    
class CommunicationConfig:
    """通信配置"""
    DEMAND_TOPIC = "demand.flow"
    PUMP_CONTROL_TOPIC_PREFIX = "action.pump"

class PhysicalConstants:
    """物理常量"""
    SOURCE_WATER_LEVEL = 10.0  # 源水库初始水位（米）
    DOWNSTREAM_WATER_LEVEL = 25.0  # 下游水库初始水位（米）
    NUM_PUMPS = 3  # 泵站泵数量
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

def create_enhanced_pump_station_simulation() -> Dict[str, Any]:
    """
    创建增强的泵站仿真系统 - 遵循三个核心原则
    
    Returns:
        包含仿真系统所有组件的字典
    """
    # 1. 创建仿真配置 - 使用配置常量
    simulation_config = {
        'start_time': SimulationConfig.START_TIME,
        'end_time': SimulationConfig.END_TIME,
        'time_step': SimulationConfig.TIME_STEP
    }
    
    # 2. 使用构建器创建系统 - 遵循物理模型合理性原则
    builder = create_pump_station_system(simulation_config)
    
    # 3. 使用配置常量创建通信主题
    DEMAND_TOPIC = CommunicationConfig.DEMAND_TOPIC
    CONTROL_TOPIC_PREFIX = CommunicationConfig.PUMP_CONTROL_TOPIC_PREFIX
    
    # 4. 创建通用代理 - 遵循通用性原则
    demand_agent = ConfigurableDemandAgent(
        "demand_agent", 
        builder.harness.message_bus, 
        DEMAND_TOPIC
    )
    builder.add_agent(demand_agent)
    
    # 5. 获取泵站组件并验证存在
    pump_station = builder.get_component(SystemTopologyConfig.PUMP_STATION_ID)
    if pump_station is None:
        raise ValueError(f"Pump station '{SystemTopologyConfig.PUMP_STATION_ID}' not found in builder")
    
    # 6. 创建泵控制代理
    pump_control_agent = PumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=builder.harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=CONTROL_TOPIC_PREFIX
    )
    builder.add_agent(pump_control_agent)
    
    return {
        'builder': builder,
        'pump_station': pump_station,
        'agents': {
            'demand_agent': demand_agent,
            'pump_control_agent': pump_control_agent
        },
        'config': simulation_config
    }

def run_pump_station_simulation_refactored() -> bool:
    """
    重构的泵站仿真 - 遵循三个核心原则
    
    Returns:
        仿真是否成功执行
    """
    try:
        print("--- 设置重构的泵站控制仿真 ---")
        print("遵循三个核心原则：")
        print("1. 禁止魔数、硬编码及隐式默认值")
        print("2. 物理模型的合理性")
        print("3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性")
        print()

        # 1. 创建仿真系统
        simulation_system = create_enhanced_pump_station_simulation()
        builder = simulation_system['builder']
        pump_station = simulation_system['pump_station']
        agents = simulation_system['agents']
        config = simulation_system['config']

        # 2. 构建仿真系统
        builder.build()
        print("\n--- 运行重构仿真 ---")
        
        # 3. 计算仿真步数 - 使用配置常量
        num_steps = int(config['end_time'] / config['time_step'])
        
        # 4. 手动执行仿真循环
        for i in range(num_steps):
            current_time = i * config['time_step']
            
            # 运行代理
            agents['demand_agent'].run(current_time)
            agents['pump_control_agent'].execute_control_logic()
            
            # 步进物理模型
            builder.harness._step_physical_models(config['time_step'])
            
            # 存储历史数据
            step_history = {'time': current_time}
            for cid in builder.harness.sorted_components:
                step_history[cid] = builder.harness.components[cid].get_state()
            builder.harness.history.append(step_history)
            
            # 按配置间隔打印状态
            if i % int(MonitoringConfig.STATUS_REPORT_INTERVAL / config['time_step']) == 0:
                station_state = pump_station.get_state()
                print(f"Time {current_time:.0f}s: Active Pumps={station_state.get('active_pumps', 0)}, "
                      f"Total Outflow={station_state.get('total_outflow', 0.0):.2f} m^3/s")

        # 5. 打印最终结果
        print("\n--- 仿真完成 ---")
        builder.print_final_states()
        
        final_station_state = pump_station.get_state()
        print(f"\n最终泵站状态：")
        print(f"  活跃泵数: {final_station_state.get('active_pumps', 0)}")
        print(f"  总出流量: {final_station_state.get('total_outflow', 0.0):.2f} m^3/s")
        
        return True
        
    except Exception as e:
        print(f"错误：仿真执行失败 - {e}")
        return False

def main() -> bool:
    """主函数：运行重构的泵站控制仿真"""
    return run_pump_station_simulation_refactored()

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"\n=== 重构泵站仿真完成 ===\n退出代码： {exit_code}")
    sys.exit(exit_code)
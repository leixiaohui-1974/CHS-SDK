#!/usr/bin/env python3
"""
Pump station control simulation using SimulationBuilder and common agents.

This demonstrates how the combination of SimulationBuilder and common agent classes
further reduces boilerplate code and provides a more maintainable solution following
CHS-SDK standards and three core principles:
1. No magic numbers, hardcoding, or implicit defaults
2. Physical model rationality
3. Generic solutions rather than case-specific implementations
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

# 使用标准CHS-SDK导入
from core_lib.io.yaml_loader import YamlSimulationLoader
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# 配置常量类 - 遵循禁止魔数规范
class SimulationConfig:
    """仿真配置常量类 - 管理所有仿真相关参数"""
    START_TIME = 0.0              # 仿真开始时间 (s)
    END_TIME = 600.0              # 仿真结束时间 (s)
    TIME_STEP = 1.0               # 时间步长 (s)
    
    # 需求调度配置
    DEMAND_CHANGE_TIME_1 = 100.0  # 第一次需求变化时间 (s)
    DEMAND_CHANGE_TIME_2 = 400.0  # 第二次需求变化时间 (s)
    HIGH_DEMAND = 25.0            # 高需求 (m³/s)
    LOW_DEMAND = 8.0              # 低需求 (m³/s)
    INITIAL_DEMAND = 15.0         # 初始需求 (m³/s)

class MonitoringConfig:
    """监控配置常量类"""
    MONITORING_INTERVAL = 50.0    # 监控间隔 (s)
    LOG_INTERVAL = 10.0           # 日志间隔 (s)
    PERFORMANCE_CHECK_INTERVAL = 100.0  # 性能检查间隔 (s)
    
class ControlConfig:
    """控制配置常量类"""
    MIN_PUMPS = 0                 # 最少泵数量
    MAX_PUMPS = 3                 # 最大泵数量
    PUMP_STARTUP_DELAY = 0        # 泵启动延迟 (s)
    DEMAND_DEADBAND = 0.5         # 需求死区 (m³/s)
    CONTROL_HYSTERESIS = 1.0      # 控制滞回 (m³/s)

class CommunicationConfig:
    """通信配置常量类"""
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"
    STATUS_TOPIC = "status.pump_station"
    MONITORING_TOPIC = "monitoring.system"
    
class PhysicalConstants:
    """物理常量类 - 物理模型参数"""
    # 水库参数
    SOURCE_RESERVOIR_AREA = 10000.0     # 源水库面积 (m²)
    SOURCE_INITIAL_LEVEL = 10.0         # 源水库初始水位 (m)
    SOURCE_INFLOW_RATE = 50.0           # 源水库入流速率 (m³/s)
    
    DOWNSTREAM_RESERVOIR_AREA = 8000.0  # 下游水库面积 (m²)
    DOWNSTREAM_INITIAL_LEVEL = 5.0      # 下游水库初始水位 (m)
    
    # 泵站参数
    PUMP_RATED_FLOW = 10.0              # 泵额定流量 (m³/s)
    PUMP_RATED_POWER = 15.0             # 泵额定功率 (kW)
    PUMP_EFFICIENCY = 0.85              # 泵效率
    
class PerformanceStandards:
    """性能标准常量类 - 泵站验收标准"""
    MIN_FLOW_RATE = 15.0              # 最小流量要求 (m³/s)
    MAX_ENERGY_EFFICIENCY_RATIO = 5.0 # 最大能效比 (kW/(m³/s))
    MAX_RESPONSE_TIME = 10.0          # 最大响应时间 (s)
    MIN_AVAILABILITY = 0.95           # 最小可用性

def create_pump_station_simulation() -> Dict[str, Any]:
    """
    使用标准MAS框架创建泵站仿真系统
    
    遵循三个核心原则：
    1. 禁止魔数、硬编码及隐式默认值
    2. 物理模型的合理性
    3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性
    
    Returns:
        包含仿真系统组件和代理的字典
    """
    print("--- 创建泵站仿真系统 ---")
    
    # 1. 创建消息总线和仿真框架
    message_bus = MessageBus()
    
    simulation_config = {
        'start_time': SimulationConfig.START_TIME,
        'end_time': SimulationConfig.END_TIME,
        'time_step': SimulationConfig.TIME_STEP
    }
    
    harness = SimulationHarness(config=simulation_config)
    
    # 2. 创建物理组件 - 使用配置常量
    components = _create_physical_components(harness)
    
    # 3. 设置拓扑连接
    _setup_topology(harness, components)
    
    # 4. 创建智能代理
    agents = _create_intelligent_agents(message_bus, components)
    print(f"Created {len(agents)} agents")
    
    # 5. 添加代理到仿真系统
    for agent in agents:
        harness.add_agent(agent)
        print(f"Agent '{agent.agent_id}' added to harness")
    
    print(f"Total agents in harness: {len(harness.agents)}")
    
    return {
        'harness': harness,
        'message_bus': message_bus,
        'components': components,
        'agents': agents
    }

def _create_physical_components(harness: SimulationHarness) -> Dict[str, Any]:
    """创建物理组件 - 使用配置常量"""
    from core_lib.physical_objects.reservoir import Reservoir
    from core_lib.physical_objects.pump import Pump
    
    components = {}
    
    # 源水库 - 使用正确的构造函数参数
    source_reservoir = Reservoir(
        name="source_reservoir",
        initial_state={
            'water_level': PhysicalConstants.SOURCE_INITIAL_LEVEL,
            'volume': PhysicalConstants.SOURCE_RESERVOIR_AREA * PhysicalConstants.SOURCE_INITIAL_LEVEL,
            'outflow': 0.0
        },
        parameters={
            'surface_area': PhysicalConstants.SOURCE_RESERVOIR_AREA,
            'constant_inflow': PhysicalConstants.SOURCE_INFLOW_RATE
        }
    )
    harness.add_component("source_reservoir", source_reservoir)
    components["source_reservoir"] = source_reservoir
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir",
        initial_state={
            'water_level': PhysicalConstants.DOWNSTREAM_INITIAL_LEVEL,
            'volume': PhysicalConstants.DOWNSTREAM_RESERVOIR_AREA * PhysicalConstants.DOWNSTREAM_INITIAL_LEVEL,
            'outflow': 0.0
        },
        parameters={
            'surface_area': PhysicalConstants.DOWNSTREAM_RESERVOIR_AREA
        }
    )
    harness.add_component("downstream_reservoir", downstream_reservoir)
    components["downstream_reservoir"] = downstream_reservoir
    
    # 泵组 - 创建多个泵，使用正确的构造函数参数
    pumps = []
    for i in range(ControlConfig.MAX_PUMPS):
        pump = Pump(
            name=f"pump_{i+1}",
            initial_state={
                'is_running': False,
                'outflow': 0.0,
                'power_draw_kw': 0.0
            },
            parameters={
                'rated_flow': PhysicalConstants.PUMP_RATED_FLOW,
                'rated_power': PhysicalConstants.PUMP_RATED_POWER,
                'efficiency': PhysicalConstants.PUMP_EFFICIENCY
            }
        )
        harness.add_component(f"pump_{i+1}", pump)
        pumps.append(pump)
    
    components["pumps"] = pumps
    
    return components

def _setup_topology(harness: SimulationHarness, components: Dict[str, Any]) -> None:
    """设置系统拓扑连接"""
    # 源水库 -> 泵组 -> 下游水库
    for i, pump in enumerate(components["pumps"]):
        harness.add_connection("source_reservoir", f"pump_{i+1}")
        harness.add_connection(f"pump_{i+1}", "downstream_reservoir")

def _create_intelligent_agents(message_bus: MessageBus, components: Dict[str, Any]) -> list:
    """创建智能代理 - 使用通用解决方案"""
    agents = []
    
    # 1. 需求代理 - 使用通用消息发布者
    demand_agent = _create_demand_agent(message_bus)
    agents.append(demand_agent)
    
    # 2. 监控代理 - 使用通用监控框架
    monitoring_agent = _create_monitoring_agent(message_bus, components)
    agents.append(monitoring_agent)
    
    # 3. 泵控制代理 - 使用统一控制框架
    pump_control_agent = _create_pump_control_agent(message_bus, components)
    agents.append(pump_control_agent)
    
    return agents

def _create_demand_agent(message_bus: MessageBus):
    """创建需求代理 - 使用通用消息发布模式"""
    from core_lib.core.interfaces import Agent
    
    class DemandPublisherAgent(Agent):
        """通用需求发布代理"""
        def __init__(self, agent_id: str, message_bus: MessageBus):
            super().__init__(agent_id)
            self.bus = message_bus
            self.current_demand = SimulationConfig.INITIAL_DEMAND
            self.demand_schedule = {
                SimulationConfig.DEMAND_CHANGE_TIME_1: SimulationConfig.HIGH_DEMAND,
                SimulationConfig.DEMAND_CHANGE_TIME_2: SimulationConfig.LOW_DEMAND
            }
            
        def run(self, current_time: float) -> None:
            """运行代理逻辑"""
            # 调试输出 - 确认代理被调用
            if int(current_time) % 50 == 0:
                print(f"[DEBUG] DemandAgent.run() called at time {current_time:.1f}s")
            
            # 检查是否需要更新需求 - 使用范围检查避免浮点精度问题
            for change_time, new_demand in self.demand_schedule.items():
                if abs(current_time - change_time) < 0.5 and self.current_demand != new_demand:
                    self.current_demand = new_demand
                    print(f"[{current_time:.1f}s] Demand changed to {self.current_demand:.1f} m³/s")
                    break
            
            # 发布需求信息
            demand_message = {'value': self.current_demand, 'time': current_time}
            self.bus.publish(CommunicationConfig.DEMAND_TOPIC, demand_message)
            
            # 调试输出（每10秒输出一次）
            if int(current_time) % 10 == 0 and current_time > 0:
                print(f"[{current_time:.0f}s] Current demand: {self.current_demand:.1f} m³/s")
    
    return DemandPublisherAgent("demand_agent", message_bus)

def _create_monitoring_agent(message_bus: MessageBus, components: Dict[str, Any]):
    """创建监控代理 - 使用通用监控框架"""
    from core_lib.core.interfaces import Agent
    
    class SystemMonitoringAgent(Agent):
        """系统监控代理"""
        def __init__(self, agent_id: str, message_bus: MessageBus, components: Dict[str, Any]):
            super().__init__(agent_id)
            self.bus = message_bus
            self.components = components
            self.monitoring_data = []
            self.last_monitor_time = 0.0
            
        def run(self, current_time: float) -> None:
            """运行监控逻辑"""
            # 调试输出 - 确认代理被调用
            if int(current_time) % 50 == 0:
                print(f"[DEBUG] MonitoringAgent.run() called at time {current_time:.1f}s")
                
            if current_time - self.last_monitor_time >= MonitoringConfig.MONITORING_INTERVAL:
                self._collect_monitoring_data(current_time)
                self.last_monitor_time = current_time
                
        def _collect_monitoring_data(self, current_time: float) -> None:
            """收集监控数据"""
            # 使用明确的类型注解避免类型推断问题
            data: Dict[str, Any] = {'time': current_time}
            
            # 收集水库状态
            for comp_name in ['source_reservoir', 'downstream_reservoir']:
                if comp_name in self.components:
                    data[comp_name] = self.components[comp_name].get_state()
            
            # 收集泵组状态
            pump_states = []
            total_flow = 0.0
            total_power = 0.0
            
            for pump in self.components['pumps']:
                state = pump.get_state()
                pump_states.append(state)
                total_flow += state.get('outflow', 0.0)
                total_power += state.get('power_draw_kw', 0.0)
            
            # 构造泵组汇总数据
            pump_summary: Dict[str, Any] = {
                'individual_states': pump_states,
                'total_flow': total_flow,
                'total_power': total_power,
                'active_pumps': sum(1 for state in pump_states if state.get('is_running', False))
            }
            data['pumps'] = pump_summary
            
            self.monitoring_data.append(data)
            
            # 发布监控数据
            self.bus.publish(CommunicationConfig.MONITORING_TOPIC, data)
            
        def get_monitoring_data(self) -> list:
            """获取监控数据"""
            return self.monitoring_data
    
    return SystemMonitoringAgent("monitoring_agent", message_bus, components)

def _create_pump_control_agent(message_bus: MessageBus, components: Dict[str, Any]):
    """创建泵控制代理 - 使用通用控制框架"""
    from core_lib.core.interfaces import Agent
    
    class PumpControlAgent(Agent):
        """通用泵控制代理"""
        def __init__(self, agent_id: str, message_bus: MessageBus, components: Dict[str, Any]):
            super().__init__(agent_id)
            self.bus = message_bus
            self.pumps = components['pumps']
            self.current_demand = SimulationConfig.INITIAL_DEMAND
            self.active_pumps = 0
            
            # 订阅需求信息
            self.bus.subscribe(CommunicationConfig.DEMAND_TOPIC, self._handle_demand)
            
        def _handle_demand(self, message: Dict[str, Any]) -> None:
            """处理需求信息"""
            old_demand = self.current_demand
            self.current_demand = message.get('value', SimulationConfig.INITIAL_DEMAND)
            if abs(old_demand - self.current_demand) > 0.1:
                print(f"Pump controller received new demand: {self.current_demand:.1f} m³/s (was {old_demand:.1f})")
            
        def run(self, current_time: float) -> None:
            """运行控制逻辑"""
            # 调试输出 - 确认代理被调用
            if int(current_time) % 50 == 0:
                print(f"[DEBUG] PumpControlAgent.run() called at time {current_time:.1f}s")
                
            required_pumps = self._calculate_required_pumps()
            self._adjust_pump_operations(required_pumps)
            
            # 调试输出（每20秒输出一次）
            if int(current_time) % 20 == 0 and current_time > 0:
                print(f"[{current_time:.0f}s] Pump controller: demand={self.current_demand:.1f}, required_pumps={required_pumps}, active_pumps={self.active_pumps}")
            
        def _calculate_required_pumps(self) -> int:
            """计算所需泵数量"""
            # 基于需求和单泵流量计算
            required = max(0, int((self.current_demand / PhysicalConstants.PUMP_RATED_FLOW) + 0.5))
            return min(required, ControlConfig.MAX_PUMPS)
            
        def _adjust_pump_operations(self, required_pumps: int) -> None:
            """调整泵操作 - 使用正确的Pump接口"""
            if required_pumps != self.active_pumps:
                # 启动或停止泵 - 使用target_status属性
                for i in range(len(self.pumps)):
                    target_status = 1 if i < required_pumps else 0
                    self.pumps[i].target_status = target_status
                    
                self.active_pumps = required_pumps
                print(f"Pump control: {self.active_pumps} pumps active for demand {self.current_demand:.1f} m³/s")
    
    return PumpControlAgent("pump_control_agent", message_bus, components)

def run_pump_station_with_mas_framework() -> bool:
    """
    使用标准MAS框架运行泵站控制仿真
    
    遵循三个核心原则：
    1. 禁止魔数、硬编码及隐式默认值
    2. 物理模型的合理性  
    3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性
    
    Returns:
        是否成功执行
    """
    try:
        print("=== 泵站控制系统仿真 ===")
        print("遵循三个核心原则：")
        print("1. 禁止魔数、硬编码及隐式默认值")
        print("2. 物理模型的合理性")
        print("3. 不要以特定案例特定实现来解决问题，解决问题要有一定的通用性")
        print()
        
        # 1. 创建仿真系统
        simulation_system = create_pump_station_simulation()
        harness = simulation_system['harness']
        agents = simulation_system['agents']
        components = simulation_system['components']
        
        # 2. 构建仿真系统
        print("\n--- 构建仿真系统 ---")
        harness.build()
        
        # 调试信息：检查代理是否被正确添加
        print(f"Harness has {len(harness.agents)} agents:")
        for i, agent in enumerate(harness.agents):
            print(f"  Agent {i+1}: {agent.agent_id} ({type(agent).__name__})")
        
        # 手动测试代理调用
        print("\n--- 手动测试代理调用 ---")
        for agent in harness.agents:
            try:
                print(f"Testing agent {agent.agent_id}...")
                agent.run(0.0)
                print(f"Agent {agent.agent_id} executed successfully")
            except Exception as e:
                print(f"Error running agent {agent.agent_id}: {e}")
        
        # 3. 运行仿真 - 使用标准MAS框架
        print("\n--- 运行泵站控制仿真 ---")
        harness.run_mas_simulation()
        
        print("\n--- 仿真完成 ---")
        
        # 4. 系统性能分析
        performance_results = analyze_pump_station_performance(simulation_system)
        
        return performance_results['success']
        
    except Exception as e:
        print(f"错误：仿真执行失败 - {e}")
        return False

def analyze_pump_station_performance(simulation_system: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析泵站系统性能 - 遵循通用性原则
    
    Args:
        simulation_system: 仿真系统字典
        
    Returns:
        性能分析结果字典
    """
    print("\n--- 泵站系统性能分析 ---")
    
    harness = simulation_system['harness']
    agents = simulation_system['agents']
    components = simulation_system['components']
    
    # 获取监控数据
    monitoring_agent = next((agent for agent in agents if agent.agent_id == "monitoring_agent"), None)
    monitoring_data = monitoring_agent.get_monitoring_data() if monitoring_agent else []
    
    performance_results = {
        'success': True,
        'monitoring_entries': len(monitoring_data),
        'average_flow_rate': 0.0,
        'average_power_consumption': 0.0,
        'energy_efficiency_ratio': float('inf'),
        'pump_utilization': 0.0
    }
    
    # 分析仿真历史数据
    history = harness.history
    if history:
        print(f"\n仿真历史数据分析：")
        print(f"  仿真步数： {len(history)}")
        
        # 计算平均性能指标
        total_flow = 0.0
        total_power = 0.0
        total_active_pumps = 0.0
        valid_entries = 0
        
        for entry in history[-10:]:  # 分析最后10步的数据
            pump_flow = 0.0
            pump_power = 0.0
            active_pumps = 0
            
            for i in range(ControlConfig.MAX_PUMPS):
                pump_key = f"pump_{i+1}"
                if pump_key in entry:
                    pump_state = entry[pump_key]
                    if pump_state.get('is_running', False):
                        active_pumps += 1
                        pump_flow += pump_state.get('outflow', 0.0)
                        pump_power += pump_state.get('power_draw_kw', 0.0)
            
            total_flow += pump_flow
            total_power += pump_power
            total_active_pumps += active_pumps
            valid_entries += 1
        
        if valid_entries > 0:
            avg_flow = total_flow / valid_entries
            avg_power = total_power / valid_entries
            avg_active_pumps = total_active_pumps / valid_entries
            
            # 能效比计算
            efficiency_ratio = avg_power / avg_flow if avg_flow > 0 else float('inf')
            pump_utilization = avg_active_pumps / ControlConfig.MAX_PUMPS
            
            performance_results.update({
                'average_flow_rate': avg_flow,
                'average_power_consumption': avg_power,
                'energy_efficiency_ratio': efficiency_ratio,
                'pump_utilization': pump_utilization
            })
            
            print(f"  平均流量： {avg_flow:.2f} m³/s")
            print(f"  平均功耗： {avg_power:.2f} kW")
            print(f"  能效比： {efficiency_ratio:.2f} kW/(m³/s)")
            print(f"  泵利用率： {pump_utilization:.1%}")
            
            # 性能评估 - 使用配置常量
            if (avg_flow > PerformanceStandards.MIN_FLOW_RATE and 
                efficiency_ratio < PerformanceStandards.MAX_ENERGY_EFFICIENCY_RATIO):
                print("\n✅ 系统性能：优秀 - 高流量且能效良好")
            elif avg_flow > PerformanceStandards.MIN_FLOW_RATE * 0.8:
                print("\n⚠️ 系统性能：良好 - 流量合格")
            else:
                print("\n❌ 系统性能：较差 - 流量不足或能效低")
                performance_results['success'] = False
    
    # 最终系统状态
    print(f"\n最终泵站状态：")
    for i, pump in enumerate(components['pumps']):
        state = pump.get_state()
        print(f"  泵 {i+1}： {'运行' if state.get('is_running', False) else '停止'} - "
              f"流量 {state.get('outflow', 0.0):.2f} m³/s")
    
    return performance_results

def main() -> bool:
    """主函数：运行泵站控制仿真"""
    return run_pump_station_with_mas_framework()

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"\n=== 泵站控制仿真完成 ===\n退出代码： {exit_code}")
    sys.exit(exit_code)
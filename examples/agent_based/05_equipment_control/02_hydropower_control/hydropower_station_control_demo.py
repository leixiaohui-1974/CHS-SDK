#!/usr/bin/env python3
"""
水电站控制系统演示示例

本示例展示如何基于 core_lib 框架实现一个标准的水电站控制系统，包括：
1. 水库水位感知器
2. 坝后水位感知器  
3. 2台水轮机
4. 1个闸门
5. 电力需求发布方
6. 水电站控制智能体

教学目标：
- 理解水电站控制系统的架构设计
- 掌握多组件协调控制方法
- 学习电力需求响应控制策略
- 了解水位-流量-发电功率的耦合关系

技术改进：
- 符合CHS-SDK规范的配置参数
- 增强的消息传递机制
- 改进的控制代理订阅逻辑
- 完善的性能验收标准
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Any, List

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.hydropower_station import HydropowerStation
from core_lib.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent
from core_lib.local_agents.control.hydropower_station_control_agent import HydropowerStationControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class DebugWaterTurbine(WaterTurbine):
    """带调试信息的水轮机"""
    
    def handle_action_message(self, message):
        """处理控制消息并添加调试信息"""
        print(f"[DebugTurbine] {self.name} received message: {message}")
        super().handle_action_message(message)
        print(f"[DebugTurbine] {self.name} target_outflow set to: {self.target_outflow}")
    
    def step(self, action: dict, time_step: float):
        """步进方法并添加调试信息"""
        # 只在特定时间点输出调试信息
        if int(time_step * 100) % 100 == 0:  # 每100步输出一次
            print(f"[DebugTurbine] {self.name} step called with action: {action}")
            print(f"[DebugTurbine] {self.name} current target_outflow: {self.target_outflow}")
            print(f"[DebugTurbine] {self.name} current inflow: {getattr(self, '_inflow', 'NOT_SET')}")
        
        result = super().step(action, time_step)
        
        if int(time_step * 100) % 100 == 0:  # 只在特定时间点输出结果
            print(f"[DebugTurbine] {self.name} step result: {result}")
        
        # 确保总是返回有效的状态
        if result is None:
            print(f"[DebugTurbine] WARNING: {self.name} step returned None, returning default state")
            return {'outflow': 0.0, 'power': 0.0}
        
        return result

class StatefulHydropowerStation(HydropowerStation):
    """有状态的水电站，能够参与出流计算"""
    
    @property
    def is_stateful(self) -> bool:
        """水电站是有状态组件，需要参与出流计算"""
        return True
    
    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """重写step方法，确保正确计算和设置出流"""
        # 调用父类的step方法
        result = super().step(action, time_step)
        
        # 确保出流状态正确设置
        total_outflow = result.get('total_outflow', 0.0)
        self._state['outflow'] = total_outflow
        
        return result

class SimplifiedHydropowerControlAgent(Agent):
    """简化的水电站控制代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, 
                 power_demand_topic: str, upstream_reservoir: Reservoir,
                 downstream_reservoir: Reservoir, hydropower_station: HydropowerStation):
        super().__init__(agent_id)
        self.bus = message_bus
        self.upstream_reservoir = upstream_reservoir
        self.downstream_reservoir = downstream_reservoir
        self.hydropower_station = hydropower_station
        self.target_power = 0.0
        
        # 教学演示用变量
        self.demo_power_output = 0.0
        self.demo_flow_output = 0.0
        self.last_log_time = -1  # 用于控制日志输出频率
        
        # 订阅电力需求
        self.bus.subscribe(power_demand_topic, self.handle_power_demand)
        
        # 为每个水轮机创建控制主题
        self.turbine_action_topics = []
        for i, turbine in enumerate(hydropower_station.turbines):
            topic = f"action.turbine_{i+1}"
            self.turbine_action_topics.append(topic)
            print(f"[SimplifiedControl] Will publish to turbine control topic: {topic}")
        
    def handle_power_demand(self, message):
        """处理电力需求消息"""
        if isinstance(message, dict):
            self.target_power = message.get('target_power_generation', 0.0)
            print(f"[SimplifiedControl] Received power demand: {self.target_power/1e6:.1f} MW")
    
    def run(self, current_time: float):
        """控制逻辑"""
        # 获取水位信息
        upstream_state = self.upstream_reservoir.get_state()
        downstream_state = self.downstream_reservoir.get_state()
        
        upstream_level = upstream_state.get('water_level', 0.0)
        downstream_level = downstream_state.get('water_level', 0.0)
        
        # 计算水头
        head = upstream_level - downstream_level
        
        # 控制日志输出频率 - 只在需求变化时或每100秒输出一次
        should_log = (int(current_time) % 100 == 0) or (current_time - self.last_log_time > 50)
        
        if should_log:
            print(f"[SimplifiedControl] t={current_time:.0f}s: upstream={upstream_level:.1f}m, "
                  f"downstream={downstream_level:.1f}m, head={head:.1f}m, target_power={self.target_power/1e6:.1f}MW")
            self.last_log_time = current_time
        
        # 简化的控制逻辑
        if self.target_power > 0 and head > 10.0:  # 最小水头要求
            # 计算所需流量 (简化公式: P = ρ * g * Q * H * η)
            # Q = P / (ρ * g * H * η)
            rho = 1000  # kg/m3
            g = 9.81    # m/s2
            eta = 0.85  # 效率
            
            required_flow = self.target_power / (rho * g * head * eta)
            required_flow = min(required_flow, 100.0)  # 限制最大流量
            
            # 只在需求变化时输出流量信息
            if should_log:
                print(f"[SimplifiedControl] Required flow: {required_flow:.2f} m³/s for {self.target_power/1e6:.1f} MW")
            
            # 实际控制水轮机（通过消息总线发布控制命令）
            turbines = self.hydropower_station.turbines
            if turbines:
                total_power_generated = 0
                total_flow_used = 0
                
                for i, turbine in enumerate(turbines):
                    # 平均分配流量
                    turbine_flow = required_flow / len(turbines)
                    
                    # 限制单台水轮机最大流量
                    max_turbine_flow = turbine.get_parameters().get('max_flow_rate', 50.0)
                    turbine_flow = min(turbine_flow, max_turbine_flow)
                    
                    # 通过消息总线发布控制命令
                    control_message = {
                        'target_outflow': turbine_flow,
                        'timestamp': current_time
                    }
                    self.bus.publish(self.turbine_action_topics[i], control_message)
                    
                    # 调试：检查控制命令是否发送
                    if should_log:
                        print(f"[SimplifiedControl] Published to {self.turbine_action_topics[i]}: {control_message}")
                    
                    # 计算理论功率（用于演示）
                    turbine_power = turbine_flow * rho * g * head * eta
                    total_power_generated += turbine_power
                    total_flow_used += turbine_flow
                    
                    # 只在关键时间点打印详细信息
                    if should_log:
                        print(f"[SimplifiedControl] Turbine {i+1}: target_flow={turbine_flow:.2f} m³/s, "
                              f"theoretical_power={turbine_power/1e6:.2f} MW")
                
                # 记录效果用于分析
                self.demo_power_output = total_power_generated
                self.demo_flow_output = total_flow_used
                
                if should_log:
                    print(f"[SimplifiedControl] Station total: theoretical_power={total_power_generated/1e6:.2f} MW, "
                          f"target_flow={total_flow_used:.2f} m³/s")
        else:
            # 停止操作 - 关闭所有水轮机
            turbines = self.hydropower_station.turbines
            if turbines:
                for i, turbine in enumerate(turbines):
                    # 通过消息总线发布停止命令
                    control_message = {
                        'target_outflow': 0.0,
                        'timestamp': current_time
                    }
                    self.bus.publish(self.turbine_action_topics[i], control_message)
            
            # 停止操作
            self.demo_power_output = 0.0
            self.demo_flow_output = 0.0

class PowerDemandAgent(Agent):
    """电力需求发布代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_schedule = {
            0: 0.0,      # 初始无需求
            50: 20.0,    # 20MW at t=50s
            150: 40.0,   # 40MW at t=150s
            300: 60.0,   # 60MW at t=300s
            450: 30.0,   # 30MW at t=450s
            550: 0.0     # 0MW at t=550s
        }
        
    def run(self, current_time: float):
        """根据时间表发布电力需求"""
        if int(current_time) in self.demand_schedule:
            demand = self.demand_schedule[int(current_time)]
            print(f"--- POWER DEMAND: {demand} MW at t={current_time:.0f}s ---")
            message = {
                'target_power_generation': demand * 1e6,  # 转换为瓦特
                'target_total_outflow': 0.0,  # 流量目标由控制逻辑决定
                'timestamp': current_time
            }
            self.bus.publish(self.demand_topic, message)
            print(f"[PowerDemand] Published: {message}")

class DownstreamReservoirPerceptionAgent(Agent):
    """坝后水位感知代理"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus, 
                 downstream_reservoir: Reservoir, state_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.reservoir = downstream_reservoir
        self.state_topic = state_topic
        
    def run(self, current_time: float):
        """发布坝后水位状态"""
        state = self.reservoir.get_state()
        downstream_head = state.get('water_level', 0.0)
        
        # 发布坝后水位信息
        message = {
            'downstream_head': downstream_head,
            'downstream_volume': state.get('volume', 0.0),
            'timestamp': current_time
        }
        self.bus.publish(self.state_topic, message)
        
        # 每50步打印一次调试信息
        if int(current_time) % 50 == 0:
            print(f"[DownstreamPerception] t={current_time:.0f}s: downstream_head={downstream_head:.1f}m")

def create_hydropower_system():
    """创建水电站系统"""
    print("=== Creating Hydropower Station System ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'time_step': 1.0, 'start_time': 0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    POWER_DEMAND_TOPIC = "demand.power"
    UPSTREAM_STATE_TOPIC = "state.upstream_reservoir"
    DOWNSTREAM_STATE_TOPIC = "state.downstream_reservoir"
    HYDROPOWER_STATE_TOPIC = "state.hydropower_station"
    GOAL_TOPIC = "goal.hydropower_station"
    
    # 创建物理组件
    print("Creating physical components...")
    
    # 上游水库（坝前）
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 100.0, 'volume': 500e6},  # 100m水位，5亿立方米
        parameters={'surface_area': 5e6}  # 5平方公里
    )
    
    # 下游水库（坝后）
    downstream_reservoir = Reservoir(
        name="downstream_reservoir", 
        initial_state={'water_level': 20.0, 'volume': 50e6},   # 20m水位，5千万立方米
        parameters={'surface_area': 2.5e6}  # 2.5平方公里
    )
    
    # 水轮机参数
    turbine1_params = {
        'efficiency': 0.85,
        'max_flow_rate': 50.0,  # m³/s
        'rated_power': 25e6     # 25MW
    }
    
    turbine2_params = {
        'efficiency': 0.88,
        'max_flow_rate': 60.0,  # m³/s
        'rated_power': 30e6     # 30MW
    }
    
    # 创建水轮机
    turbine1 = DebugWaterTurbine(
        name="turbine_1",
        initial_state={'outflow': 0.0, 'power': 0.0},
        parameters=turbine1_params,
        message_bus=message_bus,
        action_topic="action.turbine_1"
    )
    
    turbine2 = DebugWaterTurbine(
        name="turbine_2", 
        initial_state={'outflow': 0.0, 'power': 0.0},
        parameters=turbine2_params,
        message_bus=message_bus,
        action_topic="action.turbine_2"
    )
    
    # 闸门参数
    gate_params = {
        'width': 10.0,  # 闸门宽度 10m
        'height': 5.0,  # 闸门高度 5m
        'discharge_coefficient': 0.6
    }
    
    # 创建闸门
    gate = Gate(
        name="spillway_gate",
        initial_state={'opening': 0.0, 'outflow': 0.0},
        parameters=gate_params
    )
    
    # 创建水电站
    hydropower_station = StatefulHydropowerStation(
        name="hydropower_station",
        initial_state={},
        parameters={},
        turbines=[turbine1, turbine2],
        gates=[gate]
    )
    
    # 添加组件到仿真平台
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("hydropower_station", hydropower_station)
    
    # 定义连接关系
    harness.add_connection("upstream_reservoir", "hydropower_station")
    harness.add_connection("hydropower_station", "downstream_reservoir")
    
    print("Hydropower system created successfully!")
    
    # 构建仿真环境（进行拓扑排序）
    print("Building simulation environment...")
    harness.build()
    
    # 调试：检查拓扑连接
    print(f"\n=== 拓扑连接调试 ===")
    print(f"inverse_topology: {harness.inverse_topology}")
    print(f"topology: {harness.topology}")
    print(f"sorted_components: {harness.sorted_components}")
    print(f"=== 拓扑连接调试结束 ===\n")
    
    return (harness, message_bus, POWER_DEMAND_TOPIC, UPSTREAM_STATE_TOPIC, 
            DOWNSTREAM_STATE_TOPIC, HYDROPOWER_STATE_TOPIC, GOAL_TOPIC, 
            upstream_reservoir, downstream_reservoir, hydropower_station)

def create_control_system(message_bus: MessageBus, upstream_reservoir: Reservoir,
                         downstream_reservoir: Reservoir, hydropower_station: HydropowerStation,
                         power_demand_topic: str, upstream_state_topic: str,
                         downstream_state_topic: str, hydropower_state_topic: str,
                         goal_topic: str, time_step: float):
    """创建控制系统"""
    print("=== Creating Control System ===")
    
    # 创建代理
    agents = []
    
    # 1. 电力需求代理
    power_demand_agent = PowerDemandAgent("power_demand_agent", message_bus, power_demand_topic)
    agents.append(power_demand_agent)
    
    # 2. 上游水库感知代理
    upstream_perception_agent = ReservoirPerceptionAgent(
        "upstream_perception_agent", upstream_reservoir, message_bus, upstream_state_topic
    )
    agents.append(upstream_perception_agent)
    
    # 3. 下游水库感知代理
    downstream_perception_agent = DownstreamReservoirPerceptionAgent(
        "downstream_perception_agent", message_bus, downstream_reservoir, downstream_state_topic
    )
    agents.append(downstream_perception_agent)
    
    # 4. 简化的水电站控制代理
    simplified_control_agent = SimplifiedHydropowerControlAgent(
        "simplified_hydropower_control",
        message_bus,
        power_demand_topic,
        upstream_reservoir,
        downstream_reservoir,
        hydropower_station
    )
    agents.append(simplified_control_agent)
    
    print("Control system created successfully!")
    return agents

def analyze_results(harness: SimulationHarness, agents: List[Agent]):
    """分析仿真结果"""
    print("\n=== Analyzing Results ===")
    
    history = harness.history
    if not history:
        print("No simulation history available")
        return
    
    # 调试：检查历史数据结构
    print(f"仿真历史数据点数: {len(history)}")
    if len(history) > 0:
        print(f"第一个时间步数据键: {list(history[0].keys())}")
        if 'hydropower_station' in history[0]:
            print(f"水电站状态键: {list(history[0]['hydropower_station'].keys())}")
            print(f"水电站状态示例: {history[0]['hydropower_station']}")
        
        # 检查水轮机状态
        if 'hydropower_station' in history[0]:
            station_state = history[0]['hydropower_station']
            print(f"水电站总功率: {station_state.get('total_power_generation', 0)} W")
            print(f"水电站总流量: {station_state.get('total_outflow', 0)} m³/s")
            print(f"水轮机流量: {station_state.get('turbine_outflow', 0)} m³/s")
        
        # 检查几个关键时间点的数据
        for i in [50, 100, 150, 200, 250, 300]:
            if i < len(history):
                step_data = history[i]
                if 'hydropower_station' in step_data:
                    station_state = step_data['hydropower_station']
                    print(f"t={i}s: 功率={station_state.get('total_power_generation', 0)/1e6:.2f}MW, "
                          f"流量={station_state.get('total_outflow', 0):.2f}m³/s")
    
    # 提取数据
    time_data = []
    upstream_level_data = []
    downstream_level_data = []
    power_data = []
    total_flow_data = []
    turbine_flow_data = []
    gate_flow_data = []
    
    for i, step_data in enumerate(history):
        time_data.append(i * harness.config['time_step'])
        
        # 上游水位
        if 'upstream_reservoir' in step_data:
            upstream_state = step_data['upstream_reservoir']
            upstream_level_data.append(upstream_state.get('water_level', 0))
        else:
            upstream_level_data.append(0)
        
        # 下游水位
        if 'downstream_reservoir' in step_data:
            downstream_state = step_data['downstream_reservoir']
            downstream_level_data.append(downstream_state.get('water_level', 0))
        else:
            downstream_level_data.append(0)
        
        # 水电站状态
        if 'hydropower_station' in step_data:
            station_state = step_data['hydropower_station']
            # 从水电站状态中获取功率数据
            total_power = station_state.get('total_power_generation', 0)
            if total_power > 0:
                power_data.append(total_power / 1e6)  # 转换为MW
            else:
                power_data.append(0)
            
            total_flow_data.append(station_state.get('total_outflow', 0))
            turbine_flow_data.append(station_state.get('turbine_outflow', 0))
            gate_flow_data.append(station_state.get('spillway_outflow', 0))
        else:
            power_data.append(0)
            total_flow_data.append(0)
            turbine_flow_data.append(0)
            gate_flow_data.append(0)
    
    # 计算性能指标
    avg_power = 0
    max_power = 0
    avg_flow = 0
    max_flow = 0
    
    if power_data:
        avg_power = np.mean(power_data)
        max_power = np.max(power_data)
    
    if total_flow_data:
        avg_flow = np.mean(total_flow_data)
        max_flow = np.max(total_flow_data)
        
    print(f"\n=== 仿真性能分析 ===")
    
    if power_data:
        print(f"发电功率统计:")
        print(f"  平均发电功率: {avg_power:.2f} MW")
        print(f"  最大发电功率: {max_power:.2f} MW")
        
        if total_flow_data:
            print(f"\n流量统计:")
            print(f"  平均总流量: {avg_flow:.2f} m³/s")
            print(f"  最大总流量: {max_flow:.2f} m³/s")
        
        # 绘制结果
        plot_results(time_data, upstream_level_data, downstream_level_data, 
                    power_data, total_flow_data, turbine_flow_data, gate_flow_data)
        
        # 性能验收和验证
        print(f"\n=== 控制效果验证 ===")
        
        # 检查功率输出
        if max_power > 10.0:  # 最大功率超过10MW
            print(f"✓ PASS: 水电站控制系统运行正常")
            print(f"  - 最大发电功率: {max_power:.2f} MW")
            print(f"  - 平均发电功率: {avg_power:.2f} MW")
        elif max_power > 0:
            print(f"~ PARTIAL: 水电站控制系统部分运行")
            print(f"  - 最大发电功率: {max_power:.2f} MW (偏低)")
            print(f"  - 平均发电功率: {avg_power:.2f} MW")
        else:
            print(f"✗ FAIL: 水电站控制系统未产生功率输出")
            print(f"  - 检查控制逻辑和物理模型连接")
        
        # 检查流量控制
        if max_flow > 0:
            print(f"✓ 流量控制正常: 最大流量 {max_flow:.2f} m³/s")
        else:
            print(f"✗ 流量控制异常: 未检测到流量输出")
        
        # 检查功率-流量关系
        if max_power > 0 and max_flow > 0:
            power_flow_ratio = max_power / max_flow if max_flow > 0 else 0
            print(f"✓ 功率-流量关系: {power_flow_ratio:.3f} MW/(m³/s)")
            
            # 验证功率-流量关系的合理性
            if 0.1 < power_flow_ratio < 2.0:  # 合理的功率-流量比
                print(f"✓ 功率-流量关系合理")
            else:
                print(f"⚠ 功率-流量关系异常: {power_flow_ratio:.3f} MW/(m³/s)")
        
        # 检查控制响应性
        power_changes = 0
        for i in range(1, len(power_data)):
            if abs(power_data[i] - power_data[i-1]) > 1.0:  # 功率变化超过1MW
                power_changes += 1
        
        if power_changes > 0:
            print(f"✓ 控制响应性正常: 检测到 {power_changes} 次功率变化")
        else:
            print(f"⚠ 控制响应性异常: 未检测到明显的功率变化")
    else:
        print("未检测到有效的仿真数据")
    
    return {
        'avg_power': avg_power,
        'max_power': max_power,
        'avg_flow': avg_flow,
        'max_flow': max_flow
    }

def plot_results(time_data, upstream_level_data, downstream_level_data, 
                power_data, total_flow_data, turbine_flow_data, gate_flow_data):
    """绘制结果"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 水位变化
    ax1.plot(time_data, upstream_level_data, 'b-', linewidth=2, label='Upstream Level')
    ax1.plot(time_data, downstream_level_data, 'r-', linewidth=2, label='Downstream Level')
    ax1.set_title('Reservoir Water Levels', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Water Level (m)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 发电功率
    ax2.plot(time_data, power_data, 'g-', linewidth=2, label='Power Generation')
    ax2.set_title('Power Generation', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Power (MW)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 流量分配
    ax3.plot(time_data, total_flow_data, 'purple', linewidth=2, label='Total Flow')
    ax3.plot(time_data, turbine_flow_data, 'orange', linewidth=2, label='Turbine Flow')
    ax3.plot(time_data, gate_flow_data, 'brown', linewidth=2, label='Gate Flow')
    ax3.set_title('Flow Distribution', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Flow Rate (m³/s)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 水头-功率关系
    head_data = [u - d for u, d in zip(upstream_level_data, downstream_level_data)]
    ax4.scatter(head_data, power_data, alpha=0.6, s=20)
    ax4.set_title('Head vs Power Relationship', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Head (m)')
    ax4.set_ylabel('Power (MW)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("hydropower_station_control_results.png", dpi=300, bbox_inches='tight')
    print("Results saved to hydropower_station_control_results.png")
    plt.show()

def run_hydropower_simulation():
    """运行水电站仿真"""
    print("\n=== 水电站控制系统仿真演示 ===\nHydropower Station Control System Simulation")
    print("本示例演示基于core_lib框架的水电站控制技术")
    print("教学目标:")
    print("1. 理解水电站控制系统架构设计")
    print("2. 掌握多组件协调控制方法")
    print("3. 学习电力需求响应控制策略")
    print("4. 了解水位-流量-发电功率耦合关系")
    
    # 创建系统
    (harness, message_bus, power_demand_topic, upstream_state_topic,
     downstream_state_topic, hydropower_state_topic, goal_topic,
     upstream_reservoir, downstream_reservoir, hydropower_station) = create_hydropower_system()
    
    # 创建控制系统
    agents = create_control_system(
        message_bus, upstream_reservoir, downstream_reservoir, hydropower_station,
        power_demand_topic, upstream_state_topic, downstream_state_topic,
        hydropower_state_topic, goal_topic, harness.config['time_step']
    )
    
    # 添加代理
    for agent in agents:
        harness.add_agent(agent)
    
    # 构建并运行仿真
    print("\n=== Building and Running Simulation ===")
    harness.build()
    
    print("Running simulation...")
    harness.run_mas_simulation()
    
    # 分析结果
    performance = analyze_results(harness, agents)
    
    # 确保 performance不为None
    if performance is None:
        performance = {'avg_power': 0, 'max_power': 0, 'avg_flow': 0, 'max_flow': 0}
    
    print("\n=== 仿真完成 ===\nSimulation Complete")
    print("关键学习要点:")
    print("1. ✓ 水电站需要水轮机和闸门的协调控制")
    print("2. ✓ 发电功率取决于水头和流量")
    print("3. ✓ 水库水位影响可用水头和发电能力")
    print("4. ✓ 多代理协调实现复杂控制策略")
    
    print(f"\n技术指标:")
    print(f"  系统响应性: {'正常' if performance.get('max_power', 0) > 0 else '异常'}")
    print(f"  发电效率: {performance.get('avg_power', 0):.1f} MW (平均)")
    print(f"  最大功率: {performance.get('max_power', 0):.1f} MW")
    
    return performance

if __name__ == "__main__":
    performance = run_hydropower_simulation()

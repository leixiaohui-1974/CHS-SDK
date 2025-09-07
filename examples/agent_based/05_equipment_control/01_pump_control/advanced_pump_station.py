#!/usr/bin/env python3
"""
高级泵站控制系统教学示例

本示例展示多泵协同控制技术，包括：
1. 多泵系统建模和特性分析
2. 负荷分配算法实现
3. 启停控制策略
4. 系统优化和能效管理

教学目标：
- 理解多泵系统的建模方法
- 掌握负荷分配和优化算法
- 学习泵站启停控制策略
- 了解系统能效管理方法
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent

class PumpStatus(Enum):
    """水泵状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAULT = "fault"

@dataclass
class PumpInfo:
    """水泵信息数据类"""
    pump_id: str
    max_flow: float
    max_head: float
    rated_power: float
    efficiency_curve: Dict
    status: PumpStatus = PumpStatus.STOPPED
    current_flow: float = 0.0
    current_speed: float = 0.0
    start_time: float = 0.0
    stop_time: float = 0.0

class AdvancedDemandAgent(Agent):
    """高级需求代理 - 模拟复杂的流量需求模式"""
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.base_demand = 10.0
        self.demand_pattern = "variable"  # constant, step, sinusoidal, variable
        
    def run(self, current_time: float):
        """根据需求模式生成需求"""
        if self.demand_pattern == "constant":
            demand = self.base_demand
        elif self.demand_pattern == "step":
            demand = self._step_demand(current_time)
        elif self.demand_pattern == "sinusoidal":
            demand = self._sinusoidal_demand(current_time)
        else:  # variable
            demand = self._variable_demand(current_time)
            
        self.bus.publish(self.demand_topic, {'value': demand})
        
    def _step_demand(self, time: float) -> float:
        """阶跃需求模式"""
        if time < 100:
            return 5.0
        elif time < 200:
            return 15.0
        elif time < 300:
            return 25.0
        elif time < 400:
            return 10.0
        else:
            return 20.0
            
    def _sinusoidal_demand(self, time: float) -> float:
        """正弦需求模式"""
        return self.base_demand + 10 * np.sin(2 * np.pi * time / 200)
        
    def _variable_demand(self, time: float) -> float:
        """变化需求模式"""
        base = self.base_demand
        variation = 5 * np.sin(2 * np.pi * time / 150)
        noise = 2 * np.random.normal(0, 1)
        return max(0, base + variation + noise)

class PumpStationController:
    """高级泵站控制器"""
    
    def __init__(self, pump_station: PumpStation, message_bus, control_topic_prefix: str):
        self.pump_station = pump_station
        self.message_bus = message_bus
        self.control_topic_prefix = control_topic_prefix
        self.pumps_info = self._initialize_pumps_info()
        self.current_demand = 0.0
        self.control_strategy = "optimal"  # optimal, sequential, parallel
        
    def _initialize_pumps_info(self) -> List[PumpInfo]:
        """初始化水泵信息"""
        pumps_info = []
        for i, pump in enumerate(self.pump_station.pumps):
            pump_info = PumpInfo(
                pump_id=f"pump_{i+1}",
                max_flow=pump.get_parameters().get('max_flow_rate', 10.0),
                max_head=pump.get_parameters().get('max_head', 20.0),
                rated_power=pump.get_parameters().get('power_consumption_kw', 50.0),
                efficiency_curve=pump.get_parameters().get('efficiency_curve', {})
            )
            pumps_info.append(pump_info)
        return pumps_info
        
    def update_demand(self, demand: float):
        """更新需求"""
        self.current_demand = demand
        self._control_pumps()
        
    def _control_pumps(self):
        """控制水泵运行"""
        if self.control_strategy == "optimal":
            self._optimal_control()
        elif self.control_strategy == "sequential":
            self._sequential_control()
        else:  # parallel
            self._parallel_control()
            
    def _optimal_control(self):
        """最优控制策略"""
        # 计算最优泵组合
        optimal_combination = self._find_optimal_combination(self.current_demand)
        
        # 控制水泵启停
        for i, pump_info in enumerate(self.pumps_info):
            if i in optimal_combination:
                if pump_info.status == PumpStatus.STOPPED:
                    self._start_pump(i)
                elif pump_info.status == PumpStatus.RUNNING:
                    self._adjust_pump_speed(i, optimal_combination[i])
            else:
                if pump_info.status == PumpStatus.RUNNING:
                    self._stop_pump(i)
                    
    def _sequential_control(self):
        """顺序控制策略"""
        total_flow = sum(pump.current_flow for pump in self.pumps_info 
                        if pump.status == PumpStatus.RUNNING)
        
        if total_flow < self.current_demand:
            # 需要启动更多水泵
            for i, pump_info in enumerate(self.pumps_info):
                if pump_info.status == PumpStatus.STOPPED:
                    self._start_pump(i)
                    break
        elif total_flow > self.current_demand * 1.1:  # 10%余量
            # 需要停止水泵
            for i, pump_info in enumerate(reversed(self.pumps_info)):
                if pump_info.status == PumpStatus.RUNNING:
                    self._stop_pump(i)
                    break
                    
    def _parallel_control(self):
        """并联控制策略"""
        # 所有水泵以相同速度运行
        target_speed = min(1.0, self.current_demand / sum(pump.max_flow for pump in self.pumps_info))
        
        for i, pump_info in enumerate(self.pumps_info):
            if pump_info.status == PumpStatus.RUNNING:
                self._adjust_pump_speed(i, target_speed)
                
    def _find_optimal_combination(self, demand: float) -> Dict[int, float]:
        """寻找最优泵组合"""
        n_pumps = len(self.pumps_info)
        best_combination = {}
        best_efficiency = 0.0
        
        # 尝试所有可能的泵组合
        for i in range(1, 2**n_pumps):
            combination = {}
            total_max_flow = 0
            
            for j in range(n_pumps):
                if i & (1 << j):  # 检查第j个泵是否被选中
                    combination[j] = 1.0  # 满速运行
                    total_max_flow += self.pumps_info[j].max_flow
                    
            if total_max_flow >= demand:
                # 计算效率
                efficiency = self._calculate_combination_efficiency(combination, demand)
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_combination = combination
                    
        return best_combination
        
    def _calculate_combination_efficiency(self, combination: Dict[int, float], demand: float) -> float:
        """计算组合效率"""
        total_power = 0
        total_flow = 0
        
        for pump_idx, speed in combination.items():
            pump_info = self.pumps_info[pump_idx]
            flow = pump_info.max_flow * speed
            power = pump_info.rated_power * speed**3  # 功率与转速的三次方成正比
            total_power += power
            total_flow += flow
            
        if total_power > 0:
            return (demand * 9.81 * 20) / (total_power * 1000)  # 简化效率计算
        return 0.0
        
    def _start_pump(self, pump_idx: int):
        """启动水泵"""
        pump_info = self.pumps_info[pump_idx]
        pump_info.status = PumpStatus.STARTING
        pump_info.start_time = 0.0  # 启动时间
        
        # 发布启动命令
        topic = f"{self.control_topic_prefix}.p{pump_idx+1}.start"
        self.message_bus.publish(topic, {'command': 'start'})
        
    def _stop_pump(self, pump_idx: int):
        """停止水泵"""
        pump_info = self.pumps_info[pump_idx]
        pump_info.status = PumpStatus.STOPPING
        pump_info.stop_time = 0.0  # 停止时间
        
        # 发布停止命令
        topic = f"{self.control_topic_prefix}.p{pump_idx+1}.stop"
        self.message_bus.publish(topic, {'command': 'stop'})
        
    def _adjust_pump_speed(self, pump_idx: int, speed: float):
        """调整水泵转速"""
        pump_info = self.pumps_info[pump_idx]
        pump_info.current_speed = speed
        
        # 发布转速命令
        topic = f"{self.control_topic_prefix}.p{pump_idx+1}.speed"
        self.message_bus.publish(topic, {'speed': speed})
        
    def get_status(self) -> Dict:
        """获取泵站状态"""
        running_pumps = sum(1 for pump in self.pumps_info if pump.status == PumpStatus.RUNNING)
        total_flow = sum(pump.current_flow for pump in self.pumps_info 
                        if pump.status == PumpStatus.RUNNING)
        total_power = sum(pump.rated_power * pump.current_speed**3 for pump in self.pumps_info 
                         if pump.status == PumpStatus.RUNNING)
        
        return {
            'running_pumps': running_pumps,
            'total_pumps': len(self.pumps_info),
            'total_flow': total_flow,
            'total_power': total_power,
            'demand': self.current_demand,
            'efficiency': (total_flow * 9.81 * 20) / (total_power * 1000) if total_power > 0 else 0
        }

class AdvancedPumpAnalyzer:
    """高级泵站分析器"""
    
    def __init__(self):
        self.history = {
            'time': [],
            'demand': [],
            'total_flow': [],
            'running_pumps': [],
            'total_power': [],
            'efficiency': [],
            'pump_status': []
        }
        
    def record_step(self, time: float, demand: float, status: Dict, pumps_info: List[PumpInfo]):
        """记录仿真步骤"""
        self.history['time'].append(time)
        self.history['demand'].append(demand)
        self.history['total_flow'].append(status['total_flow'])
        self.history['running_pumps'].append(status['running_pumps'])
        self.history['total_power'].append(status['total_power'])
        self.history['efficiency'].append(status['efficiency'])
        
        # 记录各泵状态
        pump_status = {}
        for pump_info in pumps_info:
            pump_status[pump_info.pump_id] = {
                'status': pump_info.status.value,
                'flow': pump_info.current_flow,
                'speed': pump_info.current_speed
            }
        self.history['pump_status'].append(pump_status)
        
    def analyze_performance(self) -> Dict:
        """分析性能"""
        if not self.history['time']:
            return {}
            
        # 计算控制性能
        flow_errors = [abs(flow - demand) for flow, demand in 
                      zip(self.history['total_flow'], self.history['demand'])]
        
        # 计算能效指标
        avg_efficiency = np.mean(self.history['efficiency'])
        avg_power = np.mean(self.history['total_power'])
        
        # 计算泵利用率
        pump_utilization = np.mean(self.history['running_pumps']) / len(self.history['pump_status'][0])
        
        performance = {
            'mean_flow_error': np.mean(flow_errors),
            'max_flow_error': np.max(flow_errors),
            'flow_rmse': np.sqrt(np.mean([e**2 for e in flow_errors])),
            'average_efficiency': avg_efficiency,
            'average_power': avg_power,
            'pump_utilization': pump_utilization,
            'energy_efficiency': avg_efficiency * pump_utilization
        }
        
        return performance
        
    def plot_results(self, save_path: str = "advanced_pump_station_results.png"):
        """绘制结果"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 流量控制响应
        ax1.plot(self.history['time'], self.history['demand'], 'r--', 
                linewidth=2, label='Demand')
        ax1.plot(self.history['time'], self.history['total_flow'], 'b-', 
                linewidth=2, label='Total Flow')
        ax1.set_title('Flow Control Response', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Flow Rate (m³/s)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 运行水泵数量
        ax2.plot(self.history['time'], self.history['running_pumps'], 'g-', 
                linewidth=2, label='Running Pumps')
        ax2.set_title('Pump Operation Status', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Number of Running Pumps')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 功率消耗
        ax3.plot(self.history['time'], self.history['total_power'], 'purple', 
                linewidth=2, label='Total Power')
        ax3.set_title('Power Consumption', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Power (kW)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 效率特性
        ax4.plot(self.history['time'], self.history['efficiency'], 'orange', 
                linewidth=2, label='System Efficiency')
        ax4.set_title('System Efficiency Over Time', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Efficiency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Results saved to {save_path}")
        plt.show()

def create_advanced_pump_system():
    """创建高级泵站系统"""
    print("=== Creating Advanced Pump Station System ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC_PREFIX = "action.pump"
    
    # 创建物理组件
    print("Creating physical components...")
    
    # 上游水库
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 25.0, 'volume': 100e6},
        parameters={'surface_area': 4.0e6}
    )
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir",
        initial_state={'water_level': 8.0, 'volume': 20e6},
        parameters={'surface_area': 2.5e6}
    )
    
    # 创建多台水泵 - 不同规格
    pumps = []
    pump_specs = [
        {'max_flow_rate': 15.0, 'max_head': 25.0, 'power_consumption_kw': 75},
        {'max_flow_rate': 12.0, 'max_head': 30.0, 'power_consumption_kw': 80},
        {'max_flow_rate': 18.0, 'max_head': 20.0, 'power_consumption_kw': 70},
        {'max_flow_rate': 10.0, 'max_head': 35.0, 'power_consumption_kw': 85}
    ]
    
    for i, specs in enumerate(pump_specs):
        pump = Pump(
            name=f"pump_{i+1}",
            initial_state={'outflow': 0, 'speed': 0, 'power_draw_kw': 0},
            parameters=specs,
            message_bus=message_bus,
            action_topic=f"{CONTROL_TOPIC_PREFIX}.p{i+1}.speed",
            action_key='speed'
        )
        pumps.append(pump)
    
    # 创建泵站
    pump_station = PumpStation(
        name="advanced_pump_station",
        initial_state={},
        parameters={},
        pumps=pumps
    )
    
    # 添加组件
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("advanced_pump_station", pump_station)
    
    # 定义连接
    harness.add_connection("upstream_reservoir", "advanced_pump_station")
    harness.add_connection("advanced_pump_station", "downstream_reservoir")
    
    print("Advanced pump station system created successfully!")
    return harness, message_bus, DEMAND_TOPIC, CONTROL_TOPIC_PREFIX, pump_station

def run_advanced_simulation():
    """运行高级仿真"""
    print("\n=== Advanced Pump Station Control System Simulation ===")
    print("This example demonstrates multi-pump coordination and optimization")
    print("Learning objectives:")
    print("1. Multi-pump system modeling and control")
    print("2. Load distribution and optimization algorithms")
    print("3. Pump start/stop control strategies")
    print("4. System efficiency management")
    
    # 创建系统
    harness, message_bus, demand_topic, control_topic_prefix, pump_station = create_advanced_pump_system()
    
    # 创建代理和控制器
    demand_agent = AdvancedDemandAgent("advanced_demand_agent", message_bus, demand_topic)
    pump_controller = PumpStationController(pump_station, message_bus, control_topic_prefix)
    
    # 添加代理
    harness.add_agent(demand_agent)
    
    # 创建分析器
    analyzer = AdvancedPumpAnalyzer()
    
    # 构建并运行仿真
    print("\n=== Building and Running Simulation ===")
    harness.build()
    
    num_steps = int(harness.end_time / harness.dt)
    current_demand = 0.0
    
    print(f"Running simulation for {num_steps} steps...")
    
    for i in range(num_steps):
        current_time = i * harness.dt
        
        # 运行代理
        demand_agent.run(current_time)
        
        # 获取当前需求
        messages = message_bus.get_messages(demand_topic)
        if messages:
            current_demand = messages[-1].get('value', current_demand)
            
        # 更新控制器
        pump_controller.update_demand(current_demand)
        
        # 步进物理模型
        harness._step_physical_models(harness.dt)
        
        # 记录数据
        status = pump_controller.get_status()
        analyzer.record_step(current_time, current_demand, status, pump_controller.pumps_info)
        
        # 打印状态（每50步）
        if i % 50 == 0:
            print(f"Time {current_time:.0f}s: Demand={current_demand:.1f} m³/s, "
                  f"Flow={status['total_flow']:.1f} m³/s, "
                  f"Pumps={status['running_pumps']}/{status['total_pumps']}, "
                  f"Power={status['total_power']:.1f} kW, "
                  f"Efficiency={status['efficiency']:.2f}")
    
    # 分析结果
    print("\n=== Performance Analysis ===")
    performance = analyzer.analyze_performance()
    
    print(f"Control Performance:")
    print(f"  Mean Flow Error: {performance.get('mean_flow_error', 0):.3f} m³/s")
    print(f"  Maximum Flow Error: {performance.get('max_flow_error', 0):.3f} m³/s")
    print(f"  Flow RMSE: {performance.get('flow_rmse', 0):.3f} m³/s")
    
    print(f"\nEnergy Performance:")
    print(f"  Average Efficiency: {performance.get('average_efficiency', 0):.3f}")
    print(f"  Average Power: {performance.get('average_power', 0):.1f} kW")
    print(f"  Pump Utilization: {performance.get('pump_utilization', 0):.2f}")
    print(f"  Energy Efficiency: {performance.get('energy_efficiency', 0):.3f}")
    
    # 绘制结果
    analyzer.plot_results("advanced_pump_station_results.png")
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. Multi-pump coordination requires sophisticated control algorithms")
    print("2. Optimal pump combination depends on efficiency characteristics")
    print("3. System efficiency varies with operating conditions")
    print("4. Advanced control strategies can significantly improve performance")
    
    return performance

if __name__ == "__main__":
    performance = run_advanced_simulation()

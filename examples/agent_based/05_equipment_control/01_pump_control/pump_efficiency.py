#!/usr/bin/env python3
"""
水泵效率优化控制系统教学示例

本示例展示水泵能效管理和优化技术，包括：
1. 水泵效率特性分析和建模
2. 变频调速控制策略
3. 最优运行点搜索算法
4. 能耗优化和成本控制

教学目标：
- 理解水泵效率特性和影响因素
- 掌握变频调速控制技术
- 学习最优运行点搜索方法
- 了解能耗优化和成本控制策略
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import minimize_scalar
import pandas as pd

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent

@dataclass
class EfficiencyPoint:
    """效率点数据类"""
    flow: float
    head: float
    efficiency: float
    power: float
    speed: float

class PumpEfficiencyModel:
    """水泵效率模型"""
    
    def __init__(self, pump_params: Dict):
        self.max_flow = pump_params.get('max_flow_rate', 20.0)
        self.max_head = pump_params.get('max_head', 30.0)
        self.rated_power = pump_params.get('power_consumption_kw', 100.0)
        self.max_speed = pump_params.get('max_speed', 1500.0)
        
        # 效率特性曲线参数
        self.efficiency_params = {
            'peak_efficiency': 0.85,
            'peak_flow_ratio': 0.7,  # 峰值效率对应的流量比例
            'flow_range': [0.1, 1.0],  # 有效流量范围
            'head_range': [0.5, 1.0]   # 有效扬程范围
        }
        
    def calculate_efficiency(self, flow: float, head: float, speed: float) -> float:
        """计算水泵效率"""
        # 归一化参数
        flow_ratio = flow / self.max_flow
        head_ratio = head / self.max_head
        speed_ratio = speed / self.max_speed
        
        print(f"[EfficiencyModel] Flow={flow}, Head={head}, Speed={speed}")
        print(f"[EfficiencyModel] Ratios: flow={flow_ratio:.3f}, head={head_ratio:.3f}, speed={speed_ratio:.3f}")
        
        # 效率计算（基于实际水泵特性）
        if flow_ratio < 0.1 or flow_ratio > 1.0:
            print(f"[EfficiencyModel] Flow ratio {flow_ratio:.3f} out of range [0.1, 1.0], returning 0")
            return 0.0
            
        # 流量效率特性
        flow_efficiency = self._flow_efficiency_curve(flow_ratio)
        
        # 扬程效率特性
        head_efficiency = self._head_efficiency_curve(head_ratio)
        
        # 转速效率特性
        speed_efficiency = self._speed_efficiency_curve(speed_ratio)
        
        # 综合效率
        total_efficiency = flow_efficiency * head_efficiency * speed_efficiency
        return min(total_efficiency, self.efficiency_params['peak_efficiency'])
        
    def _flow_efficiency_curve(self, flow_ratio: float) -> float:
        """流量效率特性曲线"""
        peak_ratio = self.efficiency_params['peak_flow_ratio']
        
        if flow_ratio <= peak_ratio:
            # 上升段
            return 0.3 + 0.7 * (flow_ratio / peak_ratio)
        else:
            # 下降段
            return 1.0 - 0.3 * ((flow_ratio - peak_ratio) / (1.0 - peak_ratio))
            
    def _head_efficiency_curve(self, head_ratio: float) -> float:
        """扬程效率特性曲线"""
        if head_ratio < 0.5:
            return 0.5 + head_ratio
        elif head_ratio <= 1.0:
            return 1.0
        else:
            return max(0.7, 1.0 - 0.3 * (head_ratio - 1.0))
            
    def _speed_efficiency_curve(self, speed_ratio: float) -> float:
        """转速效率特性曲线"""
        if speed_ratio < 0.3:
            return 0.5 + 0.5 * speed_ratio / 0.3
        elif speed_ratio <= 1.0:
            return 1.0
        else:
            return max(0.8, 1.0 - 0.2 * (speed_ratio - 1.0))
            
    def calculate_power(self, flow: float, head: float, efficiency: float) -> float:
        """计算功率消耗"""
        if efficiency <= 0:
            return 0.0
        return (flow * head * 9.81 * 1000) / (efficiency * 1000)  # kW
        
    def find_optimal_operating_point(self, target_flow: float, target_head: float) -> EfficiencyPoint:
        """寻找最优运行点"""
        def objective(speed_ratio):
            speed = speed_ratio * self.max_speed
            efficiency = self.calculate_efficiency(target_flow, target_head, speed)
            power = self.calculate_power(target_flow, target_head, efficiency)
            return -efficiency  # 最大化效率（最小化负效率）
            
        # 约束条件
        constraints = [
            {'type': 'ineq', 'fun': lambda x: x},  # speed_ratio >= 0
            {'type': 'ineq', 'fun': lambda x: 1.0 - x}  # speed_ratio <= 1
        ]
        
        # 优化
        result = minimize_scalar(objective, bounds=(0.3, 1.0), method='bounded')
        
        optimal_speed_ratio = result.x
        optimal_speed = optimal_speed_ratio * self.max_speed
        optimal_efficiency = self.calculate_efficiency(target_flow, target_head, optimal_speed)
        optimal_power = self.calculate_power(target_flow, target_head, optimal_efficiency)
        
        return EfficiencyPoint(
            flow=target_flow,
            head=target_head,
            efficiency=optimal_efficiency,
            power=optimal_power,
            speed=optimal_speed
        )

class VariableSpeedController:
    """变频调速控制器"""
    
    def __init__(self, efficiency_model: PumpEfficiencyModel):
        self.efficiency_model = efficiency_model
        self.current_speed = 0.0
        self.target_flow = 0.0
        self.target_head = 0.0
        self.control_mode = "efficiency"  # efficiency, flow, power
        
    def update_targets(self, flow: float, head: float):
        """更新目标值"""
        self.target_flow = flow
        self.target_head = head
        
    def calculate_optimal_speed(self) -> float:
        """计算最优转速"""
        if self.control_mode == "efficiency":
            optimal_point = self.efficiency_model.find_optimal_operating_point(
                self.target_flow, self.target_head
            )
            return optimal_point.speed
        elif self.control_mode == "flow":
            # 基于流量控制
            return min(1.0, self.target_flow / self.efficiency_model.max_flow) * self.efficiency_model.max_speed
        else:  # power
            # 基于功率控制
            return min(1.0, self.target_flow / self.efficiency_model.max_flow) * self.efficiency_model.max_speed
            
    def get_efficiency_at_speed(self, speed: float) -> float:
        """获取指定转速下的效率"""
        return self.efficiency_model.calculate_efficiency(
            self.target_flow, self.target_head, speed
        )

class EfficiencyOptimizationAgent(Agent):
    """效率优化代理"""
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str, 
                 pump_station: PumpStation, efficiency_model: PumpEfficiencyModel):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.pump_station = pump_station
        self.efficiency_model = efficiency_model
        self.variable_speed_controller = VariableSpeedController(efficiency_model)
        self.current_demand = 0.0
        self.optimization_history = []
        
        # 订阅需求主题
        self.bus.subscribe(self.demand_topic, self.handle_demand_message)
        
    def handle_demand_message(self, message):
        """处理需求消息"""
        self.current_demand = message.get('value', self.current_demand)
        print(f"[EfficiencyAgent] Received demand: {self.current_demand}")
        
    def run(self, current_time: float):
        """运行效率优化"""
        # 使用当前需求（通过订阅更新）
        if self.current_demand <= 0:
            print(f"[EfficiencyAgent] Warning: No demand received, current_demand={self.current_demand}")
            return
            
        # 计算目标扬程（简化计算）
        target_head = 20.0  # 固定扬程
        
        # 更新控制器目标
        self.variable_speed_controller.update_targets(self.current_demand, target_head)
        
        # 计算最优转速
        optimal_speed = self.variable_speed_controller.calculate_optimal_speed()
        
        # 计算效率
        efficiency = self.variable_speed_controller.get_efficiency_at_speed(optimal_speed)
        
        print(f"[EfficiencyAgent] Demand={self.current_demand}, Speed={optimal_speed}, Efficiency={efficiency}")
        
        # 记录优化历史
        self.optimization_history.append({
            'time': current_time,
            'demand': self.current_demand,
            'optimal_speed': optimal_speed,
            'efficiency': efficiency,
            'power': self.efficiency_model.calculate_power(
                self.current_demand, target_head, efficiency
            )
        })
        
        # 发布控制命令 - 适配当前的 Pump 接口
        # 基于效率决定是否启动泵（简化处理）
        control_signal = 1 if efficiency > 0.5 else 0
        control_topic = "action.pump.efficiency_pump"
        self.bus.publish(control_topic, {'control_signal': control_signal})

class VariableDemandAgent(Agent):
    """变化需求代理"""
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.base_demand = 10.0
        self.demand_pattern = "optimization_test"
        
    def run(self, current_time: float):
        """生成优化测试需求"""
        if self.demand_pattern == "optimization_test":
            demand = self._optimization_test_pattern(current_time)
        else:
            demand = self.base_demand
            
        print(f"[DemandAgent] Publishing demand: {demand} at time {current_time}")
        self.bus.publish(self.demand_topic, {'value': demand})
        
    def _optimization_test_pattern(self, time: float) -> float:
        """优化测试需求模式"""
        if time < 100:
            return 5.0   # 低负荷
        elif time < 200:
            return 15.0  # 中负荷
        elif time < 300:
            return 25.0  # 高负荷
        elif time < 400:
            return 8.0   # 中低负荷
        elif time < 500:
            return 20.0  # 中高负荷
        else:
            return 12.0  # 中等负荷

class EfficiencyAnalyzer:
    """效率分析器"""
    
    def __init__(self):
        self.history = {
            'time': [],
            'demand': [],
            'actual_flow': [],
            'speed': [],
            'efficiency': [],
            'power': [],
            'optimal_efficiency': [],
            'efficiency_loss': []
        }
        
    def record_step(self, time: float, demand: float, pump_state: Dict, 
                   optimization_data: Dict):
        """记录仿真步骤"""
        self.history['time'].append(time)
        self.history['demand'].append(demand)
        self.history['actual_flow'].append(pump_state.get('total_outflow', 0))
        # 使用优化数据中的转速，因为当前 Pump 类不直接支持转速
        self.history['speed'].append(optimization_data.get('optimal_speed', 0))
        self.history['efficiency'].append(pump_state.get('efficiency', 0))
        self.history['power'].append(pump_state.get('total_power_draw_kw', 0))
        self.history['optimal_efficiency'].append(optimization_data.get('efficiency', 0))
        
        # 计算效率损失
        optimal_eff = optimization_data.get('efficiency', 0)
        actual_eff = pump_state.get('efficiency', 0)
        efficiency_loss = max(0, optimal_eff - actual_eff)
        self.history['efficiency_loss'].append(efficiency_loss)
        
    def analyze_efficiency_performance(self) -> Dict:
        """分析效率性能"""
        if not self.history['time']:
            return {}
            
        # 计算效率指标
        avg_efficiency = np.mean(self.history['efficiency'])
        avg_optimal_efficiency = np.mean(self.history['optimal_efficiency'])
        avg_efficiency_loss = np.mean(self.history['efficiency_loss'])
        
        # 计算能耗指标
        total_energy = np.sum(self.history['power']) * 1.0  # 假设时间步长为1秒
        avg_power = np.mean(self.history['power'])
        
        # 计算节能潜力
        energy_savings_potential = avg_efficiency_loss * avg_power
        
        performance = {
            'average_efficiency': avg_efficiency,
            'average_optimal_efficiency': avg_optimal_efficiency,
            'average_efficiency_loss': avg_efficiency_loss,
            'efficiency_improvement_potential': avg_efficiency_loss / avg_efficiency * 100,
            'total_energy_consumption': total_energy,
            'average_power': avg_power,
            'energy_savings_potential': energy_savings_potential
        }
        
        return performance
        
    def plot_efficiency_analysis(self, save_path: str = "pump_efficiency_results.png"):
        """绘制效率分析结果"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 效率对比
        ax1.plot(self.history['time'], self.history['efficiency'], 'b-', 
                linewidth=2, label='Actual Efficiency')
        ax1.plot(self.history['time'], self.history['optimal_efficiency'], 'r--', 
                linewidth=2, label='Optimal Efficiency')
        ax1.set_title('Efficiency Comparison', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Efficiency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 效率损失
        ax2.plot(self.history['time'], self.history['efficiency_loss'], 'orange', 
                linewidth=2, label='Efficiency Loss')
        ax2.set_title('Efficiency Loss Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Efficiency Loss')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 功率消耗
        ax3.plot(self.history['time'], self.history['power'], 'purple', 
                linewidth=2, label='Power Consumption')
        ax3.set_title('Power Consumption', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Power (kW)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 效率-流量特性
        ax4.scatter(self.history['actual_flow'], self.history['efficiency'], 
                   alpha=0.6, label='Actual Operating Points')
        ax4.scatter(self.history['demand'], self.history['optimal_efficiency'], 
                   alpha=0.6, label='Optimal Operating Points')
        ax4.set_title('Efficiency vs Flow Rate', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Flow Rate (m³/s)')
        ax4.set_ylabel('Efficiency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Results saved to {save_path}")
        plt.show()

def create_efficiency_optimization_system():
    """创建效率优化系统"""
    print("=== Creating Pump Efficiency Optimization System ===")
    
    # 仿真配置
    simulation_config = {'end_time': 600, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus
    
    # 通信主题
    DEMAND_TOPIC = "demand.flow"
    CONTROL_TOPIC = "action.pump.speed"
    
    # 创建物理组件
    print("Creating physical components...")
    
    # 上游水库
    upstream_reservoir = Reservoir(
        name="upstream_reservoir",
        initial_state={'water_level': 30.0, 'volume': 150e6},
        parameters={'surface_area': 5.0e6}
    )
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir",
        initial_state={'water_level': 10.0, 'volume': 30e6},
        parameters={'surface_area': 3.0e6}
    )
    
    # 水泵参数 - 高效率水泵
    pump_params = {
        'max_flow_rate': 30.0,
        'max_head': 25.0,
        'max_speed': 1800.0,
        'power_consumption_kw': 120,
        'efficiency_curve': {
            'flow_points': [0, 5, 10, 15, 20, 25, 30],
            'efficiency_points': [0, 70, 80, 85, 88, 85, 80]
        }
    }
    
    # 创建水泵
    pump = Pump(
        name="efficiency_pump",
        initial_state={'outflow': 0, 'power_draw_kw': 0, 'status': 0, 'efficiency': 0.0},
        parameters=pump_params,
        message_bus=message_bus,
        action_topic=CONTROL_TOPIC
    )
    
    # 创建泵站
    pump_station = PumpStation(
        name="efficiency_pump_station",
        initial_state={},
        parameters={},
        pumps=[pump]
    )
    
    # 添加组件
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("efficiency_pump_station", pump_station)
    
    # 定义连接
    harness.add_connection("upstream_reservoir", "efficiency_pump_station")
    harness.add_connection("efficiency_pump_station", "downstream_reservoir")
    
    print("Efficiency optimization system created successfully!")
    return harness, message_bus, DEMAND_TOPIC, CONTROL_TOPIC, pump_station, pump_params

def run_efficiency_optimization_simulation():
    """运行效率优化仿真"""
    print("\n=== Pump Efficiency Optimization System Simulation ===")
    print("This example demonstrates pump efficiency optimization techniques")
    print("Learning objectives:")
    print("1. Pump efficiency characteristics and modeling")
    print("2. Variable speed control strategies")
    print("3. Optimal operating point search algorithms")
    print("4. Energy consumption optimization")
    
    # 创建系统
    harness, message_bus, demand_topic, control_topic, pump_station, pump_params = create_efficiency_optimization_system()
    
    # 创建效率模型
    efficiency_model = PumpEfficiencyModel(pump_params)
    
    # 创建代理
    demand_agent = VariableDemandAgent("variable_demand_agent", message_bus, demand_topic)
    efficiency_agent = EfficiencyOptimizationAgent(
        "efficiency_optimization_agent", message_bus, demand_topic, 
        pump_station, efficiency_model
    )
    
    # 添加代理
    harness.add_agent(demand_agent)
    harness.add_agent(efficiency_agent)
    
    # 创建分析器
    analyzer = EfficiencyAnalyzer()
    
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
        efficiency_agent.run(current_time)
        
        # 需求通过代理的订阅机制自动更新，这里使用效率代理的当前需求
        current_demand = efficiency_agent.current_demand
            
        # 步进物理模型
        harness._step_physical_models(harness.dt)
        
        # 记录数据
        pump_state = pump_station.get_state()
        optimization_data = efficiency_agent.optimization_history[-1] if efficiency_agent.optimization_history else {}
        analyzer.record_step(current_time, current_demand, pump_state, optimization_data)
        
        # 打印状态（每50步）
        if i % 50 == 0:
            optimization_data = efficiency_agent.optimization_history[-1] if efficiency_agent.optimization_history else {}
            print(f"Time {current_time:.0f}s: Demand={current_demand:.1f} m³/s, "
                  f"Flow={pump_state.get('total_outflow', 0):.1f} m³/s, "
                  f"Speed={optimization_data.get('optimal_speed', 0):.0f} rpm, "
                  f"Efficiency={pump_state.get('efficiency', 0):.3f}, "
                  f"Power={pump_state.get('total_power_draw_kw', 0):.1f} kW")
    
    # 分析结果
    print("\n=== Efficiency Performance Analysis ===")
    performance = analyzer.analyze_efficiency_performance()
    
    print(f"Efficiency Performance:")
    print(f"  Average Efficiency: {performance.get('average_efficiency', 0):.3f}")
    print(f"  Average Optimal Efficiency: {performance.get('average_optimal_efficiency', 0):.3f}")
    print(f"  Average Efficiency Loss: {performance.get('average_efficiency_loss', 0):.3f}")
    print(f"  Efficiency Improvement Potential: {performance.get('efficiency_improvement_potential', 0):.1f}%")
    
    print(f"\nEnergy Performance:")
    print(f"  Total Energy Consumption: {performance.get('total_energy_consumption', 0):.1f} kWh")
    print(f"  Average Power: {performance.get('average_power', 0):.1f} kW")
    print(f"  Energy Savings Potential: {performance.get('energy_savings_potential', 0):.1f} kW")
    
    # 绘制结果
    analyzer.plot_efficiency_analysis("pump_efficiency_optimization_results.png")
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. Pump efficiency varies significantly with operating conditions")
    print("2. Variable speed control can optimize efficiency")
    print("3. Optimal operating points depend on efficiency characteristics")
    print("4. Significant energy savings are possible through optimization")
    
    return performance

if __name__ == "__main__":
    performance = run_efficiency_optimization_simulation()

#!/usr/bin/env python3
"""
基础水泵控制系统教学示例

本示例展示单台水泵的基本控制方法，包括：
1. 水泵数学模型和特性曲线
2. PID控制策略实现
3. 流量-扬程特性分析
4. 控制性能评估

教学目标：
- 理解水泵的物理特性和数学模型
- 掌握PID控制在水泵控制中的应用
- 学习水泵特性曲线的分析方法
- 掌握控制系统的性能评估方法
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.unified_pump_control_agent import UnifiedPumpControlAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.interfaces import Agent

class DemandAgent(Agent):
    """需求代理 - 模拟变化的流量需求"""
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str):
        super().__init__(agent_id)
        self.bus = message_bus
        self.demand_topic = demand_topic
        self.demand_schedule = {
            50: 5.0,   # 5 m³/s at t=50s
            150: 15.0, # 15 m³/s at t=150s
            300: 8.0,  # 8 m³/s at t=300s
            450: 20.0  # 20 m³/s at t=450s
        }
        
    def run(self, current_time: float):
        """根据时间表发布需求"""
        if int(current_time) in self.demand_schedule:
            demand = self.demand_schedule[int(current_time)]
            print(f"--- DEMAND CHANGE: New demand at t={current_time:.0f}s: {demand} m³/s ---")
            self.bus.publish(self.demand_topic, {'value': demand})

class PumpControlAnalyzer:
    """水泵控制性能分析器"""
    
    def __init__(self):
        self.history = {
            'time': [],
            'demand': [],
            'actual_flow': [],
            'pump_speed': [],
            'power': [],
            'efficiency': []
        }
        
    def record_step(self, time: float, demand: float, pump_state: Dict):
        """记录仿真步骤数据"""
        self.history['time'].append(time)
        self.history['demand'].append(demand)
        self.history['actual_flow'].append(pump_state.get('outflow', 0))
        self.history['pump_speed'].append(pump_state.get('speed', 0))
        self.history['power'].append(pump_state.get('power_draw_kw', 0))
        self.history['efficiency'].append(pump_state.get('efficiency', 0))
        
    def analyze_performance(self) -> Dict:
        """分析控制性能"""
        if not self.history['time']:
            return {}
            
        # 计算控制误差
        errors = [abs(actual - demand) for actual, demand in 
                 zip(self.history['actual_flow'], self.history['demand'])]
        
        # 计算性能指标
        performance = {
            'mean_absolute_error': np.mean(errors),
            'max_error': np.max(errors),
            'rmse': np.sqrt(np.mean([e**2 for e in errors])),
            'average_power': np.mean(self.history['power']),
            'average_efficiency': np.mean(self.history['efficiency']),
            'settling_time': self._calculate_settling_time(),
            'overshoot': self._calculate_overshoot()
        }
        
        return performance
        
    def _calculate_settling_time(self) -> float:
        """计算调节时间（误差小于5%的时间）"""
        if len(self.history['time']) < 10:
            return 0.0
            
        target_error = 0.05  # 5%误差
        for i in range(len(self.history['time']) - 1, -1, -1):
            if i > 0:
                error = abs(self.history['actual_flow'][i] - self.history['demand'][i])
                if error > target_error:
                    return self.history['time'][i]
        return 0.0
        
    def _calculate_overshoot(self) -> float:
        """计算超调量"""
        if len(self.history['actual_flow']) < 10:
            return 0.0
            
        max_flow = np.max(self.history['actual_flow'])
        final_flow = self.history['actual_flow'][-1]
        
        if final_flow > 0:
            return (max_flow - final_flow) / final_flow * 100
        return 0.0
        
    def plot_results(self, save_path: str = "pump_control_results.png"):
        """绘制控制结果"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 流量控制响应
        ax1.plot(self.history['time'], self.history['demand'], 'r--', 
                linewidth=2, label='Demand')
        ax1.plot(self.history['time'], self.history['actual_flow'], 'b-', 
                linewidth=2, label='Actual Flow')
        ax1.set_title('Flow Control Response', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Flow Rate (m³/s)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 控制误差
        errors = [abs(actual - demand) for actual, demand in 
                 zip(self.history['actual_flow'], self.history['demand'])]
        ax2.plot(self.history['time'], errors, 'g-', linewidth=2, label='Control Error')
        ax2.axhline(y=0.5, color='orange', linestyle='--', label='Acceptable Error')
        ax2.set_title('Control Error Over Time', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Error (m³/s)')
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
        
        # 4. 效率特性
        ax4.plot(self.history['actual_flow'], self.history['efficiency'], 'orange', 
                linewidth=2, label='Efficiency')
        ax4.set_title('Pump Efficiency vs Flow', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Flow Rate (m³/s)')
        ax4.set_ylabel('Efficiency (%)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Results saved to {save_path}")
        plt.show()

def create_pump_system():
    """创建水泵系统"""
    print("=== Creating Pump System ===")
    
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
        initial_state={'water_level': 20.0, 'volume': 50e6},
        parameters={'surface_area': 2.5e6}
    )
    
    # 下游水库
    downstream_reservoir = Reservoir(
        name="downstream_reservoir", 
        initial_state={'water_level': 5.0, 'volume': 10e6},
        parameters={'surface_area': 2.0e6}
    )
    
    # 水泵参数 - 基于实际水泵特性
    pump_params = {
        'max_flow_rate': 25.0,      # 最大流量 m³/s
        'max_head': 30.0,          # 最大扬程 m
        'max_speed': 1500.0,       # 最大转速 rpm
        'power_consumption_kw': 100, # 额定功率 kW
        'efficiency_curve': {      # 效率特性曲线
            'flow_points': [0, 5, 10, 15, 20, 25],
            'efficiency_points': [0, 65, 80, 85, 80, 70]
        }
    }
    
    # 创建水泵
    pump = Pump(
        name="main_pump",
        initial_state={'outflow': 0, 'speed': 0, 'power_draw_kw': 0},
        parameters=pump_params,
        message_bus=message_bus,
        action_topic=CONTROL_TOPIC,
        action_key='control_signal'
    )
    
    # 创建泵站
    pump_station = PumpStation(
        name="pump_station_1",
        initial_state={},
        parameters={},
        pumps=[pump]
    )
    
    # 添加组件到仿真平台
    harness.add_component("upstream_reservoir", upstream_reservoir)
    harness.add_component("downstream_reservoir", downstream_reservoir)
    harness.add_component("pump_station_1", pump_station)
    
    # 定义连接关系
    harness.add_connection("upstream_reservoir", "pump_station_1")
    harness.add_connection("pump_station_1", "downstream_reservoir")
    
    print("Pump system created successfully!")
    return harness, message_bus, DEMAND_TOPIC, CONTROL_TOPIC, pump_station

def create_control_system(message_bus, demand_topic: str, control_topic: str, 
                         pump_station, dt: float):
    """创建控制系统"""
    print("=== Creating Control System ===")
    
    # 创建需求代理
    demand_agent = DemandAgent("demand_agent", message_bus, demand_topic)
    
    # 创建PID控制器 - 针对流量控制优化
    pid_controller = PIDController(
        Kp=2.0,      # 比例增益
        Ki=0.5,      # 积分增益  
        Kd=0.1,      # 微分增益
        setpoint=10.0,  # 初始设定点
        min_output=0.0,  # 最小输出
        max_output=1.0   # 最大输出（相对转速）
    )
    
    # 创建水泵控制代理
    pump_control_agent = UnifiedPumpControlAgent(
        agent_id="pump_control_agent",
        message_bus=message_bus,
        pump_station=pump_station,
        demand_topic=demand_topic,
        control_topic_prefix="action.pump",
        dt=dt
    )
    
    print("Control system created successfully!")
    return demand_agent, pump_control_agent

def run_simulation():
    """运行仿真"""
    print("\n=== Basic Pump Control System Simulation ===")
    print("This example demonstrates single pump control with PID strategy")
    print("Learning objectives:")
    print("1. Understanding pump physical characteristics")
    print("2. PID control implementation for flow control")
    print("3. Performance analysis and optimization")
    print("4. Real-time demand response")
    
    # 创建系统
    harness, message_bus, demand_topic, control_topic, pump_station = create_pump_system()
    demand_agent, pump_control_agent = create_control_system(
        message_bus, demand_topic, control_topic, pump_station, harness.dt
    )
    
    # 添加代理
    harness.add_agent(demand_agent)
    
    # 创建性能分析器
    analyzer = PumpControlAnalyzer()
    
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
        
        # 步进物理模型
        harness._step_physical_models(harness.dt)
        
        # 记录数据
        pump_state = pump_station.get_state()
        analyzer.record_step(current_time, current_demand, pump_state)
        
        # 打印状态（每50步）
        if i % 50 == 0:
            print(f"Time {current_time:.0f}s: Demand={current_demand:.1f} m³/s, "
                  f"Flow={pump_state.get('total_outflow', 0):.1f} m³/s, "
                  f"Power={pump_state.get('total_power_draw_kw', 0):.1f} kW")
    
    # 分析结果
    print("\n=== Performance Analysis ===")
    performance = analyzer.analyze_performance()
    
    print(f"Control Performance:")
    print(f"  Mean Absolute Error: {performance.get('mean_absolute_error', 0):.3f} m³/s")
    print(f"  Maximum Error: {performance.get('max_error', 0):.3f} m³/s")
    print(f"  RMSE: {performance.get('rmse', 0):.3f} m³/s")
    print(f"  Settling Time: {performance.get('settling_time', 0):.1f} s")
    print(f"  Overshoot: {performance.get('overshoot', 0):.1f}%")
    
    print(f"\nEnergy Performance:")
    print(f"  Average Power: {performance.get('average_power', 0):.1f} kW")
    print(f"  Average Efficiency: {performance.get('average_efficiency', 0):.1f}%")
    
    # 绘制结果
    analyzer.plot_results("basic_pump_control_results.png")
    
    print("\n=== Simulation Complete ===")
    print("Key Learning Points:")
    print("1. PID control provides good tracking performance for pump flow control")
    print("2. Pump efficiency varies with operating point")
    print("3. System response time depends on control parameters")
    print("4. Demand changes require appropriate control tuning")
    
    return performance

if __name__ == "__main__":
    performance = run_simulation()

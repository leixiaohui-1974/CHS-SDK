"""
控制过程可视化脚本
用于分析水位控制系统的控制过程，包括水位变化、闸门开度和控制信号
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class DebugMessageTracker:
    """用于跟踪消息传递的调试类"""
    def __init__(self):
        self.messages = {
            'reservoir_state': [],
            'gate_actions': [],
            'control_signals': [],
            'pid_outputs': []
        }
        self.time_stamps = []
    
    def track_reservoir_state(self, time, message):
        self.messages['reservoir_state'].append((time, message))
    
    def track_gate_action(self, time, message):
        self.messages['gate_actions'].append((time, message))
    
    def track_control_signal(self, time, message):
        self.messages['control_signals'].append((time, message))
    
    def track_pid_output(self, time, output):
        self.messages['pid_outputs'].append((time, output))

def run_simulation_with_tracking():
    """运行带有消息跟踪的仿真"""
    print("=== 运行带跟踪的仿真 ===")
    
    # 创建消息跟踪器
    tracker = DebugMessageTracker()
    
    # 1. 仿真设置
    simulation_config = {'duration': 100, 'dt': 1.0}  # 较短的仿真时间用于调试
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. 通信主题
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"

    # 3. 物理组件
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 21e6, 'water_level': 14.0},
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]}
    )
    
    gate_params = {
        'max_rate_of_change': 0.5,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 1.0
    }
    
    # 创建带有跟踪功能的闸门
    class TrackedGate(Gate):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tracker = tracker
            
        def handle_control_signal(self, message):
            print(f"[DEBUG] 闸门接收到控制信号: {message}")
            tracker.track_gate_action(harness.t, message)
            super().handle_control_signal(message)
    
    gate = TrackedGate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. 智能体组件
    # 数字孪生智能体
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # PID控制器
    class TrackedPIDController(PIDController):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tracker = tracker
            
        def update(self, measurement, dt):
            output = super().update(measurement, dt)
            print(f"[DEBUG] PID输出: {output:.4f} (测量值: {measurement:.2f}, 设定值: {self.setpoint:.2f})")
            tracker.track_pid_output(harness.t, output)
            return output
    
    pid_controller = TrackedPIDController(
        Kp=10.0, Ki=1.0, Kd=0.0,
        setpoint=12.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )

    # 本地控制智能体
    class TrackedLocalControlAgent(LocalControlAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.tracker = tracker
            
        def handle_observation(self, message):
            print(f"[DEBUG] 控制智能体接收到观测值: {message}")
            tracker.track_reservoir_state(harness.t, message)
            super().handle_observation(message)
            
        def publish_action(self, control_signal):
            print(f"[DEBUG] 控制智能体发布动作: {control_signal}")
            tracker.track_control_signal(harness.t, control_signal)
            super().publish_action(control_signal)
    
    control_agent = TrackedLocalControlAgent(
        agent_id="control_agent_gate_1",
        message_bus=message_bus,
        dt=harness.dt,
        target_component="gate_1",
        control_type="gate_control",
        data_sources={"primary_data": RESERVOIR_STATE_TOPIC},
        control_targets={"primary_target": GATE_ACTION_TOPIC},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC
    )

    # 5. 仿真框架设置
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)
    harness.add_connection("reservoir_1", "gate_1")
    harness.build()

    # 6. 运行仿真
    print("\n=== 开始仿真 ===")
    harness.run_mas_simulation()
    print("\n=== 仿真完成 ===")

    return harness, tracker

def plot_control_process(harness, tracker):
    """绘制控制过程图"""
    print("\n=== 绘制控制过程图 ===")
    
    # 提取仿真数据
    times = [step['time'] for step in harness.history]
    water_levels = [step['reservoir_1']['water_level'] for step in harness.history if 'reservoir_1' in step]
    gate_openings = [step['gate_1']['opening'] for step in harness.history if 'gate_1' in step]
    
    # 提取跟踪数据
    reservoir_states = tracker.messages['reservoir_state']
    gate_actions = tracker.messages['gate_actions']
    control_signals = tracker.messages['control_signals']
    pid_outputs = tracker.messages['pid_outputs']
    
    # 创建图表
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('水位控制系统过程分析', fontsize=16, fontproperties='SimHei')
    
    # 1. 水位变化图
    ax1 = axes[0]
    ax1.plot(times, water_levels, 'b-', linewidth=2, label='实际水位')
    ax1.axhline(y=12.0, color='r', linestyle='--', linewidth=2, label='目标水位')
    ax1.set_ylabel('水位 (m)', fontsize=12)
    ax1.set_title('水位变化过程', fontsize=14, fontproperties='SimHei')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 闸门开度变化图
    ax2 = axes[1]
    ax2.plot(times, gate_openings, 'g-', linewidth=2, label='闸门开度')
    ax2.set_ylabel('闸门开度', fontsize=12)
    ax2.set_title('闸门开度变化过程', fontsize=14, fontproperties='SimHei')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 控制信号和PID输出图
    ax3 = axes[2]
    if pid_outputs:
        pid_times = [t for t, _ in pid_outputs]
        pid_values = [v for _, v in pid_outputs]
        ax3.plot(pid_times, pid_values, 'r-', linewidth=2, label='PID输出')
    
    if control_signals:
        signal_times = [t for t, _ in control_signals]
        signal_values = [v if isinstance(v, (int, float)) else v.get('control_signal', 0) for _, v in control_signals]
        ax3.plot(signal_times, signal_values, 'orange', marker='o', linestyle='', label='控制信号')
    
    ax3.set_xlabel('时间 (s)', fontsize=12)
    ax3.set_ylabel('控制信号', fontsize=12)
    ax3.set_title('控制信号分析', fontsize=14, fontproperties='SimHei')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'control_process_analysis_{timestamp}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"控制过程图已保存为: {filename}")
    
    # 显示图表
    plt.show()
    
    return filename

def print_debug_analysis(tracker):
    """打印调试分析结果"""
    print("\n=== 调试分析结果 ===")
    
    print(f"水库状态消息数量: {len(tracker.messages['reservoir_state'])}")
    print(f"闸门动作消息数量: {len(tracker.messages['gate_actions'])}")
    print(f"控制信号消息数量: {len(tracker.messages['control_signals'])}")
    print(f"PID输出记录数量: {len(tracker.messages['pid_outputs'])}")
    
    # 显示前几条消息
    if tracker.messages['reservoir_state']:
        print("\n前3条水库状态消息:")
        for i, (t, msg) in enumerate(tracker.messages['reservoir_state'][:3]):
            print(f"  t={t:.1f}s: {msg}")
    
    if tracker.messages['control_signals']:
        print("\n前3条控制信号消息:")
        for i, (t, msg) in enumerate(tracker.messages['control_signals'][:3]):
            print(f"  t={t:.1f}s: {msg}")
    
    if tracker.messages['gate_actions']:
        print("\n前3条闸门动作消息:")
        for i, (t, msg) in enumerate(tracker.messages['gate_actions'][:3]):
            print(f"  t={t:.1f}s: {msg}")
    
    if tracker.messages['pid_outputs']:
        print("\n前3个PID输出:")
        for i, (t, output) in enumerate(tracker.messages['pid_outputs'][:3]):
            print(f"  t={t:.1f}s: {output:.4f}")

def main():
    """主函数"""
    try:
        # 运行仿真
        harness, tracker = run_simulation_with_tracking()
        
        # 打印调试分析
        print_debug_analysis(tracker)
        
        # 绘制控制过程图
        plot_filename = plot_control_process(harness, tracker)
        
        print(f"\n=== 分析完成 ===")
        print(f"控制过程图已保存为: {plot_filename}")
        
    except Exception as e:
        print(f"仿真过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
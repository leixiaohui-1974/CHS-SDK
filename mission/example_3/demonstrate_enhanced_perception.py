#-*- coding: utf-8 -*-
"""
演示脚本：展示增强后的感知智能体的认知能力。
(简化版，不使用SimulationHarness)
"""
import sys
import os
import numpy as np

# 调整路径以导入核心库
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.local_agents.perception.reservoir_perception_agent import ReservoirPerceptionAgent

# --- 1. 监控器设置 ---
def create_monitor(message_bus: MessageBus, topic: str):
    """一个简单的函数，用于监控并打印我们感兴趣的消息。"""
    print(f"\n--- 监控器正在监听主题: {topic} ---")
    def monitor_callback(message):
        is_anomaly = message.get('is_anomaly', False)
        warning = message.get('warning_message')
        time = message.get('time', 'N/A')

        if is_anomaly or warning:
            print(f"[监控器] 在时间 {time} 收到一条值得关注的消息:")
            # 检查water_level是否存在且不为None
            water_level = message.get('water_level')
            if water_level is not None:
                print(f"  > 水位: {water_level:.2f}")
            else:
                print(f"  > 水位: N/A")

            if is_anomaly:
                print("  > 检测到异常!")
            if warning:
                print(f"  > {warning}")
            print("-" * 20)

    message_bus.subscribe(topic, monitor_callback)

# --- 2. 仿真设置 ---
def run_demonstration():
    """设置并运行仿真，以演示增强的感知能力。"""
    print("--- 正在设置仿真 ---")
    bus = MessageBus()

    # 创建一个物理水库模型
    initial_state = {'water_level': 10.0, 'volume': 1000.0}
    parameters = {'area': 100.0}
    reservoir = Reservoir(
        name='演示水库',
        initial_state=initial_state,
        parameters=parameters
    )

    # 为我们的新认知功能定义配置
    cognitive_config = {
        'history_size': 20,
        'target_variables': ['water_level'],
        'anomaly_detection': {
            'contamination': 0.1
        },
        'predictive_warning': {
            'trend_window': 3,
            'thresholds': {
                'water_level': -5.0
            }
        }
    }

    # 创建感知智能体，并传入认知配置
    perception_agent = ReservoirPerceptionAgent(
        agent_id='res_perceiver_1',
        reservoir_model=reservoir,
        message_bus=bus,
        state_topic='perception/reservoir/state',
        cognitive_config=cognitive_config
    )

    # 设置监控器以监听智能体的输出
    create_monitor(bus, 'perception/reservoir/state')

    # --- 3. 运行带有故障注入的仿真 ---
    print("\n--- 开始运行仿真 ---")
    for t in range(20):
        print(f"--- 时间步 {t} ---")

        current_state = reservoir.get_state()

        # 在调用agent.run()之前操纵状态
        if t == 5:
            print(">>> 注入传感器故障 (None 值) <<<")
            # 直接修改模型的内部状态来模拟传感器故障
            reservoir._state['water_level'] = None
        elif t == 10:
            print(">>> 模拟水位快速下降 <<<")
            reservoir.set_state({'water_level': 8.0, 'volume': 800.0})
        elif t == 11:
            reservoir.set_state({'water_level': 2.0, 'volume': 200.0}) # 这将触发预警
        else:
            # 正常操作：水位轻微下降
            if current_state.get('water_level') is not None:
                new_level = current_state['water_level'] - 0.5
                new_volume = reservoir._get_volume_from_level(new_level)
                reservoir.set_state({'water_level': new_level, 'volume': new_volume})

        # 直接调用智能体的run方法
        perception_agent.run(current_time=float(t))

    print("\n--- 仿真结束 ---")

if __name__ == "__main__":
    run_demonstration()

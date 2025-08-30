# -*- coding: utf-8 -*-
import sys
import os

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from core_lib.local_agents.control.pid_controller import PIDController

class JointControlCoordinatorAgent(Agent):
    """
    一个联合控制协调智能体。
    它根据水位误差，计算一个总的净流量需求，然后将其分配给
    一个进水泵和一个出水阀来共同执行。
    """
    def __init__(self, agent_id: str, message_bus: MessageBus, config: dict):
        super().__init__(agent_id)
        self.bus = message_bus
        pid_conf = config['pid_params']
        actuator_conf = config['actuator_limits']
        msg_conf = config['messaging_params']

        self.pid_controller = PIDController(
            Kp=pid_conf['Kp'], Ki=pid_conf['Ki'], Kd=pid_conf['Kd'],
            setpoint=pid_conf['setpoint'],
            min_output=pid_conf['min_output'],
            max_output=pid_conf['max_output']
        )

        self.max_inflow = actuator_conf['max_inflow']
        self.max_outflow = actuator_conf['max_outflow']

        self.state_topic = msg_conf['state_topic']
        self.pump_topic = msg_conf['pump_command_topic']
        self.valve_topic = msg_conf['valve_command_topic']

        self.bus.subscribe(self.state_topic, self.handle_state_message)
        print(f"JointControlCoordinatorAgent '{self.agent_id}' created and subscribed to state topic '{self.state_topic}'.")

    def handle_state_message(self, message: Message):
        """当收到新的水位状态时，执行控制逻辑。"""
        water_level = message.get('water_level')
        if water_level is None:
            return

        # 1. PID控制器计算一个总体的“净流量”调整值
        # 如果水位低，error为正，net_flow_demand为正（需要更多水进来）
        # 如果水位高，error为负，net_flow_demand为负（需要更多水出去）
        observation = {'process_variable': water_level}
        net_flow_demand = self.pid_controller.compute_control_action(observation, dt=1.0) # dt is used by derivative

        # 2. 将净流量需求分配给水泵和水阀
        # 这是一个简化的分配策略：
        # - 如果需要净流入，优先开大水泵，关小水阀
        # - 如果需要净流出，优先开大水阀，关小水泵

        pump_inflow = 0
        valve_outflow = 0

        if net_flow_demand > 0: # 需要水
            pump_inflow = net_flow_demand
            valve_outflow = 0
        else: # 需要排水
            pump_inflow = 0
            valve_outflow = -net_flow_demand # demand is negative, so outflow is positive

        # 3. 限制执行器的输出在物理范围内
        pump_inflow = max(0, min(pump_inflow, self.max_inflow))
        valve_outflow = max(0, min(valve_outflow, self.max_outflow))

        # 4. 发布控制指令
        self.bus.publish(self.pump_topic, {'control_signal': pump_inflow})
        self.bus.publish(self.valve_topic, {'control_signal': valve_outflow})

    def run(self, **kwargs):
        # 这个智能体是事件驱动的，所以run方法是空的
        pass

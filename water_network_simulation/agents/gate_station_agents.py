import time
from .base_agent import BaseAgent
from communication.pubsub_broker import PubSubBroker
from models.pid_controller import PIDController

# Role 1: Perception Agent (The Digital Twin)
class GateStationPerceptionAgent(BaseAgent):
    """
    3a. 闸站感知智能体
    负责“感知”和“认知”，是闸站的数字孪生。
    """
    def __init__(self, agent_id: str, broker: PubSubBroker, gate_id: str):
        super().__init__(agent_id, broker)
        self.gate_id = gate_id

        # 状态
        self.actual_opening = None
        self.upstream_level = None
        self.downstream_level = None

        # 孪生成果：过流特性模型
        self.flow_coefficient = 20.0  # 初始估计值

        # 订阅
        self.broker.subscribe("gate_executor_status", self._handle_executor_status)
        self.broker.subscribe("channel_clean_data", self._handle_channel_data) # Assuming it gets downstream level from channel
        self.broker.subscribe("raw_sensor_data", lambda msg: setattr(self, 'upstream_level', msg.get('upstream_level'))) # And upstream from raw data for head diff

    def _handle_executor_status(self, message):
        self.actual_opening = message.get('actual_opening')

    def _handle_channel_data(self, message):
        self.downstream_level = message.get('downstream_level')

    def run_step(self, time_step: int):
        # 在这个简化版本中，感知智能体主要负责监听和未来可能的模型辨识
        # 真正的辨识需要流量数据，这里我们假设它在后台进行
        # 此处仅做数据汇集和状态发布
        if all([self.actual_opening is not None, self.upstream_level is not None, self.downstream_level is not None]):
            # 发布孪生成果 (即使它在这个仿真中没有被积极使用)
            twin_data = {
                'timestamp': time.time(),
                'gate_id': self.gate_id,
                'model_type': 'flow_coefficient',
                'parameters': {'C_d': self.flow_coefficient}
            }
            self.broker.publish("gate_twin_model", twin_data)

        # For this simulation, this agent is more of a pass-through and placeholder for real-world identification logic.
        # No console output needed to keep the main output clean.

# Role 2: Control Agent (The Brain)
class GateStationControlAgent(BaseAgent):
    """
    3b. 闸站控制智能体
    负责“决策”和“行动”，是闸站的“大脑”。
    """
    def __init__(self, agent_id: str, broker: PubSubBroker, gate_id: str, pid_params: dict):
        super().__init__(agent_id, broker)
        self.gate_id = gate_id

        # 控制器
        self.pid = PIDController(Kp=pid_params['Kp'], Ki=pid_params['Ki'], Kd=pid_params['Kd'])

        # 状态
        self.current_downstream_level = None
        self.control_target_level = None # 由中心调度器设置

        # 订阅
        self.broker.subscribe("channel_clean_data", self._handle_channel_data)
        self.broker.subscribe("control_goals", self._handle_control_goal)

    def _handle_channel_data(self, message):
        self.current_downstream_level = message.get('downstream_level')

    def _handle_control_goal(self, message):
        # 仅处理发给自己的指令
        if message.get('target_id') == self.gate_id:
            new_setpoint = message.get('target_level')
            if new_setpoint is not None and new_setpoint != self.control_target_level:
                self.control_target_level = new_setpoint
                self.pid.set_setpoint(self.control_target_level)
                print(f"\nGATE CONTROL ({self.agent_id}): Received new control target level: {self.control_target_level}m\n")


    def run_step(self, time_step: int):
        if self.current_downstream_level is None or self.control_target_level is None:
            # 如果没有目标或当前状态，则不执行控制
            return

        # --- 1. 指令生成 ---
        # 使用PID控制器计算控制输出。输出是一个修正值。
        pid_output = self.pid.update(self.current_downstream_level)

        # --- 2. 指令转换 ---
        # 将PID输出转换为闸门开度指令。
        # 这是一个简化的逻辑：如果水位低，增加开度；如果水位高，减小开度。
        # 注意：这是一个反向作用系统，水位高需要减小开度（减少入流）
        # 因此我们将 PID 输出反向应用
        current_opening_guess = 0.5 # A baseline opening
        target_opening = current_opening_guess - pid_output

        # 限制开度在合理范围 [0, 1]
        target_opening = max(0, min(1, target_opening))

        # --- 3. 输出控制指令 ---
        control_command = {
            'timestamp': time.time(),
            'gate_id': self.gate_id,
            'target_opening': target_opening
        }
        self.broker.publish("gate_control_command", control_command)

        if time_step % 10 == 0:
            print(f"--- Step {time_step}: GATE CONTROL ({self.agent_id}) ---")
            print(f"  Target Level: {self.control_target_level}m | Current Level: {self.current_downstream_level:.3f}m | PID Output: {pid_output:.3f} -> Target Opening: {target_opening:.2%}")

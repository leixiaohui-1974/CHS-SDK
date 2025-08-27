import time
from .base_agent import BaseAgent
from communication.pubsub_broker import PubSubBroker

class CentralDispatchAgent(BaseAgent):
    """
    4. 中心调度智能体
    作为宏观“大脑”，进行跨区域、长时空尺度的战略决策。
    """
    def __init__(self, agent_id: str, broker: PubSubBroker):
        super().__init__(agent_id, broker)

        # 状态
        self.channel_twin_models = {}
        self.gate_twin_models = {}
        self.is_emergency_mode = False
        self.default_target_level = 4.5 # m, 默认的目标水位
        self.emergency_target_level = 4.3 # m, 应急情况下的目标水位

        # 订阅
        self.broker.subscribe("channel_twin_model", self._handle_channel_twin)
        self.broker.subscribe("gate_twin_model", self._handle_gate_twin)
        self.broker.subscribe("anomaly_reports", self._handle_anomaly)

    def _handle_channel_twin(self, message):
        self.channel_twin_models[message['channel_id']] = message['parameters']

    def _handle_gate_twin(self, message):
        self.gate_twin_models[message['gate_id']] = message['parameters']

    def _handle_anomaly(self, message):
        """快思考：处理异常报告"""
        if not self.is_emergency_mode:
            print(f"\n!!! CENTRAL DISPATCH ({self.agent_id}): EMERGENCY! Received anomaly report: {message['message']}!!!")
            print(f"    Overriding regular schedule. Setting emergency target level to {self.emergency_target_level}m.\n")
            self.is_emergency_mode = True
            # 立即发布应急指令
            self.publish_control_goal(self.emergency_target_level, "gate_1")

    def publish_control_goal(self, target_level, target_id):
        """发布控制目标到总线"""
        goal = {
            'timestamp': time.time(),
            'source': self.agent_id,
            'target_id': target_id, # 'gate_1'
            'target_level': target_level
        }
        self.broker.publish("control_goals", goal)

    def run_step(self, time_step: int):
        # --- 慢思考：周期性调度 ---
        # 如果不在紧急模式下，则执行常规调度
        if not self.is_emergency_mode:
            # 在第10步，发布初始的控制目标
            if time_step == 10:
                print(f"\n--- CENTRAL DISPATCH ({self.agent_id}): Issuing initial control goal. Target: {self.default_target_level}m ---\n")
                self.publish_control_goal(self.default_target_level, "gate_1")

            # 在第120步，模拟一个新的调度计划，改变目标水位
            if time_step == 120:
                new_target = 4.7
                print(f"\n--- CENTRAL DISPATCH ({self.agent_id}): New schedule. Changing target level to {new_target}m ---\n")
                self.publish_control_goal(new_target, "gate_1")

        # 退出紧急模式 (例如，在异常发生一段时间后)
        if self.is_emergency_mode and time_step > 100:
             self.is_emergency_mode = False
             print(f"\n--- CENTRAL DISPATCH ({self.agent_id}): Emergency condition resolved. Returning to normal operations. ---\n")
             self.publish_control_goal(self.default_target_level, "gate_1")

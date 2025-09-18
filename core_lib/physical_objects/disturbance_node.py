"""
A component that represents a point of water withdrawal or external inflow.
"""
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional
import numpy as np

class DisturbanceNode(PhysicalObjectInterface):
    """
    A simple node that allows for the withdrawal (or addition) of water.

    This component is designed to be controlled by a disturbance agent via the
    message bus. It receives an inflow from an upstream component and passes a
    modified outflow downstream.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, action_topic: Optional[str] = None,
                 action_key: str = 'outflow'):
        super().__init__(name, initial_state, parameters)
        self._diversion_flow = initial_state.get('outflow', 0.0)  # 存储分流量在属性中
        self._state['outflow'] = 0.0  # outflow字段用于存储通过流量
        self._state['passthrough_flow'] = 0.0
        self.bus = message_bus
        self.action_topic = action_topic
        self.action_key = action_key

        if self.bus and self.action_topic:
            self.bus.subscribe(self.action_topic, self.handle_action_message)
            print(f"DisturbanceNode '{self.name}' subscribed to action topic '{self.action_topic}'.")

    def handle_action_message(self, message: Message):
        """Callback to handle incoming action messages from the bus."""
        if self.action_key in message:
            new_value = message.get(self.action_key)
            if new_value is not None:
                self._diversion_flow = float(new_value)

    def step(self, action: any, time_step: float) -> State:
        """
        Updates the node's state. The primary control is via the message bus,
        but this can also handle direct actions if needed.
        """
        # 调试信息：查看Diversion_1接收到的action内容
        if hasattr(self, 'name') and self.name == 'Diversion_1':
            print(f"\n=== Diversion_1 调试信息 ===")
            print(f"接收到的action: {action}")
            print(f"当前入流 _inflow: {getattr(self, '_inflow', 'None')}")
            print(f"当前状态 outflow: {self._state.get('outflow', 'None')}")
            print(f"action_key: {self.action_key}")
            print(f"action中是否包含{self.action_key}: {self.action_key in action if isinstance(action, dict) else False}")
        
        # Direct action can override message bus for testing/simplicity
        if isinstance(action, dict) and self.action_key in action:
            old_outflow = getattr(self, '_diversion_flow', 0.0)
            self._diversion_flow = float(action[self.action_key])
            if hasattr(self, 'name') and self.name == 'Diversion_1':
                print(f"通过action设置分流量: {old_outflow} -> {self._diversion_flow}")

        # 计算通过流量：使用存储的分流量而不是当前的outflow
        diversion_flow = getattr(self, '_diversion_flow', 0.0)  # 从属性中获取分流量
        passthrough_flow = max(0, self._inflow - diversion_flow)
        self._state['passthrough_flow'] = passthrough_flow
        
        # 更新状态：存储分流量和通过流量
        self._state['diversion_flow'] = diversion_flow
        self._state['outflow'] = passthrough_flow  # outflow字段存储实际输出给下游的流量
        
        if hasattr(self, 'name') and self.name == 'Diversion_1':
            print(f"Diversion_1 -> 入流: {getattr(self, '_inflow', 0):.3f}, 分流: {diversion_flow:.3f}, 通过: {passthrough_flow:.3f}")

        return self.get_state()

    @property
    def outflow(self):
        """The outflow passed to the next component in the network."""
        # 返回实际输出给下游的流量（现在存储在outflow字段中）
        return self._state.get('outflow', 0.0)

    def set_inflow(self, inflow: float):
        """Sets the inflow for the current time step. Called by the harness."""
        self._inflow = inflow
        self._state['inflow'] = inflow

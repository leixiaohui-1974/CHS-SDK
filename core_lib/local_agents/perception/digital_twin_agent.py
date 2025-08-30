"""
用于状态同步、增强和发布的数字孪生智能体。
"""
from core_lib.core.interfaces import Agent, Simulatable, State
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Optional, Dict, Any

class DigitalTwinAgent(Agent):
    """
    一个感知智能体，作为物理对象的数字孪生。

    其主要职责是维护一个内部仿真模型，并将其状态发布到消息总线。
    它还可以对原始状态执行“认知”增强，例如平滑噪声数据。
    """

    def __init__(self,
                 agent_id: str,
                 simulated_object: Simulatable,
                 message_bus: MessageBus,
                 state_topic: str,
                 smoothing_config: Optional[Dict[str, float]] = None,
                 **kwargs):
        """
        初始化 DigitalTwinAgent。

        Args:
            agent_id: 该智能体的唯一ID。
            simulated_object: 该智能体所孪生的仿真模型。
            message_bus: 用于通信的系统消息总线。
            state_topic: 用于发布对象状态的主题。
            smoothing_config: (可选) 应用指数移动平均（EMA）平滑的配置。
                示例: {'water_level': 0.3, 'outflow': 0.5}
                值是alpha（平滑因子）。
        """
        super().__init__(agent_id)
        self.model = simulated_object
        self.bus = message_bus
        self.state_topic = state_topic
        self.smoothing_config = smoothing_config
        self.smoothed_states: Dict[str, float] = {}

        model_id = self.model.name
        print(f"DigitalTwinAgent '{self.agent_id}' 已为模型 '{model_id}' 创建。将向主题 '{self.state_topic}' 发布状态。")
        if self.smoothing_config:
            print(f"  - 已为以下键启用平滑处理: {list(self.smoothing_config.keys())}")

    def _apply_smoothing(self, state: State) -> State:
        """对配置的状态变量应用指数移动平均（EMA）平滑。"""
        if not self.smoothing_config:
            return state

        smoothed_state = state.copy()
        for key, alpha in self.smoothing_config.items():
            if key in smoothed_state:
                raw_value = smoothed_state[key]
                last_smoothed = self.smoothed_states.get(key, raw_value) # 用第一个原始值进行初始化
                new_smoothed = alpha * raw_value + (1 - alpha) * last_smoothed
                smoothed_state[key] = new_smoothed
                self.smoothed_states[key] = new_smoothed
        return smoothed_state

    def publish_state(self):
        """
        获取当前状态，应用增强功能，并为每个状态变量在其自己的子主题上发布。
        """
        raw_state = self.model.get_state()
        enhanced_state = self._apply_smoothing(raw_state)

        # 将完整的状态字典发布到基础主题
        self.bus.publish(self.state_topic, enhanced_state)

        # 同时，将每个键值对发布到其自己的子主题
        # 这允许像ParameterIdentificationAgent这样的智能体只订阅它们需要的数据，
        # 并使用它们期望的简单 {'value': ...} 格式。
        for key, value in enhanced_state.items():
            if isinstance(value, (int, float)):
                sub_topic = f"{self.state_topic}/{key}"
                message: Message = {'value': value}
                self.bus.publish(sub_topic, message)

    def run(self, current_time: float):
        """
        智能体的主要执行逻辑。

        在仿真环境中，此方法在每个时间步由仿真平台调用，
        以使智能体发布其当前状态。

        Args:
            current_time: 当前仿真时间（该智能体忽略此参数）。
        """
        # print(f"  [Debug DTA] Agent '{self.agent_id}' running at time {current_time}.")
        self.publish_state()

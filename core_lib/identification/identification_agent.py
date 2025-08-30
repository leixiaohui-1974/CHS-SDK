"""
一个负责协调参数辨识过程的智能体。
"""
from core_lib.core.interfaces import Agent, Identifiable
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, List

class ParameterIdentificationAgent(Agent):
    """
    一个收集仿真和观测数据，并为一个目标模型触发参数辨识过程的智能体。
    """

    def __init__(self, agent_id: str, target_model: Identifiable,
                 message_bus: MessageBus, config: Dict[str, Any]):
        """
        初始化 ParameterIdentificationAgent。

        Args:
            agent_id: 该智能体的唯一ID。
            target_model: 需要被辨识参数的模型实例。
            message_bus: 系统的消息总线。
            config: 一个包含智能体配置的字典：
                - identification_interval: 在运行一次辨识前需要收集的数据点数量。
                - identification_data_map: 一个字典，将模型的 identify_parameters 方法所需的
                                           键（例如 'rainfall', 'observed_runoff'）映射到
                                           它们对应的主题。
        """
        super().__init__(agent_id)
        self.target_model = target_model
        self.bus = message_bus

        # 配置
        self.id_interval = config.get("identification_interval", 100)
        self.data_map = config["identification_data_map"]

        # 内部状态
        self.data_history: Dict[str, List[float]] = {key: [] for key in self.data_map.keys()}
        self.new_data_count = 0

        # 订阅所有必需的数据主题
        for model_key, topic in self.data_map.items():
            # lambda 表达式捕获了每次循环的 'model_key' 以供处理函数使用
            self.bus.subscribe(topic, lambda msg, key=model_key: self.handle_data_message(msg, key))
            print(f"[{self.agent_id}] 已订阅主题 '{topic}' 用于数据键 '{model_key}'.")

    def handle_data_message(self, message: Message, model_key: str):
        """用于存储传入数据的回调函数。"""
        value = message.get("value") # 假设是一个简单的 {'value': ...} 格式的消息
        if isinstance(value, (int, float)):
            self.data_history[model_key].append(value)
            # 仅对一个数据流递增计数器，以确保同步
            if model_key == list(self.data_map.keys())[0]:
                self.new_data_count += 1

    def run(self, current_time: float):
        """
        检查是否已收集足够的数据，并触发辨识过程。
        """
        if self.new_data_count >= self.id_interval:
            print(f"  [{current_time}s] [{self.agent_id}] 已收集 {self.new_data_count} 个新数据点。正在触发参数辨识。")

            # 为模型准备数据
            # 模型的 identify_parameters 方法期望接收 numpy 数组
            import numpy as np

            # 为防止索引错误，找到所有数据流中的最小长度
            min_len = min(len(v) for v in self.data_history.values())
            if min_len < 1:
                print(f"  [{current_time}s] [{self.agent_id}] 没有足够的数据运行辨识 (min_len={min_len})。跳过。")
                return

            # 将所有数据流截断到最小长度
            data_for_model = {key: np.array(values[:min_len]) for key, values in self.data_history.items()}

            # 触发辨识并获取结果
            new_params = self.target_model.identify_parameters(data_for_model)

            # 发布新参数以供 ModelUpdaterAgent 使用
            if new_params:
                message = {
                    "model_name": self.target_model.name,
                    "parameters": new_params
                }
                publish_topic = f"identified_parameters/{self.target_model.name}"
                self.bus.publish(publish_topic, message)
                print(f"  [{current_time}s] [{self.agent_id}] 已为 '{self.target_model.name}' 在主题 '{publish_topic}' 上发布新参数。")

            # 为下一批次重置
            self.clear_history()

    def clear_history(self):
        """清除收集的数据历史。"""
        self.data_history = {key: [] for key in self.data_map.keys()}
        self.new_data_count = 0
        print(f"  [{self.agent_id}] 数据历史已清除。准备好进入下一个辨识周期。")

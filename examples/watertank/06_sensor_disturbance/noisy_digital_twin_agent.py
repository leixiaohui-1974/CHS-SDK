# -*- coding: utf-8 -*-
import sys
import os
import random

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core.interfaces import State

class NoisyDigitalTwinAgent(DigitalTwinAgent):
    """
    一个特殊的数字孪生智能体，它在发布状态前会为水位数据添加噪声，
    用以模拟不精确的传感器。
    """
    def __init__(self, noise_params: dict, **kwargs):
        """
        初始化智能体。

        Args:
            noise_params (dict): 包含噪声参数（如 'mean', 'std_dev'）的字典。
            **kwargs: 传递给 DigitalTwinAgent 基类的参数。
        """
        super().__init__(**kwargs)
        self.noise_mean = noise_params.get('mean', 0.0)
        self.noise_std_dev = noise_params.get('std_dev', 0.0)
        self.last_noisy_level = 0.0 # For logging
        print(f"NoisyDigitalTwinAgent '{self.agent_id}' initialized with noise(mean={self.noise_mean}, std_dev={self.noise_std_dev}).")

    def publish_state(self):
        """
        重写 publish_state 方法。
        获取真实状态，添加噪声，然后发布带有噪声的状态。
        """
        raw_state = self.model.get_state()
        noisy_state = raw_state.copy()

        true_level = noisy_state.get('water_level', 0.0)
        noise = random.gauss(self.noise_mean, self.noise_std_dev)
        noisy_level = true_level + noise

        # 更新消息中的水位为带噪声的值
        noisy_state['water_level'] = noisy_level
        self.last_noisy_level = noisy_level # Store for logging

        # 调用基类的平滑方法（如果配置了）
        enhanced_state = self._apply_smoothing(noisy_state)

        self.bus.publish(self.state_topic, enhanced_state)

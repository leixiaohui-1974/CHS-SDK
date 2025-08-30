# -*- coding: utf-8 -*-
import sys
import os
import random

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from core_lib.physical_objects.reservoir import Reservoir

class NoisyActuatorReservoir(Reservoir):
    """
    一个特殊的 Reservoir 模型，它的执行器（入流口）是不精确的。
    它在接收到入流指令时，会引入系统性的偏差和随机噪声。
    """
    def __init__(self, noise_params: dict, **kwargs):
        """
        初始化。

        Args:
            noise_params (dict): 包含 'bias' 和 'std_dev' 的字典。
            **kwargs: 传递给 Reservoir 基类的参数。
        """
        super().__init__(**kwargs)
        self.bias = noise_params.get('bias', 1.0) # e.g., 0.95 means it only delivers 95% of command
        self.std_dev = noise_params.get('std_dev', 0.0)
        self.actual_inflow = 0.0 # For logging
        print(f"NoisyActuatorReservoir '{self.name}' initialized with actuator noise (bias={self.bias}, std_dev={self.std_dev}).")

    def set_inflow(self, commanded_inflow: float):
        """
        重写 set_inflow 方法以模拟不精确的执行器。
        """
        noise = random.gauss(0, self.std_dev)
        # Apply bias and noise
        self.actual_inflow = (commanded_inflow * self.bias) + noise
        # Ensure physical constraints (e.g., no negative flow)
        if self.actual_inflow < 0:
            self.actual_inflow = 0

        # Call the parent's set_inflow with the 'actual' noisy value
        super().set_inflow(self.actual_inflow)

    def get_state(self):
        """
        重写 get_state 以包含实际入流，方便记录。
        """
        state = super().get_state()
        state['actual_inflow'] = self.actual_inflow
        return state

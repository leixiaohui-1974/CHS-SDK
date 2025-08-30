# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    智能体的抽象基类。
    所有具体的智能体都应继承自该类。
    """
    def __init__(self, agent_id, config):
        """
        初始化智能体。

        :param agent_id: 智能体的唯一标识符。
        :param config: 包含智能体配置的字典。
        """
        self.agent_id = agent_id
        self.config = config

    @abstractmethod
    def step(self, observation):
        """
        智能体执行一步操作。

        :param observation: 从环境中接收到的观察值。
        :return: 智能体产生的动作或状态。
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        获取智能体的当前状态。

        :return: 智能体的当前状态。
        """
        pass

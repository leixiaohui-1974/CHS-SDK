from abc import ABC, abstractmethod
from communication.pubsub_broker import PubSubBroker

class BaseAgent(ABC):
    """
    所有智能体的抽象基类。
    定义了所有智能体必须具备的通用接口。
    """
    def __init__(self, agent_id: str, broker: PubSubBroker):
        self.agent_id = agent_id
        self.broker = broker
        print(f"Agent {self.agent_id}: Initialized.")

    @abstractmethod
    def run_step(self, time_step: int):
        """
        每个智能体在仿真循环的每一步中执行的核心逻辑。
        """
        pass

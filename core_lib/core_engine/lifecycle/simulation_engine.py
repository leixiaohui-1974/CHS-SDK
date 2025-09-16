from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SimulationResult:
    success: bool
    history: List[Dict[str, Any]]
    start_time: float
    end_time: float
    time_step: float
    metadata: Optional[Dict[str, Any]] = None


class SimulationEngine(ABC):
    """
    抽象仿真引擎接口，定义统一扩展点：
    - configure: 注入配置与依赖
    - initialize: 构建模型与拓扑
    - step: 单步推进
    - run: 主循环
    - finalize: 收尾与结果封装
    """

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def step(self, current_time: float, time_step: float) -> None:
        pass

    @abstractmethod
    def run(self) -> SimulationResult:
        pass

    @abstractmethod
    def finalize(self) -> None:
        pass



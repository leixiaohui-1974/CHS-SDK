from __future__ import annotations

from typing import Any, Dict, List

from core_lib.core_engine.lifecycle.simulation_engine import SimulationEngine, SimulationResult
from core_lib.core_engine.testing.simulation_harness import SimulationHarness


class BasicSimulationEngine(SimulationEngine):
    """
    一个最小可用的仿真引擎实现：
    - 使用现有 SimulationHarness 作为后端执行器
    - 明确返回结构化 SimulationResult，而非随意的原始数据
    - 对外暴露清晰扩展点
    """

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._harness: SimulationHarness | None = None
        self._history: List[Dict[str, Any]] = []

    def configure(self, config: Dict[str, Any]) -> None:
        self._config = dict(config)

    def initialize(self) -> None:
        if 'start_time' not in self._config or 'end_time' not in self._config:
            raise ValueError("Missing required 'start_time' or 'end_time' in config")
        if 'time_step' not in self._config:
            raise ValueError("Missing required 'time_step' in config")
        self._harness = SimulationHarness({
            'start_time': self._config['start_time'],
            'end_time': self._config['end_time'],
            'time_step': self._config['time_step'],
        })
        # TODO: 这里可以通过配置注入组件/控制器/智能体等

    def step(self, current_time: float, time_step: float) -> None:
        # 委托给 harness 的内部步进（复用其现有逻辑）
        if self._harness is None:
            raise RuntimeError('Engine not initialized')
        # harness 的 run_simulation 自带循环，这里暂提供占位，供未来细粒度控制扩展
        pass

    def run(self) -> SimulationResult:
        if self._harness is None:
            raise RuntimeError('Engine not initialized')

        # 运行简单仿真，生成历史
        self._harness.is_running = True
        self._harness.sort_components_topologically()
        self._harness.run_simulation()
        self._history = list(self._harness.history)

        return SimulationResult(
            success=True,
            history=self._history,
            start_time=self._harness.start_time,
            end_time=self._harness.t,
            time_step=self._harness.time_step,
            metadata={'engine': 'BasicSimulationEngine'}
        )

    def finalize(self) -> None:
        # 清理或导出在此实现
        pass



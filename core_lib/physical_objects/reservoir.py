"""
水库的仿真模型。
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.central_coordination.collaboration.message_bus import MessageBus, Message
from typing import Dict, Any, Optional, List

class Reservoir(PhysicalObjectInterface):
    """
    代表水务系统中的一个基础对象：水库。
    其状态由入流和出流的水量平衡决定。
    它可以接收来自上游组件的物理入流，也可以通过消息总线接收数据驱动的入流（例如，降雨、观测数据）。
    库容和水位之间的关系由库容曲线定义。
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus: Optional[MessageBus] = None, inflow_topic: Optional[str] = None):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0) # 确保状态中有outflow键

        if 'storage_curve' not in self._params:
            raise ValueError("水库参数必须包含 'storage_curve'。")

        self._validate_and_prepare_storage_curve()

        self.bus = message_bus
        # 为了灵活性，从构造函数参数或parameters字典中获取入流主题
        self.inflow_topic = inflow_topic or self._params.get('inflow_topic')
        self.data_inflow = 0.0

        if self.bus and self.inflow_topic:
            self.bus.subscribe(self.inflow_topic, self.handle_inflow_message)
            print(f"水库 '{self.name}' 已订阅数据入流主题 '{self.inflow_topic}'.")

        print(f"水库 '{self.name}' 已创建，初始状态为 {self._state}.")

    def _validate_and_prepare_storage_curve(self):
        """验证库容曲线并为其准备插值计算。"""
        curve = self._params['storage_curve']
        if not isinstance(curve, list) or len(curve) < 2 or not all(isinstance(p, (list, tuple)) and len(p) == 2 for p in curve):
            raise ValueError("'storage_curve' 必须是一个由 [库容, 水位] 对组成的列表。")

        # 确保它是一个numpy数组，并按库容排序以便于插值
        self.storage_curve_np = np.array(sorted(curve, key=lambda p: p[0]))
        self._volumes = self.storage_curve_np[:, 0]
        self._levels = self.storage_curve_np[:, 1]

        if not np.all(np.diff(self._volumes) > 0):
            raise ValueError("'storage_curve' 中的库容值必须是严格递增的。")

    def _get_level_from_volume(self, volume: float) -> float:
        """使用库容曲线通过库容插值计算水位。"""
        return np.interp(volume, self._volumes, self._levels)

    def _get_volume_from_level(self, level: float) -> float:
        """使用库容曲线通过水位插值计算库容。"""
        return np.interp(level, self._levels, self._volumes)

    def set_parameters(self, parameters: Parameters):
        """重写该方法，以便在参数更新时重新验证库容曲线。"""
        super().set_parameters(parameters)
        if 'storage_curve' in parameters:
            self._validate_and_prepare_storage_curve()

    def handle_inflow_message(self, message: Message):
        """处理数据驱动入流消息的回调函数。"""
        inflow_value = message.get('control_signal') or message.get('inflow_rate')
        if isinstance(inflow_value, (int, float)):
            self.data_inflow += inflow_value

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """模拟水库在单个时间步内的状态变化。"""
        physical_inflow = self._inflow
        total_inflow = physical_inflow + self.data_inflow
        outflow = action.get('outflow', 0)

        current_volume = self._state.get('volume', 0)

        delta_volume = (total_inflow - outflow) * dt
        new_volume = max(0, current_volume + delta_volume)

        self._state['volume'] = new_volume
        self._state['water_level'] = self._get_level_from_volume(new_volume)
        self._state['outflow'] = outflow
        self._state['inflow'] = total_inflow # 将总入流添加到状态中，供感知智能体使用

        # 为下一个时间步重置数据驱动的入流
        self.data_inflow = 0.0

        return self._state

    @property
    def is_stateful(self) -> bool:
        return True

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline') -> Parameters:
        """
        使用历史数据辨识库容曲线参数。

        Args:
            data: 一个包含numpy数组的字典，应包含：
                  - 'inflows': 总入流的时间序列数据。
                  - 'outflows': 总出流的时间序列数据。
                  - 'levels': 观测水位的时间序列数据。
            method: 辨识方法（目前仅支持 'offline'）。

        Returns:
            一个包含新辨识出的 'storage_curve' 的字典。
        """
        if not all(k in data for k in ['inflows', 'outflows', 'levels']):
            raise ValueError("辨识数据必须包含 'inflows', 'outflows', 和 'levels'.")

        inflows = data['inflows']
        outflows = data['outflows']
        observed_levels = data['levels']

        # 假设dt是恒定的，从数据点数量推断（例如，一天的数据）。
        # 理想情况下，这个值应该由数据提供。这里我们假设步长是每小时。
        dt = 3600 # 秒

        def _simulation_error(level_params: np.ndarray) -> float:
            """优化器的目标函数。"""
            # 使用优化器当前的参数创建一个候选库容曲线
            candidate_curve = np.column_stack((self._volumes, level_params))

            # 以防万一，按库容排序，尽管我们只优化水位
            candidate_curve = candidate_curve[candidate_curve[:, 0].argsort()]
            candidate_volumes = candidate_curve[:, 0]
            candidate_levels = candidate_curve[:, 1]

            # 模拟水量平衡
            simulated_volumes = np.zeros_like(inflows)
            initial_volume = np.interp(observed_levels[0], candidate_levels, candidate_volumes)
            simulated_volumes[0] = initial_volume

            for i in range(1, len(inflows)):
                delta_v = (inflows[i-1] - outflows[i-1]) * dt
                simulated_volumes[i] = simulated_volumes[i-1] + delta_v

            # 使用候选曲线将模拟库容转换为水位
            simulated_levels = np.interp(simulated_volumes, candidate_volumes, candidate_levels)

            # 计算均方根误差 (RMSE)
            rmse = np.sqrt(np.mean((simulated_levels - observed_levels)**2))
            return rmse

        # 我们优化曲线的'level'部分，保持'volume'点固定。
        initial_guess = self._levels

        # 定义边界以防止水位变得不单调
        bounds = [(initial_guess[i-1] if i > 0 else -np.inf,
                   initial_guess[i+1] if i < len(initial_guess)-1 else np.inf)
                  for i in range(len(initial_guess))]

        result = minimize(
            _simulation_error,
            initial_guess,
            method='L-BFGS-B', # 一个支持边界的优秀拟牛顿法
            bounds=bounds
        )

        if result.success:
            new_levels = result.x
            new_storage_curve = np.column_stack((self._volumes, new_levels)).tolist()
            print(f"为 '{self.name}' 进行的参数辨识成功。")
            return {'storage_curve': new_storage_curve}
        else:
            print(f"警告: 为 '{self.name}' 进行的参数辨识失败: {result.message}")
            return {'storage_curve': self._params['storage_curve']} # 返回原始值

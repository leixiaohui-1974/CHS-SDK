"""
水库的仿真模型。
"""
import numpy as np
from scipy.optimize import minimize
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters
from core_lib.core.event_bus import get_global_event_bus
from typing import Dict, Any, Optional, List

class Reservoir(PhysicalObjectInterface):
    """
    代表水务系统中的一个基础对象：水库。
    其状态由入流和出流的水量平衡决定。
    它可以接收来自上游组件的物理入流，也可以通过消息总线接收数据驱动的入流（例如，降雨、观测数据）。
    库容和水位之间的关系由库容曲线定义。
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters,
                 message_bus = None, inflow_topic: Optional[str] = None, **kwargs):
        super().__init__(name, initial_state, parameters)
        self._initial_state = initial_state.copy()

        self._state.setdefault('outflow', 0) # 确保状态中有outflow键

        if 'storage_curve' in self._params:
            self._validate_and_prepare_storage_curve()
        elif 'surface_area' not in self._params and 'area' not in self._params:
            raise ValueError("Reservoir parameters must include either 'storage_curve' or 'surface_area'/'area'.")

        # 补全缺失的初始状态：如果只提供了 water_level 而没有 volume，则计算 volume
        self._complete_initial_state()

        self.bus = message_bus
        # 为了灵活性，从构造函数参数或parameters字典中获取入流主题
        self.inflow_topic = inflow_topic or self._params.get('inflow_topic')
        self.data_inflow = 0.0
        # For new flexible topic subscriptions
        self.topic_inflows = {}
        self.topic_outflows = {}

        if self.bus:
            # New flexible way to subscribe from lists in parameters
            self._subscribe_from_config('inflow_topics', self.topic_inflows)
            self._subscribe_from_config('outflow_topics', self.topic_outflows)

        if self.bus and self.inflow_topic:
            self.bus.subscribe(self.inflow_topic, self.handle_inflow_message)
            print(f"水库 '{self.name}' 已订阅数据入流主题 '{self.inflow_topic}'.")

        # 处理从components.yml传入的inflow参数
        if 'inflow' in kwargs:
            self._inflow = kwargs['inflow']
            print(f"水库 '{self.name}' 从配置中设置初始入流为 {self._inflow} m³/s")
        elif 'inflow' in self._params:
            self._inflow = self._params['inflow']
            print(f"水库 '{self.name}' 从参数中设置初始入流为 {self._inflow} m³/s")

        print(f"水库 '{self.name}' 已创建，初始状态为 {self._state}.")

    def _complete_initial_state(self):
        """补全缺失的初始状态：如果只提供了 water_level 而没有 volume，则计算 volume；反之亦然。"""
        has_level = 'water_level' in self._state
        has_volume = 'volume' in self._state
        
        if has_level and not has_volume:
            # 根据 water_level 计算 volume
            if hasattr(self, 'storage_curve_np'):
                # 使用库容曲线
                volume = np.interp(self._state['water_level'], self._levels, self._volumes)
            else:
                # 使用线性关系
                area = self._params.get('surface_area', self._params.get('area', 1.0))
                volume = self._state['water_level'] * area
            self._state['volume'] = volume
            self._initial_state['volume'] = volume
            print(f"根据水位 {self._state['water_level']} m 计算得到初始体积 {volume} m^3")
        elif has_volume and not has_level:
            # 根据 volume 计算 water_level
            level = self._get_level_from_volume(self._state['volume'])
            self._state['water_level'] = level
            self._initial_state['water_level'] = level
            print(f"根据体积 {self._state['volume']} m^3 计算得到初始水位 {level} m")
        elif not has_level and not has_volume:
            # 两者都没有，设置默认值
            self._state['water_level'] = 0.0
            self._state['volume'] = 0.0
            self._initial_state['water_level'] = 0.0
            self._initial_state['volume'] = 0.0
            print("警告：初始状态中既没有水位也没有体积，设置为默认值 0")

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
        """Calculates water level from volume, using storage curve if available, otherwise assuming a linear relationship."""
        if hasattr(self, 'storage_curve_np'):
            return np.interp(volume, self._volumes, self._levels)
        else:
            area = self._params.get('surface_area', self._params.get('area', 1.0))
            if area <= 0:
                return 0.0
            # If initial state for level is provided, use it as a reference.
            initial_level = self._initial_state.get('water_level', 0)
            initial_volume = self._initial_state.get('volume', 0)
            return initial_level + (volume - initial_volume) / area

    def _get_volume_from_level(self, level: float) -> float:
        """Calculates volume from water level, using storage curve if available, otherwise assuming a linear relationship."""
        if hasattr(self, 'storage_curve_np'):
            return np.interp(level, self._levels, self._volumes)
        else:
            area = self._params.get('surface_area', self._params.get('area', 1.0))
            # If initial state for level is provided, use it as a reference.
            initial_level = self._initial_state.get('water_level', 0)
            initial_volume = self._initial_state.get('volume', 0)
            return initial_volume + (level - initial_level) * area

    def set_parameters(self, parameters: Parameters):
        """重写该方法，以便在参数更新时重新验证库容曲线。"""
        super().set_parameters(parameters)
        if 'storage_curve' in parameters:
            self._validate_and_prepare_storage_curve()


    def _subscribe_from_config(self, config_key: str, storage: Dict[str, float]):
        """Reads topic configurations from parameters and subscribes handlers."""
        topic_configs = self._params.get(config_key, [])
        if not isinstance(topic_configs, list):
            print(f"Warning: Reservoir '{self.name}' expects '{config_key}' to be a list.")
            return

        for config in topic_configs:
            topic = config.get('topic')
            key = config.get('key', 'value')
            if not topic:
                continue

            storage[topic] = 0.0
            # Use a closure to capture topic-specific variables correctly for the handler
            def create_handler(topic_name, msg_key, storage_dict):
                def handler(message: Dict[str, Any]):
                    value = message.get(msg_key, 0.0)
                    if isinstance(value, (int, float)):
                        storage_dict[topic_name] = value
                return handler

            self.bus.subscribe(topic, create_handler(topic, key, storage))
            print(f"Reservoir '{self.name}' subscribed to {config_key.replace('_', ' ')} '{topic}' with key '{key}'.")

    def handle_inflow_message(self, message: Dict[str, Any]):
        """处理数据驱动入流消息的回调函数。"""
        inflow_value = message.get('control_signal') or message.get('inflow_rate')
        if isinstance(inflow_value, (int, float)):
            self.data_inflow += inflow_value

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """模拟水库在单个时间步内的状态变化。"""

        physical_inflow = self._inflow
        legacy_data_inflow = self.data_inflow
        topic_based_inflow = sum(self.topic_inflows.values())
        total_inflow = physical_inflow + legacy_data_inflow + topic_based_inflow

        # Sum outflows from all sources
        action_outflow = action.get('outflow', 0)
        topic_based_outflow = sum(self.topic_outflows.values())
        total_outflow = action_outflow + topic_based_outflow

        # Calculate water balance
        current_volume = self._state.get('volume', 0)
        delta_volume = (total_inflow - total_outflow) * time_step
        new_volume = max(0, current_volume + delta_volume)

        # Update state
        self._state['volume'] = new_volume
        self._state['water_level'] = self._get_level_from_volume(new_volume)

        self._state['outflow'] = total_outflow
        self._state['inflow'] = total_inflow # 将总入流添加到状态中，供感知智能体使用

        # 为下一个时间步重置数据驱动的入流
        self.data_inflow = 0.0
        for topic in self.topic_inflows:
            self.topic_inflows[topic] = 0.0
        for topic in self.topic_outflows:
            self.topic_outflows[topic] = 0.0

        return self._state

    def set_inflow(self, inflow: float):
        """设置水库的入流量。
        
        Args:
            inflow: 新的入流量 (m³/s)
        """
        self._inflow = inflow
        print(f"水库 '{self.name}' 入流已设置为 {inflow} m³/s")

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
        if not hasattr(self, 'storage_curve_np'):
            raise NotImplementedError("Parameter identification is only supported for reservoirs with a defined 'storage_curve'.")

        if not all(k in data for k in ['inflows', 'outflows', 'levels']):
            raise ValueError("辨识数据必须包含 'inflows', 'outflows', 和 'levels'.")

        inflows = data['inflows']
        outflows = data['outflows']
        observed_levels = data['levels']

        # 假设dt是恒定的，从数据点数量推断（例如，一天的数据）。
        # 理想情况下，这个值应该由数据提供。这里我们假设步长是每小时。
        time_step= 3600 # 秒

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
                delta_v = (inflows[i-1] - outflows[i-1]) * time_step
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

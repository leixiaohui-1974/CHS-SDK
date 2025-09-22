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
                 message_bus: Optional[MessageBus] = None, inflow_topic: Optional[str] = None, **kwargs):
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
            print(f"水库 '{self.name}' 从配置中设置初始入流为 {self._inflow} m3/s")
        elif 'inflow' in self._params:
            self._inflow = self._params['inflow']
            print(f"水库 '{self.name}' 从参数中设置初始入流为 {self._inflow} m3/s")

        print(f"水库 '{self.name}' 已创建，初始状态为 {self._state}.")

    def _complete_initial_state(self):
        """补全缺失的初始状态：如果只提供了 water_level 而没有 volume，则计算 volume；反之亦然。"""
        has_level = 'water_level' in self._state
        has_volume = 'volume' in self._state
        
        if has_level and has_volume:
            # 同时有水位和库容，需要检查一致性
            provided_level = self._state['water_level']
            provided_volume = self._state['volume']
            
            # 根据水位计算应有的库容
            expected_volume = self._get_volume_from_level(provided_level)
            
            # 检查是否一致（允许小量误差）
            volume_diff = abs(provided_volume - expected_volume)
            tolerance = max(10.0, expected_volume * 0.1)  # 10m³或10%的误差
            
            if volume_diff > tolerance:
                print(f"警告：水库 '{self.name}' 初始状态不一致！")
                print(f"  配置的水位 {provided_level:.3f}m 对应的库容应为 {expected_volume:.3f}m³")
                print(f"  但配置的库容是 {provided_volume:.3f}m³，相差 {volume_diff:.3f}m³")
                print(f"  将优先使用水位值，并重新计算库容")
                
                # 优先使用水位，重新计算库容
                self._state['volume'] = expected_volume
                self._initial_state['volume'] = expected_volume
                print(f"  修正后：水位 {provided_level:.3f}m，库容 {expected_volume:.3f}m³")
            else:
                print(f"水库 '{self.name}' 初始状态一致：水位 {provided_level:.3f}m，库容 {provided_volume:.3f}m³")
                
        elif has_level and not has_volume:
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
            print(f"警告：水库 '{self.name}' 初始状态中既没有水位也没有体积，设置为默认值 0")

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
            # 检查是否超出库容曲线范围
            max_volume = self._volumes[-1]
            min_volume = self._volumes[0]
            
            if volume > max_volume:
                # 超出最大库容，警告并使用线性外推
                max_level = self._levels[-1]
                # 使用最后两点的斜率进行线性外推
                if len(self._volumes) >= 2:
                    volume_diff = self._volumes[-1] - self._volumes[-2]
                    level_diff = self._levels[-1] - self._levels[-2]
                    if volume_diff > 0:
                        slope = level_diff / volume_diff
                        extrapolated_level = max_level + (volume - max_volume) * slope
                        print(f"警告：水库 '{self.name}' 库容 {volume:.1f}m³ 超出曲线范围（最大 {max_volume:.1f}m³）")
                        print(f"  使用线性外推：水位 {extrapolated_level:.3f}m")
                        return extrapolated_level
                return max_level
            elif volume < min_volume:
                # 低于最小库容，返回最小水位
                return self._levels[0]
            else:
                # 正常范围内，使用插值
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
                def handler(message: Message):
                    value = message.get(msg_key, 0.0)
                    if isinstance(value, (int, float)):
                        storage_dict[topic_name] = value
                return handler

            self.bus.subscribe(topic, create_handler(topic, key, storage))
            print(f"Reservoir '{self.name}' subscribed to {config_key.replace('_', ' ')} '{topic}' with key '{key}'.")

    def handle_inflow_message(self, message: Message):
        """处理数据驱动入流消息的回调函数。"""
        inflow_value = message.get('control_signal') or message.get('inflow_rate')
        if isinstance(inflow_value, (int, float)):
            self.data_inflow += inflow_value

    def step(self, action: Dict[str, Any], time_step: float) -> State:
        """模拟水库在单个时间步内的状态变化。"""
        
        # 获取当前仿真时间（从action中传递）
        current_time = action.get('current_time', 0.0)
        
        physical_inflow = self._inflow
        legacy_data_inflow = self.data_inflow
        topic_based_inflow = sum(self.topic_inflows.values())
        total_inflow = physical_inflow + legacy_data_inflow + topic_based_inflow

        # 处理出流：action中的出流是可选的，可以为0
        action_outflow = action.get('outflow', 0)  # 这里允许默认为0，因为水库可以没有外部出流
        topic_based_outflow = sum(self.topic_outflows.values())
        
        # 检查是否有固定出流参数（边界条件）
        fixed_outflow = self._params.get('outflow', 0.0)
        
        # 如果有出流时间序列，则按时间序列设置
        outflow_timeseries = self._params.get('outflow_timeSeries')
        if outflow_timeseries:
            prescribed_outflow = self._interpolate_timeseries(outflow_timeseries, current_time)
            total_outflow = prescribed_outflow + topic_based_outflow
            print(f"水库 '{self.name}' - 出流边界条件：时间 {current_time}s，出流 {prescribed_outflow:.3f}m³/s")
        elif fixed_outflow > 0:
            # 使用固定出流参数
            total_outflow = fixed_outflow + topic_based_outflow
            print(f"水库 '{self.name}' - 固定出流：{fixed_outflow:.3f}m³/s")
        else:
            # 使用action中的出流
            total_outflow = action_outflow + topic_based_outflow

        # 检查边界条件类型（根据nodeType参数决定）
        node_type = self._params.get('nodeType', 0)  # 0-内部节点，1-水位边界节点，2-流量边界节点
        water_level_timeseries = self._params.get('water_level_timeSeries')
        
        # 只有当明确指定为水位边界节点时，才强制按水位时间序列设置
        if node_type == 1 and water_level_timeseries:
            # 水位边界条件：根据时间序列设置水位，库容也需要相应调整
            prescribed_level = self._interpolate_timeseries(water_level_timeseries, current_time)
            self._state['water_level'] = prescribed_level
            # 根据新水位计算相应的库容
            self._state['volume'] = self._get_volume_from_level(prescribed_level)
            
            print(f"水库 '{self.name}' - 水位边界条件：时间 {current_time}s，水位 {prescribed_level:.3f}m，库容 {self._state['volume']:.3f}m³")
        else:
            # 正常水量平衡计算（包括内部节点和流量边界节点）
            current_volume = self._state.get('volume', 0)
            delta_volume = (total_inflow - total_outflow) * time_step
            new_volume = max(0, current_volume + delta_volume)
            
            # 更新状态
            self._state['volume'] = new_volume
            self._state['water_level'] = self._get_level_from_volume(new_volume)
            
            # 调试信息：显示水量平衡计算
            if abs(delta_volume) > 0.001:  # 只有在有显著变化时才打印
                print(f"水库 '{self.name}' - 水量平衡：入流{total_inflow:.3f} - 出流{total_outflow:.3f} = 净流量{total_inflow-total_outflow:.3f}m³/s")
                print(f"  时间步{time_step}s，体积变化{delta_volume:.3f}m³，新体积{new_volume:.3f}m³，新水位{self._state['water_level']:.3f}m")

        self._state['outflow'] = total_outflow
        self._state['inflow'] = total_inflow # 将总入流添加到状态中，供感知智能体使用

        # 为下一个时间步重置数据驱动的入流
        self.data_inflow = 0.0
        for topic in self.topic_inflows:
            self.topic_inflows[topic] = 0.0
        for topic in self.topic_outflows:
            self.topic_outflows[topic] = 0.0

        return self._state
    
    def _interpolate_timeseries(self, timeseries: List[List[float]], current_time: float) -> float:
        """对时间序列数据进行线性插值"""
        if not timeseries or len(timeseries) == 0:
            return 0.0
            
        # 时间序列格式：[[time, value], [time, value], ...]
        times = [point[0] for point in timeseries]
        values = [point[1] for point in timeseries]
        
        # 如果当前时间在范围之外，返回边界值
        if current_time <= times[0]:
            return values[0]
        if current_time >= times[-1]:
            return values[-1]
            
        # 线性插值
        for i in range(len(times) - 1):
            if times[i] <= current_time <= times[i + 1]:
                # 线性插值公式
                t1, t2 = times[i], times[i + 1]
                v1, v2 = values[i], values[i + 1]
                interpolated_value = v1 + (v2 - v1) * (current_time - t1) / (t2 - t1)
                return interpolated_value
                
        return values[0]  # 默认返回第一个值

    def set_inflow(self, inflow: float):
        """设置水库的入流量。
        
        Args:
            inflow: 新的入流量 (m³/s)
        """
        self._inflow = inflow
        print(f"水库 '{self.name}' 入流已设置为 {inflow} m3/s")

    @property
    def is_stateful(self) -> bool:
        return True

    def identify_parameters(self, data: Dict[str, np.ndarray], method: str = 'offline', time_step: Optional[float] = None) -> Parameters:
        """
        使用历史数据辨识库容曲线参数。

        Args:
            data: 一个包含numpy数组的字典，应包含：
                  - 'inflows': 总入流的时间序列数据。
                  - 'outflows': 总出流的时间序列数据。
                  - 'levels': 观测水位的时间序列数据。
                  - 'time_step' (可选): 数据时间步长，单位为秒。
            method: 辨识方法（目前仅支持 'offline'）。
            time_step: 数据时间步长（秒），如果为None，将尝试从data中获取或使用默认值。

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

        # 获取时间步长：优先级顺序为 time_step参数 > data字典中的time_step > 默认值
        if time_step is not None:
            dt = time_step
        elif 'time_step' in data:
            dt = float(data['time_step'])
        else:
            # 默认值：根据数据特征推断
            # 如果数据点少于100个，假设为小时级数据；否则假设为分钟级数据
            data_length = len(inflows)
            if data_length < 100:
                dt = 3600.0  # 1小时（秒）
                print(f"警告: 未提供时间步长，根据数据长度 {data_length} 推断为小时级数据，使用 {dt} 秒")
            else:
                dt = 60.0    # 1分钟（秒）
                print(f"警告: 未提供时间步长，根据数据长度 {data_length} 推断为分钟级数据，使用 {dt} 秒")

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

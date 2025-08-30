# -*- coding: utf-8 -*-
import numpy as np
from collections import deque
import warnings
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters

class UnifiedCanal(PhysicalObjectInterface):
    """
    A unified model for a canal reach that can represent several different
    simplified models based on a `model_type` parameter.
    """
    def __init__(self, name: str, initial_state: State, parameters: Parameters, **kwargs):
        super().__init__(name, initial_state, parameters)

        self.model_type = self._params.get('model_type', 'integral_delay')

        # Common parameters
        self._state['water_level'] = initial_state.get('water_level', 5.0)
        self._state['inflow'] = initial_state.get('inflow', 0.0)
        self._state['outflow'] = initial_state.get('outflow', 0.0)

        # Model-specific parameter handling
        if self.model_type == 'integral':
            self.surface_area = self._params.get('surface_area', 10000.0)
            self.outlet_coefficient = self._params.get('outlet_coefficient', 5.0)
        elif self.model_type == 'integral_delay':
            self.gain = self._params.get('gain', 0.001)
            self.delay = self._params.get('delay', 300)
        elif self.model_type == 'integral_delay_zero':
            self.gain = self._params.get('gain', 0.001)
            self.delay = self._params.get('delay', 300)
            self.zero_time_constant = self._params.get('zero_time_constant', 50)
        elif self.model_type == 'linear_reservoir':
            self.storage_constant = self._params.get('storage_constant', 1200)
            self.level_storage_ratio = self._params.get('level_storage_ratio', 0.005)
            self.storage = self._state.get('water_level', 0.0) / self.level_storage_ratio

        # History buffer for delay models
        self.inflow_history = None
        self.history_size = 0

    def step(self, action: any, dt: float) -> State:
        if dt <= 0:
            return self.get_state()

        if self.model_type == 'integral':
            self._step_integral(dt)
        elif self.model_type == 'integral_delay':
            self._step_integral_delay(dt)
        elif self.model_type == 'integral_delay_zero':
            self._step_integral_delay_zero(dt)
        elif self.model_type == 'linear_reservoir':
            self._step_linear_reservoir(dt)
        else:
            raise ValueError(f"Unknown canal model type: {self.model_type}")

        return self.get_state()

    def _initialize_history(self, dt):
        if self.inflow_history is None:
            self.history_size = int(self.delay / dt) + 2 if self.delay else 2
            initial_inflow = self._state.get('inflow', 0.0)
            self.inflow_history = deque([initial_inflow] * self.history_size, maxlen=self.history_size)

    def _step_integral(self, dt: float):
        inflow = self._inflow
        self._state['inflow'] = inflow

        # Outflow is a function of water level (like a reservoir)
        self._state['outflow'] = self.outlet_coefficient * np.sqrt(max(0, self._state['water_level']))

        self._state['water_level'] += (inflow - self._state['outflow']) / self.surface_area * dt
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_integral_delay(self, dt: float):
        self._initialize_history(dt)
        inflow = self._inflow
        self._state['inflow'] = inflow
        self.inflow_history.append(inflow)
        delayed_inflow = self.inflow_history[0]
        self._state['outflow'] = delayed_inflow
        self._state['water_level'] += self.gain * (inflow - delayed_inflow) * dt
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_integral_delay_zero(self, dt: float):
        self._initialize_history(dt)
        inflow = self._inflow
        self._state['inflow'] = inflow
        self.inflow_history.append(inflow)
        q_in_delayed = self.inflow_history[1]
        q_in_delayed_previous = self.inflow_history[0]
        derivative_term = (q_in_delayed - q_in_delayed_previous) / dt
        self._state['outflow'] = q_in_delayed + self.zero_time_constant * derivative_term
        self._state['water_level'] += self.gain * (inflow - self._state['outflow']) * dt
        self._state['water_level'] = max(0, self._state['water_level'])

    def _step_linear_reservoir(self, dt: float):
        inflow = self._inflow
        self._state['inflow'] = inflow
        outflow_old = self._state['outflow']
        outflow_new = (self.storage_constant * outflow_old + dt * inflow) / (self.storage_constant + dt)
        self._state['outflow'] = outflow_new
        storage_change = (inflow - outflow_new) * dt
        self.storage += storage_change
        self._state['water_level'] = self.storage * self.level_storage_ratio
        self._state['water_level'] = max(0, self._state['water_level'])

    @property
    def is_stateful(self) -> bool:
        return True

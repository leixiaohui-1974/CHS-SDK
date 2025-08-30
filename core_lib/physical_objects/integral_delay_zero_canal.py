# -*- coding: utf-8 -*-
import numpy as np
from collections import deque
from core_lib.core.interfaces import PhysicalObjectInterface, State, Parameters

class IntegralDelayZeroCanal(PhysicalObjectInterface):
    """
    Represents a canal reach modeled with an integral, delay, and zero process.
    This model extends the IntegralDelayCanal by adding a zero to the transfer
    function, which can help approximate the wave propagation dynamics more closely.

    The outflow is modeled as a function of the delayed inflow, including a zero term:
    q_out(t) = q_in(t-τ) + Tz * (q_in(t-τ) - q_in(t-τ-dt)) / dt
    where τ is the delay and Tz is the time constant of the zero.
    """
    def __init__(self, name: str, initial_state: State, parameters: Parameters, **kwargs):
        super().__init__(name, initial_state, parameters)
        self.gain = self._params.get('gain', 0.001)
        self.delay = self._params.get('delay', 300) # seconds
        self.zero_time_constant = self._params.get('zero_time_constant', 50) # seconds

        self._state['water_level'] = initial_state.get('water_level', 5.0)
        self._state['inflow'] = initial_state.get('inflow', 0.0)
        self._state['outflow'] = initial_state.get('outflow', 0.0)

        self.inflow_history = None
        self.history_size = 0

    def step(self, action: any, dt: float) -> State:
        """
        Advances the canal simulation for one time step.
        """
        if self.inflow_history is None:
            if dt > 0:
                self.history_size = int(self.delay / dt) + 2
            else:
                self.history_size = 2

            initial_inflow = self._state.get('inflow', 0.0)
            self.inflow_history = deque([initial_inflow] * self.history_size, maxlen=self.history_size)

        inflow = self._inflow
        self._state['inflow'] = inflow

        if len(self.inflow_history) == self.history_size:
            q_in_delayed = self.inflow_history[1]
            q_in_delayed_previous = self.inflow_history[0]

            # Outflow calculation with zero term
            if dt > 0:
                derivative_term = (q_in_delayed - q_in_delayed_previous) / dt
                self._state['outflow'] = q_in_delayed + self.zero_time_constant * derivative_term
            else:
                self._state['outflow'] = q_in_delayed
        else:
            # Not enough history yet, assume zero outflow
            self._state['outflow'] = 0

        # Add the current inflow to the history for the next step
        self.inflow_history.append(inflow)

        # Update water level based on the integral action
        self._state['water_level'] += self.gain * (inflow - self._state['outflow']) * dt
        self._state['water_level'] = max(0, self._state['water_level'])

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        return True

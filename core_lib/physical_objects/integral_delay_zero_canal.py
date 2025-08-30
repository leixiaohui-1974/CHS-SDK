# -*- coding: utf-8 -*-
import numpy as np
from collections import deque
from core_lib.core.interfaces import PhysicalObjectInterface

class IntegralDelayZeroCanal(PhysicalObjectInterface):
    """
    Represents a canal reach modeled with an integral, delay, and zero process.
    This model extends the IntegralDelayCanal by adding a zero to the transfer
    function, which can help approximate the wave propagation dynamics more closely.

    The outflow is modeled as a function of the delayed inflow, including a zero term:
    q_out(t) = q_in(t-τ) + Tz * (q_in(t-τ) - q_in(t-τ-dt)) / dt
    where τ is the delay and Tz is the time constant of the zero.
    """
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.gain = kwargs.get('gain', 0.001)
        self.delay = kwargs.get('delay', 300) # seconds
        self.zero_time_constant = kwargs.get('zero_time_constant', 50) # seconds
        self.water_level = kwargs.get('initial_water_level', 5.0)
        self.inflow = 0.0
        self.outflow = 0.0

        self.time_step = kwargs.get('dt', 10) # Default timestep of 10s
        if self.time_step > 0:
            # We need one extra history point for the zero term calculation
            self.history_size = int(self.delay / self.time_step) + 1
        else:
            self.history_size = 2

        initial_inflow = kwargs.get('initial_inflow', 0.0)
        self.inflow_history = deque([initial_inflow] * self.history_size, maxlen=self.history_size)

    def update_state(self, new_inflow):
        """
        Updates the canal state based on the new inflow.
        """
        self.inflow = new_inflow

        if len(self.inflow_history) == self.history_size:
            q_in_delayed = self.inflow_history[1]
            q_in_delayed_previous = self.inflow_history[0]

            # Outflow calculation with zero term
            derivative_term = (q_in_delayed - q_in_delayed_previous) / self.time_step
            self.outflow = q_in_delayed + self.zero_time_constant * derivative_term
        else:
            # Not enough history yet, assume zero outflow
            self.outflow = 0

        # Add the current inflow to the history for the next step
        self.inflow_history.append(self.inflow)

        # Update water level based on the integral action
        self.water_level += self.gain * (self.inflow - self.outflow) * self.time_step


    def get_state(self):
        """Returns the current state of the canal."""
        return {
            'water_level': self.water_level,
            'inflow': self.inflow,
            'outflow': self.outflow
        }

    def set_inflow(self, inflow):
        """Callback to receive inflow from an upstream object."""
        self.update_state(inflow)

    def connect(self, upstream_object):
        """Connects to an upstream object that provides inflow."""
        pass # Connections are handled by the simulation harness

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
    g = 9.81  # Gravity

    def __init__(self, name: str, initial_state: State, parameters: Parameters, **kwargs):
        super().__init__(name, initial_state, parameters)

        self.model_type = self._params.get('model_type', 'integral_delay')

        # Common parameters for simple models
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
        elif self.model_type == 'st_venant':
            self.length = self._params['length']
            self.num_points = self._params['num_points']
            self.dx = self.length / (self.num_points - 1)

            self.bottom_width = self._params['bottom_width']
            self.side_slope_z = self._params['side_slope_z']
            self.manning_n = self._params['manning_n']
            self.slope = self._params['slope']

            initial_H = self._params.get('initial_H', np.full(self.num_points, 5.0))
            initial_Q = self._params.get('initial_Q', np.full(self.num_points, 10.0))

            self.H = np.array(initial_H, dtype=float)
            self.Q = np.array(initial_Q, dtype=float)

            if len(self.H) != self.num_points or len(self.Q) != self.num_points:
                raise ValueError("Length of initial_H and initial_Q must match num_points.")

            print(f"UnifiedCanal '{self.name}' (st_venant model) created with {self.num_points} points (dx = {self.dx:.2f}m).")

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
        elif self.model_type == 'st_venant':
            raise NotImplementedError("The 'st_venant' model cannot be run with step(). It must be used with the NetworkSolver.")
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

    # --- St. Venant Model Methods ---

    def _area(self, h):
        return (self.bottom_width + self.side_slope_z * h) * h

    def _top_width(self, h):
        return self.bottom_width + 2 * self.side_slope_z * h

    def _wetted_perimeter(self, h):
        return self.bottom_width + 2 * h * np.sqrt(1 + self.side_slope_z**2)

    def _friction_slope(self, Q, A, R):
        if A < 1e-6 or R < 1e-6:
            return 0
        return (self.manning_n**2 * Q * abs(Q)) / (A**2 * R**(4/3))

    def get_equations(self, dt: float, theta: float = 0.6):
        """
        Generates the linearized Saint-Venant equations for each segment of the reach.
        This method is only applicable when model_type is 'st_venant'.
        """
        if self.model_type != 'st_venant':
            raise RuntimeError("get_equations() is only valid for the 'st_venant' model type.")

        equations = []
        for i in range(self.num_points - 1):
            H_i, Q_i = self.H[i], self.Q[i]
            H_i1, Q_i1 = self.H[i+1], self.Q[i+1]
            H_avg = (H_i + H_i1) / 2
            Q_avg = (Q_i + Q_i1) / 2
            A_avg = self._area(H_avg)
            B_avg = self._top_width(H_avg)
            P_avg = self._wetted_perimeter(H_avg)
            R_avg = A_avg / P_avg if P_avg > 1e-6 else 0
            Sf_avg = self._friction_slope(Q_avg, A_avg, R_avg)

            # Simplified but stable Preissmann scheme formulation
            # Eq1: Continuity
            L1 = -theta
            L2 = B_avg * self.dx / (2 * dt)
            L3 = theta
            L4 = B_avg * self.dx / (2 * dt)
            RHS_cont = Q_i - Q_i1

            # Eq2: Momentum
            M1 = -self.g * A_avg * theta
            M2 = self.dx / (2 * dt)
            M3 = self.g * A_avg * theta
            M4 = self.dx / (2 * dt)

            if R_avg > 1e-6 and A_avg > 1e-6:
                dSf_dQ = 2 * self.manning_n**2 * abs(Q_avg) / (A_avg**2 * R_avg**(4/3))
                M2 += self.g * A_avg * self.dx * dSf_dQ * theta
                M4 += self.g * A_avg * self.dx * dSf_dQ * theta

            RHS_mom = self.dx/dt * ( (Q_i+Q_i1)/2 - (self.Q[i]+self.Q[i+1])/2) - \
                      self.g*A_avg*self.dx * ( (H_i1-H_i)/self.dx - self.slope + Sf_avg)

            Ai = np.array([[L3, L4], [M3, M4]])
            Bi = np.array([[L1, L2], [M1, M2]])
            Ci = np.array([RHS_cont, RHS_mom])

            equations.append((Ai, Bi, Ci))

        return equations

    def update_state(self, dH: np.ndarray, dQ: np.ndarray):
        """
        Updates the state variables H and Q with the deltas calculated by the solver.
        This method is only applicable when model_type is 'st_venant'.
        """
        if self.model_type != 'st_venant':
            raise RuntimeError("update_state() is only valid for the 'st_venant' model type.")

        self.H += dH
        self.Q += dQ

"""
Simulation model for a Pipe.
"""
import math
from swp.core.interfaces import Simulatable, State, Parameters
from typing import Dict, Any

class Pipe(Simulatable):
    """
    Represents a pipe, which transports water between two points.

    This model uses a simplified version of the Darcy-Weisbach equation to calculate
    flow based on the head difference between its upstream and downstream ends.
    The flow is considered to be turbulent and is proportional to the square root
    of the head loss.
    """

    def __init__(self, pipe_id: str, initial_state: State, params: Parameters):
        """
        Initializes the Pipe model.

        Args:
            pipe_id: The unique ID for the pipe.
            initial_state: The initial state of the pipe, e.g., {'flow': 0}.
            params: A dictionary of the pipe's physical parameters, including:
                    - 'length' (m)
                    - 'diameter' (m)
                    - 'friction_factor' (dimensionless, e.g., 0.02 for cast iron)
        """
        self.pipe_id = pipe_id
        self._state = initial_state
        self._params = params
        self._state['flow'] = initial_state.get('flow', 0)
        self._state['head_loss'] = 0

        # Pre-calculate a flow coefficient to simplify the step calculation
        # From Darcy-Weisbach: H_f = f * (L/D) * (V^2 / 2g)
        # and Q = V * A. Rearranging for Q gives:
        # Q = A * sqrt(2 * g * D * H_f / (f * L))
        # We can group the constant parts into a coefficient C.
        g = 9.81
        area = (math.pi / 4) * (self._params['diameter'] ** 2)
        self.flow_coefficient = area * math.sqrt(2 * g * self._params['diameter'] / (self._params['friction_factor'] * self._params['length']))

        print(f"Pipe '{self.pipe_id}' created with flow coefficient {self.flow_coefficient:.4f}.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Calculates the flow through the pipe for one time step.

        The flow is determined by the head difference provided by the harness. This
        model assumes that the flow stabilizes within a single time step.

        Args:
            action: A dictionary containing:
                    - 'upstream_head': The water head at the start of the pipe (m).
                    - 'downstream_head': The water head at the end of the pipe (m).
            dt: The time step duration (ignored in this steady-state flow model).

        Returns:
            The updated state of the pipe.
        """
        upstream_head = action.get('upstream_head', 0)
        downstream_head = action.get('downstream_head', 0)

        head_difference = upstream_head - downstream_head

        if head_difference > 0:
            # Flow is positive (downstream)
            flow = self.flow_coefficient * math.sqrt(head_difference)
            self._state['head_loss'] = head_difference
        else:
            # No flow or reverse flow (simplified to no flow)
            flow = 0
            self._state['head_loss'] = 0

        self._state['flow'] = flow
        # In this model, outflow is the same as flow
        self._state['outflow'] = flow

        return self._state

    def get_state(self) -> State:
        """Returns the current state of the pipe."""
        return self._state

    def set_state(self, state: State):
        """Sets the state of the pipe."""
        self._state = state

    def get_parameters(self) -> Parameters:
        """Returns the model parameters of the pipe."""
        return self._params

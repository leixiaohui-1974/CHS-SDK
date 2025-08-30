import collections
from typing import Optional

from core_lib.core.interfaces import PhysicalObjectInterface, State

class IntegralDelayCanal(PhysicalObjectInterface):
    """
    Represents a canal using an integral time-delay model.

    This model is a simple representation often used for designing controllers.
    It captures two key aspects of canal hydraulics: the storage effect (integration)
    and the wave travel time (time delay).

    The water level `y` at the downstream end of the canal is modeled as:
    dy/dt = K * u(t - tau)

    where:
    - y is the water level.
    - u is the inflow at the upstream end.
    - K is the process gain (e.g., 1 / surface_area).
    - tau is the time delay.

    State Variables:
        - water_level (float): The water level at the downstream end of the canal (m).
        - outflow (float): The outflow from the canal, assumed to be the delayed inflow (m^3/s).

    Parameters:
        - gain (float): The integrating gain of the process.
        - delay (float): The time delay in seconds.
    """

    def __init__(self, name: str, initial_state: State, parameters: dict, **kwargs):
        super().__init__(name, initial_state, parameters)
        self.gain = self._params['gain']
        self.delay = self._params['delay']  # in seconds

        # State variables
        self._state['water_level'] = initial_state.get('water_level', 0)
        self._state['outflow'] = initial_state.get('outflow', 0)

        # Inflow history buffer will be initialized on the first step call
        self.inflow_history = None
        self.history_size = 0

    def step(self, action: any, dt: float) -> State:
        """
        Advances the canal simulation for one time step.
        """
        # Initialize history buffer on the first call to step, when dt is known
        if self.inflow_history is None:
            if dt > 0:
                self.history_size = int(self.delay / dt) + 2
            else:
                self.history_size = 2 # Avoid division by zero, have at least one delay slot
            self.inflow_history = collections.deque(
                [self._inflow] * self.history_size, maxlen=self.history_size
            )

        # Get inflow from upstream component (set by the simulation harness)
        inflow = self._inflow

        # Store current inflow in history
        self.inflow_history.append(inflow)

        # Get delayed inflow. The deque stores the most recent item at the right.
        # The item at index 0 is the oldest, which corresponds to u(t - tau).
        delayed_inflow = self.inflow_history[0]

        # Update water level using the discrete-time version of the model
        self._state['water_level'] += self.gain * delayed_inflow * dt
        self._state['water_level'] = max(0, self._state['water_level']) # Water level cannot be negative

        # The outflow of this canal reach is the delayed inflow
        self._state['outflow'] = delayed_inflow

        return self.get_state()

    @property
    def is_stateful(self) -> bool:
        """A canal stores water, so it is a stateful component."""
        return True

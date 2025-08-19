"""
Simulation model for a Reservoir.
"""
from swp.core.interfaces import PhysicalObjectInterface, State, Parameters
from typing import Dict, Any

class Reservoir(PhysicalObjectInterface):
    """
    Represents a reservoir, a fundamental object in a water system.
    Its state is determined by the balance of inflows and outflows.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        super().__init__(name, initial_state, parameters)
        self._state.setdefault('outflow', 0) # Ensure outflow is in the state
        print(f"Reservoir '{self.name}' created with initial state {self._state}.")

    def step(self, action: Dict[str, Any], dt: float) -> State:
        """
        Simulates the reservoir's change over a single time step.
        """
        inflow = self._inflow
        # The harness calculates the required outflow from downstream demand and provides it in the action
        outflow = action.get('outflow', 0)

        current_volume = self._state.get('volume', 0)
        surface_area = self._params.get('surface_area', 1e6) # m^2

        # Water balance equation
        delta_volume = (inflow - outflow) * dt
        new_volume = current_volume + delta_volume

        self._state['volume'] = new_volume
        self._state['water_level'] = new_volume / surface_area # Simplified relationship

        # The outflow is already set by the harness, so we just keep it.

        return self._state

    @property
    def is_stateful(self) -> bool:
        return True

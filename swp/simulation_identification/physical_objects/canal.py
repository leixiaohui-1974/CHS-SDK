import math

from swp.core.interfaces import PhysicalObjectInterface, State


class Canal(PhysicalObjectInterface):
    """
    Represents a canal with a trapezoidal cross-section using Manning's equation for flow.

    This model simulates the water flow and volume changes in a canal segment.
    The outflow is calculated based on the hydraulic properties derived from the
    current water level.

    State Variables:
        - volume (float): The current volume of water in the canal (m^3).
        - water_level (float): The current water level in the canal (m).
        - outflow (float): The calculated outflow from the canal for the current step (m^3/s).

    Parameters:
        - bottom_width (float): The width of the bottom of the canal (m).
        - length (float): The length of the canal segment (m).
        - slope (float): The longitudinal slope of the canal bed (dimensionless).
        - side_slope_z (float): The slope of the canal sides (z in z:1, horizontal:vertical).
        - manning_n (float): Manning's roughness coefficient.
    """

    def __init__(self, name: str, initial_state: State, parameters: dict):
        super().__init__(name, initial_state, parameters)
        # Parameters are accessed via self._params, but can be copied to attributes for convenience
        self.bottom_width = self._params['bottom_width']
        self.length = self._params['length']
        self.slope = self._params['slope']
        self.side_slope_z = self._params['side_slope_z']
        self.manning_n = self._params['manning_n']

    def step(self, action: any, dt: float) -> State:
        """
        Advances the canal simulation for one time step.
        """
        # Inflow is set by the harness via set_inflow()
        inflow = self._inflow

        # Approximate water level from volume. For a trapezoid, this is more complex.
        # V = L * (b*y + z*y^2) -> z*y^2 + b*y - V/L = 0
        # Solving the quadratic equation for y (water_level)
        a = self.side_slope_z
        b = self.bottom_width
        c = -self._state['volume'] / self.length if self.length > 0 else 0

        if a == 0:  # Rectangular channel case
            water_level = self._state['volume'] / (self.bottom_width * self.length) if (self.bottom_width * self.length) > 0 else 0
        else:
            # Quadratic formula: y = (-b + sqrt(b^2 - 4ac)) / 2a
            discriminant = b**2 - 4 * a * c
            if discriminant >= 0:
                water_level = (-b + math.sqrt(discriminant)) / (2 * a)
            else:
                water_level = 0

        self._state['water_level'] = water_level

        # Calculate hydraulic properties for a trapezoidal channel
        if water_level > 0:
            area = (self.bottom_width + self.side_slope_z * water_level) * water_level
            wetted_perimeter = self.bottom_width + 2 * water_level * math.sqrt(1 + self.side_slope_z**2)
            hydraulic_radius = area / wetted_perimeter if wetted_perimeter > 0 else 0
        else:
            area = 0
            hydraulic_radius = 0

        # Calculate outflow using Manning's equation
        # Q = (1/n) * A * R_h^(2/3) * S^(1/2)
        outflow = (1 / self.manning_n) * area * (hydraulic_radius**(2/3)) * (self.slope**0.5) if area > 0 else 0
        self._state['outflow'] = outflow

        # Update volume based on inflow and outflow using mass balance
        self._state['volume'] += (inflow - outflow) * dt
        self._state['volume'] = max(0, self._state['volume']) # Volume cannot be negative

        return self.get_state()

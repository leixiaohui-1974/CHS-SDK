import math

class LevelPoolCanal:
    """
    A simple level-pool routing canal model.

    This model assumes that the water surface in the canal is always horizontal.
    The outflow is calculated based on the water level at the downstream end,
    which is assumed to be the same as the average water level in the canal.
    """
    def __init__(self, name: str, initial_state: dict, parameters: dict):
        self.name = name
        self.state = initial_state
        self.parameters = parameters
        self.inflow = 0.0

    def set_inflow(self, inflow: float):
        self.inflow = inflow

    def step(self, action: dict, dt: float):
        # For level-pool, assume water level is directly proportional to volume
        # and outflow is a function of the water level. This is a simplification.

        # Calculate new volume
        outflow_area = self.state['water_level'] * self.parameters['bottom_width'] # Simplified cross-section
        outflow_velocity = self.parameters['manning_n'] * math.sqrt(self.parameters['slope']) * (outflow_area / (self.parameters['bottom_width'] + 2 * self.state['water_level']))**(2/3)
        self.state['outflow'] = outflow_area * outflow_velocity

        self.state['volume'] += (self.inflow - self.state['outflow']) * dt

        # Update water level based on new volume
        # V = A * L = (b*y + z*y^2) * L
        # This is hard to solve for y, so we'll use a simpler approximation
        self.state['water_level'] = self.state['volume'] / (self.parameters['length'] * self.parameters['bottom_width'])

        return self.state

    def get_state(self):
        return self.state

class IntegralCanal:
    """
    An integral model of a canal.

    This model assumes that the outflow is directly proportional to the volume of water
    stored in the canal, representing a simple linear reservoir.
    """
    def __init__(self, name: str, initial_state: dict, parameters: dict):
        self.name = name
        self.state = initial_state
        self.parameters = parameters
        self.inflow = 0.0

    def set_inflow(self, inflow: float):
        self.inflow = inflow

    def step(self, action: dict, dt: float):
        # Outflow is a linear function of storage (volume)
        # Q_out = k * V
        k = self.parameters.get('k', 0.0001) # Linear discharge coefficient
        self.state['outflow'] = k * self.state['volume']

        # Update volume
        self.state['volume'] += (self.inflow - self.state['outflow']) * dt

        # Water level is proportional to volume
        self.state['water_level'] = self.state['volume'] / (self.parameters['length'] * self.parameters['bottom_width'])

        return self.state

    def get_state(self):
        return self.state

class IntegralDelayZeroPointCanal:
    """
    An integral-delay model with a zero-point offset.

    This model is similar to the integral-delay model but includes a 'zero-point'
    parameter, which represents a baseline water level or volume that does not
    contribute to outflow dynamics.
    """
    def __init__(self, name: str, initial_state: dict, parameters: dict):
        self.name = name
        self.state = initial_state
        self.parameters = parameters
        self.inflow = 0.0
        self.inflow_history = [0.0] * int(self.parameters['delay'] / parameters.get('dt', 10))


    def set_inflow(self, inflow: float):
        self.inflow = inflow

    def step(self, action: dict, dt: float):
        # Add current inflow to history
        self.inflow_history.append(self.inflow)

        # Get delayed inflow
        delayed_inflow = self.inflow_history.pop(0)

        # Volume change is based on the delayed inflow
        zero_point_volume = self.parameters.get('zero_point_volume', 0)
        effective_volume = self.state['volume'] - zero_point_volume
        self.state['outflow'] = delayed_inflow

        self.state['volume'] += (self.inflow - self.state['outflow']) * dt

        # Update water level
        self.state['water_level'] = self.state['volume'] / (self.parameters['length'] * self.parameters['bottom_width'])

        return self.state

    def get_state(self):
        return self.state

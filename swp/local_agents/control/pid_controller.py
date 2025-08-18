"""
A Proportional-Integral-Derivative (PID) Controller.
"""
from swp.core.interfaces import Controller, State

class PIDController(Controller):
    """
    A standard PID controller.

    This is one of the most common types of controllers and serves as a baseline
    control strategy. It computes a control action based on the error between a
    desired setpoint and a measured process variable.
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float):
        """
        Initializes the PID controller.

        Args:
            Kp: Proportional gain.
            Ki: Integral gain.
            Kd: Derivative gain.
            setpoint: The desired value for the system state.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self._integral = 0
        self._previous_error = 0
        print(f"PIDController created with Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}.")

    def compute_control_action(self, observation: State) -> float:
        """
        Computes the PID control action.

        Args:
            observation: The current state of the system, e.g., {'water_level': 10.5}.
                         It must contain a key 'process_variable'.

        Returns:
            The computed control action (e.g., a gate opening command).
        """
        # This assumes the observation dictionary contains the value to be controlled.
        # A more robust implementation would specify the key.
        process_variable = observation.get('process_variable', 0)
        error = self.setpoint - process_variable

        self._integral += error
        derivative = error - self._previous_error

        output = (self.Kp * error) + (self.Ki * self._integral) + (self.Kd * derivative)

        self._previous_error = error

        # print(f"PID: Setpoint={self.setpoint}, PV={process_variable}, Output={output}")
        return output

    def set_setpoint(self, new_setpoint: float):
        """
        Updates the controller's setpoint.

        Args:
            new_setpoint: The new target value for the system state.
        """
        print(f"PIDController setpoint updated from {self.setpoint} to {new_setpoint}.")
        self.setpoint = new_setpoint
        # Reset integral and derivative terms to prevent sudden jumps in output
        self._integral = 0
        self._previous_error = 0

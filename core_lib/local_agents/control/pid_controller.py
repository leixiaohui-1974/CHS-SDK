"""
A Proportional-Integral-Derivative (PID) Controller with anti-windup.
"""
from core_lib.core.interfaces import Controller, State

class PIDController(Controller):
    """
    A standard PID controller with clamping and anti-windup.

    This controller computes an action based on the error between a setpoint and a
    process variable. It includes an anti-windup mechanism to prevent integral
    term saturation when the actuator is at its limit.
    """

    def __init__(self, Kp: float, Ki: float, Kd: float, setpoint: float,
                 min_output: float, max_output: float, bias: float = 0.0):
        """
        Initializes the PID controller.

        Args:
            Kp: Proportional gain.
            Ki: Integral gain.
            Kd: Derivative gain.
            setpoint: The desired value for the system state.
            min_output: The minimum value for the control action.
            max_output: The maximum value for the control action.
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.min_output = min_output
        self.max_output = max_output
        self.bias = bias

        self._integral = 0
        self._previous_error = 0
        print(
            "PIDController created with Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}, "
            "OutputRange=[{min_output}, {max_output}], Bias={bias}."
            .format(
                Kp=Kp,
                Ki=Ki,
                Kd=Kd,
                setpoint=setpoint,
                min_output=min_output,
                max_output=max_output,
                bias=bias,
            )
        )

    def compute_control_action(self, observation: State, dt: float) -> float:
        """
        Computes the PID control action with anti-windup.

        Args:
            observation: The current state, must contain the key 'process_variable'.
            dt: The time step duration in seconds.

        Returns:
            The computed and clamped control action.
        """
        if dt <= 0:
            return self.min_output # Avoid division by zero

        process_variable = observation.get('process_variable')
        if process_variable is None:
            # Handle cases where the observation is not as expected
            # Returning a neutral or safe value
            return self._previous_output if hasattr(self, '_previous_output') else self.min_output

        error = self.setpoint - process_variable

        # Reset the integral term if the error crosses zero to prevent residual
        # integral energy from driving the actuator past the setpoint.
        if error * self._previous_error < 0:
            self._integral = 0

        # Proportional term
        p_term = self.Kp * error

        # Integral term (with anti-windup logic handled during clamping)
        i_term = self.Ki * self._integral

        # Derivative term
        derivative = (error - self._previous_error) / dt
        d_term = self.Kd * derivative

        # Compute raw, unclamped output
        effective_min = self.min_output - self.bias
        effective_max = self.max_output - self.bias

        output = p_term + i_term + d_term

        # Determine whether integrating the error would push the actuator further
        # into saturation. This logic takes the sign of Ki into account so that
        # controllers configured with inverted gains (e.g., valves that open when
        # the error is negative) can still unwind the integral term.
        should_integrate = True
        control_effect = self.Ki * error

        if output > effective_max and control_effect >= 0:
            should_integrate = False
        elif output < effective_min and control_effect <= 0:
            should_integrate = False

        # Clamp the preliminary output before updating the integral term. This
        # allows the back-calculation step below to pull the integrator toward the
        # saturated output when necessary.
        clamped_delta = max(effective_min, min(output, effective_max))

        if should_integrate:
            self._integral += error * dt
        elif self.Ki != 0:
            # Back-calculation anti-windup: adjust the integrator in the direction
            # of the clamped output so that the stored integral energy reflects the
            # actuator's actual operating point.
            self._integral += (clamped_delta - output) / self.Ki

        # Recompute the output using the (possibly) updated integral state and
        # apply the actuator limits once more to obtain the final command.
        i_term = self.Ki * self._integral
        output = p_term + i_term + d_term
        clamped_delta = max(effective_min, min(output, effective_max))
        clamped_output = self.bias + clamped_delta

        # Update state for next iteration
        self._previous_error = error
        self._previous_output = clamped_output

        return clamped_output

    def set_setpoint(self, new_setpoint: float):
        """
        Updates the controller's setpoint and resets internal states.
        """
        if self.setpoint != new_setpoint:
            print(f"PIDController setpoint updated from {self.setpoint} to {new_setpoint}.")
            self.setpoint = new_setpoint
            # Reset integral and derivative error to prevent output jumps
            self._integral = 0
            self._previous_error = 0 # Or set to current error if smooth transition is needed

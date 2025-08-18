"""
Core Interfaces (Abstract Base Classes)

This module defines the fundamental abstract base classes (ABCs) for the Smart Water Platform.
These interfaces enforce a consistent, modular, and pluggable architecture, ensuring that
different components (simulators, agents, controllers) can interact seamlessly.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

# Type alias for state dictionaries
State = Dict[str, Any]
Parameters = Dict[str, Any]


class Simulatable(ABC):
    """
    An interface for any physical or logical component that can be simulated over time.

    This applies to physical objects (e.g., RiverChannel, Reservoir, Gate) and
    control objects. It ensures that the simulation engine can advance the state
    of any component in a uniform way.
    """

    @abstractmethod
    def step(self, action: Any, dt: float) -> State:
        """
        Advance the simulation of the component by one time step.

        Args:
            action: The control action applied to the component during this step.
            dt: The time duration of the simulation step (e.g., in seconds).

        Returns:
            The new state of the component after the step.
        """
        pass

    @abstractmethod
    def get_state(self) -> State:
        """
        Get the current state of the component.

        Returns:
            A dictionary representing the current state variables.
        """
        pass

    @abstractmethod
    def set_state(self, state: State):
        """
        Set the state of the component.

        Args:
            state: A dictionary representing the new state.
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Parameters:
        """
        Get the model parameters of the component.

        Returns:
            A dictionary of the component's parameters (e.g., Manning's n, gate discharge coefficient).
        """
        pass


class Identifiable(ABC):
    """
    An interface for models whose parameters can be identified (estimated) from data.

    This is typically implemented by Simulatable models that need to be calibrated
    against real-world measurements.
    """

    @abstractmethod
    def identify_parameters(self, data: Any, method: str = 'offline') -> Parameters:
        """
        Perform parameter identification using provided data.

        Args:
            data: The dataset to use for identification (e.g., time series of inputs and outputs).
            method: The identification method ('offline', 'online').

        Returns:
            A dictionary of the newly identified parameters.
        """
        pass


class Agent(ABC):
    """
    An interface for an autonomous agent in the multi-agent system.

    This is the base class for Perception, Control, and Disturbance agents.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    def run(self, current_time: float):
        """
        The main execution loop or entry point for the agent's behavior.

        Args:
            current_time: The current simulation time in seconds.
        """
        pass


class Controller(ABC):
    """
    An interface for a control algorithm module.

    This separates the control logic from the physical object it controls,
    allowing different control strategies (PID, MPC, RL) to be swapped out.
    """

    @abstractmethod
    def compute_control_action(self, observation: State, dt: float) -> Any:
        """
        Compute the next control action based on the current system observation.

        Args:
            observation: The current state or observation of the system to be controlled.
            dt: The time step duration in seconds.

        Returns:
            The computed control action to be sent to the actuator.
        """
        pass


class Disturbance(ABC):
    """
    An interface for a disturbance model.
    """

    @abstractmethod
    def get_disturbance(self, time: float) -> Dict[str, Any]:
        """
        Get the disturbance value(s) at a specific time.

        Args:
            time: The simulation time.

        Returns:
            A dictionary of disturbance values (e.g., {'inflow_change': 0.5}).
        """
        pass

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
    def step(self, action: Any, time_step: float) -> State:
        """
        Advance the simulation of the component by one time step.

        Args:
            action: The control action applied to the component during this step.
            time_step: The time duration of the simulation step (e.g., in seconds).

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

    @abstractmethod
    def set_parameters(self, parameters: Parameters):
        """
        Set the model parameters of the component.

        Args:
            parameters: A dictionary of the new parameters to apply.
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
    def compute_control_action(self, observation: State, time_step: float) -> Any:
        """
        Compute the next control action based on the current system observation.

        Args:
            observation: The current state or observation of the system to be controlled.
            time_step: The time step duration in seconds.

        Returns:
            The computed control action to be sent to the actuator.
        """
        pass


class PhysicalObjectInterface(Simulatable, Identifiable, ABC):
    """
    A specialized interface for a physical object in the water system.

    This combines the `Simulatable` and `Identifiable` interfaces and adds
    a `name` property, as all physical components must have a unique identifier
    within the simulation harness.
    
    Extended to support both discrete simulation and numerical solver modes.
    """

    def __init__(self, name: str, initial_state: State, parameters: Parameters):
        self._name = name
        self._state = initial_state.copy()
        self._params = parameters.copy()
        self._inflow = 0.0  # Transient variable to store inflow from the previous component

    @property
    def name(self) -> str:
        return self._name

    def get_state(self) -> State:
        return self._state.copy()

    def set_state(self, state: State):
        self._state = state

    def get_parameters(self) -> Parameters:
        return self._params.copy()

    def set_parameters(self, parameters: Parameters):
        """
        Updates the model's parameters. It merges the new parameters with the
        existing ones, allowing for partial updates.
        """
        self._params.update(parameters)
        print(f"Parameters for '{self.name}' updated with: {parameters}")

    def set_inflow(self, inflow: float):
        """
        Sets the inflow for the current time step. This is called by the harness.
        """
        self._inflow = inflow

    def identify_parameters(self, data: Any, method: str = 'offline') -> Parameters:
        """
        Default implementation for parameter identification.
        Can be overridden by subclasses for specific models.
        
        Args:
            data: The dataset to use for identification (e.g., time series of inputs and outputs).
            method: The identification method ('offline', 'online').
            
        Returns:
            A dictionary of the newly identified parameters.
            
        Raises:
            NotImplementedError: If parameter identification is required but not implemented.
        """
        # 如果子类没有实现参数识别，应该抛出异常而不是返回当前参数
        raise NotImplementedError(
            f"Parameter identification for {self.name} is not implemented. "
            f"Subclasses must override this method to provide parameter identification functionality."
        )

    @property
    def is_stateful(self) -> bool:
        """
        Returns True if the component stores a volume of water, False otherwise.
        This helps the harness determine how to calculate flow. Stateful components
        (like reservoirs) have their outflow determined by downstream demand, while
        non-stateful components (like pipes or valves) have their outflow determined
        by their inflow and internal properties.
        """
        return False  # Default to False for components like valves, pipes, etc.
    
    # 数值求解器支持（可选实现）
    def get_equations(self, time_step: float, theta: float) -> list:
        """
        Returns the linearized hydraulic equations for this component.
        
        Used by numerical solvers (like NetworkSolver) to build the global
        system of equations. Components that don't support numerical solving
        can return an empty list.
        
        Args:
            time_step: The time step for the numerical integration.
            theta: The implicit/explicit weighting factor (0.0 to 1.0).
            
        Returns:
            A list of equation dictionaries for the numerical solver.
        """
        return []  # Default: no equations (not used in numerical solving)
    
    def link_to_reaches(self, up_obj, down_obj):
        """
        Links this component to upstream and downstream objects.
        
        Used by numerical solvers to establish connectivity in the network.
        Components that don't support numerical solving can ignore this.
        
        Args:
            up_obj: The upstream object/reach.
            down_obj: The downstream object/reach.
        """
        pass  # Default: no linking (not used in numerical solving)


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

# Agent Development Guidelines for the Smart Water Platform

This document provides instructions and conventions for AI agents working on this codebase. The primary goal is to maintain the modular, extensible, and robust architecture established in the initial design.

## 1. Core Architectural Principles

- **Modularity is Paramount**: Every new piece of functionality, whether it's a simulation model, a control algorithm, or a data processing utility, should be designed as a self-contained module.
- **Adhere to Interfaces**: All major components **must** inherit from the appropriate abstract base class defined in `swp/core/interfaces.py`. This is non-negotiable as it ensures the "pluggable" nature of the system.
  - `Simulatable`: For all dynamic models (physical or logical).
  - `Controller`: For all control algorithms.
  - `Agent`: For all autonomous agents.
- **Decouple Components**: Components should not have hard-coded dependencies on each other. Interaction should be mediated by the `SimulationHarness` (for simulation-time coupling) or the `MessageBus` (for inter-agent communication). Avoid direct method calls between components that are not tightly coupled by design.
- **Configuration-Driven**: Do not hard-code parameters or system structures. The `AgentFactory` (`swp/core_engine/agent_factory/factory.py`) is designed to build systems from configuration dictionaries. When adding new components, extend the factory to support them.

## 2. How to Add New Components

### Adding a New Physical Model (e.g., a Pipe)

1.  **Create the class file**: `swp/simulation_identification/physical_objects/pipe.py`.
2.  **Implement the `Simulatable` interface**:
    ```python
    from swp.core.interfaces import Simulatable, State, Parameters

    class Pipe(Simulatable):
        # ... implement all abstract methods: step, get_state, set_state, get_parameters
    ```
3.  **Extend the `AgentFactory`**: Modify `swp/core_engine/agent_factory/factory.py` to recognize and build the `Pipe` model from a configuration block.
4.  **Write a Unit Test**: Create a test file in a new `tests/` directory (e.g., `tests/simulation/test_pipe.py`) to verify the model's behavior in isolation.
5.  **Update Documentation**: Add the `Pipe` model to the `README.md` and any relevant tutorial documents.

### Adding a New Control Algorithm (e.g., MPC)

1.  **Create the class file**: `swp/local_agents/control/mpc_controller.py`.
2.  **Implement the `Controller` interface**:
    ```python
    from swp.core.interfaces import Controller, State

    class MPCController(Controller):
        # ... implement compute_control_action
    ```
3.  **Extend the `AgentFactory`**: Update the factory to support creating the `MPCController` from a configuration block.
4.  **Update the `SimulationHarness` (if necessary)**: The harness may need to be updated to provide the more complex state predictions required by an MPC controller.
5.  **Create an Example**: Add a new example script or extend the existing one to show how the `MPCController` can be used.

## 3. Testing and Verification

- **Run the Example**: Before submitting any changes, always run the `example_simulation.py` script to ensure you have not broken the core integration.
  ```bash
  python3 example_simulation.py
  ```
- **Add Tests**: For any new functionality, add corresponding unit tests. The goal is to build a comprehensive test suite that can be run automatically.

By following these guidelines, we can ensure the platform evolves in a structured and maintainable way, fulfilling its vision as a true "Mother Machine" for intelligent water systems.

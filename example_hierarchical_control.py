"""
End-to-End Example: A Hierarchical Control System

This script demonstrates a two-level hierarchical control system, which is a
core concept of the Smart Water Platform's vision. The control logic has been
updated to be more robust, with a time-aware PID controller that includes
an anti-windup mechanism.

The scenario consists of:
- A low-level control loop (MAS-based):
  - A DigitalTwinAgent publishes a reservoir's state.
  - A LocalControlAgent subscribes to this state and controls a gate using a
    PID controller to meet a setpoint.
- A high-level supervisory loop:
  - A CentralDispatcher agent subscribes to the reservoir's state.
  - Based on a set of rules (e.g., if the water level is too high), it
    dynamically changes the setpoint for the LocalControlAgent.

This showcases a system where a central "brain" can manage the objectives
of local controllers in response to the overall system state.
"""
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.examples.helpers import setup_hierarchical_control_system

def run_hierarchical_control_example():
    """
    Sets up and runs the hierarchical control simulation.
    """
    print("--- Setting up the Hierarchical Control Example ---")

    # 1. Create the central communication channel
    message_bus = MessageBus()

    # 2. Set up the simulation environment
    simulation_dt = 1.0
    components, agents = setup_hierarchical_control_system(message_bus, simulation_dt)

    # 3. Set up and run the simulation
    simulation_config = {'duration': 500, 'dt': simulation_dt}
    harness = SimulationHarness(config=simulation_config)

    for component in components:
        harness.add_component(component)
    for agent in agents:
        harness.add_agent(agent)

    # 4. Define topology and build the harness
    harness.add_connection("reservoir_1", "gate_1")
    harness.build()

    # 5. Run the simulation
    harness.run_mas_simulation()

if __name__ == "__main__":
    run_hierarchical_control_example()

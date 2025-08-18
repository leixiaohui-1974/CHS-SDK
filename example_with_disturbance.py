"""
End-to-End Example: Hierarchical Control with a Disturbance Event

This script demonstrates the resilience of the hierarchical control system
when faced with an external disturbance (a sudden rainfall event).

The scenario is the same as the hierarchical control example, but adds:
- A RainfallAgent that simulates a sudden, heavy inflow into the reservoir
  midway through the simulation.
- A Reservoir model that is now message-aware and subscribes to disturbance
  topics.

This example showcases how the decoupled agents can react to unexpected events
to maintain system stability.
"""
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.simulation_identification.disturbances.rainfall_agent import RainfallAgent
from swp.examples.helpers import setup_hierarchical_control_system


def run_disturbance_example():
    """
    Sets up and runs the hierarchical control simulation with a disturbance.
    """
    print("--- Setting up the Hierarchical Control with Disturbance Example ---")

    # 1. Simulation and Communication Setup
    simulation_dt = 1.0
    simulation_config = {'duration': 1000, 'dt': simulation_dt}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. Set up the core system using the helper
    components, agents = setup_hierarchical_control_system(message_bus, simulation_dt)

    # 3. Create the Disturbance Agent
    RAINFALL_TOPIC = "disturbance.rainfall.inflow"
    rainfall_config = {
        "topic": RAINFALL_TOPIC,
        "start_time": 300,
        "duration": 200,
        "inflow_rate": 150  # A significant inflow
    }
    rainfall_agent = RainfallAgent("rainfall_agent_1", message_bus, rainfall_config)

    # 4. Add all components and agents to the harness
    for component in components:
        # The reservoir needs to be made aware of the disturbance topic
        if hasattr(component, 'disturbance_topics'):
            component.disturbance_topics.append(RAINFALL_TOPIC)
        harness.add_component(component)

    for agent in agents:
        harness.add_agent(agent)
    harness.add_agent(rainfall_agent)

    # 5. Run the MAS simulation
    harness.run_mas_simulation()


if __name__ == "__main__":
    run_disturbance_example()

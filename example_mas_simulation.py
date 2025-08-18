"""
End-to-End Example: A Multi-Agent System (MAS) Simulation

This script demonstrates a true multi-agent, event-driven simulation using the
MessageBus for communication, fully decoupling all components.

The scenario consists of:
- A MessageBus to handle all communication.
- A Reservoir model (a physical component).
- A Gate model that subscribes to an "action" topic on the bus to receive commands.
- A DigitalTwinAgent for the reservoir that publishes the reservoir's state to a "state" topic.
- A LocalControlAgent that subscribes to the "state" topic, runs a PID algorithm,
  and publishes commands to the "action" topic.
- A SimulationHarness running in "MAS mode", which only advances time and calls
  the run/step methods on agents and models.

This architecture is much closer to a real-world distributed control system.
"""
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_mas_example():
    """
    Sets up and runs the event-driven multi-agent simulation.
    """
    print("--- Setting up the MAS Example ---")

    # 1. Create the central communication channel
    message_bus = MessageBus()

    # 2. Define topics for communication
    # Topics are strings that agents use to filter messages.
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"

    # 3. Create the physical components
    # The Gate is now message-bus-aware and subscribes to its action topic.
    reservoir = Reservoir(
        reservoir_id="reservoir_1",
        initial_state={'volume': 15e6, 'water_level': 10.0},
        params={'surface_area': 1.5e6}
    )
    gate = Gate(
        gate_id="gate_1",
        initial_state={'opening': 0.1},
        params={'max_rate_of_change': 0.05, 'discharge_coefficient': 0.6, 'width': 10},
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. Create the Agents
    # The DigitalTwinAgent will publish the reservoir's state.
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # The LocalControlAgent wraps a PID controller and communicates for it.
    pid_controller = PIDController(Kp=0.4, Ki=0.02, Kd=0.1, setpoint=12.0)
    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        action_topic=GATE_ACTION_TOPIC
    )

    # 5. Set up the Simulation Harness in MAS mode
    simulation_config = {'duration': 300, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)

    # Add the physical models (components that are "Simulatable")
    harness.add_component(reservoir)
    harness.add_component(gate)

    # Add the agents
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)

    # 6. Run the MAS simulation
    harness.run_mas_simulation()

if __name__ == "__main__":
    run_mas_example()

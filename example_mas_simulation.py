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
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_mas_example():
    """
    Sets up and runs the event-driven multi-agent simulation.
    """
    print("--- Setting up the MAS Example ---")

    # The harness now creates and owns the message bus
    simulation_config = {'duration': 300, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus # Get a reference to the bus

    # 2. Define topics for communication
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"

    # 3. Create the physical components
    gate_params = {
        'max_rate_of_change': 0.1,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 1.0
    }
    reservoir = Reservoir(
        reservoir_id="reservoir_1",
        initial_state={'volume': 21e6, 'water_level': 14.0}, # Start high
        params={'surface_area': 1.5e6}
    )
    gate = Gate(
        gate_id="gate_1",
        initial_state={'opening': 0.1},
        params=gate_params,
        message_bus=message_bus, # The gate needs the bus to get actions
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. Create the Agents
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # Controller is reverse-acting (opening gate lowers level)
    pid_controller = PIDController(
        Kp=-0.5, Ki=-0.01, Kd=-0.1, setpoint=12.0,
        min_output=0.0, max_output=gate_params['max_opening']
    )

    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level', # Important: tell agent what to look for
        action_topic=GATE_ACTION_TOPIC,
        dt=harness.dt # Agent needs to know the time step
    )

    # 5. Add components and agents to the harness
    harness.add_component(reservoir)
    harness.add_component(gate)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)

    # Define topology
    harness.add_connection("reservoir_1", "gate_1")

    # 6. Build and run the MAS simulation
    harness.build()
    harness.run_mas_simulation()

if __name__ == "__main__":
    run_mas_example()

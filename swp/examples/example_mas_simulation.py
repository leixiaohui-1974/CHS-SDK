"""
End-to-End Example: A Multi-Agent System (MAS) Simulation

This script demonstrates a true multi-agent, event-driven simulation using the
MessageBus for communication, fully decoupling all components.
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

    simulation_config = {'duration': 300, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"

    gate_params = {
        'max_rate_of_change': 0.1,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 1.0
    }
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 21e6, 'water_level': 14.0},
        parameters={'surface_area': 1.5e6}
    )
    gate = Gate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    pid_controller = PIDController(
        Kp=-0.5, Ki=-0.01, Kd=-0.1, setpoint=12.0,
        min_output=0.0, max_output=gate_params['max_opening']
    )

    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=harness.dt
    )

    harness.add_component(reservoir)
    harness.add_component(gate)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)

    harness.add_connection("reservoir_1", "gate_1")

    harness.build()
    harness.run_mas_simulation()

if __name__ == "__main__":
    run_mas_example()

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
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.core_engine.testing.simulation_harness import SimulationHarness

def run_hierarchical_control_example():
    """
    Sets up and runs the hierarchical control simulation.
    """
    print("--- Setting up the Hierarchical Control Example ---")

    # 1. Create the central communication channel
    message_bus = MessageBus()

    # 2. Define topics for communication
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"

    # 3. Create the physical components
    gate_params = {
        'max_rate_of_change': 0.5, # m/s
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 5.0 # meters
    }
    reservoir = Reservoir(
        reservoir_id="reservoir_1",
        initial_state={'volume': 28.5e6, 'water_level': 19.0},
        params={'surface_area': 1.5e6}
    )
    gate = Gate(
        gate_id="gate_1",
        initial_state={'opening': 0.1},
        params=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. Create the Low-Level Agents
    reservoir_twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    gate_twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_gate_1",
        simulated_object=gate,
        message_bus=message_bus,
        state_topic=GATE_STATE_TOPIC
    )

    # The PID controller is now aware of the actuator's physical limits.
    # For a reverse-acting process (opening a gate DECREASES water level),
    # the gains must be negative.
    pid_controller = PIDController(
        Kp=-0.8, Ki=-0.1, Kd=-0.2, setpoint=15.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )

    # Simulation time step must be passed to the agent
    simulation_dt = 1.0

    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level', # Explicitly tell agent what to observe
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC
    )

    # 5. Create the High-Level Agent (The "Brain")
    dispatcher_rules = {
        'flood_threshold': 18.0,
        'normal_setpoint': 15.0,
        'flood_setpoint': 12.0
    }
    dispatcher = CentralDispatcher(
        agent_id="central_dispatcher_1",
        message_bus=message_bus,
        state_subscriptions={'reservoir_level': RESERVOIR_STATE_TOPIC},
        command_topics={'gate1_command': GATE_COMMAND_TOPIC},
        rules=dispatcher_rules
    )

    # 6. Set up and run the simulation
    simulation_config = {'duration': 500, 'dt': simulation_dt}
    harness = SimulationHarness(config=simulation_config)

    harness.add_component(reservoir)
    harness.add_component(gate)

    harness.add_agent(reservoir_twin_agent)
    harness.add_agent(gate_twin_agent)
    harness.add_agent(control_agent)
    harness.add_agent(dispatcher)

    harness.run_mas_simulation()

if __name__ == "__main__":
    run_hierarchical_control_example()

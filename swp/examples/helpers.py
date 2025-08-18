"""
Helper functions for setting up simulation examples.
"""
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.central_coordination.collaboration.message_bus import MessageBus

def setup_hierarchical_control_system(message_bus, simulation_dt):
    """
    A helper function to set up the common components of the hierarchical
    control examples.
    """
    # Define topics for communication
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_STATE_TOPIC = "state.gate.gate_1"
    GATE_ACTION_TOPIC = "action.gate.opening"
    GATE_COMMAND_TOPIC = "command.gate1.setpoint"

    # Create the physical components
    gate_params = {
        'max_rate_of_change': 0.5,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 5.0
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

    # Create the Low-Level Agents
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

    pid_controller = PIDController(
        Kp=-0.8, Ki=-0.1, Kd=-0.2, setpoint=15.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )

    control_agent = LocalControlAgent(
        agent_id="control_agent_gate_1",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_COMMAND_TOPIC,
        feedback_topic=GATE_STATE_TOPIC
    )

    # Create the High-Level Agent
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

    components = [reservoir, gate]
    agents = [reservoir_twin_agent, gate_twin_agent, control_agent, dispatcher]

    return components, agents

"""
End-to-End Example: Branched Network Simulation with Multi-Agent Control

This script demonstrates the platform's capability to handle complex, non-linear
topologies with a full multi-agent control system.

The scenario consists of:
- Reservoir 1 (`res1`) and Reservoir 2 (`res2`)
- Gates `g1` and `g2` controlling their outflows.
- A tributary channel (`trib_chan`) and a main channel (`main_chan`).
- A confluence where `trib_chan` and `g2` flow into `main_chan`.
- A final outflow gate `g3`.

The control system features:
- A CentralDispatcher that sets high-level operational goals.
- Two LocalControlAgents, each with a PID controller, to manage the gates.
- DigitalTwinAgents for all physical components to publish their state.
"""
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher

def run_branched_network_example():
    """
    Sets up and runs the branched network simulation example.
    """
    print("--- Setting up the Branched Network Example with MAS Control ---")

    # 1. Set up the Simulation Harness and Message Bus
    simulation_config = {'duration': 1000, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. Define the physical components
    res1 = Reservoir("res1", {'volume': 15e6, 'water_level': 10.0}, {'surface_area': 1.5e6})
    g1 = Gate("g1", {'opening': 0.1}, {'width': 10, 'max_rate_of_change': 0.1})
    trib_chan = RiverChannel("trib_chan", {'volume': 2e5, 'water_level': 2.0}, {'k': 0.0002})

    res2 = Reservoir("res2", {'volume': 30e6, 'water_level': 20.0}, {'surface_area': 1.5e6})
    g2 = Gate("g2", {'opening': 0.1}, {'width': 15, 'max_rate_of_change': 0.1})

    main_chan = RiverChannel("main_chan", {'volume': 8e5, 'water_level': 8.0}, {'k': 0.0001})
    g3 = Gate("g3", {'opening': 0.5}, {'width': 20}) # Uncontrolled gate

    physical_components = [res1, g1, trib_chan, res2, g2, main_chan, g3]
    for comp in physical_components:
        harness.add_component(comp)

    # 3. Define the network topology
    print("\nDefining network connections...")
    harness.add_connection("res1", "g1")
    harness.add_connection("g1", "trib_chan")
    harness.add_connection("res2", "g2")
    harness.add_connection("trib_chan", "main_chan")
    harness.add_connection("g2", "main_chan")
    harness.add_connection("main_chan", "g3")
    print("Connections defined.")

    # 4. Define the Multi-Agent System
    print("\nDefining the multi-agent control system...")

    # Digital Twin Agents to publish state
    twin_agents = [
        DigitalTwinAgent(agent_id="twin_res1", simulated_object=res1, message_bus=message_bus, state_topic="state.res1.level"),
        DigitalTwinAgent(agent_id="twin_g1", simulated_object=g1, message_bus=message_bus, state_topic="state.g1.opening"),
        DigitalTwinAgent(agent_id="twin_res2", simulated_object=res2, message_bus=message_bus, state_topic="state.res2.level"),
        DigitalTwinAgent(agent_id="twin_g2", simulated_object=g2, message_bus=message_bus, state_topic="state.g2.opening"),
    ]

    # PID controllers for the gates
    pid1 = PIDController(Kp=-0.5, Ki=-0.05, Kd=-0.1, setpoint=12.0, min_output=0.0, max_output=1.0)
    pid2 = PIDController(Kp=-0.4, Ki=-0.04, Kd=-0.1, setpoint=18.0, min_output=0.0, max_output=1.0)

    # Local Control Agents to wrap the PIDs
    lca1 = LocalControlAgent(
        agent_id="lca_g1",
        controller=pid1,
        message_bus=message_bus,
        observation_topic="state.res1.level",
        observation_key="water_level", # Key to extract from the observation message
        action_topic="action.g1.opening",
        dt=simulation_config['dt'],
        command_topic="command.res1.setpoint"
    )
    lca2 = LocalControlAgent(
        agent_id="lca_g2",
        controller=pid2,
        message_bus=message_bus,
        observation_topic="state.res2.level",
        observation_key="water_level", # Key to extract from the observation message
        action_topic="action.g2.opening",
        dt=simulation_config['dt'],
        command_topic="command.res2.setpoint"
    )

    # Central Dispatcher to manage high-level goals
    # Note: The logic for this dispatcher is simplified for this example.
    # A real-world dispatcher would have more complex, coordinated rules.
    dispatcher_rules = {
        'res1_normal_setpoint': 12.0,
        'res2_normal_setpoint': 18.0,
    }
    dispatcher = CentralDispatcher(
        agent_id="central_dispatcher",
        message_bus=message_bus,
        state_subscriptions={
            "res1_level": "state.res1.level",
            "res2_level": "state.res2.level"
        },
        command_topics={
            "res1_command": "command.res1.setpoint",
            "res2_command": "command.res2.setpoint"
        },
        rules=dispatcher_rules
    )

    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        harness.add_agent(agent)
    print("Agent system defined.")

    # 5. Build and run the simulation
    print("\nBuilding simulation harness...")
    harness.build()
    harness.run_mas_simulation()

if __name__ == "__main__":
    run_branched_network_example()

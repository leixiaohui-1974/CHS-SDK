"""
End-to-End Example: Hierarchical Control of a Canal with a Diversion
using the Saint-Venant Equations for high-fidelity physical simulation.

This script demonstrates setting up a simulation with the St. Venant model
and integrating the *perception* layer of an agent-based system.

NOTE: The full control loop is not enabled by default. The St. Venant model
is highly sensitive to its physical and numerical parameters. As configured,
the model becomes numerically unstable when a PID controller is attached.
Achieving stability for a closed-loop simulation requires careful tuning of
the canal's physical properties, the solver's numerical parameters (dt, theta),
and the controller's gains, likely requiring domain expertise in hydraulics.

This example successfully demonstrates:
1. Setting up a network of StVenantReach and GateNode objects.
2. Configuring and running the NetworkSolver.
3. Creating an adapter to make a physical model compatible with agents.
4. Running a DigitalTwinAgent to perceive the state of the physical model
   and publish it to a message bus.
"""
import numpy as np
import time

from swp.core_engine.solver.network_solver import NetworkSolver
from swp.simulation_identification.physical_objects.st_venant_reach import StVenantReach
from swp.simulation_identification.hydro_nodes.gate_node import GateNode
from swp.central_coordination.collaboration.message_bus import MessageBus, Message
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent


# =============================================================================
# Interface Adapter for StVenantReach
# =============================================================================
class ReachTwinAdapter:
    """
    Adapts the StVenantReach object to be compatible with the DigitalTwinAgent,
    which expects a `get_state()` method.
    """
    def __init__(self, reach: StVenantReach):
        self.reach = reach
        self.name = reach.name

    def get_state(self):
        """Returns the state of the reach in a dictionary format."""
        return {
            'water_level': self.reach.H[-1],
            'inflow': self.reach.Q[0],
            'outflow': self.reach.Q[-1]
        }

# =============================================================================
# Centralized Configuration
# =============================================================================
SIMULATION_CONFIG = {
    "duration": 50,
    "dt": 2.0,
    "theta": 1.0,
    "num_points": 25,
    "canal_length": 5000,
    "canal_bottom_width": 20,
    "canal_side_slope_z": 2,
    "canal_manning_n": 0.030,
    "canal_slope": 0.001,
    "initial_water_level": 5.0,
    "normal_inflow": 150, # Note: This high inflow causes unrealistic water levels
    "gate_width": 15.0,
    "gate_discharge_coeff": 0.8,
    "initial_gate_opening": 0.5,
}

def setup_physical_network(config):
    """Creates and connects the physical components and the solver."""
    num_points = config["num_points"]
    initial_h = config["initial_water_level"]
    initial_q = config["normal_inflow"]

    initial_H = np.full(num_points, initial_h, dtype=float)
    initial_Q = np.full(num_points, initial_q, dtype=float)

    upstream_reach = StVenantReach(
        name="upstream_reach", length=config["canal_length"], num_points=num_points,
        bottom_width=config["canal_bottom_width"], side_slope_z=config["canal_side_slope_z"],
        manning_n=config["canal_manning_n"], slope=config["canal_slope"],
        initial_H=initial_H.copy(), initial_Q=initial_Q.copy()
    )

    gate_node = GateNode(
        name="control_gate", width=config["gate_width"],
        discharge_coeff=config["gate_discharge_coeff"]
    )
    gate_node.set_opening(config["initial_gate_opening"])

    downstream_reach = StVenantReach(
        name="downstream_reach", length=config["canal_length"], num_points=num_points,
        bottom_width=config["canal_bottom_width"], side_slope_z=config["canal_side_slope_z"],
        manning_n=config["canal_manning_n"], slope=config["canal_slope"],
        initial_H=(initial_H - 0.1).copy(), initial_Q=initial_Q.copy()
    )

    solver = NetworkSolver(dt=config["dt"], theta=config["theta"])
    solver.add_component(upstream_reach)
    solver.add_component(gate_node)
    solver.add_component(downstream_reach)

    gate_node.upstream_idx = -1
    gate_node.downstream_idx = 0
    gate_node.link_to_reaches(up_obj=upstream_reach, down_obj=downstream_reach)

    solver.add_boundary_condition(
        component=upstream_reach, var='Q', point_idx=0,
        value_func=lambda t: config["normal_inflow"]
    )
    solver.add_boundary_condition(
        component=downstream_reach, var='H', point_idx=-1,
        value_func=lambda t: config["initial_water_level"] - 0.1
    )
    return solver, {"upstream": upstream_reach}, {"gate": gate_node}

def run_perception_test(config):
    """
    Runs a simulation to test the physics solver integrated with the perception
    agent (DigitalTwinAgent).
    """
    print("--- Setting up and running perception layer test ---")
    solver, reaches, nodes = setup_physical_network(config)

    message_bus = MessageBus()
    upstream_reach_adapter = ReachTwinAdapter(reaches["upstream"])

    UPSTREAM_STATE_TOPIC = "state/reach/upstream"
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_upstream",
        simulated_object=upstream_reach_adapter,
        message_bus=message_bus,
        state_topic=UPSTREAM_STATE_TOPIC
    )

    dt = config["dt"]
    num_steps = int(config["duration"] / dt)

    last_received_message = {}
    def message_listener(message: Message):
        nonlocal last_received_message
        last_received_message = message
    message_bus.subscribe(UPSTREAM_STATE_TOPIC, message_listener)

    print("\n--- Running Solver with Perception Agent ---")
    for i in range(num_steps):
        current_time_s = i * dt
        solver.step(current_time_s)
        twin_agent.run(current_time_s)
        print(f"Step {i+1}/{num_steps} | Upstream Level: {reaches['upstream'].H[-1]:.4f} m | "
              f"Listener Received: {last_received_message}")

    print("\n--- Perception layer test complete! ---")

if __name__ == "__main__":
    run_perception_test(SIMULATION_CONFIG)

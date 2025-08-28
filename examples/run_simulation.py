import json
import os
import sys
import pandas as pd
from typing import Dict, Any

# --- Add project root to Python path ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import all necessary classes from the core library ---
# Core
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus
# Physical Components
from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.simulation_identification.physical_objects.valve import Valve
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine
# Agents
from swp.local_agents.io.physical_io_agent import PhysicalIOAgent
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.simulation_identification.disturbances.rainfall_agent import RainfallAgent
from swp.simulation_identification.disturbances.water_use_agent import WaterUseAgent
from swp.mission.agents.csv_inflow_agent import CsvInflowAgent
from swp.mission.agents.emergency_agent import EmergencyAgent
from swp.mission.agents.central_dispatcher_agent import CentralDispatcherAgent
from swp.mission.agents.grid_communication_agent import GridCommunicationAgent
from swp.mission.agents.inflow_forecaster_agent import InflowForecasterAgent
from swp.mission.agents.supervisor_agent import SupervisorAgent
from swp.mission.agents.inflow_agent import InflowAgent
# Controllers
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.custom_controllers import HydropowerController, DirectGateController
# Rules
from swp.central_coordination.dispatch.rules import RULE_SETS

# --- Mappings for dynamic instantiation ---
COMPONENT_MAP = {
    "Canal": Canal, "Gate": Gate, "Reservoir": Reservoir, "Pipe": Pipe, "Valve": Valve, "WaterTurbine": WaterTurbine
}
AGENT_MAP = {
    "PhysicalIOAgent": PhysicalIOAgent, "LocalControlAgent": LocalControlAgent, "DigitalTwinAgent": DigitalTwinAgent,
    "CentralMPCAgent": CentralMPCAgent, "CentralDispatcher": CentralDispatcher, "RainfallAgent": RainfallAgent,
    "WaterUseAgent": WaterUseAgent, "CsvInflowAgent": CsvInflowAgent, "EmergencyAgent": EmergencyAgent,
    "CentralDispatcherAgent": CentralDispatcherAgent, "GridCommunicationAgent": GridCommunicationAgent,
    "InflowForecasterAgent": InflowForecasterAgent, "SupervisorAgent": SupervisorAgent, "InflowAgent": InflowAgent
}
CONTROLLER_MAP = {
    "PIDController": PIDController, "HydropowerController": HydropowerController, "DirectGateController": DirectGateController
}

def load_and_run(config_path: str):
    """
    Loads a simulation config, its linked disturbance config, and runs the simulation.
    """
    with open(config_path, 'r') as f:
        sim_config = json.load(f)

    print(f"--- Running Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {sim_config.get('description', 'No description provided.')} ---")

    harness = SimulationHarness(config=sim_config.get('harness_config', {}))
    bus = harness.message_bus

    # Load disturbance config if specified
    disturbance_agents_config = []
    if 'disturbance_file' in sim_config:
        # Assume disturbance file is relative to the main config file
        base_dir = os.path.dirname(config_path)
        dist_path = os.path.join(base_dir, sim_config['disturbance_file'])
        with open(dist_path, 'r') as f:
            disturbance_config = json.load(f)
            disturbance_agents_config = disturbance_config.get('agents', [])

    all_agents_config = sim_config.get('agents', []) + disturbance_agents_config

    components = {}
    for comp_config in sim_config.get('components', []):
        comp_type = comp_config.pop('type')
        comp_name = comp_config.pop('name')
        if 'inflow_topic' in comp_config: comp_config['message_bus'] = bus
        components[comp_name] = COMPONENT_MAP[comp_type](name=comp_name, **comp_config)
        harness.add_component(components[comp_name])

    for conn in sim_config.get('connections', []):
        harness.add_connection(conn[0], conn[1])

    controllers = {c.pop('name'): CONTROLLER_MAP[c.pop('type')](**c['parameters']) for c in sim_config.get('controllers', [])}

    for agent_config in all_agents_config:
        agent_type = agent_config.pop('type')
        agent_name = agent_config.pop('name')
        cls = AGENT_MAP[agent_type]

        if agent_type == "PhysicalIOAgent":
            for s in agent_config.get('sensors_config', {}).values(): s['obj'] = components[s.pop('component')]
            for a in agent_config.get('actuators_config', {}).values(): a['obj'] = components[a.pop('component')]
        elif agent_type == "LocalControlAgent":
            agent_config['controller'] = controllers[agent_config.pop('controller')]
            if 'dt' not in agent_config: agent_config['dt'] = harness.dt
        elif agent_type == "DigitalTwinAgent":
            agent_config['simulated_object'] = components[agent_config.pop('simulated_object')]
        elif agent_type == "CentralDispatcher":
            agent_config['rules'] = RULE_SETS[agent_config.pop('ruleset')]
        elif agent_type == "CsvInflowAgent":
            agent_config['target_component'] = components[agent_config.pop('target_component')]
        elif agent_type == "CentralMPCAgent":
            # This agent expects its params in a nested 'config' dict
            harness.add_agent(cls(agent_id=agent_name, message_bus=bus, config=agent_config))
            continue

        harness.add_agent(cls(agent_id=agent_name, message_bus=bus, **agent_config))

    print("\nBuilding simulation harness...")
    harness.build()
    print("Running simulation...")
    harness.run_mas_simulation()
    print("Simulation finished.")

    # --- Save standardized output ---
    output_dir = os.path.join(os.path.dirname(config_path), sim_config.get('output_dir', 'output/'))
    os.makedirs(output_dir, exist_ok=True)

    if harness.history:
        flat_history = [{'time': s['time'], **{f"{k}_{sk}": sv for k,v in s.items() if isinstance(v,dict) for sk,sv in v.items()}} for s in harness.history]
        history_df = pd.DataFrame(flat_history)
        history_df.to_csv(os.path.join(output_dir, 'history.csv'), index=False)
        print(f"Standardized history saved to {os.path.join(output_dir, 'history.csv')}")

    if 'plot_config_file' in sim_config:
        plot_config_path = os.path.join(os.path.dirname(config_path), sim_config['plot_config_file'])
        if os.path.exists(plot_config_path):
            import shutil
            shutil.copy(plot_config_path, os.path.join(output_dir, 'plots.json'))
            print(f"Plot config copied to {os.path.join(output_dir, 'plots.json')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_sim_config.json>", file=sys.stderr)
        sys.exit(1)
    load_and_run(sys.argv[1])

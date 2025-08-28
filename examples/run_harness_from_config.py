import json
import os
import sys
import pandas as pd
import numpy as np
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

def run_harness_simulation(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Harness Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {config.get('description', 'No description provided.')} ---")

    harness = SimulationHarness(config=config.get('harness_config', {}))
    bus = harness.message_bus

    json_str = json.dumps(config)
    if 'topics' in config:
        for key, value in config['topics'].items():
            json_str = json_str.replace(f'"{key}"', f'"{value}"')
    config = json.loads(json_str)

    components = {}
    for comp_config in config.get('components', []):
        comp_type = comp_config.pop('type')
        if 'inflow_topic' in comp_config: comp_config['message_bus'] = bus
        components[comp_config['name']] = COMPONENT_MAP[comp_type](**comp_config)
        harness.add_component(components[comp_config['name']])

    for conn in config.get('connections', []):
        harness.add_connection(conn[0], conn[1])

    controllers = {c['name']: CONTROLLER_MAP[c['type']](**c['parameters']) for c in config.get('controllers', [])}

    for agent_config in config.get('agents', []):
        agent_type = agent_config.pop('type')
        agent_name = agent_config.pop('name')
        cls = AGENT_MAP[agent_type]

        # Resolve object references and special parameters
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
        elif agent_type == "CentralMPCAgent":
            # This agent also expects a single 'config' dictionary
            harness.add_agent(cls(agent_id=agent_name, message_bus=bus, config=agent_config))
            continue
        elif agent_type == "CsvInflowAgent":
            agent_config['component'] = components[agent_config.pop('component')]

        harness.add_agent(cls(agent_id=agent_name, message_bus=bus, **agent_config))

    print("\nBuilding simulation harness...")
    harness.build()
    print("Running simulation...")
    harness.run_mas_simulation()
    print("Simulation finished.")

    # Process history and save output
    if harness.history:
        flat_history = [{'time': s['time'], **{f"{k}_{sk}": sv for k,v in s.items() if isinstance(v,dict) for sk,sv in v.items()}} for s in harness.history]
        history_df = pd.DataFrame(flat_history)
        if 'output_settings' in config and 'history_file' in config['output_settings']:
            output_path = config['output_settings']['history_file']
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            history_df.to_csv(output_path, index=False)
            print(f"History saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>")
        sys.exit(1)
    run_harness_simulation(sys.argv[1])

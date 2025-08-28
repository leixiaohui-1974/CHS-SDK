import json
import os
import sys
import pandas as pd
import numpy as np

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Core infrastructure
from swp.core_engine.testing.simulation_harness import SimulationHarness

# Physical Components
from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.simulation_identification.physical_objects.valve import Valve
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine

from typing import Dict, Any

# Agents and Controllers
from swp.core.interfaces import Agent, Controller
from swp.local_agents.io.physical_io_agent import PhysicalIOAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.simulation_identification.disturbances.rainfall_agent import RainfallAgent
from swp.simulation_identification.disturbances.water_use_agent import WaterUseAgent
from swp.mission.agents.csv_inflow_agent import CsvInflowAgent
from swp.mission.agents.emergency_agent import EmergencyAgent
from swp.mission.agents.central_dispatcher_agent import CentralDispatcherAgent
from swp.mission.agents.grid_communication_agent import GridCommunicationAgent


# Helper/Custom classes moved from original scripts
class InflowForecasterAgent(Agent):
    def __init__(self, agent_id, message_bus, topic, forecast_data, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.topic = topic
        self.forecast_data = forecast_data
    def run(self, current_time):
        if current_time == 0:
            print(f"--- InflowForecaster '{self.agent_id}' is publishing a forecast. ---")
            self.bus.publish(self.topic, {'inflow_forecast': self.forecast_data})

class SupervisorAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus, power_target_topic: str, initial_target_mw: float, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.power_target_topic = power_target_topic
        self.initial_target_mw = initial_target_mw
        self._sent = False
    def run(self, current_time: float):
        if not self._sent and current_time >= 0:
            self.bus.publish(self.power_target_topic, {'target_mw': self.initial_target_mw})
            self._sent = True

class InflowAgent(Agent):
    def __init__(self, agent_id: str, message_bus: MessageBus, inflow_topic: str, inflow_rate: float, **kwargs):
        super().__init__(agent_id)
        self.bus = message_bus
        self.inflow_topic = inflow_topic
        self.inflow_rate = inflow_rate
    def run(self, current_time: float):
        self.bus.publish(self.inflow_topic, {'inflow_rate': self.inflow_rate})

class HydropowerController(Controller):
    def __init__(self, head_m: float, **kwargs):
        self.head = head_m
        self.power_target_mw = 0
        self.grid_limit_mw = float('inf')

    def compute_control_action(self, observation: Dict[str, Any], dt: float) -> Dict[str, Any]:
        # Update head from the latest observation from the reservoir
        self.head = observation.get('water_level', self.head)

        # Simple distribution logic
        num_turbines = 6
        target_per_turbine = self.power_target_mw / num_turbines

        # respect grid limit
        if self.power_target_mw > self.grid_limit_mw:
            target_per_turbine = self.grid_limit_mw / num_turbines

        # This is a highly simplified model. A real one would use the lookup table.
        # Power (MW) = eff * rho * g * Q * H / 1e6
        # Q = Power * 1e6 / (eff * rho * g * H)
        eff, rho, g = 0.9, 1000, 9.81
        required_flow_per_turbine = (target_per_turbine * 1e6) / (eff * rho * g * self.head) if self.head > 0 else 0

        actions = {}
        for i in range(num_turbines):
            actions[f'action/turbine/{i+1}'] = {'outflow': required_flow_per_turbine}
        return actions

    def update_setpoint(self, message: Dict[str, Any]):
        if 'target_mw' in message:
            self.power_target_mw = message.get('target_mw', self.power_target_mw)
        if 'limit_mw' in message:
            self.grid_limit_mw = message.get('limit_mw', self.grid_limit_mw)

class DirectGateController(Controller):
    def __init__(self, setpoint=1.0): self.setpoint = setpoint
    def compute_control_action(self, obs, dt): return {'opening': self.setpoint}
    def update_setpoint(self, msg): self.setpoint = msg.get('new_setpoint', self.setpoint)

# Rule sets for the rule-based dispatcher
RULE_SETS = {
    "joint_dispatch_rules": {
        "profiles": {
            "flood": {
                "condition": lambda states: states.get('reservoir', {}).get('water_level', 0) > 22.0,
                "commands": { "hydro_station_control": {"new_setpoint": 400}, "diversion_gate_control": {"new_setpoint": 0.0} }
            },
            "normal": {
                "condition": lambda states: True,
                "commands": { "hydro_station_control": {"new_setpoint": 100}, "diversion_gate_control": {"new_setpoint": 1.0} }
            }
        }
    }
}

# Component and Agent Mappings
COMPONENT_MAP = {
    "Canal": Canal, "Gate": Gate, "Reservoir": Reservoir,
    "Pipe": Pipe, "Valve": Valve, "WaterTurbine": WaterTurbine
}
AGENT_MAP = {
    "PhysicalIOAgent": PhysicalIOAgent,
    "LocalControlAgent": LocalControlAgent,
    "DigitalTwinAgent": DigitalTwinAgent,
    "CentralMPCAgent": CentralMPCAgent,
    "CentralDispatcher": CentralDispatcher,
    "RainfallAgent": RainfallAgent,
    "WaterUseAgent": WaterUseAgent,
    "InflowForecasterAgent": InflowForecasterAgent,
    "SupervisorAgent": SupervisorAgent,
    "InflowAgent": InflowAgent,
    "GridCommunicationAgent": GridCommunicationAgent,
    "CsvInflowAgent": CsvInflowAgent,
    "EmergencyAgent": EmergencyAgent,
    "CentralDispatcherAgent": CentralDispatcherAgent
}
CONTROLLER_MAP = {
    "PIDController": PIDController,
    "HydropowerController": HydropowerController,
    "DirectGateController": DirectGateController
}

def run_harness_simulation(config_path):
    """
    Builds and runs a SimulationHarness-based simulation from a JSON config file.
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Harness Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {config.get('description', 'No description provided.')} ---")

    # 1. Initialize Harness and Message Bus
    harness = SimulationHarness(config=config.get('harness_config', {}))
    bus = harness.message_bus

    # Replace topic placeholders
    json_str = json.dumps(config)
    if 'topics' in config:
        for key, value in config['topics'].items():
            json_str = json_str.replace(f'"{key}"', f'"{value}"')
    config = json.loads(json_str)

    # 2. Instantiate Components
    components = {}
    for comp_config in config.get('components', []):
        comp_type = comp_config.pop('type')
        comp_name = comp_config['name']
        # Pass the bus to components that might need it (e.g., for inflow topics)
        if 'inflow_topic' in comp_config:
            comp_config['message_bus'] = bus

        cls = COMPONENT_MAP.get(comp_type)
        if cls:
            components[comp_name] = cls(**comp_config)
            harness.add_component(components[comp_name])
        else:
            print(f"Warning: Component type '{comp_type}' not found in COMPONENT_MAP.")

    # 3. Add Connections
    for conn in config.get('connections', []):
        harness.add_connection(conn[0], conn[1])

    # 4. Instantiate Controllers
    controllers = {}
    for ctrl_config in config.get('controllers', []):
        ctrl_type = ctrl_config.pop('type')
        ctrl_name = ctrl_config['name']
        cls = CONTROLLER_MAP.get(ctrl_type)
        if cls:
            controllers[ctrl_name] = cls(**ctrl_config['parameters'])
        else:
            print(f"Warning: Controller type '{ctrl_type}' not found in CONTROLLER_MAP.")

    # 5. Instantiate Agents
    for agent_config in config.get('agents', []):
        agent_type = agent_config.pop('type')
        agent_name = agent_config.pop('name')

        # Add bus to all agents' configs
        agent_config['message_bus'] = bus

        # Handle special agent instantiation logic
        if agent_type == "PhysicalIOAgent":
            for s_key, s_val in agent_config.get('sensors_config', {}).items():
                s_val['obj'] = components[s_val.pop('component')]
            for a_key, a_val in agent_config.get('actuators_config', {}).items():
                a_val['obj'] = components[a_val.pop('component')]

        elif agent_type == "LocalControlAgent":
            controller_name = agent_config.pop('controller')
            agent_config['controller'] = controllers[controller_name]
            if 'dt' not in agent_config:
                agent_config['dt'] = harness.dt

        elif agent_type == "DigitalTwinAgent":
            sim_object_name = agent_config.pop('simulated_object')
            agent_config['simulated_object'] = components[sim_object_name]

        cls = AGENT_MAP.get(agent_type)
        if not cls:
            print(f"Warning: Agent type '{agent_type}' not found in AGENT_MAP.")
            continue

        if agent_type in ["WaterUseAgent", "RainfallAgent"]:
            # These agents expect a single 'config' dictionary.
            harness.add_agent(cls(agent_id=agent_name, message_bus=bus, config=agent_config['config']))
            continue # Skip the generic add_agent call at the end

        elif agent_type == "CentralDispatcher":
            ruleset_name = agent_config.pop('ruleset')
            agent_config['rules'] = RULE_SETS[ruleset_name]

        elif agent_type == "CsvInflowAgent":
            component_name = agent_config.pop('component')
            agent_config['component'] = components[component_name]

        harness.add_agent(cls(agent_id=agent_name, **agent_config))

    # 6. Build and Run
    print("\nBuilding simulation harness...")
    harness.build()
    print("Running simulation...")

    # Add scenario events to the harness's event queue
    for event in config.get('scenario', {}).get('events', []):
        if event['type'] == 'set_state':
            target_comp = components[event['target']]
            def action(tc=target_comp, s=event['state']):
                # Create a closure to capture the component and state
                print(f"--- Scenario Event: Setting state for {tc.name} to {s} ---")
                tc.set_state(s)
            harness.add_event(event['time'], action)

    harness.run_mas_simulation()
    print("Simulation finished.")

    # 7. Process and Save Output
    history_df = None
    if harness.history:
        flat_history = []
        for step_data in harness.history:
            flat_step = {'time': step_data['time']}
            for key, value in step_data.items():
                if isinstance(value, dict): # It's a component state
                    for state_key, state_value in value.items():
                        flat_step[f"{key}_{state_key}"] = state_value
            flat_history.append(flat_step)
        history_df = pd.DataFrame(flat_history)

    if history_df is not None and 'output_settings' in config and 'history_file' in config['output_settings']:
        output_path = config['output_settings']['history_file']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        history_df.to_csv(output_path, index=False)
        print(f"History saved to {output_path}")

    # 8. Plotting
    if 'output_settings' in config and 'plot_file' in config['output_settings']:
        # This is a simplified plotting logic for Mission 5.2
        if 'mission_5_2' in config_path:
            history_df = pd.DataFrame(harness.history)
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
            power_cols = [f'turbine_{i+1}_power' for i in range(6)]
            total_power_mw = history_df[power_cols].sum(axis=1) / 1e6
            ax1.plot(history_df['time'], total_power_mw, label='Total Power (MW)')
            ax1.axhline(12.0, color='g', linestyle='--', label='Initial Target')
            ax1.axhline(6.0, color='r', linestyle='--', label='Grid Limit')
            ax1.axvline(150, color='gray', linestyle=':', label='Grid Event')
            ax1.set_ylabel('Power (MW)'); ax1.legend(); ax1.grid(True)

            outflow_cols = [f'turbine_{i+1}_outflow' for i in range(6)]
            history_df[outflow_cols].plot(ax=ax2)
            ax2.set_ylabel('Outflow (m^3/s)'); ax2.legend(); ax2.grid(True)

            plt.xlabel('Time (s)')
            plt.savefig(config['output_settings']['plot_file'])
            print(f"Plot saved to {config['output_settings']['plot_file']}")


    # 9. Verification
    if 'verification' in config and history_df is not None:
        print("\n--- Verification ---")
        ver_config = config['verification']
        ver_type = ver_config['type']

        if ver_type == 'check_final_state':
            comp_name = ver_config['component']
            state_key = ver_config['state_key']
            final_value = history_df.iloc[-1][f"{comp_name}_{state_key}"]
            target_value = ver_config['value']
            tolerance = ver_config['tolerance']

            print(f"Checking if final value of '{comp_name}.{state_key}' ({final_value:.3f}) is close to {target_value:.3f}")
            assert abs(final_value - target_value) < tolerance, \
                f"Verification FAILED: Final value {final_value} is not within {tolerance} of {target_value}"
            print("Verification SUCCESS: Final state is within the expected tolerance.")

        elif ver_type == 'check_max_value':
            history_key = ver_config['history_key']
            max_value = history_df[history_key].max()
            target_value = ver_config['value']
            condition = ver_config['condition']

            print(f"Checking if max value of '{history_key}' ({max_value:.3f}) is {condition} {target_value:.3f}")
            if condition == 'less_than':
                assert max_value < target_value, f"Verification FAILED: Max value {max_value} is not less than {target_value}"
            else:
                print(f"Condition '{condition}' not implemented for check_max_value.")

            print("Verification SUCCESS: Max value meets the condition.")

        else:
            print(f"Verification type '{ver_type}' not implemented.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_file_path = sys.argv[1]
    else:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>")
        sys.exit(1)

    run_harness_simulation(config_file_path)

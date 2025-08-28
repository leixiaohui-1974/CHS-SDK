import json
import os
import sys
import pandas as pd
import numpy as np
import math

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import all necessary classes ---
# Core
from swp.central_coordination.collaboration.message_bus import MessageBus
# Components
from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
# Agents
from swp.local_agents.io.physical_io_agent import PhysicalIOAgent
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent
# Controllers
from swp.local_agents.control.pid_controller import PIDController

# --- Mappings for dynamic instantiation ---
COMPONENT_MAP = {"Canal": Canal, "Gate": Gate}
AGENT_MAP = {
    "PhysicalIOAgent": PhysicalIOAgent, "LocalControlAgent": LocalControlAgent,
    "DigitalTwinAgent": DigitalTwinAgent, "CentralMPCAgent": CentralMPCAgent
}
CONTROLLER_MAP = {"PIDController": PIDController}

def run_simulation_from_config(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {config.get('description', 'No description provided.')} ---")

    bus = MessageBus()

    json_str = json.dumps(config)
    if 'topics' in config:
        for key, value in config['topics'].items():
            json_str = json_str.replace(f'"{key}"', f'"{value}"')
    config = json.loads(json_str)

    components = {c['name']: COMPONENT_MAP[c['type']](**c) for c in config.get('components', [])}
    controllers = {c['name']: CONTROLLER_MAP[c['type']](**c['parameters']) for c in config.get('controllers', [])}

    agents = []
    for ac in config.get('agents', []):
        agent_type = ac.pop('type')
        if agent_type == "PhysicalIOAgent":
            for s in ac.get('sensors_config', {}).values(): s['obj'] = components[s.pop('component')]
            for a in ac.get('actuators_config', {}).values(): a['obj'] = components[a.pop('component')]
        elif agent_type == "LocalControlAgent":
            ac['controller'] = controllers[ac.pop('controller')]
        elif agent_type == "DigitalTwinAgent":
            ac['simulated_object'] = components[ac.pop('simulated_object')]

        # MPC agent has a nested config dict, so we handle it differently
        if agent_type == "CentralMPCAgent":
            agents.append(CentralMPCAgent(message_bus=bus, **ac))
        else:
            agents.append(AGENT_MAP[agent_type](message_bus=bus, **ac))

    sim_settings = config['simulation_settings']
    dt, duration = sim_settings['dt'], sim_settings['duration']
    num_steps = int(duration / dt)
    scenario = config.get('scenario', {})
    events = sorted(scenario.get('events', []), key=lambda e: e['time'])
    history, raw_scenario_values, event_idx = [], [], 0
    inflow = scenario.get('initial_inflow', 0)

    print(f"\nStarting simulation... Duration: {duration}s, Timestep: {dt}s")

    for i in range(num_steps):
        current_time = i * dt
        # Handle noisy injection scenario
        if scenario.get('type') == 'noisy_injection':
            noisy_val = scenario['true_value'] + np.random.normal(0, scenario['noise_std'])
            raw_scenario_values.append(noisy_val)
            components[scenario['component']].set_state({scenario['state_key']: noisy_val})

        # Handle timed events
        if event_idx < len(events) and current_time >= events[event_idx]['time']:
            event = events[event_idx]
            if event['type'] == 'inflow_change': inflow = event['value']
            elif event['type'] == 'publish_command': bus.publish(event['topic'], event['payload'])
            event_idx += 1

        for agent in agents: agent.run(current_time)

        # Manual physics step for Mission 1.1
        if "mission_1_1" in config_path:
            uc, cg = components["upstream_canal"], components["control_gate"]
            cs = uc.get_state()
            gs = cg.step({'upstream_head': cs['water_level'], 'downstream_head': 0, 'control_signal': cg.get_state()['opening']}, dt)
            go = gs['outflow']
            nv = max(0, cs['volume'] + (inflow - go) * dt)
            L, b, z = uc.length, uc.bottom_width, uc.side_slope_z
            c_quad = -nv / L if L > 0 else 0
            nl = (-b + math.sqrt(b**2 - 4*z*c_quad)) / (2*z) if z!=0 else nv/(b*L)
            uc.set_state({'volume': nv, 'water_level': nl, 'outflow': go})

        # Record history
        step_data = {'time': current_time, 'inflow': inflow}
        for name, comp in components.items():
            for key, value in comp.get_state().items(): step_data[f"{name}_{key}"] = value
        history.append(step_data)

    print("\nSimulation finished.")
    # Handle saving and verification if needed...

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_config.json>")
        sys.exit(1)
    run_simulation_from_config(sys.argv[1])

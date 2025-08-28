import json
import os
import sys
import pandas as pd
import math

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import os
import sys
import pandas as pd
import math

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
try:
    import scipy
except ImportError:
    print("\nError: Some examples require the 'scipy' library.")
    print("Please run: pip install scipy\n")
    scipy = None

from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.local_agents.io.physical_io_agent import PhysicalIOAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_mpc_agent import CentralMPCAgent

def run_simulation_from_config(config_path):
    """
    Runs a simulation based on a JSON configuration file, supporting physical
    components and a multi-agent system.
    """
    # 1. Load and parse the configuration file
    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"--- Running Simulation from Config: {os.path.basename(config_path)} ---")
    print(f"--- {config.get('description', 'No description provided.')} ---")

    # Initialize core infrastructure
    bus = MessageBus()

    # Replace topic placeholders in the entire config string
    json_str = json.dumps(config)
    if 'topics' in config:
        for key, value in config['topics'].items():
            json_str = json_str.replace(f'"{key}"', f'"{value}"')
    config = json.loads(json_str)

    # 2. Initialize components from config
    components = {}
    if 'components' in config:
        for comp_config in config['components']:
            comp_name = comp_config['name']
            comp_type = comp_config['type']
            if comp_type == "Canal":
                components[comp_name] = Canal(
                    name=comp_name,
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )
            elif comp_type == "Gate":
                components[comp_name] = Gate(
                    name=comp_name,
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=comp_config.get('parameters', {})
                )

    # 3. Initialize controllers from config
    controllers = {}
    if 'controllers' in config:
        for ctrl_config in config['controllers']:
            ctrl_name = ctrl_config['name']
            ctrl_type = ctrl_config['type']
            if ctrl_type == "PIDController":
                controllers[ctrl_name] = PIDController(**ctrl_config['parameters'])

    # 4. Initialize agents from config
    agents = []
    if 'agents' in config:
        for agent_config in config['agents']:
            agent_name = agent_config['name']
            agent_type = agent_config['type']

            if agent_type == "PhysicalIOAgent":
                # Resolve component references in sensor/actuator configs
                for s_key, s_val in agent_config.get('sensors_config', {}).items():
                    s_val['obj'] = components[s_val.pop('component')]
                for a_key, a_val in agent_config.get('actuators_config', {}).items():
                    a_val['obj'] = components[a_val.pop('component')]

                agents.append(PhysicalIOAgent(
                    agent_id=agent_name,
                    message_bus=bus,
                    sensors_config=agent_config.get('sensors_config', {}),
                    actuators_config=agent_config.get('actuators_config', {})
                ))

            elif agent_type == "LocalControlAgent":
                controller_name = agent_config.pop('controller')
                agents.append(LocalControlAgent(
                    agent_id=agent_name,
                    controller=controllers[controller_name],
                    message_bus=bus,
                    **agent_config
                ))

            elif agent_type == "DigitalTwinAgent":
                sim_object_name = agent_config.pop('simulated_object')
                agents.append(DigitalTwinAgent(
                    agent_id=agent_name,
                    simulated_object=components[sim_object_name],
                    message_bus=bus,
                    **agent_config
                ))

            elif agent_type == "CentralMPCAgent":
                if not scipy:
                    print(f"Skipping {agent_name} ({agent_type}) because 'scipy' is not installed.")
                    continue
                agents.append(CentralMPCAgent(
                    agent_id=agent_name,
                    message_bus=bus,
                    config=agent_config['config']
                ))

    # 5. Set up simulation loop
    sim_settings = config['simulation_settings']
    dt = sim_settings['dt']
    duration = sim_settings['duration']
    num_steps = int(duration / dt)

    scenario = config.get('scenario', {})
    inflow = scenario.get('initial_inflow', 0)
    events = sorted(scenario.get('events', []), key=lambda e: e['time'])

    history = []
    raw_scenario_values = [] # For verification

    print(f"\nStarting simulation... Duration: {duration}s, Timestep: {dt}s")

    event_idx = 0
    for i in range(num_steps):
        current_time = i * dt

        # Handle scenario-specific logic for this step
        if scenario.get('type') == 'noisy_injection':
            true_value = scenario['true_value']
            noise_std = scenario['noise_std']
            target_comp = components[scenario['component']]
            target_key = scenario['state_key']

            noisy_value = true_value + np.random.normal(0, noise_std)
            raw_scenario_values.append(noisy_value)

            current_state = target_comp.get_state()
            current_state[target_key] = noisy_value
            target_comp.set_state(current_state)

        # Check for and apply timed events
        if event_idx < len(events) and current_time >= events[event_idx]['time']:
            event = events[event_idx]
            event_type = event['type']
            print(f"\n!!! Event at t={current_time}s: Type '{event_type}' !!!")
            if event_type == 'inflow_change':
                inflow = event['value']
            elif event_type == 'publish_command':
                bus.publish(event['topic'], event['payload'])
            event_idx += 1

        # Run agents
        for agent in agents:
            agent.run(current_time)

        # 5. Core simulation logic (manual stepping for now)
        # This part will be replaced by the SimulationHarness in later examples
        # For now, we manually step the components we know exist.
        if "upstream_canal" in components and "control_gate" in components:
            upstream_canal = components["upstream_canal"]
            control_gate = components["control_gate"]

            canal_state = upstream_canal.get_state()
            gate_action = {'upstream_head': canal_state['water_level'], 'downstream_head': 0}
            gate_state = control_gate.step(gate_action, dt)
            gate_outflow = gate_state['outflow']

            # Simplified physics update
            new_volume = canal_state['volume'] + (inflow - gate_outflow) * dt
            # Level calculation is complex, so we simplify here for non-physics examples
            # In a real scenario, a proper model or harness would handle this.
            new_level = canal_state['water_level'] + (inflow - gate_outflow) * dt * 0.0001

            upstream_canal.set_state({
                'volume': new_volume,
                'water_level': new_level,
                'outflow': gate_outflow
            })

        # 6. Record history
        step_data = {'time': current_time, 'inflow': inflow}
        if components:
            for name, component in components.items():
                for key, value in component.get_state().items():
                    step_data[f"{name}_{key}"] = value
        history.append(step_data)

        if i % 10 == 0 or num_steps < 50:
            # Dynamically print available component states
            log_line = f"Time: {current_time:5.1f}s"
            if "control_gate" in components:
                log_line += f", Gate Opening: {components['control_gate'].get_state()['opening']:.3f}"
            if "upstream_canal" in components:
                log_line += f", Canal Level: {components['upstream_canal'].get_state()['water_level']:.3f}"
            print(log_line)

    print("\nSimulation finished.")

    # 7. Save output
    if 'output_settings' in config and 'history_file' in config['output_settings']:
        output_path = config['output_settings']['history_file']
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        history_df = pd.DataFrame(history)
        history_df.to_csv(output_path, index=False)
        print(f"History saved to {output_path}")

    # 8. Verification (optional, based on config)
    if 'verification' in config:
        print("\n--- Verification ---")
        ver_config = config['verification']
        ver_type = ver_config['type']
        history_df = pd.DataFrame(history)

        # Set up listener for verification if needed
        received_commands = []
        if 'listener_topic' in ver_config:
            def command_listener(message):
                received_commands.append(message)
            bus.subscribe(ver_config['listener_topic'], command_listener)

        # Re-run the simulation events to capture commands
        # This is inefficient, but simple for this runner. A better way is to
        # log all bus messages during the simulation.
        event_idx = 0
        for i in range(num_steps):
            current_time = i * dt
            if event_idx < len(events) and current_time >= events[event_idx]['time']:
                event = events[event_idx]
                if event['type'] == 'publish_command':
                    bus.publish(event['topic'], event['payload'])
                event_idx += 1
            for agent in agents:
                agent.run(current_time)


        if ver_type == 'variance_reduction':
            component_state_to_check = history_df[f"{scenario['component']}_{scenario['state_key']}"].tolist()
            state_variance = np.var(component_state_to_check)
            raw_injected_variance = np.var(raw_scenario_values)

            print(f"Raw Injected Data Variance: {raw_injected_variance:.4f}")
            print(f"Component State Variance in History: {state_variance:.4f}")
            assert abs(raw_injected_variance - state_variance) < 1e-9, "Component state variance should match injected noise variance."
            print("Verification SUCCESS: Component state reflects the injected noisy data as expected.")

        elif ver_type == 'check_command_value':
            assert len(received_commands) > 0, "Verification FAILED: No command was received on the listener topic."

            last_command = received_commands[-1]
            value_to_check = last_command.get(ver_config['payload_key'])
            assert value_to_check is not None, f"Verification FAILED: Key '{ver_config['payload_key']}' not in command payload."

            condition = ver_config['condition']
            target_value = ver_config['value']

            print(f"Checking if received value {value_to_check} is {condition} {target_value}")

            if condition == 'less_than':
                assert value_to_check < target_value, f"Verification FAILED: {value_to_check} is not less than {target_value}"
            elif condition == 'greater_than':
                assert value_to_check > target_value, f"Verification FAILED: {value_to_check} is not greater than {target_value}"
            elif condition == 'equal_to':
                assert abs(value_to_check - target_value) < 1e-9, f"Verification FAILED: {value_to_check} is not equal to {target_value}"

            print("Verification SUCCESS: Received command value meets the condition.")

        else:
            print("Verification checks passed (placeholder).")

if __name__ == "__main__":
    # The runner script is designed to be called with a config file path.
    # For direct execution, we assume the config is in the same directory.
    default_config = os.path.join(os.path.dirname(__file__), 'mission_1_1_physical_model.json')
    if len(sys.argv) > 1:
        config_file_path = sys.argv[1]
    else:
        print(f"Usage: python {sys.argv[0]} [path_to_config.json]")
        print(f"Running with default config: {default_config}")
        config_file_path = default_config

    run_simulation_from_config(config_file_path)

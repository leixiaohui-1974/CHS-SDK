"""
Debug version of the MAS simulation script with detailed logging.
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

def run_debug_simulation():
    """
    Sets up and runs the multi-agent system simulation with detailed debugging.
    """
    print("=== Setting up Debug MAS Simulation ===")

    # 1. --- Simulation Harness and Message Bus Setup ---
    simulation_config = {'duration': 50, 'dt': 1.0}  # Shorter simulation for debugging
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. --- Communication Topics ---
    RESERVOIR_STATE_TOPIC = "state.reservoir.level"
    GATE_ACTION_TOPIC = "action.gate.opening"
    DEBUG_TOPIC = "debug.info"

    # 3. --- Physical Components ---
    reservoir = Reservoir(
        name="reservoir_1",
        initial_state={'volume': 21e6, 'water_level': 14.0},
        parameters={'surface_area': 1.5e6, 'storage_curve': [[0, 0], [30e6, 20]]}
    )
    
    gate_params = {
        'max_rate_of_change': 0.5,
        'discharge_coefficient': 0.6,
        'width': 10,
        'max_opening': 1.0
    }
    
    # Create a debug wrapper for the gate to log control signals
    class DebugGate(Gate):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.control_signal_log = []
            
        def handle_control_signal(self, message):
            print(f"[DEBUG] Gate received control signal: {message}")
            self.control_signal_log.append((harness.t, message))
            super().handle_control_signal(message)
    
    gate = DebugGate(
        name="gate_1",
        initial_state={'opening': 0.1},
        parameters=gate_params,
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    # 4. --- Agent Components ---
    # Digital Twin Agent for the Reservoir
    twin_agent = DigitalTwinAgent(
        agent_id="twin_agent_reservoir_1",
        simulated_object=reservoir,
        message_bus=message_bus,
        state_topic=RESERVOIR_STATE_TOPIC
    )

    # PID Controller
    pid_controller = PIDController(
        Kp=10.0, Ki=1.0, Kd=0.0,
        setpoint=12.0,
        min_output=0.0,
        max_output=gate_params['max_opening']
    )

    # Local Control Agent for the Gate
    class DebugLocalControlAgent(LocalControlAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.observation_log = []
            self.control_output_log = []
            
        def handle_observation(self, message):
            print(f"[DEBUG] ControlAgent received observation: {message}")
            self.observation_log.append((harness.t, message))
            super().handle_observation(message)
            
        def publish_action(self, control_signal):
            print(f"[DEBUG] ControlAgent publishing action: {control_signal}")
            self.control_output_log.append((harness.t, control_signal))
            super().publish_action(control_signal)
    
    control_agent = DebugLocalControlAgent(
        agent_id="control_agent_gate_1",
        message_bus=message_bus,
        dt=harness.dt,
        target_component="gate_1",
        control_type="gate_control",
        data_sources={"primary_data": RESERVOIR_STATE_TOPIC},
        control_targets={"primary_target": GATE_ACTION_TOPIC},
        allocation_config={},
        controller_config={},
        controller=pid_controller,
        observation_topic=RESERVOIR_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC
    )
    
    # Enable control logging
    control_agent.enable_control_logging(enabled=True, state_topic="control.state.debug", interval=1)

    # 5. --- Debug Message Listeners ---
    def debug_reservoir_state_listener(message):
        print(f"[DEBUG] Reservoir state published: {message}")
    
    def debug_gate_action_listener(message):
        print(f"[DEBUG] Gate action published: {message}")
    
    def debug_control_state_listener(message):
        print(f"[DEBUG] Control state published: {message}")
    
    # Subscribe to all topics for debugging
    message_bus.subscribe(RESERVOIR_STATE_TOPIC, debug_reservoir_state_listener)
    message_bus.subscribe(GATE_ACTION_TOPIC, debug_gate_action_listener)
    message_bus.subscribe("control.state.debug", debug_control_state_listener)

    # 6. --- Harness Final Setup ---
    print(f"\n=== Simulation Configuration ===")
    print(f"Reservoir initial level: {reservoir._state['water_level']:.2f} m")
    print(f"Target water level: {pid_controller.setpoint:.2f} m")
    print(f"Gate initial opening: {gate._state['opening']:.2f}")
    print(f"Simulation duration: {simulation_config['duration']} s")
    print(f"Time step: {simulation_config['dt']} s")
    print(f"===============================\n")
    
    harness.add_component("reservoir_1", reservoir)
    harness.add_component("gate_1", gate)
    harness.add_agent(twin_agent)
    harness.add_agent(control_agent)
    harness.add_connection("reservoir_1", "gate_1")
    harness.build()

    # 7. --- Run Simulation ---
    print("\n=== Running Debug Simulation ===")
    harness.run_mas_simulation()
    print("\n=== Simulation Complete ===")

    # 8. --- Debug Analysis ---
    print("\n=== Debug Analysis ===")
    print(f"Final reservoir water level: {harness.history[-1]['reservoir_1']['water_level']:.2f} m")
    print(f"Final gate opening: {harness.history[-1]['gate_1']['opening']:.3f}")
    
    print(f"\nControlAgent received {len(control_agent.observation_log)} observations")
    print(f"ControlAgent sent {len(control_agent.control_output_log)} control signals")
    print(f"Gate received {len(gate.control_signal_log)} control signals")
    
    # Show first few observations and control signals
    if control_agent.observation_log:
        print("\nFirst 3 observations received by ControlAgent:")
        for i, (t, obs) in enumerate(control_agent.observation_log[:3]):
            print(f"  t={t:.1f}s: {obs}")
    
    if control_agent.control_output_log:
        print("\nFirst 3 control signals sent by ControlAgent:")
        for i, (t, signal) in enumerate(control_agent.control_output_log[:3]):
            print(f"  t={t:.1f}s: {signal}")
    
    if gate.control_signal_log:
        print("\nFirst 3 control signals received by Gate:")
        for i, (t, signal) in enumerate(gate.control_signal_log[:3]):
            print(f"  t={t:.1f}s: {signal}")
    
    # Show water level and gate opening over time
    print("\nWater level and gate opening over time:")
    for i, step in enumerate(harness.history[:10]):  # Show first 10 steps
        if 'reservoir_1' in step and 'gate_1' in step:
            t = step['time']
            level = step['reservoir_1']['water_level']
            opening = step['gate_1']['opening']
            print(f"  t={t:.1f}s: Level={level:.2f}m, Opening={opening:.3f}")

if __name__ == "__main__":
    run_debug_simulation()
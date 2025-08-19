"""
An example of a simulation involving a pump and a valve.

This scenario models a pump transferring water from a lower source reservoir
to a higher destination reservoir through a pipe and a valve.
"""

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.simulation_identification.physical_objects.valve import Valve
from swp.simulation_identification.physical_objects.pump import Pump
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

def run_pump_valve_example():
    """
    Sets up and runs the pump-valve simulation scenario.
    """
    print("--- Setting up the Pump-Valve Simulation Example ---")

    # 1. Create the Message Bus
    message_bus = MessageBus()
    print("MessageBus created.")

    # 2. Create the Simulation Harness
    config = {'duration': 200, 'dt': 1.0}
    harness = SimulationHarness(config)
    print("SimulationHarness created.")

    # 3. Create Components
    # A source reservoir at a lower elevation
    source_reservoir_params = {'surface_area': 10000} # m^2
    source_reservoir_state = {'volume': 50000, 'water_level': 5.0, 'outflow': 0} # m^3, m
    source_reservoir = Reservoir("source_res", source_reservoir_state, source_reservoir_params)

    # A destination reservoir at a higher elevation
    dest_reservoir_params = {'surface_area': 5000} # m^2
    dest_reservoir_state = {'volume': 25000, 'water_level': 5.0, 'outflow': 0} # m^3, m
    dest_reservoir = Reservoir("dest_res", dest_reservoir_state, dest_reservoir_params)

    # A pump to move water from the source
    pump_params = {'max_flow_rate': 5, 'max_head': 20, 'power_consumption_kw': 75} # m^3/s, m, kW
    pump_state = {'status': 0, 'flow_rate': 0, 'power_draw_kw': 0} # Initially off
    pump = Pump("pump1", pump_state, pump_params, message_bus=message_bus, action_topic="action.pump1.status")

    # A pipe connecting the pump to the valve
    pipe_params = {'length': 100, 'diameter': 0.5, 'friction_factor': 0.02}
    pipe_state = {'flow': 0, 'head_loss': 0}
    pipe = Pipe("pipe1", pipe_state, pipe_params)

    # A valve controlling flow into the destination reservoir
    valve_params = {'diameter': 0.5, 'discharge_coefficient': 0.9}
    valve_state = {'opening': 0} # Initially closed
    valve = Valve("valve1", valve_state, valve_params, message_bus=message_bus, action_topic="action.valve1.opening")

    # Add components to the harness
    harness.add_component(source_reservoir)
    harness.add_component(pump)
    harness.add_component(pipe)
    harness.add_component(valve)
    harness.add_component(dest_reservoir)

    # 4. Define Topology (Water Flow)
    harness.add_connection("source_res", "pump1")
    harness.add_connection("pump1", "pipe1")
    harness.add_connection("pipe1", "valve1")
    harness.add_connection("valve1", "dest_res")

    # 5. Build the harness (calculates the execution order)
    harness.build()

    # 6. Run the simulation
    # We will control the pump and valve directly via messages for this example.
    # No complex agents are needed, we just publish messages at specific times.

    num_steps = int(harness.duration / harness.dt)

    for i in range(num_steps):
        current_time = i * harness.dt
        print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

        # Control Logic:
        # - At t=5s, turn the pump on.
        # - At t=10s, open the valve to 50%.
        # - At t=100s, open the valve to 100%.
        # - At t=180s, turn the pump off and close the valve.
        if current_time == 5:
            print("\n>>> COMMAND: Turning pump ON.\n")
            message_bus.publish("action.pump1.status", {'control_signal': 1})

        if current_time == 10:
            print("\n>>> COMMAND: Opening valve to 50%.\n")
            message_bus.publish("action.valve1.opening", {'control_signal': 50})

        if current_time == 100:
            print("\n>>> COMMAND: Opening valve to 100%.\n")
            message_bus.publish("action.valve1.opening", {'control_signal': 100})

        if current_time == 180:
            print("\n>>> COMMAND: Turning pump OFF and closing valve.\n")
            message_bus.publish("action.pump1.status", {'control_signal': 0})
            message_bus.publish("action.valve1.opening", {'control_signal': 0})


        # The harness automatically handles the agent perception/action phase,
        # which in this simplified case is just the message bus processing the
        # messages we published above.
        print("  Phase 1: Triggering agent perception and action cascade.")
        # We don't have agents, but we can manually trigger message processing if needed.
        # In this setup, the components' handlers are called upon publish.

        print("  Phase 2: Stepping physical models with interactions.")
        harness._step_physical_models(harness.dt)

        # Print state summary
        print("  State Update:")
        for cid in harness.sorted_components:
            state_str = ", ".join(f"{k}={v:.2f}" for k, v in harness.components[cid].get_state().items())
            print(f"    {cid}: {state_str}")
        print("")

    print("MAS Simulation finished.")


if __name__ == "__main__":
    run_pump_valve_example()

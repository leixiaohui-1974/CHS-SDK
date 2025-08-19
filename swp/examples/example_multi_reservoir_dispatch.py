"""
Example of the CentralDispatcher coordinating a multi-reservoir system.
"""
import numpy as np
import pandas as pd
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.examples.helpers import setup_logging

def main():
    setup_logging()
    print("--- Setting up the Multi-Reservoir Dispatch Example ---")

    # --- 1. Setup Phase ---
    bus = SimulationHarness(config={'dt': 3600}).message_bus # Use a bus for dispatcher
    dt = 3600

    # Define Rules for the Dispatcher
    rules = {
        "res1_flood_threshold": 5.5, "res1_drought_threshold": 4.5,
        "res1_normal_setpoint": 5.0, "res1_system_flood_setpoint": 4.0, "res1_system_drought_setpoint": 6.0,

        "res2_flood_threshold": 11.0, "res2_drought_threshold": 9.0,
        "res2_normal_setpoint": 10.0, "res2_system_flood_setpoint": 8.0, "res2_system_drought_setpoint": 12.0,
    }

    # Create the Central Dispatcher Agent
    dispatcher = CentralDispatcher(
        agent_id="system_dispatcher", message_bus=bus,
        state_subscriptions={"res1": "state/res1", "res2": "state/res2"},
        command_topics={"res1_control": "command/res1", "res2_control": "command/res2"},
        rules=rules
    )

    # Create Components and their local PID controllers
    res1 = Reservoir("res1", {'volume': 5e6, 'water_level': 5.0}, {'surface_area': 1e6})
    gate1 = Gate("gate1", {'opening': 0.5}, {'width': 5, 'discharge_coeff': 0.8})
    pid1 = PIDController(Kp=0.5, Ki=0.1, Kd=0.05, setpoint=rules["res1_normal_setpoint"], min_output=0, max_output=1)

    res2 = Reservoir("res2", {'volume': 10e6, 'water_level': 10.0}, {'surface_area': 1e6})
    gate2 = Gate("gate2", {'opening': 0.5}, {'width': 8, 'discharge_coeff': 0.8})
    pid2 = PIDController(Kp=0.5, Ki=0.1, Kd=0.05, setpoint=rules["res2_normal_setpoint"], min_output=0, max_output=1)

    # Listen for commands from the dispatcher
    bus.subscribe("command/res1", lambda msg: pid1.set_setpoint(msg['new_setpoint']))
    bus.subscribe("command/res2", lambda msg: pid2.set_setpoint(msg['new_setpoint']))

    # --- 2. Simulation Loop ---
    print("\n--- Running Simulation ---")
    history = []
    inflows = [50, 50, 50, 500, 500, 500, 10, 10, 10, 10] # Inflow scenario for res1

    for t, inflow1 in enumerate(inflows):
        # Publish current states to the bus for the dispatcher
        bus.publish("state/res1", res1.get_state())
        bus.publish("state/res2", res2.get_state())

        # Dispatcher makes a decision
        dispatcher.run(current_time=t*dt)

        # Local controllers compute actions
        action1 = pid1.compute_control_action({'process_variable': res1.get_state()['water_level']}, dt)
        gate1.step({'opening': action1}, dt)

        inflow2 = gate1.get_state()['outflow']
        res1.step({'outflow': inflow2}, dt) # Set outflow based on gate
        res1.set_inflow(inflow1) # Update inflow for next step's balance

        action2 = pid2.compute_control_action({'process_variable': res2.get_state()['water_level']}, dt)
        gate2.step({'opening': action2}, dt)

        inflow3 = gate2.get_state()['outflow']
        res2.step({'outflow': inflow3}, dt)
        res2.set_inflow(inflow2)

        # Record history
        history.append({
            'time': t, 'res1_level': res1.get_state()['water_level'], 'res2_level': res2.get_state()['water_level'],
            'pid1_setpoint': pid1.setpoint, 'pid2_setpoint': pid2.setpoint
        })

    # --- 3. Results ---
    results_df = pd.DataFrame(history)
    print("\n--- Simulation Results ---")
    print(results_df)

if __name__ == "__main__":
    main()

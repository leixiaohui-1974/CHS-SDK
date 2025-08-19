"""
An example of a simulation involving a pump and a valve.
"""
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

    config = {'duration': 200, 'dt': 1.0}
    harness = SimulationHarness(config)
    message_bus = harness.message_bus

    source_reservoir = Reservoir(
        name="source_res",
        initial_state={'volume': 50000, 'water_level': 5.0},
        parameters={'surface_area': 10000}
    )
    dest_reservoir = Reservoir(
        name="dest_res",
        initial_state={'volume': 25000, 'water_level': 5.0},
        parameters={'surface_area': 5000}
    )
    pump = Pump(
        name="pump1",
        initial_state={'status': 0, 'outflow': 0},
        parameters={'max_flow_rate': 5, 'max_head': 20, 'power_consumption_kw': 75},
        message_bus=message_bus,
        action_topic="action.pump1.status"
    )
    pipe = Pipe(
        name="pipe1",
        initial_state={'outflow': 0},
        parameters={'length': 100, 'diameter': 0.5, 'friction_factor': 0.02}
    )
    valve = Valve(
        name="valve1",
        initial_state={'opening': 0},
        parameters={'diameter': 0.5, 'discharge_coefficient': 0.9},
        message_bus=message_bus,
        action_topic="action.valve1.opening"
    )

    harness.add_component(source_reservoir)
    harness.add_component(pump)
    harness.add_component(pipe)
    harness.add_component(valve)
    harness.add_component(dest_reservoir)

    harness.add_connection("source_res", "pump1")
    harness.add_connection("pump1", "pipe1")
    harness.add_connection("pipe1", "valve1")
    harness.add_connection("valve1", "dest_res")

    harness.build()

    num_steps = int(harness.duration / harness.dt)

    for i in range(num_steps):
        current_time = i * harness.dt
        print(f"--- MAS Simulation Step {i+1}, Time: {current_time:.2f}s ---")

        if current_time == 5:
            print("\n>>> COMMAND: Turning pump ON.\n")
            message_bus.publish("action.pump1.status", {'control_signal': 1})

        if current_time == 10:
            print("\n>>> COMMAND: Opening valve to 50%.\n")
            message_bus.publish("action.valve1.opening", {'control_signal': 0.5})

        if current_time == 100:
            print("\n>>> COMMAND: Opening valve to 100%.\n")
            message_bus.publish("action.valve1.opening", {'control_signal': 1.0})

        if current_time == 180:
            print("\n>>> COMMAND: Turning pump OFF and closing valve.\n")
            message_bus.publish("action.pump1.status", {'control_signal': 0})
            message_bus.publish("action.valve1.opening", {'control_signal': 0})

        harness._step_physical_models(harness.dt)

        print("  State Update:")
        for cid in harness.sorted_components:
            state = harness.components[cid].get_state()
            state_str = ", ".join(f"{k}={v:.2f}" for k, v in state.items() if isinstance(v, (int, float)))
            print(f"    {cid}: {state_str}")
        print("")

    print("MAS Simulation finished.")


if __name__ == "__main__":
    run_pump_valve_example()

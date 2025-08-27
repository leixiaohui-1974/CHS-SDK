"""
End-to-End Example: Hierarchical Control of a Canal with a Diversion

This script implements the simulation scenario described by the user.
It features a canal system with a gate, a diversion outlet, and is subject
to several disturbances. The control architecture is hierarchical, with a
central MPC/rule-based dispatcher setting goals for a local PID controller.

The system topology is as follows:
Upstream Inflow -> [Upstream Canal] -> [Diversion] -> [Control Gate] -> [Downstream Canal]

Key Components:
- Physical: Two Canals, one Gate.
- Agents:
  - DigitalTwinAgent for the upstream canal.
  - LocalControlAgent (PID) for the gate.
  - CentralDispatcher (MPC/rules) for high-level setpoint control.
  - ARIMAForecaster for predicting upstream inflow.
  - RainfallAgent to simulate a storm disturbance.
  - WaterUseAgent to simulate outflow from the diversion.

The simulation runs through normal, disturbance, and recovery phases to
test the resilience and effectiveness of the control strategy.
"""
import numpy as np
import matplotlib.pyplot as plt

from swp.core.interfaces import Agent
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.simulation_identification.physical_objects.canal import Canal
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher
from swp.local_agents.prediction.arima_forecaster import ARIMAForecaster
from swp.simulation_identification.disturbances.rainfall_agent import RainfallAgent
from swp.simulation_identification.disturbances.water_use_agent import WaterUseAgent


def run_simulation():
    """
    Sets up and runs the entire canal diversion simulation.
    """
    print("--- Setting up the Canal Diversion Simulation ---")

    # Simulation parameters
    simulation_duration = 400  # s
    simulation_dt = 1.0      # s
    normal_inflow = 150      # m^3/s, baseline inflow for the upstream canal

    # Communication topics and central message bus
    # These need to be defined before the components that might use them.
    UPSTREAM_STATE_TOPIC = "state/canal/upstream"
    UPSTREAM_INFLOW_PREDICTION_TOPIC = "prediction/inflow/upstream"
    UPSTREAM_INFLOW_DATA_TOPIC = "data/inflow/upstream" # For rainfall agents
    GATE_CONTROL_SETPOINT_TOPIC = "command/gate/setpoint"
    GATE_ACTION_TOPIC = "action/gate/opening"
    message_bus = MessageBus()

    # Step 3: Configure Physical Components

    # To have an initial water level of 5m (the normal setpoint), we need to calculate
    # the corresponding initial volume for the trapezoidal canal.
    # V = L * (b*y + z*y^2)
    canal_length = 5000  # m
    canal_bottom_width = 20 # m
    canal_side_slope = 2  # z=2
    initial_water_level = 5.0 # m
    initial_volume = canal_length * (canal_bottom_width * initial_water_level + canal_side_slope * initial_water_level**2)

    upstream_canal = Canal(
        name="upstream_canal",
        initial_state={'volume': initial_volume, 'water_level': initial_water_level, 'outflow': normal_inflow},
        parameters={
            'bottom_width': canal_bottom_width,
            'length': canal_length,
            'slope': 0.001,
            'side_slope_z': canal_side_slope,
            'manning_n': 0.030
        },
        message_bus=message_bus,
        inflow_topic=UPSTREAM_INFLOW_DATA_TOPIC
    )

    control_gate = Gate(
        name="control_gate",
        initial_state={'opening': 0.5}, # Start 50% open
        parameters={
            'max_rate_of_change': 0.1,  # Max 10% change per second
            'discharge_coefficient': 0.8,
            'width': 15,
            'max_opening': 10.0
        },
        message_bus=message_bus,
        action_topic=GATE_ACTION_TOPIC
    )

    downstream_canal = Canal(
        name="downstream_canal",
        initial_state={'volume': initial_volume / 2, 'water_level': initial_water_level / 2, 'outflow': 0},
        parameters={
            'bottom_width': canal_bottom_width,
            'length': canal_length,
            'slope': 0.001,
            'side_slope_z': canal_side_slope,
            'manning_n': 0.030
        }
    )

    physical_components = [upstream_canal, control_gate, downstream_canal]

    # The rest of the setup will go here...
    print("Physical components configured.")

    # Step 4: Configure Agent Components

    # Digital Twin Agent for the upstream canal
    twin_agent_upstream = DigitalTwinAgent(
        agent_id="twin_agent_upstream",
        simulated_object=upstream_canal,
        message_bus=message_bus,
        state_topic=UPSTREAM_STATE_TOPIC
    )

    # PID Control Agent for the gate
    pid_controller = PIDController(
        Kp=-0.5, Ki=-0.1, Kd=-0.05,
        setpoint=5.0,  # Initial setpoint
        min_output=0.0,
        max_output=control_gate.get_parameters()['max_opening']
    )
    gate_control_agent = LocalControlAgent(
        agent_id="gate_control_agent",
        controller=pid_controller,
        message_bus=message_bus,
        observation_topic=UPSTREAM_STATE_TOPIC,
        observation_key='water_level',
        action_topic=GATE_ACTION_TOPIC,
        dt=simulation_dt,
        command_topic=GATE_CONTROL_SETPOINT_TOPIC
    )

    # Central Dispatcher Agent
    # For this example, we use rule-based logic as a stand-in for a full MPC implementation
    # The logic is provided by the prompt's parameters.
    dispatcher_rules = {
        'flood_threshold': 6.0,
        'normal_setpoint': 5.0,
        'emergency_setpoint': 4.0,
        'prediction_horizon': 10 # This would be used by a real MPC
    }
    central_dispatcher = CentralDispatcher(
        agent_id="central_dispatcher",
        message_bus=message_bus,
        state_subscriptions={'upstream_level': UPSTREAM_STATE_TOPIC},
        forecast_subscriptions={'inflow_forecast': UPSTREAM_INFLOW_PREDICTION_TOPIC},
        command_topics={'gate_setpoint': GATE_CONTROL_SETPOINT_TOPIC},
        rules=dispatcher_rules
    )

    # Forecasting Agent
    # In a real scenario, this would be trained on historical data.
    # The agent will build its own history by listening to the topic.
    forecaster_config = {
        "observation_topic": UPSTREAM_STATE_TOPIC,
        "observation_key": "inflow",
        "forecast_topic": UPSTREAM_INFLOW_PREDICTION_TOPIC,
        "history_size": 100,
        "arima_order": (1, 1, 0),
        "forecast_steps": 10,
        "refit_interval": 20 # Refit model every 20 steps
    }
    rainfall_forecaster = ARIMAForecaster(
        agent_id="rainfall_forecaster",
        message_bus=message_bus,
        config=forecaster_config
    )

    # Agent to provide the constant baseline inflow
    inflow_source_config = {
        "topic": UPSTREAM_INFLOW_DATA_TOPIC,
        "start_time": 0,
        "duration": simulation_duration,
        "inflow_rate": normal_inflow
    }
    inflow_source_agent = RainfallAgent(
        agent_id="inflow_source_agent",
        message_bus=message_bus,
        config=inflow_source_config
    )

    # Rainfall Disturbance Agent
    rainfall_config = {
        "topic": UPSTREAM_INFLOW_DATA_TOPIC,
        "start_time": 100,
        "duration": 100,
        "inflow_rate": 50.0
    }
    rainfall_agent = RainfallAgent(
        agent_id="rainfall_agent",
        message_bus=message_bus,
        config=rainfall_config
    )

    # Water Use Disturbance Agent
    water_use_agent = WaterUseAgent(
        agent_id="water_use_agent",
        canal_to_affect=upstream_canal,
        start_time=0,
        duration=400, # Active for the whole simulation
        diversion_rate=20.0, # m^3/s
        dt=simulation_dt
    )

    agent_components = [
        twin_agent_upstream,
        gate_control_agent,
        central_dispatcher,
        rainfall_forecaster,
        inflow_source_agent,
        rainfall_agent,
        water_use_agent
    ]

    print("Agent components configured.")

    # Step 5: Build and Run the Simulation
    harness = SimulationHarness(
        config={'duration': simulation_duration, 'dt': simulation_dt}
    )

    for component in physical_components:
        harness.add_component(component)

    for agent in agent_components:
        harness.add_agent(agent)

    # Define the physical topology of the water network
    harness.add_connection("upstream_canal", "control_gate")
    harness.add_connection("control_gate", "downstream_canal")

    # Build and run the simulation
    print("\n--- Running Simulation ---")
    harness.build()
    results = harness.run_mas_simulation()
    print("--- Simulation Complete ---")

    # The final step will be to plot these results
    return results

def plot_results(results):
    """
    Processes and plots the results from the simulation.
    """
    print("\n--- Plotting Simulation Results ---")

    # Extract data series
    time = results['time']
    upstream_level = results['upstream_canal']['water_level']
    gate_opening = results['control_gate']['opening']
    upstream_inflow = results['upstream_canal']['inflow']
    upstream_outflow = results['upstream_canal']['outflow']

    # We need to get the setpoint history from the PID controller's internal log
    pid_history = results['agents']['gate_control_agent']['history']
    setpoints = [h.get('setpoint', np.nan) for h in pid_history]

    fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
    fig.suptitle('Canal Diversion Simulation Results', fontsize=16)

    # Plot 1: Upstream Water Level and PID Setpoint
    axs[0].plot(time, upstream_level, label='Upstream Water Level (m)', color='b')
    axs[0].plot(time, setpoints, label='PID Setpoint (m)', color='r', linestyle='--')
    axs[0].axvline(x=100, color='grey', linestyle=':', label='Disturbance Start')
    axs[0].axvline(x=200, color='grey', linestyle=':', label='Disturbance End')
    axs[0].set_ylabel('Water Level (m)')
    axs[0].legend()
    axs[0].grid(True)
    axs[0].set_title('Upstream Canal Water Level vs. Control Setpoint')

    # Plot 2: Gate Opening
    axs[1].plot(time, gate_opening, label='Gate Opening (%)', color='g')
    # Convert opening to percentage for the label
    axs[1].fill_between(time, 0, gate_opening, color='g', alpha=0.2)
    axs[1].set_ylabel('Opening (%)')
    axs[1].legend()
    axs[1].grid(True)
    axs[1].set_title('Control Gate Opening')

    # Plot 3: Inflows and Outflows
    axs[2].plot(time, upstream_inflow, label='Total Inflow (m³/s)', color='c')
    axs[2].plot(time, upstream_outflow, label='Natural Outflow (m³/s)', color='m')
    # Note: The diversion outflow is not explicitly logged, but it's reflected in the inflow
    axs[2].set_xlabel('Time (s)')
    axs[2].set_ylabel('Flow Rate (m³/s)')
    axs[2].legend()
    axs[2].grid(True)
    axs[2].set_title('Upstream Canal Flow Dynamics')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Save the figure instead of showing it to be compatible with non-GUI environments
    output_filename = "simulation_results.png"
    plt.savefig(output_filename)
    print(f"Results plot saved to {output_filename}")


if __name__ == "__main__":
    simulation_results = run_simulation()
    if simulation_results:
        plot_results(simulation_results)

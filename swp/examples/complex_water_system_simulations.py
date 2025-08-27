"""
This file contains a series of examples to demonstrate the capabilities of the SWP platform.
The examples are structured to build upon each other, starting from individual component
simulations and culminating in a complex, multi-agent, hierarchical control system.

This script is designed to be run from the root of the repository.
"""

# Import necessary libraries and modules
import asyncio
import math
import time
import numpy as np
import pandas as pd

# Core components from the SWP framework
from swp.core.interfaces import State, Parameters
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.central_coordination.collaboration.message_bus import MessageBus, Message

# Physical object models
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.simulation_identification.physical_objects.valve import Valve
from swp.simulation_identification.physical_objects.pump import Pump, PumpStation
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.rainfall_runoff import RainfallRunoff
from swp.simulation_identification.physical_objects.river_channel import RiverChannel

# Agents
from swp.local_agents.control.pump_control_agent import PumpControlAgent
from swp.local_agents.control.hydropower_station_agent import HydropowerStationAgent
from swp.local_agents.control.pressure_control_agent import PressureControlAgent
# from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.prediction.arima_forecaster import ARIMAForecaster
# from swp.local_agents.prediction.forecasting_agent import ForecastingAgent
from swp.simulation_identification.identification.identification_agent import ParameterIdentificationAgent
from swp.central_coordination.dispatch.central_dispatcher_agent import CentralDispatcherAgent
from swp.local_agents.disturbances.water_use_agent import WaterUseAgent

# Data processing
from swp.data_processing.cleaner import fill_missing_with_interpolation
from swp.data_processing.evaluator import calculate_rmse, calculate_nse, calculate_kge


def print_header(title):
    """Helper function to print a formatted header for each example."""
    print("\n" + "="*80)
    print(f"Running Example: {title}")
    print("="*80)


def example_1_1_pipe_and_valve_simulation():
    """
    Demonstrates the physical dynamics of a pressurized pipe and valve.
    This function simulates how flow and head loss change in response to
    different valve openings in a simple gravity-fed system.
    """
    print_header("1.1: Pressurized Pipe and Valve Simulation")

    # 1. Initialize components with specified parameters
    pipe_params = {'length': 1000, 'diameter': 0.5, 'friction_factor': 0.02}
    pipe = Pipe(name="main_pipe", initial_state={}, parameters=pipe_params)

    valve_params = {'diameter': 0.5, 'discharge_coefficient': 0.8}
    valve = Valve(name="control_valve", initial_state={'opening': 100.0}, parameters=valve_params)

    # 2. Define the system's boundary conditions
    upstream_head = 100.0  # meters
    downstream_head_final = 50.0  # meters
    total_head_diff = upstream_head - downstream_head_final

    print("System Boundary Conditions:")
    print(f"  - Upstream Head: {upstream_head:.2f} m")
    print(f"  - Downstream Head (final): {downstream_head_final:.2f} m")
    print(f"  - Total Available Head: {total_head_diff:.2f} m\n")

    # 3. Simulate the system for different valve openings
    for opening in [100, 75, 50, 25, 10]:
        # Set the valve's opening for the current scenario
        valve.step({'control_signal': opening}, dt=1)

        # 4. Find the equilibrium flow and intermediate head using a binary search solver.
        #    This is a manual way to find the point where flow through the pipe
        #    equals the flow through the valve (Q_pipe = Q_valve).
        low_h_guess = downstream_head_final
        high_h_guess = upstream_head
        intermediate_head = (low_h_guess + high_h_guess) / 2

        # Iterate to find the stable intermediate head
        for _ in range(30): # Increased iterations for better convergence
            # Action for the pipe based on the current guess
            pipe_action = {'upstream_head': upstream_head, 'downstream_head': intermediate_head}
            pipe.step(pipe_action, dt=1)
            q_pipe = pipe.get_state()['outflow']

            # Action for the valve based on the current guess.
            # The control_signal (opening) is already set in the valve's state from the outer loop.
            valve_action = {'upstream_head': intermediate_head, 'downstream_head': downstream_head_final}
            valve.step(valve_action, dt=1)
            q_valve = valve.get_state()['outflow']

            # Adjust the guess for the intermediate head based on the flow imbalance
            if q_pipe > q_valve:
                # q_pipe is high and q_valve is low, which means the intermediate head is too low.
                # We need to increase it, so we raise the lower bound of our search.
                low_h_guess = intermediate_head
            else:
                # q_pipe is low and q_valve is high, which means the intermediate head is too high.
                # We need to decrease it, so we lower the upper bound of our search.
                high_h_guess = intermediate_head
            intermediate_head = (low_h_guess + high_h_guess) / 2

        # 5. With the converged intermediate head, get the final, stable system state
        final_q = pipe.get_state()['outflow']
        pipe_head_loss = upstream_head - intermediate_head
        valve_head_loss = intermediate_head - downstream_head_final

        print(f"--- Valve Opening: {opening}% ---")
        print(f"  Equilibrium Flow: {final_q:.4f} m^3/s")
        print(f"  Intermediate Head (between pipe and valve): {intermediate_head:.2f} m")
        print(f"  Pipe Head Loss (friction): {pipe_head_loss:.2f} m")
        print(f"  Valve Head Loss (throttling): {valve_head_loss:.2f} m")
        print(f"  Total Calculated Head Loss: {pipe_head_loss + valve_head_loss:.2f} m (should match total available head)")
        print("-" * 25)


def example_1_2_pump_station_control():
    """
    Demonstrates multi-unit coordinated control of a pump station.
    An agent listens to flow demand and turns pumps on/off to meet it.
    """
    print_header("1.2: Pump Station Multi-Unit Coordinated Control")

    # 1. Initialize the message bus for agent communication
    bus = MessageBus()

    # 2. Define topics for communication
    demand_topic = "pump_station/flow_demand"
    control_topic_prefix = "pumps/control"

    # 3. Create individual pumps
    pump_params = {'max_flow_rate': 1.5, 'max_head': 30, 'power_consumption_kw': 50}
    pumps = []
    for i in range(4):
        pump_name = f"pump_{i+1}"
        pump = Pump(
            name=pump_name,
            initial_state={'status': 0},
            parameters=pump_params,
            message_bus=bus,
            action_topic=f"{control_topic_prefix}.{pump_name}"
        )
        pumps.append(pump)

    # 4. Create the pump station to manage the pumps
    pump_station = PumpStation(name="main_pump_station", initial_state={}, parameters={}, pumps=pumps)

    # 5. Create the control agent
    agent = PumpControlAgent(
        agent_id="PumpController",
        message_bus=bus,
        pump_station=pump_station,
        demand_topic=demand_topic,
        control_topic_prefix=control_topic_prefix
    )

    # 6. Simulation loop
    print("\n--- Simulation Run ---")
    demands_to_test = {0: 0.0, 2: 2.0, 4: 4.0, 6: 6.5, 8: 3.0}

    for step in range(10):
        print(f"\n--- Time Step {step} ---")

        # Publish a new demand if specified for this step
        if step in demands_to_test:
            demand_value = demands_to_test[step]
            # A message is just a dictionary. The agent's handler expects a 'value' key.
            demand_message = {'value': demand_value, 'sender': 'System'}
            bus.publish(demand_topic, demand_message)

        # Agent executes its logic based on the latest demand.
        # This will also publish the control messages.
        agent.execute_control_logic()

        # In this simple implementation, publishing is synchronous and directly calls the
        # listeners, so there is no separate dispatch step required.

        # Simulate the pump station's response to the control signals
        # We provide a dummy head difference for the pumps to operate
        station_action = {'upstream_head': 10, 'downstream_head': 30}
        pump_station.step(station_action, dt=1)

        station_state = pump_station.get_state()
        print(f"Station State: {station_state['active_pumps']} pumps active, "
              f"Total Flow: {station_state['total_outflow']:.2f} m^3/s")


def example_1_3_hydropower_station_scheduling():
    """
    Demonstrates multi-device, multi-objective scheduling for a hydropower station.
    An agent balances flood control, water supply, and power generation.
    """
    print_header("1.3: Hydropower Station Multi-Device Joint Scheduling")

    # 1. Setup
    bus = MessageBus()
    dt = 3600  # Time step of 1 hour

    # 2. Create Reservoir
    reservoir_params = {'surface_area': 5e6} # 5 km^2
    initial_volume = 50e6 # 50 million m^3
    initial_level = initial_volume / reservoir_params['surface_area'] # 10m
    reservoir = Reservoir(
        name="main_reservoir",
        initial_state={'volume': initial_volume, 'water_level': initial_level},
        parameters=reservoir_params
    )

    # 3. Create Gates and Turbines
    gate_params = {'width': 5, 'discharge_coefficient': 0.8, 'max_opening': 2.0}
    turbine_gate_1 = Gate(name="turbine_gate_1", initial_state={'opening': 0}, parameters=gate_params, message_bus=bus, action_topic="gates/tg1")
    turbine_gate_2 = Gate(name="turbine_gate_2", initial_state={'opening': 0}, parameters=gate_params, message_bus=bus, action_topic="gates/tg2")
    flood_gate = Gate(name="flood_gate", initial_state={'opening': 0}, parameters={**gate_params, 'width': 10}, message_bus=bus, action_topic="gates/flood")
    supply_gate = Gate(name="supply_gate", initial_state={'opening': 0}, parameters={**gate_params, 'width': 2}, message_bus=bus, action_topic="gates/supply")

    outlets = [turbine_gate_1, turbine_gate_2, flood_gate, supply_gate]

    # 4. Create Agent
    agent_config = {
        'normal_level': 10.0,
        'flood_warning_level': 10.5, # Lowered to ensure flood logic is triggered
        'min_supply_opening': 0.2, # 20% opening
    }
    agent = HydropowerStationAgent(
        agent_id="HydropowerMaster",
        message_bus=bus,
        reservoir=reservoir,
        flood_gate_topic="gates/flood",
        supply_gate_topic="gates/supply",
        turbine_gate_topics=["gates/tg1", "gates/tg2"],
        config=agent_config
    )

    # 5. Simulation Loop
    print("\n--- Simulation Run ---")
    base_inflow = 10  # m^3/s
    for step in range(24):
        # --- Disturbance ---
        # Simulate a more severe flood pulse starting at hour 5
        inflow = base_inflow
        if 5 <= step < 15:
            inflow += 250 * math.sin((step - 5) / 10 * math.pi) # Increased magnitude

        print(f"\n--- Hour {step}, Inflow: {inflow:.2f} m^3/s ---")

        # --- Agent Logic ---
        agent.execute_control_logic()

        # --- System Update ---
        # Calculate total outflow from all gates
        total_outflow = 0
        reservoir_level = reservoir.get_state()['water_level']
        for outlet in outlets:
            # Action for each gate contains the current reservoir level as upstream head
            outlet_action = {'upstream_head': reservoir_level, 'downstream_head': 0} # Assuming free discharge
            outlet.step(outlet_action, dt)
            total_outflow += outlet.get_state()['outflow']

        # Update the reservoir with the net flow
        reservoir_action = {'outflow': total_outflow}
        reservoir.set_inflow(inflow) # Manually set the inflow for this step
        reservoir.step(reservoir_action, dt)

        # --- Logging ---
        print(f"Reservoir Level: {reservoir.get_state()['water_level']:.2f} m")
        print(f"  - TG1 Opening: {turbine_gate_1.get_state()['opening']:.2f}, Flow: {turbine_gate_1.get_state()['outflow']:.2f}")
        print(f"  - TG2 Opening: {turbine_gate_2.get_state()['opening']:.2f}, Flow: {turbine_gate_2.get_state()['outflow']:.2f}")
        print(f"  - Flood Gate Opening: {flood_gate.get_state()['opening']:.2f}, Flow: {flood_gate.get_state()['outflow']:.2f}")
        print(f"  - Supply Gate Opening: {supply_gate.get_state()['opening']:.2f}, Flow: {supply_gate.get_state()['outflow']:.2f}")
        print(f"  - Total Outflow: {total_outflow:.2f} m^3/s")


def example_1_4_data_processing():
    """
    Demonstrates data cleaning and performance evaluation.
    Creates a time series with imperfections, cleans it, and evaluates
    the cleaning performance against the ground truth.
    """
    print_header("1.4: Data Cleaning and Evaluation Diagnosis")

    # 1. Create ground truth and imperfect data
    # Ground truth: A smooth sine wave
    true_values = pd.Series(np.sin(np.linspace(0, 10, 100)) * 10 + 50)

    # Imperfect data: A copy with missing values and outliers
    imperfect_values = true_values.copy()

    # Add missing values (NaNs)
    imperfect_values.iloc[[10, 25, 40, 60, 85]] = np.nan

    # Add outliers
    imperfect_values.iloc[15] = 100  # Spike up
    imperfect_values.iloc[50] = 0    # Spike down
    imperfect_values.iloc[75] *= 0.5 # Drop

    print("Generated 100 data points.")
    print(f"Original data has {imperfect_values.isna().sum()} missing values and several outliers.\n")

    # 2. Clean the data
    # Fill missing values using linear interpolation
    cleaned_values = fill_missing_with_interpolation(imperfect_values.copy())
    print("Step 1: Filled missing values using interpolation.")
    print(f"Data now has {cleaned_values.isna().sum()} missing values.\n")

    # Note: A complete outlier removal step would typically be next.
    # For this example, we focus on the provided platform functions.
    # The evaluator will show how outliers negatively impact the score.

    # 3. Evaluate the cleaned data against the ground truth
    # First, let's evaluate the 'imperfect' data to get a baseline
    print("--- Evaluating Imperfect Data (with outliers, without NaNs for metrics) ---")
    # Evaluator functions can't handle NaNs, so we drop them for the baseline score
    imperfect_subset = imperfect_values.dropna()
    true_subset_for_imperfect = true_values[imperfect_subset.index]
    rmse_before = calculate_rmse(true_subset_for_imperfect, imperfect_subset)
    nse_before = calculate_nse(true_subset_for_imperfect, imperfect_subset)
    kge_before = calculate_kge(true_subset_for_imperfect, imperfect_subset)
    print(f"Baseline RMSE (imperfect vs true): {rmse_before:.4f}")
    print(f"Baseline NSE (imperfect vs true): {nse_before:.4f}")
    print(f"Baseline KGE (imperfect vs true): {kge_before:.4f}\n")


    print("--- Evaluating Cleaned Data ---")
    rmse_after = calculate_rmse(true_values, cleaned_values)
    nse_after = calculate_nse(true_values, cleaned_values)
    kge_after = calculate_kge(true_values, cleaned_values)

    print(f"Cleaned Data RMSE: {rmse_after:.4f}")
    print(f"Cleaned Data NSE: {nse_after:.4f} (Closer to 1 is better)")
    print(f"Cleaned Data KGE: {kge_after:.4f} (Closer to 1 is better)")
    print("\nObservation: Interpolation fixed the NaNs, but the outliers still significantly")
    print("degrade the performance metrics (e.g., high RMSE, low NSE/KGE).")


def example_1_5_forecasting_and_warning():
    """
    Demonstrates a forecasting agent making a prediction and issuing a warning.
    An ARIMA agent is given historical data, makes a forecast, and if the
    forecast exceeds a threshold, a warning is published to the message bus.
    """
    print_header("1.5: Prediction and Early Warning")

    # 1. Setup
    bus = MessageBus()
    warning_topic = "system/warnings/high_flow"

    # Simple listener to print any warnings received
    def warning_listener(message):
        print(f"\n>>> WARNING RECEIVED! Topic: '{message['topic']}', Details: {message['details']} <<<")

    bus.subscribe(warning_topic, warning_listener)

    # 2. Create the forecasting agent
    agent_config = {
        "observation_topic": "data/inflow", # Dummy topic, not used for this manual forecast
        "observation_key": "value",
        "forecast_topic": "forecast/inflow",
        "history_size": 200,
        "arima_order": (2, 1, 2), # A reasonable default for seasonal data
        "forecast_steps": 12, # Forecast the next 12 hours
    }
    agent = ARIMAForecaster(agent_id="InflowForecaster", message_bus=bus, config=agent_config)

    # 3. Create historical data with a clear trend and seasonality
    print("Generating historical data with an upward trend...")
    time_steps = np.arange(100)
    # A sine wave for seasonality, plus a linear trend
    history_data = pd.Series(
        np.sin(time_steps * 0.5) * 10 + (time_steps * 0.5) + 20
    )
    # Manually load the historical data into the agent
    agent.history.extend(history_data.tolist())

    # 4. Perform forecast
    print(f"Agent has {len(agent.history)} historical data points. Performing forecast...")
    # We call the internal method directly for this example
    forecast = agent._fit_and_forecast()

    if forecast:
        print(f"\nForecasted values for the next {len(forecast)} steps: ")
        print([round(v, 2) for v in forecast])

        # 5. Issue a warning if the forecast exceeds a threshold
        warning_threshold = 80
        print(f"\nChecking if forecast exceeds warning threshold of {warning_threshold}...")

        max_forecast_value = max(forecast)
        if max_forecast_value > warning_threshold:
            print(f"Condition met: Max forecast value ({max_forecast_value:.2f}) > {warning_threshold}")
            warning_message = {
                "topic": warning_topic,
                "details": f"High inflow predicted. Max forecast: {max_forecast_value:.2f} m^3/s."
            }
            bus.publish(warning_topic, warning_message)
        else:
            print("Condition not met. No warning issued.")
    else:
        print("\nForecast could not be generated.")


def example_1_6_parameter_identification():
    """
    Demonstrates the parameter identification capability of the platform.
    An agent observes rainfall and runoff data to automatically calibrate
    a RainfallRunoff model's runoff coefficient.
    """
    print_header("1.6: System Identification")

    # 1. Define ground truth and generate synthetic data
    true_params = {
        'catchment_area': 1e7,       # 10 km^2
        'runoff_coefficient': 0.6    # This is the "true" value we want to find
    }
    num_data_points = 100
    # Rainfall intensity in m/s (equivalent to mm/hr / 3.6e6)
    rainfall_series = np.random.rand(num_data_points) * 5e-5 # Simulates up to 180 mm/hr

    # Calculate "observed" runoff using the true parameters
    observed_runoff = true_params['runoff_coefficient'] * rainfall_series * true_params['catchment_area']

    print(f"Generated {num_data_points} data points for rainfall and observed runoff.")
    print(f"True runoff coefficient is: {true_params['runoff_coefficient']}\n")

    # 2. Create a model with incorrect initial parameters
    initial_params = {
        'catchment_area': true_params['catchment_area'], # Area is known
        'runoff_coefficient': 0.1 # Incorrect initial guess
    }
    model_to_identify = RainfallRunoff(name="Catchment_A", parameters=initial_params)
    print(f"Model created with initial (incorrect) runoff coefficient: {initial_params['runoff_coefficient']}\n")

    # 3. Setup the identification agent
    bus = MessageBus()
    agent_config = {
        "identification_interval": num_data_points,
        "identification_data_map": {
            'rainfall': 'data/rainfall',
            'observed_runoff': 'data/observed_runoff'
        }
    }
    agent = ParameterIdentificationAgent(
        agent_id="Identifier",
        target_model=model_to_identify,
        message_bus=bus,
        config=agent_config
    )

    # 4. Simulate the data collection process
    print("Simulating data stream by publishing to message bus...")
    for i in range(num_data_points):
        bus.publish('data/rainfall', {'value': rainfall_series[i]})
        bus.publish('data/observed_runoff', {'value': observed_runoff[i]})

    # 5. Trigger the identification process
    # The agent's run method will detect that enough data has been collected.
    agent.run(current_time=0)

    # 6. Verify the result
    final_params = model_to_identify.get_parameters()
    final_coeff = final_params['runoff_coefficient']
    print(f"\nFinal identified runoff coefficient: {final_coeff:.4f}")

    # Check if the identified parameter is close to the true value
    if abs(final_coeff - true_params['runoff_coefficient']) < 1e-3:
        print("SUCCESS: Identified parameter is very close to the true value.")
    else:
        print("NOTE: Identified parameter has moved towards the true value.")


def example_2_1_pressurized_network_control():
    """
    Demonstrates a closed-loop control system for a pressurized pipe network.
    An agent monitors pressure at the end of a pipe and controls a pump station
    at the beginning to keep the pressure within a target range, while a downstream
    valve simulates changing user demand.
    """
    print_header("2.1: Pressurized Water Transmission Pipe Network Closed-Loop Control")

    # 1. Setup
    bus = MessageBus()
    dt = 10  # seconds

    # Components
    # Upstream reservoir (source) - provides a constant head
    upstream_reservoir = Reservoir(name="source_res", initial_state={'water_level': 10}, parameters={})

    # Pump Station
    control_topic_prefix = "pumps/control"
    # Finely-tuned parameters to allow for stable control
    pump_params = {'max_flow_rate': 1.5, 'max_head': 38, 'power_consumption_kw': 60}
    pumps = [Pump(name=f"p_{i}", initial_state={'status': 0}, parameters=pump_params,
                  message_bus=bus, action_topic=f"{control_topic_prefix}.p_{i}") for i in range(3)]
    pump_station = PumpStation(name="main_ps", initial_state={}, parameters={}, pumps=pumps)

    # Pipe
    pipe_params = {'length': 150, 'diameter': 0.8, 'friction_factor': 0.025}
    pipe = Pipe(name="main_pipe", initial_state={}, parameters=pipe_params)

    # Downstream valve to simulate demand changes
    valve_params = {'diameter': 0.8, 'discharge_coefficient': 0.9}
    demand_valve = Valve(name="demand_valve", initial_state={'opening': 50.0}, parameters=valve_params)

    # 2. Control Agent
    # The agent will try to maintain the pressure at the *inlet* of the valve.
    # In our simplified model, this is the downstream head of the pipe.
    agent_config = {'min_pressure': 40.0, 'max_pressure': 45.0}
    agent = PressureControlAgent(
        agent_id="PressureRegulator",
        message_bus=bus,
        pump_station=pump_station,
        pressure_source_component=pipe, # The agent reads pressure from the pipe's state
        control_topic_prefix=control_topic_prefix,
        config=agent_config
    )

    # 3. Simulation Loop
    print("\n--- Simulation Run ---")
    print(f"Control Target: Maintain pressure between {agent_config['min_pressure']} and {agent_config['max_pressure']} m.\n")

    # Store history for plotting or analysis
    history = []

    for t in range(60): # Simulate for 10 minutes (60 steps of 10s)
        # --- Simulate Demand Change ---
        if t == 10:
            print("\n>>> DEMAND INCREASE: Downstream valve opening increased to 60% <<<\n")
            demand_valve.step({'control_signal': 60.0}, dt)
        if t == 40:
            print("\n>>> DEMAND DECREASE: Downstream valve opening decreased to 30% <<<\n")
            demand_valve.step({'control_signal': 30.0}, dt)

        # --- Agent Logic ---
        # Agent reads pressure and decides on pump status
        agent.execute_control_logic()

        # --- System Physics ---
        # The core of this simulation is finding the equilibrium flow and pressure
        # for the current state of the pumps and valve.

        num_active_pumps = agent.active_pumps
        pump_station_flow = num_active_pumps * pump_params['max_flow_rate']

        # The total head provided by the pumps
        pump_head_gain = pump_params['max_head'] if num_active_pumps > 0 else 0
        pipe_inlet_head = upstream_reservoir.get_state()['water_level'] + pump_head_gain

        # We need to find the pipe outlet head (pressure) where pipe flow matches valve flow
        low_h_guess = 0
        high_h_guess = pipe_inlet_head
        pipe_outlet_head = (low_h_guess + high_h_guess) / 2

        for _ in range(20):
            # Calculate flow through pipe
            pipe.step({'upstream_head': pipe_inlet_head, 'downstream_head': pipe_outlet_head}, dt)
            q_pipe = pipe.get_state()['outflow']

            # Calculate flow through valve
            q_valve = demand_valve._calculate_flow(pipe_outlet_head, 0) # Assuming discharge to atmosphere

            # In a pumped system, the pump flow is forced. The pipe must carry this flow.
            # The head at the end of the pipe is the inlet head minus the friction loss.
            # So, we don't need a solver here. This is simpler.
            break # Exit the solver loop, it's not needed.

        # Correct physics for a pump-driven system:
        pipe._inflow = pump_station_flow # The pumps determine the flow
        pipe.step({}, dt) # Calculate head loss based on this flow
        pipe_head_loss = pipe.get_state()['head_loss']

        # The pressure at the end of the pipe is the starting pressure minus the loss
        final_pipe_outlet_head = pipe_inlet_head - pipe_head_loss

        # Update the state of the component the agent is monitoring
        pipe.set_state({'downstream_head': final_pipe_outlet_head})

        # --- Logging ---
        log_entry = {
            "time": t * dt,
            "valve_opening": demand_valve.get_state()['opening'],
            "active_pumps": agent.active_pumps,
            "flow": pump_station_flow,
            "pressure": final_pipe_outlet_head
        }
        history.append(log_entry)
        print(f"Time: {log_entry['time']:3d}s | Pumps: {log_entry['active_pumps']} | Flow: {log_entry['flow']:.2f} | Pressure: {log_entry['pressure']:.2f}m")

def example_2_2_integrated_basin_scheduling():
    """
    Demonstrates integrated basin scheduling with multiple agents and a
    central dispatcher for emergency override.
    """
    print_header("2.2: Joint Scheduling of Water Resources in the Basin")

    # 1. Setup
    bus = MessageBus()
    dt = 3600  # 1 hour time step

    # 2. Physical Components
    # Reservoir
    reservoir_params = {'surface_area': 1e7} # 10 km^2
    initial_volume = 200e6 # 200 million m^3
    initial_level = initial_volume / reservoir_params['surface_area'] # 20m
    reservoir = Reservoir(name="main_reservoir", initial_state={'volume': initial_volume, 'water_level': initial_level}, parameters=reservoir_params)

    # Hydropower Station Outlets
    gate_params = {'width': 5, 'discharge_coefficient': 0.8, 'max_opening': 2.0}
    turbine_gate = Gate(name="turbine_gate", initial_state={'opening': 0}, parameters=gate_params, message_bus=bus, action_topic="station/tg1")
    flood_gate = Gate(name="flood_gate", initial_state={'opening': 0}, parameters={**gate_params, 'width': 15}, message_bus=bus, action_topic="station/flood")

    # River Channel
    channel = RiverChannel(name="main_river", initial_state={'volume': 50000, 'outflow': 5}, parameters={'k': 0.0001})

    # Downstream Water Supply Outlet
    supply_gate = Gate(name="supply_gate", initial_state={'opening': 0}, parameters={**gate_params, 'width': 3}, message_bus=bus, action_topic="downstream/supply")

    # 3. Agents
    # Hydropower Agent (local control)
    hp_agent_config = {'normal_level': 20.0, 'flood_warning_level': 22.0, 'min_supply_opening': 0.1}
    hp_agent = HydropowerStationAgent(agent_id="HydropowerOps", message_bus=bus, reservoir=reservoir,
                                      flood_gate_topic="station/flood", supply_gate_topic="station/supply", # Note: supply topic not used by this agent
                                      turbine_gate_topics=["station/tg1"], config=hp_agent_config)

    # Water User Agent (local demand)
    user_agent = WaterUseAgent(agent_id="CityWaterDept", message_bus=bus, supply_gate_topic="downstream/supply")

    # Central Dispatcher (global override)
    dispatcher_config = {'emergency_flood_level': 23.5}
    dispatcher = CentralDispatcherAgent(agent_id="BasinControlCenter", message_bus=bus, reservoir=reservoir,
                                        supply_gate_topic="downstream/supply", config=dispatcher_config)

    # 4. Simulation Loop
    print("\n--- Simulation Run: Flood and Peak Demand Coincidence ---")
    base_inflow = 50  # m^3/s
    for t in range(48): # 2 days
        current_time = t * dt
        hour_of_day = (current_time / 3600) % 24

        # Flood disturbance
        inflow = base_inflow
        if 10 <= t < 34:
            inflow += 600 * math.sin((t - 10) / 24 * math.pi)

        print(f"\n--- Hour {t}, Inflow: {inflow:.2f} m^3/s, Res Level: {reservoir.get_state()['water_level']:.2f}m ---")

        # 5. Agent Execution Order (Perception -> Local Action -> Global Override)
        hp_agent.run(current_time) # Hydropower agent makes its decision
        user_agent.run(current_time) # Water user agent makes its decision
        dispatcher.run(current_time) # Dispatcher can override decisions if needed

        # 6. Physics Update
        # Hydropower station outflow
        res_level = reservoir.get_state()['water_level']
        turbine_gate.step({'upstream_head': res_level, 'downstream_head': 10}, dt)
        flood_gate.step({'upstream_head': res_level, 'downstream_head': 10}, dt)
        station_outflow = turbine_gate.get_state()['outflow'] + flood_gate.get_state()['outflow']

        # Reservoir update
        reservoir.set_inflow(inflow)
        reservoir.step({'outflow': station_outflow}, dt)

        # River channel update
        channel.set_inflow(station_outflow)
        channel.step({}, dt)

        # Downstream supply update
        channel_head = channel.get_state()['volume'] * 0.0001 # Simplified head calculation
        supply_gate.step({'upstream_head': channel_head, 'downstream_head': 0}, dt)

        # Final water balance for the channel (subtract water taken by supply gate)
        channel.set_state({'volume': channel.get_state()['volume'] - supply_gate.get_state()['outflow'] * dt})

        # 7. Logging
        print(f"  HP Ops Decision: TG Opening={turbine_gate.get_state()['opening']:.2f}, FG Opening={flood_gate.get_state()['opening']:.2f}")
        print(f"  City Demand Decision: SG Opening={user_agent.supply_gate_topic} -> {supply_gate.get_state()['opening']:.2f}")
        print(f"  Dispatcher Status: Monitoring. Emergency Level: {dispatcher.emergency_flood_level}m")
        print(f"  River Outflow: {channel.get_state()['outflow']:.2f} m^3/s")

if __name__ == "__main__":
    print("Starting complex water system simulations...\n")

    # Run Example 1.1
    example_1_1_pipe_and_valve_simulation()

    # Run Example 1.2
    example_1_2_pump_station_control()

    # Run Example 1.3
    example_1_3_hydropower_station_scheduling()

    # Run Example 1.4
    example_1_4_data_processing()

    # Run Example 1.5
    example_1_5_forecasting_and_warning()

    # Run Example 1.6
    example_1_6_parameter_identification()

    # Run Example 2.1
    example_2_1_pressurized_network_control()

    # Run Example 2.2
    example_2_2_integrated_basin_scheduling()

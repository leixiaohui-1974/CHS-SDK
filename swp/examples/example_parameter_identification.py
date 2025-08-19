"""
Example demonstrating the use of the ParameterIdentificationAgent to
auto-calibrate a model's parameters.
"""
import numpy as np
import pandas as pd
from swp.simulation_identification.physical_objects.rainfall_runoff import RainfallRunoff
from swp.simulation_identification.identification.identification_agent import ParameterIdentificationAgent
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.data_processing.evaluator import calculate_rmse
from swp.examples.helpers import setup_logging

def main():
    setup_logging()
    print("--- Setting up the Parameter Identification Example ---")

    # 1. Ground Truth and Synthetic Data
    # We define a 'true' runoff coefficient that our agent will try to find.
    true_coeff = 0.75
    catchment_area = 2000
    np.random.seed(0)
    rainfall_series = np.random.rand(20) * 0.01
    # The "real" observed runoff is generated using the true coefficient.
    observed_runoff_series = true_coeff * rainfall_series * catchment_area

    # 2. Setup Model with wrong initial parameter
    # We start with a bad guess for the runoff coefficient.
    initial_wrong_coeff = 0.10
    model_params = {'catchment_area': catchment_area, 'runoff_coefficient': initial_wrong_coeff}
    runoff_model = RainfallRunoff(name="catchment_to_calibrate", parameters=model_params)

    print(f"Initial runoff coefficient: {runoff_model.get_parameters()['runoff_coefficient']:.2f}")

    # 3. Evaluate initial model performance (should be poor)
    initial_simulated_runoff = initial_wrong_coeff * rainfall_series * catchment_area
    initial_rmse = calculate_rmse(initial_simulated_runoff, observed_runoff_series)
    print(f"Initial RMSE: {initial_rmse:.4f}")

    # 4. Setup the Identification Agent
    bus = MessageBus()
    agent_config = {
        "identification_interval": 20, # Run identification after 20 data points
        "identification_data_map": {
            "rainfall": "data/rainfall",
            "observed_runoff": "data/observed_runoff"
        }
    }
    id_agent = ParameterIdentificationAgent(
        agent_id="id_agent_1",
        target_model=runoff_model,
        message_bus=bus,
        config=agent_config
    )

    # 5. Simulate data streaming and run the agent
    print("\n--- Simulating data stream and running identification ---")
    for i in range(len(rainfall_series)):
        bus.publish("data/rainfall", {'value': rainfall_series[i]})
        bus.publish("data/observed_runoff", {'value': observed_runoff_series[i]})

    # Run the agent to trigger the identification process
    id_agent.run(current_time=1)

    # 6. Evaluate final model performance (should be much better)
    final_coeff = runoff_model.get_parameters()['runoff_coefficient']
    print(f"\nFinal identified runoff coefficient: {final_coeff:.2f}")

    final_simulated_runoff = final_coeff * rainfall_series * catchment_area
    final_rmse = calculate_rmse(final_simulated_runoff, observed_runoff_series)
    print(f"Final RMSE: {final_rmse:.4f}")

    assert final_rmse < initial_rmse
    assert abs(final_coeff - true_coeff) < 1e-3

    print("\nExample finished successfully. The agent correctly identified the parameter.")

if __name__ == "__main__":
    main()

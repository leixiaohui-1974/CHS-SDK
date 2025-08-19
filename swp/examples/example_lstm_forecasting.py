"""
Example demonstrating the use of the LSTMFlowForecaster.
"""
import numpy as np
import matplotlib.pyplot as plt
from swp.local_agents.prediction.lstm_forecaster import LSTMFlowForecaster
from swp.central_coordination.collaboration.message_bus import MessageBus
from swp.examples.helpers import setup_logging

def main():
    setup_logging()
    print("--- Setting up the LSTM Forecasting Example ---")

    # 1. Generate synthetic time series data
    total_points = 250
    time_steps = np.linspace(0, 40 * np.pi, total_points)
    # A sine wave with an upward trend and some noise
    data = 20 * np.sin(time_steps) + 0.01 * time_steps**2 + np.random.randn(total_points) * 5 + 100

    # 2. Setup the agent
    bus = MessageBus()
    config = {
        "observation_topic": "data/inflow",
        "observation_key": "value",
        "forecast_topic": "forecast/inflow",
        "history_size": 200,
        "refit_interval": 200, # Train once with the full history
        "input_window_size": 40,
        "output_window_size": 10,
        "epochs": 100, # A reasonable number of epochs for a demo
        "learning_rate": 0.005,
        "hidden_size": 64,
        "num_layers": 2
    }
    lstm_agent = LSTMFlowForecaster("lstm_forecaster_1", bus, config)

    # 3. Feed historical data to the agent
    training_data = data[:config["history_size"]]
    for value in training_data:
        lstm_agent.handle_observation_message({'value': value})

    # 4. Run the agent to train the model
    print("\n--- Training LSTM Model ---")
    # The agent's run method will trigger training as new_obs >= refit_interval
    lstm_agent.run(current_time=1)
    print("--- Training Complete ---")

    # 5. Generate a forecast
    print("\n--- Generating Forecast ---")
    forecast = lstm_agent._forecast()
    print(f"Forecasted values: {np.round(forecast, 2)}")

    # 6. Plot the results for visualization
    plt.figure(figsize=(15, 7))

    # Plot historical data used for training
    plt.plot(range(len(training_data)), training_data, label='Training Data', color='blue')

    # Plot the true future values
    true_future_range = range(len(training_data), len(training_data) + config["output_window_size"])
    true_future_values = data[len(training_data) : len(training_data) + config["output_window_size"]]
    plt.plot(true_future_range, true_future_values, 'go-', label='True Future Values')

    # Plot the forecasted values
    plt.plot(true_future_range, forecast, 'ro--', label='LSTM Forecast')

    plt.title("LSTM Time Series Forecasting", fontsize=16)
    plt.xlabel("Time Steps")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()

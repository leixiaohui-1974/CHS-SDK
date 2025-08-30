# Canal Model Comparison Example

This example demonstrates and compares four different canal models:
1.  **Level-Pool Model:** A simple routing model where the water surface is assumed to be horizontal.
2.  **Integral Model:** A model where outflow is a linear function of the total volume of water in the canal.
3.  **Integral-Delay Model:** An integral model that includes a time delay to represent wave propagation.
4.  **Integral-Delay with Zero-Point Model:** An integral-delay model that includes a zero-point offset for the volume.

## Simulation Setup

The simulation consists of a single canal reach between an upstream and a downstream reservoir. A gate at the upstream end of the canal controls the inflow. A PID controller is used to adjust the gate opening to maintain a constant water level in the canal.

Each of the four models is run as a separate scenario, and the results are plotted together for comparison.

## Running the Example

To run the example, execute the following command from the root of the repository:

```bash
python3 docs/examples/canal_control/canal_model_comparison/run_model_comparison.py
```

This will run all four scenarios, save the results to CSV files in the current directory, and generate a plot named `model_comparison_results.png` showing the water level dynamics for each model.

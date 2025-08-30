# Canal Model Comparison Example

This example demonstrates and compares four different simplified models for simulating water flow in a canal reach.

## Description

The simulation is set up with a single canal reach between two reservoirs with fixed water levels. An upstream gate controls the inflow to the canal. The simulation starts in a steady state, and then a step change is introduced in the upstream gate opening to observe the dynamic response of the canal's water level.

This example runs the same scenario four times, each time using a different mathematical model for the canal. The results are then plotted together for comparison.

## Canal Models

The four canal models compared are:

1.  **Integral Model (`Canal`)**: This is the simplest model, representing the canal as a single reservoir where the water level is the integral of the net flow (inflow - outflow). It does not account for wave travel time. The governing equation is:
    `dh/dt = (1/A) * (q_in - q_out)`
    where `h` is water level, `A` is the surface area, `q_in` is inflow, and `q_out` is outflow.

2.  **Integral-Delay Model (`IntegralDelayCanal`)**: This model adds a time delay to the inflow, which represents the travel time of water from the upstream end to the downstream end. The outflow is a delayed version of the inflow. This is a common and simple way to model the transport delay in canals. The model is:
    `q_out(t) = q_in(t - τ)`
    `dh/dt = K * (q_in(t) - q_out(t))`

3.  **Integral-Delay-Zero Model (`IntegralDelayZeroCanal`)**: This is an extension of the integral-delay model that adds a "zero" to the transfer function. This term can help to better approximate the initial response of the canal to a change in flow. The outflow is a function of the delayed inflow and its rate of change:
    `q_out(t) = q_in(t - τ) + Tz * d/dt(q_in(t - τ))`

4.  **Linear Reservoir Model (`RiverChannel`)**: This model, often used for river reaches, represents the canal as a series of linear reservoirs. The outflow of each reservoir is proportional to the storage. This model can capture some of the diffusive effects of wave propagation. The governing equation for a single segment is:
    `dS/dt = q_in - q_out`
    `S = k * q_out`
    where `S` is storage and `k` is the storage constant.

## How to Run

To run the example, execute the following command from the root of the repository:

```bash
python examples/canal_model/canal_model_comparison/run_model_comparison.py
```

This will run all four simulations, save the results to CSV files in the current directory, and generate a plot `model_comparison_results.png` showing the water level responses of the different models.

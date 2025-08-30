# Examples for Parameter Identification

This directory contains examples demonstrating the parameter identification capabilities for various digital twin models. Each subdirectory focuses on identifying a specific parameter for a specific model, showcasing how the system can self-calibrate based on simulated "observed" data.

## How the Examples Work

Each example follows a similar pattern:

1.  **True vs. Twin**: Two versions of a model are created.
    *   A **"true"** model with a known, correct parameter (e.g., a known pipe roughness). This model is used to generate realistic, dynamic data for the simulation.
    *   A **"twin"** model which is the digital twin we want to calibrate. It starts with an initial, incorrect guess for the parameter.
2.  **Perception**: A set of `DigitalTwinAgent` instances observe the state of the "true" system (e.g., water levels, flows, gate openings) and publish this data to the message bus.
3.  **Identification**: A `ParameterIdentificationAgent` is configured to listen to this "observed" data. It also monitors the inputs and outputs of the "twin" model.
4.  **Optimization**: When enough data is collected, the `ParameterIdentificationAgent` calls the `.identify_parameters()` method on the twin model. This method uses an optimization algorithm (`scipy.optimize.minimize`) to find the parameter value that best explains the observed data.
5.  **Update**: A `ModelUpdaterAgent` listens for the results of the identification and automatically applies the new, corrected parameter to the twin model.

## Examples

### 1. Reservoir Storage Curve (`01_reservoir_storage_curve`)
*   **Goal**: Identify the non-linear storage curve (volume vs. water level) of a reservoir.
*   **Status**: **Working**.
*   **To Run**:
    ```bash
    python examples/identification/01_reservoir_storage_curve/run_identification.py
    ```
*   **Expected Outcome**: The script will print a table comparing the true, initial, and final identified storage curves. The final curve should be significantly closer to the true curve than the initial guess. A plot (`identification_results.png`) will also be generated.

### 2. Gate Discharge Coefficient (`02_gate_discharge_coefficient`)
*   **Goal**: Identify the discharge coefficient (`C`) of a gate.
*   **Status**: **Working**.
*   **To Run**:
    ```bash
    python examples/identification/02_gate_discharge_coefficient/run_identification.py
    ```
*   **Expected Outcome**: The script will print the true, initial, and final identified discharge coefficients. The final value should be very close to the true value of 0.8.

### 3. Pipe Roughness (`03_pipe_roughness`)
*   **Goal**: Identify the Manning's roughness coefficient (`n`) of a pipe.
*   **Status**: **Partially Working (Known Issue)**.
*   **To Run**:
    ```bash
    python examples/identification/03_pipe_roughness/run_identification.py
    ```
*   **Known Issue**: The example runs without error, and the full agent-based identification process is triggered. However, the optimization algorithm currently fails to find the correct value for the Manning's `n`, instead converging on the upper bound of its search space. This indicates a subtle issue in the interaction between the optimizer and the pipe's hydraulic equations that requires further investigation. The example is still valuable for demonstrating the overall structure and data flow of an identification scenario.

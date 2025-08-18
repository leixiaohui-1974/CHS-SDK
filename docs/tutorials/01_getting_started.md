# Tutorial 1: Your First Simulation - A Simple Reservoir-Gate System

Welcome to the Smart Water Platform! This tutorial will guide you through the process of setting up and running your first simulation. We will use the `example_simulation.py` script as our guide.

The goal of this scenario is to simulate a single reservoir whose water level is controlled by a single downstream gate. A PID controller will be used to adjust the gate's opening to try and maintain a constant water level in the reservoir.

This example demonstrates the core concepts of the platform:
- **Modularity**: Physical components (`Reservoir`, `Gate`) and control logic (`PIDController`) are separate, independent objects.
- **Composition**: The `SimulationHarness` assembles these independent components into a runnable system.
- **Testability**: The entire system can be run and tested in a simulated, offline environment.

## Step 1: Understanding the Components

Let's break down the code in `example_simulation.py`.

### The `Reservoir` Model
```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir

reservoir_params = {
    'surface_area': 1.5e6, # m^2
}
reservoir_initial_state = {
    'volume': 15e6, # m^3
    'water_level': 10.0 # m
}
reservoir = Reservoir(
    reservoir_id="reservoir_1",
    initial_state=reservoir_initial_state,
    params=reservoir_params
)
```
Here, we create an instance of the `Reservoir` model. It's initialized with:
- A unique `reservoir_id`.
- An `initial_state`, which defines its starting conditions.
- A `params` dictionary, which contains static physical parameters of the reservoir.

### The `Gate` Model
```python
from swp.simulation_identification.physical_objects.gate import Gate

gate_params = {
    'max_rate_of_change': 0.1, # 10% per second
    'discharge_coefficient': 0.6,
    'width': 10 # m
}
gate_initial_state = {
    'opening': 0.5 # 50% open
}
gate = Gate(
    gate_id="gate_1",
    initial_state=gate_initial_state,
    params=gate_params
)
```
Similarly, we create a `Gate`. Its parameters define how it operates (e.g., how fast it can open/close) and its physical characteristics for calculating water flow.

### The `PIDController`
```python
from swp.local_agents.control.pid_controller import PIDController

pid_controller = PIDController(
    Kp=0.5,      # Proportional gain
    Ki=0.01,     # Integral gain
    Kd=0.1,      # Derivative gain
    setpoint=12.0 # Target water level in meters
)
```
This is our control logic. We instantiate a standard PID controller. Its goal (`setpoint`) is to maintain the water level at `12.0` meters. The `Kp`, `Ki`, and `Kd` gains determine how aggressively it responds to errors between the setpoint and the actual water level.

## Step 2: Assembling the System with the `SimulationHarness`

The `SimulationHarness` is the engine that runs the simulation. We configure it, add our components and controllers, and then tell it to run.

```python
from swp.core_engine.testing.simulation_harness import SimulationHarness

# Define simulation settings
simulation_config = {
    'duration': 300, # Simulate for 300 seconds
    'dt': 1.0        # Time step of 1 second
}
harness = SimulationHarness(config=simulation_config)

# Add the components to the harness
harness.add_component(reservoir)
harness.add_component(gate)

# Add the controller and associate it with the component it controls
harness.add_controller(controlled_object_id="gate_1", controller=pid_controller)
```
Notice how we add each component individually. We then link the `pid_controller` to the `gate_1`. The harness now knows that this controller is responsible for providing the control actions for `gate_1`.

## Step 3: Running the Simulation

The final step is simple:
```python
harness.run_simulation()
```
To run the entire script, navigate to the root directory of the project in your terminal and execute:
```bash
python3 example_simulation.py
```

## Step 4: Interpreting the Output

You will see a step-by-step log printed to your console. For each time step, you should see something like this:

```
--- Simulation Step 1, Time: 0.00s ---
  Controller for 'gate_1': Target opening = 1.00 (based on reservoir level 10.00m)
  Interaction: Discharge from 'gate_1' = 50.426 m^3/s
  State Update: Reservoir water level = 10.000m
```

Let's break this down:
1.  The controller sees that the reservoir level (10.0m) is below its setpoint (12.0m), so it commands the gate to open further (target opening = 1.00 or 100%).
2.  The harness calculates the discharge from the gate based on the reservoir's water level and the gate's new opening.
3.  The harness updates the reservoir's state, accounting for its constant inflow and the new outflow from the gate.

By watching these values over time, you can see the entire closed-loop control system in action.

Congratulations! You have successfully run your first simulation using the Smart Water Platform. You can now try modifying the parameters in `example_simulation.py` (e.g., the controller gains or the setpoint) and re-running the simulation to see how the system's behavior changes.

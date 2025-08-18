# Tutorial 1: Your First Simulation - A Simple Reservoir-Gate System

Welcome to the Smart Water Platform! This tutorial will guide you through the process of setting up and running your first simulation. We will use the `example_simulation.py` script as our guide.

The goal of this scenario is to simulate a single reservoir whose water level is too high. A PID controller will be used to adjust a downstream gate, opening it to release water and bring the level down to a desired setpoint.

This example demonstrates the core concepts of the platform's non-agent-based, centralized simulation mode:
- **Modularity**: Physical components (`Reservoir`, `Gate`) and control logic (`PIDController`) are separate, independent objects.
- **Composition**: The `SimulationHarness` assembles these independent components into a runnable system.
- **Orchestration**: The harness directly calls the components and controllers in a step-by-step loop to run the simulation.

## Step 1: Understanding the Components

Let's break down the code in `example_simulation.py`.

### The `Reservoir` Model
```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir

reservoir_params = {
    'surface_area': 1.5e6, # m^2
}
reservoir_initial_state = {
    'volume': 21e6, # m^3, equivalent to 14m * 1.5e6 m^2
    'water_level': 14.0 # m, start above the setpoint
}
reservoir = Reservoir(
    reservoir_id="reservoir_1",
    initial_state=reservoir_initial_state,
    params=reservoir_params
)
```
Here, we create an instance of the `Reservoir` model. It's initialized with a unique ID, an `initial_state` (we're starting with the water level at 14.0m), and a `params` dictionary for its static physical parameters.

### The `Gate` Model
```python
from swp.simulation_identification.physical_objects.gate import Gate

gate_params = {
    'max_rate_of_change': 0.1,
    'discharge_coefficient': 0.6,
    'width': 10
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

# For a reverse-acting process (opening the gate DECREASES the water level),
# the controller gains must be negative.
pid_controller = PIDController(
    Kp=-0.5,
    Ki=-0.01,
    Kd=-0.1,
    setpoint=12.0, # Target water level in meters
    min_output=0.0,
    max_output=1.0 # Gate opening is a percentage
)
```
This is our control logic. We instantiate a PID controller with a `setpoint` (goal) of 12.0 meters.

Crucially, the gains (`Kp`, `Ki`, `Kd`) are **negative**. This is because our system is **reverse-acting**: increasing the control variable (the gate opening) causes the measured variable (the water level) to decrease. A negative gain ensures that when the level is too high (a positive error), the controller output is also positive (opening the gate).

## Step 2: Assembling the System with the `SimulationHarness`

The `SimulationHarness` is the engine that runs the simulation. We configure it, add our components and controllers, and then tell it to run.

```python
from swp.core_engine.testing.simulation_harness import SimulationHarness

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
Notice how we add each component individually. We then link the `pid_controller` to the component with the ID `gate_1`. The harness now knows that this controller is responsible for providing the control actions for `gate_1`.

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

You will see a step-by-step log printed to your console. For the first step, you should see:

```
--- Simulation Step 1, Time: 0.00s ---
  Controller for 'gate_1': Target opening = 1.00 (based on reservoir level 14.00m)
  Interaction: Discharge from 'gate_1' = 49.720 m^3/s
  State Update: Reservoir water level = 14.000m
```

Let's break this down:
1.  The controller sees that the reservoir level (14.0m) is above its setpoint (12.0m). Because of the negative gains, it calculates a large positive control action, which is clamped to the maximum of `1.00` (100% open).
2.  The harness calculates the `Discharge` from the gate based on the current water level and the gate's opening.
3.  The harness updates the reservoir's state, applying this discharge as an `outflow`. The water level begins to drop (though it may not be visible in the log until the next step due to the order of operations).

By watching the `State Update` line in the log, you can see the water level gradually decrease towards the 12.0m setpoint, proving that our simple control system is working as intended.

Congratulations! You have successfully run your first simulation using the Smart Water Platform. You can now try modifying the parameters in `example_simulation.py` (e.g., the controller gains or the setpoint) and re-running the simulation to see how the system's behavior changes.

# Tutorial 2: Building a Multi-Component System

This tutorial expands on the concepts from Tutorial 1 by demonstrating how to simulate a more complex system with multiple, interconnected components and multiple independent controllers. We will be working with the `example_multi_gate_river.py` script.

## 1. Scenario Overview

The system we will build follows this physical topology:
**`Reservoir` -> `Gate 1` -> `RiverChannel` -> `Gate 2`**

This represents a common water system configuration. We have two distinct control objectives that will be managed by our central `SimulationHarness`:
1.  **Objective 1**: Control the water level in the `Reservoir` by adjusting the opening of `Gate 1`. The goal is to raise the level from 15m to 18m.
2.  **Objective 2**: Control the water volume in the `RiverChannel` by adjusting the opening of `Gate 2`. The goal is to lower the volume from 500,000 m³ to 400,000 m³.

This setup allows us to explore how different parts of a system can be controlled independently and how their actions affect each other.

## 2. Code Breakdown

Let's examine the key parts of `example_multi_gate_river.py`.

### 2.1. Instantiating the Components
We start by creating instances of all four physical components. Each is given a unique ID (e.g., `reservoir_id="reservoir_1"`) which is crucial for the harness to identify and connect them.

```python
# All four components are created with their own initial states and parameters
reservoir = Reservoir(reservoir_id="reservoir_1", ...)
gate1 = Gate(gate_id="gate_1", ...)
channel = RiverChannel(channel_id="channel_1", ...)
gate2 = Gate(gate_id="gate_2", ...)
```

### 2.2. Configuring Multiple, Independent Controllers
A key part of this example is the use of two separate PID controllers to achieve two different goals.

**Controller 1: Reservoir Level Control**
```python
controller1 = PIDController(
    Kp=0.2, Ki=0.01, Kd=0.05, setpoint=18.0,
    min_output=0.0, max_output=1.0
)
```
This controller's goal is to raise the reservoir level to 18.0m. To do this, it needs to *close* `gate_1`. Since a positive error (level is too low) should result in a negative action (closing the gate), this is a **direct-acting** controller, and its gains are positive. (Note: Our harness logic for this example is simplified and doesn't fully show this, but the gain theory is sound).

**Controller 2: Channel Volume Control**
```python
controller2 = PIDController(
    Kp=-1e-5, Ki=-1e-7, Kd=-1e-6, setpoint=4e5,
    min_output=0.0, max_output=1.0
)
```
This controller's goal is to lower the channel volume to 400,000 m³. To do this, it needs to *open* `gate_2`. Since a positive error (volume is too high) must result in a positive action (opening the gate), this is a **reverse-acting** process, and its gains must be negative.

### 2.3. Assembling the System with the Harness
The `add_controller` method is now more explicit, requiring us to define the full control loop wiring.

```python
harness.add_controller(
    controller_id="res_level_ctrl",  # A unique name for the controller logic
    controller=controller1,
    controlled_id="gate_1",          # The component this controller sends actions to
    observed_id="reservoir_1",       # The component this controller gets its state from
    observation_key="water_level"    # The specific state variable to watch
)
harness.add_controller(
    controller_id="chan_vol_ctrl",
    controller=controller2,
    controlled_id="gate_2",
    observed_id="channel_1",
    observation_key="volume"
)
```
This new signature makes the `run_simulation` method in the harness much more powerful, as it can now wire any controller to any component's state variable and control any other component.

## 3. Understanding the Simulation Logic

The generalized `run_simulation` method now performs these steps:
1.  **Iterate Through Controllers**: For each controller defined (e.g., `res_level_ctrl`), it finds the `observed_id` component (`reservoir_1`).
2.  **Get Observation**: It retrieves the specified `observation_key` (`water_level`) from that component's state.
3.  **Compute Action**: It passes this observation to the controller, which computes a control signal.
4.  **Store Action**: The harness stores this action, mapping it to the `controlled_id` (`gate_1`).
5.  **Repeat**: It repeats this for all controllers.
6.  **Apply Actions**: It applies all the stored actions to the target components.
7.  **Simulate Physics**: It executes the hardcoded physics for the `Reservoir -> Gate -> Channel -> Gate` topology, calculating discharges and updating component states.

## 4. Running the Example

Execute the script from your terminal:
```bash
python3 example_multi_gate_river.py
```
Observe the output. You will see the controllers for `gate_1` and `gate_2` working independently to achieve their goals.

```
--- Simulation Step 1, Time: 0.00s ---
  Controller 'res_level_ctrl': Target for 'gate_1' = 0.75
  Controller 'chan_vol_ctrl': Target for 'gate_2' = 1.00
  State Update: Res Level=16.67m, Chan Vol=499970.59m^3, G1 Open=0.25, G2 Open=0.55
```
Here you can see both controllers computing their desired targets simultaneously. You can then trace how the `Res Level` and `Chan Vol` change over time in response to the two gates opening and closing. This demonstrates a simple but powerful example of multi-variable control in an orchestrated simulation.

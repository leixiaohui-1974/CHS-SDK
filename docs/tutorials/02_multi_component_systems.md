# Tutorial 2: Building a Multi-Component System

This tutorial expands on the concepts from Tutorial 1 by demonstrating how to simulate a more complex system with multiple, interconnected components. We will be working with the `example_multi_gate_river.py` script.

## 1. Scenario Overview

The system we will build follows this topology:
**`Reservoir` -> `Gate 1` -> `RiverChannel` -> `Gate 2`**

This represents a common water system configuration. We have two distinct control objectives:
1.  **Objective 1**: Control the water level in the `Reservoir` by adjusting the opening of `Gate 1`.
2.  **Objective 2**: Control the water volume in the `RiverChannel` by adjusting the opening of `Gate 2`.

This setup allows us to explore how different parts of a system can be controlled independently and how their actions affect each other.

## 2. Code Breakdown

Let's examine the key parts of `example_multi_gate_river.py`.

### 2.1. Instantiating the Components
We start by creating instances of all four physical components: one `Reservoir`, one `RiverChannel`, and two `Gate` models. Each is given a unique ID and its own set of initial states and parameters.

```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel

reservoir = Reservoir(...)
gate1 = Gate(gate_id="gate_1", ...)
channel = RiverChannel(...)
gate2 = Gate(gate_id="gate_2", ...)
```
Note that we are careful to give each gate a unique `gate_id`.

### 2.2. Configuring Multiple Controllers
A key difference in this example is that we now have two controllers for our two gates.

```python
from swp.local_agents.control.pid_controller import PIDController

# Controller 1 targets a water level of 18m in the main reservoir.
controller1 = PIDController(Kp=0.1, Ki=0.005, Kd=0.05, setpoint=18.0)

# Controller 2 targets a volume of 400,000 m^3 in the river channel.
controller2 = PIDController(Kp=1e-5, Ki=1e-7, Kd=1e-6, setpoint=4e5)
```
Notice that the gains (`Kp`, `Ki`, `Kd`) and `setpoint` for `controller2` are very different from `controller1`. This is because it is controlling a different physical process (channel volume vs. reservoir level), which has different dynamics and scales.

### 2.3. Assembling the System
We add all components and controllers to the harness. It's crucial to associate the correct controller with the correct gate.

```python
harness = SimulationHarness(...)

# Add all four physical components
harness.add_component(reservoir)
harness.add_component(gate1)
harness.add_component(channel)
harness.add_component(gate2)

# Add the two controllers, linking them to the correct gate ID
harness.add_controller(controlled_object_id="gate_1", controller=controller1)
harness.add_controller(controlled_object_id="gate_2", controller=controller2)
```

## 3. Understanding the Simulation Logic

When you run `harness.run_simulation()`, the harness (which we upgraded in this phase) executes a more complex sequence of operations at each time step:

1.  **Identify Components**: It finds all the components you added (`Reservoir`, `Gate`s, `RiverChannel`).
2.  **Control Gate 1**: It uses `controller1` to compute an action for `gate1` based on the `reservoir`'s water level.
3.  **Calculate Gate 1 Discharge**: It calculates the flow through `gate1`. Importantly, it now uses the `RiverChannel`'s water level as the `downstream_level`, making the simulation more physically realistic.
4.  **Update River Channel**: The discharge from `gate1` becomes the inflow for the `RiverChannel`. The harness then calls the channel's `step` method.
5.  **Control Gate 2**: It uses `controller2` to compute an action for `gate2` based on the `RiverChannel`'s volume.
6.  **Calculate Gate 2 Discharge**: It calculates the flow through `gate2`. This flow now determines the final outflow from the `RiverChannel`.
7.  **Update Reservoir**: Finally, it updates the `Reservoir`'s volume based on its own inflow and the calculated outflow from `gate1`.

This demonstrates a coordinated, sequential simulation of a water system topology.

## 4. Running the Example

Execute the script from your terminal:
```bash
python3 example_multi_gate_river.py
```
Observe the output. You will now see separate log entries for both controllers and all four components, allowing you to trace the cascading effects through the system. For example, you can see how an action at `gate1` changes the `RiverChannel`'s volume, which in turn causes `controller2` to take action at `gate2`.

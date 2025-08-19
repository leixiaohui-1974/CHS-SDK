# Training 1: Building a Basic Simulation

This tutorial will guide you through the process of building a simple simulation from scratch using the Smart Water Platform. We will build the hydropower simulation that is in `swp/examples/example_hydropower_simulation.py`.

## 1. Core Concepts

The platform is built around a few core concepts:

-   **Physical Models**: These are Python classes that represent physical components in a water system, like a `Lake`, `Pipe`, or `Gate`. They must inherit from `PhysicalObjectInterface`.
-   **Simulation Harness**: This is the main engine that manages the simulation. You add your physical models to the harness, define how they are connected, and then run the simulation.
-   **State and Parameters**: Each model has a `state` (e.g., current water volume) which changes over time, and `parameters` (e.g., pipe diameter) which are static.

## 2. Setting up the Simulation File

First, create a new Python file. Let's call it `my_first_simulation.py`.

## 3. Importing Necessary Classes

You will need to import the `SimulationHarness` and the physical models you want to use.

```python
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.simulation_identification.physical_objects.lake import Lake
from swp.simulation_identification.physical_objects.water_turbine import WaterTurbine
from swp.simulation_identification.physical_objects.canal import Canal
```

## 4. Initializing the Simulation Harness

The harness is initialized with a configuration dictionary that specifies the `duration` of the simulation (in seconds) and the `dt` (time step in seconds).

```python
# Simulate for 1 day with 1-hour time steps
config = {'duration': 86400, 'dt': 3600}
harness = SimulationHarness(config)
```

## 5. Creating Physical Models

Now, create instances of the models you want to simulate. Each model needs a unique `name`, an `initial_state` dictionary, and a `parameters` dictionary.

```python
# Upper Lake
initial_lake_volume = 40e6
lake_surface_area = 2e6
upper_lake = Lake(
    name="upper_lake",
    initial_state={'volume': initial_lake_volume, 'water_level': initial_lake_volume / lake_surface_area},
    parameters={'surface_area': lake_surface_area, 'max_volume': 50e6}
)

# Hydropower Turbine
turbine = WaterTurbine(
    name="turbine_1",
    initial_state={'power': 0, 'outflow': 0},
    parameters={'efficiency': 0.85, 'max_flow_rate': 150}
)

# Tailrace Canal
tailrace_canal = Canal(
    name="tailrace_canal",
    initial_state={'volume': 100000, 'water_level': 2.1},
    parameters={
        'bottom_width': 20,
        'length': 5000,
        'slope': 0.0002,
        'side_slope_z': 2,
        'manning_n': 0.025
    }
)
```

## 6. Adding Components to the Harness

Add your created models to the harness.

```python
harness.add_component(upper_lake)
harness.add_component(turbine)
harness.add_component(tailrace_canal)
```

## 7. Defining the Topology

Define how the components are connected. The connections represent the direction of water flow.

```python
harness.add_connection("upper_lake", "turbine_1")
harness.add_connection("turbine_1", "tailrace_canal")
```

## 8. Building and Running the Simulation

Finally, build the harness (which calculates the correct order to run the models in) and run the simulation.

```python
harness.build()
harness.run_simulation()
```

And that's it! You have built and run your first simulation. The `run_simulation` method will print the state of each component at each time step.

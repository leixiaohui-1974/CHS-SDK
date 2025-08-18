# Tutorial 5: Simulating Complex Networks

In the previous tutorials, we built a sophisticated, multi-agent control system. However, all our examples featured a simple, linear topology: a single reservoir flowing into a single channel. Real-world water systems are rarely this simple. They are complex networks with multiple sources, tributaries, and branching paths.

This tutorial covers the most significant enhancement to the Smart Water Platform to date: a **graph-based simulation harness** that allows for the modeling of arbitrarily complex, non-linear network topologies.

## The Limitations of a Linear Approach

The previous `SimulationHarness` was hard-coded to simulate a specific, linear chain of components. To model a different structure, one would have had to modify the harness's internal simulation loop. This was inflexible and not scalable.

To overcome this, we have refactored the harness to think of the water system not as a list, but as a **directed graph**.

## The Graph-Based Topology

In this new paradigm, the water system is a collection of component "nodes" connected by directional "edges" that represent the flow of water.

-   **Nodes**: These are the physical components (`Reservoir`, `Gate`, `RiverChannel`).
-   **Edges**: These represent the connections between components (e.g., a `Gate`'s output flows into a `RiverChannel`).

This approach is incredibly flexible and allows us to model real-world scenarios like:
-   A river being fed by multiple tributaries.
-   A channel splitting into two separate canals.
-   Complex, multi-reservoir systems.

### The New `SimulationHarness` API

To support this new model, the `SimulationHarness` API has been updated:

1.  **`add_component(component)`**: This method remains the same, but it's now just one part of defining the system. It adds a component (a node) to our graph.

2.  **`add_connection(upstream_id, downstream_id)`**: This is the new core method for defining the network structure. It creates a directed edge in the graph, telling the harness that water flows from the `upstream_id` component to the `downstream_id` component.

3.  **`build()`**: After all components and connections have been added, you must call this method. It performs a **topological sort** on the graph to determine the correct computational order (always processing upstream components before downstream ones) and checks for any physically impossible cycles (e.g., a river flowing back into itself).

## Example: A Branched River Network

The best way to understand this is to walk through the new `example_branched_network.py` script, which now includes a full multi-agent control system.

This example models the following network:
- **Reservoir 1** -> **Gate 1** -> **Tributary Channel**
- **Reservoir 2** -> **Gate 2** -> **Main Channel**
- The **Tributary Channel** also flows into the **Main Channel** (a confluence).
- The **Main Channel** flows out through a final **Gate 3**.

Here is the breakdown of the script:

### 1. Imports and Boilerplate
```python
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.river_channel import RiverChannel
from swp.core_engine.testing.simulation_harness import SimulationHarness
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.local_control_agent import LocalControlAgent
from swp.central_coordination.dispatch.central_dispatcher import CentralDispatcher

def run_branched_network_example():
    # ...
```
We start by importing all the necessary classes for both the physical components and the agent control system.

### 2. Initializing the Harness and Components
```python
    # 1. Set up the Simulation Harness and Message Bus
    simulation_config = {'duration': 1000, 'dt': 1.0}
    harness = SimulationHarness(config=simulation_config)
    message_bus = harness.message_bus

    # 2. Define the physical components
    res1 = Reservoir("res1", {'volume': 15e6, 'water_level': 10.0}, {'surface_area': 1.5e6})
    g1 = Gate("g1", {'opening': 0.1}, {'width': 10, 'max_rate_of_change': 0.1})
    trib_chan = RiverChannel("trib_chan", {'volume': 2e5, 'water_level': 2.0}, {'k': 0.0002})

    res2 = Reservoir("res2", {'volume': 30e6, 'water_level': 20.0}, {'surface_area': 1.5e6})
    g2 = Gate("g2", {'opening': 0.1}, {'width': 15, 'max_rate_of_change': 0.1})

    main_chan = RiverChannel("main_chan", {'volume': 8e5, 'water_level': 8.0}, {'k': 0.0001})
    g3 = Gate("g3", {'opening': 0.5}, {'width': 20}) # Uncontrolled gate

    physical_components = [res1, g1, trib_chan, res2, g2, main_chan, g3]
    for comp in physical_components:
        harness.add_component(comp)
```
First, we create the `SimulationHarness`. Then, we instantiate all seven physical components that make up our network. Finally, we add them all to the harness using `add_component()`. At this point, the harness knows about the nodes but not how they are connected.

### 3. Defining the Topology
```python
    # 3. Define the network topology
    print("\nDefining network connections...")
    harness.add_connection("res1", "g1")
    harness.add_connection("g1", "trib_chan")
    harness.add_connection("res2", "g2")
    harness.add_connection("trib_chan", "main_chan")
    harness.add_connection("g2", "main_chan")
    harness.add_connection("main_chan", "g3")
    print("Connections defined.")
```
This is the new, critical part. We use a series of `add_connection()` calls to define the exact structure of the water network. This creates the directed graph that the harness will use for the simulation, including the confluence where `trib_chan` and `g2` both flow into `main_chan`.

### 4. Defining the Multi-Agent Control System
```python
    # 4. Define the Multi-Agent System
    # ... (DigitalTwinAgent, PIDController, LocalControlAgent, CentralDispatcher instances)

    all_agents = twin_agents + [lca1, lca2, dispatcher]
    for agent in all_agents:
        harness.add_agent(agent)
```
This section is similar to previous tutorials. We create a full hierarchical control system:
-   **Digital Twins** for the reservoirs and controlled gates to publish their state.
-   **PID Controllers** for `g1` and `g2`.
-   **Local Control Agents** to manage each PID controller, subscribing to the appropriate reservoir level and publishing to the appropriate gate's action topic.
-   A **Central Dispatcher** that monitors both reservoir levels and sends high-level setpoint commands to the local agents.

### 5. Build and Run
```python
    # 5. Build and run the simulation
    print("\nBuilding simulation harness...")
    harness.build()
    harness.run_mas_simulation()
```
Finally, we call `harness.build()` to finalize the topology. Then, `harness.run_mas_simulation()` kicks off the simulation. The harness now automatically handles the complex data flow between all components according to the graph we defined.

## Conclusion

By shifting to a graph-based topology, the Smart Water Platform is now capable of modeling and simulating far more realistic and complex scenarios. This foundational change opens the door to simulating entire water districts, optimizing interconnected systems, and exploring more sophisticated control strategies.

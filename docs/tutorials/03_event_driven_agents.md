# Tutorial 3: Event-Driven Agents and the Message Bus

This tutorial introduces the most significant architectural evolution of the Smart Water Platform: the **Multi-Agent System (MAS)** architecture. We will move away from the centralized `SimulationHarness` logic used in the first two examples and explore a truly decoupled, event-driven system using the `example_mas_simulation.py` script.

## 1. A New Architecture: From Orchestration to Collaboration

In our previous examples, the `SimulationHarness` acted as a central orchestrator. It knew about every component, called controllers directly, and manually passed data between components. This is simple but not scalable or realistic for a large, distributed system.

The MAS architecture changes this paradigm:
- **Agents are independent**: They don't know about each other; they only know about the `MessageBus`.
- **Communication is asynchronous**: Agents publish information (messages) to named "topics" and subscribe to the topics they care about. This is known as the **Publish/Subscribe** pattern.
- **The Harness is simplified**: The `SimulationHarness` becomes a simple timekeeper and physics engine. It no longer contains control logic.

This is a powerful concept that mirrors how real-world distributed control systems are built.

## 2. Key Components in the MAS Architecture

Let's look at the new and upgraded components that make this possible.

### 2.1. The `MessageBus`
The `MessageBus` is the central nervous system of our platform. All agents connect to it. An agent can `publish` a message to a specific topic (e.g., `"state.reservoir.level"`) and `subscribe` to any topic it's interested in. When a message is published to a topic, the bus ensures all subscribers to that topic receive the message.

### 2.2. The `LocalControlAgent`
In `example_mas_simulation.py`, we no longer use a `PIDController` directly. We wrap it in a `LocalControlAgent`.

```python
# from swp.local_agents.control.local_control_agent import LocalControlAgent

control_agent = LocalControlAgent(
    agent_id="control_agent_gate_1",
    controller=pid_controller,
    message_bus=message_bus,
    observation_topic=RESERVOIR_STATE_TOPIC,
    action_topic=GATE_ACTION_TOPIC
)
```
This agent is a true, independent component. Its sole job is to:
1.  **Listen** for messages on its `observation_topic` (`state.reservoir.level`).
2.  When a message arrives, it passes the data to its internal `pid_controller`.
3.  It takes the controller's output and **publishes** it as a new message to its `action_topic` (`action.gate.opening`).

### 2.3. The Upgraded `DigitalTwinAgent`
This agent now acts as a proper sensor feed.
```python
# from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent

twin_agent = DigitalTwinAgent(
    agent_id="twin_agent_reservoir_1",
    simulated_object=reservoir,
    message_bus=message_bus,
    state_topic=RESERVOIR_STATE_TOPIC
)
```
Its `run()` method now has a purpose: at each simulation step, it reads the state of its physical model (`reservoir`) and **publishes** that state to the `state_topic`.

### 2.4. Message-Aware Physical Models
For the system to be fully decoupled, the physical models must also react to messages. We upgraded the `Gate` model to do this.

```python
# from swp.simulation_identification.physical_objects.gate import Gate

gate = Gate(
    gate_id="gate_1",
    ...,
    message_bus=message_bus,
    action_topic=GATE_ACTION_TOPIC
)
```
When instantiated, the `Gate` now **subscribes** to its `action_topic`. When the `control_agent` publishes a new command, the gate receives it and updates its internal target opening. When the harness later calls the `gate.step()` method, the gate already knows what its target is.

## 3. The MAS Simulation Loop

The `SimulationHarness` now has a new method, `run_mas_simulation()`. At each time step, it performs a clean, two-phase process:

1.  **Phase 1: Run Agents (Thinking)**: The harness calls the `run()` method on every agent.
    - `twin_agent` publishes the reservoir's current state.
    - The `message_bus` immediately delivers this state message to the `control_agent` (because it's a subscriber).
    - The `control_agent`'s `handle_observation` method is triggered, it computes a new control signal, and publishes it to the action topic.
    - The `message_bus` delivers the action message to the `gate` model. The gate's `handle_action_message` method is triggered, and it updates its internal action.

2.  **Phase 2: Step Physical Models (Acting)**: The harness calls the `step()` method on every physical model.
    - The `gate` executes its `step` logic using the action it just received from the bus.
    - The harness calculates the resulting outflow and tells the `reservoir` to execute its `step` logic.

This loop beautifully illustrates the separation of concerns: agents think, models act.

## 4. Why This Architecture Matters

- **Scalability**: We can add dozens of new agents, sensors, and controllers without changing any existing components. We just need to define new topics and ensure they subscribe to the right ones.
- **Decoupling**: The control logic is fully separated from the physical models. We could replace the PID controller inside the `control_agent` with a more advanced algorithm, and nothing else in the system would need to change.
- **Realism**: This architecture is much closer to how real-world distributed control systems are built, paving the way for more advanced features like network latency simulation and hardware-in-the-loop testing.

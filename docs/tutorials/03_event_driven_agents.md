# Tutorial 3: Event-Driven Agents and the Message Bus

This tutorial introduces the most significant architectural evolution of the Smart Water Platform: the **Multi-Agent System (MAS)** architecture. We will move away from the centralized `SimulationHarness` logic used in the first two examples and explore a truly decoupled, event-driven system using the `example_mas_simulation.py` script.

## 1. A New Architecture: From Orchestration to Collaboration

In our previous examples, the `SimulationHarness` acted as a central orchestrator. It knew about every component, called controllers directly, and manually passed data between components. This is simple but not scalable or realistic for a large, distributed system.

The MAS architecture changes this paradigm:
- **Agents are independent**: They don't know about each other; they only know about the `MessageBus`.
- **Communication is event-driven**: Agents publish information (messages) to named "topics" and subscribe to the topics they care about. This is known as the **Publish/Subscribe** pattern.
- **The Harness is simplified**: The `SimulationHarness` becomes a simple timekeeper and physics engine. It no longer contains control logic.

This is a powerful concept that mirrors how real-world distributed control systems are built.

## 2. Key Components in the MAS Architecture

Let's look at the new and upgraded components that make this possible.

### 2.1. The `MessageBus`
The `MessageBus` is the central nervous system of our platform. All agents and message-aware components connect to it. An agent can `publish` a message to a specific topic (e.g., `"state.reservoir.level"`) and `subscribe` to any topic it's interested in. When a message is published to a topic, the bus ensures all subscribers to that topic receive the message immediately.

### 2.2. The `DigitalTwinAgent`
This agent's role is to act as a "digital twin" for a physical component, reporting its state to the rest of the system.
```python
twin_agent = DigitalTwinAgent(
    agent_id="twin_agent_reservoir_1",
    simulated_object=reservoir,
    message_bus=message_bus,
    state_topic=RESERVOIR_STATE_TOPIC
)
```
Its `run()` method now has a clear purpose: at each simulation step, the harness calls `run()`, and the agent reads the state of its physical model (`reservoir`) and **publishes** that state to its `state_topic`.

### 2.3. The `LocalControlAgent`
In `example_mas_simulation.py`, the `PIDController` is wrapped by a `LocalControlAgent`. This agent handles all the communication, allowing the controller to focus purely on its algorithm.

```python
control_agent = LocalControlAgent(
    agent_id="control_agent_gate_1",
    controller=pid_controller,
    message_bus=message_bus,
    observation_topic=RESERVOIR_STATE_TOPIC,
    observation_key='water_level', # Tell the agent which part of the message to use
    action_topic=GATE_ACTION_TOPIC,
    dt=harness.dt # The agent needs to know the simulation time step
)
```
This agent's job is to:
1.  **Listen** for messages on its `observation_topic`.
2.  When a message arrives, it uses the `observation_key` to extract the relevant value (e.g., `14.0`).
3.  It passes this value and the simulation time step (`dt`) to its internal `pid_controller`.
4.  It takes the controller's output and **publishes** it as a new message to its `action_topic`.

### 2.4. Message-Aware Physical Models
For the system to be fully decoupled, the physical models themselves can react to messages. We've made the `Gate` model message-aware.

```python
gate = Gate(
    gate_id="gate_1",
    ...,
    message_bus=message_bus,
    action_topic=GATE_ACTION_TOPIC
)
```
When instantiated, the `Gate` now **subscribes** to its `action_topic`. When the `control_agent` publishes a new command, the gate's `handle_action_message` method is triggered, and it updates its internal target opening. When the harness later calls the `gate.step()` method, the gate already knows where it's supposed to move.

## 3. The MAS Simulation Loop

The `SimulationHarness` now uses the `run_mas_simulation()` method. At each time step, it performs a clean, two-phase process:

1.  **Phase 1: Perception & Action Cascade**: The harness calls the `run()` method on the `DigitalTwinAgent`.
    - The twin publishes the reservoir's current state.
    - The synchronous `message_bus` immediately delivers this state message to the `control_agent`.
    - The `control_agent`'s `handle_observation` method is triggered, it computes a new control signal, and publishes it to the action topic.
    - The bus delivers the action message to the `gate` model, which updates its internal target.

2.  **Phase 2: Physical Step**: The harness calls the `step()` method on every physical model.
    - The harness calculates the physical interaction (the discharge from the gate).
    - It steps the `reservoir` and `gate`, updating their states based on the physics and the actions received in Phase 1.

This loop beautifully illustrates the separation of concerns: agents think, models act.

## 4. Why This Architecture Matters

- **Scalability**: New agents and components can be added to the system without modifying the existing ones. We just need to define new topics and ensure they subscribe to the right ones.
- **Decoupling**: The control logic is fully separated from the physical models, allowing for easy swapping of algorithms.
- **Realism**: This architecture is much closer to how real-world distributed control systems are built, paving the way for more advanced features like network latency simulation and hardware-in-the-loop testing.

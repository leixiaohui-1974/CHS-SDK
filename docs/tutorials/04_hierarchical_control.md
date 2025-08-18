# Tutorial 4: Hierarchical Control with a Central Dispatcher

Welcome to the final tutorial in our introductory series. Here, we will build on the event-driven concepts from Tutorial 3 to create a **hierarchical control system**. This is a powerful pattern where a high-level "supervisor" agent manages the objectives of one or more low-level "operator" agents.

We will explore the `example_hierarchical_control.py` script, which is the most advanced example of the platform's capabilities.

## 1. Scenario Overview

The scenario demonstrates a two-level control hierarchy:
- **Low-Level Loop (The "Operator")**: A `LocalControlAgent` is responsible for the direct, real-time control of a gate. Its goal is to maintain a specific water level in a reservoir, which it does by listening to the reservoir's state and adjusting the gate opening.
- **High-Level Loop (The "Supervisor")**: A `CentralDispatcher` agent acts as a system-wide supervisor. It also listens to the reservoir's state, but its job is to make strategic decisions. If it detects a "flood condition" (the water level is too high), it will issue a command to the `LocalControlAgent`, telling it to aim for a new, lower water level setpoint.

This creates a dynamic system where a central "brain" can manage the objectives of local controllers in response to the overall system state.

## 2. The Two-Level Control Loop

The system operates on two nested, event-driven loops that communicate via the `MessageBus`:
1.  **Low-Level State/Action Loop**:
    - `twin_agent_reservoir_1` publishes the reservoir's state to `state.reservoir.level`.
    - `control_agent_gate_1` receives this state, computes an action with its PID controller, and publishes it to `action.gate.opening`.
    - The `gate_1` model receives the action and updates its target.
2.  **High-Level State/Command Loop**:
    - `central_dispatcher_1` also receives the state from `state.reservoir.level`.
    - It applies its internal rules and decides if the setpoint needs to change.
    - If a change is needed, it publishes a new setpoint message to the `command.gate1.setpoint` topic.
    - `control_agent_gate_1`, which is also subscribed to this command topic, receives the new setpoint and updates its internal PID controller's goal.

## 3. Code Breakdown

Let's examine the new and updated parts of `example_hierarchical_control.py`.

### 3.1. Upgrading the `LocalControlAgent`
The `LocalControlAgent` is now instantiated with two new topics:
- `command_topic`: The topic to listen for new commands from the supervisor.
- `feedback_topic`: The topic to listen for state updates from the component it is controlling (in this case, the gate itself). This creates a complete closed loop.

```python
control_agent = LocalControlAgent(
    agent_id="control_agent_gate_1",
    controller=pid_controller,
    message_bus=message_bus,
    observation_topic=RESERVOIR_STATE_TOPIC,
    observation_key='water_level',
    action_topic=GATE_ACTION_TOPIC,
    dt=simulation_dt,
    command_topic=GATE_COMMAND_TOPIC,
    feedback_topic=GATE_STATE_TOPIC
)
```
The agent's internal logic now has a `handle_command_message` method to process incoming commands and a `handle_feedback_message` to receive updates from its controlled actuator.

### 3.2. Implementing the `CentralDispatcher`
This is a new type of agent that represents a higher level of intelligence. It subscribes to one or more state topics and publishes to one or more command topics. Its core logic is defined by a set of rules.

```python
dispatcher_rules = {
    'flood_threshold': 18.0,   # If level > 18m, it's a flood risk
    'normal_setpoint': 15.0, # Normal target level
    'flood_setpoint': 12.0   # Emergency target level to lower the water
}
dispatcher = CentralDispatcher(
    agent_id="central_dispatcher_1",
    message_bus=message_bus,
    state_subscriptions={'reservoir_level': RESERVOIR_STATE_TOPIC},
    command_topics={'gate1_command': GATE_COMMAND_TOPIC},
    rules=dispatcher_rules
)
```
In this example, the dispatcher's rule is simple: if the `reservoir_level` goes above the `flood_threshold` of 18.0m, it will publish a command to the `gate1_command` topic, telling the local agent to adopt the `flood_setpoint` of 12.0m.

## 4. Running the Simulation and Interpreting the Results

Execute the script from your terminal:
```bash
python3 example_hierarchical_control.py
```
The log output clearly shows the hierarchy in action.

**Step 1: The Supervisor Intervenes**
At the very start, the water level is 19.0m, which is above the 18.0m flood threshold.
```
--- MAS Simulation Step 1, Time: 0.00s ---
  Phase 1: Triggering agent perception and action cascade.
PIDController setpoint updated from 15.0 to 12.0.
```
Before the first step is even complete, the `CentralDispatcher` has already received the initial state, evaluated its rules, and published a command. The `LocalControlAgent` receives this command and immediately updates its PID controller's setpoint from the default 15.0 to the new, emergency setpoint of 12.0.

**Step 2: The Operator Executes**
Now using the new setpoint, the `LocalControlAgent` gets to work.
```
  Phase 2: Stepping physical models with interactions.
  State Update: Reservoir level = 19.000m, Gate opening = 0.600m
```
Because the level (19.0m) is far above the new target (12.0m), the PID controller commands the gate to open. Over the next several steps, the gate continues to open until it reaches its maximum, and the reservoir level steadily decreases.

This example provides the foundation for building truly intelligent, multi-layered control systems where strategic, system-wide goals can be translated into concrete, robustly executed actions for local controllers.

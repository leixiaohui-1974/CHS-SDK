# Tutorial 5: Handling Disturbances

In a real-world water system, perfect stability is an illusion. Systems are constantly affected by external factors, or "disturbances." A robust control system must be ableto react to these events to maintain its desired state.

This tutorial demonstrates how our Multi-Agent System can be made resilient to such disturbances. We will introduce a `RainfallAgent` that injects a sudden, large inflow of water into our reservoir, and we will observe how the hierarchical control system works to mitigate its impact.

## Key Concepts

### 1. Disturbance Agents

A disturbance is simply an event that affects the state of a physical component, originating from outside the normal control loop. We can model these events using specialized agents. In our case, we've created `RainfallAgent`.

- **Time-Based Trigger**: This agent is configured to activate at a specific time in the simulation (`start_time`) and for a certain `duration`.
- **Publishing Disturbances**: When active, it publishes a message on a specific "disturbance topic" (e.g., `disturbance.rainfall.inflow`) containing a payload (e.g., `{'inflow': 150}`).

### 2. Message-Aware Physical Models

For a disturbance to have an effect, the physical model must be able to receive and process it. We achieve this by making the `Reservoir` model "message-aware."

- **Subscription to Disturbances**: The `Reservoir` is now initialized with a list of `disturbance_topics` it should subscribe to.
- **Internal State Updates**: When a message is received on one of these topics, the reservoir's internal `handle_message` method is called, which updates its inflow based on the message payload. This directly impacts its physical state in the next simulation step.

### 3. System Resilience

This example showcases the full power of the hierarchical control architecture:
- The **Local Control Agent** acts as the first line of defense, immediately reacting to small deviations from the setpoint caused by the disturbance.
- The **Central Dispatcher** monitors the overall system state. If the disturbance is large enough to push the system into a dangerous state (e.g., crossing a `flood_threshold`), the dispatcher can intervene by issuing a new, safer setpoint to the local agent.

## The Example: `example_with_disturbance.py`

This script builds directly on the hierarchical control example.

[include-code: example_with_disturbance.py]

### Setup

1.  **RainfallAgent**: We create an instance of `RainfallAgent`, configuring it to start a heavy rainfall event at `t=300s` that lasts for `200s`.
    ```python
    rainfall_config = {
        "topic": RAINFALL_TOPIC,
        "start_time": 300,
        "duration": 200,
        "inflow_rate": 150 # A significant inflow
    }
    rainfall_agent = RainfallAgent("rainfall_agent_1", message_bus, rainfall_config)
    ```
2.  **Message-Aware Reservoir**: We instantiate the `Reservoir` with the `disturbance_topics` parameter, telling it to listen for messages on the `RAINFALL_TOPIC`.
    ```python
    reservoir = Reservoir(
        # ...
        message_bus=message_bus,
        disturbance_topics=[RAINFALL_TOPIC]
    )
    ```
3.  **Dispatcher Rules**: The `CentralDispatcher` is configured with a `flood_threshold` of 13.0m. If the water level exceeds this, it will issue an emergency `flood_setpoint` of 11.0m.
    ```python
    dispatcher_rules = {
        'flood_threshold': 13.0,
        'normal_setpoint': 12.0,
        'flood_setpoint': 11.0
    }
    ```

### Running the Simulation

When you run the script, you will observe the following behavior:

1.  **Initial Stability**: For the first 300 seconds, the system is stable. The reservoir water level is held steady at the `normal_setpoint` of 12.0m by the `LocalControlAgent`.
2.  **Disturbance Event**: At `t=300s`, the `RainfallAgent` activates and begins publishing inflow messages.
    ```
    --- Rainfall event STARTED at t=300.0s ---
    ```
3.  **System Reaction**: The reservoir's volume and water level begin to rise due to the new inflow. The `LocalControlAgent`'s PID controller immediately detects this error (the difference between the rising level and the 12.0m setpoint) and starts opening the gate to release more water.
4.  **Successful Mitigation**: In this scenario, the disturbance is significant but not catastrophic. The PID controller is effective enough to counteract the rainfall by opening the gate, preventing the water level from ever reaching the `flood_threshold` of 13.0m. The `CentralDispatcher` sees the rising level but, because the threshold is never breached, it continues to command the `normal_setpoint`.
    ```
    [central_dispatcher_1] Reservoir level is 12.02m. Commanding setpoint: 12.00m
    ```
5.  **Recovery**: At `t=500s`, the rainfall event ends. The `LocalControlAgent`, still trying to achieve the 12.0m setpoint, now has a gate that is too far open. The water level begins to drop. The PID controller corrects this "overshoot" by gradually closing the gate until the system re-stabilizes at the original 12.0m setpoint.

This example demonstrates the robustness and intelligence of the MAS and hierarchical control structure. The system automatically handled a significant external event without requiring high-level intervention, proving the effectiveness of the local controller. It also shows that the framework is in place for the central dispatcher to take command if the situation had become more severe.

# 05. Physical IO Agent (`PhysicalIOAgent`)

## Overview

The `PhysicalIOAgent` acts as the crucial interface layer between the digital control agents and the physical world (or, in this simulation, the digital representation of the physical world). It simulates the behavior of hardware components like sensors and actuators that are part of a real-world Supervisory Control and Data Acquisition (SCADA) system.

Its primary role is to bridge the gap between high-level control commands and the low-level physical state changes, and to provide realistic sensor feedback to the rest of the system.

## Key Responsibilities

1.  **Simulating Sensors**: It reads the "true" state from the physical model objects (e.g., the water level in a `Canal`), optionally adds random noise to simulate sensor inaccuracy, and publishes this data onto the `MessageBus` for other agents to consume.
2.  **Simulating Actuators**: It subscribes to specific "action" topics on the `MessageBus`. When a message with a control command is received (e.g., "set gate opening to 0.5m"), it translates this command into a direct state change on the corresponding physical model object (e.g., setting the `target_opening` attribute of a `Gate` object).

## Configuration

The `PhysicalIOAgent` is initialized with the following parameters:

-   `agent_id` (str): A unique identifier for the agent.
-   `message_bus` (MessageBus): An instance of the system's message bus.
-   `sensors_config` (dict): A dictionary defining the configuration for all sensors managed by this agent.
-   `actuators_config` (dict): A dictionary defining the configuration for all actuators managed by this agent.

### `sensors_config`

The keys of this dictionary are unique names for each sensor. The value is another dictionary with the following keys:

-   `obj` (PhysicalObjectInterface): The actual physical object instance to read from (e.g., a `Canal` or `Reservoir` object).
-   `state_key` (str): The key to use when looking up the value from the object's state dictionary (returned by `get_state()`).
-   `topic` (str): The `MessageBus` topic on which to publish the sensor readings.
-   `noise_std` (float, optional): The standard deviation of the Gaussian noise to be added to the true value. Defaults to `0.0`.

**Example:**

```python
sensors_config = {
    'canal_level_sensor': {
        'obj': upstream_canal,          # The canal object to monitor
        'state_key': 'water_level',     # Read the 'water_level' from its state
        'topic': 'state.canal.level',   # Publish to this topic
        'noise_std': 0.02               # Add noise with a stddev of 0.02m
    }
}
```

### `actuators_config`

The keys of this dictionary are unique names for each actuator. The value is another dictionary with the following keys:

-   `obj` (PhysicalObjectInterface): The actual physical object instance to control (e.g., a `Gate` or `Pump` object).
-   `target_attr` (str): The name of the attribute on the physical object that the agent should set as the target state (e.g., `target_opening`). The physical object's `step` method is responsible for moving from its current state towards this target state.
-   `topic` (str): The `MessageBus` topic to which this actuator listens for commands.
-   `control_key` (str): The key to look for in the incoming message's payload to find the desired control value.

**Example:**

```python
actuators_config = {
    'gate_actuator': {
        'obj': control_gate,                # The gate object to control
        'target_attr': 'target_opening',    # Set the 'target_opening' attribute on the gate
        'topic': 'action.gate.opening',     # Listen on this topic for commands
        'control_key': 'target_opening'     # The command message will contain this key
    }
}
```

## Operation

### Sensing (Publishing Data)

The sensing operation is triggered by calling the agent's `run(current_time)` method at each simulation step. For each configured sensor, the agent:
1.  Calls the `get_state()` method on the associated physical object.
2.  Retrieves the true value using the `state_key`.
3.  Generates a random noise value from a normal distribution (`mean=0`, `std=noise_std`).
4.  Adds the noise to the true value.
5.  Publishes a message to the specified `topic`.

The published message is a dictionary with the following structure:
```json
{
    "<state_key>": <noisy_value>,
    "timestamp": <current_time>
}
```
For example: `{'water_level': 1.513, 'timestamp': 10.0}`.

### Actuating (Subscribing to Commands)

During initialization, the `PhysicalIOAgent` automatically subscribes to the topics defined in its `actuators_config`. When a message arrives on one of these topics, the agent's internal callback is triggered. The callback:
1.  Retrieves the control value from the message payload using the `control_key`.
2.  Uses `setattr()` to update the attribute named `target_attr` on the associated physical object with this value.

For example, if a message `{'target_opening': 0.75}` is published to the `action.gate.opening` topic, the agent will execute the equivalent of `control_gate.target_opening = 0.75`. The `Gate` object's own `step` method is then responsible for gradually changing its actual opening to meet this new target.

## Example Usage

The following example demonstrates how to set up and run a `PhysicalIOAgent` to monitor a canal's water level and control a gate.

```python
import time
from core_lib.physical_objects.canal import Canal
from core_lib.physical_objects.gate import Gate
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent

# 1. Initialize Physical Components and Message Bus
bus = MessageBus()
# Note: Physical objects require proper initialization with parameters.
# upstream_canal = Canal(name="upstream_canal", ...)
# control_gate = Gate(name="control_gate", ...)


# 2. Define topics
STATE_TOPIC = "state/canal/level"
ACTION_TOPIC = "action/gate/opening"

# 3. Configure and create the PhysicalIOAgent
# This assumes 'upstream_canal' and 'control_gate' are initialized objects.
# io_agent = PhysicalIOAgent(
#     agent_id="io_agent_1",
#     message_bus=bus,
#     sensors_config={
#         'canal_level_sensor': {
#             'obj': upstream_canal,
#             'state_key': 'water_level',
#             'topic': STATE_TOPIC,
#             'noise_std': 0.02
#         }
#     },
#     actuators_config={
#         'gate_actuator': {
#             'obj': control_gate,
#             'target_attr': 'target_opening',
#             'topic': ACTION_TOPIC,
#             'control_key': 'target_opening'
#         }
#     }
# )

# 4. Set up a listener to see the agent's output
def print_sensor_data(message):
    print(f"Received sensor data: {message}")
bus.subscribe(STATE_TOPIC, print_sensor_data)

# 5. Simulation Loop
# dt = 1.0
# for t in range(20):
#     # In a real scenario, another agent would publish this command.
#     if t == 5:
#         print("\n>>> Sending command to open gate to 0.5m\n")
#         bus.publish(ACTION_TOPIC, {'target_opening': 0.5})

#     # The IO Agent reads sensors and publishes data
#     io_agent.run(current_time=t)

#     # The physical models evolve
#     # (gate moves towards its target, canal water level changes)
#     control_gate.step(...)
#     upstream_canal.step(...)

#     time.sleep(0.1)
```

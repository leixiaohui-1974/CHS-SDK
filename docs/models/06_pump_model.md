# Pump Model

The `Pump` model represents a water pump that adds energy to the system to move water from a lower elevation to a higher one. It is a fundamental component for simulating water transfer against a natural hydraulic gradient.

## Physics

The current `Pump` model is a simplified representation with a fixed-rate operation. Its behavior is governed by the following rules:

1.  **On/Off State:** The pump has two primary states: 'on' (`status` = 1) and 'off' (`status` = 0).
2.  **Flow Rate:** When the pump is 'on', it delivers its `max_flow_rate`, as long as the operational constraints are met. When 'off', the flow rate is zero.
3.  **Head Constraint:** The pump can only operate if the required head lift (the difference between the downstream and upstream water levels) is less than or equal to its `max_head` parameter. If the required head exceeds the maximum, the flow rate drops to zero even if the pump is 'on'.
4.  **Power Consumption:** When the pump is 'on' and successfully producing flow, it draws a fixed amount of power specified by `power_consumption_kw`.

This model is designed to be extended in the future to support more complex physics, such as variable speed drives or pump performance curves (flow vs. head).

## Parameters

- `max_flow_rate` (float): The fixed flow rate in m³/s that the pump provides when it is on and operating within its head limit.
- `max_head` (float): The maximum head difference (in meters) that the pump can overcome.
- `power_consumption_kw` (float): The power in kilowatts that the pump consumes when it is active and producing flow.

## State

- `status` (int): The operational status of the pump. 0 for 'off', 1 for 'on'.
- `flow_rate` (float): The calculated flow rate produced by the pump for the current time step, in m³/s.
- `power_draw_kw` (float): The power consumed by the pump in the current time step, in kilowatts.

## Control

The `Pump` is message-aware. It can be turned on or off by an agent publishing a message to its `action_topic`. The `control_signal` in the message should be `1` to turn the pump on and `0` to turn it off.

## Example Usage

```python
from swp.simulation_identification.physical_objects.pump import Pump
from swp.central_coordination.collaboration.message_bus import MessageBus

# A message bus is needed for agent-based control
message_bus = MessageBus()

# Define pump parameters and initial state
pump_params = {'max_flow_rate': 5, 'max_head': 20, 'power_consumption_kw': 75}
pump_state = {'status': 0} # Initially off

# Create the pump instance
pump = Pump(
    pump_id="pump1",
    initial_state=pump_state,
    params=pump_params,
    message_bus=message_bus,
    action_topic="action.pump1.status"
)

# An agent can now turn the pump on
# message_bus.publish("action.pump1.status", Message(content={'control_signal': 1}))
```

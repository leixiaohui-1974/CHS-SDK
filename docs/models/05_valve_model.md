# Valve Model

The `Valve` model represents a controllable valve within the water network. It simulates the flow of water through a pipe segment where the flow can be throttled. The valve's primary control parameter is its opening percentage, which ranges from 0% (fully closed) to 100% (fully open).

## Physics

The flow through the valve is calculated using a simplified orifice flow equation:

`Q = C_d_eff * A * sqrt(2 * g * Δh)`

Where:
- `Q` is the volumetric flow rate (m³/s).
- `C_d_eff` is the effective discharge coefficient. This is calculated by scaling the valve's maximum `discharge_coefficient` by its current opening percentage. For example, a valve that is 50% open will have a `C_d_eff` that is half of its maximum.
- `A` is the cross-sectional area of the pipe, determined by the `diameter` parameter.
- `g` is the acceleration due to gravity (9.81 m/s²).
- `Δh` is the head difference between the valve's upstream and downstream nodes.

The model assumes that flow only occurs in the downstream direction (i.e., when `Δh > 0`).

## Parameters

- `diameter` (float): The diameter of the pipe where the valve is installed, in meters.
- `discharge_coefficient` (float): The maximum discharge coefficient of the valve when it is fully open. This is a dimensionless value, typically between 0.6 and 0.9.

## State

- `opening` (float): The current opening of the valve, as a percentage (0-100).
- `flow_rate` (float): The calculated flow rate through the valve for the current time step, in m³/s.

## Control

The `Valve` is message-aware and can be controlled by an agent publishing to its designated `action_topic`. The control message should contain a `control_signal` with the desired opening percentage.

## Example Usage

Here is how to create a `Valve` instance in a simulation script:

```python
from swp.simulation_identification.physical_objects.valve import Valve
from swp.central_coordination.collaboration.message_bus import MessageBus

# A message bus is needed for agent-based control
message_bus = MessageBus()

# Define valve parameters and initial state
valve_params = {'diameter': 0.5, 'discharge_coefficient': 0.9}
valve_state = {'opening': 0} # Initially closed

# Create the valve instance
valve = Valve(
    valve_id="valve1",
    initial_state=valve_state,
    params=valve_params,
    message_bus=message_bus,
    action_topic="action.valve1.opening"
)

# An agent can now control the valve by publishing to "action.valve1.opening"
# message_bus.publish("action.valve1.opening", Message(content={'control_signal': 50}))
```

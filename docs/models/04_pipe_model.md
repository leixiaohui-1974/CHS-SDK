# Physical Models: Pipe

The `Pipe` model simulates the flow of water through a pressurized pipe. It connects two nodes in the water system and calculates the flow rate based on the head difference between them.

## Physical Principles

The model uses a simplified form of the **Darcy-Weisbach equation** to relate head loss to flow rate. The head loss ($H_f$) due to friction in a pipe is given by:

$H_f = f \frac{L}{D} \frac{V^2}{2g}$

Where:
- $f$ is the Darcy friction factor.
- $L$ is the length of the pipe.
- $D$ is the diameter of the pipe.
- $V$ is the average velocity of the water.
- $g$ is the acceleration due to gravity.

Since flow rate $Q = V \cdot A$ (where $A$ is the cross-sectional area), we can rearrange the equation to solve for $Q$:

$Q = A \sqrt{\frac{2 g D H_f}{f L}}$

For simulation purposes, we pre-calculate a `flow_coefficient` ($C$) that groups the constant physical parameters:

$C = A \sqrt{\frac{2 g D}{f L}}$

This simplifies the flow calculation in each simulation step to:

$Q = C \sqrt{H_f}$

The model assumes that the flow is turbulent and that it stabilizes within a single time step. It currently does not account for reverse flow; if the downstream head is higher than the upstream head, the flow is set to zero.

## State and Parameters

### State

-   `flow` (m³/s): The calculated flow rate through the pipe.
-   `outflow` (m³/s): Same as `flow`. This is the value used by downstream components.
-   `head_loss` (m): The difference between the upstream and downstream head.

### Parameters

When creating a `Pipe` instance, you must provide a `params` dictionary containing:
-   `length` (m): The length of the pipe.
-   `diameter` (m): The internal diameter of the pipe.
-   `friction_factor` (dimensionless): The Darcy friction factor for the pipe material (e.g., a typical value for cast iron is `0.02`).

## Example Usage

Here is how to create a `Pipe` instance:

```python
pipe = Pipe(
    pipe_id="pipe1",
    initial_state={'flow': 0},
    params={
        'length': 1000,  # 1 km
        'diameter': 1.5, # m
        'friction_factor': 0.02
    }
)
```

In the `SimulationHarness`, the `Pipe`'s `step()` method is called with an `action` dictionary that must contain the `upstream_head` and `downstream_head`, which the harness calculates from the connected components.

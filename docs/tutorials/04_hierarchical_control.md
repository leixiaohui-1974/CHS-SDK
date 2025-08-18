# Tutorial 4: Hierarchical Control with a Central Dispatcher

*This document is a placeholder for the fourth tutorial. The content below is an outline for future development.*

## 1. Introduction to Hierarchical Control

This tutorial introduces a two-level hierarchical control system. This is a common and powerful pattern in complex systems, where a high-level "supervisor" manages the goals of one or more low-level "operators".

We will explore the `example_hierarchical_control.py` script, which demonstrates:
- A `LocalControlAgent` performing its direct control task.
- A `CentralDispatcher` agent observing the system and changing the `LocalControlAgent`'s objective based on a high-level strategy.

## 2. The Two-Level Control Loop

The system operates on two nested control loops:
1.  **Low-Level Loop (Fast)**: The `LocalControlAgent` constantly tries to match its `setpoint` by controlling its gate. This is the same event-driven loop from Tutorial 3.
2.  **High-Level Loop (Slow/Strategic)**: The `CentralDispatcher` monitors the overall system state. When certain conditions are met (e.g., a flood risk), it intervenes by sending a new command to the low-level agent, effectively changing its goal.

## 3. Code Breakdown

### 3.1. Upgrading the `LocalControlAgent`
- A look at the new `command_topic` parameter in the agent's constructor.
- Explanation of the `handle_command_message` method, which allows the agent to be controlled from above.
- How the `PIDController`'s `set_setpoint` method enables this dynamic goal adjustment.

### 3.2. Implementing the `CentralDispatcher`
- How the dispatcher subscribes to system state topics (e.g., `state.reservoir.level`).
- A breakdown of the simple, rule-based logic in its `run()` method.
- How it publishes commands to the `LocalControlAgent`'s command topic.

## 4. Running the Simulation and Interpreting the Results

- How to run `example_hierarchical_control.py`.
- How to read the log to see the hierarchical interaction. Key things to look for:
  - The initial `CentralDispatcher` command changing the setpoint from 15.0 to 12.0 due to the high initial water level.
  - The `LocalControlAgent` acknowledging and applying this new setpoint.
  - How the system behaves differently once the water level drops below the dispatcher's threshold, causing it to issue a new "return to normal" command.

This example provides the foundation for building truly intelligent, multi-layered control systems where strategic, system-wide goals can be translated into concrete actions for local controllers.

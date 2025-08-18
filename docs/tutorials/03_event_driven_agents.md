# Tutorial 3: Event-Driven Agents and the Message Bus

*This document is a placeholder for the third tutorial. The content below is an outline for future development.*

## 1. A New Architecture: From Orchestration to Collaboration

This tutorial introduces the most advanced and powerful feature of the Smart Water Platform: the Multi-Agent System (MAS) architecture. We will move away from the centralized `SimulationHarness` logic used in the first two examples and explore a truly decoupled, event-driven system using the `example_mas_simulation.py` script.

In this architecture:
- **Agents are independent**: They don't know about each other; they only know about the `MessageBus`.
- **Communication is asynchronous**: Agents publish information to named "topics" and subscribe to the topics they care about.
- **The Harness is simplified**: The `SimulationHarness` becomes a simple timekeeper and physics engine, with no knowledge of the control logic.

## 2. Key Components in the MAS Architecture

### 2.1. The `MessageBus`
- The central nervous system of the platform.
- Explanation of the publish/subscribe (`pub/sub`) pattern.
- How topics (e.g., `state.reservoir.level`) are used to route information.

### 2.2. The `LocalControlAgent`
- This is a true, independent agent (unlike the simple `PIDController` used before).
- It **encapsulates** a controller algorithm.
- It **subscribes** to a state topic to get its input.
- It **publishes** its decisions to an action topic.

### 2.3. The Upgraded `DigitalTwinAgent`
- This agent now acts as a true sensor feed.
- It **publishes** the state of its associated physical model to the `MessageBus` at each time step.

### 2.4. Message-Aware Physical Models
- How the `Gate` model was upgraded to **subscribe** to an action topic, making it a self-contained component that listens for its own commands.

## 3. Code and Simulation Walkthrough

- A step-by-step breakdown of `example_mas_simulation.py`.
- How the `MessageBus` is created and shared among the agents and components.
- How the agents are instantiated and linked to their topics.
- A detailed look at the new `run_mas_simulation` method in the harness, highlighting the two-phase (Think/Act) process at each time step.

## 4. Why This Architecture Matters

- **Scalability**: New agents and components can be added to the system without modifying the existing ones.
- **Decoupling**: The control logic is fully separated from the physical models, allowing for easy swapping of algorithms.
- **Realism**: This architecture more closely mirrors how real-world distributed SCADA and control systems are built.

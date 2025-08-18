# Tutorial 2: Building a Multi-Component System

*This document is a placeholder for the second, more advanced tutorial. The content below is an outline for future development.*

## 1. Introduction

This tutorial builds upon the concepts from Tutorial 1 and demonstrates how to simulate a more complex system with multiple interacting components. We will explore the `example_multi_gate_river.py` script.

The goal of this scenario is to control a river system composed of a reservoir, an upstream gate, a river channel, and a downstream gate.

## 2. Scenario Overview

The system topology is as follows:
**`Reservoir` -> `Gate 1` -> `RiverChannel` -> `Gate 2`**

- **Gate 1**'s primary role is to control the water level of the **Reservoir**.
- **Gate 2**'s primary role is to control the water volume within the **RiverChannel**.

This introduces the concept of cascading effects and multiple control objectives within the same system.

## 3. Code Breakdown

### 3.1. Instantiating the Components
- A step-by-step look at creating the `Reservoir`, both `Gate` models, and the new `RiverChannel` model.
- Explanation of the parameters chosen for each component.

### 3.2. Configuring Multiple Controllers
- How to create two separate `PIDController` instances with different setpoints and gains for their unique objectives.
- How to associate each controller with the correct gate (`gate_1` and `gate_2`) in the `SimulationHarness`.

## 4. Understanding the Simulation Logic

- A deeper dive into the `SimulationHarness`'s execution loop.
- How the output of one component becomes the input for the next (e.g., how the discharge from `gate_1` becomes the inflow for the `RiverChannel`).
- How the presence of the downstream `RiverChannel` affects the discharge calculation of the upstream `gate_1` (the concept of `downstream_level`).

## 5. Running and Interpreting the Results

- How to run the `example_multi_gate_river.py` script.
- A guide to reading the log output, paying attention to both controller actions and how they affect different parts of the system simultaneously.
- Ideas for experimentation, such as changing controller setpoints to see how the system responds to conflicting objectives.

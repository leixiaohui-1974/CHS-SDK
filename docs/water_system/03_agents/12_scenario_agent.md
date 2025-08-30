# ScenarioAgent

The `ScenarioAgent` is a specialized agent responsible for managing and executing predefined test scenarios within the simulation. A scenario consists of a timeline of events that are injected into the system to test its response to various situations. These events can include disturbances like sudden rainfall or equipment failures, or they can be high-level commands issued at specific simulation times.

This agent is crucial for ensuring the robustness and reliability of the control strategies implemented in the water system. By simulating a wide range of scenarios, we can evaluate how the system behaves under both normal and exceptional conditions.

## How it Works

The `ScenarioAgent` operates on a `scenario_script`, which is a list of events scheduled to occur at specific times. The agent continuously checks the current simulation time against the event timeline. When the simulation time matches an event's scheduled time, the `ScenarioAgent` publishes the event's message to the specified topic on the `MessageBus`.

## Initialization

The `ScenarioAgent` is initialized with the following parameters:

- `agent_id` (str): A unique identifier for the agent.
- `message_bus` (MessageBus): An instance of the system's `MessageBus` for communication.
- `scenario_script` (List[Dict[str, Any]]): A list of timed events that define the scenario.

Each event in the `scenario_script` is a dictionary containing three keys:
- `time` (float): The simulation time at which the event should be executed.
- `topic` (str): The topic on the `MessageBus` to which the event message will be published.
- `message` (Any): The content of the message to be published.

The script is sorted by time upon initialization to ensure events are executed in the correct order.

## Usage Example

Here is an example of how to define a `scenario_script` and use it to initialize a `ScenarioAgent`.

### Scenario Script Definition

First, define the sequence of events for your scenario. For instance, you might want to simulate a sudden increase in water demand, followed by a pipe burst.

```python
scenario_script = [
    {
        'time': 100.0,
        'topic': 'water.demand.update',
        'message': {'zone': 'A', 'demand_increase': 0.5}
    },
    {
        'time': 250.0,
        'topic': 'infrastructure.failure',
        'message': {'type': 'pipe_burst', 'location': 'pipe_12', 'severity': 'high'}
    },
    {
        'time': 300.0,
        'topic': 'water.demand.update',
        'message': {'zone': 'A', 'demand_increase': 0.2}
    }
]
```

### Agent Initialization and Execution

Next, create an instance of the `ScenarioAgent` with this script and integrate it into the main simulation loop.

```python
from core_lib.mission.scenario_agent import ScenarioAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus

# Assume message_bus is an existing instance of MessageBus
message_bus = MessageBus()

# Initialize the ScenarioAgent
scenario_agent = ScenarioAgent(
    agent_id='scenario_agent_1',
    message_bus=message_bus,
    scenario_script=scenario_script
)

# In the main simulation loop
current_simulation_time = 0.0
time_step = 1.0

while current_simulation_time <= 500.0:
    # Other simulation logic...

    # Run the ScenarioAgent
    scenario_agent.run(current_time=current_simulation_time)

    # Other simulation logic...

    current_simulation_time += time_step
```

In this example, the `ScenarioAgent` will publish the demand update and pipe burst messages at the specified simulation times, allowing you to observe and validate the system's response.

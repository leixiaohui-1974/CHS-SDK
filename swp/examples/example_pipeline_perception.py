"""
Example: Testing the PipelinePerceptionAgent

This script demonstrates how to set up and run a simulation with a Pipe
and its corresponding PipelinePerceptionAgent. It verifies that the agent
correctly monitors the pipe's state and publishes it to the message bus.
"""
import sys
import os
from typing import List, Dict, Any

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swp.core_engine.agent_factory.factory import AgentFactory
from swp.central_coordination.collaboration.message_bus import MessageBus

# 1. Define a mock subscriber to capture messages from the bus
class MockSubscriber:
    def __init__(self):
        self.received_messages: List[Dict[str, Any]] = []

    def handle_message(self, message: Dict[str, Any]):
        print(f"MockSubscriber received message: {message}")
        self.received_messages.append(message)

# 2. Define the system configuration
PIPELINE_STATE_TOPIC = "state.pipe.main"
SYSTEM_CONFIG = {
    "components": [
        {
            "model": {
                "id": "pipe_1",
                "type": "Pipe",
                "initial_state": {"outflow": 0.0, "head_loss": 0.0},
                "params": {
                    "length": 1000,         # meters
                    "diameter": 0.5,        # meters
                    "friction_factor": 0.02
                }
            },
            "perception_agent": {
                "agent_id": "pa_pipe_1",
                "state_topic": PIPELINE_STATE_TOPIC
            }
        }
    ]
}

def run_test():
    """
    Runs the test scenario.
    """
    print("--- Starting PipelinePerceptionAgent Test ---")

    # 3. Initialize the Message Bus and Mock Subscriber
    bus = MessageBus()
    subscriber = MockSubscriber()
    bus.subscribe(PIPELINE_STATE_TOPIC, subscriber.handle_message)
    print(f"MockSubscriber subscribed to topic '{PIPELINE_STATE_TOPIC}'.")

    # 4. Initialize the Agent Factory and create the system
    factory = AgentFactory(message_bus=bus)
    agents, models = factory.create_system_from_config(SYSTEM_CONFIG)

    # Ensure the correct agent and model were created
    assert len(agents) == 1, "Expected one agent to be created"
    assert len(models) == 1, "Expected one model to be created"

    pipeline_agent = agents[0]
    pipe_model = models["pipe_1"]

    print(f"\n--- Running Simulation Step ---")

    # 5. Manually run the agent's logic
    # In a real simulation, a harness would call agent.run() at each time step.
    pipeline_agent.run(current_time=0)

    # 6. Verify the outcome
    print("\n--- Verifying Results ---")
    assert len(subscriber.received_messages) == 1, "Subscriber should have received exactly one message."

    received_state = subscriber.received_messages[0]
    original_state = pipe_model.get_state()

    assert received_state == original_state, "The state received by the subscriber should match the model's state."
    print("Verification successful: Agent published the correct state to the message bus.")

    # 7. (Optional) Simulate a change and re-run
    print("\n--- Simulating a State Change ---")
    # Simulate flow by providing upstream and downstream heads
    action = {'upstream_head': 10, 'downstream_head': 5}
    pipe_model.step(action=action, dt=1.0)
    print(f"Pipe model state updated: {pipe_model.get_state()}")

    # Run the agent again
    pipeline_agent.run(current_time=1)

    assert len(subscriber.received_messages) == 2, "Subscriber should now have two messages."
    new_received_state = subscriber.received_messages[1]
    new_original_state = pipe_model.get_state()
    assert new_received_state == new_original_state, "The new state should be correctly published."
    print("Second verification successful after state change.")

    print("\n--- PipelinePerceptionAgent Test Passed ---")


if __name__ == "__main__":
    run_test()

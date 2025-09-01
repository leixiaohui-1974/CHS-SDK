# -*- coding: utf-8 -*-

from core_lib.core.interfaces import Agent
import yaml

class LLMScenarioDesignerAgent(Agent):
    """
    Implements Role 2: Scenario Designer.

    This agent takes a natural language description of a complex event sequence
    and converts it into a structured YAML format that can be used by the
    `ScenarioAgent` to orchestrate events during a simulation.

    The LLM call is simulated in the `_call_llm_for_scenario` method.
    """

    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.scenario_scripts = {}

    def run(self, current_time: float):
        # This agent is typically used for pre-simulation setup,
        # so its run method might not be used in a running simulation.
        pass

    def step(self, t: int, dt: int):
        # This agent is typically used for pre-simulation setup.
        pass

    def design_scenario_from_description(self, description: str):
        """
        Generates a scenario event file from a natural language description.

        Args:
            description (str): e.g., "At timestep 100, fail pump_1 by setting its
                               status to 0. Then at timestep 200, start a heavy
                               rainfall event with an intensity of 50."
        """
        print(f"[{self.agent_id}] Received scenario description: '{description}'")
        print(f"[{self.agent_id}] Calling LLM to generate scenario script...")

        llm_output = self._call_llm_for_scenario(description)

        print(f"[{self.agent_id}] LLM call successful. Formatting scenario.")
        self.generated_scenario = yaml.dump({'scenario': llm_output})
        
        print(f"[{self.agent_id}] Scenario script generated successfully.")
        return self.generated_scenario

    def _call_llm_for_scenario(self, description: str) -> list:
        """
        [SIMULATED] This method simulates a call to an LLM.

        The LLM would be prompted to understand time-based events, agent actions,
        and parameter changes, returning a structured list of events.

        Returns:
            list: A list of event dictionaries for the ScenarioAgent.
        """
        # Hardcoded response for demonstration.
        events = []
        if "fail pump_1" in description and "rainfall" in description:
            events.append({
                'time': 100,
                'actions': [{
                    'agent_id': 'pump_control_agent', # An agent that can set status
                    'topic': 'pump_1.control.set_status',
                    'payload': {'status': 0}
                }]
            })
            events.append({
                'time': 200,
                'actions': [{
                    'agent_id': 'rainfall_agent_1',
                    'topic': 'rainfall.control.set_intensity',
                    'payload': {'intensity': 50.0} # mm/hr
                }]
            })
        return events

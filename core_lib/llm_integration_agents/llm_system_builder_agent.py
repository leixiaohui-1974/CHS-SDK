# -*- coding: utf-8 -*-

from core_lib.core.interfaces import BaseAgent
import yaml

class LLMSystemBuilderAgent(BaseAgent):
    """
    Implements Role 1: System Architect & Builder.

    This agent takes a high-level, natural language description of a water network
    and converts it into the structured YAML configuration files required by the
    simulation engine (`components.yml`, `topology.yml`, `agents.yml`).

    In this prototype, the LLM call is simulated. In a real implementation,
    the `_call_llm_for_config` method would make a request to an LLM API
    with a carefully crafted prompt.
    """
    def __init__(self, agent_id: str, message_bus):
        super().__init__(agent_id, message_bus)
        self.generated_configs = {}

    def step(self, t: int, dt: int):
        # This agent is typically used for pre-simulation setup,
        # so its step method might not be used in a running simulation.
        pass

    def build_system_from_description(self, description: str):
        """
        Takes a natural language description and generates system configuration files.

        Args:
            description (str): A natural language text describing the water system.
                               e.g., "A reservoir feeds a single river channel through a gate."
        """
        print(f"[{self.id}] Received system description: '{description}'")
        print(f"[{self.id}] Calling LLM to generate configuration...")

        # In a real implementation, this would involve a complex prompt explaining
        # the YAML structure and providing examples.
        llm_output = self._call_llm_for_config(description)

        print(f"[{self.id}] LLM call successful. Parsing generated configurations.")
        self.generated_configs = {
            'components': yaml.dump(llm_output['components']),
            'topology': yaml.dump(llm_output['topology']),
            'agents': yaml.dump(llm_output['agents'])
        }

        print(f"[{self.id}] System configuration generated successfully.")
        return self.generated_configs

    def _call_llm_for_config(self, description: str) -> dict:
        """
        [SIMULATED] This method simulates a call to an LLM.

        The LLM would be prompted to return a JSON or YAML object containing the
        three required configuration sections.

        Args:
            description (str): The natural language input.

        Returns:
            dict: A dictionary containing the structured configuration.
        """
        # This is a hardcoded response for demonstration purposes.
        # A real LLM would generate this based on the description.
        if "reservoir" in description.lower() and "gate" in description.lower():
            return {
                'components': {
                    'reservoir_1': {
                        'type': 'Reservoir',
                        'params': {'initial_storage': 1000000, 'area': 50000}
                    },
                    'gate_1': {
                        'type': 'Gate',
                        'params': {'width': 5.0, 'discharge_coefficient': 0.8}
                    },
                    'channel_1': {
                        'type': 'RiverChannel',
                        'params': {'length': 1000, 'slope': 0.001, 'manning': 0.03}
                    }
                },
                'topology': {
                    'connections': [
                        {'from': 'reservoir_1', 'to': 'gate_1'},
                        {'from': 'gate_1', 'to': 'channel_1'}
                    ]
                },
                'agents': {
                    'reservoir_perception_agent': {
                        'type': 'ReservoirPerceptionAgent',
                        'params': {'physical_component_id': 'reservoir_1'}
                    },
                    'gate_control_agent': {
                        'type': 'GateControlAgent',
                        'params': {
                            'physical_component_id': 'gate_1',
                            'controller_configs': {'type': 'PID', 'kp': 1.0, 'ki': 0.1}
                        }
                    }
                }
            }
        else:
            # Default empty response if the description is not recognized
            return {'components': {}, 'topology': {}, 'agents': {}}

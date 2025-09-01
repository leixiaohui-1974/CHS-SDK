# -*- coding: utf-8 -*-

from core_lib.core.interfaces import Agent

class LLMDispatchCommanderAgent(Agent):
    """
    Implements Role 3: Intelligent Dispatch Commander.

    This agent acts as the bridge between a human operator (or a high-level AI)
    and the `CentralDispatcherAgent`. It listens for high-level natural language
    commands, uses a (simulated) LLM to interpret them, and translates them into
    structured commands that the `CentralDispatcherAgent` can execute.
    """

    def __init__(self, agent_id: str, message_bus, central_dispatcher_id: str):
        super().__init__(agent_id, message_bus)
        self.central_dispatcher_id = central_dispatcher_id
        
        # Topic for receiving high-level natural language commands
        self.command_topic = f"{self.id}.command.natural_language"
        
        # Topic to send structured commands to the Central Dispatcher
        self.dispatcher_control_topic = f"{self.central_dispatcher_id}.control.set_strategy"
        
        self._message_bus.subscribe(self.command_topic, self.handle_command)

    def run(self, current_time: float):
        # This agent is event-driven and responds to messages,
        # so its run method might not be used in a running simulation.
        pass
        print(f"[{self.id}] Initialized. Listening for commands on '{self.command_topic}'.")

    def handle_command(self, topic: str, payload: dict):
        """Callback to handle incoming natural language commands."""
        command = payload.get('text', '')
        print(f"[{self.id}] Received command: '{command}'")
        
        # Use LLM to interpret the command and generate a structured strategy
        structured_command = self._call_llm_for_dispatch_strategy(command)
        
        if structured_command:
            print(f"[{self.id}] Interpreted strategy: {structured_command}")
            print(f"[{self.id}] Publishing structured command to '{self.dispatcher_control_topic}'")
            self._message_bus.publish(self.dispatcher_control_topic, structured_command)
        else:
            print(f"[{self.id}] Could not interpret the command.")

    def _call_llm_for_dispatch_strategy(self, command: str) -> dict:
        """
        [SIMULATED] This method simulates an LLM call to interpret a dispatch command.
        
        The LLM would parse the intent, goals, and constraints from the text.
        
        Returns:
            dict: A structured command for the CentralDispatcherAgent.
        """
        command_lower = command.lower()
        if "prioritize flood control" in command_lower:
            return {
                'mode': 'emergency',
                'params': {
                    'priority': 'flood_control',
                    'target_water_level': 135.0, # Target flood limit level
                    'target_reservoirs': ['reservoir_1']
                }
            }
        elif "maximize profit" in command_lower or "economic benefit" in command_lower:
            return {
                'mode': 'mpc_optimization',
                'params': {
                    'objective': 'maximize_profit',
                    'constraints': {
                        'min_ecological_flow': 5.0
                    }
                }
            }
        else:
            return None

    def step(self, t: int, dt: int):
        # This agent is event-driven, so the step function is passive.
        pass

"""
Agent Factory for automated generation of agents and systems.
"""
from typing import Dict, Any, List
from swp.core.interfaces import Agent
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.control.pid_controller import PIDController

class AgentFactory:
    """
    The Agent Factory is a core component of the "Mother Machine".

    It takes a high-level system configuration and automatically builds the
    entire system from it, including physical models, digital twin agents,
    and control agents. This enables rapid setup of new simulation scenarios
    and automated system generation.
    """

    def __init__(self):
        print("AgentFactory created.")

    def create_system_from_config(self, config: Dict[str, Any]) -> List[Agent]:
        """
        Builds an entire system of agents and models from a config dictionary.

        Args:
            config: A dictionary describing the system to be built.

        Returns:
            A list of all agents created for the system.
        """
        print("Creating system from configuration...")
        agents = []

        # Example of creating a local control agent setup from config
        if 'local_control_setups' in config:
            for setup_config in config['local_control_setups']:
                # 1. Create the physical object model
                if setup_config['model']['type'] == 'Reservoir':
                    model = Reservoir(
                        reservoir_id=setup_config['model']['id'],
                        initial_state=setup_config['model']['initial_state'],
                        params=setup_config['model']['params']
                    )
                elif setup_config['model']['type'] == 'Gate':
                    model = Gate(
                        gate_id=setup_config['model']['id'],
                        initial_state=setup_config['model']['initial_state'],
                        params=setup_config['model']['params']
                    )
                else:
                    continue # Skip unknown model types

                # 2. Create the Digital Twin (Perception Agent)
                twin_agent = DigitalTwinAgent(
                    agent_id=f"twin_{model.reservoir_id if hasattr(model, 'reservoir_id') else model.gate_id}",
                    simulated_object=model
                )
                agents.append(twin_agent)

                # 3. Create the Controller
                if setup_config['controller']['type'] == 'PID':
                    controller = PIDController(
                        **setup_config['controller']['params']
                    )

                # Here you would create a LocalControlAgent that USES the controller.
                # For simplicity in this stub, we won't define a separate LocalControlAgent class yet.

        print(f"System created with {len(agents)} agents.")
        return agents

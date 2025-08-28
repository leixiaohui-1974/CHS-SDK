"""
Agent Factory for automated generation of agents and systems.
"""
from typing import Dict, Any, List, Tuple
from swp.core.interfaces import Agent, Simulatable
from swp.simulation_identification.physical_objects.reservoir import Reservoir
from swp.simulation_identification.physical_objects.gate import Gate
from swp.simulation_identification.physical_objects.pipe import Pipe
from swp.simulation_identification.physical_objects.pump import Pump, PumpStation
from swp.simulation_identification.physical_objects.valve import Valve, ValveStation
from swp.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from swp.local_agents.perception.pipeline_perception_agent import PipelinePerceptionAgent
from swp.local_agents.perception.pump_station_perception_agent import PumpStationPerceptionAgent
from swp.local_agents.perception.valve_station_perception_agent import ValveStationPerceptionAgent
from swp.local_agents.control.pid_controller import PIDController
from swp.local_agents.control.pump_station_control_agent import PumpStationControlAgent
from swp.local_agents.control.valve_station_control_agent import ValveStationControlAgent
from swp.central_coordination.collaboration.message_bus import MessageBus


class AgentFactory:
    """
    The Agent Factory is a core component of the "Mother Machine".

    It takes a high-level system configuration and automatically builds the
    entire system from it, including physical models, digital twin agents,
    and control agents. This enables rapid setup of new simulation scenarios
    and automated system generation.
    """

    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        print("AgentFactory created and linked with a message bus.")

    def create_system_from_config(self, config: Dict[str, Any]) -> Tuple[List[Agent], Dict[str, Simulatable]]:
        """
        Builds an entire system of agents and models from a config dictionary.

        Args:
            config: A dictionary describing the system to be built.

        Returns:
            A tuple containing:
            - A list of all agents created for the system.
            - A dictionary of all models created, keyed by their ID.
        """
        print("Creating system from configuration...")
        agents: List[Agent] = []
        models: Dict[str, Simulatable] = {}

        if 'components' in config:
            for comp_config in config['components']:
                # 1. Create the physical object model
                model_config = comp_config['model']
                model_type = model_config['type']
                model_id = model_config['id']
                model: Simulatable

                if model_type == 'Reservoir':
                    model = Reservoir(
                        name=model_id,
                        initial_state=model_config['initial_state'],
                        parameters=model_config['params']
                    )
                elif model_type == 'Gate':
                    model = Gate(
                        name=model_id,
                        initial_state=model_config['initial_state'],
                        parameters=model_config['params']
                    )
                elif model_type == 'Pipe':
                    model = Pipe(
                        name=model_id,
                        initial_state=model_config['initial_state'],
                        parameters=model_config['params']
                    )
                elif model_type == 'PumpStation':
                    pumps = []
                    for pump_config in model_config['pumps']:
                        pump = Pump(
                            name=pump_config['id'],
                            initial_state=pump_config['initial_state'],
                            parameters=pump_config['params'],
                            message_bus=self.bus,
                            action_topic=pump_config.get('action_topic')
                        )
                        pumps.append(pump)
                    model = PumpStation(
                        name=model_id,
                        initial_state=model_config['initial_state'],
                        parameters=model_config['params'],
                        pumps=pumps
                    )
                elif model_type == 'ValveStation':
                    valves = []
                    for valve_config in model_config['valves']:
                        valve = Valve(
                            name=valve_config['id'],
                            initial_state=valve_config['initial_state'],
                            parameters=valve_config['params'],
                            message_bus=self.bus,
                            action_topic=valve_config.get('action_topic')
                        )
                        valves.append(valve)
                    model = ValveStation(
                        name=model_id,
                        initial_state=model_config['initial_state'],
                        parameters=model_config['params'],
                        valves=valves
                    )
                else:
                    print(f"Warning: Unknown model type '{model_type}' in config. Skipping.")
                    continue

                models[model_id] = model

                # 2. Create the Perception Agent (if specified)
                if 'perception_agent' in comp_config:
                    pa_config = comp_config['perception_agent']
                    pa_id = pa_config['agent_id']
                    pa_topic = pa_config['state_topic']

                    if isinstance(model, Pipe):
                        perception_agent = PipelinePerceptionAgent(
                            agent_id=pa_id,
                            pipe_model=model,
                            message_bus=self.bus,
                            state_topic=pa_topic
                        )
                    elif isinstance(model, PumpStation):
                        perception_agent = PumpStationPerceptionAgent(
                            agent_id=pa_id,
                            pump_station_model=model,
                            message_bus=self.bus,
                            state_topic=pa_topic
                        )
                    elif isinstance(model, ValveStation):
                        perception_agent = ValveStationPerceptionAgent(
                            agent_id=pa_id,
                            valve_station_model=model,
                            message_bus=self.bus,
                            state_topic=pa_topic
                        )
                    else:
                        # Use the generic DigitalTwinAgent for other models
                        perception_agent = DigitalTwinAgent(
                            agent_id=pa_id,
                            simulated_object=model,
                            message_bus=self.bus,
                            state_topic=pa_topic
                        )
                    agents.append(perception_agent)

                # 3. Create the Control Agent (if specified)
                if 'control_agent' in comp_config:
                    ca_config = comp_config['control_agent']
                    ca_type = ca_config.get('type')

                    if ca_type == 'PumpStationControlAgent' and isinstance(model, PumpStation):
                        pump_action_topics = [p_conf.get('action_topic') for p_conf in model_config.get('pumps', [])]
                        control_agent = PumpStationControlAgent(
                            agent_id=ca_config['agent_id'],
                            message_bus=self.bus,
                            goal_topic=ca_config['goal_topic'],
                            state_topic=comp_config['perception_agent']['state_topic'],
                            pump_action_topics=pump_action_topics
                        )
                        agents.append(control_agent)
                    elif ca_type == 'ValveStationControlAgent' and isinstance(model, ValveStation):
                        valve_action_topics = [v_conf.get('action_topic') for v_conf in model_config.get('valves', [])]
                        control_agent = ValveStationControlAgent(
                            agent_id=ca_config['agent_id'],
                            message_bus=self.bus,
                            goal_topic=ca_config['goal_topic'],
                            state_topic=comp_config['perception_agent']['state_topic'],
                            valve_action_topics=valve_action_topics,
                            kp=ca_config.get('kp', 0.1)
                        )
                        agents.append(control_agent)
                    else:
                        # Placeholder for other control agents
                        pass

        print(f"System created with {len(agents)} agents and {len(models)} models.")
        return agents, models

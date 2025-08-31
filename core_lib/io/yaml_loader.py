"""
Loads a simulation scenario from a set of YAML configuration files.
"""
import yaml
from pathlib import Path
import logging
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.io.object_factory import ObjectFactory

class BaseYamlLoader:
    """
    Base class for loading YAML files from a directory.
    """
    def __init__(self, scenario_path: str):
        self.scenario_path = Path(scenario_path)

    def _load_yaml(self, file_name: str):
        """Loads a single YAML file from the scenario directory."""
        file_path = self.scenario_path / file_name
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Configuration file not found: {file_path}. Skipping.")
            return None
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return None

class SimulationBuilder(BaseYamlLoader):
    """
    Reads a directory of YAML files to configure and instantiate a simulation.
    """

    def __init__(self, scenario_path: str, agents_file: str = 'agents.yml'):
        """
        Initializes the loader with the path to the scenario directory.
        """
        super().__init__(scenario_path)
        self.config = self._load_yaml('config.yml')
        self.components_config = self._load_yaml('components.yml')
        self.topology_config = self._load_yaml('topology.yml')
        self.agents_config = self._load_yaml(agents_file)

        self.harness = None
        self.message_bus = None
        self.component_instances = {}
        self.object_factory = None
        logging.info(f"SimulationBuilder initialized for scenario: {self.scenario_path.name}")

    def load(self) -> SimulationHarness:
        """
        Loads, instantiates, and wires up the full simulation.
        """
        if not all([self.config, self.components_config, self.topology_config]):
            raise ValueError("Core configuration files (config, components, topology) are missing.")

        self._setup_infrastructure()
        self._load_components()
        self._load_topology()

        if self.agents_config:
            self._load_agents_and_controllers()
        else:
            logging.warning("Agents file not found or is empty. Running a non-agent simulation.")

        logging.info("Simulation loaded successfully. Building harness...")
        self.harness.build()
        logging.info("Harness built. Loader is ready.")
        return self.harness

    def _setup_infrastructure(self):
        """Initializes the message bus, simulation harness and object factory."""
        logging.info("Setting up simulation infrastructure...")
        self.message_bus = MessageBus()
        sim_config = self.config.get('simulation', {})
        self.harness = SimulationHarness(config=sim_config)

        context = {
            'message_bus': self.message_bus,
            'dt': self.harness.config.get('dt')
        }
        DEFAULT_CLASS_MAP = {
            # Physical Objects
            "Reservoir": "core_lib.physical_objects.reservoir.Reservoir",
            "Gate": "core_lib.physical_objects.gate.Gate",
            "UnifiedCanal": "core_lib.physical_objects.unified_canal.UnifiedCanal",
            "Pipe": "core_lib.physical_objects.pipe.Pipe",
            "Pump": "core_lib.physical_objects.pump.Pump",
            "Valve": "core_lib.physical_objects.valve.Valve",
            "HydropowerStation": "core_lib.physical_objects.hydropower_station.HydropowerStation",
            "Lake": "core_lib.physical_objects.lake.Lake",
            "RiverChannel": "core_lib.physical_objects.river_channel.RiverChannel",
            "WaterTurbine": "core_lib.physical_objects.water_turbine.WaterTurbine",
            "RainfallRunoff": "core_lib.physical_objects.rainfall_runoff.RainfallRunoff",
            "IntegralDelayCanal": "core_lib.physical_objects.integral_delay_canal.IntegralDelayCanal",

            # Agents & Controllers
            "PIDController": "core_lib.local_agents.control.pid_controller.PIDController",
            "LocalControlAgent": "core_lib.local_agents.control.local_control_agent.LocalControlAgent",
            "DigitalTwinAgent": "core_lib.local_agents.perception.digital_twin_agent.DigitalTwinAgent",
            "ParameterIdentificationAgent": "core_lib.identification.identification_agent.ParameterIdentificationAgent",
            "CentralDispatcherAgent": "core_lib.central_coordination.dispatch.central_dispatcher.CentralDispatcherAgent",
            "CsvInflowAgent": "core_lib.data_access.csv_inflow_agent.CsvInflowAgent",
            "EmergencyAgent": "core_lib.local_agents.supervisory.emergency_agent.EmergencyAgent",
            "TopicLoggerAgent": "core_lib.local_agents.utility.topic_logger_agent.TopicLoggerAgent",
        }
        self.object_factory = ObjectFactory(context, class_map=DEFAULT_CLASS_MAP)


    def _load_components(self):
        """Loads and instantiates all physical components."""
        logging.info("Loading physical components...")
        for comp_conf in self.components_config.get('components', []):
            comp_id = comp_conf.pop('id')

            # Resolve obj_id references to component instances
            def resolve_obj_ids(d):
                for k, v in d.items():
                    if isinstance(v, dict):
                        if 'obj_id' in v:
                            obj_id = v.pop('obj_id')
                            d[k] = self.component_instances[obj_id]
                        else:
                            resolve_obj_ids(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                resolve_obj_ids(item)

            resolve_obj_ids(comp_conf)

            instance = self.object_factory.create(comp_conf, name=comp_id)
            self.harness.add_component(comp_id, instance)
            self.component_instances[comp_id] = instance
        logging.info(f"Loaded {len(self.component_instances)} components.")

    def _load_topology(self):
        """Loads and defines the connections between components."""
        logging.info("Loading topology...")
        topology_for_bus = {}
        for conn_conf in self.topology_config.get('connections', []):
            upstream_id = conn_conf['upstream']
            downstream_id = conn_conf['downstream']

            logging.info(f"  - Connecting '{upstream_id}' -> '{downstream_id}'")
            self.harness.add_connection(upstream_id, downstream_id)

            if upstream_id not in topology_for_bus:
                topology_for_bus[upstream_id] = {}
            if downstream_id not in topology_for_bus:
                topology_for_bus[downstream_id] = {}

            topology_for_bus[upstream_id]['downstream'] = downstream_id
            topology_for_bus[downstream_id]['upstream'] = upstream_id

        self.message_bus.set_component_topology(topology_for_bus)
        logging.info("Topology loaded.")

    def _load_agents_and_controllers(self):
        """Loads and instantiates all agents and controllers."""
        logging.info("Loading agents and controllers...")

        # Load controllers
        if 'controllers' in self.agents_config:
            for controller_conf in self.agents_config.get('controllers', []):
                controller_id = controller_conf.pop('id')
                controlled_id = controller_conf.pop('controlled_id')
                observed_id = controller_conf.pop('observed_id')
                observation_key = controller_conf.pop('observation_key')

                instance = self.object_factory.create(controller_conf, controller_id=controller_id)
                self.harness.add_controller(
                    controller_id=controller_id,
                    controller=instance,
                    controlled_id=controlled_id,
                    observed_id=observed_id,
                    observation_key=observation_key
                )

        # Load agents
        if 'agents' in self.agents_config:
            for agent_conf in self.agents_config.get('agents', []):
                agent_id = agent_conf.pop('id')
                class_name = agent_conf.get('class')

                # Resolve obj_id references to component instances
                def resolve_obj_ids(d):
                    for k, v in list(d.items()):
                        if k == 'obj_id' or k == 'simulated_object_id' or k == 'target_model_id' or k == 'target_component_id':
                            if k == 'simulated_object_id':
                                d['simulated_object'] = self.component_instances[v]
                            elif k == 'target_model_id':
                                d['target_model'] = self.component_instances[v]
                            elif k == 'target_component_id':
                                d['target_component'] = self.component_instances[v]
                            else:
                                d['obj'] = self.component_instances[v]
                            del d[k]
                        elif isinstance(v, dict):
                            resolve_obj_ids(v)
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict):
                                    resolve_obj_ids(item)

                resolve_obj_ids(agent_conf)

                # Special handling for CsvInflowAgent to resolve relative path
                if class_name and 'CsvInflowAgent' in class_name:
                    if 'config' in agent_conf and 'csv_file' in agent_conf['config']:
                        csv_file = agent_conf['config'].pop('csv_file')
                        agent_conf['config']['csv_file_path'] = self.scenario_path / csv_file

                # The object factory will unpack the 'config' block from the YAML
                # into keyword arguments for the agent's constructor.
                instance = self.object_factory.create(agent_conf, agent_id=agent_id)

                self.harness.add_agent(instance)
        logging.info("Agents and controllers loaded.")

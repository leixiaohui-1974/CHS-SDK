"""
Loads a simulation scenario from a set of YAML configuration files.
"""
import yaml
from pathlib import Path
import logging
import importlib

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.central_coordination.collaboration.message_bus import MessageBus

class SimulationLoader:
    """
    Reads a directory of YAML files to configure and instantiate a simulation,
    including the physical components, topology, agents, and controllers.
    """

    def __init__(self, scenario_path: str):
        """
        Initializes the loader with the path to the scenario directory.

        Args:
            scenario_path: The path to the directory containing config.yml,
                           components.yml, topology.yml, and agents.yml.
        """
        self.scenario_path = Path(scenario_path)
        self.config = self._load_yaml('config.yml')
        self.components_config = self._load_yaml('components.yml')
        self.topology_config = self._load_yaml('topology.yml')
        self.agents_config = self._load_yaml('agents.yml')

        self.harness = None
        self.message_bus = None
        self.component_instances = {}

        logging.info(f"SimulationLoader initialized for scenario: {self.scenario_path.name}")

    def _instantiate_object(self, config: dict) -> object:
        """
        Instantiates an object from a configuration dictionary that has a 'class' key.
        """
        class_name = config['class']
        ObjectClass = self._get_class(class_name)

        object_config = config.get('config', {})

        import inspect
        final_args = object_config.copy()
        sig = inspect.signature(ObjectClass.__init__)

        # Inject dependencies like message_bus if the constructor needs them
        if 'message_bus' in sig.parameters:
            final_args['message_bus'] = self.message_bus

        return ObjectClass(**final_args)

    def _load_yaml(self, file_name: str):
        """Loads a single YAML file from the scenario directory."""
        file_path = self.scenario_path / file_name
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {file_path}")
            return None
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return None

    def load(self) -> SimulationHarness:
        """
        Loads, instantiates, and wires up the full simulation.

        Returns:
            A fully configured SimulationHarness instance, ready to be run.
        """
        if not all([self.config, self.components_config, self.topology_config, self.agents_config]):
            raise ValueError("One or more configuration files failed to load. Cannot build simulation.")

        self._setup_infrastructure()
        self._load_components()
        self._load_topology()
        self._load_agents_and_controllers()

        logging.info("Simulation loaded successfully. Building harness...")
        self.harness.build()
        logging.info("Harness built. Loader is ready.")
        return self.harness

    def _get_class(self, class_path: str):
        """
        Dynamically imports and returns a class object from a string path.
        It first checks a map of short names and then falls back to importing
        the path directly.
        """
        CLASS_MAP = {
            # Physical Components
            "Reservoir": "core_lib.physical_objects.reservoir.Reservoir",
            "Gate": "core_lib.physical_objects.gate.Gate",
            "Canal": "core_lib.physical_objects.canal.Canal",
            "IntegralDelayCanal": "core_lib.physical_objects.integral_delay_canal.IntegralDelayCanal",
            "Pipe": "core_lib.physical_objects.pipe.Pipe",
            "Valve": "core_lib.physical_objects.valve.Valve",

            # Controllers
            "PIDController": "core_lib.local_agents.control.pid_controller.PIDController",

            # Agents
            "LocalControlAgent": "core_lib.local_agents.control.local_control_agent.LocalControlAgent",
            "DigitalTwinAgent": "core_lib.local_agents.perception.digital_twin_agent.DigitalTwinAgent",
            "EmergencyAgent": "core_lib.local_agents.supervisory.emergency_agent.EmergencyAgent",
            "CentralDispatcherAgent": "core_lib.local_agents.supervisory.central_dispatcher_agent.CentralDispatcherAgent",
            "CsvInflowAgent": "core_lib.data_access.csv_inflow_agent.CsvInflowAgent",
            "ParameterIdentificationAgent": "core_lib.identification.identification_agent.ParameterIdentificationAgent",
            "ModelUpdaterAgent": "core_lib.identification.model_updater_agent.ModelUpdaterAgent",
            "ConstantValueAgent": "core_lib.local_agents.utility.constant_value_agent.ConstantValueAgent",
        }

        full_class_path = CLASS_MAP.get(class_path, class_path)

        try:
            module_name, class_name = full_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            logging.error(f"Could not find or import class '{class_path}' from path '{full_class_path}': {e}")
            raise ImportError(f"Could not find or import class '{class_path}'") from e

    def _setup_infrastructure(self):
        """Initializes the message bus and simulation harness."""
        logging.info("Setting up simulation infrastructure...")
        self.message_bus = MessageBus()
        sim_config = self.config.get('simulation', {})
        self.harness = SimulationHarness(config=sim_config)

    def _load_components(self):
        """Loads and instantiates all physical components."""
        logging.info("Loading physical components...")
        for comp_conf in self.components_config.get('components', []):
            comp_id = comp_conf.pop('id')
            comp_class_name = comp_conf.pop('class')

            logging.info(f"  - Creating component '{comp_id}' of class '{comp_class_name}'")
            CompClass = self._get_class(comp_class_name)

            # Pass all remaining yaml keys as kwargs to the constructor
            args = { 'name': comp_id, **comp_conf }

            # Inspect constructor signature to see if it accepts message_bus
            import inspect
            sig = inspect.signature(CompClass.__init__)
            has_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())

            if 'message_bus' in sig.parameters or has_kwargs:
                args['message_bus'] = self.message_bus

            instance = CompClass(**args)

            self.harness.add_component(instance)
            self.component_instances[comp_id] = instance
        logging.info(f"Loaded {len(self.component_instances)} components.")

    def _load_topology(self):
        """Loads and defines the connections between components."""
        logging.info("Loading topology...")
        for conn_conf in self.topology_config.get('connections', []):
            upstream_id = conn_conf['upstream']
            downstream_id = conn_conf['downstream']

            logging.info(f"  - Connecting '{upstream_id}' -> '{downstream_id}'")
            self.harness.add_connection(upstream_id, downstream_id)
        logging.info("Topology loaded.")

    def _load_agents_and_controllers(self):
        """Loads and instantiates all agents and controllers."""
        logging.info("Loading agents and controllers...")

        for agent_conf in self.agents_config.get('agents', []):
            agent_id = agent_conf.pop('id')
            agent_class_name = agent_conf.pop('class')

            logging.info(f"  - Creating agent '{agent_id}' of class '{agent_class_name}'")
            AgentClass = self._get_class(agent_class_name)

            # Unpack the 'config' block if it exists
            if 'config' in agent_conf:
                config_block = agent_conf.pop('config')
                agent_conf.update(config_block)

            # --- Handle all special argument adaptations before calling the constructor ---
            if 'simulated_object_id' in agent_conf:
                sim_obj_id = agent_conf.pop('simulated_object_id')
                agent_conf['simulated_object'] = self.component_instances[sim_obj_id]

            if 'target_component_id' in agent_conf:
                target_comp_id = agent_conf.pop('target_component_id')
                agent_conf['target_component'] = self.component_instances[target_comp_id]

            if agent_class_name == 'CsvInflowAgent':
                if 'csv_file' in agent_conf:
                    agent_conf['csv_file_path'] = str(self.scenario_path / agent_conf.pop('csv_file'))
                if 'value_column' in agent_conf:
                    agent_conf['data_column'] = agent_conf.pop('value_column')
                if 'output_topic' in agent_conf:
                    agent_conf['inflow_topic'] = agent_conf.pop('output_topic')
                agent_conf.pop('data_id', None)

            # Recursively instantiate any nested components (like controllers)
            for key, value in agent_conf.items():
                if isinstance(value, dict) and 'class' in value:
                    logging.info(f"    - Found nested object '{key}' of class '{value['class']}'")
                    agent_conf[key] = self._instantiate_object(value)

            # Special handling for ParameterIdentificationAgent constructor
            if agent_class_name == 'ParameterIdentificationAgent':
                target_model_id = agent_conf.pop('target_model_id')
                target_model_instance = self.component_instances[target_model_id]
                instance = AgentClass(
                    agent_id=agent_id,
                    message_bus=self.message_bus,
                    target_model=target_model_instance,
                    config=agent_conf
                )
            else:
                # --- Generic constructor call with argument adaptation ---
                final_args = {'agent_id': agent_id, 'message_bus': self.message_bus, **agent_conf}

                # Inject 'dt' from global sim config if the agent constructor accepts it
                import inspect
                sig = inspect.signature(AgentClass.__init__)
                if 'dt' in sig.parameters and 'dt' not in final_args:
                    if self.harness.config and 'dt' in self.harness.config:
                        final_args['dt'] = self.harness.config['dt']

                instance = AgentClass(**final_args)
            self.harness.add_agent(instance)

        for ctrl_conf in self.agents_config.get('controllers', []):
            ctrl_id = ctrl_conf.pop('id')
            ctrl_class_name = ctrl_conf.pop('class')

            logging.info(f"  - Creating controller '{ctrl_id}' of class '{ctrl_class_name}'")
            CtrlClass = self._get_class(ctrl_class_name)

            controlled_id = ctrl_conf.pop('controlled_id')
            observed_id = ctrl_conf.pop('observed_id')
            observation_key = ctrl_conf.pop('observation_key')

            # The rest of the config goes into the controller's constructor
            config = ctrl_conf.get('config', {})
            controller_instance = CtrlClass(**config)

            self.harness.add_controller(
                controller_id=ctrl_id,
                controller=controller_instance,
                controlled_id=controlled_id,
                observed_id=observed_id,
                observation_key=observation_key
            )

        logging.info("Agents and controllers loaded.")

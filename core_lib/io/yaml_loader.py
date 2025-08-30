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
    Reads a directory of YAML files to configure and instantiate a simulation.
    """

    def __init__(self, scenario_path: str, agents_file: str = 'agents.yml'):
        """
        Initializes the loader with the path to the scenario directory.

        Args:
            scenario_path: The path to the directory containing config.yml, etc.
            agents_file: The name of the agents configuration file to load.
        """
        self.scenario_path = Path(scenario_path)
        self.config = self._load_yaml('config.yml')
        self.components_config = self._load_yaml('components.yml')
        self.topology_config = self._load_yaml('topology.yml')
        self.agents_config = self._load_yaml(agents_file) # Use the specified agents file

        self.harness = None
        self.message_bus = None
        self.component_instances = {}
        logging.info(f"SimulationLoader initialized for scenario: {self.scenario_path.name}")
        logging.info(f"Using agents configuration: {agents_file}")

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

        if 'dt' in sig.parameters and 'dt' not in final_args:
            if self.harness and self.harness.config and 'dt' in self.harness.config:
                final_args['dt'] = self.harness.config['dt']

        return ObjectClass(**final_args)

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
            logging.warning(f"Agents file not found or is empty. Running a non-agent simulation.")

        logging.info("Simulation loaded successfully. Building harness...")
        self.harness.build()
        logging.info("Harness built. Loader is ready.")
        return self.harness

    def _get_class(self, class_path: str):
        """
        Dynamically imports and returns a class object from a string path.
        """
        CLASS_MAP = {
            "Reservoir": "core_lib.physical_objects.reservoir.Reservoir",
            "Gate": "core_lib.physical_objects.gate.Gate",
            "UnifiedCanal": "core_lib.physical_objects.unified_canal.UnifiedCanal",
            "PIDController": "core_lib.local_agents.control.pid_controller.PIDController",
            "LocalControlAgent": "core_lib.local_agents.control.local_control_agent.LocalControlAgent",
            "DigitalTwinAgent": "core_lib.local_agents.perception.digital_twin_agent.DigitalTwinAgent",
        }
        full_class_path = CLASS_MAP.get(class_path, class_path)
        try:
            module_name, class_name = full_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
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
            CompClass = self._get_class(comp_conf.pop('class'))
            args = { 'name': comp_id, **comp_conf }
            import inspect
            sig = inspect.signature(CompClass.__init__)
            has_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
            if 'message_bus' in sig.parameters or has_kwargs:
                args['message_bus'] = self.message_bus
            if not has_kwargs:
                valid_args = list(sig.parameters.keys())
                args = {k: v for k, v in args.items() if k in valid_args or k == 'name'}
            instance = CompClass(**args)
            self.harness.add_component(instance)
            self.component_instances[comp_id] = instance
        logging.info(f"Loaded {len(self.component_instances)} components.")

    def _load_topology(self):
        """Loads and defines the connections between components."""
        logging.info("Loading topology...")
        for conn_conf in self.topology_config.get('connections', []):
            self.harness.add_connection(conn_conf['upstream'], conn_conf['downstream'])
        logging.info("Topology loaded.")

    def _load_agents_and_controllers(self):
        """Loads and instantiates all agents and controllers."""
        logging.info("Loading agents and controllers...")
        for agent_conf in self.agents_config.get('agents', []):
            agent_id = agent_conf.pop('id')
            agent_class_name = agent_conf.pop('class')
            AgentClass = self._get_class(agent_class_name)

            # Unpack the 'config' block if it exists
            if 'config' in agent_conf:
                config_block = agent_conf.pop('config')
                agent_conf.update(config_block)

            # Special handling for agents
            if 'simulated_object_id' in agent_conf:
                agent_conf['simulated_object'] = self.component_instances[agent_conf.pop('simulated_object_id')]

            # Recursively instantiate nested components
            for key, value in agent_conf.items():
                if isinstance(value, dict) and 'class' in value:
                    agent_conf[key] = self._instantiate_object(value)

            final_args = {'agent_id': agent_id, 'message_bus': self.message_bus, **agent_conf}

            import inspect
            sig = inspect.signature(AgentClass.__init__)
            if 'dt' in sig.parameters and 'dt' not in final_args:
                if self.harness.config and 'dt' in self.harness.config:
                    final_args['dt'] = self.harness.config['dt']

            # Remove args not in constructor unless it has **kwargs
            has_kwargs = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
            if not has_kwargs:
                valid_args = list(sig.parameters.keys())
                final_args = {k: v for k, v in final_args.items() if k in valid_args}

            instance = AgentClass(**final_args)
            self.harness.add_agent(instance)
        logging.info("Agents loaded.")

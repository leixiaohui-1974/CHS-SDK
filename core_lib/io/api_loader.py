"""
Loads and builds a simulation scenario from Pydantic models provided by the API.
"""
import logging
from typing import Dict, Any

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core.event_bus import get_global_event_bus
from core_lib.io.object_factory import ObjectFactory
from core_lib.models.api_models import SimulationRequest
from core_lib.models.physical_models import ReservoirModel, GateModel, PipeModel, UnifiedCanalModel

class SimulationBuilderFromModels:
    """
    Reads Pydantic models to configure and instantiate a simulation harness.
    This class is the bridge between the API data layer and the core simulation engine.
    """

    def __init__(self, request_data: SimulationRequest, sim_config: Dict[str, Any]):
        """
        Initializes the builder with the validated request data.

        Args:
            request_data: The Pydantic model containing the full simulation definition.
            sim_config: A dictionary with global simulation settings (e.g., dt, start_time).
        """
        self.request_data = request_data
        self.sim_config = sim_config

        self.harness: SimulationHarness = None
        self.message_bus=None = None
        self.component_instances: Dict[str, Any] = {}
        self.object_factory: ObjectFactory = None
        logging.info("SimulationBuilderFromModels initialized.")

    def build(self) -> SimulationHarness:
        """
        Loads, instantiates, and wires up the full simulation from the models.
        """
        self._setup_infrastructure()
        self._load_components()
        self._load_topology()
        self._load_agents()

        logging.info("Simulation loaded successfully from models. Building harness...")
        self.harness.build()
        logging.info("Harness built. Builder is ready.")
        return self.harness

    def _setup_infrastructure(self):
        """Initializes the message bus, simulation harness, and object factory."""
        logging.info("Setting up simulation infrastructure...")
        self.message_bus = get_global_event_bus()
        self.harness = SimulationHarness(config=self.sim_config)

        context = {
            'message_bus': self.message_bus,
            'dt': self.harness.config.get('dt')
        }
        self.object_factory = ObjectFactory(context)

    def _load_components(self):
        """Instantiates all physical components from the Pydantic models."""
        logging.info("Loading physical components from models...")

        MODEL_TO_CLASS_PATH = {
            ReservoirModel: "core_lib.physical_objects.reservoir.Reservoir",
            GateModel: "core_lib.physical_objects.gate.Gate",
            PipeModel: "core_lib.physical_objects.pipe.Pipe",
            UnifiedCanalModel: "core_lib.physical_objects.unified_canal.UnifiedCanal",
        }

        component_model_lists = [
            self.request_data.components.reservoirs,
            self.request_data.components.gates,
            self.request_data.components.pipes,
            self.request_data.components.unified_canals,
        ]

        for component_list in component_model_lists:
            for component_model in component_list:
                instance_name = component_model.name

                creation_dict = component_model.model_dump(exclude_none=True)
                creation_dict['class'] = MODEL_TO_CLASS_PATH[type(component_model)]

                instance = self.object_factory.create(creation_dict, name=instance_name)

                self.harness.add_component(instance_name, instance)
                self.component_instances[instance_name] = instance
        logging.info(f"Loaded {len(self.component_instances)} components.")

    def _load_topology(self):
        """Loads and defines the connections between components."""
        logging.info("Loading topology from models...")
        topology_for_bus = {}
        for conn in self.request_data.topology.connections:
            upstream_id = conn.upstream
            downstream_id = conn.downstream

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

    def _load_agents(self):
        """Instantiates all agents from the Pydantic models."""
        logging.info("Loading agents from models...")
        for agent_config in self.request_data.agents.agents:
            agent_id = agent_config.id
            class_name = agent_config.class_name
            # With GenericAgentConfig, params is already a dict.
            print(f"agent_config.params: {agent_config.params}")
            params = agent_config.params

            # HACK: Handle potential stale model fields due to hot-reloading issues.
            # This makes the loader robust to both old and new field names.
            if 'csv_file' in params:
                params['csv_file_path'] = params.pop('csv_file')
            if 'value_column' in params:
                params['data_column'] = params.pop('value_column')
            if 'output_topic' in params:
                params['inflow_topic'] = params.pop('output_topic')

            # Resolve 'target_component' string to the actual component instance, if it exists
            if 'target_component' in params and params['target_component']:
                target_name = params.pop('target_component')
                component_instance = self.component_instances.get(target_name)
                if component_instance:
                    # The constructor of ReservoirPerceptionAgent expects 'reservoir_model'
                    if 'reservoirperception' in class_name.lower():
                         params['reservoir_model'] = component_instance
                    else:
                        # For other agents like CSVInflowAgent, the kwarg is 'target_component'
                        params['target_component'] = component_instance

            # Handle nested controller creation
            if 'controller' in params and isinstance(params['controller'], dict):
                controller_config = params.pop('controller')
                params['controller'] = self.object_factory.create(controller_config)

            # --- Logic to resolve component ID strings to component instances ---
            # This mirrors the logic from the yaml_loader to make the API path robust.
            if 'simulated_object_id' in params:
                sim_obj_id = params.pop('simulated_object_id')
                if sim_obj_id in self.component_instances:
                    params['simulated_object'] = self.component_instances[sim_obj_id]
                else:
                    logging.warning(f"Agent '{agent_id}' refers to a non-existent simulated_object_id '{sim_obj_id}'.")

            # HACK: Special handling for CentralDispatcherAgent, which requires a 'reservoir'
            # instance but doesn't have it specified in the example config.
            if 'centraldispatcheragent' in class_name.lower():
                # Find the first reservoir and inject it.
                first_reservoir = next((comp for comp in self.component_instances.values() if 'reservoir' in type(comp).__name__.lower()), None)
                if first_reservoir and 'reservoir' not in params:
                    params['reservoir'] = first_reservoir
                elif not first_reservoir:
                    logging.warning(f"CentralDispatcherAgent '{agent_id}' was defined, but no reservoir was found to assign to it.")

            # The object factory expects a dict with a 'class' key and uses the rest as kwargs
            factory_config = {
                'class': class_name,
                **params
            }

            instance = self.object_factory.create(factory_config, agent_id=agent_id)
            self.harness.add_agent(instance)
        logging.info(f"Loaded {len(self.request_data.agents.agents)} agents.")

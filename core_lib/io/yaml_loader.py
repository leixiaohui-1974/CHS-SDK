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
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"Configuration file not found: {file_path}. Skipping.")
            return None
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return None

class YamlSimulationLoader(BaseYamlLoader):
    """
    Reads a directory of YAML files to configure and instantiate a simulation.
    """

    def __init__(self, scenario_path: str, agents_file: str = 'agents.yml'):
        """
        Initializes the loader with the path to the scenario directory.
        """
        super().__init__(scenario_path)
        
        # 设置日志级别为INFO以显示调试信息
        logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
        
        self.config = self._load_yaml('config.yml')
        self.components_config = self._load_yaml('components.yml')
        self.topology_config = self._load_yaml('topology.yml')
        self.agents_config = self._load_yaml(agents_file)

        self.harness = None
        self.message_bus = None
        self.component_instances = {}
        self.object_factory = None
        logging.info(f"YamlSimulationLoader initialized for scenario: {self.scenario_path.name}")

    def load(self) -> SimulationHarness:
        """
        Loads, instantiates, and wires up the full simulation.
        """
        print(f"\n=== LOAD方法开始 ===")
        if not all([self.config, self.components_config, self.topology_config]):
            raise ValueError("Core configuration files (config, components, topology) are missing.")

        print(f"\n调试: 开始加载仿真，topology_config内容预览: {str(self.topology_config)[:200]}...")
        
        print("\n1. 调用 _setup_infrastructure()...")
        self._setup_infrastructure()
        print("1. _setup_infrastructure() 完成")
        
        print("\n2. 调用 _load_components()...")
        self._load_components()
        print("2. _load_components() 完成")
        
        print(f"\n3. 准备加载拓扑连接... 调用 _load_topology()")
        try:
            self._load_topology()
            print("3. _load_topology() 成功完成")
        except Exception as e:
            print(f"3. _load_topology() 异常: {e}")
            import traceback
            traceback.print_exc()
            raise

        if self.agents_config:
            print("\n4. 加载智能体和控制器...")
            self._load_agents_and_controllers()
            print("4. 智能体和控制器加载完成")
        else:
            logging.warning("Agents file not found or is empty. Running a non-agent simulation.")

        print("\n5. 构建 harness...")
        logging.info("Simulation loaded successfully. Building harness...")
        self.harness.build()
        logging.info("Harness built. Loader is ready.")
        print("5. harness 构建完成")
        
        print("\n=== LOAD方法完成 ===")
        return self.harness

    def _setup_infrastructure(self):
        """Initializes the message bus, simulation harness and object factory."""
        logging.info("Setting up simulation infrastructure...")
        self.message_bus = MessageBus()
        sim_config = self.config.get('simulation', {})
        self.harness = SimulationHarness(config=sim_config)

        context = {
            'message_bus': self.message_bus,
            'time_step': self.harness.config.get('time_step')
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
        print("\n======== 拓扑连接加载开始 ========")
        logging.info("Loading topology...")
        
        # 获取连接信息
        if 'topology' in self.topology_config and 'connections' in self.topology_config['topology']:
            connections = self.topology_config['topology']['connections']
        elif 'connections' in self.topology_config:
            connections = self.topology_config['connections']
        else:
            connections = []
            print("警告: 未找到拓扑连接配置")
            return
        
        print(f"找到 {len(connections)} 个连接")
        
        # 逐个加载连接
        for i, conn_conf in enumerate(connections):
            upstream_id = conn_conf['upstream']
            downstream_id = conn_conf['downstream']
            print(f"连接 {i+1}: {upstream_id} -> {downstream_id}")
            
            # 检查组件是否存在
            if upstream_id not in self.component_instances:
                print(f"错误: 上游组件 '{upstream_id}' 不存在")
                continue
            if downstream_id not in self.component_instances:
                print(f"错误: 下游组件 '{downstream_id}' 不存在")
                continue
                
            # 添加连接
            self.harness.add_connection(upstream_id, downstream_id)
            print(f"成功添加连接: {upstream_id} -> {downstream_id}")

        # 验证结果
        print(f"\n拓扑验证:")
        print(f"- 组件数: {len(self.harness.components)}")
        print(f"- 连接数: {sum(len(v) for v in self.harness.topology.values())}")
        print(f"- topology: {dict(self.harness.topology)}")
        print(f"- inverse_topology: {dict(self.harness.inverse_topology)}")
        print("======== 拓扑连接加载完成 ========\n")
        
        # 设置消息总线拓扑（简化）
        topology_for_bus = {}
        for upstream_id in self.harness.topology:
            if self.harness.topology[upstream_id]:  # 有下游连接
                downstream_id = self.harness.topology[upstream_id][0]  # 取第一个下游
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
                                print(f"Resolving simulated_object_id '{v}' for agent '{agent_id}'")
                                if v in self.component_instances:
                                    d['simulated_object'] = self.component_instances[v]
                                    print(f"Successfully resolved to: {type(self.component_instances[v])}")
                                else:
                                    print(f"ERROR: Component '{v}' not found in component_instances")
                                    print(f"Available components: {list(self.component_instances.keys())}")
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
        
        # Process output configuration to create TopicLoggerAgents
        self._process_output_config()
    
    def _process_output_config(self):
        """Process output configuration to create TopicLoggerAgents for data logging."""
        if not self.config or 'output' not in self.config:
            logging.info("No output configuration found.")
            return
            
        output_configs = self.config['output']
        if not isinstance(output_configs, list):
            logging.warning("Output configuration should be a list.")
            return
            
        logging.info(f"Processing {len(output_configs)} output configurations...")
        
        for i, output_config in enumerate(output_configs):
            if not isinstance(output_config, dict):
                logging.warning(f"Output config {i} is not a dictionary, skipping.")
                continue
                
            topic = output_config.get('topic')
            file_name = output_config.get('file')
            
            if not topic or not file_name:
                logging.warning(f"Output config {i} missing 'topic' or 'file', skipping.")
                continue
                
            # Create a TopicLoggerAgent for this topic
            logger_agent_id = f"logger_{topic.replace('/', '_').replace(' ', '_')}"
            
            try:
                logger_agent = self.object_factory.create({
                    'class': 'core_lib.local_agents.utility.topic_logger_agent.TopicLoggerAgent',
                    'config': {
                        'topic_to_log': topic
                    }
                }, agent_id=logger_agent_id, message_bus=self.message_bus)
                
                self.harness.add_agent(logger_agent)
                
                # Store the mapping for later CSV export
                if not hasattr(self.harness, '_output_configs'):
                    self.harness._output_configs = []
                self.harness._output_configs.append({
                    'topic': topic,
                    'file': file_name,
                    'agent_id': logger_agent_id
                })
                
                logging.info(f"Created TopicLoggerAgent '{logger_agent_id}' for topic '{topic}' -> '{file_name}'")
                
            except Exception as e:
                logging.error(f"Failed to create TopicLoggerAgent for topic '{topic}': {e}")
                
        logging.info("Output configuration processing completed.")

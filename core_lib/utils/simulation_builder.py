#!/usr/bin/env python3
"""
仿真构建器 (Simulation Builder)

提供简化的仿真构建接口，减少示例代码的复杂度，让开发者专注于业务逻辑。

主要功能：
- 简化组件创建
- 自动化连接管理
- 智能体快速配置
- 常见仿真模式的预设
- 一键式仿真运行
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

# 导入核心组件
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.core_engine.testing.simulation_harness import SimulationHarness

# 导入物理对象
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.physical_objects.pump import Pump
from core_lib.physical_objects.water_turbine import WaterTurbine as Turbine

# 导入智能体
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.data_access.csv_inflow_agent import CsvInflowAgent
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent

# 导入工具
from core_lib.utils.example_utils import ExampleConfig

logger = logging.getLogger(__name__)

class SimulationBuilder:
    """
    仿真构建器类
    
    提供流式API来构建仿真系统，简化组件创建和连接过程。
    """
    
    def __init__(self, simulation_params: Optional[Dict[str, Any]] = None):
        """
        初始化仿真构建器
        
        Args:
            simulation_params: 仿真参数字典，包含end_time、time_step等
        """
        self.simulation_params = simulation_params or {'end_time': 100, 'time_step': 1.0, 'start_time': 0}
        
        # 核心组件
        self.message_bus = MessageBus()
        self.harness = None
        
        # 组件和智能体存储
        self.components = {}
        self.agents = {}
        self.connections = []
        
        # 预设配置
        self.presets = {
            'reservoir_default': {
                'initial_state': {'water_level': 10.0, 'volume': 10e6},
                'parameters': {'surface_area': 1e6, 'storage_curve': [[0, 0], [30e6, 30]]}
            },
            'gate_default': {
                'initial_state': {'opening': 0.5},
                'parameters': {'discharge_coefficient': 0.8, 'width': 10}
            },
            'channel_default': {
                'initial_state': {'volume': 500000},
                'parameters': {'k': 0.0001}
            },
            'pump_default': {
                'initial_state': {'is_on': False, 'power': 0.0},
                'parameters': {'max_power': 1000, 'efficiency': 0.85}
            },
            'turbine_default': {
                'initial_state': {'power_output': 0.0},
                'parameters': {'efficiency': 0.9, 'rated_power': 1000}
            }
        }
        
        logger.info("仿真构建器初始化完成")
    
    def add_reservoir(self, name: str, water_level: float = 10.0, 
                     surface_area: float = 1e6, 
                     storage_curve: Optional[List[List[float]]] = None,
                     **kwargs) -> 'SimulationBuilder':
        """
        添加水库组件
        
        Args:
            name: 水库名称
            water_level: 初始水位
            surface_area: 水面面积
            storage_curve: 库容曲线
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        if storage_curve is None:
            storage_curve = [[0, 0], [30e6, 30]]
        
        volume = water_level * surface_area
        
        reservoir = Reservoir(
            name=name,
            initial_state={'water_level': water_level, 'volume': volume},
            parameters={'surface_area': surface_area, 'storage_curve': storage_curve, **kwargs},
            message_bus=self.message_bus
        )
        
        self.components[name] = reservoir
        logger.info(f"已添加水库: {name} (水位: {water_level}m, 面积: {surface_area}m²)")
        return self
    
    def add_gate(self, name: str, opening: float = 0.5, 
                width: float = 10, discharge_coeff: float = 0.8,
                **kwargs) -> 'SimulationBuilder':
        """
        添加闸门组件
        
        Args:
            name: 闸门名称
            opening: 初始开度 (0-1)
            width: 闸门宽度
            discharge_coeff: 流量系数
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        gate = Gate(
            name=name,
            initial_state={'opening': opening},
            parameters={'width': width, 'discharge_coefficient': discharge_coeff, **kwargs},
            message_bus=self.message_bus
        )
        
        self.components[name] = gate
        logger.info(f"已添加闸门: {name} (开度: {opening}, 宽度: {width}m)")
        return self
    
    def add_channel(self, name: str, volume: float = 500000, 
                   k: float = 0.0001, **kwargs) -> 'SimulationBuilder':
        """
        添加河道组件
        
        Args:
            name: 河道名称
            volume: 初始体积
            k: 存储系数
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        channel = RiverChannel(
            name=name,
            initial_state={'volume': volume},
            parameters={'k': k, **kwargs},
            message_bus=self.message_bus
        )
        
        self.components[name] = channel
        logger.info(f"已添加河道: {name} (体积: {volume}m³, k: {k})")
        return self
    
    def add_pump(self, name: str, max_power: float = 1000, 
                efficiency: float = 0.85, is_on: bool = False,
                **kwargs) -> 'SimulationBuilder':
        """
        添加水泵组件
        
        Args:
            name: 水泵名称
            max_power: 最大功率
            efficiency: 效率
            is_on: 初始状态
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        pump = Pump(
            name=name,
            initial_state={'is_on': is_on, 'power': 0.0},
            parameters={'max_power': max_power, 'efficiency': efficiency, **kwargs},
            message_bus=self.message_bus
        )
        
        self.components[name] = pump
        logger.info(f"已添加水泵: {name} (最大功率: {max_power}W, 效率: {efficiency})")
        return self
    
    def add_turbine(self, name: str, rated_power: float = 1000,
                   efficiency: float = 0.9, **kwargs) -> 'SimulationBuilder':
        """
        添加水轮机组件
        
        Args:
            name: 水轮机名称
            rated_power: 额定功率
            efficiency: 效率
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        turbine = Turbine(
            name=name,
            initial_state={'power_output': 0.0},
            parameters={'rated_power': rated_power, 'efficiency': efficiency, **kwargs},
            message_bus=self.message_bus
        )
        
        self.components[name] = turbine
        logger.info(f"已添加水轮机: {name} (额定功率: {rated_power}W, 效率: {efficiency})")
        return self
    
    def connect_components(self, connections: List[Tuple[str, str]]) -> 'SimulationBuilder':
        """
        连接组件
        
        Args:
            connections: 连接列表，每个元素为(上游组件名, 下游组件名)
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        for upstream, downstream in connections:
            if upstream not in self.components:
                raise ValueError(f"上游组件 '{upstream}' 不存在")
            if downstream not in self.components:
                raise ValueError(f"下游组件 '{downstream}' 不存在")
            
            self.connections.append((upstream, downstream))
            logger.info(f"已连接: {upstream} -> {downstream}")
        
        return self
    
    def add_pid_controller(self, name: str, controlled_component: str,
                          setpoint: float, kp: float = 1.0, ki: float = 0.1, 
                          kd: float = 0.01, control_variable: str = 'opening',
                          measurement_topic: Optional[str] = None,
                          **kwargs) -> 'SimulationBuilder':
        """
        添加PID控制器
        
        Args:
            name: 控制器名称
            controlled_component: 被控制的组件名称
            setpoint: 设定值
            kp: 比例增益
            ki: 积分增益
            kd: 微分增益
            control_variable: 控制变量名
            measurement_topic: 测量主题
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        if controlled_component not in self.components:
            raise ValueError(f"被控制组件 '{controlled_component}' 不存在")
        
        if measurement_topic is None:
            measurement_topic = f"{controlled_component}_state"
        
        controller = PIDController(
            agent_id=name,
            message_bus=self.message_bus,
            controlled_component=self.components[controlled_component],
            setpoint=setpoint,
            kp=kp, ki=ki, kd=kd,
            control_variable=control_variable,
            measurement_topic=measurement_topic,
            time_step=self.simulation_params.get('dt', 1.0),
            **kwargs
        )
        
        self.agents[name] = controller
        logger.info(f"已添加PID控制器: {name} (控制 {controlled_component}, 设定值: {setpoint})")
        return self
    
    def add_digital_twin(self, name: str, simulated_component: str,
                        state_topic: Optional[str] = None,
                        **kwargs) -> 'SimulationBuilder':
        """
        添加数字孪生智能体
        
        Args:
            name: 智能体名称
            simulated_component: 被模拟的组件名称
            state_topic: 状态发布主题
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        if simulated_component not in self.components:
            raise ValueError(f"被模拟组件 '{simulated_component}' 不存在")
        
        if state_topic is None:
            state_topic = f"{simulated_component}_state"
        
        twin = DigitalTwinAgent(
            agent_id=name,
            message_bus=self.message_bus,
            simulated_object=self.components[simulated_component],
            state_topic=state_topic,
            **kwargs
        )
        
        self.agents[name] = twin
        logger.info(f"已添加数字孪生: {name} (模拟 {simulated_component})")
        return self
    
    def add_csv_inflow(self, name: str, target_component: str,
                      csv_file: str, time_column: str = 'time',
                      data_column: str = 'inflow',
                      topic: Optional[str] = None,
                      **kwargs) -> 'SimulationBuilder':
        """
        添加CSV入流智能体
        
        Args:
            name: 智能体名称
            target_component: 目标组件名称
            csv_file: CSV文件路径
            time_column: 时间列名
            data_column: 数据列名
            topic: 发布主题
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        if target_component not in self.components:
            raise ValueError(f"目标组件 '{target_component}' 不存在")
        
        if topic is None:
            topic = f"{target_component}_inflow"
        
        inflow_agent = CsvInflowAgent(
            agent_id=name,
            message_bus=self.message_bus,
            target_component=self.components[target_component],
            inflow_topic=topic,
            csv_file_path=csv_file,
            time_column=time_column,
            data_column=data_column,
            **kwargs
        )
        
        self.agents[name] = inflow_agent
        logger.info(f"已添加CSV入流智能体: {name} (目标: {target_component}, 文件: {csv_file})")
        return self
    
    def add_physical_io(self, name: str, target_component: str,
                       input_topic: Optional[str] = None,
                       output_topic: Optional[str] = None,
                       **kwargs) -> 'SimulationBuilder':
        """
        添加物理IO智能体
        
        Args:
            name: 智能体名称
            target_component: 目标组件名称
            input_topic: 输入主题
            output_topic: 输出主题
            **kwargs: 其他参数
            
        Returns:
            SimulationBuilder: 返回自身以支持链式调用
        """
        if target_component not in self.components:
            raise ValueError(f"目标组件 '{target_component}' 不存在")
        
        if input_topic is None:
            input_topic = f"{target_component}_command"
        if output_topic is None:
            output_topic = f"{target_component}_state"
        
        io_agent = PhysicalIOAgent(
            agent_id=name,
            message_bus=self.message_bus,
            physical_object=self.components[target_component],
            input_topic=input_topic,
            output_topic=output_topic,
            **kwargs
        )
        
        self.agents[name] = io_agent
        logger.info(f"已添加物理IO智能体: {name} (目标: {target_component})")
        return self
    
    def build(self) -> SimulationHarness:
        """
        构建仿真系统
        
        Returns:
            SimulationHarness: 仿真测试框架
        """
        # 创建仿真测试框架
        self.harness = SimulationHarness({
            'start_time': self.simulation_params.get('start_time', 0),
            'end_time': self.simulation_params.get('end_time', 100),
            'time_step': self.simulation_params.get('time_step', 1.0)
        })
        
        # 添加所有组件
        for component in self.components.values():
            self.harness.add_component(component)
        
        # 建立连接
        for upstream_name, downstream_name in self.connections:
            upstream = self.components[upstream_name]
            downstream = self.components[downstream_name]
            self.harness.connect_components(upstream, downstream)
        
        # 添加所有智能体
        for agent in self.agents.values():
            self.harness.add_agent(agent)
        
        logger.info(f"仿真系统构建完成: {len(self.components)}个组件, {len(self.agents)}个智能体")
        return self.harness
    
    def run(self) -> Dict[str, Any]:
        """
        运行仿真
        
        Returns:
            Dict[str, Any]: 仿真结果
        """
        if self.harness is None:
            self.build()
        
        logger.info("开始运行仿真...")
        results = self.harness.run_mas_simulation()
        logger.info("仿真运行完成")
        
        return results
    
    def get_component(self, name: str):
        """
        获取组件
        
        Args:
            name: 组件名称
            
        Returns:
            组件对象
        """
        return self.components.get(name)
    
    def get_agent(self, name: str):
        """
        获取智能体
        
        Args:
            name: 智能体名称
            
        Returns:
            智能体对象
        """
        return self.agents.get(name)
    
    def get_message_bus(self) -> MessageBus:
        """
        获取消息总线
        
        Returns:
            MessageBus: 消息总线对象
        """
        return self.message_bus

class PresetSimulations:
    """
    预设仿真模式
    
    提供常见仿真场景的快速创建方法。
    """
    
    @staticmethod
    def single_reservoir_control(reservoir_setpoint: float = 12.0,
                               simulation_end_time: float = 100,
                               time_step: float = 1.0) -> SimulationBuilder:
        """
        单水库控制仿真
        
        Args:
            reservoir_setpoint: 水库水位设定值
            simulation_end_time: 仿真结束时间
            dt: 时间步长
            
        Returns:
            SimulationBuilder: 配置好的仿真构建器
        """
        builder = SimulationBuilder({'end_time': simulation_end_time, 'time_step': time_step, 'start_time': 0})
        
        builder.add_reservoir('reservoir', water_level=10.0) \
               .add_gate('gate', opening=0.5) \
               .connect_components([('reservoir', 'gate')]) \
               .add_digital_twin('reservoir_twin', 'reservoir') \
               .add_pid_controller('reservoir_controller', 'gate', 
                                 setpoint=reservoir_setpoint,
                                 measurement_topic='reservoir_state')
        
        return builder
    
    @staticmethod
    def cascade_reservoirs(num_reservoirs: int = 3,
                          setpoints: Optional[List[float]] = None,
                          simulation_end_time: float = 200,
                          time_step: float = 1.0) -> SimulationBuilder:
        """
        梯级水库仿真
        
        Args:
            num_reservoirs: 水库数量
            setpoints: 各水库设定值列表
            simulation_end_time: 仿真结束时间
            dt: 时间步长
            
        Returns:
            SimulationBuilder: 配置好的仿真构建器
        """
        if setpoints is None:
            setpoints = [12.0] * num_reservoirs
        
        if len(setpoints) != num_reservoirs:
            raise ValueError("设定值数量必须与水库数量一致")
        
        builder = SimulationBuilder({'end_time': simulation_end_time, 'time_step': time_step, 'start_time': 0})
        
        # 创建水库和闸门
        connections = []
        for i in range(num_reservoirs):
            res_name = f'reservoir_{i+1}'
            gate_name = f'gate_{i+1}'
            
            builder.add_reservoir(res_name, water_level=10.0 + i) \
                   .add_gate(gate_name, opening=0.5)
            
            # 连接水库和闸门
            connections.append((res_name, gate_name))
            
            # 连接上一个闸门到当前水库
            if i > 0:
                prev_gate = f'gate_{i}'
                connections.append((prev_gate, res_name))
        
        builder.connect_components(connections)
        
        # 添加控制器和数字孪生
        for i in range(num_reservoirs):
            res_name = f'reservoir_{i+1}'
            gate_name = f'gate_{i+1}'
            
            builder.add_digital_twin(f'{res_name}_twin', res_name) \
                   .add_pid_controller(f'{res_name}_controller', gate_name,
                                     setpoint=setpoints[i],
                                     measurement_topic=f'{res_name}_state')
        
        return builder
    
    @staticmethod
    def pump_station_control(target_flow: float = 50.0,
                           simulation_end_time: float = 150,
                           time_step: float = 1.0) -> SimulationBuilder:
        """
        泵站控制仿真
        
        Args:
            target_flow: 目标流量
            simulation_end_time: 仿真结束时间
            dt: 时间步长
            
        Returns:
            SimulationBuilder: 配置好的仿真构建器
        """
        builder = SimulationBuilder({'end_time': simulation_end_time, 'time_step': time_step, 'start_time': 0})
        
        builder.add_reservoir('source_reservoir', water_level=15.0) \
               .add_pump('pump_station', max_power=2000) \
               .add_reservoir('target_reservoir', water_level=8.0) \
               .connect_components([('source_reservoir', 'pump_station'),
                                  ('pump_station', 'target_reservoir')]) \
               .add_digital_twin('pump_twin', 'pump_station') \
               .add_pid_controller('pump_controller', 'pump_station',
                                 setpoint=target_flow,
                                 control_variable='power',
                                 measurement_topic='pump_station_state')
        
        return builder

def create_simple_simulation(components_config: Dict[str, Dict[str, Any]],
                           connections: List[Tuple[str, str]],
                           simulation_params: Optional[Dict[str, Any]] = None) -> SimulationBuilder:
    """
    从配置字典创建简单仿真
    
    Args:
        components_config: 组件配置字典
        connections: 连接列表
        simulation_params: 仿真参数
        
    Returns:
        SimulationBuilder: 配置好的仿真构建器
    """
    builder = SimulationBuilder(simulation_params)
    
    # 根据配置创建组件
    for comp_name, comp_config in components_config.items():
        comp_type = comp_config.get('type', 'reservoir')
        
        if comp_type == 'reservoir':
            builder.add_reservoir(comp_name, **comp_config.get('parameters', {}))
        elif comp_type == 'gate':
            builder.add_gate(comp_name, **comp_config.get('parameters', {}))
        elif comp_type == 'channel':
            builder.add_channel(comp_name, **comp_config.get('parameters', {}))
        elif comp_type == 'pump':
            builder.add_pump(comp_name, **comp_config.get('parameters', {}))
        elif comp_type == 'turbine':
            builder.add_turbine(comp_name, **comp_config.get('parameters', {}))
        else:
            logger.warning(f"未知组件类型: {comp_type}")
    
    # 建立连接
    builder.connect_components(connections)
    
    return builder
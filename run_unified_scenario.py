#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一仿真场景运行器

这个脚本提供了一个通用的接口来运行任何基于单一YAML配置文件的仿真场景。
它支持两种运行方式：
1. 命令行方式：python run_unified_scenario.py <config_file_path>
2. 程序调用方式：run_simulation_from_config(config_path)

主要特点：
- 支持单一YAML配置文件格式
- 自动创建物理组件和智能体
- 集成验证和分析功能
- 提供详细的仿真进度和结果报告
"""

import time
import sys
import os
import argparse
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入核心库
import yaml
from core_lib.physical_objects.unified_canal import UnifiedCanal
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.physical_objects.integral_delay_canal import IntegralDelayCanal
from core_lib.physical_objects.disturbance_node import DisturbanceNode
from core_lib.local_agents.io.physical_io_agent import PhysicalIOAgent
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.custom_controllers import DirectGateController
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.central_agents.central_mpc_agent import CentralMPCAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.disturbances.rainfall_agent import RainfallAgent
from core_lib.disturbances.water_use_agent import WaterUseAgent
# from core_lib.disturbances.inflow_forecaster_agent import InflowForecasterAgent  # Module not found
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.core_engine.testing.common_agents import DemandAgent, MonitoringAgent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.debug.log_manager import get_log_manager, setup_logging
from core_lib.debug.debug_collector import collect_debug_data, DataType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_simulation_config(config_path: str) -> Dict[str, Any]:
    """加载仿真配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件未找到: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_components_from_config(config: Dict[str, Any],
                                  message_bus: Optional[MessageBus] = None) -> Dict[str, Any]:
    """根据配置创建物理组件"""
    components = {}
    pump_registry: Dict[str, Pump] = {}

    if 'components' not in config:
        return components

    components_config = config['components']

    def build_pump_from_definition(definition: Dict[str, Any],
                                   default_prefix: Optional[str],
                                   fallback_index: int,
                                   parent_id: str) -> Pump:
        reference_id = definition.get('obj_id') or definition.get('ref')
        if reference_id:
            pump_obj = pump_registry.get(reference_id)
            if not pump_obj:
                raise ValueError(f"PumpStation '{parent_id}' 引用了未定义的泵组件 '{reference_id}'。")
            return pump_obj

        pump_id = definition.get('id') or definition.get('name') or f"{parent_id}_pump_{fallback_index}"
        pump_name = definition.get('name', pump_id)
        initial_state = definition.get('initial_state', {}).copy()
        parameters = definition.get('parameters', {}).copy()

        bus_cfg = definition.get('message_bus', {})
        action_topic = bus_cfg.get('action_topic')
        if not action_topic and default_prefix:
            action_topic = f"{default_prefix}.{pump_id}"

        enabled = bus_cfg.get('enabled', bool(action_topic))
        if enabled and action_topic and message_bus is not None:
            pump_obj = Pump(
                name=pump_name,
                initial_state=initial_state,
                parameters=parameters,
                message_bus=message_bus,
                action_topic=action_topic
            )
        else:
            pump_obj = Pump(
                name=pump_name,
                initial_state=initial_state,
                parameters=parameters
            )

        pump_registry[pump_id] = pump_obj
        return pump_obj

    def create_pump_station(component_id: str, comp_config: Dict[str, Any],
                             comp_name: str) -> PumpStation:
        station_initial = comp_config.get('initial_state', {}).copy()
        station_params = comp_config.get('parameters', {}).copy()

        bus_cfg = comp_config.get('message_bus', {}) or {}
        default_prefix = (bus_cfg.get('control_topic_prefix') or
                          bus_cfg.get('action_topic_prefix') or
                          bus_cfg.get('action_topic') or
                          bus_cfg.get('topic_prefix'))

        pump_defaults = comp_config.get('pump_parameters', {}) or {}
        default_initial = comp_config.get('pump_initial_state', {}) or {}

        pump_definitions = comp_config.get('pumps') or []
        if not pump_definitions:
            num_pumps = (comp_config.get('num_pumps') or
                         bus_cfg.get('num_pumps') or
                         comp_config.get('parameters', {}).get('num_pumps'))
            if not num_pumps:
                num_pumps = 0
            for index in range(1, int(num_pumps) + 1):
                pump_definitions.append({
                    'id': f"{component_id}_pump_{index}",
                    'initial_state': default_initial.copy(),
                    'parameters': pump_defaults.copy(),
                })

        pumps: List[Pump] = []
        for idx, pump_def in enumerate(pump_definitions, start=1):
            combined_def = {
                'id': pump_def.get('id'),
                'name': pump_def.get('name'),
                'initial_state': default_initial.copy(),
                'parameters': pump_defaults.copy(),
                'message_bus': pump_def.get('message_bus', {}).copy(),
            }

            combined_def['initial_state'].update(pump_def.get('initial_state', {}))
            combined_def['parameters'].update(pump_def.get('parameters', {}))

            if 'obj_id' in pump_def:
                combined_def['obj_id'] = pump_def['obj_id']
            if 'ref' in pump_def:
                combined_def['ref'] = pump_def['ref']

            pumps.append(build_pump_from_definition(combined_def, default_prefix, idx, component_id))

        return PumpStation(
            name=comp_name,
            initial_state=station_initial,
            parameters=station_params,
            pumps=pumps
        )

    def _merge_bus_parameters(params: Dict[str, Any], bus_cfg: Dict[str, Any]) -> Dict[str, Any]:
        if not bus_cfg:
            return params
        merged = deepcopy(params)
        for key in ('inflow_topics', 'outflow_topics', 'disturbance_topics'):
            if key in bus_cfg and key not in merged:
                merged[key] = deepcopy(bus_cfg[key])
        return merged

    # 处理列表格式的components配置（universal_config格式）
    if isinstance(components_config, list):
        for comp_config in components_config:
            comp_id = comp_config.get('id')
            comp_class = comp_config.get('class', '')

            if not comp_id:
                logger.warning("组件配置缺少id字段，跳过")
                continue

            parameters = _merge_bus_parameters(
                comp_config.get('parameters', {}),
                comp_config.get('message_bus', {})
            )

            bus_cfg = comp_config.get('message_bus', {})
            bus_enabled = bool(bus_cfg.get('enabled')) and message_bus is not None

            gate_kwargs: Dict[str, Any] = {}
            reservoir_kwargs: Dict[str, Any] = {}

            if bus_enabled:
                gate_kwargs['message_bus'] = message_bus
                gate_kwargs['action_topic'] = bus_cfg.get('action_topic')
                gate_kwargs['action_key'] = bus_cfg.get('action_key', 'control_signal')

                reservoir_kwargs['message_bus'] = message_bus
                reservoir_kwargs['inflow_topic'] = bus_cfg.get('inflow_topic') or bus_cfg.get('topic')

            # 根据class字段确定组件类型
            if 'pump.PumpStation' in comp_class or 'PumpStation' in comp_class:
                station = create_pump_station(
                    comp_id,
                    comp_config,
                    comp_config.get('name', comp_id)
                )
                components[comp_id] = station
            elif 'unified_canal.UnifiedCanal' in comp_class or 'UnifiedCanal' in comp_class:
                components[comp_id] = UnifiedCanal(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=parameters.get('model_type', 'canal'),
                    parameters=parameters
                )
            elif ('pump.Pump' in comp_class or
                  (comp_class.endswith('Pump') and 'PumpStation' not in comp_class)):
                pump_obj = build_pump_from_definition(
                    {
                        'id': comp_id,
                        'name': comp_config.get('name', comp_id),
                        'initial_state': comp_config.get('initial_state', {}),
                        'parameters': parameters,
                        'message_bus': comp_config.get('message_bus', {}),
                    },
                    comp_config.get('message_bus', {}).get('control_topic_prefix'),
                    1,
                    comp_id
                )
                components[comp_id] = pump_obj
            elif 'gate.Gate' in comp_class or 'Gate' in comp_class:
                components[comp_id] = Gate(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters,
                    **{k: v for k, v in gate_kwargs.items() if v is not None}
                )
            elif 'water_turbine.WaterTurbine' in comp_class or 'WaterTurbine' in comp_class:
                components[comp_id] = WaterTurbine(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            elif 'reservoir.Reservoir' in comp_class or 'Reservoir' in comp_class:
                components[comp_id] = Reservoir(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters,
                    **{k: v for k, v in reservoir_kwargs.items() if v is not None}
                )
            elif 'river_channel.RiverChannel' in comp_class or 'RiverChannel' in comp_class:
                components[comp_id] = RiverChannel(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            elif 'IntegralDelayCanal' in comp_class:
                # IntegralDelayCanal已弃用，映射到UnifiedCanal
                components[comp_id] = UnifiedCanal(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=parameters.get('model_type', 'integral_delay'),
                    parameters=parameters
                )
            elif 'disturbance_node.DisturbanceNode' in comp_class or 'DisturbanceNode' in comp_class:
                components[comp_id] = DisturbanceNode(
                    name=comp_config.get('name', comp_id),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            else:
                logger.warning(f"未知的组件类型: {comp_class}，跳过组件 {comp_id}")

    # 处理字典格式的components配置（传统格式）
    elif isinstance(components_config, dict):
        for comp_name, comp_config in components_config.items():
            comp_type = comp_config.get('type')

            parameters = _merge_bus_parameters(
                comp_config.get('parameters', {}),
                comp_config.get('message_bus', {})
            )

            bus_cfg = comp_config.get('message_bus', {})
            bus_enabled = bool(bus_cfg.get('enabled')) and message_bus is not None

            gate_kwargs: Dict[str, Any] = {}
            reservoir_kwargs: Dict[str, Any] = {}

            if bus_enabled:
                gate_kwargs['message_bus'] = message_bus
                gate_kwargs['action_topic'] = bus_cfg.get('action_topic')
                gate_kwargs['action_key'] = bus_cfg.get('action_key', 'control_signal')

                reservoir_kwargs['message_bus'] = message_bus
                reservoir_kwargs['inflow_topic'] = bus_cfg.get('inflow_topic') or bus_cfg.get('topic')

            if comp_type == 'PumpStation':
                station = create_pump_station(
                    comp_name,
                    comp_config,
                    comp_config.get('name', comp_name)
                )
                components[comp_name] = station
            elif comp_type == 'UnifiedCanal':
                components[comp_name] = UnifiedCanal(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=parameters.get('model_type', 'canal'),
                    parameters=parameters
                )
            elif comp_type == 'Pump':
                pump_obj = build_pump_from_definition(
                    {
                        'id': comp_name,
                        'name': comp_config.get('name', comp_name),
                        'initial_state': comp_config.get('initial_state', {}),
                        'parameters': parameters,
                        'message_bus': comp_config.get('message_bus', {}),
                    },
                    comp_config.get('message_bus', {}).get('control_topic_prefix'),
                    1,
                    comp_name
                )
                components[comp_name] = pump_obj
            elif comp_type == 'Gate':
                components[comp_name] = Gate(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters,
                    **{k: v for k, v in gate_kwargs.items() if v is not None}
                )
            elif comp_type == 'WaterTurbine':
                components[comp_name] = WaterTurbine(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            elif comp_type == 'Reservoir':
                components[comp_name] = Reservoir(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters,
                    **{k: v for k, v in reservoir_kwargs.items() if v is not None}
                )
            elif comp_type == 'RiverChannel':
                components[comp_name] = RiverChannel(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            elif comp_type == 'IntegralDelayCanal':
                # IntegralDelayCanal已弃用，映射到UnifiedCanal
                components[comp_name] = UnifiedCanal(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    model_type=parameters.get('model_type', 'integral_delay'),
                    parameters=parameters
                )
            elif comp_type == 'DisturbanceNode':
                components[comp_name] = DisturbanceNode(
                    name=comp_config.get('name', comp_name),
                    initial_state=comp_config.get('initial_state', {}),
                    parameters=parameters
                )
            else:
                logger.warning(f"未知的组件类型: {comp_type}，跳过组件 {comp_name}")

    return components

def _coerce_bool(value: Any, default: bool = False) -> bool:
    """Best-effort conversion of configuration values to boolean."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _extract_agent_config(agent_config: Dict[str, Any]) -> Dict[str, Any]:
    """Return a mutable configuration dictionary for an agent entry."""

    if isinstance(agent_config.get('config'), dict):
        return deepcopy(agent_config['config'])

    excluded_keys = {'type', 'agent_id', 'name', 'class'}
    return {k: deepcopy(v) for k, v in agent_config.items() if k not in excluded_keys}


def create_agents_from_config(config: Dict[str, Any], components: Dict[str, Any],
                             message_bus: MessageBus) -> Dict[str, Any]:
    """根据配置创建智能体"""
    agents = {}
    
    if 'agents' not in config:
        return agents
    
    agents_config = config['agents']
    
    # 处理列表格式的agents配置（universal_config格式）
    if isinstance(agents_config, list):
        normalized_agents: Dict[str, Dict[str, Any]] = {}
        for agent_config in agents_config:
            agent_id = agent_config.get('id')
            if not agent_id:
                logger.warning("智能体配置缺少id字段，跳过")
                continue

            config_block = agent_config.get('config', {}).copy()
            config_block['type'] = agent_config.get('type') or agent_config.get('class')
            config_block['agent_id'] = agent_id
            normalized_agents[agent_id] = config_block

        agents_config = normalized_agents
    
    # 处理字典格式的agents配置（传统格式）
    for agent_name, agent_config in agents_config.items():
        agent_type = agent_config.get('type')
        agent_id = agent_config.get('agent_id', agent_name)
        
        try:
            normalized_type = agent_type or agent_config.get('class', '')
            if normalized_type == 'PhysicalIOAgent':
                agents[agent_name] = PhysicalIOAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif normalized_type == 'LocalControlAgent':
                config_data = _extract_agent_config(agent_config)
                mb_config = config_data.pop('message_bus', {})

                sim_dt = config.get('simulation', {}).get('dt', 1.0)
                dt = config_data.pop('dt', sim_dt)
                target_component = config_data.pop('target_component', mb_config.get('target_component', ''))
                control_type = config_data.pop('control_type', 'default')

                data_sources = config_data.pop('data_sources', None)
                if not data_sources:
                    primary_observation = mb_config.get('observation_topic') or mb_config.get('primary_data')
                    if primary_observation:
                        data_sources = {'primary_data': primary_observation}
                    else:
                        data_sources = {}

                control_targets = config_data.pop('control_targets', None)
                if not control_targets:
                    primary_action = mb_config.get('action_topic') or mb_config.get('primary_target')
                    if primary_action:
                        control_targets = {'primary_target': primary_action}
                    else:
                        control_targets = {}

                allocation_config = config_data.pop('allocation', config_data.pop('allocation_config', {}))

                controller_section = config_data.pop('controller', None)
                controller_config = config_data.pop('controller_config', None)
                controller = None
                if controller_section:
                    ctrl_type = controller_section.get('type') or controller_section.get('class')
                    params = controller_section.get('parameters', {})
                    if ctrl_type == 'PIDController':
                        limits = params.get('output_limits')
                        if isinstance(limits, (list, tuple)) and len(limits) == 2:
                            min_out, max_out = limits
                        else:
                            min_out = params.get('min_output', 0.0)
                            max_out = params.get('max_output', 1.0)
                        controller = PIDController(
                            Kp=params.get('Kp', params.get('kp', 0.0)),
                            Ki=params.get('Ki', params.get('ki', 0.0)),
                            Kd=params.get('Kd', params.get('kd', 0.0)),
                            setpoint=params.get('setpoint', 0.0),
                            min_output=min_out,
                            max_output=max_out
                        )
                        if controller_config is None:
                            controller_config = {'type': 'PIDController', 'parameters': params}
                    elif ctrl_type == 'DirectGateController':
                        controller = DirectGateController(**params)
                        if controller_config is None:
                            controller_config = {'type': 'DirectGateController', 'parameters': params}
                    else:
                        logger.warning(f"未知的控制器类型: {ctrl_type}，智能体 {agent_name} 将不创建控制器")

                logging_config = config_data.pop('logging', {})
                log_observations = _coerce_bool(logging_config.get('log_observations', False))

                observation_topic = config_data.pop(
                    'observation_topic',
                    mb_config.get('observation_topic') or data_sources.get('primary_data') if data_sources else None
                )
                observation_key = config_data.pop('observation_key', mb_config.get('observation_key'))
                action_topic = config_data.pop(
                    'action_topic',
                    mb_config.get('action_topic') or control_targets.get('primary_target') if control_targets else None
                )
                command_topic = config_data.pop('command_topic', mb_config.get('command_topic'))
                feedback_topic = config_data.pop('feedback_topic', mb_config.get('feedback_topic'))

                agents[agent_name] = LocalControlAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    dt=dt,
                    target_component=target_component,
                    control_type=control_type,
                    data_sources=data_sources,
                    control_targets=control_targets,
                    allocation_config=allocation_config,
                    controller_config=controller_config or {},
                    controller=controller,
                    observation_topic=observation_topic,
                    observation_key=observation_key,
                    action_topic=action_topic,
                    command_topic=command_topic,
                    feedback_topic=feedback_topic,
                    log_observations=log_observations,
                    **config_data
                )
            elif normalized_type == 'DigitalTwinAgent':
                config_data = _extract_agent_config(agent_config)
                simulated_object_name = config_data.pop('simulated_object', agent_config.get('simulated_object'))
                message_info = config_data.pop('message_bus', {})
                state_topic = config_data.pop('state_topic', message_info.get('state_topic'))

                simulated_object = components.get(simulated_object_name)
                if not simulated_object:
                    logger.warning(f"智能体 {agent_name} 的模拟对象 '{simulated_object_name}' 未找到，跳过创建")
                    continue
                if not state_topic:
                    logger.warning(f"智能体 {agent_name} 未提供 state_topic，跳过创建")
                    continue

                agents[agent_name] = DigitalTwinAgent(
                    agent_id=agent_id,
                    simulated_object=simulated_object,
                    message_bus=message_bus,
                    state_topic=state_topic,
                    **config_data
                )
            elif normalized_type == 'CentralMPCAgent':
                agents[agent_name] = CentralMPCAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif normalized_type in {'CentralDispatcher', 'CentralDispatcherAgent'}:
                config_data = _extract_agent_config(agent_config)
                agents[agent_name] = CentralDispatcherAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **config_data
                )
            elif normalized_type == 'DemandAgent':
                config_data = _extract_agent_config(agent_config)
                demand_topic = (
                    config_data.pop('demand_topic', None)
                    or agent_config.get('demand_topic')
                    or config.get('communication', {}).get('topics', {}).get('demand')
                )
                schedule_raw = config_data.pop('demand_schedule', agent_config.get('demand_schedule', {}))
                if schedule_raw is None:
                    schedule_raw = {}
                demand_schedule: Dict[float, float] = {}
                for key, value in schedule_raw.items():
                    try:
                        time_key = float(key)
                        demand_schedule[time_key] = float(value)
                    except (TypeError, ValueError):
                        logger.warning(f"DemandAgent {agent_name} 忽略无效的需求条目 {key}: {value}")
                if not demand_topic:
                    logger.warning(f"DemandAgent {agent_name} 缺少 demand_topic，跳过创建")
                    continue
                agents[agent_name] = DemandAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    demand_topic=demand_topic,
                    demand_schedule=demand_schedule,
                )
            elif normalized_type == 'MonitoringAgent':
                config_data = _extract_agent_config(agent_config)
                component_spec = config_data.pop('components', agent_config.get('components', {}))
                monitored_components: Dict[str, Any] = {}
                if isinstance(component_spec, dict):
                    for alias, comp_id in component_spec.items():
                        target_id = comp_id if isinstance(comp_id, str) else alias
                        if target_id in components:
                            monitored_components[alias] = components[target_id]
                elif isinstance(component_spec, list):
                    for comp_id in component_spec:
                        if comp_id in components:
                            monitored_components[comp_id] = components[comp_id]
                else:
                    logger.warning(f"MonitoringAgent {agent_name} 未提供有效的 components 配置，默认监控全部组件")
                    monitored_components = components

                monitoring_interval = config_data.pop('monitoring_interval', config_data.pop('interval', 60.0))
                agents[agent_name] = MonitoringAgent(
                    agent_id=agent_id,
                    components=monitored_components,
                    monitoring_interval=monitoring_interval,
                )
            elif normalized_type == 'PumpControlAgent':
                config_data = _extract_agent_config(agent_config)
                target_component = (
                    config_data.pop('pump_station', None)
                    or config_data.pop('target_component', None)
                    or agent_config.get('pump_station')
                    or agent_config.get('target_component')
                )

                if isinstance(target_component, dict):
                    target_component = target_component.get('obj_id') or target_component.get('id')

                pump_station = components.get(target_component)
                if not pump_station:
                    logger.warning(f"PumpControlAgent {agent_name} 的泵站 '{target_component}' 未找到，跳过创建")
                    continue

                demand_topic = config_data.pop('demand_topic', agent_config.get('demand_topic'))
                if not demand_topic:
                    demand_topic = config.get('communication', {}).get('topics', {}).get('demand')

                control_prefix = config_data.pop('control_topic_prefix', agent_config.get('control_topic_prefix'))
                if not control_prefix:
                    control_prefix = config.get('communication', {}).get('topics', {}).get('pump_action_prefix')

                agents[agent_name] = PumpControlAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    pump_station=pump_station,
                    demand_topic=demand_topic,
                    control_topic_prefix=control_prefix,
                )
            elif normalized_type == 'RainfallAgent':
                agents[agent_name] = RainfallAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif normalized_type == 'WaterUseAgent':
                agents[agent_name] = WaterUseAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            elif normalized_type == 'InflowForecasterAgent':
                agents[agent_name] = InflowForecasterAgent(
                    agent_id=agent_id,
                    message_bus=message_bus,
                    **agent_config.get('config', {})
                )
            else:
                logger.warning(f"未知的智能体类型: {agent_type}，跳过智能体 {agent_name}")
        except Exception as e:
            logger.error(f"创建智能体 {agent_name} 失败: {e}")
    
    return agents

def setup_connections(harness: SimulationHarness, config: Dict[str, Any], 
                     components: Dict[str, Any]):
    """设置组件连接"""
    if 'connections' not in config:
        return
    
    for connection in config['connections']:
        from_comp = connection.get('from')
        to_comp = connection.get('to')
        
        if from_comp in components and to_comp in components:
            harness.add_connection(from_comp, to_comp)
            logger.info(f"添加连接: {from_comp} -> {to_comp}")
        else:
            logger.warning(f"连接中的组件不存在: {from_comp} -> {to_comp}")

def perform_analysis(config: Dict[str, Any], harness: SimulationHarness) -> Dict[str, Any]:
    """执行仿真结果分析和验证"""
    analysis_results = {}
    
    if 'analysis' not in config or not config['analysis'].get('enable_validation', False):
        return analysis_results
    
    analysis_config = config['analysis']
    history = harness.history
    
    # 基本统计
    analysis_results['simulation_steps'] = len(history)
    analysis_results['simulation_duration'] = len(history) * config.get('simulation', {}).get('time_step', 60)
    
    # 性能指标计算
    if 'performance_metrics' in analysis_config:
        metrics = {}
        for metric in analysis_config['performance_metrics']:
            if metric == 'water_level_stability':
                # 计算水位稳定性
                water_levels = [step.get('water_level', 0) for step in history]
                if water_levels:
                    metrics['water_level_mean'] = sum(water_levels) / len(water_levels)
                    metrics['water_level_std'] = (sum((x - metrics['water_level_mean'])**2 for x in water_levels) / len(water_levels))**0.5
            elif metric == 'control_performance':
                # 计算控制性能
                control_actions = [step.get('control_action', 0) for step in history]
                if control_actions:
                    metrics['control_actions_count'] = len([x for x in control_actions if abs(x) > 0.01])
        
        analysis_results['performance_metrics'] = metrics
    
    # 预期行为验证
    if 'expected_behavior' in analysis_config:
        expected = analysis_config['expected_behavior']
        validation_results = {}
        
        # 检查最终状态
        if history and 'final_water_level_range' in expected:
            final_level = history[-1].get('water_level', 0)
            level_range = expected['final_water_level_range']
            validation_results['final_water_level_in_range'] = level_range[0] <= final_level <= level_range[1]
        
        analysis_results['validation_results'] = validation_results
    
    return analysis_results

def run_simulation_from_config(config_path: str, show_progress: bool = True, 
                              show_summary: bool = True) -> Dict[str, Any]:
    """从配置文件运行仿真的主函数"""
    start_time = time.time()
    
    try:
        # 加载配置
        if show_progress:
            print(f"\n=== 🚀 开始仿真 ===\n")
            print(f"📁 配置文件: {config_path}")
        
        config = load_simulation_config(config_path)
        
        # 获取仿真参数
        sim_config = config.get('simulation', {})
        duration = sim_config.get('duration', 3600)
        time_step = sim_config.get('time_step', 60)
        description = sim_config.get('description', '未命名仿真')
        
        if show_progress:
            print(f"📋 仿真描述: {description}")
            print(f"⏱️  仿真时长: {duration}秒 (时间步长: {time_step}秒)")
        
        # 设置基础设施
        harness = SimulationHarness(config={'duration': duration, 'dt': time_step})
        message_bus = harness.message_bus
        
        # 创建组件
        if show_progress:
            print(f"\n🔧 创建物理组件...")
        components = create_components_from_config(config, message_bus)
        
        for comp_name, component in components.items():
            harness.add_component(comp_name, component)
            if show_progress:
                print(f"  ✅ {comp_name}: {type(component).__name__}")
        
        # 设置连接
        if show_progress:
            print(f"\n🔗 设置组件连接...")
        setup_connections(harness, config, components)
        
        # 创建智能体
        if show_progress:
            print(f"\n🤖 创建智能体...")
        agents = create_agents_from_config(config, components, message_bus)
        
        for agent_name, agent in agents.items():
            harness.add_agent(agent)
            if show_progress:
                print(f"  ✅ {agent_name}: {type(agent).__name__}")
        
        # 构建仿真
        if show_progress:
            print(f"\n⚙️  构建仿真环境...")
        harness.build()
        
        # 运行仿真
        if show_progress:
            print(f"\n🏃 运行仿真...")
        harness.run_mas_simulation()
        
        # 分析结果
        if show_progress:
            print(f"\n📊 分析仿真结果...")
        analysis_results = perform_analysis(config, harness)
        
        # 计算运行时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 显示总结
        if show_summary:
            print(f"\n=== 📈 仿真完成总结 ===\n")
            print(f"✅ 仿真状态: 成功完成")
            print(f"⏱️  执行时间: {execution_time:.2f}秒")
            print(f"📊 仿真步数: {len(harness.history)}")
            print(f"🔧 物理组件: {len(components)}个")
            print(f"🤖 智能体: {len(agents)}个")
            
            if analysis_results:
                print(f"\n📋 分析结果:")
                if 'performance_metrics' in analysis_results:
                    for metric, value in analysis_results['performance_metrics'].items():
                        print(f"  📈 {metric}: {value}")
                
                if 'validation_results' in analysis_results:
                    print(f"\n✅ 验证结果:")
                    for check, result in analysis_results['validation_results'].items():
                        status = "✅ 通过" if result else "❌ 失败"
                        print(f"  {check}: {status}")
        
        return {
            'success': True,
            'execution_time': execution_time,
            'components_count': len(components),
            'agents_count': len(agents),
            'simulation_steps': len(harness.history),
            'analysis_results': analysis_results,
            'history': harness.history
        }
    
    except Exception as e:
        error_msg = f"仿真运行失败: {str(e)}"
        logger.error(error_msg)
        if show_summary:
            print(f"\n❌ {error_msg}")
        return {
            'success': False,
            'error': str(e),
            'execution_time': time.time() - start_time
        }

def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="运行基于YAML配置文件的仿真场景")
    parser.add_argument("config_path", type=str, help="YAML配置文件的路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，不显示进度信息")
    parser.add_argument("--no-summary", action="store_true", help="不显示仿真总结")
    
    args = parser.parse_args()
    
    # 运行仿真
    result = run_simulation_from_config(
        config_path=args.config_path,
        show_progress=not args.quiet,
        show_summary=not args.no_summary
    )
    
    # 设置退出码
    sys.exit(0 if result['success'] else 1)

if __name__ == "__main__":
    main()
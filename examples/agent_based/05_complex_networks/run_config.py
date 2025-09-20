#!/usr/bin/env python3
"""Configuration-driven runner for the branched network control scenario."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import yaml

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.river_channel import RiverChannel
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness


def load_config(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def _get_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def create_components(config: Dict[str, Any], harness: SimulationHarness) -> Dict[str, Any]:
    components: Dict[str, Any] = {}
    for comp_id, comp_cfg in config['components'].items():
        comp_type = comp_cfg['type']
        initial_state = comp_cfg.get('initial_state', {})
        parameters = comp_cfg.get('parameters', {})

        if comp_type == 'Reservoir':
            component = Reservoir(comp_id, initial_state, parameters)
        elif comp_type == 'Gate':
            mb_cfg = comp_cfg.get('message_bus', {})
            if mb_cfg.get('enabled', False):
                component = Gate(
                    comp_id,
                    initial_state,
                    parameters,
                    harness.message_bus,
                    mb_cfg.get('action_topic'),
                )
            else:
                component = Gate(comp_id, initial_state, parameters)
        elif comp_type == 'RiverChannel':
            component = RiverChannel(comp_id, initial_state, parameters)
        else:
            raise ValueError(f"Unsupported component type: {comp_type}")

        harness.add_component(comp_id, component)
        components[comp_id] = component

    return components


def apply_network(harness: SimulationHarness, network: List[List[str]]) -> None:
    for upstream, downstream in network:
        harness.add_connection(upstream, downstream)


def create_agents(config: Dict[str, Any], components: Dict[str, Any], harness: SimulationHarness) -> List[Any]:
    agents: List[Any] = []
    topics = config.get('communication', {}).get('topics', {})
    logging_cfg = config.get('logging', {})
    default_log_flag = _get_bool(logging_cfg.get('log_observations'))

    for agent_name, agent_cfg in config['agents'].items():
        agent_type = agent_cfg['type']
        agent_id = agent_cfg['agent_id']

        if agent_type == 'DigitalTwinAgent':
            sim_obj = components[agent_cfg['simulated_object']]
            state_topic = agent_cfg['message_bus']['state_topic']
            agent = DigitalTwinAgent(agent_id, sim_obj, harness.message_bus, state_topic)
            agents.append(agent)
            continue

        if agent_type == 'LocalControlAgent':
            controller_cfg = agent_cfg['controller']
            ctrl_params = controller_cfg['parameters']
            controller = PIDController(
                Kp=ctrl_params['Kp'],
                Ki=ctrl_params['Ki'],
                Kd=ctrl_params['Kd'],
                setpoint=ctrl_params['setpoint'],
                min_output=ctrl_params['min_output'],
                max_output=ctrl_params['max_output'],
            )

            mb_cfg = agent_cfg.get('message_bus', {})
            observation_topic = mb_cfg.get('observation_topic') or agent_cfg['data_sources'].get('primary_data')
            action_topic = mb_cfg.get('action_topic') or agent_cfg['control_targets'].get('primary_target')

            agent = LocalControlAgent(
                agent_id=agent_id,
                message_bus=harness.message_bus,
                dt=config['simulation']['dt'],
                target_component=agent_cfg.get('target_component'),
                control_type=agent_cfg.get('control_type', 'gate_control'),
                data_sources=agent_cfg.get('data_sources', {'primary_data': observation_topic}),
                control_targets=agent_cfg.get('control_targets', {'primary_target': action_topic}),
                allocation_config=agent_cfg.get('allocation', agent_cfg.get('allocation_config', {})),
                controller_config=controller_cfg,
                controller=controller,
                observation_topic=observation_topic,
                observation_key=mb_cfg.get('observation_key', 'water_level'),
                action_topic=action_topic,
                command_topic=mb_cfg.get('command_topic', topics.get('res1_command')),
                log_observations=_get_bool(mb_cfg.get('log_observations'), default_log_flag),
            )
            agents.append(agent)
            continue

        if agent_type == 'CentralDispatcherAgent':
            mb_cfg = agent_cfg.get('message_bus', {})
            agent = CentralDispatcherAgent(
                agent_id=agent_id,
                message_bus=harness.message_bus,
                mode=agent_cfg.get('mode', 'rule'),
                subscribed_topic=mb_cfg.get('subscribed_topic', topics.get('res1_state')),
                observation_key=mb_cfg.get('observation_key', 'water_level'),
                command_topic=mb_cfg.get('command_topic', topics.get('res1_command')),
                dispatcher_params=agent_cfg.get('dispatcher_params', {}),
            )
            agents.append(agent)
            continue

        raise ValueError(f"Unsupported agent type: {agent_type}")

    for agent in agents:
        harness.add_agent(agent)

    return agents


def compute_metrics(history: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    validation = config['validation']
    time_series = [step['time'] for step in history]

    reservoir_metrics = {}
    for res_id, rules in validation['reservoirs'].items():
        target = rules['target']
        tolerance = rules['tolerance']
        levels = [step[res_id]['water_level'] for step in history]
        final_level = levels[-1]
        initial_level = levels[0]
        error = abs(final_level - target)
        within = error <= tolerance

        time_to_target = None
        for idx, level in enumerate(levels):
            if abs(level - target) <= tolerance:
                time_to_target = time_series[idx]
                break

        reservoir_metrics[res_id] = {
            'initial': initial_level,
            'final': final_level,
            'target': target,
            'tolerance': tolerance,
            'error': error,
            'within': within,
            'time_to_target': time_to_target,
        }

    score_cfg = validation.get('score', {})
    if all(data['within'] for data in reservoir_metrics.values()):
        score = score_cfg.get('pass', 1.0)
    else:
        score = score_cfg.get('fail', 0.0)

    gate_metrics = {}
    for gate_id in [gid for gid in ('g1', 'g2') if gid in history[0]]:
        openings = [step[gate_id].get('opening', 0.0) for step in history]
        gate_metrics[gate_id] = {
            'min': min(openings),
            'max': max(openings),
            'final': openings[-1],
        }

    return {
        'reservoirs': reservoir_metrics,
        'gates': gate_metrics,
        'score': score,
        'duration': time_series[-1] if time_series else 0,
    }


def generate_report(config: Dict[str, Any], metrics: Dict[str, Any], output_path: Path) -> None:
    report_cfg = config.get('report', {})
    title = report_cfg.get('title', '复杂网络仿真结果')
    description = report_cfg.get('description', '')

    lines: List[str] = [f"# {title}"]
    if description:
        lines.append('')
        lines.append(description)

    lines.append('')
    lines.append('## 仿真配置摘要')
    sim_cfg = config['simulation']
    lines.append(f"- 时长：{sim_cfg['duration']} s，步长 {sim_cfg['dt']} s")
    lines.append(f"- 控制器数量：2 个本地控制 + 1 个调度器 + 4 个数字孪生")

    lines.append('')
    lines.append('## 水库水位指标')
    lines.append('| 水库 | 初始水位 (m) | 目标水位 (m) | 最终水位 (m) | 绝对误差 (m) | 达标时间 (s) | 是否满足容差 |')
    lines.append('| --- | --- | --- | --- | --- | --- | --- |')
    for res_id, data in metrics['reservoirs'].items():
        time_to_target = data['time_to_target'] if data['time_to_target'] is not None else '未达到'
        status = '✅' if data['within'] else '⚠️'
        lines.append(
            f"| {res_id} | {data['initial']:.3f} | {data['target']:.3f} | "
            f"{data['final']:.3f} | {data['error']:.3f} | {time_to_target} | {status} |"
        )

    if metrics['gates']:
        lines.append('')
        lines.append('## 闸门开度范围')
        lines.append('| 闸门 | 最小开度 | 最大开度 | 最终开度 |')
        lines.append('| --- | --- | --- | --- |')
        for gate_id, data in metrics['gates'].items():
            lines.append(f"| {gate_id} | {data['min']:.3f} | {data['max']:.3f} | {data['final']:.3f} |")

    lines.append('')
    lines.append('## 综合评分与结论')
    score = metrics['score']
    if score >= 1.0:
        verdict = '所有水库均在容差内完成调控，评分达到满分。'
    else:
        verdict = '至少一座水库未满足稳态误差要求，需要进一步调参。'
    lines.append(f"- 评分：{score:.3f}")
    lines.append(f"- 结论：{verdict}")

    lines.append('')
    lines.append('## 运行时间戳')
    lines.append(f"- 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    output_path.write_text('\n'.join(lines), encoding='utf-8')


def run_simulation(config: Dict[str, Any]) -> SimulationHarness:
    harness = SimulationHarness(config['simulation'])
    components = create_components(config, harness)
    apply_network(harness, config.get('network', []))
    create_agents(config, components, harness)

    print("\n--- 构建并运行仿真 ---")
    harness.build()
    harness.run_mas_simulation()
    print("\n--- 仿真完成 ---")
    return harness


def main() -> None:
    config_path = Path(__file__).with_name('config.yml')
    config = load_config(config_path)

    harness = run_simulation(config)
    metrics = compute_metrics(harness.history, config)

    report_path = Path(__file__).with_name(config['report']['path'])
    generate_report(config, metrics, report_path)

    if _get_bool(config.get('logging', {}).get('print_summary', True)):
        print('\n=== 仿真摘要 ===')
        for res_id, data in metrics['reservoirs'].items():
            status = '达标' if data['within'] else '未达标'
            print(
                f"{res_id}: 最终水位 {data['final']:.3f} m, "
                f"目标 {data['target']:.3f} m, 误差 {data['error']:.3f} m ({status})"
            )
        print(f"综合评分：{metrics['score']:.3f}")
        print(f"报告路径：{report_path}")


if __name__ == '__main__':
    main()

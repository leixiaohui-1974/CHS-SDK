#!/usr/bin/env python3
"""Configuration-driven rainfall disturbance handling simulation."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import yaml
import matplotlib.pyplot as plt
import numpy as np


def _to_bool(value: Any, default: bool = False) -> bool:
    """Best-effort conversion of configuration values to boolean."""
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


# Ensure project root is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.local_agents.control.local_control_agent import LocalControlAgent
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent
from core_lib.disturbances.rainfall_agent import RainfallAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open('r', encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def create_components(config: Dict[str, Any], message_bus) -> Dict[str, Any]:
    components: Dict[str, Any] = {}
    topics = config.get('communication', {}).get('topics', {})

    for name, comp_config in config['components'].items():
        comp_type = comp_config['type']
        initial_state = comp_config.get('initial_state', {})
        parameters = comp_config.get('parameters', {})
        mb_config = comp_config.get('message_bus', {})

        if comp_type == 'Reservoir':
            kwargs: Dict[str, Any] = {}
            if _to_bool(mb_config.get('enabled', True), True):
                kwargs['message_bus'] = message_bus
                inflow_topic = mb_config.get('inflow_topic') or topics.get('rainfall_disturbance')
                if inflow_topic:
                    kwargs['inflow_topic'] = inflow_topic
            components[name] = Reservoir(
                name=name,
                initial_state=initial_state,
                parameters=parameters,
                **kwargs,
            )
        elif comp_type == 'Gate':
            kwargs = {}
            if _to_bool(mb_config.get('enabled', True), True):
                kwargs['message_bus'] = message_bus
                kwargs['action_topic'] = mb_config.get('action_topic') or topics.get('gate_action')
                kwargs['action_key'] = mb_config.get('action_key', 'control_signal')
            components[name] = Gate(
                name=name,
                initial_state=initial_state,
                parameters=parameters,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported component type: {comp_type}")

    return components


def create_agents(config: Dict[str, Any], components: Dict[str, Any], message_bus) -> List[Any]:
    agents: List[Any] = []
    topics = config.get('communication', {}).get('topics', {})
    sim_dt = config['simulation']['dt']

    for agent_name, agent_config in config['agents'].items():
        agent_type = agent_config['type']
        agent_id = agent_config.get('agent_id', agent_name)

        if agent_type == 'DigitalTwinAgent':
            simulated_object = components[agent_config['simulated_object']]
            state_topic = agent_config['message_bus']['state_topic']
            agent = DigitalTwinAgent(
                agent_id=agent_id,
                simulated_object=simulated_object,
                message_bus=message_bus,
                state_topic=state_topic,
            )
            agents.append(agent)
        elif agent_type == 'LocalControlAgent':
            controller_cfg = agent_config['controller']
            controller_params = controller_cfg['parameters']
            pid = PIDController(
                Kp=controller_params['Kp'],
                Ki=controller_params['Ki'],
                Kd=controller_params['Kd'],
                setpoint=controller_params['setpoint'],
                min_output=controller_params.get('min_output', controller_params.get('output_limits', [0, 1])[0]),
                max_output=controller_params.get('max_output', controller_params.get('output_limits', [0, 1])[1]),
            )
            mb_config = agent_config.get('message_bus', {})
            data_sources = agent_config.get('data_sources') or {
                'primary_data': mb_config.get('observation_topic') or topics.get('reservoir_state')
            }
            control_targets = agent_config.get('control_targets') or {
                'primary_target': mb_config.get('action_topic') or topics.get('gate_action')
            }
            logging_cfg = agent_config.get('logging', {})
            log_observations = _to_bool(logging_cfg.get('log_observations'), False)

            agent = LocalControlAgent(
                agent_id=agent_id,
                message_bus=message_bus,
                dt=agent_config.get('dt', sim_dt),
                target_component=agent_config.get('target_component'),
                control_type=agent_config.get('control_type', 'gate_control'),
                data_sources=data_sources,
                control_targets=control_targets,
                allocation_config=agent_config.get('allocation', agent_config.get('allocation_config', {})),
                controller_config=controller_cfg,
                controller=pid,
                observation_topic=mb_config.get('observation_topic', data_sources['primary_data']),
                observation_key=mb_config.get('observation_key'),
                action_topic=mb_config.get('action_topic', control_targets['primary_target']),
                command_topic=mb_config.get('command_topic'),
                feedback_topic=mb_config.get('feedback_topic'),
                log_observations=log_observations,
            )
            agents.append(agent)
        elif agent_type == 'CentralDispatcherAgent':
            agent = CentralDispatcherAgent(
                agent_id=agent_id,
                message_bus=message_bus,
                **{k: v for k, v in agent_config.items() if k not in {'type', 'agent_id'}},
            )
            agents.append(agent)
        elif agent_type == 'RainfallAgent':
            rainfall_cfg = agent_config.get('config', {})
            if not rainfall_cfg:
                raise ValueError("RainfallAgent requires a 'config' section.")
            agent = RainfallAgent(
                agent_id=agent_id,
                message_bus=message_bus,
                **rainfall_cfg,
            )
            agents.append(agent)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    return agents


def _identify_components(config: Dict[str, Any]) -> Tuple[str, str]:
    reservoir_name = None
    gate_name = None
    for name, comp_cfg in config['components'].items():
        if comp_cfg['type'] == 'Reservoir' and reservoir_name is None:
            reservoir_name = name
        elif comp_cfg['type'] == 'Gate' and gate_name is None:
            gate_name = name
    if not reservoir_name or not gate_name:
        raise ValueError("Configuration must define at least one Reservoir and one Gate component.")
    return reservoir_name, gate_name


def extract_simulation_data(history: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, np.ndarray]:
    reservoir_name, gate_name = _identify_components(config)
    base_inflow = config['components'][reservoir_name].get('parameters', {}).get('inflow', 0.0)

    time_data = np.array([entry['time'] for entry in history], dtype=float)
    reservoir_levels = np.array([entry[reservoir_name]['water_level'] for entry in history], dtype=float)
    reservoir_inflow = np.array([entry[reservoir_name].get('inflow', 0.0) for entry in history], dtype=float)
    gate_opening = np.array([entry[gate_name]['opening'] for entry in history], dtype=float)
    gate_outflow = np.array([entry[gate_name].get('outflow', 0.0) for entry in history], dtype=float)
    rainfall_inflow = np.maximum(reservoir_inflow - base_inflow, 0.0)

    return {
        'time': time_data,
        'reservoir_levels': reservoir_levels,
        'reservoir_inflow': reservoir_inflow,
        'gate_opening': gate_opening,
        'gate_outflow': gate_outflow,
        'rainfall_inflow': rainfall_inflow,
        'base_inflow': base_inflow,
    }


def analyze_results(config: Dict[str, Any], data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    analysis_cfg = config.get('analysis', {})
    target_level = analysis_cfg.get('setpoint', 12.0)
    steady_tol = analysis_cfg.get('steady_state_tolerance', 0.1)
    window = int(analysis_cfg.get('steady_state_window', 120))
    max_allowable_level = analysis_cfg.get('max_allowable_level', target_level + 0.3)
    score_weights = analysis_cfg.get('score_weights', {'steady_state': 0.4, 'overshoot': 0.3, 'recovery': 0.3})

    time = data['time']
    levels = data['reservoir_levels']
    gate_opening = data['gate_opening']

    final_level = float(levels[-1])
    final_error = abs(final_level - target_level)
    max_level = float(np.max(levels))
    overshoot = max(0.0, max_level - target_level)

    recent_levels = levels[-window:] if window < len(levels) else levels
    steady_band = float(np.max(np.abs(recent_levels - target_level)))

    # Rainfall recovery time
    rainfall_agent_cfg = next(
        (cfg for cfg in config['agents'].values() if cfg['type'] == 'RainfallAgent'),
        None,
    )
    rainfall_end = 0.0
    if rainfall_agent_cfg:
        rain_cfg = rainfall_agent_cfg['config']
        rainfall_end = rain_cfg['start_time'] + rain_cfg['duration']

    recovery_time = float('inf')
    for t, level in zip(time, levels):
        if t >= rainfall_end and abs(level - target_level) <= steady_tol:
            recovery_time = float(t - rainfall_end)
            break

    recovery_target = config.get('validation', {}).get('metrics', {}).get('recovery_duration', 240)

    score = 0.0
    score_breakdown = {}

    steady_ok = steady_band <= steady_tol
    score_breakdown['steady_state'] = steady_ok
    if steady_ok:
        score += score_weights.get('steady_state', 0.0)

    overshoot_ok = max_level <= max_allowable_level
    score_breakdown['overshoot'] = overshoot_ok
    if overshoot_ok:
        score += score_weights.get('overshoot', 0.0)

    recovery_ok = recovery_time <= recovery_target
    score_breakdown['recovery'] = recovery_ok
    if recovery_ok:
        score += score_weights.get('recovery', 0.0)

    validation_cfg = config.get('validation', {}).get('metrics', {})
    validation_results = {
        'final_error': final_error <= validation_cfg.get('final_error_max', steady_tol),
        'overshoot': overshoot <= validation_cfg.get('overshoot_max', max_allowable_level - target_level),
        'recovery_time': recovery_time <= validation_cfg.get('recovery_duration', recovery_target),
    }

    overall_pass = all(validation_results.values()) and score >= config.get('validation', {}).get('scoring', {}).get('minimum_pass_score', 1.0)

    return {
        'final_level': final_level,
        'final_error': final_error,
        'max_level': max_level,
        'overshoot': overshoot,
        'steady_band': steady_band,
        'recovery_time': recovery_time,
        'score': score,
        'score_breakdown': score_breakdown,
        'validation_results': validation_results,
        'overall_pass': overall_pass,
        'target_level': target_level,
        'rainfall_end': rainfall_end,
    }


def generate_plots(config: Dict[str, Any], data: Dict[str, np.ndarray]) -> None:
    viz_cfg = config.get('visualization', {})
    if not viz_cfg.get('enabled', True):
        return

    time = data['time']
    levels = data['reservoir_levels']
    gate_opening = data['gate_opening']
    rainfall = data['rainfall_inflow']

    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

    axes[0].plot(time, levels, label='Reservoir Level', color='#1f77b4', linewidth=2)
    target = config.get('analysis', {}).get('setpoint', 12.0)
    axes[0].axhline(target, color='r', linestyle='--', linewidth=1.5, label=f'Target {target:.2f} m')
    axes[0].set_ylabel('Water Level (m)')
    axes[0].set_title('Reservoir Water Level Response')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(time, gate_opening, color='#2ca02c', linewidth=2)
    axes[1].set_ylabel('Gate Opening (m)')
    axes[1].set_title('Gate Command Tracking')
    axes[1].grid(True, alpha=0.3)

    axes[2].fill_between(time, rainfall, color='#ff7f0e', alpha=0.6, label='Rainfall Inflow')
    axes[2].set_ylabel('Rainfall Inflow (m³/s)')
    axes[2].set_xlabel('Time (s)')
    axes[2].set_title('Disturbance Profile')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    plt.tight_layout()
    save_path = Path(__file__).with_name(viz_cfg.get('save_path', 'disturbance_handling_results.png'))
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"结果图已保存到 {save_path}")


def generate_markdown_report(config: Dict[str, Any], data: Dict[str, np.ndarray], metrics: Dict[str, Any]) -> None:
    analysis_cfg = config.get('analysis', {})
    report_name = analysis_cfg.get('report_filename', 'disturbance_handling_report.md')
    report_path = Path(__file__).with_name(report_name)

    lines = [
        "# 扰动响应示例自动验证报告",
        "",
        "本报告由 `run_config.py` 自动生成，用于记录 `agent_based/06_handling_disturbances` 示例的仿真验证结果。",
        "",
        "## 仿真配置",
        f"- 仿真时长：{config['simulation']['duration']} s",
        f"- 时间步长：{config['simulation']['dt']} s",
        f"- 目标水位：{metrics['target_level']:.2f} m",
        "",
        "## 核心结果",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 最终水位 | {metrics['final_level']:.3f} m |",
        f"| 稳态误差 | {metrics['final_error']:.3f} m |",
        f"| 最大水位 | {metrics['max_level']:.3f} m |",
        f"| 超调量 | {metrics['overshoot']:.3f} m |",
        f"| 恢复时间 | {metrics['recovery_time']:.1f} s |",
        f"| 综合评分 | {metrics['score']:.3f} |",
        "",
        "## 验证结论",
    ]

    for check, passed in metrics['validation_results'].items():
        status = "通过 ✅" if passed else "未通过 ❌"
        lines.append(f"- {check}：{status}")

    status = "通过 ✅" if metrics['overall_pass'] else "未通过 ❌"
    lines.append(f"- 综合判定：{status}")
    lines.append("")
    lines.append("## 运行环境")
    lines.append(f"- 报告生成时间：{datetime.now().isoformat()}\n")

    report_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"分析报告已生成：{report_path}")


def run_simulation(config: Dict[str, Any]) -> SimulationHarness:
    print("--- 正在构建扰动仿真 ---")

    simulation_cfg = {
        'start_time': config['simulation'].get('start_time', 0),
        'end_time': config['simulation']['duration'],
        'dt': config['simulation']['dt'],
    }
    harness = SimulationHarness(config=simulation_cfg)
    message_bus = harness.message_bus

    components = create_components(config, message_bus)
    for name, component in components.items():
        harness.add_component(name, component)

    agents = create_agents(config, components, message_bus)
    for agent in agents:
        harness.add_agent(agent)

    for connection in config.get('connections', []):
        harness.add_connection(connection['from'], connection['to'])

    harness.build()
    print("--- 开始仿真 ---")
    harness.run_mas_simulation()
    print("--- 仿真完成 ---")
    return harness


def main() -> None:
    config_path = Path(__file__).with_name('config.yml')
    config = load_config(config_path)

    harness = run_simulation(config)
    data = extract_simulation_data(harness.history, config)
    metrics = analyze_results(config, data)

    generate_plots(config, data)
    generate_markdown_report(config, data, metrics)

    if metrics['overall_pass']:
        print("✅ 示例验证通过，控制系统成功抑制扰动影响。")
    else:
        print("❌ 示例验证未通过，请检查参数或模型设置。")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Configuration-driven pump station control simulation."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml
import matplotlib.pyplot as plt

# Ensure project root available for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.core_engine.testing.common_agents import DemandAgent, MonitoringAgent
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent

from analysis_utils import evaluate_flow_tracking  # pylint: disable=wrong-import-position


def load_config(config_path: Path) -> Dict:
    with config_path.open('r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def create_components(config: Dict, harness: SimulationHarness) -> Dict[str, object]:
    components: Dict[str, object] = {}
    topics = config.get('communication', {}).get('topics', {})
    action_prefix = topics.get('pump_action_prefix', 'action.pump')

    for name, comp_config in config.get('components', {}).items():
        comp_type = comp_config.get('type')
        if comp_type == 'Reservoir':
            component = Reservoir(
                name=name,
                initial_state=comp_config.get('initial_state', {}),
                parameters=comp_config.get('parameters', {}),
            )
        elif comp_type == 'PumpStation':
            pumps: List[Pump] = []
            pump_definitions = comp_config.get('pumps', [])
            station_bus = comp_config.get('message_bus', {})
            prefix = station_bus.get('control_topic_prefix', action_prefix)
            for idx, pump_def in enumerate(pump_definitions, start=1):
                pump_id = pump_def.get('id') or f"{name}_pump_{idx}"
                initial_state = pump_def.get('initial_state', {})
                parameters = pump_def.get('parameters', {})
                pump_bus = pump_def.get('message_bus', {})
                action_topic = pump_bus.get('action_topic') or f"{prefix}.{pump_id}"
                pump = Pump(
                    name=pump_id,
                    initial_state=initial_state,
                    parameters=parameters,
                    message_bus=harness.message_bus,
                    action_topic=action_topic,
                )
                pumps.append(pump)

            component = PumpStation(
                name=name,
                initial_state=comp_config.get('initial_state', {}),
                parameters=comp_config.get('parameters', {}),
                pumps=pumps,
            )
        else:
            raise ValueError(f"Unsupported component type: {comp_type}")

        harness.add_component(name, component)
        components[name] = component

    return components


def connect_components(config: Dict, harness: SimulationHarness) -> None:
    for connection in config.get('connections', []):
        harness.add_connection(connection['from'], connection['to'])


def create_agents(config: Dict, components: Dict[str, object], harness: SimulationHarness):
    agents_config = config.get('agents', {})
    agents = []

    topics = config.get('communication', {}).get('topics', {})
    demand_topic = topics.get('demand')

    demand_cfg = agents_config.get('demand_agent')
    if demand_cfg:
        demand_topic = demand_cfg.get('demand_topic', demand_topic)
        demand_agent = DemandAgent(
            agent_id=demand_cfg.get('agent_id', 'demand_agent'),
            message_bus=harness.message_bus,
            demand_topic=demand_topic,
            demand_schedule=demand_cfg.get('demand_schedule', {}),
        )
        agents.append(demand_agent)

    monitor_cfg = agents_config.get('monitoring_agent')
    monitoring_agent = None
    if monitor_cfg:
        monitored_components = {}
        for alias, comp_id in monitor_cfg.get('components', {}).items():
            if comp_id in components:
                monitored_components[alias] = components[comp_id]
        monitoring_agent = MonitoringAgent(
            agent_id=monitor_cfg.get('agent_id', 'monitor'),
            components=monitored_components,
            monitoring_interval=monitor_cfg.get('monitoring_interval', 60.0),
        )
        agents.append(monitoring_agent)

    controller_cfg = agents_config.get('pump_controller')
    pump_controller = None
    if controller_cfg:
        target_name = controller_cfg.get('target_component')
        pump_station = components.get(target_name)
        if not pump_station:
            raise ValueError(f"Pump controller target component '{target_name}' not found")
        pump_controller = PumpControlAgent(
            agent_id=controller_cfg.get('agent_id', 'pump_ctrl_agent'),
            message_bus=harness.message_bus,
            pump_station=pump_station,
            demand_topic=controller_cfg.get('demand_topic') or demand_topic,
            control_topic_prefix=controller_cfg.get('control_topic_prefix') or topics.get('pump_action_prefix'),
        )

    for agent in agents:
        harness.add_agent(agent)

    return agents, pump_controller, monitoring_agent


def run_simulation(config: Dict, harness: SimulationHarness, agents: List, pump_controller: PumpControlAgent):
    dt = config['simulation']['dt']
    duration = config['simulation']['duration']
    num_steps = int(duration / dt)

    for step in range(num_steps):
        current_time = step * dt
        for agent in agents:
            agent.run(current_time)
        if pump_controller:
            pump_controller.execute_control_logic()
        harness._step_physical_models(dt)  # pylint: disable=protected-access

        step_history = {"time": current_time}
        for component_id in harness.sorted_components:
            step_history[component_id] = harness.components[component_id].get_state()
        if pump_controller:
            step_history['demand'] = pump_controller.current_demand
        harness.history.append(step_history)


def generate_report(config: Dict, results: Dict[str, object], output_dir: Path) -> Path:
    analysis_cfg = config.get('analysis', {})
    report_file = Path(analysis_cfg.get('report_file', 'pump_station_report.md'))
    if not report_file.is_absolute():
        report_file = output_dir / report_file
    report_file.parent.mkdir(parents=True, exist_ok=True)

    segments = results['segments']
    score = results['score']
    tolerance = results.get('tolerance')

    lines = [
        "# 泵站协同控制示例自动验证报告",
        "",
        "本报告由 `run_config.py` 自动生成，用于记录 `agent_based/08_pump_station_control` 示例的仿真与验证结果。",
        "",
        "## 仿真配置",
        f"- 仿真时长：{config['simulation']['duration']} s",
        f"- 时间步长：{config['simulation']['dt']} s",
        f"- 需求主题：{config['communication']['topics'].get('demand', 'demand.pump.flow')}",
        f"- 控制前缀：{config['communication']['topics'].get('pump_action_prefix', 'action.pump')}",
        "",
        "## 流量跟踪表现",
        "| 时间段 (s) | 目标流量 (m³/s) | 平均流量 (m³/s) | 绝对误差 (m³/s) |",
        "| --- | --- | --- | --- |",
    ]

    for segment in segments:
        lines.append(
            f"| {segment['start']:.0f}-{segment['end']:.0f} | "
            f"{segment['target']:.2f} | {segment['average_flow']:.2f} | {segment['abs_error']:.2f} |"
        )

    lines.extend([
        "",
        "## 验证结论",
        f"- 允许误差：±{tolerance:.2f} m³/s" if tolerance is not None else "- 允许误差：未设置",
        f"- 评分：{score:.3f} （1.000 表示完全通过）",
        f"- 验证结果：{'通过 ✅' if score >= analysis_cfg.get('score_target', 1.0) else '未通过 ❌'}",
        "",
        "## 生成时间",
        f"- {datetime.now().astimezone().isoformat(timespec='seconds')}",
    ])

    report_file.write_text("\n".join(lines), encoding='utf-8')
    return report_file


def generate_plots(config: Dict, harness: SimulationHarness, output_dir: Path):
    viz_cfg = config.get('visualization', {})
    if not viz_cfg.get('enabled', False):
        return None

    times = [entry['time'] for entry in harness.history]
    flows = [entry['ps1'].get('total_outflow', 0.0) for entry in harness.history]
    demands = [entry.get('demand', 0.0) for entry in harness.history]

    plt.figure(figsize=(12, 6))
    plt.plot(times, flows, label='实际流量', linewidth=2)
    plt.step(times, demands, label='需求流量', where='post', linestyle='--')
    plt.xlabel('时间 (s)')
    plt.ylabel('流量 (m³/s)')
    plt.title('泵站出流与需求对比')
    plt.grid(True, alpha=0.3)
    plt.legend()

    save_path = Path(viz_cfg.get('save_path', '08_pump_station_results.png'))
    if not save_path.is_absolute():
        save_path = output_dir / save_path
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    return save_path


def main(config_path: str = 'config.yml'):
    scenario_dir = Path(__file__).parent
    config = load_config(scenario_dir / config_path)

    harness = SimulationHarness({
        'duration': config['simulation']['duration'],
        'dt': config['simulation']['dt'],
    })

    components = create_components(config, harness)
    connect_components(config, harness)
    harness.build()

    agents, pump_controller, monitoring_agent = create_agents(config, components, harness)
    run_simulation(config, harness, agents, pump_controller)

    results = evaluate_flow_tracking(harness.history)
    analysis_cfg = config.get('analysis', {})
    score_target = analysis_cfg.get('score_target', 1.0)
    if results['score'] < score_target:
        raise SystemExit('Validation failed: flow tracking score below target.')

    report_path = generate_report(config, results, scenario_dir)
    plot_path = generate_plots(config, harness, scenario_dir)

    print('\n=== 验证结果 ===')
    print(f"评分：{results['score']:.3f}，目标：{score_target:.3f}")
    print(f"报告位置：{report_path}")
    if plot_path:
        print(f"图表已保存：{plot_path}")
    else:
        print('未生成图表（配置禁用或未指定）。')

    if monitoring_agent:
        data = monitoring_agent.get_monitoring_data()
        print(f"监控记录条数：{len(data)}")


if __name__ == '__main__':
    main()

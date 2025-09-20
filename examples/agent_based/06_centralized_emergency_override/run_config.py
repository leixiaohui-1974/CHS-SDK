#!/usr/bin/env python3
"""Configuration-driven runner for the centralized emergency override scenario."""

import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core_lib.core_engine.testing.simulation_harness import SimulationHarness  # noqa: E402
from core_lib.local_agents.control.custom_controllers import DirectGateController  # noqa: E402
from core_lib.local_agents.control.local_control_agent import LocalControlAgent  # noqa: E402
from core_lib.local_agents.control.pid_controller import PIDController  # noqa: E402
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent  # noqa: E402
from core_lib.central_coordination.dispatch.central_dispatcher import CentralDispatcherAgent  # noqa: E402
from core_lib.physical_objects.gate import Gate  # noqa: E402
from core_lib.physical_objects.reservoir import Reservoir  # noqa: E402


@dataclass
class ScenarioMetrics:
    time: List[float]
    levels: List[float]
    openings: List[float]
    override_time: float
    max_level: float
    final_level: float


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_components(config: Dict[str, Any], harness: SimulationHarness) -> Dict[str, Any]:
    components_cfg = config.get("components", {})
    components: Dict[str, Any] = {}

    for comp_id, comp_cfg in components_cfg.items():
        comp_type = comp_cfg["type"]
        initial_state = comp_cfg.get("initial_state", {})
        parameters = comp_cfg.get("parameters", {})

        if comp_type == "Reservoir":
            component = Reservoir(comp_id, initial_state, parameters)
        elif comp_type == "Gate":
            mb_cfg = comp_cfg.get("message_bus", {})
            if mb_cfg.get("enabled"):
                component = Gate(
                    comp_id,
                    initial_state,
                    parameters,
                    message_bus=harness.message_bus,
                    action_topic=mb_cfg.get("action_topic"),
                    action_key=mb_cfg.get("action_key", "opening"),
                )
            else:
                component = Gate(comp_id, initial_state, parameters)
        else:
            raise ValueError(f"Unsupported component type: {comp_type}")

        harness.add_component(comp_id, component)
        components[comp_id] = component

    return components


def _apply_connections(config: Dict[str, Any], harness: SimulationHarness) -> None:
    for connection in config.get("connections", []):
        upstream = connection["from"]
        downstream = connection["to"]
        harness.add_connection(upstream, downstream)


def _instantiate_controller(controller_cfg: Dict[str, Any]):
    ctrl_type = controller_cfg.get("type") or controller_cfg.get("class")
    params = controller_cfg.get("parameters", {})

    if ctrl_type == "PIDController":
        return PIDController(
            Kp=params.get("Kp", params.get("kp", 0.0)),
            Ki=params.get("Ki", params.get("ki", 0.0)),
            Kd=params.get("Kd", params.get("kd", 0.0)),
            setpoint=params.get("setpoint", 0.0),
            min_output=params.get("min_output", params.get("output_limits", [0.0, 1.0])[0]),
            max_output=params.get("max_output", params.get("output_limits", [0.0, 1.0])[1]),
        )
    if ctrl_type == "DirectGateController":
        return DirectGateController(**params)

    raise ValueError(f"Unsupported controller type: {ctrl_type}")


def _build_agents(config: Dict[str, Any], harness: SimulationHarness, components: Dict[str, Any]) -> None:
    dt = config.get("simulation", {}).get("dt", 1.0)
    agents_cfg = config.get("agents", {})

    for agent_name, agent_cfg in agents_cfg.items():
        agent_type = agent_cfg.get("type")
        agent_id = agent_cfg.get("agent_id", agent_name)

        if agent_type == "DigitalTwinAgent":
            simulated_object_name = agent_cfg.get("simulated_object")
            simulated_object = components[simulated_object_name]
            state_topic = agent_cfg.get("message_bus", {}).get("state_topic")
            agent = DigitalTwinAgent(agent_id, simulated_object, harness.message_bus, state_topic)
            harness.add_agent(agent)
            continue

        if agent_type == "LocalControlAgent":
            controller_cfg = agent_cfg.get("controller", {})
            controller = _instantiate_controller(controller_cfg)

            mb_cfg = agent_cfg.get("message_bus", {})
            observation_topic = mb_cfg.get("observation_topic")
            observation_key = mb_cfg.get("observation_key")
            action_topic = mb_cfg.get("action_topic")
            command_topic = mb_cfg.get("command_topic")

            data_sources = agent_cfg.get("data_sources", {})
            control_targets = agent_cfg.get("control_targets", {})

            agent = LocalControlAgent(
                agent_id=agent_id,
                message_bus=harness.message_bus,
                dt=dt,
                target_component=agent_cfg.get("target_component"),
                control_type=agent_cfg.get("control_type", "local_control"),
                data_sources=data_sources,
                control_targets=control_targets,
                allocation_config=agent_cfg.get("allocation", {}),
                controller_config=controller_cfg,
                controller=controller,
                observation_topic=observation_topic,
                observation_key=observation_key,
                action_topic=action_topic,
                command_topic=command_topic,
                log_observations=agent_cfg.get("logging", {}).get("log_observations", False),
            )
            harness.add_agent(agent)
            continue

        if agent_type == "CentralDispatcherAgent":
            dispatcher = CentralDispatcherAgent(
                agent_id=agent_id,
                message_bus=harness.message_bus,
                mode=agent_cfg.get("mode", "rule"),
                subscribed_topic=agent_cfg.get("subscribed_topic"),
                observation_key=agent_cfg.get("observation_key"),
                command_topic=agent_cfg.get("command_topic"),
                dispatcher_params=agent_cfg.get("dispatcher_params", {}),
            )
            harness.add_agent(dispatcher)
            continue

        raise ValueError(f"Unsupported agent type: {agent_type}")


def _run_harness(harness: SimulationHarness) -> None:
    while harness.is_running and harness.t < harness.end_time:
        harness.step()


def _extract_metrics(harness: SimulationHarness) -> ScenarioMetrics:
    time_series, levels, openings = [], [], []
    override_time = None

    for step in harness.history:
        time_series.append(step["time"])
        level = step["main_reservoir"].get("water_level", 0.0)
        opening = step["flood_gate"].get("opening", 0.0)
        levels.append(level)
        openings.append(opening)
        if override_time is None and opening >= 0.95:
            override_time = step["time"]

    override_time = override_time if override_time is not None else float("nan")
    return ScenarioMetrics(
        time=time_series,
        levels=levels,
        openings=openings,
        override_time=override_time,
        max_level=max(levels),
        final_level=levels[-1],
    )


def _evaluate(metrics: ScenarioMetrics, config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    analysis_cfg = config.get("analysis", {})
    target = analysis_cfg.get("target_safe_level", 99.5)
    tolerance = analysis_cfg.get("tolerance", 0.1)
    deadline = analysis_cfg.get("override_deadline", 180.0)
    max_level = analysis_cfg.get("max_allowable_level", metrics.max_level)

    final_within = abs(metrics.final_level - target) <= tolerance
    override_quick = metrics.override_time <= deadline
    peak_contained = metrics.max_level <= max_level

    score = 1.0 if all([final_within, override_quick, peak_contained]) else 0.0
    details = {
        "target": target,
        "tolerance": tolerance,
        "deadline": deadline,
        "max_allowable_level": max_level,
        "final_level": metrics.final_level,
        "override_time": metrics.override_time,
        "max_level": metrics.max_level,
        "score": score,
    }
    return score, details


def _write_report(config: Dict[str, Any], metrics: ScenarioMetrics, details: Dict[str, Any]) -> None:
    report_name = config.get("analysis", {}).get("report_filename", "centralized_emergency_override_report.md")
    report_path = Path(__file__).with_name(report_name)

    lines = [
        "# 集中式紧急防洪调度验证报告",
        "",
        "本报告由 `run_config.py` 自动生成，记录 `agent_based/06_centralized_emergency_override` 示例的仿真结果。",
        "",
        "## 运行配置",
        f"- 仿真时长：{len(metrics.time)} s",
        f"- 时间步长：{config.get('simulation', {}).get('dt', 1.0)} s",
        f"- 报告生成时间：{datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "## 关键指标",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 最终水位 | {metrics.final_level:.3f} m |",
        f"| 峰值水位 | {metrics.max_level:.3f} m |",
        f"| 紧急指令触发时间 | {metrics.override_time:.1f} s |",
        f"| 评分 | {details['score']:.3f} |",
        "",
        "## 判定准则",
        f"- 目标安全水位：{details['target']:.3f} ± {details['tolerance']:.3f} m",
        f"- 紧急指令触发截止：{details['deadline']:.1f} s",
        f"- 允许的峰值水位上限：{details['max_allowable_level']:.3f} m",
        "",
        "## 结论",
        "- 验证结果：{}".format("通过 ✅" if details["score"] >= 1.0 else "未通过 ❌"),
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report written to {report_path}")


def run_from_config(config_path: Path) -> float:
    config = load_config(config_path)
    harness = SimulationHarness(config=config.get("simulation", {}))

    components = _build_components(config, harness)
    _apply_connections(config, harness)
    harness.build()

    _build_agents(config, harness, components)
    _run_harness(harness)

    metrics = _extract_metrics(harness)
    score, details = _evaluate(metrics, config)

    print("--- Centralized Emergency Override (YAML) ---")
    print(f"Score: {score:.3f}")
    print(f"Maximum water level: {metrics.max_level:.3f} m")
    print(f"Final water level: {metrics.final_level:.3f} m")
    print(f"Override time: {metrics.override_time:.1f} s")

    _write_report(config, metrics, details)
    return score


def main() -> None:
    config_path = Path(__file__).with_name("config.yml")
    score = run_from_config(config_path)
    if score < 1.0:
        raise SystemExit("Validation failed: score below 1.0")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()


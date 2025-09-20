#!/usr/bin/env python3
"""Hard-coded centralized emergency override scenario."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from core_lib.central_coordination.dispatch.central_dispatcher import (  # noqa: E402
    CentralDispatcherAgent,
)
from core_lib.core_engine.testing.simulation_harness import (  # noqa: E402
    SimulationHarness,
)
from core_lib.local_agents.control.custom_controllers import (  # noqa: E402
    DirectGateController,
)
from core_lib.local_agents.control.local_control_agent import (  # noqa: E402
    LocalControlAgent,
)
from core_lib.local_agents.perception.digital_twin_agent import (  # noqa: E402
    DigitalTwinAgent,
)
from core_lib.physical_objects.gate import Gate  # noqa: E402
from core_lib.physical_objects.reservoir import Reservoir  # noqa: E402


SIM_CONFIG = {"duration": 600, "dt": 1.0}
RESERVOIR_CONFIG = {
    "initial_state": {"water_level": 98.0, "volume": 260000.0},
    "parameters": {
        "surface_area": 2200.0,  # m²
        "storage_curve": [[0.0, 90.0], [650000.0, 110.0]],
        "inflow": 200.0,  # m³/s constant inflow
    },
}
GATE_CONFIG = {
    "initial_state": {"opening": 0.12},
    "parameters": {
        "width": 6.0,
        "discharge_coefficient": 0.78,
        "max_opening": 1.0,
        "max_rate_of_change": 0.3,
    },
}

TOPICS = {
    "state": "state/reservoir/main",
    "action": "action/gate/flood",
    "command": "command/gate/flood",
}


@dataclass
class ScenarioMetrics:
    time: List[float]
    levels: List[float]
    openings: List[float]
    override_time: float
    max_level: float
    final_level: float


def _create_harness() -> SimulationHarness:
    harness = SimulationHarness(config=SIM_CONFIG)

    reservoir = Reservoir(
        "main_reservoir",
        RESERVOIR_CONFIG["initial_state"],
        RESERVOIR_CONFIG["parameters"],
    )

    gate = Gate(
        "flood_gate",
        GATE_CONFIG["initial_state"],
        GATE_CONFIG["parameters"],
        message_bus=harness.message_bus,
        action_topic=TOPICS["action"],
        action_key="opening",
    )

    harness.add_component("main_reservoir", reservoir)
    harness.add_component("flood_gate", gate)
    harness.add_connection("main_reservoir", "flood_gate")
    harness.build()
    return harness


def _create_agents(harness: SimulationHarness) -> None:
    bus = harness.message_bus

    twin_reservoir = DigitalTwinAgent(
        agent_id="twin_reservoir",
        simulated_object=harness.components["main_reservoir"],
        message_bus=bus,
        state_topic=TOPICS["state"],
    )
    harness.add_agent(twin_reservoir)

    gate_controller = DirectGateController(setpoint=0.12)
    gate_agent = LocalControlAgent(
        agent_id="gate_follower",
        message_bus=bus,
        dt=harness.dt,
        target_component="flood_gate",
        control_type="direct_gate_control",
        data_sources={"primary_data": TOPICS["state"]},
        control_targets={"primary_target": TOPICS["action"]},
        allocation_config={},
        controller_config={"type": "DirectGateController", "parameters": {"setpoint": 0.12}},
        controller=gate_controller,
        observation_topic=TOPICS["state"],
        observation_key="water_level",
        action_topic=TOPICS["action"],
        command_topic=TOPICS["command"],
        log_observations=False,
    )
    harness.add_agent(gate_agent)

    dispatcher = CentralDispatcherAgent(
        agent_id="central_dispatcher",
        message_bus=bus,
        mode="rule",
        subscribed_topic=TOPICS["state"],
        observation_key="water_level",
        command_topic=TOPICS["command"],
        dispatcher_params={
            "low_level": 98.9,
            "high_level": 99.1,
            "high_setpoint": 0.12,
            "low_setpoint": 1.0,
        },
    )
    harness.add_agent(dispatcher)


def run_simulation() -> Dict[str, ScenarioMetrics]:
    harness = _create_harness()
    _create_agents(harness)

    while harness.is_running and harness.t < harness.end_time:
        harness.step()

    time_series, level_series, opening_series = [], [], []
    override_time = None
    for step in harness.history:
        time_series.append(step["time"])
        level = step["main_reservoir"].get("water_level", 0.0)
        opening = step["flood_gate"].get("opening", 0.0)
        level_series.append(level)
        opening_series.append(opening)
        if override_time is None and opening >= 0.95:
            override_time = step["time"]

    override_time = override_time if override_time is not None else float("nan")

    metrics = ScenarioMetrics(
        time=time_series,
        levels=level_series,
        openings=opening_series,
        override_time=override_time,
        max_level=max(level_series),
        final_level=level_series[-1],
    )

    summary = {
        "score": _evaluate(metrics),
        "metrics": metrics,
    }
    return {"summary": summary}


def _evaluate(metrics: ScenarioMetrics) -> float:
    target_final_level = 99.0
    tolerance = 0.1
    override_deadline = 220.0

    final_within_band = abs(metrics.final_level - target_final_level) <= tolerance
    override_quick = metrics.override_time <= override_deadline
    peak_contained = metrics.max_level <= 99.2

    if all([final_within_band, override_quick, peak_contained]):
        return 1.0
    return 0.0


def main() -> None:
    results = run_simulation()["summary"]
    metrics: ScenarioMetrics = results["metrics"]

    print("--- Centralized Emergency Override Summary ---")
    print(f"Score: {results['score']:.3f}")
    print(f"Maximum water level: {metrics.max_level:.3f} m")
    print(f"Final water level: {metrics.final_level:.3f} m")
    print(f"Gate override triggered at: {metrics.override_time:.1f} s")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()


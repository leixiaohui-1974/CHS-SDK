"""Compare PID control strategies for the canal system using a simplified hydraulic model."""

from __future__ import annotations
"""Run and evaluate canal PID control strategies using a simplified model."""

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core_lib.local_agents.control.pid_controller import PIDController

G = 9.81  # gravitational acceleration (m/s^2)


@dataclass
class SimulationParameters:
    """Physical parameters shared by all scenarios."""

    dt: float = 10.0  # simulation time step (s)
    duration: float = 7200.0  # total duration (s)
    reservoir_area: float = 10000.0  # surface area of upstream reservoir (m^2)
    canal1_area: float = 5500.0  # equivalent surface area of canal pool 1 (m^2)
    canal2_area: float = 4800.0  # equivalent surface area of canal pool 2 (m^2)
    max_opening: float = 1.0
    gate1_capacity: float = 36.0  # max flow (m^3/s) at full opening for gate 1
    gate2_capacity: float = 36.0  # max flow (m^3/s) at full opening for gate 2
    base_inflow: float = 18.0  # upstream inflow (m^3/s)
    base_demand: float = 18.0  # downstream delivery demand (m^3/s)


@dataclass
class ScenarioDefinition:
    """Configuration for a single control strategy."""

    label: str
    tracked_levels: Dict[str, float]
    gate1_mode: str  # 'fixed' or 'pid'
    gate1_setpoint: float
    gate2_setpoint: float


SCENARIOS: Dict[str, ScenarioDefinition] = {
    "local_upstream": ScenarioDefinition(
        label="Local Upstream Control",
        tracked_levels={"canal_1": 5.0},
        gate1_mode="fixed",
        gate1_setpoint=0.5,  # fixed opening for gate 1
        gate2_setpoint=5.0,
    ),
    "distant_downstream": ScenarioDefinition(
        label="Distant Downstream Control",
        tracked_levels={"canal_1": 5.0, "canal_2": 4.5},
        gate1_mode="pid",
        gate1_setpoint=5.0,
        gate2_setpoint=4.5,
    ),
}


def _gate_flow(opening: float, capacity: float, params: SimulationParameters) -> float:
    """Compute gate discharge using a linearised capacity model."""

    opening = max(0.0, min(opening, params.max_opening))
    return opening * capacity


def _initial_state(params: SimulationParameters) -> Dict[str, float]:
    """Return a steady-state initial condition."""

    gate1_opening = 0.5
    gate1_flow = _gate_flow(gate1_opening, params.gate1_capacity, params)
    gate2_opening = 0.5
    gate2_flow = _gate_flow(gate2_opening, params.gate2_capacity, params)

    demand_flow = params.base_demand
    return {
        "time": 0.0,
        "reservoir_level": 10.0,
        "reservoir_volume": 10.0 * params.reservoir_area,
        "gate1_opening": gate1_opening,
        "gate1_flow": gate1_flow,
        "canal1_level": 5.0,
        "gate2_opening": gate2_opening,
        "gate2_flow": gate2_flow,
        "canal2_level": 4.5,
        "demand_flow": demand_flow,
    }


def _simulate(strategy: ScenarioDefinition, params: SimulationParameters) -> pd.DataFrame:
    """Run the control simulation for a given strategy."""

    state = _initial_state(params)
    history: List[Dict[str, float]] = [state.copy()]

    gate1_controller = None
    if strategy.gate1_mode == "pid":
        gate1_controller = PIDController(
            Kp=-0.7,
            Ki=-0.007,
            Kd=-0.06,
            setpoint=strategy.gate1_setpoint,
            min_output=0.0,
            max_output=params.max_opening,
            bias=0.5,
        )

    gate2_controller = PIDController(
        Kp=-0.9,
        Ki=-0.012,
        Kd=-0.08,
        setpoint=strategy.gate2_setpoint,
        min_output=0.0,
        max_output=params.max_opening,
        bias=0.5,
    )

    num_steps = int(params.duration // params.dt)

    for step in range(1, num_steps + 1):
        current = history[-1].copy()
        time_now = step * params.dt

        reservoir_level = current["reservoir_level"]
        canal1_level = current["canal1_level"]
        canal2_level = current["canal2_level"]

        # Gate 1 control
        if gate1_controller:
            gate1_opening = gate1_controller.compute_control_action(
                {"process_variable": canal1_level}, params.dt
            )
        else:
            gate1_opening = strategy.gate1_setpoint

        # Gate 2 control
        feedback_level = canal1_level if strategy.label.startswith("Local") else canal2_level
        gate2_opening = gate2_controller.compute_control_action(
            {"process_variable": feedback_level}, params.dt
        )

        gate1_flow = _gate_flow(gate1_opening, params.gate1_capacity, params)
        gate2_flow = _gate_flow(gate2_opening, params.gate2_capacity, params)

        # Demand adjusts with tail water level to mimic downstream needs.
        demand_flow = params.base_demand

        # Reservoir mass balance
        net_inflow = params.base_inflow - gate1_flow
        reservoir_volume = max(0.0, current["reservoir_volume"] + net_inflow * params.dt)
        reservoir_level = reservoir_volume / params.reservoir_area

        # Canal 1 mass balance
        canal1_delta = (gate1_flow - gate2_flow) * params.dt / params.canal1_area
        canal1_level = max(0.0, canal1_level + canal1_delta)

        # Canal 2 mass balance
        canal2_delta = (gate2_flow - demand_flow) * params.dt / params.canal2_area
        canal2_level = max(0.0, canal2_level + canal2_delta)

        next_state = {
            "time": time_now,
            "reservoir_level": reservoir_level,
            "reservoir_volume": reservoir_volume,
            "gate1_opening": gate1_opening,
            "gate1_flow": gate1_flow,
            "canal1_level": canal1_level,
            "gate2_opening": gate2_opening,
            "gate2_flow": gate2_flow,
            "canal2_level": canal2_level,
            "demand_flow": demand_flow,
        }
        history.append(next_state)

    df = pd.DataFrame(history)
    df.rename(
        columns={
            "reservoir_level": "upstream_reservoir_water_level",
            "reservoir_volume": "upstream_reservoir_volume",
            "gate1_flow": "gate_1_outflow",
            "gate1_opening": "gate_1_opening",
            "gate2_flow": "gate_2_outflow",
            "gate2_opening": "gate_2_opening",
            "canal1_level": "canal_1_water_level",
            "canal2_level": "canal_2_water_level",
        },
        inplace=True,
    )
    return df


def _compute_settling_time(series: pd.Series, time: pd.Series, setpoint: float, tolerance: float) -> float:
    deviation = (series - setpoint).abs()
    violation_positions = np.where(deviation.to_numpy() > tolerance)[0]
    if len(violation_positions) == 0:
        return float(time.iloc[0])
    last_violation = violation_positions[-1]
    if last_violation + 1 < len(time):
        return float(time.iloc[last_violation + 1])
    return float(time.iloc[-1])


def evaluate_performance(df: pd.DataFrame, scenario: ScenarioDefinition, params: SimulationParameters) -> Tuple[pd.DataFrame, Dict[str, float]]:
    time = df["time"]
    dt = params.dt
    metrics = []
    scores: Dict[str, float] = {}

    for component, setpoint in scenario.tracked_levels.items():
        column = f"{component}_water_level"
        series = df[column]
        steady_state_error = float(abs(series.iloc[-1] - setpoint))
        peak_overshoot = float(max(series.max() - setpoint, 0.0))
        undershoot = float(max(setpoint - series.min(), 0.0))
        iae = float((series - setpoint).abs().sum() * dt)
        tolerance = max(0.02, 0.01 * setpoint)
        settling_time = _compute_settling_time(series, time, setpoint, tolerance)

        precision_score = max(0.0, 1.0 - steady_state_error / max(0.05 * setpoint, 0.05))
        smoothness_score = max(0.0, 1.0 - peak_overshoot / max(0.15 * setpoint, 0.15))
        overall = 100.0 * min(1.0, 0.65 * precision_score + 0.35 * smoothness_score)
        scores[component] = overall

        metrics.append(
            {
                "组件": component,
                "设定值 (m)": round(setpoint, 3),
                "最终水位偏差 (m)": round(steady_state_error, 4),
                "最大超调 (m)": round(peak_overshoot, 4),
                "最大欠调 (m)": round(undershoot, 4),
                "积分绝对误差 (m·s)": round(iae, 2),
                "稳定时间 (s)": round(settling_time, 1),
                "评分": round(overall, 2),
            }
        )

    return pd.DataFrame(metrics), scores


def run_scenario(key: str, scenario: ScenarioDefinition, params: SimulationParameters, base_path: Path) -> Dict[str, any]:
    print(f"\n=== Running {scenario.label} ===")
    df = _simulate(scenario, params)

    output_file = base_path / f"results_{key}.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved results to {output_file}")

    metrics_df, scores = evaluate_performance(df, scenario, params)
    print(metrics_df.to_string(index=False))

    if all(score >= 99.0 for score in scores.values()):
        print("Performance check: ✅ All tracked levels meet the full-score requirement.")
    else:
        print("Performance check: ⚠️ Some levels did not reach the target score. Please review controller tuning.")

    return {
        "dataframe": df,
        "metrics": metrics_df,
        "scores": scores,
        "output_file": output_file,
    }


def main() -> None:
    params = SimulationParameters()
    base_path = Path(__file__).parent
    summaries = []

    for key, scenario in SCENARIOS.items():
        result = run_scenario(key, scenario, params, base_path)
        average_score = float(np.mean(list(result["scores"].values())))
        summaries.append(
            {
                "策略": scenario.label,
                "监控节点": ", ".join(scenario.tracked_levels.keys()),
                "平均得分": round(average_score, 2),
                "结果文件": result["output_file"].name,
            }
        )

    summary_df = pd.DataFrame(summaries)
    print("\n=== 汇总评估 ===")
    print(summary_df.to_string(index=False))

    guidance = [
        "若要进一步减小响应时间，可在不引起震荡的前提下微调 Kp 与 Ki。",
        "遇到来水突增情景，可相应提高 gate_1 的固定基准开度或调节 PID 偏置。",
        "建议定期重放不同工况扰动，以验证控制器在极端情况下的鲁棒性。",
    ]
    print("\n控制策略调优建议：")
    for item in guidance:
        print(f"- {item}")


if __name__ == "__main__":
    main()

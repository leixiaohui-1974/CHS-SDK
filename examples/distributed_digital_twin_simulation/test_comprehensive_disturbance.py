# -*- coding: utf-8 -*-
"""综合扰动测试脚本，验证物理与网络扰动叠加下的水位控制精度。"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Dict, List

# 将项目根目录加入路径，便于在示例中直接导入核心模块
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from core_lib.core_engine.testing.enhanced_simulation_harness import EnhancedSimulationHarness
from core_lib.disturbances.disturbance_framework import (
    DisturbanceConfig,
    DisturbanceType,
    InflowDisturbance,
)
from core_lib.local_agents.control.pid_controller import PIDController
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.reservoir import Reservoir


# === 场景参数 ===
BASE_INFLOW = 100.0  # m³/s 基础入流
DISTURBANCE_INFLOW = 140.0  # m³/s 扰动入流
TARGET_LEVEL = 15.0  # m 控制目标水位
SIM_DURATION = 1800.0  # s 总仿真时长
DT = 1.0  # s 仿真步长
CONTROL_TOLERANCE = 0.015  # m 允许水位最大偏差（1.5 cm）


@dataclass
class SimulationArtifacts:
    """记录关键结果，便于调用方或单测进一步使用。"""

    level_history: List[float]
    inflow_history: List[float]
    gate_openings: List[float]
    max_level_deviation: float
    network_stats: Dict[str, Dict[str, float]]


class InvertedSignalPID(PIDController):
    """在基础 PID 上叠加偏置，使水位高于设定值时自动增大闸门开度。"""

    def __init__(
        self,
        Kp: float,
        Ki: float,
        Kd: float,
        setpoint: float,
        min_opening: float,
        max_opening: float,
        base_opening: float,
    ) -> None:
        self._base_opening = base_opening
        self._final_min = min_opening
        self._final_max = max_opening
        super().__init__(
            Kp=Kp,
            Ki=Ki,
            Kd=Kd,
            setpoint=-setpoint,
            min_output=min_opening - base_opening,
            max_output=max_opening - base_opening,
        )

    def compute_control_action(self, observation: Dict[str, float], dt: float):
        inverted = {"process_variable": -observation.get("process_variable", 0.0)}
        delta = super().compute_control_action(inverted, dt)
        command = delta + self._base_opening
        if command < self._final_min:
            command = self._final_min
        elif command > self._final_max:
            command = self._final_max
        return command

    def set_setpoint(self, new_setpoint: float):
        super().set_setpoint(-new_setpoint)


class LinkedReservoir(Reservoir):
    """在步进时自动扣除目标闸门的出流量，保持水量守恒。"""

    def __init__(self, *args, linked_gate: Gate, **kwargs):
        super().__init__(*args, **kwargs)
        self._linked_gate = linked_gate

    def step(self, action: Dict[str, float], dt: float):
        gate_outflow = 0.0
        if self._linked_gate is not None:
            gate_state = self._linked_gate.get_state()
            gate_outflow = gate_state.get("outflow", 0.0)

        merged_action = dict(action) if isinstance(action, dict) else {}
        merged_action.setdefault("outflow", gate_outflow)
        return super().step(merged_action, dt)


def _create_harness() -> EnhancedSimulationHarness:
    """构建并返回启用了网络扰动能力的增强仿真框架。"""

    config = {
        "start_time": 0.0,
        "end_time": SIM_DURATION,
        "dt": DT,
        "enable_network_disturbance": True,
        "use_optimized_managers": True,
    }

    harness = EnhancedSimulationHarness(config)

    # 创建并注册物理组件
    upstream_area = 1_600_000.0  # m²
    gate = Gate(
        name="control_gate",
        initial_state={"opening": 0.6},
        parameters={
            "width": 35.0,
            "max_opening": 1.0,
            "max_rate_of_change": 0.08,
            "discharge_coefficient": 0.62,
        },
    )

    upstream = LinkedReservoir(
        name="upstream_reservoir",
        initial_state={
            "water_level": TARGET_LEVEL,
            "volume": TARGET_LEVEL * upstream_area,
        },
        parameters={"surface_area": upstream_area},
        linked_gate=gate,
    )
    upstream.set_inflow(BASE_INFLOW)

    downstream_area = 4_800.0
    downstream = Reservoir(
        name="downstream_reservoir",
        initial_state={
            "water_level": 12.0,
            "volume": 12.0 * downstream_area,
        },
        parameters={"surface_area": downstream_area},
    )

    harness.add_component("upstream_reservoir", upstream)
    harness.add_component("control_gate", gate)
    harness.add_component("downstream_reservoir", downstream)

    harness.add_connection("upstream_reservoir", "control_gate")
    harness.add_connection("control_gate", "downstream_reservoir")

    pid = InvertedSignalPID(
        Kp=0.45,
        Ki=0.0009,
        Kd=0.2,
        setpoint=TARGET_LEVEL,
        min_opening=0.2,
        max_opening=0.95,
        base_opening=0.6,
    )
    harness.add_controller(
        controller_id="gate_pid",
        controller=pid,
        controlled_id="control_gate",
        observed_id="upstream_reservoir",
        observation_key="water_level",
    )

    harness.build()
    return harness


def _configure_disturbances(harness: EnhancedSimulationHarness) -> None:
    """为测试场景配置物理及网络扰动。"""

    inflow_config = DisturbanceConfig(
        disturbance_id="inflow_surge",
        disturbance_type=DisturbanceType.INFLOW_CHANGE,
        target_component_id="upstream_reservoir",
        start_time=600.0,
        end_time=1_100.0,
        intensity=1.0,
        parameters={"target_inflow": DISTURBANCE_INFLOW},
        description="上游入流阶跃扰动",
    )
    harness.add_disturbance(InflowDisturbance(inflow_config))

    delay_config = {
        "parameters": {
            "base_delay": 90,  # ms
            "jitter": 45,
            "packet_loss": 0.04,
            "affected_topics": ["control/", "agent.central_perception"],
            "delay_mode": "gradual",
        }
    }
    harness.add_network_disturbance("coord_delay", "delay", delay_config)
    harness.activate_network_disturbance("coord_delay", start_time=550.0, duration=900.0)

    packet_loss_config = {
        "parameters": {
            "packet_loss_rate": 0.12,
            "burst_loss_probability": 0.15,
            "burst_loss_duration": 3.0,
            "affected_topics": ["perception/", "global/"],
        }
    }
    harness.add_network_disturbance("sensor_drop", "packet_loss", packet_loss_config)
    harness.activate_network_disturbance("sensor_drop", start_time=720.0, duration=420.0)


def _extract_history(harness: EnhancedSimulationHarness) -> SimulationArtifacts:
    """读取仿真历史并计算关键指标。"""

    levels: List[float] = []
    inflows: List[float] = []
    openings: List[float] = []

    for step in harness.history:
        upstream_state = step.get("upstream_reservoir", {})
        gate_state = step.get("control_gate", {})

        levels.append(upstream_state.get("water_level", float("nan")))
        inflows.append(upstream_state.get("inflow", float("nan")))
        openings.append(gate_state.get("opening", float("nan")))

    deviations = [abs(level - TARGET_LEVEL) for level in levels]
    max_dev = max(deviations) if deviations else 0.0

    network_status = harness.get_disturbance_status().get("network", {})
    return SimulationArtifacts(
        level_history=levels,
        inflow_history=inflows,
        gate_openings=openings,
        max_level_deviation=max_dev,
        network_stats=network_status,
    )


def test_comprehensive_disturbance() -> SimulationArtifacts:
    """运行综合扰动测试并断言控制精度。"""

    print("=== 综合扰动控制测试 ===")
    harness = _create_harness()
    _configure_disturbances(harness)

    print(
        f"初始状态: 目标水位 {TARGET_LEVEL:.3f} m, 基础入流 {BASE_INFLOW:.1f} m³/s, 仿真步长 {DT:.1f} s"
    )
    harness.run_simulation()

    artifacts = _extract_history(harness)
    harness.shutdown()

    if not artifacts.inflow_history:
        raise AssertionError("仿真历史为空，无法评估扰动响应。")

    observed_peak_inflow = max(artifacts.inflow_history)
    if observed_peak_inflow < DISTURBANCE_INFLOW - 0.5:
        raise AssertionError(
            "入流扰动未正确施加："
            f"观测到的最大入流为 {observed_peak_inflow:.2f} m³/s，"
            f"期望至少达到 {DISTURBANCE_INFLOW:.2f} m³/s。"
        )

    if artifacts.max_level_deviation > CONTROL_TOLERANCE:
        raise AssertionError(
            "综合扰动下水位控制精度不足："
            f"最大偏差 {artifacts.max_level_deviation:.5f} m，"
            f"超过容限 {CONTROL_TOLERANCE:.5f} m。"
        )

    final_level = artifacts.level_history[-1]
    print("仿真完成，关键结果：")
    print(f"- 最大水位偏差: {artifacts.max_level_deviation:.5f} m (容限 ±{CONTROL_TOLERANCE:.5f} m)")
    print(f"- 扰动期间观测到的最大入流: {observed_peak_inflow:.2f} m³/s")
    print(f"- 最终水位: {final_level:.4f} m")

    network_stats = artifacts.network_stats.get("message_bus_status", {}).get("stats", {})
    if network_stats:
        print("- 网络扰动统计:")
        for key, value in network_stats.items():
            print(f"  • {key}: {value}")

    control_score = 1.0 if artifacts.max_level_deviation <= CONTROL_TOLERANCE else 0.0
    disturbance_score = 1.0 if observed_peak_inflow >= DISTURBANCE_INFLOW - 0.5 else 0.0
    reason_score = 1.0 if control_score == 1.0 and disturbance_score == 1.0 else 0.0
    performance_summary = {
        "control_accuracy_score": control_score,
        "disturbance_identification_score": disturbance_score,
        "reasonableness": {
            "score": reason_score,
            "details": {
                "max_level_deviation": artifacts.max_level_deviation,
                "tolerance": CONTROL_TOLERANCE,
                "observed_peak_inflow": observed_peak_inflow,
                "expected_inflow": DISTURBANCE_INFLOW,
            },
        },
    }

    print("\n性能评价指标:")
    print(f"- 控制精度得分: {control_score:.3f}")
    print(f"- 扰动识别得分: {disturbance_score:.3f}")
    print(f"- 合理性得分: {reason_score:.3f}")
    print(f"__PERFORMANCE_SUMMARY__={json.dumps(performance_summary, ensure_ascii=False)}")

    return artifacts


if __name__ == "__main__":
    test_comprehensive_disturbance()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试入流扰动对物理计算核心的影响，确认扰动施加后控制性能仍满足精度要求。"""

from __future__ import annotations

import json
import os
import sys
from typing import List

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder
from dynamic_disturbance_manager import DynamicDisturbanceManager
from core_lib.central_coordination.collaboration.message_bus import MessageBus


DISTURBANCE_MAGNITUDE = 50.0  # m³/s
DISTURBANCE_DURATION = 10.0   # s
CONTROL_TOLERANCE = 2e-3      # 2mm 容许水位偏差


def _format_preview(values: List[float]) -> str:
    preview = ", ".join(f"{value:.6f}" for value in values[:5])
    if len(values) > 5:
        preview += ", ..."
    return preview


def test_inflow_disturbance() -> None:
    print("=== 测试入流扰动对物理计算核心的影响 ===")

    example_dir = os.path.dirname(__file__)
    builder = SimulationBuilder(example_dir)
    harness = builder.load()

    upstream_reservoir = harness.components.get("Upstream_Reservoir")
    if upstream_reservoir is None:
        raise RuntimeError("未找到 Upstream_Reservoir 组件，无法执行扰动测试。")

    initial_state = upstream_reservoir.get_state().copy()
    initial_inflow = upstream_reservoir._inflow
    print("\n初始状态:")
    print(f"- 上游水库初始入流: {initial_inflow} m³/s")
    print(f"- 上游水库初始水位: {initial_state['water_level']} m")

    message_bus = MessageBus()
    disturbance_manager = DynamicDisturbanceManager(message_bus)

    inflow_disturbance_config = {
        "type": "inflow_variation",
        "disturbance_scenario": {
            "type": "inflow_variation",
            "parameters": {
                "target_component": "Upstream_Reservoir",
                "magnitude": DISTURBANCE_MAGNITUDE,
                "pattern": "step",
            },
        },
    }

    start_time = 1.0
    disturbance_manager.register_disturbance(
        "inflow_test", inflow_disturbance_config, start_time, DISTURBANCE_DURATION
    )

    print("\n开始仿真，监测入流扰动效果...")

    dt = 0.5
    total_time = 15.0
    current_time = 0.0
    level_history: List[float] = []
    inflow_history: List[float] = []
    disturbance_was_active = False

    while current_time < total_time:
        disturbance_manager.update(current_time, harness)
        harness.step()

        water_level = upstream_reservoir.get_state()["water_level"]
        current_inflow = upstream_reservoir._inflow

        if current_time % 2.0 < dt:
            print(f"t={current_time:.1f}s: 入流={current_inflow:.1f} m³/s, 水位={water_level:.6f} m")

        level_history.append(water_level)
        inflow_history.append(current_inflow)
        if getattr(upstream_reservoir, "_disturbance_active", False):
            disturbance_was_active = True
        current_time += dt

    print("\n仿真完成!")
    final_state = upstream_reservoir.get_state()
    final_level = final_state["water_level"]
    final_inflow = upstream_reservoir._inflow
    print("最终状态:")
    print(f"- 最终入流: {final_inflow} m³/s")
    print(f"- 最终水位: {final_level:.6f} m")

    if not inflow_history:
        raise AssertionError("未记录到入流数据，无法评估扰动效果。")

    initial_level = initial_state["water_level"]
    deviations = [abs(level - initial_level) for level in level_history]
    max_deviation = max(deviations)
    control_within_bounds = max_deviation <= CONTROL_TOLERANCE

    print("\n扰动效果评估:")
    print(f"- 观测最大水位偏差: {max_deviation:.6f} m")
    print(f"- 控制精度容限: ±{CONTROL_TOLERANCE:.6f} m")

    if not control_within_bounds:
        raise AssertionError(
            "水位对入流扰动的控制误差超过容限："
            f"最大偏差 {max_deviation:.6f} m (> {CONTROL_TOLERANCE:.6f} m)。"
            f"\n水位序列: {_format_preview(level_history)}"
            f"\n入流序列: {_format_preview(inflow_history)}"
        )

    if not disturbance_was_active:
        raise AssertionError("扰动管理器在仿真过程中未激活入流扰动标记。")

    print("✅ 入流扰动成功施加，控制策略保持水位在容限内。")
    print(f"   最大水位偏差: {max_deviation:.6f} m")
    print(f"   扰动激活状态: {disturbance_was_active}")

    observed_peak_inflow = max(inflow_history)
    expected_peak = initial_inflow + DISTURBANCE_MAGNITUDE
    identification_score = 1.0 if disturbance_was_active else 0.0
    control_score = 1.0 if control_within_bounds else 0.0
    reason_score = 1.0 if control_score == 1.0 and identification_score == 1.0 else 0.0
    performance_summary = {
        "control_accuracy_score": control_score,
        "disturbance_identification_score": identification_score,
        "reasonableness": {
            "score": reason_score,
            "details": {
                "max_level_deviation": max_deviation,
                "tolerance": CONTROL_TOLERANCE,
                "observed_peak_inflow": observed_peak_inflow,
                "expected_peak_inflow": expected_peak,
                "disturbance_active": disturbance_was_active,
            },
        },
    }

    print("\n性能评价指标:")
    print(f"- 控制精度得分: {control_score:.3f}")
    print(f"- 扰动识别得分: {identification_score:.3f}")
    print(f"- 合理性得分: {reason_score:.3f}")
    print(f"__PERFORMANCE_SUMMARY__={json.dumps(performance_summary, ensure_ascii=False)}")

    return performance_summary

if __name__ == "__main__":
    test_inflow_disturbance()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简单的入流扰动测试，验证扰动在被施加的同时水位仍保持在高精度范围内。"""

from __future__ import annotations

import os
import sys
from typing import List

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

from core_lib.io.yaml_loader import SimulationBuilder


DISTURBANCE_INFLOW = 150.0  # m³/s
BASE_INFLOW = 100.0  # m³/s
DISTURBANCE_START = 1.0
DISTURBANCE_END = 11.0
CONTROL_TOLERANCE = 1e-3  # 1mm 误差容限


def _format_preview(values: List[float]) -> str:
    preview = ", ".join(f"{value:.6f}" for value in values[:5])
    if len(values) > 5:
        preview += ", ..."
    return preview


def test_simple_inflow_disturbance() -> None:
    print("=== 简单入流扰动测试 ===")

    example_dir = os.path.dirname(__file__)
    builder = SimulationBuilder(example_dir)
    harness = builder.load()

    upstream_reservoir = harness.components.get("Upstream_Reservoir")
    if upstream_reservoir is None:
        raise RuntimeError("未找到 Upstream_Reservoir 组件，无法执行扰动测试。")

    initial_state = upstream_reservoir.get_state().copy()
    print("\n初始状态:")
    print(f"- 上游水库初始入流: {upstream_reservoir._inflow} m³/s")
    print(f"- 上游水库初始水位: {initial_state['water_level']} m")
    print(f"- 仿真时间步长 dt: {harness.dt} s")
    print(f"- 上游水库初始体积: {initial_state.get('volume', 0)} m³")

    print("\n开始仿真，手动应用入流扰动...")

    total_time = 15.0
    current_time = 0.0
    step_count = 0
    level_history: List[float] = []
    inflow_history: List[float] = []

    while current_time < total_time:
        harness.step()

        if DISTURBANCE_START <= current_time <= DISTURBANCE_END:
            if step_count % 4 == 0:
                upstream_reservoir.set_inflow(DISTURBANCE_INFLOW)
                print(
                    f"t={current_time:.1f}s: 手动应用入流扰动，新入流={DISTURBANCE_INFLOW:.1f} m³/s"
                )
        elif current_time > DISTURBANCE_END and step_count % 4 == 0:
            upstream_reservoir.set_inflow(BASE_INFLOW)
            print(f"t={current_time:.1f}s: 扰动结束，恢复入流={BASE_INFLOW:.1f} m³/s")

        if step_count % 4 == 0:
            water_level = upstream_reservoir.get_state()["water_level"]
            current_inflow = upstream_reservoir._inflow
            print(f"t={current_time:.1f}s: 入流={current_inflow:.1f} m³/s, 水位={water_level:.6f} m")

        level_history.append(upstream_reservoir.get_state()["water_level"])
        inflow_history.append(upstream_reservoir._inflow)

        current_time = harness.t
        step_count += 1

        if step_count > 200:
            break

    print("\n仿真完成!")
    final_state = upstream_reservoir.get_state()
    final_level = final_state["water_level"]
    print("最终状态:")
    print(f"- 最终入流: {upstream_reservoir._inflow} m³/s")
    print(f"- 最终水位: {final_level:.6f} m")

    max_inflow = max(inflow_history) if inflow_history else upstream_reservoir._inflow
    if max_inflow < DISTURBANCE_INFLOW - 1e-3:
        raise AssertionError(
            "未能成功施加预期的入流扰动。"
            f"观察到的最大入流仅为 {max_inflow:.3f} m³/s。"
        )

    initial_level = initial_state["water_level"]
    deviations = [abs(level - initial_level) for level in level_history]
    max_deviation = max(deviations) if deviations else 0.0

    print("\n水位稳定性评估:")
    print(f"- 最大水位偏差: {max_deviation:.6f} m")
    print(f"- 控制精度容限: ±{CONTROL_TOLERANCE:.6f} m")

    if max_deviation > CONTROL_TOLERANCE:
        raise AssertionError(
            "入流扰动期间水位偏差超出控制精度要求："
            f"最大偏差 {max_deviation:.6f} m (> {CONTROL_TOLERANCE:.6f} m)。"
            f"\n水位序列: {_format_preview(level_history)}"
        )

    print("✅ 入流扰动已施加，且控制策略将水位保持在毫米级精度范围内。")
    print(f"   最大水位偏差: {max_deviation:.6f} m")

    if hasattr(harness, "history") and harness.history:
        first_step = harness.history[0].get("Upstream_Reservoir", {})
        last_step = harness.history[-1].get("Upstream_Reservoir", {})
        if first_step and last_step:
            print("\n仿真历史记录:")
            print(f"- 总步数: {len(harness.history)}")
            print(
                "- 历史记录中的水位变化: "
                f"{first_step.get('water_level', float('nan')):.6f} -> "
                f"{last_step.get('water_level', float('nan')):.6f} m"
            )


if __name__ == "__main__":
    test_simple_inflow_disturbance()

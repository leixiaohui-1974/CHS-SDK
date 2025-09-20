#!/usr/bin/env python3
"""Pump station simulation with common agents and automatic reporting."""
from __future__ import annotations

import os
import sys

# Ensure project root on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_lib.core_engine.testing.common_agents import DemandAgent, MonitoringAgent
from core_lib.core_engine.testing.simulation_builder import SimulationBuilder
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent

from analysis_utils import evaluate_flow_tracking  # pylint: disable=wrong-import-position
from scenario_settings import (  # pylint: disable=wrong-import-position
    ACTION_TOPIC_PREFIX,
    DEMAND_PROFILE,
    DEMAND_TOPIC,
    SIMULATION_CONFIG,
    create_builder,
)


def run_pump_station_with_common_agents():
    """Run the pump station scenario using reusable agents for orchestration."""
    print("=== Pump Station Simulation (common agents & reporting) ===")

    builder: SimulationBuilder = create_builder()

    demand_agent = DemandAgent(
        agent_id="demand_agent",
        message_bus=builder.harness.message_bus,
        demand_topic=DEMAND_TOPIC,
        demand_schedule=DEMAND_PROFILE,
    )
    monitoring_agent = MonitoringAgent(
        agent_id="monitor",
        components={
            "source_res": builder.get_component("source_res"),
            "downstream_res": builder.get_component("downstream_res"),
            "ps1": builder.get_component("ps1"),
        },
        monitoring_interval=60.0,
    )

    builder.add_agent(demand_agent)
    builder.add_agent(monitoring_agent)

    pump_station = builder.get_component("ps1")
    pump_controller = PumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=builder.harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=ACTION_TOPIC_PREFIX,
    )

    builder.build()

    dt = SIMULATION_CONFIG["dt"]
    num_steps = int(SIMULATION_CONFIG["duration"] / dt)

    for step in range(num_steps):
        current_time = step * dt
        for agent in builder.agents:
            agent.run(current_time)
        pump_controller.execute_control_logic()
        builder.harness._step_physical_models(dt)  # pylint: disable=protected-access

        step_history = {"time": current_time}
        for component_id in builder.harness.sorted_components:
            step_history[component_id] = builder.harness.components[component_id].get_state()
        step_history["demand"] = pump_controller.current_demand
        builder.harness.history.append(step_history)

    results = evaluate_flow_tracking(builder.harness.history)
    score = results["score"]

    print("\n--- Common Agent Simulation Summary ---")
    for segment in results["segments"]:
        print(
            f"Segment {segment['start']:5.0f}-{segment['end']:5.0f}s: "
            f"target={segment['target']:5.1f} m³/s | "
            f"avg_flow={segment['average_flow']:5.2f} m³/s | "
            f"abs_error={segment['abs_error']:4.2f}"
        )
    print(f"Overall score: {score:.3f}")

    if score < 1.0:
        raise SystemExit("Common agent implementation failed validation.")

    monitoring_data = monitoring_agent.get_monitoring_data()
    if monitoring_data:
        first_entry = monitoring_data[0]
        last_entry = monitoring_data[-1]
        print("\nMonitoring insights:")
        print(f"Initial pump station state: {first_entry.get('ps1', {})}")
        print(f"Final pump station state:   {last_entry.get('ps1', {})}")
    else:
        print("No monitoring data recorded.")

    print("Common agent workflow achieved perfect tracking.")


if __name__ == "__main__":
    run_pump_station_with_common_agents()

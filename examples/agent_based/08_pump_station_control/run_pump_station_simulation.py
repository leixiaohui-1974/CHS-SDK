#!/usr/bin/env python3
"""Hard-coded pump station control scenario.

This script demonstrates the original "single file" implementation style where the
physical system, agents and evaluation logic are defined directly in Python code.
It serves as the most explicit version of the example and mirrors the parameters
used by the configuration-driven workflows.
"""
from __future__ import annotations

import os
import sys

# Ensure project root on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core_lib.core_engine.testing.common_agents import DemandAgent
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.local_agents.control.pump_control_agent import PumpControlAgent
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.physical_objects.reservoir import Reservoir

from analysis_utils import evaluate_flow_tracking  # pylint: disable=wrong-import-position
from scenario_settings import (  # pylint: disable=wrong-import-position
    ACTION_TOPIC_PREFIX,
    DEMAND_PROFILE,
    DEMAND_TOPIC,
    FLOW_TOLERANCE,
    PUMP_INITIAL_STATE,
    PUMP_PARAMETERS,
    RESERVOIR_CONFIG,
    SIMULATION_CONFIG,
)


def run_pump_station_simulation():
    """Run the direct Python pump station simulation."""
    print("=== Pump Station Control Simulation (hard-coded version) ===")

    harness = SimulationHarness({
        "duration": SIMULATION_CONFIG["duration"],
        "dt": SIMULATION_CONFIG["dt"],
    })

    source_reservoir = Reservoir(
        "source_res",
        initial_state={"water_level": RESERVOIR_CONFIG["source"]["water_level"]},
        parameters={
            "surface_area": RESERVOIR_CONFIG["source"]["surface_area"],
            "inflow": RESERVOIR_CONFIG["source"]["inflow"],
        },
    )
    downstream_reservoir = Reservoir(
        "downstream_res",
        initial_state={"water_level": RESERVOIR_CONFIG["downstream"]["water_level"]},
        parameters={"surface_area": RESERVOIR_CONFIG["downstream"]["surface_area"]},
    )

    pumps = []
    for index in range(1, 4):
        action_topic = f"{ACTION_TOPIC_PREFIX}.p{index}"
        pump = Pump(
            name=f"p{index}",
            initial_state=PUMP_INITIAL_STATE.copy(),
            parameters=PUMP_PARAMETERS.copy(),
            message_bus=harness.message_bus,
            action_topic=action_topic,
        )
        pumps.append(pump)

    pump_station = PumpStation("ps1", initial_state={}, parameters={}, pumps=pumps)

    harness.add_component("source_res", source_reservoir)
    harness.add_component("ps1", pump_station)
    harness.add_component("downstream_res", downstream_reservoir)
    harness.add_connection("source_res", "ps1")
    harness.add_connection("ps1", "downstream_res")
    harness.build()

    demand_agent = DemandAgent(
        agent_id="demand_agent",
        message_bus=harness.message_bus,
        demand_topic=DEMAND_TOPIC,
        demand_schedule=DEMAND_PROFILE,
    )
    harness.add_agent(demand_agent)

    pump_controller = PumpControlAgent(
        agent_id="pump_ctrl_agent",
        message_bus=harness.message_bus,
        pump_station=pump_station,
        demand_topic=DEMAND_TOPIC,
        control_topic_prefix=ACTION_TOPIC_PREFIX,
    )

    dt = SIMULATION_CONFIG["dt"]
    num_steps = int(SIMULATION_CONFIG["duration"] / dt)

    for step in range(num_steps):
        current_time = step * dt
        demand_agent.run(current_time)
        pump_controller.execute_control_logic()
        harness._step_physical_models(dt)  # pylint: disable=protected-access

        step_history = {"time": current_time}
        for component_id in harness.sorted_components:
            step_history[component_id] = harness.components[component_id].get_state()
        step_history["demand"] = pump_controller.current_demand
        harness.history.append(step_history)

        if step % 100 == 0:
            state = pump_station.get_state()
            print(
                f"t={current_time:5.1f}s | demand={pump_controller.current_demand:5.1f} m³/s | "
                f"active_pumps={state.get('active_pumps')} | flow={state.get('total_outflow', 0.0):5.2f} m³/s"
            )

    results = evaluate_flow_tracking(harness.history)
    score = results["score"]

    print("\n--- Performance Summary ---")
    for segment in results["segments"]:
        print(
            f"Segment {segment['start']:5.0f}-{segment['end']:5.0f}s: "
            f"target={segment['target']:5.1f} m³/s | "
            f"avg_flow={segment['average_flow']:5.2f} m³/s | "
            f"abs_error={segment['abs_error']:4.2f}"
        )
    print(f"Overall score: {score:.3f} (tolerance {FLOW_TOLERANCE} m³/s)")

    if score < 1.0:
        raise SystemExit("Pump station failed to meet the target accuracy.")

    print("Simulation complete with a perfect tracking score.")


if __name__ == "__main__":
    run_pump_station_simulation()

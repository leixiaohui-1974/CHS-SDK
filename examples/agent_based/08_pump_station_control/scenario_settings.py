"""Shared configuration for the pump station control example."""
from __future__ import annotations

from typing import Dict, List

from core_lib.core_engine.testing.simulation_builder import SimulationBuilder


DEMAND_TOPIC = "demand.pump.flow"
ACTION_TOPIC_PREFIX = "action.pump"

SIMULATION_CONFIG: Dict[str, float] = {
    "duration": 720.0,
    "dt": 1.0,
}

RESERVOIR_CONFIG: Dict[str, Dict[str, float]] = {
    "source": {
        "water_level": 11.5,
        "surface_area": 180000.0,
        "inflow": 32.0,
    },
    "downstream": {
        "water_level": 24.0,
        "surface_area": 220000.0,
    },
}

PUMP_PARAMETERS: Dict[str, float] = {
    "max_flow_rate": 12.5,
    "max_head": 22.0,
    "power_consumption_kw": 45.0,
}

PUMP_INITIAL_STATE: Dict[str, int] = {"status": 0}

DEMAND_PROFILE: Dict[float, float] = {
    0.0: 12.5,
    200.0: 25.0,
    380.0: 37.5,
    520.0: 12.5,
}

TARGET_PROFILE: List[Dict[str, float]] = [
    {"start": 0.0, "end": 200.0, "target": 12.5},
    {"start": 200.0, "end": 380.0, "target": 25.0},
    {"start": 380.0, "end": 520.0, "target": 37.5},
    {"start": 520.0, "end": SIMULATION_CONFIG["duration"], "target": 12.5},
]

FLOW_TOLERANCE = 0.25
SETTLING_MARGIN = 40.0


def create_builder() -> SimulationBuilder:
    """Construct a simulation builder with the shared pump-station setup."""
    builder = SimulationBuilder({
        "end_time": SIMULATION_CONFIG["duration"],
        "dt": SIMULATION_CONFIG["dt"],
    })

    builder.add_reservoir(
        "source_res",
        water_level=RESERVOIR_CONFIG["source"]["water_level"],
        surface_area=RESERVOIR_CONFIG["source"]["surface_area"],
        additional_parameters={"inflow": RESERVOIR_CONFIG["source"]["inflow"]},
    )
    builder.add_reservoir(
        "downstream_res",
        water_level=RESERVOIR_CONFIG["downstream"]["water_level"],
        surface_area=RESERVOIR_CONFIG["downstream"]["surface_area"],
    )

    builder.add_pump_station(
        "ps1",
        num_pumps=3,
        pump_max_flow=PUMP_PARAMETERS["max_flow_rate"],
        pump_max_head=PUMP_PARAMETERS["max_head"],
        pump_power=PUMP_PARAMETERS["power_consumption_kw"],
        control_topic_prefix=ACTION_TOPIC_PREFIX,
        pump_initial_state=PUMP_INITIAL_STATE,
        pump_parameters={
            "max_flow_rate": PUMP_PARAMETERS["max_flow_rate"],
            "max_head": PUMP_PARAMETERS["max_head"],
            "power_consumption_kw": PUMP_PARAMETERS["power_consumption_kw"],
        },
    )

    builder.connect_components([
        ("source_res", "ps1"),
        ("ps1", "downstream_res"),
    ])

    return builder

"""Utility functions for evaluating pump station performance."""
from __future__ import annotations

from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence

from scenario_settings import FLOW_TOLERANCE, SETTLING_MARGIN, TARGET_PROFILE


def compute_segment_metrics(times: Sequence[float], flows: Sequence[float]) -> List[Dict[str, float]]:
    """Aggregate average flow and absolute error for each demand segment."""
    metrics: List[Dict[str, float]] = []
    for segment in TARGET_PROFILE:
        start = segment["start"] + SETTLING_MARGIN
        end = segment["end"]
        segment_points = [
            flow for time_value, flow in zip(times, flows)
            if start <= time_value < end
        ]
        if not segment_points:
            continue
        avg_flow = mean(segment_points)
        metrics.append({
            "start": segment["start"],
            "end": segment["end"],
            "target": segment["target"],
            "average_flow": avg_flow,
            "abs_error": abs(avg_flow - segment["target"]),
        })
    return metrics


def evaluate_flow_tracking(history: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Evaluate simulation history and return score plus detailed metrics."""
    times: List[float] = []
    flows: List[float] = []
    pump_state_key: Optional[str] = None
    for entry in history:
        times.append(entry.get("time", 0.0))
        if pump_state_key is None:
            for key, value in entry.items():
                if key == "time":
                    continue
                if isinstance(value, dict) and (
                    "total_outflow" in value or "outflow" in value
                ):
                    pump_state_key = key
                    break
        ps_state = entry.get(pump_state_key or "ps1", {})
        flows.append(ps_state.get("total_outflow", ps_state.get("outflow", 0.0)))

    segment_data = compute_segment_metrics(times, flows)
    max_error = max((item["abs_error"] for item in segment_data), default=float("inf"))
    score = 1.0 if max_error <= FLOW_TOLERANCE else 0.0

    return {
        "score": score,
        "segments": segment_data,
        "max_error": max_error,
        "tolerance": FLOW_TOLERANCE,
    }

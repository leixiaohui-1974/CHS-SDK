"""
Pydantic models for the agents used in the hydraulic simulation.

These models define the expected structure and types for the 'params'
section of each agent's configuration in the API request.
"""
from pydantic import BaseModel, Field
from typing import Optional, Tuple, Union, Any, Dict, List

# --- Controller Models ---

class ControllerConfig(BaseModel):
    """
    Generic configuration for a controller.
    It specifies the controller's class and its specific parameters.
    """
    class_name: str = Field(..., alias='class', description="The Python class name of the controller.")
    params: Dict[str, Any] = Field(..., description="A dictionary of parameters for the controller's constructor.")


# --- Agent Parameter Models ---

class GateControlAgentParams(BaseModel):
    """Parameters for a GateControlAgent. This agent is linked via topics, not direct object reference."""
    controller: ControllerConfig = Field(..., description="The configuration for the control algorithm (e.g., PID).")
    observation_topic: str = Field(..., description="Topic to listen to for state observations.")
    observation_key: str = Field(..., description="Key in the observation message to use as input for the controller.")
    action_topic: str = Field(..., description="Topic to publish control actions to.")
    command_topic: Optional[str] = Field(None, description="Optional topic for receiving high-level commands like setpoint changes.")
    feedback_topic: Optional[str] = Field(None, description="Optional topic for receiving direct feedback from the controlled component.")


class ReservoirPerceptionAgentParams(BaseModel):
    """Parameters for a ReservoirPerceptionAgent."""
    target_component: str = Field(..., description="The name of the reservoir component to monitor.")
    state_topic: str = Field(..., description="Topic on which to publish the reservoir's state.")
    cognitive_config: Optional[Dict[str, Any]] = Field(None, description="Configuration for cognitive enhancement features.")


class CSVInflowAgentParams(BaseModel):
    """Parameters for a CsvInflowAgent. Field names must match the constructor arguments."""
    csv_file_path: str = Field(..., description="Path to the CSV file containing inflow data.")
    time_column: str = Field(..., description="Name of the column for time data.")
    data_column: str = Field(..., description="Name of the column for data values.")
    inflow_topic: str = Field(..., description="Topic to publish the inflow data on.")
    target_component: Optional[str] = Field(None, description="Optional name of the target component for context.")


# A Union of all possible agent parameter models.
AnyAgentParams = Union[
    GateControlAgentParams,
    ReservoirPerceptionAgentParams,
    CSVInflowAgentParams,
]

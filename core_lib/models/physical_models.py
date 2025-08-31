"""
Pydantic models for the physical components of the hydraulic simulation.

These models are used for data validation and serialization in the API,
ensuring that the configuration data for physical objects is well-formed
before the simulation starts.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Tuple, Optional, Dict

# Base model for common properties
class BasePhysicalObjectModel(BaseModel):
    """Base model for any physical component, requires a name for identification."""
    name: str = Field(..., description="Unique name of the component.")

# --- Reservoir Models ---

class ReservoirInitialState(BaseModel):
    """Initial state for a reservoir."""
    water_level: Optional[float] = Field(None, description="Initial water level in meters.")
    volume: Optional[float] = Field(None, description="Initial water volume in cubic meters.")
    outflow: float = Field(0.0, description="Initial outflow rate in m^3/s.")

class ReservoirParameters(BaseModel):
    """Parameters for configuring a reservoir."""
    storage_curve: Optional[List[Tuple[float, float]]] = Field(None, description="A curve defining the volume-level relationship as a list of [volume, level] pairs.")
    surface_area: Optional[float] = Field(None, description="Surface area of the reservoir in square meters (used if storage_curve is not provided).")
    area: Optional[float] = Field(None, description="Alias for surface_area.") # To support both from original code
    inflow_topics: Optional[List[Dict[str, str]]] = Field(None, description="List of topics for data-driven inflows.")
    outflow_topics: Optional[List[Dict[str, str]]] = Field(None, description="List of topics for data-driven outflows.")

    @validator('storage_curve')
    def validate_storage_curve(cls, v: Optional[List[Tuple[float, float]]]) -> Optional[List[Tuple[float, float]]]:
        if v is None:
            return v
        if len(v) < 2:
            raise ValueError("storage_curve must contain at least two points.")

        volumes = [point[0] for point in v]
        if not all(volumes[i] < volumes[i+1] for i in range(len(volumes) - 1)):
            raise ValueError("Volumes in storage_curve must be strictly increasing.")
        return v

class ReservoirModel(BasePhysicalObjectModel):
    """Pydantic model for a Reservoir component."""
    initial_state: ReservoirInitialState
    parameters: ReservoirParameters
    inflow_topic: Optional[str] = Field(None, description="Legacy topic for a single data-driven inflow.")

# --- Gate Models ---

class GateInitialState(BaseModel):
    """Initial state for a gate."""
    opening: float = Field(0.0, description="Initial opening of the gate (e.g., in meters or as a ratio).")
    outflow: float = Field(0.0, description="Initial outflow rate in m^3/s.")

class GateParameters(BaseModel):
    """Parameters for configuring a gate."""
    discharge_coefficient: float = Field(0.6, description="Discharge coefficient (C) for the orifice equation.")
    width: float = Field(2.0, description="Width of the gate in meters.")
    max_rate_of_change: Optional[float] = Field(0.05, description="Maximum rate of change of the gate opening per second.")
    max_opening: float = Field(1.0, description="Maximum physical opening of the gate.")

class GateModel(BasePhysicalObjectModel):
    """Pydantic model for a Gate component."""
    initial_state: GateInitialState
    parameters: GateParameters
    action_topic: Optional[str] = Field(None, description="Topic to subscribe to for control actions.")
    action_key: str = Field('opening', description="Key in the action message to look for the control value.")

# --- Pipe Models ---

class PipeInitialState(BaseModel):
    """Initial state for a pipe."""
    flow: float = Field(0.0, description="Initial flow rate in the pipe in m^3/s.")

class PipeParameters(BaseModel):
    """Parameters for configuring a pipe."""
    length: float = Field(..., description="Length of the pipe in meters.")
    diameter: float = Field(..., description="Diameter of the pipe in meters.")
    manning_coefficient: float = Field(0.013, description="Manning's roughness coefficient.")
    upstream_invert: float = Field(..., description="Invert elevation at the upstream end.")
    downstream_invert: float = Field(..., description="Invert elevation at the downstream end.")

class PipeModel(BasePhysicalObjectModel):
    """Pydantic model for a Pipe component."""
    initial_state: PipeInitialState
    parameters: PipeParameters

# --- UnifiedCanal Models ---

class UnifiedCanalInitialState(BaseModel):
    """Initial state for a unified canal."""
    water_depth: List[float] = Field(..., description="Initial water depth at each segment.")
    flow: List[float] = Field(..., description="Initial flow rate at each segment.")

class UnifiedCanalParameters(BaseModel):
    """Parameters for configuring a unified canal."""
    length: float
    bottom_width: float
    side_slope: float
    manning_coefficient: float
    upstream_invert: float
    downstream_invert: float
    num_segments: int

class UnifiedCanalModel(BasePhysicalObjectModel):
    """Pydantic model for a UnifiedCanal component."""
    initial_state: UnifiedCanalInitialState
    parameters: UnifiedCanalParameters

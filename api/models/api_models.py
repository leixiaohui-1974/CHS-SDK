"""API models for simulation requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Components Model ---
class ComponentsModel(BaseModel):
    """A container for all physical components in the simulation."""
    reservoirs: List[Dict[str, Any]] = Field([], description="List of reservoir components.")
    gates: List[Dict[str, Any]] = Field([], description="List of gate components.")
    pipes: List[Dict[str, Any]] = Field([], description="List of pipe components.")
    unified_canals: List[Dict[str, Any]] = Field([], description="List of unified canal components.")

# --- Topology Model ---
class TopologyConnectionModel(BaseModel):
    """Defines a single connection between two components."""
    upstream: str = Field(..., description="Name of the upstream component.")
    downstream: str = Field(..., description="Name of the downstream component.")

class TopologyModel(BaseModel):
    """Defines the connection graph of the physical components."""
    connections: List[TopologyConnectionModel] = Field([], description="List of all connections in the system.")

# --- Agent Models ---
class GenericAgentConfig(BaseModel):
    """A generic model for any agent configuration."""
    id: str = Field(..., description="Unique identifier for the agent instance.")
    class_name: str = Field(..., alias="class", description="The Python class for the agent.")
    params: Dict[str, Any] = Field({}, description="Parameters for the agent's constructor.")

class AgentsModel(BaseModel):
    """A container for all agent configurations."""
    agents: List[GenericAgentConfig]

# --- Main API Request Body Model ---
class SimulationRequest(BaseModel):
    """The main request body for the /run_simulation endpoint."""
    components: ComponentsModel
    topology: TopologyModel
    agents: AgentsModel

# --- Response Models ---
class CreateSimulationRequest(BaseModel):
    """Request model for creating a new simulation session."""
    name: str = Field(..., description="Simulation session name")
    description: Optional[str] = Field(None, description="Simulation description")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Simulation configuration")

class SimulationResponse(BaseModel):
    """Response model for simulation operations."""
    session_id: str = Field(..., description="Simulation session ID")
    status: str = Field(..., description="Current simulation status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
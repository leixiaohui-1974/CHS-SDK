"""
Pydantic models for the main API request body.

This file defines the top-level structures that aggregate the component,
agent, and topology models into a single, validatable request object
for the /run_simulation endpoint.
"""
from pydantic import BaseModel, Field, root_validator
from typing import List, Optional, Union, Literal

# Import parameter models from other files
from .physical_models import (
    ReservoirModel,
    GateModel,
    PipeModel,
    UnifiedCanalModel,
)
from .agent_models import (
    GateControlAgentParams,
    ReservoirPerceptionAgentParams,
    CSVInflowAgentParams,
)

# --- Components Model ---

class ComponentsModel(BaseModel):
    """A container for all physical components in the simulation, grouped by type."""
    reservoirs: List[ReservoirModel] = Field([], description="List of reservoir components.")
    gates: List[GateModel] = Field([], description="List of gate components.")
    pipes: List[PipeModel] = Field([], description="List of pipe components.")
    unified_canals: List[UnifiedCanalModel] = Field([], description="List of unified canal components.")

    def get_all_component_names(self) -> List[str]:
        """Helper method to get a flat list of all component names for validation."""
        names = []
        for component_list in [self.reservoirs, self.gates, self.pipes, self.unified_canals]:
            for component in component_list:
                names.append(component.name)
        return names

# --- Topology Model ---

class TopologyConnectionModel(BaseModel):
    """Defines a single connection between two components."""
    upstream: str = Field(..., description="Name of the upstream component.")
    downstream: str = Field(..., description="Name of the downstream component.")

class TopologyModel(BaseModel):
    """Defines the connection graph of the physical components."""
    connections: List[TopologyConnectionModel] = Field([], description="List of all connections in the system.")

# --- Agent Models with Discriminated Union ---
# This allows Pydantic to automatically use the correct 'params' model
# based on the value of the 'class' field.

class BaseAgentConfig(BaseModel):
    """A base model for agent configuration, providing a unique ID."""
    id: str = Field(..., description="Unique identifier for the agent instance.")

class GateControlAgentConfig(BaseAgentConfig):
    class_name: Literal["core_lib.local_agents.control.gate_control_agent.GateControlAgent"] = Field(..., alias="class")
    params: GateControlAgentParams

class ReservoirPerceptionAgentConfig(BaseAgentConfig):
    class_name: Literal["core_lib.local_agents.perception.reservoir_perception_agent.ReservoirPerceptionAgent"] = Field(..., alias="class")
    params: ReservoirPerceptionAgentParams

class CSVInflowAgentConfig(BaseAgentConfig):
    class_name: Literal["core_lib.data_access.csv_inflow_agent.CsvInflowAgent"] = Field(..., alias="class")
    params: CSVInflowAgentParams

from typing import Annotated

# Pydantic will use the 'class_name' field to decide which model to use from the union.
AnyAgentConfig = Annotated[
    Union[GateControlAgentConfig, ReservoirPerceptionAgentConfig, CSVInflowAgentConfig],
    Field(discriminator="class_name"),
]


class AgentsModel(BaseModel):
    """A container for all agent configurations."""
    agents: List[AnyAgentConfig]


# --- Main API Request Body Model ---

class SimulationRequest(BaseModel):
    """
    The main request body for the /run_simulation endpoint.
    It includes the full definition of the simulation scenario.
    """
    components: ComponentsModel
    topology: TopologyModel
    agents: AgentsModel

    @root_validator(skip_on_failure=True)
    def validate_topology_and_agents(cls, values):
        """
        Performs cross-model validation after individual model validation passes.
        1. Checks that all components in the topology exist in the components list.
        2. Checks that all `target_component` fields in agent params exist.
        """
        components: Optional[ComponentsModel] = values.get('components')
        topology: Optional[TopologyModel] = values.get('topology')
        agents: Optional[AgentsModel] = values.get('agents')

        if not components or not topology or not agents:
            return values

        all_component_names = components.get_all_component_names()

        # 1. Validate topology connections
        for conn in topology.connections:
            if conn.upstream not in all_component_names:
                raise ValueError(f"Topology validation failed: Upstream component '{conn.upstream}' not found in components list.")
            if conn.downstream not in all_component_names:
                raise ValueError(f"Topology validation failed: Downstream component '{conn.downstream}' not found in components list.")

        # 2. Validate agent targets
        for agent_config in agents.agents:
            # The union means agent_config is one of the specific types, which have .params
            if hasattr(agent_config.params, 'target_component') and agent_config.params.target_component:
                target = agent_config.params.target_component
                if target not in all_component_names:
                    raise ValueError(f"Agent validation failed: Agent '{agent_config.id}' targets non-existent component '{target}'.")

        return values
